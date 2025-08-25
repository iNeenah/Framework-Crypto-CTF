"""
Excepciones personalizadas para Crypto CTF Solver
"""


class CryptoCTFSolverError(Exception):
    """Excepción base para el framework"""
    pass


class ChallengeTimeoutError(CryptoCTFSolverError):
    """Error cuando se agota el tiempo de resolución"""
    
    def __init__(self, message: str = "Tiempo agotado para resolver el desafío", timeout: int = None):
        self.timeout = timeout
        if timeout:
            message = f"{message} (timeout: {timeout}s)"
        super().__init__(message)


class InsufficientDataError(CryptoCTFSolverError):
    """Error cuando no hay suficientes datos para resolver el desafío"""
    
    def __init__(self, message: str = "Datos insuficientes para resolver el desafío", required_data: str = None):
        self.required_data = required_data
        if required_data:
            message = f"{message} (requerido: {required_data})"
        super().__init__(message)


class NetworkConnectionError(CryptoCTFSolverError):
    """Error de conexión de red"""
    
    def __init__(self, message: str = "Error de conexión de red", host: str = None, port: int = None):
        self.host = host
        self.port = port
        if host and port:
            message = f"{message} ({host}:{port})"
        super().__init__(message)


class PluginError(CryptoCTFSolverError):
    """Error específico de plugin"""
    
    def __init__(self, message: str = "Error en plugin", plugin_name: str = None):
        self.plugin_name = plugin_name
        if plugin_name:
            message = f"{message} (plugin: {plugin_name})"
        super().__init__(message)


class FileExtractionError(CryptoCTFSolverError):
    """Error al extraer archivos comprimidos"""
    
    def __init__(self, message: str = "Error al extraer archivo", file_path: str = None):
        self.file_path = file_path
        if file_path:
            message = f"{message} (archivo: {file_path})"
        super().__init__(message)


class ValidationError(CryptoCTFSolverError):
    """Error de validación de datos"""
    
    def __init__(self, message: str = "Error de validación", field: str = None):
        self.field = field
        if field:
            message = f"{message} (campo: {field})"
        super().__init__(message)


class ConfigurationError(CryptoCTFSolverError):
    """Error de configuración"""
    
    def __init__(self, message: str = "Error de configuración", config_key: str = None):
        self.config_key = config_key
        if config_key:
            message = f"{message} (clave: {config_key})"
        super().__init__(message)


class SecurityError(CryptoCTFSolverError):
    """Error de seguridad"""
    
    def __init__(self, message: str = "Error de seguridad", security_check: str = None):
        self.security_check = security_check
        if security_check:
            message = f"{message} (check: {security_check})"
        super().__init__(message)


class ResourceLimitError(CryptoCTFSolverError):
    """Error por exceder límites de recursos"""
    
    def __init__(self, message: str = "Límite de recursos excedido", resource_type: str = None):
        self.resource_type = resource_type
        if resource_type:
            message = f"{message} (recurso: {resource_type})"
        super().__init__(message)


class MLModelError(CryptoCTFSolverError):
    """Error en modelos de Machine Learning"""
    
    def __init__(self, message: str = "Error en modelo ML", model_name: str = None):
        self.model_name = model_name
        if model_name:
            message = f"{message} (modelo: {model_name})"
        super().__init__(message)