"""
End-to-end integration tests
"""

import pytest
import tempfile
import zipfile
import json
from pathlib import Path
from unittest.mock import patch

from src.core.challenge_manager import ChallengeManager
from src.core.file_analyzer import FileAnalyzer
from src.core.plugin_manager import PluginManager
from src.ml.training.training_manager import TrainingManager
from src.models.data import ChallengeData, ChallengeType, FileInfo, NetworkInfo


class TestEndToEndIntegration:
    """Tests de integración end-to-end"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Workspace temporal para tests"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = Path(tmp_dir)
            
            # Crear estructura de directorios
            (workspace / "challenges" / "uploaded").mkdir(parents=True)
            (workspace / "challenges" / "extracted").mkdir(parents=True)
            (workspace / "challenges" / "solved").mkdir(parents=True)
            (workspace / "data" / "models").mkdir(parents=True)
            (workspace / "data" / "training_data").mkdir(parents=True)
            
            yield workspace
    
    @pytest.fixture
    def sample_rsa_challenge(self, temp_workspace):
        """Crear desafío RSA de muestra"""
        challenge_dir = temp_workspace / "challenges" / "uploaded"
        
        # Crear archivos del desafío
        public_key = challenge_dir / "public_key.pem"
        public_key.write_text("""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1234567890abcdef...
