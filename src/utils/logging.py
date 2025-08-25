"""
Sistema de logging para Crypto CTF Solver
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console

from .config import config


class CryptoLogger:
    """Clase para configurar el sistema de logging"""
    
    def __init__(self):
        self.console = Console()
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configurar el sistema de logging"""
        # Configurar logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, config.logging.level.upper()))
        
        # Limpiar handlers existentes
        root_logger.handlers.clear()
        
        # Handler para consola con Rich
        console_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=True,
            markup=True,
            rich_tracebacks=True
        )
        console_handler.setLevel(getattr(logging, config.logging.level.upper()))
        
        # Formato para consola
        console_formatter = logging.Formatter(
            "%(message)s",
            datefmt="[%X]"
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # Handler para archivo si está configurado
        if config.logging.file_path:
            self._setup_file_handler(root_logger)
    
    def _setup_file_handler(self, logger: logging.Logger) -> None:
        """Configurar handler para archivo"""
        log_file = Path(config.logging.file_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Handler rotativo para archivos
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=config.logging.max_file_size,
            backupCount=config.logging.backup_count,
            encoding='utf-8'
        )
        
        file_handler.setLevel(logging.DEBUG)  # Archivo siempre en DEBUG
        
        # Formato detallado para archivo
        file_formatter = logging.Formatter(
            config.logging.format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Obtener logger con nombre específico"""
        return logging.getLogger(name)


# Instancia global del logger
crypto_logger = CryptoLogger()


def get_logger(name: str) -> logging.Logger:
    """Función de conveniencia para obtener logger"""
    return crypto_logger.get_logger(name)


def setup_logging(level: Optional[str] = None) -> None:
    """Configurar el sistema de logging"""
    if level:
        # Actualizar nivel de configuración
        config.logging.level = level.upper()
    
    # Reconfigurar el logger
    global crypto_logger
    crypto_logger = CryptoLogger()


# Configurar logging para bibliotecas externas
def configure_external_loggers():
    """Configurar nivel de logging para bibliotecas externas"""
    external_loggers = [
        'urllib3',
        'requests',
        'tensorflow',
        'torch',
        'matplotlib',
        'PIL'
    ]
    
    for logger_name in external_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)


# Configurar al importar
configure_external_loggers()