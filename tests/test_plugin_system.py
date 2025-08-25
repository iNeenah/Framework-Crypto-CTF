"""
Tests para el sistema de plugins
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.plugins.base import CryptoPlugin, MultiTechniquePlugin, AnalysisPlugin
from src.core.plugin_manager import PluginManager
from src.models.data import ChallengeData, SolutionResult, PluginInfo, ChallengeType
from src.models.exceptions import PluginError, ChallengeTimeoutError


class MockPlugin(CryptoPlugin):
    """Plugin mock para tests"""
    
    def _create_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="mock_plugin",
            version="1.0.0",
            description="Plugin de prueba",
            supported_types=[ChallengeType.BASIC_CRYPTO],
            techniques=["mock_technique"]
        )
    
    def can_handle(self, challenge_data: ChallengeData) -> float:
        return 0.8
    
    def solve(self, challenge_data: ChallengeData) -> SolutionResult:
        return SolutionResult(
            success=True,
            flag="CTF{mock_flag}",
            method_used="mock_technique",
            confidence=0.9
        )


class MockFailingPlugin(CryptoPlugin):
    """Plugin que siempre falla para tests"""
    
    def _create_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="failing_plugin",
            version="1.0.0",
            description="Plugin que falla",
            supported_types=[ChallengeType.RSA],
            techniques=["failing_technique"]
        )
    
    def can_handle(self, challenge_data: ChallengeData) -> float:
        return 0.5
    
    def solve(self, challenge_data: ChallengeData) -> SolutionResult:
        return SolutionResult(
            success=False,
            error_message="Mock failure",
            method_used="failing_technique"
        )


class MockMultiTechniquePlugin(MultiTechniquePlugin):
    """Plugin multi-técnica mock para tests"""
    
    def _create_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="multi_plugin",
            version="1.0.0",
            description="Plugin multi-técnica",
            supported_types=[ChallengeType.RSA],
            techniques=["technique1", "technique2"]
        )
    
    def can_handle(self, challenge_data: ChallengeData) -> float:
        return 0.7
    
    def _initialize_techniques(self):
        return {
            "technique1": self._technique1,
            "technique2": self._technique2
        }
    
    def _technique1(self, challenge_data: ChallengeData) -> SolutionResult:
        return SolutionResult(success=False, error_message="Technique 1 failed")
    
    def _technique2(self, challenge_data: ChallengeData) -> SolutionResult:
        return SolutionResult(
            success=True,
            flag="CTF{multi_flag}",
            method_used="technique2",
            confidence=0.8
        )


class MockAnalysisPlugin(AnalysisPlugin):
    """Plugin de análisis mock para tests"""
    
    def _create_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="analysis_plugin",
            version="1.0.0",
            description="Plugin de análisis",
            supported_types=[ChallengeType.UNKNOWN],
            techniques=["analysis"]
        )
    
    def can_handle(self, challenge_data: ChallengeData) -> float:
        return 0.3
    
    def analyze(self, challenge_data: ChallengeData):
        return {
            "file_count": len(challenge_data.files),
            "analysis_type": "mock_analysis"
        }


class TestCryptoPlugin:
    """Tests para CryptoPlugin base"""
    
    @pytest.fixture
    def mock_plugin(self):
        return MockPlugin()
    
    @pytest.fixture
    def sample_challenge(self):
        return ChallengeData(id="test", name="Test Challenge")
    
    def test_plugin_initialization(self, mock_plugin):
        """Test inicialización de plugin"""
        assert mock_plugin._plugin_info.name == "mock_plugin"
        assert mock_plugin._plugin_info.version == "1.0.0"
        assert ChallengeType.BASIC_CRYPTO in mock_plugin._plugin_info.supported_types
    
    def test_get_plugin_info(self, mock_plugin):
        """Test obtener información del plugin"""
        info = mock_plugin.get_plugin_info()
        assert isinstance(info, PluginInfo)
        assert info.name == "mock_plugin"
    
    def test_get_techniques(self, mock_plugin):
        """Test obtener técnicas del plugin"""
        techniques = mock_plugin.get_techniques()
        assert "mock_technique" in techniques
    
    def test_set_timeout(self, mock_plugin):
        """Test establecer timeout"""
        mock_plugin.set_timeout(60)
        assert mock_plugin._timeout == 60
    
    def test_solve_with_timeout_success(self, mock_plugin, sample_challenge):
        """Test resolución exitosa con timeout"""
        result = mock_plugin.solve_with_timeout(sample_challenge)
        
        assert result.success is True
        assert result.flag == "CTF{mock_flag}"
        assert result.plugin_name == "mock_plugin"
        assert result.execution_time > 0
    
    def test_solve_with_timeout_failure(self, sample_challenge):
        """Test resolución fallida con timeout"""
        failing_plugin = MockFailingPlugin()
        result = failing_plugin.solve_with_timeout(sample_challenge)
        
        assert result.success is False
        assert result.error_message == "Mock failure"
        assert result.plugin_name == "failing_plugin"
    
    @patch('time.time')
    def test_timeout_exceeded(self, mock_time, mock_plugin, sample_challenge):
        """Test exceder timeout"""
        # Simular timeout
        mock_time.side_effect = [0, 400]  # Inicio y después de 400s
        mock_plugin.set_timeout(300)  # 5 minutos
        
        # Mock del método solve para que llame _check_timeout
        original_solve = mock_plugin.solve
        def solve_with_timeout_check(challenge_data):
            mock_plugin._check_timeout()
            return original_solve(challenge_data)
        
        mock_plugin.solve = solve_with_timeout_check
        
        result = mock_plugin.solve_with_timeout(sample_challenge)
        
        assert result.success is False
        assert "Timeout excedido" in result.error_message
    
    def test_read_file_content(self, mock_plugin):
        """Test utilidad de lectura de archivo"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            tmp.write("test content")
            tmp.flush()
            
            content = mock_plugin._read_file_content(tmp.name)
            assert content == "test content"
    
    def test_read_file_bytes(self, mock_plugin):
        """Test utilidad de lectura de archivo binario"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp:
            tmp.write(b"binary content")
            tmp.flush()
            
            content = mock_plugin._read_file_bytes(tmp.name)
            assert content == b"binary content"
    
    def test_create_success_result(self, mock_plugin):
        """Test crear resultado exitoso"""
        result = mock_plugin._create_success_result(
            flag="CTF{test}",
            method="test_method",
            confidence=0.9,
            extra_data="test"
        )
        
        assert result.success is True
        assert result.flag == "CTF{test}"
        assert result.method_used == "test_method"
        assert result.confidence == 0.9
        assert result.details["extra_data"] == "test"
    
    def test_create_failure_result(self, mock_plugin):
        """Test crear resultado fallido"""
        result = mock_plugin._create_failure_result(
            error_message="Test error",
            method="test_method",
            extra_info="test"
        )
        
        assert result.success is False
        assert result.error_message == "Test error"
        assert result.method_used == "test_method"
        assert result.details["extra_info"] == "test"


class TestMultiTechniquePlugin:
    """Tests para MultiTechniquePlugin"""
    
    @pytest.fixture
    def multi_plugin(self):
        return MockMultiTechniquePlugin()
    
    @pytest.fixture
    def sample_challenge(self):
        return ChallengeData(id="test", name="Test Challenge")
    
    def test_initialization(self, multi_plugin):
        """Test inicialización de plugin multi-técnica"""
        assert len(multi_plugin._techniques) == 2
        assert "technique1" in multi_plugin._techniques
        assert "technique2" in multi_plugin._techniques
    
    def test_get_available_techniques(self, multi_plugin):
        """Test obtener técnicas disponibles"""
        techniques = multi_plugin.get_available_techniques()
        assert "technique1" in techniques
        assert "technique2" in techniques
    
    def test_solve_with_multiple_techniques(self, multi_plugin, sample_challenge):
        """Test resolución con múltiples técnicas"""
        result = multi_plugin.solve_with_timeout(sample_challenge)
        
        # Debería usar technique2 ya que technique1 falla
        assert result.success is True
        assert result.flag == "CTF{multi_flag}"
        assert "technique2" in result.method_used


class TestAnalysisPlugin:
    """Tests para AnalysisPlugin"""
    
    @pytest.fixture
    def analysis_plugin(self):
        return MockAnalysisPlugin()
    
    @pytest.fixture
    def sample_challenge(self):
        return ChallengeData(id="test", name="Test Challenge")
    
    def test_solve_returns_analysis(self, analysis_plugin, sample_challenge):
        """Test que solve retorna análisis"""
        result = analysis_plugin.solve(sample_challenge)
        
        assert result.success is False  # Los plugins de análisis no resuelven
        assert "analysis" in result.method_used
        assert "file_count" in result.details
        assert result.details["analysis_type"] == "mock_analysis"


class TestPluginManager:
    """Tests para PluginManager"""
    
    @pytest.fixture
    def plugin_manager(self):
        # Crear manager sin cargar plugins automáticamente
        manager = PluginManager.__new__(PluginManager)
        manager.logger = Mock()
        manager._plugins = {}
        manager._plugin_classes = {}
        manager._plugin_info = {}
        return manager
    
    def test_register_plugin_class(self, plugin_manager):
        """Test registro de clase de plugin"""
        with patch('src.utils.config.config') as mock_config:
            mock_config.plugins.enabled_plugins = ["mock_plugin"]
            
            plugin_manager._register_plugin_class("MockPlugin", MockPlugin)
            
            assert "mock_plugin" in plugin_manager._plugins
            assert "mock_plugin" in plugin_manager._plugin_info
            assert isinstance(plugin_manager._plugins["mock_plugin"], MockPlugin)
    
    def test_get_available_plugins(self, plugin_manager):
        """Test obtener plugins disponibles"""
        # Agregar plugins mock
        plugin_manager._plugins["plugin1"] = Mock()
        plugin_manager._plugins["plugin2"] = Mock()
        
        available = plugin_manager.get_available_plugins()
        assert "plugin1" in available
        assert "plugin2" in available
    
    def test_get_plugin_info(self, plugin_manager):
        """Test obtener información de plugin"""
        mock_info = PluginInfo(
            name="test",
            version="1.0",
            description="Test",
            supported_types=[ChallengeType.RSA]
        )
        plugin_manager._plugin_info["test"] = mock_info
        
        info = plugin_manager.get_plugin_info("test")
        assert info == mock_info
        
        # Plugin inexistente
        assert plugin_manager.get_plugin_info("nonexistent") is None
    
    def test_get_plugin(self, plugin_manager):
        """Test obtener instancia de plugin"""
        mock_plugin = Mock()
        plugin_manager._plugins["test"] = mock_plugin
        
        plugin = plugin_manager.get_plugin("test")
        assert plugin == mock_plugin
        
        # Plugin inexistente
        assert plugin_manager.get_plugin("nonexistent") is None
    
    def test_get_plugins_for_type(self, plugin_manager):
        """Test obtener plugins por tipo"""
        # Crear plugin info mock
        rsa_info = PluginInfo(
            name="rsa_plugin",
            version="1.0",
            description="RSA Plugin",
            supported_types=[ChallengeType.RSA],
            priority=80
        )
        
        basic_info = PluginInfo(
            name="basic_plugin",
            version="1.0",
            description="Basic Plugin",
            supported_types=[ChallengeType.BASIC_CRYPTO],
            priority=60
        )
        
        plugin_manager._plugin_info["rsa_plugin"] = rsa_info
        plugin_manager._plugin_info["basic_plugin"] = basic_info
        plugin_manager._plugins["rsa_plugin"] = Mock()
        plugin_manager._plugins["basic_plugin"] = Mock()
        
        # Obtener plugins para RSA
        rsa_plugins = plugin_manager.get_plugins_for_type(ChallengeType.RSA)
        assert len(rsa_plugins) == 1
        assert rsa_plugins[0][0] == "rsa_plugin"
        assert rsa_plugins[0][2] == 0.8  # priority / 100
    
    def test_select_best_plugins(self, plugin_manager):
        """Test selección de mejores plugins"""
        # Crear plugins mock
        plugin1 = Mock()
        plugin1.can_handle.return_value = 0.9
        plugin2 = Mock()
        plugin2.can_handle.return_value = 0.5
        plugin3 = Mock()
        plugin3.can_handle.return_value = 0.0  # No puede manejar
        
        plugin_manager._plugins = {
            "plugin1": plugin1,
            "plugin2": plugin2,
            "plugin3": plugin3
        }
        
        challenge = ChallengeData(id="test", name="test")
        best_plugins = plugin_manager.select_best_plugins(challenge, max_plugins=2)
        
        assert len(best_plugins) == 2
        assert best_plugins[0][0] == "plugin1"  # Mayor confianza primero
        assert best_plugins[0][2] == 0.9
        assert best_plugins[1][0] == "plugin2"
        assert best_plugins[1][2] == 0.5
    
    def test_solve_with_plugin_success(self, plugin_manager):
        """Test resolver con plugin específico"""
        mock_plugin = Mock()
        mock_result = SolutionResult(success=True, flag="CTF{test}")
        mock_plugin.solve_with_timeout.return_value = mock_result
        
        plugin_manager._plugins["test_plugin"] = mock_plugin
        
        challenge = ChallengeData(id="test", name="test")
        result = plugin_manager.solve_with_plugin("test_plugin", challenge)
        
        assert result.success is True
        assert result.flag == "CTF{test}"
        mock_plugin.set_timeout.assert_called_once()
        mock_plugin.solve_with_timeout.assert_called_once_with(challenge)
    
    def test_solve_with_plugin_not_found(self, plugin_manager):
        """Test resolver con plugin inexistente"""
        challenge = ChallengeData(id="test", name="test")
        
        with pytest.raises(PluginError, match="Plugin no encontrado"):
            plugin_manager.solve_with_plugin("nonexistent", challenge)
    
    def test_solve_with_best_plugins(self, plugin_manager):
        """Test resolver con mejores plugins"""
        # Mock select_best_plugins
        plugin_manager.select_best_plugins = Mock()
        plugin_manager.select_best_plugins.return_value = [
            ("plugin1", Mock(), 0.9),
            ("plugin2", Mock(), 0.7)
        ]
        
        # Mock solve_with_plugin
        plugin_manager.solve_with_plugin = Mock()
        plugin_manager.solve_with_plugin.side_effect = [
            SolutionResult(success=False, error_message="Failed"),
            SolutionResult(success=True, flag="CTF{success}")
        ]
        
        challenge = ChallengeData(id="test", name="test")
        results = plugin_manager.solve_with_best_plugins(challenge)
        
        assert len(results) == 2
        assert results[0].success is False
        assert results[1].success is True
        assert results[1].flag == "CTF{success}"
    
    def test_reload_plugin(self, plugin_manager):
        """Test recargar plugin"""
        # Crear plugin mock
        plugin_class = Mock(return_value=Mock())
        plugin_class.return_value.get_plugin_info.return_value = PluginInfo(
            name="test", version="1.0", description="Test", supported_types=[]
        )
        
        plugin_manager._plugin_classes["test"] = plugin_class
        plugin_manager._plugins["test"] = Mock()
        plugin_manager._plugin_info["test"] = Mock()
        
        # Recargar
        success = plugin_manager.reload_plugin("test")
        
        assert success is True
        plugin_class.assert_called()  # Nueva instancia creada
    
    def test_get_plugin_statistics(self, plugin_manager):
        """Test obtener estadísticas de plugins"""
        # Crear plugin info mock
        info1 = PluginInfo(
            name="plugin1",
            version="1.0",
            description="Plugin 1",
            supported_types=[ChallengeType.RSA],
            enabled=True
        )
        info2 = PluginInfo(
            name="plugin2",
            version="2.0",
            description="Plugin 2",
            supported_types=[ChallengeType.BASIC_CRYPTO],
            enabled=False
        )
        
        plugin_manager._plugin_info = {"plugin1": info1, "plugin2": info2}
        plugin_manager._plugins = {"plugin1": Mock(), "plugin2": Mock()}
        
        stats = plugin_manager.get_plugin_statistics()
        
        assert stats["total_plugins"] == 2
        assert stats["enabled_plugins"] == 1
        assert "rsa" in stats["plugins_by_type"]
        assert "basic_crypto" in stats["plugins_by_type"]
        assert len(stats["plugin_details"]) == 2


if __name__ == "__main__":
    pytest.main([__file__])