#!/usr/bin/env python3
"""
Sistema de configuración avanzado para producción
"""
import os
import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
from dataclasses import dataclass, field
from datetime import datetime

from .error_handling import ValidationError, require_type, require_range
from .production_logging import get_production_logger

logger = get_production_logger("config")

@dataclass
class DatabaseConfig:
    """Configuración de base de datos"""
    enabled: bool = False
    type: str = "sqlite"  # sqlite, postgresql, mysql
    host: str = "localhost"
    port: int = 5432
    database: str = "crypto_solver"
    username: str = ""
    password: str = ""
    connection_pool_size: int = 10
    timeout: int = 30

@dataclass
class CacheConfig:
    """Configuración de cache"""
    enabled: bool = True
    type: str = "memory"  # memory, redis, file
    max_size: int = 1000
    ttl: int = 3600  # seconds
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    file_cache_dir: str = "cache"

@dataclass
class SecurityConfig:
    """Configuración de seguridad"""
    sandbox_enabled: bool = True
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    max_execution_time: int = 300  # 5 minutes
    allowed_file_types: List[str] = field(default_factory=lambda: [
        '.txt', '.py', '.c', '.cpp', '.java', '.js', '.json', '.xml', '.pem', '.key'
    ])
    blocked_patterns: List[str] = field(default_factory=lambda: [
        'rm -rf', 'format c:', 'del /f', '__import__', 'eval(', 'exec('
    ])
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    api_key_required: bool = False
    api_keys: List[str] = field(default_factory=list)

@dataclass
class PerformanceConfig:
    """Configuración de rendimiento"""
    monitoring_enabled: bool = True
    monitoring_interval: int = 60  # seconds
    max_memory_usage: int = 2 * 1024 * 1024 * 1024  # 2GB
    max_cpu_usage: float = 80.0  # percentage
    parallel_processing: bool = True
    max_workers: int = 4
    timeout_default: int = 30
    timeout_ml: int = 60
    timeout_plugin: int = 120

@dataclass
class MLConfig:
    """Configuración de Machine Learning"""
    enabled: bool = True
    auto_train: bool = False
    model_path: str = "models/ultimate_classifier.joblib"
    training_data_path: str = "data/training"
    min_training_samples: int = 50
    retrain_threshold: float = 0.7  # accuracy threshold
    feature_cache_enabled: bool = True
    prediction_cache_ttl: int = 1800  # 30 minutes

@dataclass
class PluginConfig:
    """Configuración de plugins"""
    auto_load: bool = True
    plugin_dirs: List[str] = field(default_factory=lambda: ["src/plugins"])
    disabled_plugins: List[str] = field(default_factory=list)
    plugin_timeout: int = 60
    max_plugin_memory: int = 512 * 1024 * 1024  # 512MB
    allow_external_plugins: bool = False

@dataclass
class LoggingConfig:
    """Configuración de logging"""
    level: str = "INFO"
    file_enabled: bool = True
    console_enabled: bool = True
    json_enabled: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    log_dir: str = "logs"
    structured_logging: bool = True

@dataclass
class NetworkConfig:
    """Configuración de red"""
    enabled: bool = True
    default_timeout: int = 30
    max_connections: int = 10
    retry_attempts: int = 3
    retry_delay: int = 1
    allowed_hosts: List[str] = field(default_factory=list)  # empty = all allowed
    blocked_hosts: List[str] = field(default_factory=list)
    proxy_enabled: bool = False
    proxy_host: str = ""
    proxy_port: int = 8080

@dataclass
class APIConfig:
    """Configuración de API"""
    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    max_request_size: int = 50 * 1024 * 1024  # 50MB
    rate_limiting: bool = True
    documentation_enabled: bool = True

