"""
Clase base para plugins de Crypto CTF Solver
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import time
import logging

from ..models.data import ChallengeData, SolutionResult, PluginInfo, ChallengeType
from ..models.exceptions import PluginError, ChallengeTimeoutError
from ..utils.logging import get_logger


class CryptoPlugin(ABC):
    """Clase base abstracta para todos los plugins de criptoanálisis"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self._plugin_info = self._create_plugin_info()
        self._start_time = None
        self._timeout = 300  # 5 minutos por defecto
    
    @abstractmethod
    def _create_plugin_info(self) -> PluginInfo:
        """Crear información del plugin. Debe ser implementado por cada plugin."""
        pass
    
    @abstractmethod
    def can_solve(self, challenge_data: ChallengeData) -> float:
        """
        Determinar si el plugin puede resolver el desafío.
        
        Args:
            challenge_data: Datos del desafío
            
        Returns:
            float: Confianza entre 0.0 y 1.0 de poder resolver el desafío
        """
        pass
    
    @abstractmethod
    def solve(self, challenge_data: ChallengeData) -> SolutionResult:
        """
        Intentar resolver el desafío.
        
        Args:
            challenge_data: Datos del desafío
            
        Returns:
            SolutionResult: Resultado de la resolución
        """
        pass
    
    def get_techniques(self) -> List[str]:
        """
        Obtener lista de técnicas que implementa el plugin.
        
        Returns:
            List[str]: Lista de nombres de técnicas
        """
        return self._plugin_info.techniques
    
    def get_plugin_info(self) -> PluginInfo:
        """Obtener información del plugin"""
        return self._plugin_info
    
    def set_timeout(self, timeout: int) -> None:
        """Establecer timeout para la resolución"""
        self._timeout = timeout
    
    def _check_timeout(self) -> None:
        """Verificar si se ha excedido el timeout"""
        if self._start_time and time.time() - self._start_time > self._timeout:
            raise ChallengeTimeoutError(f"Timeout excedido en plugin {self._plugin_info.name}", self._timeout)
    
    def _start_solving(self) -> None:
        """Marcar inicio de resolución"""
        self._start_time = time.time()
        self.logger.info(f"Iniciando resolución con plugin {self._plugin_info.name}")
    
    def _finish_solving(self, result: SolutionResult) -> SolutionResult:
        """Finalizar resolución y actualizar resultado"""
        if self._start_time:
            result.execution_time = time.time() - self._start_time
            result.plugin_name = self._plugin_info.name
            
            if result.success:
                self.logger.info(f"Desafío resuelto exitosamente en {result.execution_time:.2f}s")
            else:
                self.logger.warning(f"Resolución fallida después de {result.execution_time:.2f}s")
        
        return result
    
    def solve_with_timeout(self, challenge_data: ChallengeData) -> SolutionResult:
        """
        Resolver desafío con manejo de timeout.
        
        Args:
            challenge_data: Datos del desafío
            
        Returns:
            SolutionResult: Resultado de la resolución
        """
        try:
            self._start_solving()
            result = self.solve(challenge_data)
            return self._finish_solving(result)
            
        except ChallengeTimeoutError:
            result = SolutionResult(
                success=False,
                error_message=f"Timeout excedido ({self._timeout}s)",
                method_used=self._plugin_info.name,
                execution_time=self._timeout
            )
            return self._finish_solving(result)
            
        except Exception as e:
            self.logger.error(f"Error en plugin {self._plugin_info.name}: {str(e)}")
            result = SolutionResult(
                success=False,
                error_message=str(e),
                method_used=self._plugin_info.name
            )
            return self._finish_solving(result)
    
    def _read_file_content(self, file_path, encoding='utf-8') -> Optional[str]:
        """Utilidad para leer contenido de archivo"""
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"Error leyendo archivo {file_path}: {e}")
            return None
    
    def _read_file_bytes(self, file_path) -> Optional[bytes]:
        """Utilidad para leer archivo como bytes"""
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"Error leyendo archivo binario {file_path}: {e}")
            return None
    
    def _create_success_result(self, flag: str, method: str, confidence: float = 1.0, **kwargs) -> SolutionResult:
        """Crear resultado exitoso"""
        return SolutionResult(
            success=True,
            flag=flag,
            method_used=method,
            confidence=confidence,
            details=kwargs
        )
    
    def _create_failure_result(self, error_message: str, method: str = None, **kwargs) -> SolutionResult:
        """Crear resultado fallido"""
        return SolutionResult(
            success=False,
            error_message=error_message,
            method_used=method or self._plugin_info.name,
            details=kwargs
        )


class MultiTechniquePlugin(CryptoPlugin):
    """Plugin base que puede usar múltiples técnicas"""
    
    def __init__(self):
        super().__init__()
        self._techniques = self._initialize_techniques()
    
    @abstractmethod
    def _initialize_techniques(self) -> Dict[str, callable]:
        """
        Inicializar diccionario de técnicas disponibles.
        
        Returns:
            Dict[str, callable]: Mapeo de nombre de técnica a función
        """
        pass
    
    def solve(self, challenge_data: ChallengeData) -> SolutionResult:
        """Intentar resolver usando múltiples técnicas"""
        best_result = None
        best_confidence = 0.0
        
        # Ordenar técnicas por prioridad si está definida
        techniques = self._get_ordered_techniques(challenge_data)
        
        for technique_name, technique_func in techniques.items():
            self._check_timeout()
            
            try:
                self.logger.info(f"Probando técnica: {technique_name}")
                result = technique_func(challenge_data)
                
                if result.success:
                    result.method_used = f"{self._plugin_info.name}:{technique_name}"
                    return result
                
                # Guardar mejor resultado parcial
                if result.confidence > best_confidence:
                    best_result = result
                    best_confidence = result.confidence
                    
            except Exception as e:
                self.logger.warning(f"Error en técnica {technique_name}: {e}")
                continue
        
        # Si ninguna técnica tuvo éxito, retornar el mejor resultado parcial
        if best_result:
            return best_result
        
        return self._create_failure_result("Ninguna técnica fue exitosa")
    
    def _get_ordered_techniques(self, challenge_data: ChallengeData) -> Dict[str, callable]:
        """Obtener técnicas ordenadas por prioridad para el desafío específico"""
        # Por defecto, retornar en el orden original
        # Los plugins derivados pueden sobrescribir esto para optimizar el orden
        return self._techniques
    
    def get_available_techniques(self) -> List[str]:
        """Obtener lista de técnicas disponibles"""
        return list(self._techniques.keys())


class AnalysisPlugin(CryptoPlugin):
    """Plugin base para análisis de datos sin resolución directa"""
    
    def solve(self, challenge_data: ChallengeData) -> SolutionResult:
        """Realizar análisis y retornar información útil"""
        analysis_results = self.analyze(challenge_data)
        
        return SolutionResult(
            success=False,  # Los plugins de análisis no resuelven directamente
            method_used=f"{self._plugin_info.name}:analysis",
            confidence=0.0,
            details=analysis_results
        )
    
    @abstractmethod
    def analyze(self, challenge_data: ChallengeData) -> Dict[str, Any]:
        """
        Realizar análisis del desafío.
        
        Args:
            challenge_data: Datos del desafío
            
        Returns:
            Dict[str, Any]: Resultados del análisis
        """
        pass