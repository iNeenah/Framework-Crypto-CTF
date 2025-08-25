"""
Tests for Security System
"""

import pytest
import tempfile
import time
import os
from pathlib import Path
from unittest.mock import Mock, patch

from src.core.security_manager import (
    SecurityManager, SandboxConfig, ResourceLimits, 
    SecureExecutor, InputValidator, ResourceMonitor
)
from src.models.exceptions import SecurityError, ResourceLimitError
from src.models.data import ChallengeData, SolutionResult


class TestResourceLimits:
    """Tests para límites de recursos"""
    
    def test_resource_limits_creation(self):
        """Test creación de límites de recursos"""
        limits = ResourceLimits(
            max_memory_mb=256,
            max_cpu_time_seconds=60,
            max_file_size_mb=50
        )
        
        assert limits.max_memory_mb == 256
        assert limits.max_cpu_time_seconds == 60
        assert limits.max_file_size_mb == 50
    
    def test_resource_limits_defaults(self):
        """Test valores por defecto de límites"""
        limits = ResourceLimits()
        
        assert limits.max_memory_mb == 512
        assert limits.max_cpu_time_seconds == 300
        assert limits.max_open_files == 100


class TestSandboxConfig:
    """Tests para configuración de sandbox"""
    
    def test_sandbox_config_creation(self):
        """Test creación de configuración de sandbox"""
        config = SandboxConfig(
            enabled=True,
            temp_dir_isolation=True,
            network_isolation=False
        )
        
        assert config.enabled is True
        assert config.temp_dir_isolation is True
        assert config.network_isolation is False
        assert config.resource_limits is not None
    
    def test_sandbox_config_defaults(self):
        """Test valores por defecto de configuración"""
        config = SandboxConfig()
        
        assert config.enabled is True
        assert config.temp_dir_isolation is True
        assert config.filesystem_isolation is True
        assert len(config.allowed_modules) > 0
        assert len(config.blocked_modules) > 0
        
        # Verificar módulos permitidos
        assert 'os' in config.allowed_modules
        assert 'hashlib' in config.allowed_modules
        assert 'Crypto' in config.allowed_modules
        
        # Verificar módulos bloqueados
        assert 'subprocess' in config.blocked_modules
        assert 'socket' in config.blocked_modules


class TestInputValidator:
    """Tests para validador de entrada"""
    
    def test_validate_safe_file_path(self):
        """Test validación de ruta de archivo segura"""
        validator = InputValidator()
        
        safe_paths = [
            "challenge.txt",
            "data/challenge.zip",
            "test.py"
        ]
        
        for path in safe_paths:
            result = validator.validate_file_path(path)
            assert isinstance(result, Path)
    
    def test_validate_dangerous_file_path(self):
        """Test validación de ruta de archivo peligrosa"""
        validator = InputValidator()
        
        dangerous_paths = [
            "../../../etc/passwd",
            "/etc/shadow",
            "../../system32/config",
            "file.exe"  # Extensión no permitida
        ]
        
        for path in dangerous_paths:
            with pytest.raises(SecurityError):
                validator.validate_file_path(path)
    
    def test_validate_network_input_safe(self):
        """Test validación de entrada de red segura"""
        validator = InputValidator()
        
        host, port = validator.validate_network_input("example.com", 1337)
        assert host == "example.com"
        assert port == 1337
    
    def test_validate_network_input_dangerous(self):
        """Test validación de entrada de red peligrosa"""
        validator = InputValidator()
        
        # Puerto inválido
        with pytest.raises(SecurityError):
            validator.validate_network_input("example.com", 70000)
        
        # Host vacío
        with pytest.raises(SecurityError):
            validator.validate_network_input("", 1337)
    
    def test_sanitize_command_safe(self):
        """Test sanitización de comando seguro"""
        validator = InputValidator()
        
        safe_commands = [
            "ls -la",
            "cat file.txt",
            "python script.py"
        ]
        
        for command in safe_commands:
            result = validator.sanitize_command_input(command)
            assert result == command
    
    def test_sanitize_command_dangerous(self):
        """Test sanitización de comando peligroso"""
        validator = InputValidator()
        
        dangerous_commands = [
            "rm -rf /",
            "cat file.txt; rm file.txt",
            "ls | grep secret",
            "sudo su",
            "$(malicious_command)"
        ]
        
        for command in dangerous_commands:
            with pytest.raises(SecurityError):
                validator.sanitize_command_input(command)


