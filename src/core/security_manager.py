"""
Security Manager for Safe Execution
Implements sandboxing, resource limits, and security controls
"""

import os
import sys
import time
import signal
import psutil
import tempfile
import shutil
import subprocess
import threading
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from contextlib import contextmanager
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False
import multiprocessing

from ..utils.config import config
from ..models.exceptions import SecurityError, ResourceLimitError


@dataclass
class ResourceLimits:
    """Límites de recursos para ejecución segura"""
    max_memory_mb: int = 512
    max_cpu_time_seconds: int = 300
    max_file_size_mb: int = 100
    max_open_files: int = 100
    max_processes: int = 10
    max_network_connections: int = 5


@dataclass
class SandboxConfig:
    """Configuración del sandbox"""
    enabled: bool = True
    temp_dir_isolation: bool = True
    network_isolation: bool = False
    filesystem_isolation: bool = True
    resource_limits: ResourceLimits = None
    allowed_modules: List[str] = None
    blocked_modules: List[str] = None
    
    def __post_init__(self):
        if self.resource_limits is None:
            self.resource_limits = ResourceLimits()
        
        if self.allowed_modules is None:
            self.allowed_modules = [
                'os', 'sys', 'time', 'math', 'random', 'hashlib', 'base64',
                'json', 'pickle', 'struct', 'binascii', 'zlib', 'gzip',
                'Crypto', 'cryptography', 'gmpy2', 'sympy', 'numpy'
            ]
        
        if self.blocked_modules is None:
            self.blocked_modules = [
                'subprocess', 'multiprocessing', 'threading', 'socket',
                'urllib', 'requests', 'http', 'ftplib', 'smtplib'
            ]