@dataclass
class ProductionConfig:
    """Configuración principal del sistema"""
    # Información general
    version: str = "1.0.0"
    environment: str = "production"  # development, testing, production
    debug: bool = False
    
    # Configuraciones específicas
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    ml: MLConfig = field(default_factory=MLConfig)
    plugins: PluginConfig = field(default_factory=PluginConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    api: APIConfig = field(default_factory=APIConfig)
    
    # Metadatos
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

class ConfigManager:
    """Gestor de configuración avanzado"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path("config/production.yaml")
        self.config = ProductionConfig()
        self._watchers = []
        
        # Crear directorio de configuración si no existe
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Cargar configuración
        self.load_config()
    
    def load_config(self) -> ProductionConfig:
        """Cargar configuración desde archivo"""
        try:
            if self.config_path.exists():
                logger.info(f"Loading configuration from {self.config_path}")
                
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    if self.config_path.suffix.lower() == '.json':
                        data = json.load(f)
                    else:  # YAML por defecto
                        data = yaml.safe_load(f)
                
                # Actualizar configuración con datos cargados
                self._update_config_from_dict(data)
                
                logger.info("Configuration loaded successfully")
            else:
                logger.info("No configuration file found, using defaults")
                self.save_config()  # Crear archivo con valores por defecto
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.info("Using default configuration")
        
        # Aplicar variables de entorno
        self._apply_environment_variables()
        
        # Validar configuración
        self._validate_config()
        
        return self.config
    
    def save_config(self):
        """Guardar configuración actual"""
        try:
            self.config.updated_at = datetime.now().isoformat()
            
            config_dict = self._config_to_dict()
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.suffix.lower() == '.json':
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                else:  # YAML por defecto
                    yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def _update_config_from_dict(self, data: Dict[str, Any]):
        """Actualizar configuración desde diccionario"""
        for section_name, section_data in data.items():
            if hasattr(self.config, section_name) and isinstance(section_data, dict):
                section = getattr(self.config, section_name)
                
                if hasattr(section, '__dict__'):  # Es un dataclass
                    for key, value in section_data.items():
                        if hasattr(section, key):
                            setattr(section, key, value)
                        else:
                            logger.warning(f"Unknown config key: {section_name}.{key}")
                else:
                    # Es un valor simple
                    setattr(self.config, section_name, section_data)
            elif hasattr(self.config, section_name):
                setattr(self.config, section_name, section_data)
            else:
                logger.warning(f"Unknown config section: {section_name}")
    
    def _config_to_dict(self) -> Dict[str, Any]:
        """Convertir configuración a diccionario"""
        result = {}
        
        for field_name in self.config.__dataclass_fields__:
            value = getattr(self.config, field_name)
            
            if hasattr(value, '__dict__'):  # Es un dataclass
                result[field_name] = {
                    k: v for k, v in value.__dict__.items()
                }
            else:
                result[field_name] = value
        
        return result
    
    def _apply_environment_variables(self):
        """Aplicar variables de entorno"""
        env_mappings = {
            'CRYPTO_SOLVER_DEBUG': ('debug', bool),
            'CRYPTO_SOLVER_LOG_LEVEL': ('logging.level', str),
            'CRYPTO_SOLVER_CACHE_ENABLED': ('cache.enabled', bool),
            'CRYPTO_SOLVER_ML_ENABLED': ('ml.enabled', bool),
            'CRYPTO_SOLVER_API_PORT': ('api.port', int),
            'CRYPTO_SOLVER_MAX_WORKERS': ('performance.max_workers', int),
            'CRYPTO_SOLVER_SANDBOX': ('security.sandbox_enabled', bool),
        }
        
        for env_var, (config_path, value_type) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    # Convertir valor
                    if value_type == bool:
                        converted_value = env_value.lower() in ('true', '1', 'yes', 'on')
                    elif value_type == int:
                        converted_value = int(env_value)
                    elif value_type == float:
                        converted_value = float(env_value)
                    else:
                        converted_value = env_value
                    
                    # Aplicar valor
                    self._set_nested_value(config_path, converted_value)
                    logger.info(f"Applied environment variable: {env_var} = {converted_value}")
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid environment variable {env_var}: {e}")
    
    def _set_nested_value(self, path: str, value: Any):
        """Establecer valor anidado usando notación de puntos"""
        parts = path.split('.')
        obj = self.config
        
        for part in parts[:-1]:
            obj = getattr(obj, part)
        
        setattr(obj, parts[-1], value)
    
    def _validate_config(self):
        """Validar configuración"""
        try:
            # Validar rangos numéricos
            require_range(self.config.performance.max_cpu_usage, 0, 100, "performance.max_cpu_usage")
            require_range(self.config.performance.max_workers, 1, 32, "performance.max_workers")
            require_range(self.config.api.port, 1, 65535, "api.port")
            
            # Validar tipos
            require_type(self.config.debug, bool, "debug")
            require_type(self.config.version, str, "version")
            
            # Validar directorios
            if self.config.cache.type == "file":
                Path(self.config.cache.file_cache_dir).mkdir(parents=True, exist_ok=True)
            
            Path(self.config.logging.log_dir).mkdir(parents=True, exist_ok=True)
            
            # Validar niveles de logging
            valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if self.config.logging.level.upper() not in valid_log_levels:
                raise ValidationError("logging.level", f"Invalid log level: {self.config.logging.level}")
            
            logger.info("Configuration validation passed")
            
        except ValidationError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise
    
    def get(self, path: str, default: Any = None) -> Any:
        """Obtener valor de configuración usando notación de puntos"""
        try:
            parts = path.split('.')
            obj = self.config
            
            for part in parts:
                obj = getattr(obj, part)
            
            return obj
        except AttributeError:
            return default
    
    def set(self, path: str, value: Any):
        """Establecer valor de configuración"""
        self._set_nested_value(path, value)
        self.config.updated_at = datetime.now().isoformat()
    
    def reload(self):
        """Recargar configuración desde archivo"""
        self.load_config()
        logger.info("Configuration reloaded")
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Obtener información del entorno"""
        return {
            'environment': self.config.environment,
            'debug': self.config.debug,
            'version': self.config.version,
            'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            'platform': os.sys.platform,
            'config_file': str(self.config_path),
            'created_at': self.config.created_at,
            'updated_at': self.config.updated_at
        }
    
    def export_config(self, format: str = "yaml") -> str:
        """Exportar configuración como string"""
        config_dict = self._config_to_dict()
        
        if format.lower() == "json":
            return json.dumps(config_dict, indent=2, ensure_ascii=False)
        else:  # YAML por defecto
            return yaml.dump(config_dict, default_flow_style=False, allow_unicode=True)

# Instancia global del gestor de configuración
config_manager = ConfigManager()

def get_config() -> ProductionConfig:
    """Obtener configuración actual"""
    return config_manager.config

def reload_config():
    """Recargar configuración"""
    config_manager.reload()

def save_config():
    """Guardar configuración actual"""
    config_manager.save_config()