class TestSecureExecutor:
    """Tests para executor seguro"""
    
    @pytest.fixture
    def secure_config(self):
        """Configuración segura para tests"""
        return SandboxConfig(
            enabled=True,
            temp_dir_isolation=True,
            resource_limits=ResourceLimits(
                max_memory_mb=100,
                max_cpu_time_seconds=5
            )
        )
    
    @pytest.fixture
    def executor(self, secure_config):
        """Executor seguro para tests"""
        return SecureExecutor(secure_config)
    
    def test_secure_environment_context(self, executor):
        """Test context manager de entorno seguro"""
        original_cwd = os.getcwd()
        
        with executor.secure_environment() as temp_dir:
            if temp_dir:
                assert temp_dir.exists()
                assert temp_dir != Path(original_cwd)
        
        # Verificar que se restauró el directorio original
        assert os.getcwd() == original_cwd
    
    def test_execute_safe_simple_function(self, executor):
        """Test ejecución segura de función simple"""
        def simple_function(x, y):
            return x + y
        
        result = executor.execute_safe(simple_function, 2, 3)
        assert result == 5
    
    def test_execute_safe_with_timeout(self):
        """Test ejecución segura con timeout"""
        config = SandboxConfig(
            enabled=True,
            resource_limits=ResourceLimits(max_cpu_time_seconds=1)
        )
        executor = SecureExecutor(config)
        
        def slow_function():
            time.sleep(2)  # Más lento que el timeout
            return "completed"
        
        with pytest.raises(ResourceLimitError):
            executor.execute_safe(slow_function)
    
    def test_cleanup_temp_dirs(self, executor):
        """Test limpieza de directorios temporales"""
        # Crear algunos directorios temporales
        with executor.secure_environment():
            pass
        
        with executor.secure_environment():
            pass
        
        # Verificar que se pueden limpiar
        executor.cleanup_temp_dirs()
        assert len(executor._temp_dirs) == 0