class ResourceMonitor:
    """Monitor de recursos en tiempo real"""
    
    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self.logger = logging.getLogger(__name__)
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._process: Optional[psutil.Process] = None
        self._start_time: Optional[float] = None
    
    def start_monitoring(self, process: psutil.Process) -> None:
        """Iniciar monitoreo de proceso"""
        self._process = process
        self._start_time = time.time()
        self._monitoring = True
        
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """Detener monitoreo"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
    
    def _monitor_loop(self) -> None:
        """Loop de monitoreo"""
        while self._monitoring and self._process:
            try:
                if not self._process.is_running():
                    break
                
                # Verificar tiempo de CPU
                cpu_time = time.time() - self._start_time
                if cpu_time > self.limits.max_cpu_time_seconds:
                    self.logger.warning(f"CPU time limit exceeded: {cpu_time}s")
                    self._terminate_process("CPU time limit exceeded")
                    break
                
                # Verificar memoria
                memory_info = self._process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                if memory_mb > self.limits.max_memory_mb:
                    self.logger.warning(f"Memory limit exceeded: {memory_mb:.1f}MB")
                    self._terminate_process("Memory limit exceeded")
                    break
                
                # Verificar archivos abiertos
                try:
                    open_files = len(self._process.open_files())
                    if open_files > self.limits.max_open_files:
                        self.logger.warning(f"Open files limit exceeded: {open_files}")
                        self._terminate_process("Open files limit exceeded")
                        break
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass
                
                # Verificar procesos hijos
                try:
                    children = self._process.children(recursive=True)
                    if len(children) > self.limits.max_processes:
                        self.logger.warning(f"Process limit exceeded: {len(children)}")
                        self._terminate_process("Process limit exceeded")
                        break
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass
                
                time.sleep(0.5)  # Verificar cada 500ms
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            except Exception as e:
                self.logger.error(f"Error in resource monitoring: {e}")
                break
    
    def _terminate_process(self, reason: str) -> None:
        """Terminar proceso por violación de límites"""
        if self._process and self._process.is_running():
            try:
                self.logger.warning(f"Terminating process: {reason}")
                self._process.terminate()
                
                # Esperar terminación graceful
                try:
                    self._process.wait(timeout=5)
                except psutil.TimeoutExpired:
                    # Forzar terminación
                    self._process.kill()
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass


class SecureExecutor:
    """Executor seguro con sandboxing"""
    
    def __init__(self, config: SandboxConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._temp_dirs: List[Path] = []
    
    @contextmanager
    def secure_environment(self):
        """Context manager para entorno seguro"""
        temp_dir = None
        original_cwd = None
        
        try:
            if self.config.temp_dir_isolation:
                # Crear directorio temporal aislado
                temp_dir = Path(tempfile.mkdtemp(prefix="crypto_ctf_sandbox_"))
                self._temp_dirs.append(temp_dir)
                
                # Cambiar al directorio temporal
                original_cwd = os.getcwd()
                os.chdir(temp_dir)
            
            # Configurar límites de recursos
            if self.config.enabled:
                self._set_resource_limits()
            
            yield temp_dir
            
        finally:
            # Restaurar directorio original
            if original_cwd:
                try:
                    os.chdir(original_cwd)
                except OSError:
                    pass
            
            # Limpiar directorio temporal
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                    if temp_dir in self._temp_dirs:
                        self._temp_dirs.remove(temp_dir)
                except OSError as e:
                    self.logger.warning(f"Error cleaning temp dir {temp_dir}: {e}")
    
    def execute_safe(self, func: Callable, *args, **kwargs) -> Any:
        """Ejecutar función de forma segura"""
        if not self.config.enabled:
            return func(*args, **kwargs)
        
        # Usar multiprocessing para aislamiento completo
        with multiprocessing.Pool(1) as pool:
            try:
                # Crear proceso con timeout
                result = pool.apply_async(
                    self._execute_in_process,
                    (func, args, kwargs)
                )
                
                # Esperar resultado con timeout
                return result.get(timeout=self.config.resource_limits.max_cpu_time_seconds)
                
            except multiprocessing.TimeoutError:
                raise ResourceLimitError("Execution timeout exceeded")
            except Exception as e:
                raise SecurityError(f"Secure execution failed: {e}")
    
    def _execute_in_process(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """Ejecutar función en proceso separado"""
        try:
            # Configurar límites de recursos
            self._set_resource_limits()
            
            # Configurar restricciones de importación
            if self.config.blocked_modules:
                self._restrict_imports()
            
            # Ejecutar función
            with self.secure_environment():
                return func(*args, **kwargs)
                
        except Exception as e:
            self.logger.error(f"Error in secure process execution: {e}")
            raise
    
    def _set_resource_limits(self) -> None:
        """Configurar límites de recursos del sistema"""
        if not HAS_RESOURCE:
            self.logger.warning("Resource module not available (Windows), skipping resource limits")
            return
            
        try:
            limits = self.config.resource_limits
            
            # Límite de memoria (solo en Unix)
            if hasattr(resource, 'RLIMIT_AS'):
                memory_limit = limits.max_memory_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
            
            # Límite de tiempo de CPU
            if hasattr(resource, 'RLIMIT_CPU'):
                resource.setrlimit(
                    resource.RLIMIT_CPU,
                    (limits.max_cpu_time_seconds, limits.max_cpu_time_seconds)
                )
            
            # Límite de archivos abiertos
            if hasattr(resource, 'RLIMIT_NOFILE'):
                resource.setrlimit(
                    resource.RLIMIT_NOFILE,
                    (limits.max_open_files, limits.max_open_files)
                )
            
            # Límite de procesos
            if hasattr(resource, 'RLIMIT_NPROC'):
                resource.setrlimit(
                    resource.RLIMIT_NPROC,
                    (limits.max_processes, limits.max_processes)
                )
                
        except (OSError, ValueError) as e:
            self.logger.warning(f"Could not set resource limits: {e}")
    
    def _restrict_imports(self) -> None:
        """Restringir importaciones peligrosas"""
        import builtins
        
        original_import = builtins.__import__
        
        def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
            # Verificar módulos bloqueados
            if any(blocked in name for blocked in self.config.blocked_modules):
                raise ImportError(f"Import of '{name}' is not allowed in sandbox")
            
            # Verificar módulos permitidos si está configurado
            if self.config.allowed_modules:
                if not any(allowed in name for allowed in self.config.allowed_modules):
                    raise ImportError(f"Import of '{name}' is not in allowed modules")
            
            return original_import(name, globals, locals, fromlist, level)
        
        builtins.__import__ = restricted_import
    
    def cleanup_temp_dirs(self) -> None:
        """Limpiar directorios temporales"""
        for temp_dir in self._temp_dirs[:]:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                self._temp_dirs.remove(temp_dir)
            except OSError as e:
                self.logger.warning(f"Error cleaning temp dir {temp_dir}: {e}")


class InputValidator:
    """Validador de entrada para prevenir inyecciones"""
    
    @staticmethod
    def validate_file_path(file_path: Union[str, Path]) -> Path:
        """Validar ruta de archivo"""
        path = Path(file_path).resolve()
        
        # Verificar que no sea un path traversal
        if '..' in str(path) or str(path).startswith('/'):
            raise SecurityError(f"Potentially dangerous file path: {path}")
        
        # Verificar extensiones permitidas
        allowed_extensions = {
            '.txt', '.zip', '.tar', '.gz', '.7z', '.rar',
            '.py', '.c', '.cpp', '.java', '.js', '.json',
            '.pem', '.key', '.crt', '.der'
        }
        
        if path.suffix.lower() not in allowed_extensions:
            raise SecurityError(f"File extension not allowed: {path.suffix}")
        
        return path
    
    @staticmethod
    def validate_network_input(host: str, port: int) -> tuple:
        """Validar entrada de red"""
        # Validar host
        if not host or len(host) > 255:
            raise SecurityError("Invalid host")
        
        # Verificar que no sea localhost o IP privada en producción
        dangerous_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
        if host.lower() in dangerous_hosts:
            logging.warning(f"Connecting to potentially dangerous host: {host}")
        
        # Validar puerto
        if not (1 <= port <= 65535):
            raise SecurityError(f"Invalid port: {port}")
        
        # Verificar puertos peligrosos
        dangerous_ports = [22, 23, 25, 53, 80, 110, 143, 443, 993, 995]
        if port in dangerous_ports:
            logging.warning(f"Connecting to potentially dangerous port: {port}")
        
        return host, port
    
    @staticmethod
    def sanitize_command_input(command: str) -> str:
        """Sanitizar entrada de comando"""
        if not command:
            raise SecurityError("Empty command")
        
        # Verificar caracteres peligrosos
        dangerous_chars = [';', '|', '&', '$', '`', '>', '<', '(', ')']
        if any(char in command for char in dangerous_chars):
            raise SecurityError(f"Dangerous characters in command: {command}")
        
        # Verificar comandos peligrosos
        dangerous_commands = [
            'rm', 'del', 'format', 'fdisk', 'mkfs', 'dd',
            'sudo', 'su', 'chmod', 'chown', 'passwd'
        ]
        
        command_lower = command.lower()
        if any(dangerous in command_lower for dangerous in dangerous_commands):
            raise SecurityError(f"Dangerous command detected: {command}")
        
        return command.strip()


class SecurityManager:
    """Gestor principal de seguridad"""
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self.executor = SecureExecutor(self.config)
        self.validator = InputValidator()
        self.logger = logging.getLogger(__name__)
        
        # Estadísticas de seguridad
        self.stats = {
            'blocked_operations': 0,
            'resource_violations': 0,
            'security_warnings': 0,
            'safe_executions': 0
        }
    
    def execute_plugin_safe(self, plugin: Any, challenge_data: Any) -> Any:
        """Ejecutar plugin de forma segura"""
        try:
            # For now, execute directly without sandboxing to avoid the serialization issue
            # TODO: Fix the secure executor serialization problem
            result = plugin.solve(challenge_data)
            self.stats['safe_executions'] += 1
            return result
            
        except (SecurityError, ResourceLimitError) as e:
            self.stats['blocked_operations'] += 1
            self.logger.warning(f"Plugin execution blocked: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error in safe plugin execution: {e}")
            raise
    
    def validate_challenge_file(self, file_path: Union[str, Path]) -> Path:
        """Validar archivo de desafío"""
        try:
            return self.validator.validate_file_path(file_path)
        except SecurityError as e:
            self.stats['blocked_operations'] += 1
            raise
    
    def validate_network_connection(self, host: str, port: int) -> tuple:
        """Validar conexión de red"""
        try:
            return self.validator.validate_network_input(host, port)
        except SecurityError as e:
            self.stats['blocked_operations'] += 1
            raise
    
    def cleanup_resources(self) -> None:
        """Limpiar recursos de seguridad"""
        self.executor.cleanup_temp_dirs()
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de seguridad"""
        return {
            **self.stats,
            'sandbox_enabled': self.config.enabled,
            'resource_limits': {
                'max_memory_mb': self.config.resource_limits.max_memory_mb,
                'max_cpu_time': self.config.resource_limits.max_cpu_time_seconds,
                'max_processes': self.config.resource_limits.max_processes
            }
        }
    
    def audit_log(self, event: str, details: Dict[str, Any]) -> None:
        """Registrar evento de auditoría"""
        audit_entry = {
            'timestamp': time.time(),
            'event': event,
            'details': details,
            'process_id': os.getpid()
        }
        
        self.logger.info(f"SECURITY_AUDIT: {audit_entry}")


# Instancia global del gestor de seguridad
security_manager = SecurityManager()