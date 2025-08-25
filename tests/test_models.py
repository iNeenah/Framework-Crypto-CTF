"""
Tests unitarios para modelos de datos
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from src.models.data import (
    ChallengeData, NetworkInfo, SolutionResult, FileInfo, PluginInfo,
    ChallengeType, DifficultyLevel
)
from src.models.exceptions import (
    ChallengeTimeoutError, InsufficientDataError, NetworkConnectionError,
    PluginError, ValidationError
)


class TestNetworkInfo:
    """Tests para NetworkInfo"""
    
    def test_valid_network_info(self):
        """Test creación válida de NetworkInfo"""
        net_info = NetworkInfo(host="example.com", port=1337)
        assert net_info.host == "example.com"
        assert net_info.port == 1337
        assert net_info.protocol == "tcp"
        assert net_info.timeout == 30
        assert net_info.ssl is False
    
    def test_invalid_protocol(self):
        """Test protocolo inválido"""
        with pytest.raises(ValueError, match="Protocolo no soportado"):
            NetworkInfo(host="example.com", port=1337, protocol="invalid")
    
    def test_invalid_port(self):
        """Test puerto inválido"""
        with pytest.raises(ValueError, match="Puerto inválido"):
            NetworkInfo(host="example.com", port=70000)
        
        with pytest.raises(ValueError, match="Puerto inválido"):
            NetworkInfo(host="example.com", port=0)
    
    def test_to_dict(self):
        """Test conversión a diccionario"""
        net_info = NetworkInfo(host="example.com", port=1337, ssl=True)
        data = net_info.to_dict()
        
        assert data["host"] == "example.com"
        assert data["port"] == 1337
        assert data["ssl"] is True
    
    def test_from_dict(self):
        """Test creación desde diccionario"""
        data = {
            "host": "example.com",
            "port": 1337,
            "protocol": "https",
            "ssl": True
        }
        net_info = NetworkInfo.from_dict(data)
        
        assert net_info.host == "example.com"
        assert net_info.port == 1337
        assert net_info.protocol == "https"
        assert net_info.ssl is True


class TestFileInfo:
    """Tests para FileInfo"""
    
    def test_file_info_creation(self):
        """Test creación de FileInfo"""
        with tempfile.NamedTemporaryFile() as tmp:
            file_info = FileInfo(
                path=Path(tmp.name),
                size=1024,
                mime_type="text/plain"
            )
            
            assert file_info.path == Path(tmp.name)
            assert file_info.size == 1024
            assert file_info.mime_type == "text/plain"
    
    def test_string_path_conversion(self):
        """Test conversión de string a Path"""
        file_info = FileInfo(path="/tmp/test.txt", size=100)
        assert isinstance(file_info.path, Path)
        assert str(file_info.path) == "/tmp/test.txt"
    
    def test_to_from_dict(self):
        """Test serialización/deserialización"""
        original = FileInfo(
            path="/tmp/test.txt",
            size=1024,
            mime_type="text/plain",
            hash_md5="abc123"
        )
        
        data = original.to_dict()
        restored = FileInfo.from_dict(data)
        
        assert restored.path == original.path
        assert restored.size == original.size
        assert restored.mime_type == original.mime_type
        assert restored.hash_md5 == original.hash_md5


class TestChallengeData:
    """Tests para ChallengeData"""
    
    def test_basic_challenge_creation(self):
        """Test creación básica de desafío"""
        challenge = ChallengeData(id="test-1", name="Test Challenge")
        
        assert challenge.id == "test-1"
        assert challenge.name == "Test Challenge"
        assert challenge.files == []
        assert challenge.network_info is None
        assert challenge.challenge_type is None
    
    def test_invalid_id(self):
        """Test ID inválido"""
        with pytest.raises(ValueError, match="ID del desafío debe ser una cadena no vacía"):
            ChallengeData(id="", name="Test")
        
        with pytest.raises(ValueError, match="ID del desafío debe ser una cadena no vacía"):
            ChallengeData(id=None, name="Test")
    
    def test_enum_conversion(self):
        """Test conversión automática de enums"""
        challenge = ChallengeData(
            id="test-1",
            name="Test",
            challenge_type="rsa",
            difficulty=3
        )
        
        assert challenge.challenge_type == ChallengeType.RSA
        assert challenge.difficulty == DifficultyLevel.MEDIUM
    
    def test_invalid_enum_conversion(self):
        """Test conversión de enum inválido"""
        challenge = ChallengeData(
            id="test-1",
            name="Test",
            challenge_type="invalid_type"
        )
        
        assert challenge.challenge_type == ChallengeType.UNKNOWN
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    def test_add_file(self, mock_stat, mock_exists):
        """Test agregar archivo"""
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 1024
        
        challenge = ChallengeData(id="test-1", name="Test")
        challenge.add_file("/tmp/test.txt", mime_type="text/plain")
        
        assert len(challenge.files) == 1
        assert challenge.files[0].path == Path("/tmp/test.txt")
        assert challenge.files[0].size == 1024
        assert challenge.files[0].mime_type == "text/plain"
    
    @patch('pathlib.Path.exists')
    def test_add_nonexistent_file(self, mock_exists):
        """Test agregar archivo inexistente"""
        mock_exists.return_value = False
        
        challenge = ChallengeData(id="test-1", name="Test")
        
        with pytest.raises(FileNotFoundError):
            challenge.add_file("/tmp/nonexistent.txt")
    
    def test_get_files_by_extension(self):
        """Test obtener archivos por extensión"""
        challenge = ChallengeData(id="test-1", name="Test")
        
        # Agregar archivos mock
        challenge.files = [
            FileInfo(path=Path("/tmp/test.txt"), size=100),
            FileInfo(path=Path("/tmp/test.py"), size=200),
            FileInfo(path=Path("/tmp/data.TXT"), size=300),  # Case insensitive
        ]
        
        txt_files = challenge.get_files_by_extension(".txt")
        assert len(txt_files) == 2
        
        py_files = challenge.get_files_by_extension(".py")
        assert len(py_files) == 1
    
    def test_has_network_component(self):
        """Test detección de componente de red"""
        challenge = ChallengeData(id="test-1", name="Test")
        assert not challenge.has_network_component()
        
        challenge.network_info = NetworkInfo(host="example.com", port=1337)
        assert challenge.has_network_component()
    
    def test_serialization(self):
        """Test serialización completa"""
        network_info = NetworkInfo(host="example.com", port=1337)
        challenge = ChallengeData(
            id="test-1",
            name="Test Challenge",
            network_info=network_info,
            challenge_type=ChallengeType.RSA,
            difficulty=DifficultyLevel.HARD,
            description="Test description",
            hints=["hint1", "hint2"],
            tags=["crypto", "rsa"]
        )
        
        # Agregar archivo mock
        challenge.files = [FileInfo(path=Path("/tmp/test.txt"), size=100)]
        
        # Test to_dict
        data = challenge.to_dict()
        assert data["id"] == "test-1"
        assert data["challenge_type"] == "rsa"
        assert data["difficulty"] == 4
        assert len(data["files"]) == 1
        assert data["network_info"]["host"] == "example.com"
        
        # Test from_dict
        restored = ChallengeData.from_dict(data)
        assert restored.id == challenge.id
        assert restored.challenge_type == challenge.challenge_type
        assert restored.difficulty == challenge.difficulty
        assert len(restored.files) == 1
        assert restored.network_info.host == "example.com"


class TestSolutionResult:
    """Tests para SolutionResult"""
    
    def test_successful_result(self):
        """Test resultado exitoso"""
        result = SolutionResult(
            success=True,
            flag="CTF{test_flag}",
            method_used="brute_force",
            execution_time=1.5,
            confidence=0.95
        )
        
        assert result.success is True
        assert result.flag == "CTF{test_flag}"
        assert result.confidence == 0.95
    
    def test_failed_result(self):
        """Test resultado fallido"""
        result = SolutionResult(
            success=False,
            method_used="rsa_attack",
            error_message="Insufficient data"
        )
        
        assert result.success is False
        assert result.flag is None
        assert result.error_message == "Insufficient data"
    
    def test_invalid_confidence(self):
        """Test confidence inválido"""
        with pytest.raises(ValueError, match="Confidence debe estar entre 0.0 y 1.0"):
            SolutionResult(success=True, confidence=1.5)
        
        with pytest.raises(ValueError, match="Confidence debe estar entre 0.0 y 1.0"):
            SolutionResult(success=True, confidence=-0.1)
    
    def test_invalid_flag_with_failure(self):
        """Test flag con resultado fallido"""
        with pytest.raises(ValueError, match="No puede haber flag si success es False"):
            SolutionResult(success=False, flag="CTF{invalid}")
    
    def test_add_intermediate_result(self):
        """Test agregar resultado intermedio"""
        result = SolutionResult(success=True)
        result.add_intermediate_result("step1", "partial_result", 0.7)
        
        assert len(result.intermediate_results) == 1
        assert result.intermediate_results[0]["step"] == "step1"
        assert result.intermediate_results[0]["result"] == "partial_result"
        assert result.intermediate_results[0]["confidence"] == 0.7
    
    def test_serialization(self):
        """Test serialización de resultado"""
        result = SolutionResult(
            success=True,
            flag="CTF{test}",
            method_used="test_method",
            confidence=0.8,
            details={"key": "value"}
        )
        result.add_intermediate_result("step1", "result1")
        
        # Test to_dict
        data = result.to_dict()
        assert data["success"] is True
        assert data["flag"] == "CTF{test}"
        assert len(data["intermediate_results"]) == 1
        
        # Test from_dict
        restored = SolutionResult.from_dict(data)
        assert restored.success == result.success
        assert restored.flag == result.flag
        assert len(restored.intermediate_results) == 1


class TestPluginInfo:
    """Tests para PluginInfo"""
    
    def test_plugin_info_creation(self):
        """Test creación de PluginInfo"""
        plugin = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            supported_types=[ChallengeType.RSA, ChallengeType.BASIC_CRYPTO],
            techniques=["technique1", "technique2"]
        )
        
        assert plugin.name == "test_plugin"
        assert plugin.enabled is True
        assert plugin.priority == 50
        assert len(plugin.supported_types) == 2
    
    def test_can_handle_type(self):
        """Test verificación de tipo soportado"""
        plugin = PluginInfo(
            name="test",
            version="1.0",
            description="Test",
            supported_types=[ChallengeType.RSA]
        )
        
        assert plugin.can_handle_type(ChallengeType.RSA) is True
        assert plugin.can_handle_type(ChallengeType.BASIC_CRYPTO) is False
        
        # Test MIXED type
        plugin.supported_types.append(ChallengeType.MIXED)
        assert plugin.can_handle_type(ChallengeType.BASIC_CRYPTO) is True
    
    def test_serialization(self):
        """Test serialización de plugin info"""
        plugin = PluginInfo(
            name="test",
            version="1.0",
            description="Test",
            supported_types=[ChallengeType.RSA, ChallengeType.BASIC_CRYPTO]
        )
        
        # Test to_dict
        data = plugin.to_dict()
        assert data["name"] == "test"
        assert data["supported_types"] == ["rsa", "basic_crypto"]
        
        # Test from_dict
        restored = PluginInfo.from_dict(data)
        assert restored.name == plugin.name
        assert len(restored.supported_types) == 2
        assert ChallengeType.RSA in restored.supported_types


class TestExceptions:
    """Tests para excepciones personalizadas"""
    
    def test_challenge_timeout_error(self):
        """Test ChallengeTimeoutError"""
        error = ChallengeTimeoutError("Test timeout", timeout=30)
        assert "Test timeout" in str(error)
        assert "(timeout: 30s)" in str(error)
        assert error.timeout == 30
    
    def test_insufficient_data_error(self):
        """Test InsufficientDataError"""
        error = InsufficientDataError("Need more data", required_data="private_key")
        assert "Need more data" in str(error)
        assert "(requerido: private_key)" in str(error)
        assert error.required_data == "private_key"
    
    def test_network_connection_error(self):
        """Test NetworkConnectionError"""
        error = NetworkConnectionError("Connection failed", host="example.com", port=1337)
        assert "Connection failed" in str(error)
        assert "(example.com:1337)" in str(error)
        assert error.host == "example.com"
        assert error.port == 1337
    
    def test_plugin_error(self):
        """Test PluginError"""
        error = PluginError("Plugin failed", plugin_name="test_plugin")
        assert "Plugin failed" in str(error)
        assert "(plugin: test_plugin)" in str(error)
        assert error.plugin_name == "test_plugin"


if __name__ == "__main__":
    pytest.main([__file__])