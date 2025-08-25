"""
Challenge Manager - Coordinador central para resolución de desafíos
"""

import time
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import threading

from .file_analyzer import FileAnalyzer
from .plugin_manager import PluginManager, plugin_manager
from .cache_manager import cache_manager, cached, cache_challenge_analysis, cache_plugin_result
from .performance_monitor import performance_monitor, PerformanceTimer, timed_operation
from .parallel_executor import parallel_executor, ExecutionConfig, ExecutionMode
from .security_manager import security_manager
from ..models.data import ChallengeData, SolutionResult, ChallengeType, DifficultyLevel
from ..models.exceptions import (
    ChallengeTimeoutError, InsufficientDataError, 
    PluginError, ValidationError
)
from ..utils.config import config
from ..utils.logging import get_logger


class ChallengeManager:
    """Coordinador central para la resolución de desafíos de criptografía y CTF"""
    
    def __init__(self, file_analyzer: Optional[FileAnalyzer] = None, 
                 plugin_manager: Optional[PluginManager] = None):
        self.logger = get_logger(__name__)
        self.file_analyzer = file_analyzer or FileAnalyzer()
        self.plugin_manager = plugin_manager or plugin_manager
        
        # Estado interno
        self._active_challenges: Dict[str, ChallengeData] = {}
        self._solution_history: List[SolutionResult] = []
        self._stats = {
            'total_challenges': 0,
            'successful_solutions': 0,
            'failed_solutions': 0,
            'average_solve_time': 0.0,
            'plugin_usage': {}
        }
        
        # Control de recursos
        self._max_concurrent_challenges = config.plugins.max_concurrent_plugins
        self._global_timeout = config.plugins.plugin_timeout * 2  # Timeout global más largo
        self._executor = ThreadPoolExecutor(max_workers=self._max_concurrent_challenges)
        
        # Inicializar sistemas de optimización
        performance_monitor.start_monitoring(interval=2.0)
        
        self.logger.info("Challenge Manager inicializado con optimizaciones de performance")
    
    @timed_operation("load_challenge")
    def load_challenge(self, file_path: Union[str, Path]) -> ChallengeData:
        """
        Cargar y analizar un desafío desde archivo.
        
        Args:
            file_path: Ruta al archivo del desafío
            
        Returns:
            ChallengeData: Datos del desafío analizado
        """
        file_path = Path(file_path)
        self.logger.info(f"Cargando desafío desde: {file_path}")
        
        try:
            # Validar archivo con sistema de seguridad
            validated_path = security_manager.validate_challenge_file(file_path)
            
            # Verificar cache primero
            cache_key = f"challenge_load:{validated_path}:{validated_path.stat().st_mtime}"
            cached_challenge = cache_manager.get(cache_key)
            
            if cached_challenge:
                self.logger.debug(f"Challenge loaded from cache: {validated_path}")
                challenge_data = cached_challenge
            else:
                # Analizar archivo
                challenge_data = self.file_analyzer.analyze_file(validated_path)
                # Cachear resultado
                cache_manager.put(cache_key, challenge_data, ttl=3600)  # 1 hora
            
            # Registrar desafío activo
            self._active_challenges[challenge_data.id] = challenge_data
            
            # Actualizar estadísticas
            self._stats['total_challenges'] += 1
            
            self.logger.info(f"Desafío cargado: {challenge_data.id} ({challenge_data.challenge_type})")
            return challenge_data
            
        except Exception as e:
            self.logger.error(f"Error cargando desafío: {e}")
            raise ValidationError(f"Error cargando desafío desde {file_path}: {str(e)}")
    
    @timed_operation("solve_challenge")
    def solve_challenge(self, challenge_data: ChallengeData, 
                       strategy: str = "auto") -> SolutionResult:
        """
        Resolver un desafío usando la estrategia especificada.
        
        Args:
            challenge_data: Datos del desafío
            strategy: Estrategia de resolución ("auto", "parallel", "sequential", "single")
            
        Returns:
            SolutionResult: Resultado de la resolución
        """
        self.logger.info(f"Iniciando resolución de desafío {challenge_data.id} con estrategia '{strategy}'")
        
        with PerformanceTimer(f"solve_challenge_{challenge_data.challenge_type}"):
            start_time = time.time()
            
            try:
                # Verificar cache de solución
                cache_key = cache_plugin_result(challenge_data, "solution")
                cached_result = cache_manager.get(cache_key)
                
                if cached_result and cached_result.success:
                    self.logger.debug(f"Solution found in cache for {challenge_data.id}")
                    return cached_result
                
                # Validar desafío
                self._validate_challenge(challenge_data)
                
                # Detectar tipo si no está definido
                if challenge_data.challenge_type == ChallengeType.UNKNOWN:
                    challenge_data.challenge_type = self._detect_challenge_type(challenge_data)
                
                # Seleccionar estrategia de resolución
                if strategy == "auto":
                    strategy = self._select_optimal_strategy(challenge_data)
                
                # Ejecutar resolución según estrategia
                result = self._execute_strategy(challenge_data, strategy)
                
                # Actualizar resultado con tiempo total
                result.execution_time = time.time() - start_time
                
                # Cachear resultado exitoso
                if result.success:
                    cache_manager.put(cache_key, result, ttl=7200)  # 2 horas
                
                # Registrar resultado
                self._register_solution(challenge_data, result)
                
                if result.success:
                    self.logger.info(f"Desafío {challenge_data.id} resuelto exitosamente en {result.execution_time:.2f}s")
                else:
                    self.logger.warning(f"Desafío {challenge_data.id} no pudo ser resuelto")
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                self.logger.error(f"Error resolviendo desafío {challenge_data.id}: {e}")
                performance_monitor.increment_error_count("solve_challenge_error")
                
                error_result = SolutionResult(
                    success=False,
                    error_message=str(e),
                    method_used="challenge_manager",
                    execution_time=execution_time
                )
                
                self._register_solution(challenge_data, error_result)
                return error_result
    
    def solve_challenge_async(self, challenge_data: ChallengeData, 
                            strategy: str = "auto") -> asyncio.Future:
        """
        Resolver desafío de forma asíncrona.
        
        Args:
            challenge_data: Datos del desafío
            strategy: Estrategia de resolución
            
        Returns:
            asyncio.Future: Future con el resultado
        """
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(
            self._executor, 
            self.solve_challenge, 
            challenge_data, 
            strategy
        )
    
    def _validate_challenge(self, challenge_data: ChallengeData) -> None:
        """Validar que el desafío tenga datos suficientes"""
        if not challenge_data.files and not challenge_data.network_info:
            raise InsufficientDataError(
                "El desafío debe tener archivos o información de red",
                required_data="files or network_info"
            )
        
        # Validar archivos existen
        for file_info in challenge_data.files:
            if not file_info.path.exists():
                raise InsufficientDataError(
                    f"Archivo no encontrado: {file_info.path}",
                    required_data=str(file_info.path)
                )
    
    def _detect_challenge_type(self, challenge_data: ChallengeData) -> ChallengeType:
        """Detectar tipo de desafío si no está definido"""
        self.logger.info("Detectando tipo de desafío...")
        
        # El FileAnalyzer ya debería haber detectado el tipo
        if challenge_data.challenge_type and challenge_data.challenge_type != ChallengeType.UNKNOWN:
            return challenge_data.challenge_type
        
        # Análisis adicional basado en plugins disponibles
        plugin_scores = {}
        
        for plugin_name in self.plugin_manager.get_available_plugins():
            plugin = self.plugin_manager.get_plugin(plugin_name)
            if plugin:
                try:
                    confidence = plugin.can_solve(challenge_data)
                    plugin_info = plugin.get_plugin_info()
                    
                    for challenge_type in plugin_info.supported_types:
                        if challenge_type != ChallengeType.MIXED:
                            plugin_scores[challenge_type] = max(
                                plugin_scores.get(challenge_type, 0), 
                                confidence
                            )
                except Exception as e:
                    self.logger.warning(f"Error evaluando plugin {plugin_name}: {e}")
        
        # Retornar tipo con mayor confianza
        if plugin_scores:
            detected_type = max(plugin_scores, key=plugin_scores.get)
            self.logger.info(f"Tipo detectado: {detected_type} (confianza: {plugin_scores[detected_type]:.2f})")
            return detected_type
        
        return ChallengeType.UNKNOWN
    
    def _select_optimal_strategy(self, challenge_data: ChallengeData) -> str:
        """Seleccionar estrategia óptima basada en el desafío"""
        # Obtener plugins disponibles
        available_plugins = self.plugin_manager.select_best_plugins(challenge_data)
        
        if len(available_plugins) == 0:
            raise InsufficientDataError("No hay plugins disponibles para este desafío")
        elif len(available_plugins) == 1:
            return "single"
        elif len(available_plugins) <= 3:
            return "sequential"  # Pocos plugins, ejecutar secuencialmente
        else:
            return "parallel"  # Muchos plugins, ejecutar en paralelo
    
    def _execute_strategy(self, challenge_data: ChallengeData, strategy: str) -> SolutionResult:
        """Ejecutar estrategia de resolución específica"""
        self.logger.info(f"Ejecutando estrategia: {strategy}")
        
        if strategy == "single":
            return self._solve_single_plugin(challenge_data)
        elif strategy == "sequential":
            return self._solve_sequential(challenge_data)
        elif strategy == "parallel":
            return self._solve_parallel(challenge_data)
        else:
            raise ValidationError(f"Estrategia no soportada: {strategy}")
    
    def _solve_single_plugin(self, challenge_data: ChallengeData) -> SolutionResult:
        """Resolver con el mejor plugin disponible"""
        best_plugins = self.plugin_manager.select_best_plugins(challenge_data, max_plugins=1)
        
        if not best_plugins:
            return SolutionResult(
                success=False,
                error_message="No hay plugins disponibles",
                method_used="single_plugin"
            )
        
        plugin_name, plugin, confidence = best_plugins[0]
        self.logger.info(f"Usando plugin único: {plugin_name} (confianza: {confidence:.2f})")
        
        return self.plugin_manager.solve_with_plugin(plugin_name, challenge_data)
    
    def _solve_sequential(self, challenge_data: ChallengeData) -> SolutionResult:
        """Resolver secuencialmente con múltiples plugins"""
        best_plugins = self.plugin_manager.select_best_plugins(challenge_data)
        
        for plugin_name, plugin, confidence in best_plugins:
            self.logger.info(f"Probando plugin: {plugin_name} (confianza: {confidence:.2f})")
            
            try:
                result = self.plugin_manager.solve_with_plugin(plugin_name, challenge_data)
                
                if result.success:
                    self.logger.info(f"Solución encontrada con plugin: {plugin_name}")
                    return result
                
            except Exception as e:
                self.logger.warning(f"Error con plugin {plugin_name}: {e}")
                continue
        
        return SolutionResult(
            success=False,
            error_message="Ningún plugin pudo resolver el desafío",
            method_used="sequential"
        )
    
    def _solve_parallel(self, challenge_data: ChallengeData) -> SolutionResult:
        """Resolver en paralelo con múltiples plugins usando el executor avanzado"""
        best_plugins = self.plugin_manager.select_best_plugins(challenge_data)
        
        if not best_plugins:
            return SolutionResult(
                success=False,
                error_message="No hay plugins disponibles",
                method_used="parallel"
            )
        
        self.logger.info(f"Ejecutando {len(best_plugins)} plugins en paralelo")
        
        # Configurar executor paralelo
        exec_config = ExecutionConfig(
            mode=ExecutionMode.THREAD_POOL,
            max_workers=min(len(best_plugins), 4),
            timeout=self._global_timeout,
            priority_scheduling=True
        )
        
        # Usar el executor paralelo avanzado
        results = parallel_executor.execute_plugins_parallel(challenge_data, best_plugins)
        
        # Buscar primera solución exitosa
        for result in results:
            if result.success:
                self.logger.info(f"Solución encontrada con plugin: {result.plugin_name}")
                return result
        
        # Si no hay solución exitosa, devolver el mejor resultado
        if results:
            # Ordenar por confianza y tiempo de ejecución
            best_result = max(results, key=lambda r: (r.confidence or 0, -r.execution_time))
            return best_result
        
        return SolutionResult(
            success=False,
            error_message="Ningún plugin pudo resolver el desafío en paralelo",
            method_used="parallel"
        )
    
    def _register_solution(self, challenge_data: ChallengeData, result: SolutionResult) -> None:
        """Registrar resultado de solución para estadísticas"""
        self._solution_history.append(result)
        
        # Actualizar estadísticas
        if result.success:
            self._stats['successful_solutions'] += 1
        else:
            self._stats['failed_solutions'] += 1
        
        # Actualizar tiempo promedio
        total_time = sum(r.execution_time for r in self._solution_history)
        self._stats['average_solve_time'] = total_time / len(self._solution_history)
        
        # Actualizar uso de plugins
        if result.plugin_name:
            plugin_name = result.plugin_name.split(':')[0]  # Remover técnica específica
            self._stats['plugin_usage'][plugin_name] = self._stats['plugin_usage'].get(plugin_name, 0) + 1
        
        # Remover de desafíos activos
        if challenge_data.id in self._active_challenges:
            del self._active_challenges[challenge_data.id]
    
    def get_active_challenges(self) -> Dict[str, ChallengeData]:
        """Obtener desafíos actualmente en proceso"""
        return self._active_challenges.copy()
    
    def get_solution_history(self) -> List[SolutionResult]:
        """Obtener historial de soluciones"""
        return self._solution_history.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del manager"""
        stats = self._stats.copy()
        stats.update({
            'active_challenges': len(self._active_challenges),
            'success_rate': (
                self._stats['successful_solutions'] / max(1, self._stats['total_challenges'])
            ) * 100,
            'plugin_manager_stats': self.plugin_manager.get_plugin_statistics()
        })
        return stats
    
    def clear_history(self) -> None:
        """Limpiar historial de soluciones"""
        self._solution_history.clear()
        self._stats = {
            'total_challenges': 0,
            'successful_solutions': 0,
            'failed_solutions': 0,
            'average_solve_time': 0.0,
            'plugin_usage': {}
        }
        self.logger.info("Historial de soluciones limpiado")
    
    def cancel_challenge(self, challenge_id: str) -> bool:
        """
        Cancelar un desafío en proceso.
        
        Args:
            challenge_id: ID del desafío a cancelar
            
        Returns:
            bool: True si se canceló exitosamente
        """
        if challenge_id in self._active_challenges:
            del self._active_challenges[challenge_id]
            self.logger.info(f"Desafío {challenge_id} cancelado")
            return True
        return False
    
    def estimate_difficulty(self, challenge_data: ChallengeData) -> DifficultyLevel:
        """
        Estimar dificultad del desafío basado en plugins disponibles.
        
        Args:
            challenge_data: Datos del desafío
            
        Returns:
            DifficultyLevel: Nivel de dificultad estimado
        """
        # Obtener confianza promedio de plugins
        plugin_confidences = []
        
        for plugin_name in self.plugin_manager.get_available_plugins():
            plugin = self.plugin_manager.get_plugin(plugin_name)
            if plugin:
                try:
                    confidence = plugin.can_solve(challenge_data)
                    if confidence > 0:
                        plugin_confidences.append(confidence)
                except Exception:
                    continue
        
        if not plugin_confidences:
            return DifficultyLevel.EXPERT  # Si ningún plugin puede manejarlo
        
        avg_confidence = sum(plugin_confidences) / len(plugin_confidences)
        max_confidence = max(plugin_confidences)
        
        # Mapear confianza a dificultad (inversa)
        if max_confidence >= 0.9:
            return DifficultyLevel.BEGINNER
        elif max_confidence >= 0.7:
            return DifficultyLevel.EASY
        elif max_confidence >= 0.5:
            return DifficultyLevel.MEDIUM
        elif max_confidence >= 0.3:
            return DifficultyLevel.HARD
        else:
            return DifficultyLevel.EXPERT
    
    def __del__(self):
        """Cleanup al destruir el manager"""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)