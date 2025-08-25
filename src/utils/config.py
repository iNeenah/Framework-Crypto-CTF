"""
Sistema de configuración para Crypto CTF Solver
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field


@dataclass
class LoggingConfig:
    """Configuración de logging"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class PluginConfig:
    """Configuración de plugins"""
    enabled_plugins: list = None
    plugin_timeout: int = 300  # 5 minutos
    max_concurrent_plugins: int = 4
    
    def __post_init__(self):
        if self.enabled_plugins is None:
            self.enabled_plugins = ["basic_crypto", "rsa", "elliptic_curve", "network"]


@dataclass
class MLConfig:
    """Configuración de Machine Learning"""
    model_path: str = "data/models"
    training_data_path: str = "data/training_data"
    auto_train: bool = True
    min_training_samples: int = 100
    model_update_frequency: int = 50  # Cada 50 desafíos resueltos


@dataclass
class NetworkConfig:
    """Configuración de red"""
    default_timeout: int = 30
    max_connections: int = 10
    retry_attempts: int = 3
    user_agent: str = "CryptoCTFSolver/0.1.0"


@dataclass
class SecurityConfig:
    """Configuración de seguridad"""
    sandbox_enabled: bool = True
    max_memory_mb: int = 1024
    max_cpu_time: int = 300  # 5 minutos
    temp_dir_cleanup: bool = True


@dataclass
class CacheConfig:
    """Configuración de cache"""
    enabled: bool = True
    max_memory_mb: int = 100
    default_ttl: int = 3600  # 1 hora
    disk_cache_enabled: bool = True
    cache_dir: str = "data/cache"


@dataclass
class PerformanceConfig:
    """Configuración de performance"""
    monitoring_enabled: bool = True
    monitoring_interval: float = 2.0
    parallel_execution: bool = True
    max_parallel_workers: int = 4
    resource_monitoring: bool = True


class Config:
    """Clase principal de configuración"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/config.json"
        self.logging = LoggingConfig()
        self.plugins = PluginConfig()
        self.ml = MLConfig()
        self.network = NetworkConfig()
        self.security = SecurityConfig()
        self.cache = CacheConfig()
        self.performance = PerformanceConfig()
        
        # Cargar configuración si existe
        self.load_config()
    
    def load_config(self) -> None:
        """Cargar configuración desde archivo"""
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Actualizar configuraciones
                if 'logging' in data:
                    self.logging = LoggingConfig(**data['logging'])
                if 'plugins' in data:
                    self.plugins = PluginConfig(**data['plugins'])
                if 'ml' in data:
                    self.ml = MLConfig(**data['ml'])
                if 'network' in data:
                    self.network = NetworkConfig(**data['network'])
                if 'security' in data:
                    self.security = SecurityConfig(**data['security'])
                if 'cache' in data:
                    self.cache = CacheConfig(**data['cache'])
                if 'performance' in data:
                    self.performance = PerformanceConfig(**data['performance'])
                    
            except Exception as e:
                logging.warning(f"Error cargando configuración: {e}")
    
    def save_config(self) -> None:
        """Guardar configuración actual"""
        config_data = {
            'logging': asdict(self.logging),
            'plugins': asdict(self.plugins),
            'ml': asdict(self.ml),
            'network': asdict(self.network),
            'security': asdict(self.security),
            'cache': asdict(self.cache),
            'performance': asdict(self.performance)
        }
        
        # Crear directorio si no existe
        config_file = Path(self.config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def get_env_override(self, key: str, default: Any = None) -> Any:
        """Obtener override desde variables de entorno"""
        env_key = f"CRYPTO_CTF_{key.upper()}"
        return os.getenv(env_key, default)


# Instancia global de configuración
config = Config()