"""
Plugin Manager - Gestor de plugins para Crypto CTF Solver
"""

import importlib
import importlib.util
import inspect
import pkgutil
from pathlib import Path
from typing import List, Dict, Type, Optional, Tuple, Any
import logging

from ..plugins.base import CryptoPlugin
from ..models.data import ChallengeData, SolutionResult, PluginInfo, ChallengeType
from ..models.exceptions import PluginError
from ..utils.config import config
from ..utils.logging import get_logger


class PluginManager:
    """Gestor de plugins para carga dinámica y selección inteligente"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._plugins: Dict[str, CryptoPlugin] = {}
        self._plugin_classes: Dict[str, Type[CryptoPlugin]] = {}
        self._plugin_info: Dict[str, PluginInfo] = {}
        
        # Cargar plugins automáticamente
        self._load_plugins()
    
    def _load_plugins(self) -> None:
        """Cargar todos los plugins disponibles"""
        self.logger.info("Cargando plugins...")
        
        # Obtener directorio de plugins
        plugins_dir = Path(__file__).parent.parent / "plugins"
        
        # Cargar plugins desde cada subdirectorio
        for plugin_dir in plugins_dir.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('__'):
                self._load_plugin_from_directory(plugin_dir)
        
        self.logger.info(f"Cargados {len(self._plugins)} plugins")
    
    def _load_plugin_from_directory(self, plugin_dir: Path) -> None:
        """Cargar plugin desde un directorio específico"""
        try:
            # Construir nombre del módulo
            module_name = f"src.plugins.{plugin_dir.name}.plugin"
            
            # Buscar archivo principal del plugin
            main_file = plugin_dir / "plugin.py"
            if not main_file.exists():
                self.logger.warning(f"No se encontró archivo plugin.py para {plugin_dir.name}")
                return
            
            # Importar módulo usando importlib
            module = importlib.import_module(module_name)
            
            # Buscar clases que hereden de CryptoPlugin
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, CryptoPlugin) and 
                    obj != CryptoPlugin and 
                    not inspect.isabstract(obj)):
                    
                    self._register_plugin_class(name, obj)
            
        except Exception as e:
            self.logger.error(f"Error cargando plugin desde {plugin_dir}: {e}")
    
    def _register_plugin_class(self, name: str, plugin_class: Type[CryptoPlugin]) -> None:
        """Registrar clase de plugin"""
        try:
            # Crear instancia para obtener información
            instance = plugin_class()
            plugin_info = instance.get_plugin_info()
            
            # Verificar si el plugin está habilitado
            if plugin_info.name not in config.plugins.enabled_plugins:
                self.logger.info(f"Plugin {plugin_info.name} deshabilitado en configuración")
                return
            
            # Registrar plugin
            self._plugin_classes[plugin_info.name] = plugin_class
            self._plugins[plugin_info.name] = instance
            self._plugin_info[plugin_info.name] = plugin_info
            
            self.logger.info(f"Plugin registrado: {plugin_info.name} v{plugin_info.version}")
            
        except Exception as e:
            self.logger.error(f"Error registrando plugin {name}: {e}")
    
    def get_available_plugins(self) -> List[str]:
        """Obtener lista de plugins disponibles"""
        return list(self._plugins.keys())
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """Obtener información de un plugin específico"""
        return self._plugin_info.get(plugin_name)
    
    def get_all_plugin_info(self) -> Dict[str, PluginInfo]:
        """Obtener información de todos los plugins"""
        return self._plugin_info.copy()
    
    def get_plugin(self, plugin_name: str) -> Optional[CryptoPlugin]:
        """Obtener instancia de plugin específico"""
        return self._plugins.get(plugin_name)
    
    def get_plugins_for_type(self, challenge_type: ChallengeType) -> List[Tuple[str, CryptoPlugin, float]]:
        """
        Obtener plugins que pueden manejar un tipo específico de desafío.
        
        Args:
            challenge_type: Tipo de desafío
            
        Returns:
            List[Tuple[str, CryptoPlugin, float]]: Lista de (nombre, plugin, prioridad)
        """
        suitable_plugins = []
        
        for name, plugin in self._plugins.items():
            plugin_info = self._plugin_info[name]
            
            if plugin_info.can_handle_type(challenge_type):
                # Usar prioridad del plugin como score base
                priority = plugin_info.priority / 100.0
                suitable_plugins.append((name, plugin, priority))
        
        # Ordenar por prioridad descendente
        suitable_plugins.sort(key=lambda x: x[2], reverse=True)
        return suitable_plugins
    
    def select_best_plugins(self, challenge_data: ChallengeData, max_plugins: int = None) -> List[Tuple[str, CryptoPlugin, float]]:
        """
        Seleccionar los mejores plugins para un desafío específico.
        
        Args:
            challenge_data: Datos del desafío
            max_plugins: Número máximo de plugins a retornar
            
        Returns:
            List[Tuple[str, CryptoPlugin, float]]: Lista de (nombre, plugin, confianza)
        """
        if max_plugins is None:
            max_plugins = config.plugins.max_concurrent_plugins
        
        plugin_scores = []
        
        # Evaluar cada plugin
        for name, plugin in self._plugins.items():
            try:
                confidence = plugin.can_solve(challenge_data)
                if confidence > 0:
                    plugin_scores.append((name, plugin, confidence))
                    
            except Exception as e:
                self.logger.warning(f"Error evaluando plugin {name}: {e}")
                continue
        
        # Ordenar por confianza descendente
        plugin_scores.sort(key=lambda x: x[2], reverse=True)
        
        # Retornar los mejores plugins
        return plugin_scores[:max_plugins]
    
    def solve_with_plugin(self, plugin_name: str, challenge_data: ChallengeData) -> SolutionResult:
        """
        Resolver desafío con un plugin específico.
        
        Args:
            plugin_name: Nombre del plugin
            challenge_data: Datos del desafío
            
        Returns:
            SolutionResult: Resultado de la resolución
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            raise PluginError(f"Plugin no encontrado: {plugin_name}")
        
        try:
            # Importar security manager aquí para evitar imports circulares
            from .security_manager import security_manager
            
            # Ejecutar plugin de forma segura
            return security_manager.execute_plugin_safe(plugin, challenge_data)
            
        except Exception as e:
            self.logger.error(f"Error ejecutando plugin {plugin_name}: {e}")
            raise PluginError(f"Error en plugin {plugin_name}: {str(e)}")
    
    def solve_with_best_plugins(self, challenge_data: ChallengeData) -> List[SolutionResult]:
        """
        Intentar resolver desafío con los mejores plugins disponibles.
        
        Args:
            challenge_data: Datos del desafío
            
        Returns:
            List[SolutionResult]: Lista de resultados de cada plugin
        """
        best_plugins = self.select_best_plugins(challenge_data)
        results = []
        
        self.logger.info(f"Intentando resolver con {len(best_plugins)} plugins")
        
        for plugin_name, plugin, confidence in best_plugins:
            self.logger.info(f"Probando plugin {plugin_name} (confianza: {confidence:.2f})")
            
            try:
                result = self.solve_with_plugin(plugin_name, challenge_data)
                results.append(result)
                
                # Si encontramos una solución exitosa, podemos parar
                if result.success:
                    self.logger.info(f"Solución encontrada con plugin {plugin_name}")
                    break
                    
            except Exception as e:
                self.logger.error(f"Error con plugin {plugin_name}: {e}")
                # Crear resultado de error
                error_result = SolutionResult(
                    success=False,
                    error_message=str(e),
                    method_used=plugin_name,
                    confidence=0.0
                )
                results.append(error_result)
        
        return results
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """
        Recargar un plugin específico.
        
        Args:
            plugin_name: Nombre del plugin a recargar
            
        Returns:
            bool: True si se recargó exitosamente
        """
        try:
            if plugin_name in self._plugins:
                # Obtener clase del plugin
                plugin_class = self._plugin_classes.get(plugin_name)
                if plugin_class:
                    # Crear nueva instancia
                    new_instance = plugin_class()
                    
                    # Reemplazar instancia
                    self._plugins[plugin_name] = new_instance
                    self._plugin_info[plugin_name] = new_instance.get_plugin_info()
                    
                    self.logger.info(f"Plugin {plugin_name} recargado exitosamente")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error recargando plugin {plugin_name}: {e}")
            return False
    
    def reload_all_plugins(self) -> None:
        """Recargar todos los plugins"""
        self.logger.info("Recargando todos los plugins...")
        
        # Limpiar plugins actuales
        self._plugins.clear()
        self._plugin_classes.clear()
        self._plugin_info.clear()
        
        # Recargar
        self._load_plugins()
    
    def get_plugin_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de plugins"""
        stats = {
            'total_plugins': len(self._plugins),
            'enabled_plugins': len([p for p in self._plugin_info.values() if p.enabled]),
            'plugins_by_type': {},
            'plugin_details': []
        }
        
        # Contar plugins por tipo
        for plugin_info in self._plugin_info.values():
            for challenge_type in plugin_info.supported_types:
                type_name = challenge_type.value
                stats['plugins_by_type'][type_name] = stats['plugins_by_type'].get(type_name, 0) + 1
        
        # Detalles de cada plugin
        for name, plugin_info in self._plugin_info.items():
            stats['plugin_details'].append({
                'name': name,
                'version': plugin_info.version,
                'enabled': plugin_info.enabled,
                'priority': plugin_info.priority,
                'supported_types': [t.value for t in plugin_info.supported_types],
                'techniques': plugin_info.techniques
            })
        
        return stats


# Instancia global del plugin manager
plugin_manager = PluginManager()