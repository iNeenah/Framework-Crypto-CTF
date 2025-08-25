"""
Crypto CTF Solver - Main Integration Module
Entry point for the complete system
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Core components
from .core.challenge_manager import ChallengeManager
from .core.file_analyzer import FileAnalyzer
from .core.plugin_manager import plugin_manager
from .core.network_connector import NetworkConnector
from .core.cache_manager import cache_manager
from .core.performance_monitor import performance_monitor
from .core.security_manager import security_manager

# ML components
from .ml.training.training_manager import TrainingManager
from .ml.models.challenge_classifier import ChallengeClassifier

# CLI
from .cli.main import CryptoCTFSolverCLI

# Utils
from .utils.config import config
from .utils.logging import setup_logging, get_logger


class CryptoCTFSolver:
    """
    Clase principal del sistema Crypto CTF Solver
    Integra todos los componentes en un sistema unificado
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializar el sistema completo
        
        Args:
            config_path: Ruta opcional al archivo de configuración
        """
        # Configurar logging
        setup_logging(level=config.logging.level)
        self.logger = get_logger(__name__)
        
        self.logger.info("Inicializando Crypto CTF Solver...")
        
        # Cargar configuración personalizada si se proporciona
        if config_path:
            config.config_path = config_path
            config.load_config()
        
        # Inicializar componentes core
        self.file_analyzer = FileAnalyzer()
        self.challenge_manager = ChallengeManager(
            file_analyzer=self.file_analyzer,
            plugin_manager=plugin_manager
        )
        self.network_connector = NetworkConnector()
        
        # Inicializar componentes ML
        self.training_manager = TrainingManager()
        self.challenge_classifier = ChallengeClassifier()
        
        # Inicializar CLI
        self.cli = CryptoCTFSolverCLI()
        
        # Estadísticas del sistema
        self.system_stats = {
            'version': '1.0.0',
            'initialized_at': None,
            'total_challenges_processed': 0,
            'successful_solutions': 0,
            'failed_solutions': 0,
            'plugins_loaded': 0,
            'ml_model_trained': False
        }
        
        # Finalizar inicialización
        self._post_init()
        
        self.logger.info("Crypto CTF Solver inicializado exitosamente")
    
    def _post_init(self) -> None:
        """Tareas de post-inicialización"""
        import time
        
        # Registrar tiempo de inicialización
        self.system_stats['initialized_at'] = time.time()
        
        # Contar plugins cargados
        self.system_stats['plugins_loaded'] = len(plugin_manager.get_available_plugins())
        
        # Verificar si el modelo ML está entrenado
        try:
            if self.challenge_classifier.is_trained:
                self.system_stats['ml_model_trained'] = True
        except Exception:
            pass
        
        # Inicializar monitoreo de performance si está habilitado
        if config.performance.monitoring_enabled:
            performance_monitor.start_monitoring(
                interval=config.performance.monitoring_interval
            )
        
        # Limpiar cache expirado
        cache_manager.cleanup_expired()
        
        self.logger.info(f"Sistema inicializado con {self.system_stats['plugins_loaded']} plugins")
    
    @property
    def plugin_manager(self):
        """Acceso al plugin manager"""
        return plugin_manager
    
    def solve_challenge_from_file(self, file_path: str, strategy: str = "auto") -> Dict[str, Any]:
        """
        Resolver desafío desde archivo
        
        Args:
            file_path: Ruta al archivo del desafío
            strategy: Estrategia de resolución
            
        Returns:
            Diccionario con resultado detallado
        """
        try:
            # Cargar desafío
            challenge_data = self.challenge_manager.load_challenge(Path(file_path))
            
            # Resolver desafío
            result = self.challenge_manager.solve_challenge(challenge_data, strategy)
            
            # Actualizar estadísticas
            self.system_stats['total_challenges_processed'] += 1
            if result.success:
                self.system_stats['successful_solutions'] += 1
            else:
                self.system_stats['failed_solutions'] += 1
            
            # Almacenar para ML si fue exitoso
            if result.success and result.plugin_name:
                self.training_manager.add_solution_result(challenge_data, result)
            
            return {
                'success': result.success,
                'challenge_id': challenge_data.id,
                'challenge_type': challenge_data.challenge_type.value if challenge_data.challenge_type else 'UNKNOWN',
                'flag': result.flag,
                'method_used': result.method_used,
                'plugin_name': result.plugin_name,
                'confidence': result.confidence,
                'execution_time': result.execution_time,
                'error_message': result.error_message,
                'details': result.details
            }
            
        except Exception as e:
            self.logger.error(f"Error solving challenge from file {file_path}: {e}")
            self.system_stats['failed_solutions'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def solve_network_challenge(self, host: str, port: int, protocol: str = "tcp") -> Dict[str, Any]:
        """
        Resolver desafío de red
        
        Args:
            host: Host del servidor
            port: Puerto del servidor
            protocol: Protocolo de conexión
            
        Returns:
            Diccionario con resultado detallado
        """
        try:
            from .models.data import NetworkInfo, ChallengeData, ChallengeType
            
            # Crear información de red
            network_info = NetworkInfo(
                host=host,
                port=port,
                protocol=protocol
            )
            
            # Crear desafío de red
            challenge_data = ChallengeData(
                id=f"network_{host}_{port}",
                name=f"Network Challenge {host}:{port}",
                description=f"Remote challenge at {host}:{port}",
                challenge_type=ChallengeType.NETWORK,
                network_info=network_info
            )
            
            # Resolver desafío
            result = self.challenge_manager.solve_challenge(challenge_data)
            
            # Actualizar estadísticas
            self.system_stats['total_challenges_processed'] += 1
            if result.success:
                self.system_stats['successful_solutions'] += 1
            else:
                self.system_stats['failed_solutions'] += 1
            
            return {
                'success': result.success,
                'host': host,
                'port': port,
                'protocol': protocol,
                'solution': result.solution,
                'flag': result.flag,
                'method_used': result.method_used,
                'execution_time': result.execution_time,
                'error_message': result.error_message
            }
            
        except Exception as e:
            self.logger.error(f"Error solving network challenge {host}:{port}: {e}")
            self.system_stats['failed_solutions'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'host': host,
                'port': port
            }
    
    def analyze_challenge_content(self, content: str) -> Dict[str, Any]:
        """
        Analizar contenido de desafío directamente
        
        Args:
            content: Contenido del desafío como string
            
        Returns:
            Diccionario con análisis del desafío
        """
        try:
            from .models.data import ChallengeData, ChallengeType
            import tempfile
            import os
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                # Analizar contenido usando file analyzer
                challenge_data = self.file_analyzer.analyze_file(Path(temp_path))
                
                # Obtener plugins compatibles
                compatible_plugins = plugin_manager.get_compatible_plugins(challenge_data)
                
                # Determinar tipo más probable
                if compatible_plugins:
                    best_plugin, best_confidence = compatible_plugins[0]
                    plugin_name = best_plugin.__class__.__name__
                    
                    # Mapear nombre de plugin a tipo de desafío
                    type_mapping = {
                        'BasicCryptoPlugin': 'BASIC_CRYPTO',
                        'RSAPlugin': 'RSA',
                        'EllipticCurvePlugin': 'ECC',
                        'NetworkPlugin': 'NETWORK'
                    }
                    
                    detected_type = type_mapping.get(plugin_name, plugin_name.replace('Plugin', '').upper())
                    
                    # Obtener técnicas sugeridas
                    techniques = []
                    for plugin, confidence in compatible_plugins[:3]:
                        if hasattr(plugin, 'get_techniques'):
                            techniques.extend(plugin.get_techniques())
                    
                    return {
                        'success': True,
                        'detected_type': detected_type,
                        'confidence': best_confidence,
                        'suggested_techniques': techniques[:5],  # Top 5
                        'compatible_plugins': len(compatible_plugins)
                    }
                else:
                    return {
                        'success': False,
                        'detected_type': 'UNKNOWN',
                        'error': 'No compatible plugins found'
                    }
                    
            finally:
                # Limpiar archivo temporal
                try:
                    os.unlink(temp_path)
                except:
                    pass
                
        except Exception as e:
            self.logger.error(f"Error analyzing challenge content: {e}")
            return {
                'success': False,
                'error': str(e),
                'detected_type': 'ERROR'
            }

    def analyze_challenge_file(self, file_path: str, detailed: bool = False) -> Dict[str, Any]:
        """
        Analizar archivo de desafío sin resolverlo
        
        Args:
            file_path: Ruta al archivo
            detailed: Si incluir análisis detallado
            
        Returns:
            Diccionario con análisis del desafío
        """
        try:
            # Analizar archivo
            challenge_data = self.file_analyzer.analyze_file(Path(file_path))
            
            # Predicción ML si está disponible
            ml_prediction = None
            if self.challenge_classifier.is_trained:
                try:
                    predicted_type, confidence = self.challenge_classifier.predict(challenge_data)
                    ml_prediction = {
                        'predicted_type': predicted_type,
                        'confidence': confidence
                    }
                except Exception as e:
                    self.logger.debug(f"ML prediction failed: {e}")
            
            result = {
                'file_path': file_path,
                'challenge_id': challenge_data.id,
                'challenge_name': challenge_data.name,
                'detected_type': challenge_data.challenge_type.value,
                'file_count': len(challenge_data.files),
                'total_size': sum(f.size for f in challenge_data.files),
                'tags': challenge_data.tags,
                'metadata': challenge_data.metadata
            }
            
            if ml_prediction:
                result['ml_prediction'] = ml_prediction
            
            if detailed:
                result['files'] = [
                    {
                        'path': str(f.path),
                        'size': f.size,
                        'mime_type': f.mime_type,
                        'hash_md5': f.hash_md5,
                        'hash_sha256': f.hash_sha256
                    }
                    for f in challenge_data.files
                ]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing challenge file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def train_ml_model(self) -> Dict[str, Any]:
        """
        Entrenar modelo de machine learning
        
        Returns:
            Diccionario con resultados del entrenamiento
        """
        try:
            metrics = self.training_manager.train_model()
            
            if metrics.get('training_completed', False):
                self.system_stats['ml_model_trained'] = True
            
            return {
                'success': True,
                'metrics': metrics
            }
            
        except Exception as e:
            self.logger.error(f"Error training ML model: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Obtener estado completo del sistema
        
        Returns:
            Diccionario con estado del sistema
        """
        # Estadísticas de componentes
        plugin_stats = plugin_manager.get_plugin_statistics()
        cache_stats = cache_manager.get_stats()
        performance_stats = performance_monitor.get_system_stats()
        security_stats = security_manager.get_security_stats()
        
        # Estadísticas de ML
        ml_stats = {}
        try:
            ml_stats = self.training_manager.get_training_statistics()
        except Exception:
            pass
        
        return {
            'system': self.system_stats,
            'plugins': plugin_stats,
            'cache': cache_stats,
            'performance': performance_stats,
            'security': security_stats,
            'ml': ml_stats,
            'config': {
                'cache_enabled': config.cache.enabled,
                'security_enabled': config.security.sandbox_enabled,
                'performance_monitoring': config.performance.monitoring_enabled,
                'ml_auto_train': config.ml.auto_train
            }
        }
    
    def run_cli(self, args: Optional[list] = None) -> int:
        """
        Ejecutar interfaz de línea de comandos
        
        Args:
            args: Argumentos de línea de comandos
            
        Returns:
            Código de salida
        """
        return self.cli.run(args)
    
    def shutdown(self) -> None:
        """Cerrar sistema y limpiar recursos"""
        self.logger.info("Cerrando Crypto CTF Solver...")
        
        try:
            # Detener monitoreo de performance
            performance_monitor.stop_monitoring()
            
            # Limpiar recursos de seguridad
            security_manager.cleanup_resources()
            
            # Cerrar conexiones de red activas
            # (NetworkConnector se encarga de esto automáticamente)
            
            # Guardar configuración si ha cambiado
            config.save_config()
            
            self.logger.info("Sistema cerrado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error durante el cierre del sistema: {e}")


def main():
    """Función principal del programa"""
    try:
        # Crear instancia del sistema
        solver = CryptoCTFSolver()
        
        # Ejecutar CLI
        exit_code = solver.run_cli()
        
        # Cerrar sistema
        solver.shutdown()
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario")
        return 1
    except Exception as e:
        print(f"Error fatal: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())