#!/usr/bin/env python3
"""
Sistema robusto de manejo de errores para producción
"""
import functools
import traceback
import sys
from typing import Any, Callable, Dict, Optional, Type, Union
from datetime import datetime
import json

from .production_logging import get_production_logger

logger = get_production_logger("error_handler")

class CryptoSolverError(Exception):
    """Excepción base para el sistema"""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "GENERIC_ERROR"
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()

class PluginError(CryptoSolverError):
    """Error específico de plugins"""
    def __init__(self, plugin_name: str, message: str, details: Dict = None):
        super().__init__(message, "PLUGIN_ERROR", details)
        self.plugin_name = plugin_name

class MLError(CryptoSolverError):
    """Error específico de Machine Learning"""
    def __init__(self, message: str, model_name: str = None, details: Dict = None):
        super().__init__(message, "ML_ERROR", details)
        self.model_name = model_name

class ValidationError(CryptoSolverError):
    """Error de validación de entrada"""
    def __init__(self, field: str, message: str, value: Any = None):
        super().__init__(f"Validation error in {field}: {message}", "VALIDATION_ERROR")
        self.field = field
        self.value = value

class SecurityError(CryptoSolverError):
    """Error de seguridad"""
    def __init__(self, message: str, severity: str = "MEDIUM", details: Dict = None):
        super().__init__(message, "SECURITY_ERROR", details)
        self.severity = severity

class ResourceError(CryptoSolverError):
    """Error de recursos (memoria, tiempo, etc.)"""
    def __init__(self, resource_type: str, message: str, details: Dict = None):
        super().__init__(message, "RESOURCE_ERROR", details)
        self.resource_type = resource_type

class NetworkError(CryptoSolverError):
    """Error de red"""
    def __init__(self, message: str, host: str = None, port: int = None, details: Dict = None):
        super().__init__(message, "NETWORK_ERROR", details)
        self.host = host
        self.port = port

class ErrorHandler:
    """Manejador centralizado de errores"""
    
    def __init__(self):
        self.error_counts = {}
        self.error_history = []
        self.max_history = 1000
    
    def handle_error(self, error: Exception, context: Dict = None) -> Dict[str, Any]:
        """Manejar error de forma centralizada"""
        error_info = {
            'type': type(error).__name__,
            'message': str(error),
            'timestamp': datetime.now().isoformat(),
            'context': context or {},
            'traceback': traceback.format_exc()
        }
        
        # Agregar información específica si es nuestro error personalizado
        if isinstance(error, CryptoSolverError):
            error_info.update({
                'error_code': error.error_code,
                'details': error.details,
                'custom_error': True
            })
        
        # Actualizar contadores
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Agregar al historial
        self.error_history.append(error_info)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
        
        # Log según severidad
        if isinstance(error, (SecurityError, ResourceError)):
            logger.critical(f"Critical error: {error.message}", error, error_info)
        elif isinstance(error, (PluginError, MLError, NetworkError)):
            logger.error(f"System error: {error.message}", error, error_info)
        elif isinstance(error, ValidationError):
            logger.warning(f"Validation error: {error.message}", extra_data=error_info)
        else:
            logger.error(f"Unhandled error: {str(error)}", error, error_info)
        
        return error_info
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de errores"""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_counts': self.error_counts.copy(),
            'recent_errors': len(self.error_history),
            'most_common': max(self.error_counts.items(), key=lambda x: x[1]) if self.error_counts else None
        }
    
    def clear_history(self):
        """Limpiar historial de errores"""
        self.error_history.clear()
        logger.info("Error history cleared")

# Instancia global
error_handler = ErrorHandler()

def handle_exceptions(
    default_return: Any = None,
    reraise: bool = False,
    log_level: str = "ERROR",
    context: Dict = None
):
    """Decorador para manejo automático de excepciones"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Crear contexto con información de la función
                func_context = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                }
                
                if context:
                    func_context.update(context)
                
                # Manejar error
                error_handler.handle_error(e, func_context)
                
                if reraise:
                    raise
                
                return default_return
        
        return wrapper
    return decorator

def safe_execute(func: Callable, *args, default_return: Any = None, **kwargs) -> Any:
    """Ejecutar función de forma segura"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_error(e, {
            'function': func.__name__ if hasattr(func, '__name__') else str(func),
            'args': str(args)[:100],  # Limitar longitud
            'kwargs': str(kwargs)[:100]
        })
        return default_return

def validate_input(data: Any, validator: Callable, field_name: str = "input") -> Any:
    """Validar entrada de forma segura"""
    try:
        if not validator(data):
            raise ValidationError(field_name, f"Validation failed for value: {data}", data)
        return data
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(field_name, f"Validation error: {str(e)}", data)

def require_not_none(value: Any, field_name: str) -> Any:
    """Validar que un valor no sea None"""
    if value is None:
        raise ValidationError(field_name, "Value cannot be None")
    return value

def require_type(value: Any, expected_type: Type, field_name: str) -> Any:
    """Validar tipo de dato"""
    if not isinstance(value, expected_type):
        raise ValidationError(
            field_name, 
            f"Expected {expected_type.__name__}, got {type(value).__name__}",
            value
        )
    return value

def require_range(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float], field_name: str) -> Union[int, float]:
    """Validar rango numérico"""
    if not (min_val <= value <= max_val):
        raise ValidationError(
            field_name,
            f"Value {value} not in range [{min_val}, {max_val}]",
            value
        )
    return value

def require_length(value: str, min_len: int = None, max_len: int = None, field_name: str = "string") -> str:
    """Validar longitud de string"""
    if min_len is not None and len(value) < min_len:
        raise ValidationError(field_name, f"String too short (min: {min_len})", value)
    
    if max_len is not None and len(value) > max_len:
        raise ValidationError(field_name, f"String too long (max: {max_len})", value)
    
    return value

class CircuitBreaker:
    """Circuit breaker para prevenir cascadas de errores"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Ejecutar función con circuit breaker"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise ResourceError("circuit_breaker", "Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Verificar si debemos intentar resetear"""
        if self.last_failure_time is None:
            return True
        
        return (datetime.now().timestamp() - self.last_failure_time) > self.recovery_timeout
    
    def _on_success(self):
        """Manejar éxito"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Manejar fallo"""
        self.failure_count += 1
        self.last_failure_time = datetime.now().timestamp()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

def create_error_response(error: Exception, request_id: str = None) -> Dict[str, Any]:
    """Crear respuesta de error estandarizada"""
    response = {
        'success': False,
        'error': {
            'type': type(error).__name__,
            'message': str(error),
            'timestamp': datetime.now().isoformat()
        }
    }
    
    if request_id:
        response['request_id'] = request_id
    
    if isinstance(error, CryptoSolverError):
        response['error'].update({
            'code': error.error_code,
            'details': error.details
        })
    
    return response

# Configurar manejo global de excepciones no capturadas
def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    """Manejar excepciones no capturadas"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Permitir Ctrl+C
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.critical(
        "Uncaught exception",
        exc_value,
        {
            'type': exc_type.__name__,
            'traceback': ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        }
    )

# Instalar el manejador global
sys.excepthook = handle_uncaught_exception