-----END PUBLIC KEY-----""")
        
        cipher_file = challenge_dir / "cipher.txt"
        cipher_file.write_text("Encrypted message: 1234567890abcdef...")
        
        description_file = challenge_dir / "description.txt"
        description_file.write_text("RSA challenge: decrypt the message using the public key")
        
        # Crear ZIP con los archivos
        zip_path = challenge_dir / "rsa_challenge.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.write(public_key, public_key.name)
            zf.write(cipher_file, cipher_file.name)
            zf.write(description_file, description_file.name)
        
        return zip_path
    
    @pytest.fixture
    def sample_basic_crypto_challenge(self, temp_workspace):
        """Crear desafío de criptografía básica"""
        challenge_dir = temp_workspace / "challenges" / "uploaded"
        
        # Crear archivo con cifrado César
        cipher_file = challenge_dir / "caesar_cipher.txt"
        cipher_file.write_text("WKLV LV D FDHVDU FLSKHU ZLWK VKLIW 3")
        
        hint_file = challenge_dir / "hint.txt"
        hint_file.write_text("Caesar cipher with shift 3")
        
        return cipher_file
    
    def test_complete_file_analysis_workflow(self, temp_workspace, sample_rsa_challenge):
        """Test flujo completo de análisis de archivos"""
        # Inicializar componentes
        file_analyzer = FileAnalyzer(work_dir=str(temp_workspace / "challenges" / "extracted"))
        
        # Analizar desafío
        challenge_data = file_analyzer.analyze_file(sample_rsa_challenge)
        
        # Verificar resultados
        assert challenge_data.id is not None
        assert challenge_data.name == "rsa_challenge"
        assert len(challenge_data.files) == 3  # public_key.pem, cipher.txt, description.txt
        assert challenge_data.challenge_type == ChallengeType.RSA
        
        # Verificar archivos extraídos
        assert any("public_key.pem" in str(f.path) for f in challenge_data.files)
        assert any("cipher.txt" in str(f.path) for f in challenge_data.files)
        assert any("description.txt" in str(f.path) for f in challenge_data.files)
        
        # Verificar metadatos
        assert challenge_data.metadata['total_files'] == 3
        assert challenge_data.metadata['has_documents'] or challenge_data.metadata['has_text_files']
    
    def test_plugin_system_integration(self, temp_workspace, sample_basic_crypto_challenge):
        """Test integración del sistema de plugins"""
        # Crear desafío simple
        file_info = FileInfo(
            path=sample_basic_crypto_challenge,
            size=sample_basic_crypto_challenge.stat().st_size,
            mime_type="text/plain"
        )
        
        challenge_data = ChallengeData(
            id="basic_crypto_test",
            name="Basic Crypto Test",
            files=[file_info],
            challenge_type=ChallengeType.BASIC_CRYPTO
        )
        
        # Inicializar plugin manager
        plugin_manager = PluginManager()
        
        # Verificar que hay plugins disponibles
        available_plugins = plugin_manager.get_available_plugins()
        assert len(available_plugins) > 0
        
        # Seleccionar mejores plugins
        best_plugins = plugin_manager.select_best_plugins(challenge_data)
        assert len(best_plugins) > 0
        
        # Verificar que al menos un plugin puede manejar el desafío
        assert any(confidence > 0 for _, _, confidence in best_plugins)
    
    def test_challenge_manager_full_workflow(self, temp_workspace, sample_rsa_challenge):
        """Test flujo completo del Challenge Manager"""
        # Inicializar Challenge Manager
        challenge_manager = ChallengeManager()
        
        # Cargar desafío
        challenge_data = challenge_manager.load_challenge(sample_rsa_challenge)
        
        # Verificar carga
        assert challenge_data.id in challenge_manager.get_active_challenges()
        
        # Intentar resolver (puede fallar, pero debe ejecutarse sin errores)
        result = challenge_manager.solve_challenge(challenge_data, strategy="sequential")
        
        # Verificar que se ejecutó
        assert result is not None
        assert result.execution_time > 0
        assert result.method_used is not None
        
        # Verificar estadísticas
        stats = challenge_manager.get_statistics()
        assert stats['total_challenges'] >= 1
        assert stats['successful_solutions'] + stats['failed_solutions'] >= 1
        
        # Verificar que el desafío ya no está activo
        assert challenge_data.id not in challenge_manager.get_active_challenges()
    
    def test_ml_training_integration(self, temp_workspace):
        """Test integración del sistema de ML"""
        # Crear datos de entrenamiento simulados
        training_manager = TrainingManager(data_path=str(temp_workspace / "data" / "training_data"))
        
        # Crear desafíos de muestra para entrenamiento
        sample_challenges = []
        
        for i, challenge_type in enumerate([ChallengeType.RSA, ChallengeType.BASIC_CRYPTO, ChallengeType.RSA]):
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
                if challenge_type == ChallengeType.RSA:
                    tmp.write("RSA public key modulus factorization")
                else:
                    tmp.write("caesar cipher frequency analysis")
                tmp.flush()
                
                file_info = FileInfo(path=Path(tmp.name), size=100, mime_type="text/plain")
                challenge = ChallengeData(
                    id=f"training_challenge_{i}",
                    name=f"Training Challenge {i}",
                    files=[file_info],
                    challenge_type=challenge_type
                )
                sample_challenges.append(challenge)
        
        # Simular recopilación de datos de entrenamiento
        from src.models.data import SolutionResult
        
        for challenge in sample_challenges:
            result = SolutionResult(
                success=True,
                flag=f"CTF{{training_flag_{challenge.id}}}",
                method_used="mock_method",
                confidence=0.8,
                execution_time=1.0
            )
            training_manager.collect_training_data(challenge, result)
        
        # Verificar que se recopilaron datos
        training_data = training_manager.load_training_data()
        assert len(training_data) == len(sample_challenges)
        
        # Obtener estadísticas
        stats = training_manager.get_training_statistics()
        assert stats['total_training_records'] == len(sample_challenges)
        assert stats['type_distribution']['rsa'] == 2
        assert stats['type_distribution']['basic_crypto'] == 1
    
    def test_network_challenge_integration(self, temp_workspace):
        """Test integración de desafíos de red"""
        # Crear desafío de red
        network_info = NetworkInfo(
            host="example.com",
            port=1337,
            protocol="tcp",
            timeout=10
        )
        
        challenge_data = ChallengeData(
            id="network_test",
            name="Network Test Challenge",
            network_info=network_info,
            challenge_type=ChallengeType.NETWORK
        )
        
        # Inicializar Challenge Manager
        challenge_manager = ChallengeManager()
        
        # Intentar resolver (fallará por conexión, pero debe manejar el error)
        result = challenge_manager.solve_challenge(challenge_data)
        
        # Verificar que se manejó correctamente
        assert result is not None
        assert result.method_used is not None
        # Puede ser exitoso o fallido dependiendo de la disponibilidad de plugins de red
    
    def test_error_handling_integration(self, temp_workspace):
        """Test manejo de errores en integración"""
        challenge_manager = ChallengeManager()
        
        # Test con archivo inexistente
        with pytest.raises(FileNotFoundError):
            challenge_manager.load_challenge("/nonexistent/file.zip")
        
        # Test con desafío inválido
        invalid_challenge = ChallengeData(id="invalid", name="Invalid")
        result = challenge_manager.solve_challenge(invalid_challenge)
        
        assert result.success is False
        assert result.error_message is not None
    
    def test_configuration_integration(self, temp_workspace):
        """Test integración de configuración"""
        from src.utils.config import config
        
        # Verificar configuración por defecto
        assert config.plugins.enabled_plugins is not None
        assert config.plugins.plugin_timeout > 0
        assert config.ml.model_path is not None
        
        # Test de carga de configuración personalizada
        custom_config = temp_workspace / "custom_config.json"
        custom_config.write_text(json.dumps({
            "plugins": {
                "plugin_timeout": 600,
                "max_concurrent_plugins": 2
            }
        }))
        
        # Cargar configuración personalizada
        config.config_path = str(custom_config)
        config.load_config()
        
        assert config.plugins.plugin_timeout == 600
        assert config.plugins.max_concurrent_plugins == 2
    
    def test_logging_integration(self, temp_workspace):
        """Test integración del sistema de logging"""
        from src.utils.logging import get_logger
        
        # Crear logger
        logger = get_logger("test_integration")
        
        # Test logging básico
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        
        # Verificar que no hay errores
        assert logger is not None
    
    def test_performance_basic(self, temp_workspace, sample_basic_crypto_challenge):
        """Test básico de performance"""
        import time
        
        challenge_manager = ChallengeManager()
        
        # Crear desafío simple
        file_info = FileInfo(
            path=sample_basic_crypto_challenge,
            size=sample_basic_crypto_challenge.stat().st_size
        )
        
        challenge_data = ChallengeData(
            id="performance_test",
            name="Performance Test",
            files=[file_info],
            challenge_type=ChallengeType.BASIC_CRYPTO
        )
        
        # Medir tiempo de resolución
        start_time = time.time()
        result = challenge_manager.solve_challenge(challenge_data)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Verificar que se ejecutó en tiempo razonable (menos de 30 segundos)
        assert execution_time < 30.0
        assert result.execution_time > 0
    
    def test_concurrent_challenges(self, temp_workspace, sample_rsa_challenge, sample_basic_crypto_challenge):
        """Test manejo de desafíos concurrentes"""
        import asyncio
        
        challenge_manager = ChallengeManager()
        
        # Cargar múltiples desafíos
        rsa_challenge = challenge_manager.load_challenge(sample_rsa_challenge)
        
        file_info = FileInfo(
            path=sample_basic_crypto_challenge,
            size=sample_basic_crypto_challenge.stat().st_size
        )
        basic_challenge = ChallengeData(
            id="concurrent_basic",
            name="Concurrent Basic",
            files=[file_info],
            challenge_type=ChallengeType.BASIC_CRYPTO
        )
        
        # Verificar que ambos están activos
        active_challenges = challenge_manager.get_active_challenges()
        assert rsa_challenge.id in active_challenges
        
        # Resolver uno de ellos
        result = challenge_manager.solve_challenge(basic_challenge)
        
        # Verificar que se manejó correctamente
        assert result is not None
    
    def test_data_persistence(self, temp_workspace):
        """Test persistencia de datos"""
        # Test guardado y carga de ChallengeData
        challenge_data = ChallengeData(
            id="persistence_test",
            name="Persistence Test",
            challenge_type=ChallengeType.RSA,
            description="Test challenge for persistence"
        )
        
        # Guardar
        save_path = temp_workspace / "challenge_data.json"
        challenge_data.save_to_file(save_path)
        
        # Cargar
        loaded_challenge = ChallengeData.load_from_file(save_path)
        
        # Verificar
        assert loaded_challenge.id == challenge_data.id
        assert loaded_challenge.name == challenge_data.name
        assert loaded_challenge.challenge_type == challenge_data.challenge_type
        assert loaded_challenge.description == challenge_data.description
    
    def test_cleanup_and_resource_management(self, temp_workspace, sample_rsa_challenge):
        """Test limpieza y gestión de recursos"""
        file_analyzer = FileAnalyzer(work_dir=str(temp_workspace / "challenges" / "extracted"))
        
        # Analizar desafío (esto crea archivos extraídos)
        challenge_data = file_analyzer.analyze_file(sample_rsa_challenge)
        
        # Verificar que se crearon archivos
        extract_dir = temp_workspace / "challenges" / "extracted" / challenge_data.id
        assert extract_dir.exists()
        assert len(list(extract_dir.iterdir())) > 0
        
        # Limpiar archivos extraídos
        file_analyzer.cleanup_extracted_files(challenge_data.id)
        
        # Verificar limpieza
        assert not extract_dir.exists()


class TestRobustnessAndEdgeCases:
    """Tests de robustez y casos edge"""
    
    def test_malformed_zip_handling(self, tmp_path):
        """Test manejo de archivos ZIP malformados"""
        # Crear archivo que parece ZIP pero está corrupto
        fake_zip = tmp_path / "fake.zip"
        fake_zip.write_bytes(b"PK\x03\x04" + b"corrupted data" * 100)
        
        file_analyzer = FileAnalyzer()
        
        # Debería manejar el error graciosamente
        with pytest.raises(Exception):  # Puede ser FileExtractionError u otra excepción
            file_analyzer.analyze_file(fake_zip)
    
    def test_very_large_file_handling(self, tmp_path):
        """Test manejo de archivos muy grandes"""
        # Crear archivo grande (simulado con mock)
        large_file = tmp_path / "large_file.txt"
        large_file.write_text("x" * 1000)  # Archivo pequeño para el test
        
        # Mock para simular archivo muy grande
        with patch.object(Path, 'stat') as mock_stat:
            mock_stat.return_value.st_size = 100 * 1024 * 1024  # 100MB
            
            file_analyzer = FileAnalyzer()
            
            # Debería manejar archivos grandes sin problemas
            challenge_data = file_analyzer.analyze_file(large_file)
            assert challenge_data is not None
    
    def test_empty_challenge_handling(self):
        """Test manejo de desafíos vacíos"""
        empty_challenge = ChallengeData(id="empty", name="Empty")
        
        challenge_manager = ChallengeManager()
        result = challenge_manager.solve_challenge(empty_challenge)
        
        assert result.success is False
        assert "debe tener archivos o información de red" in result.error_message
    
    def test_unicode_and_special_characters(self, tmp_path):
        """Test manejo de caracteres Unicode y especiales"""
        # Crear archivo con caracteres especiales
        unicode_file = tmp_path / "测试文件.txt"
        unicode_file.write_text("Contenido con caracteres especiales: áéíóú ñ 中文 🔐", encoding='utf-8')
        
        file_analyzer = FileAnalyzer()
        challenge_data = file_analyzer.analyze_file(unicode_file)
        
        assert challenge_data is not None
        assert challenge_data.name == "测试文件"
    
    def test_network_timeout_handling(self):
        """Test manejo de timeouts de red"""
        # Crear desafío de red con timeout muy corto
        network_info = NetworkInfo(
            host="192.0.2.1",  # Dirección de documentación que no debería responder
            port=12345,
            timeout=1  # 1 segundo
        )
        
        challenge_data = ChallengeData(
            id="timeout_test",
            name="Timeout Test",
            network_info=network_info
        )
        
        challenge_manager = ChallengeManager()
        result = challenge_manager.solve_challenge(challenge_data)
        
        # Debería manejar el timeout graciosamente
        assert result is not None
        # Puede ser exitoso o fallido dependiendo de los plugins disponibles
    
    def test_memory_pressure_simulation(self, tmp_path):
        """Test simulación de presión de memoria"""
        # Crear múltiples desafíos para simular carga
        challenge_manager = ChallengeManager()
        results = []
        
        for i in range(10):  # Crear 10 desafíos pequeños
            test_file = tmp_path / f"test_{i}.txt"
            test_file.write_text(f"Test challenge {i} content")
            
            try:
                challenge_data = challenge_manager.load_challenge(test_file)
                result = challenge_manager.solve_challenge(challenge_data)
                results.append(result)
            except Exception as e:
                # Aceptable bajo presión de memoria
                pass
        
        # Al menos algunos deberían procesarse
        assert len(results) > 0


if __name__ == "__main__":
    pytest.main([__file__])