class TestSecurityManager:
    """Tests para gestor de seguridad"""
    
    @pytest.fixture
    def security_manager(self):
        """Gestor de seguridad para tests"""
        config = SandboxConfig(
            enabled=True,
            resource_limits=ResourceLimits(
                max_memory_mb=100,
                max_cpu_time_seconds=5
            )
        )
        return SecurityManager(config)
    
    def test_security_manager_initialization(self, security_manager):
        """Test inicialización del gestor de seguridad"""
        assert security_manager.config.enabled is True
        assert security_manager.executor is not None
        assert security_manager.validator is not None
        assert 'blocked_operations' in security_manager.stats
    
    def test_validate_challenge_file_safe(self, security_manager):
        """Test validación de archivo de desafío seguro"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b"test content")
            tmp.flush()
            
            result = security_manager.validate_challenge_file(tmp.name)
            assert isinstance(result, Path)
    
    def test_validate_challenge_file_dangerous(self, security_manager):
        """Test validación de archivo de desafío peligroso"""
        with pytest.raises(SecurityError):
            security_manager.validate_challenge_file("../../../etc/passwd")
        
        # Verificar que se incrementó el contador
        assert security_manager.stats['blocked_operations'] > 0
    
    def test_validate_network_connection_safe(self, security_manager):
        """Test validación de conexión de red segura"""
        host, port = security_manager.validate_network_connection("example.com", 1337)
        assert host == "example.com"
        assert port == 1337
    
    def test_validate_network_connection_dangerous(self, security_manager):
        """Test validación de conexión de red peligrosa"""
        with pytest.raises(SecurityError):
            security_manager.validate_network_connection("", 70000)
        
        assert security_manager.stats['blocked_operations'] > 0
    
    def test_execute_plugin_safe_success(self, security_manager):
        """Test ejecución segura de plugin exitosa"""
        # Mock plugin
        mock_plugin = Mock()
        mock_plugin.solve.return_value = SolutionResult(
            success=True,
            solution="test_solution"
        )
        
        # Mock challenge data
        challenge_data = ChallengeData(
            id="test_challenge",
            name="Test Challenge"
        )
        
        result = security_manager.execute_plugin_safe(mock_plugin, challenge_data)
        
        assert result.success is True
        assert result.solution == "test_solution"
        assert security_manager.stats['safe_executions'] > 0
    
    def test_execute_plugin_safe_with_error(self, security_manager):
        """Test ejecución segura de plugin con error"""
        # Mock plugin que lanza excepción
        mock_plugin = Mock()
        mock_plugin.solve.side_effect = Exception("Plugin error")
        
        challenge_data = ChallengeData(
            id="test_challenge",
            name="Test Challenge"
        )
        
        with pytest.raises(Exception):
            security_manager.execute_plugin_safe(mock_plugin, challenge_data)
    
    def test_get_security_stats(self, security_manager):
        """Test obtención de estadísticas de seguridad"""
        stats = security_manager.get_security_stats()
        
        assert 'blocked_operations' in stats
        assert 'resource_violations' in stats
        assert 'security_warnings' in stats
        assert 'safe_executions' in stats
        assert 'sandbox_enabled' in stats
        assert 'resource_limits' in stats
    
    def test_audit_log(self, security_manager):
        """Test registro de auditoría"""
        with patch.object(security_manager.logger, 'info') as mock_log:
            security_manager.audit_log("test_event", {"detail": "test_detail"})
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0][0]
            assert "SECURITY_AUDIT" in call_args
            assert "test_event" in call_args
    
    def test_cleanup_resources(self, security_manager):
        """Test limpieza de recursos"""
        # Ejecutar algo que cree recursos temporales
        with security_manager.executor.secure_environment():
            pass
        
        # Limpiar recursos
        security_manager.cleanup_resources()
        
        # Verificar limpieza
        assert len(security_manager.executor._temp_dirs) == 0


class TestResourceMonitor:
    """Tests para monitor de recursos"""
    
    @pytest.fixture
    def resource_limits(self):
        """Límites de recursos para tests"""
        return ResourceLimits(
            max_memory_mb=50,
            max_cpu_time_seconds=2,
            max_open_files=10
        )
    
    @pytest.fixture
    def monitor(self, resource_limits):
        """Monitor de recursos para tests"""
        return ResourceMonitor(resource_limits)
    
    def test_monitor_initialization(self, monitor):
        """Test inicialización del monitor"""
        assert monitor.limits is not None
        assert not monitor._monitoring
        assert monitor._process is None
    
    @patch('psutil.Process')
    def test_start_stop_monitoring(self, mock_process_class, monitor):
        """Test inicio y parada del monitoreo"""
        mock_process = Mock()
        mock_process.is_running.return_value = True
        mock_process.memory_info.return_value = Mock(rss=1024*1024)  # 1MB
        mock_process.open_files.return_value = []
        mock_process.children.return_value = []
        
        monitor.start_monitoring(mock_process)
        assert monitor._monitoring is True
        
        time.sleep(0.1)  # Permitir que el monitor ejecute
        
        monitor.stop_monitoring()
        assert monitor._monitoring is False


class TestSecurityIntegration:
    """Tests de integración del sistema de seguridad"""
    
    def test_disabled_security(self):
        """Test sistema con seguridad deshabilitada"""
        config = SandboxConfig(enabled=False)
        security_manager = SecurityManager(config)
        
        def test_function():
            return "executed"
        
        result = security_manager.executor.execute_safe(test_function)
        assert result == "executed"
    
    def test_security_with_file_operations(self):
        """Test seguridad con operaciones de archivo"""
        security_manager = SecurityManager()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b"test content")
            tmp.flush()
            
            # Validar archivo
            validated_path = security_manager.validate_challenge_file(tmp.name)
            assert validated_path.exists()
            
            # Limpiar
            os.unlink(tmp.name)
    
    def test_security_stats_tracking(self):
        """Test seguimiento de estadísticas de seguridad"""
        security_manager = SecurityManager()
        
        initial_stats = security_manager.get_security_stats()
        initial_blocked = initial_stats['blocked_operations']
        
        # Intentar operación peligrosa
        try:
            security_manager.validate_challenge_file("../../../etc/passwd")
        except SecurityError:
            pass
        
        updated_stats = security_manager.get_security_stats()
        assert updated_stats['blocked_operations'] > initial_blocked


if __name__ == "__main__":
    pytest.main([__file__])