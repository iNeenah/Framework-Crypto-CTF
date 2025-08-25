#!/usr/bin/env python3
"""
Sistema de logging robusto para producción
"""
import logging
import logging.handlers
import os
import sys
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import threading

class ProductionLogger:
    """Logger robusto para entornos de producción"""
    
    def __init__(self, name: str = "crypto_ctf_solver"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Evitar duplicar handlers
        if not self.logger.handlers:
            self._setup_handlers()
        
        # Thread-safe logging
        self._lock = threading.Lock()
        
        # Métricas de logging
        self.metrics = {
            'total_logs': 0,
            'errors': 0,
            'warnings': 0,
            'info': 0,
            'debug': 0,
            'critical': 0
        }
    
    def _setup_handlers(self):
        """Configurar handlers de logging"""
        
        # Crear directorio de logs
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Formatter detallado para archivos
        file_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Formatter simple para consola
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Handler para archivo principal (rotativo)
        main_file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "crypto_solver.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        main_file_handler.setLevel(logging.INFO)
        main_file_handler.setFormatter(file_formatter)
        
        # Handler para errores (separado)
        error_file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "errors.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(file_formatter)
        
        # Handler para debug (solo en desarrollo)
        debug_file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "debug.log",
            maxBytes=20*1024*1024,  # 20MB
            backupCount=2,
            encoding='utf-8'
        )
        debug_file_handler.setLevel(logging.DEBUG)
        debug_file_handler.setFormatter(file_formatter)
        
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # Handler para JSON logs (para análisis automatizado)
        json_handler = logging.handlers.RotatingFileHandler(
            log_dir / "structured.jsonl",
            maxBytes=15*1024*1024,  # 15MB
            backupCount=3,
            encoding='utf-8'
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(self._json_formatter())
        
        # Agregar handlers
        self.logger.addHandler(main_file_handler)
        self.logger.addHandler(error_file_handler)
        self.logger.addHandler(debug_file_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(json_handler)
    
    def _json_formatter(self):
        """Formatter para logs estructurados en JSON"""
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                    'level': record.levelname,
                    'logger': record.name,
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno,
                    'message': record.getMessage(),
                    'thread': record.thread,
                    'process': record.process
                }
                
                # Agregar información extra si existe
                if hasattr(record, 'extra_data'):
                    log_entry['extra'] = record.extra_data
                
                # Agregar stack trace para errores
                if record.exc_info:
                    log_entry['exception'] = self.formatException(record.exc_info)
                
                return json.dumps(log_entry, ensure_ascii=False)
        
        return JSONFormatter()
    
    def _update_metrics(self, level: str):
        """Actualizar métricas de logging"""
        with self._lock:
            self.metrics['total_logs'] += 1
            self.metrics[level.lower()] += 1
    
    def debug(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log de debug"""
        self._update_metrics('DEBUG')
        if extra_data:
            self.logger.debug(message, extra={'extra_data': extra_data})
        else:
            self.logger.debug(message)
    
    def info(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log de información"""
        self._update_metrics('INFO')
        if extra_data:
            self.logger.info(message, extra={'extra_data': extra_data})
        else:
            self.logger.info(message)
    
    def warning(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log de advertencia"""
        self._update_metrics('WARNING')
        if extra_data:
            self.logger.warning(message, extra={'extra_data': extra_data})
        else:
            self.logger.warning(message)
    
    def error(self, message: str, exception: Optional[Exception] = None, extra_data: Optional[Dict[str, Any]] = None):
        """Log de error"""
        self._update_metrics('ERROR')
        
        if exception:
            if extra_data:
                self.logger.error(f"{message}: {str(exception)}", exc_info=True, extra={'extra_data': extra_data})
            else:
                self.logger.error(f"{message}: {str(exception)}", exc_info=True)
        else:
            if extra_data:
                self.logger.error(message, extra={'extra_data': extra_data})
            else:
                self.logger.error(message)
    
    def critical(self, message: str, exception: Optional[Exception] = None, extra_data: Optional[Dict[str, Any]] = None):
        """Log crítico"""
        self._update_metrics('CRITICAL')
        
        if exception:
            if extra_data:
                self.logger.critical(f"{message}: {str(exception)}", exc_info=True, extra={'extra_data': extra_data})
            else:
                self.logger.critical(f"{message}: {str(exception)}", exc_info=True)
        else:
            if extra_data:
                self.logger.critical(message, extra={'extra_data': extra_data})
            else:
                self.logger.critical(message)
    
    def log_challenge_attempt(self, challenge_id: str, plugin_name: str, method: str, success: bool, execution_time: float, details: Optional[Dict] = None):
        """Log específico para intentos de resolución de desafíos"""
        extra_data = {
            'challenge_id': challenge_id,
            'plugin': plugin_name,
            'method': method,
            'success': success,
            'execution_time': execution_time,
            'details': details or {}
        }
        
        if success:
            self.info(f"Challenge solved: {challenge_id} using {plugin_name}:{method}", extra_data)
        else:
            self.warning(f"Challenge attempt failed: {challenge_id} using {plugin_name}:{method}", extra_data)
    
    def log_plugin_load(self, plugin_name: str, version: str, success: bool, error: Optional[str] = None):
        """Log específico para carga de plugins"""
        extra_data = {
            'plugin_name': plugin_name,
            'version': version,
            'success': success,
            'error': error
        }
        
        if success:
            self.info(f"Plugin loaded successfully: {plugin_name} v{version}", extra_data)
        else:
            self.error(f"Failed to load plugin: {plugin_name} - {error}", extra_data=extra_data)
    
    def log_ml_prediction(self, content_hash: str, predicted_type: str, confidence: float, execution_time: float):
        """Log específico para predicciones ML"""
        extra_data = {
            'content_hash': content_hash,
            'predicted_type': predicted_type,
            'confidence': confidence,
            'execution_time': execution_time
        }
        
        self.info(f"ML prediction: {predicted_type} (confidence: {confidence:.3f})", extra_data)
    
    def log_performance_metrics(self, operation: str, duration: float, memory_usage: Optional[float] = None, cpu_usage: Optional[float] = None):
        """Log de métricas de performance"""
        extra_data = {
            'operation': operation,
            'duration': duration,
            'memory_usage': memory_usage,
            'cpu_usage': cpu_usage
        }
        
        self.debug(f"Performance: {operation} took {duration:.3f}s", extra_data)
    
    def log_security_event(self, event_type: str, severity: str, details: Dict[str, Any]):
        """Log de eventos de seguridad"""
        extra_data = {
            'event_type': event_type,
            'severity': severity,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        if severity.upper() in ['HIGH', 'CRITICAL']:
            self.critical(f"Security event: {event_type}", extra_data=extra_data)
        elif severity.upper() == 'MEDIUM':
            self.error(f"Security event: {event_type}", extra_data=extra_data)
        else:
            self.warning(f"Security event: {event_type}", extra_data=extra_data)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de logging"""
        with self._lock:
            return self.metrics.copy()
    
    def reset_metrics(self):
        """Resetear métricas"""
        with self._lock:
            for key in self.metrics:
                self.metrics[key] = 0
    
    def set_level(self, level: str):
        """Cambiar nivel de logging"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        if level.upper() in level_map:
            self.logger.setLevel(level_map[level.upper()])
            self.info(f"Logging level changed to {level.upper()}")
        else:
            self.warning(f"Invalid logging level: {level}")

# Instancia global del logger
production_logger = ProductionLogger()

def get_production_logger(name: str = None) -> ProductionLogger:
    """Obtener instancia del logger de producción"""
    if name:
        return ProductionLogger(name)
    return production_logger