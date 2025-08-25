"""
Tests para el sistema de Machine Learning
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

from src.ml.feature_extractor import FeatureExtractor
from src.ml.models.challenge_classifier import ChallengeClassifier
from src.ml.training.training_manager import TrainingManager
from src.models.data import ChallengeData, ChallengeType, FileInfo, SolutionResult


class TestFeatureExtractor:
    """Tests para FeatureExtractor"""
    
    @pytest.fixture
    def extractor(self):
        return FeatureExtractor()
    
    @pytest.fixture
    def sample_challenge(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            tmp.write("This is a sample RSA challenge with modulus and exponent")
            tmp.flush()
            
            file_info = FileInfo(path=Path(tmp.name), size=100, mime_type="text/plain")
            return ChallengeData(
                id="test-challenge",
                name="RSA Challenge",
                description="A sample RSA cryptography challenge",
                files=[file_info],
                tags=['crypto', 'rsa'],
                challenge_type=ChallengeType.RSA
            )
    
    def test_extract_basic_features(self, extractor, sample_challenge):
        """Test extracción de características básicas"""
        features = extractor._extract_basic_features(sample_challenge)
        
        assert features['file_count'] == 1.0
        assert features['name_length'] == len("RSA Challenge")
        assert features['description_length'] > 0
        assert features['tag_count'] == 2.0
        assert features['has_network_info'] == 0.0
    
    def test_extract_file_features(self, extractor, sample_challenge):
        """Test extracción de características de archivos"""
        features = extractor._extract_file_features(sample_challenge)
        
        assert features['has_text_files'] == 1.0
        assert features['text_file_ratio'] == 1.0
        assert features['has_image_files'] == 0.0
        assert features['file_type_diversity'] >= 1.0
    
    def test_extract_content_features(self, extractor, sample_challenge):
        """Test extracción de características de contenido"""
        features = extractor._extract_content_features(sample_challenge)
        
        assert features['total_text_length'] > 0
        assert features['word_count'] > 0
        assert features['text_entropy'] > 0
        assert features['has_large_numbers'] == 0.0  # No hay números grandes en el ejemplo
    
    def test_extract_pattern_features(self, extractor, sample_challenge):
        """Test extracción de características de patrones"""
        features = extractor._extract_pattern_features(sample_challenge)
        
        assert features['rsa_pattern_count'] > 0  # Debería detectar "RSA", "modulus", "exponent"
        assert features['has_rsa_patterns'] == 1.0
        assert features['basic_crypto_pattern_count'] >= 0
    
    def test_calculate_entropy(self, extractor):
        """Test cálculo de entropía"""
        # Texto uniforme (baja entropía)
        low_entropy = extractor._calculate_entropy("aaaaaaaaaa")
        assert low_entropy < 1.0
        
        # Texto aleatorio (alta entropía)
        high_entropy = extractor._calculate_entropy("abcdefghijklmnopqrstuvwxyz")
        assert high_entropy > low_entropy
        
        # Texto vacío
        zero_entropy = extractor._calculate_entropy("")
        assert zero_entropy == 0.0
    
    def test_looks_like_base64(self, extractor):
        """Test detección de Base64"""
        base64_text = "SGVsbG8gV29ybGQ= " * 10  # Repetir para superar el umbral
        assert extractor._looks_like_base64(base64_text) is True
        
        normal_text = "This is just normal text"
        assert extractor._looks_like_base64(normal_text) is False
    
    def test_looks_like_hex(self, extractor):
        """Test detección de hexadecimal"""
        hex_text = "48656c6c6f20576f726c64" * 10  # Repetir para superar el umbral
        assert extractor._looks_like_hex(hex_text) is True
        
        normal_text = "This is just normal text"
        assert extractor._looks_like_hex(normal_text) is False
    
    def test_normalize_features(self, extractor):
        """Test normalización de características"""
        features = {
            'total_size': 1000000,  # Valor grande
            'text_file_ratio': 0.5,  # Ya normalizado
            'has_rsa_patterns': 1.0,  # Binario
            'pattern_count': 150  # Conteo grande
        }
        
        normalized = extractor.normalize_features(features)
        
        # Los valores grandes deberían ser transformados con log
        assert normalized['total_size'] < features['total_size']
        assert normalized['total_size'] > 0
        
        # Los ratios deberían mantenerse igual
        assert normalized['text_file_ratio'] == 0.5
        
        # Los binarios deberían mantenerse igual
        assert normalized['has_rsa_patterns'] == 1.0
        
        # Los conteos grandes deberían ser limitados
        assert normalized['pattern_count'] <= 100.0
    
    def test_get_feature_names(self, extractor):
        """Test obtener nombres de características"""
        feature_names = extractor.get_feature_names()
        
        assert isinstance(feature_names, list)
        assert len(feature_names) > 0
        assert 'file_count' in feature_names
        assert 'has_rsa_patterns' in feature_names
        assert 'text_entropy' in feature_names


class TestChallengeClassifier:
    """Tests para ChallengeClassifier"""
    
    @pytest.fixture
    def classifier(self):
        return ChallengeClassifier()
    
    @pytest.fixture
    def training_data(self):
        """Crear datos de entrenamiento sintéticos"""
        data = []
        
        # Crear algunos desafíos RSA
        for i in range(10):
            challenge = ChallengeData(
                id=f"rsa-{i}",
                name=f"RSA Challenge {i}",
                description="RSA factorization challenge with modulus and exponent",
                tags=['rsa', 'crypto', 'factorization'],
                challenge_type=ChallengeType.RSA
            )
            data.append((challenge, ChallengeType.RSA))
        
        # Crear algunos desafíos de criptografía básica
        for i in range(10):
            challenge = ChallengeData(
                id=f"basic-{i}",
                name=f"Caesar Cipher {i}",
                description="Classical cipher challenge with frequency analysis",
                tags=['caesar', 'cipher', 'frequency'],
                challenge_type=ChallengeType.BASIC_CRYPTO
            )
            data.append((challenge, ChallengeType.BASIC_CRYPTO))
        
        # Crear algunos desafíos de red
        for i in range(10):
            challenge = ChallengeData(
                id=f"network-{i}",
                name=f"Network Challenge {i}",
                description="Remote server challenge with socket connection",
                tags=['network', 'socket', 'server'],
                challenge_type=ChallengeType.NETWORK
            )
            data.append((challenge, ChallengeType.NETWORK))
        
        return data
    
    def test_prepare_training_data(self, classifier, training_data):
        """Test preparación de datos de entrenamiento"""
        X, y = classifier.prepare_training_data(training_data)
        
        assert X.shape[0] == len(training_data)
        assert X.shape[1] > 0  # Debería tener características
        assert len(y) == len(training_data)
        assert len(classifier.label_encoder) == 3  # RSA, BASIC_CRYPTO, NETWORK
    
    def test_train_classifier(self, classifier, training_data):
        """Test entrenamiento del clasificador"""
        metrics = classifier.train(training_data, test_size=0.3, validate=False)
        
        assert classifier.is_trained is True
        assert 'train_accuracy' in metrics
        assert 'test_accuracy' in metrics
        assert metrics['train_accuracy'] > 0.0
        assert metrics['test_accuracy'] > 0.0
    
    def test_predict(self, classifier, training_data):
        """Test predicción"""
        # Entrenar primero
        classifier.train(training_data, validate=False)
        
        # Crear desafío de prueba
        test_challenge = ChallengeData(
            id="test",
            name="RSA Factorization",
            description="Factor the modulus to find the private key",
            tags=['rsa', 'factorization'],
            challenge_type=ChallengeType.UNKNOWN
        )
        
        predicted_type, confidence = classifier.predict(test_challenge)
        
        assert isinstance(predicted_type, ChallengeType)
        assert 0.0 <= confidence <= 1.0
        # Debería predecir RSA basado en el nombre y descripción
        assert predicted_type == ChallengeType.RSA
    
    def test_predict_proba(self, classifier, training_data):
        """Test predicción de probabilidades"""
        classifier.train(training_data, validate=False)
        
        test_challenge = ChallengeData(
            id="test",
            name="Caesar Cipher",
            description="Decrypt the message using frequency analysis",
            tags=['caesar', 'frequency'],
            challenge_type=ChallengeType.UNKNOWN
        )
        
        probabilities = classifier.predict_proba(test_challenge)
        
        assert isinstance(probabilities, dict)
        assert len(probabilities) == 3  # Tres tipos entrenados
        assert all(0.0 <= prob <= 1.0 for prob in probabilities.values())
        assert abs(sum(probabilities.values()) - 1.0) < 0.01  # Suma debe ser ~1
    
    def test_explain_prediction(self, classifier, training_data):
        """Test explicación de predicción"""
        classifier.train(training_data, validate=False)
        
        test_challenge = ChallengeData(
            id="test",
            name="Network Server",
            description="Connect to the server and find the flag",
            tags=['network', 'server'],
            challenge_type=ChallengeType.UNKNOWN
        )
        
        explanation = classifier.explain_prediction(test_challenge)
        
        assert 'predicted_type' in explanation
        assert 'confidence' in explanation
        assert 'top_contributing_features' in explanation
        assert len(explanation['top_contributing_features']) > 0
    
    def test_model_persistence(self, classifier, training_data):
        """Test guardar y cargar modelo"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            model_path = Path(tmp_dir) / "test_model.joblib"
            
            # Entrenar y guardar
            classifier.train(training_data, validate=False)
            classifier.save_model(str(model_path))
            
            assert model_path.exists()
            
            # Crear nuevo clasificador y cargar
            new_classifier = ChallengeClassifier()
            new_classifier.load_model(str(model_path))
            
            assert new_classifier.is_trained is True
            assert new_classifier.feature_names == classifier.feature_names
            assert new_classifier.label_encoder == classifier.label_encoder


class TestTrainingManager:
    """Tests para TrainingManager"""
    
    @pytest.fixture
    def training_manager(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            return TrainingManager(data_dir=tmp_dir)
    
    @pytest.fixture
    def sample_challenge(self):
        return ChallengeData(
            id="test-challenge",
            name="RSA Challenge",
            description="Factor the modulus",
            tags=['rsa', 'crypto'],
            challenge_type=ChallengeType.RSA
        )
    
    @pytest.fixture
    def sample_solution(self):
        return SolutionResult(
            success=True,
            flag="CTF{factored}",
            method_used="factorization",
            confidence=0.9,
            execution_time=1.5,
            plugin_name="rsa_advanced"
        )
    
    def test_store_challenge(self, training_manager, sample_challenge):
        """Test almacenar desafío"""
        initial_count = len(training_manager.stored_challenges)
        
        training_manager.store_challenge(sample_challenge, ChallengeType.RSA)
        
        assert len(training_manager.stored_challenges) == initial_count + 1
        stored = training_manager.stored_challenges[-1]
        assert stored['id'] == sample_challenge.id
        assert stored['challenge_type'] == ChallengeType.RSA.value
    
    def test_store_solution(self, training_manager, sample_solution):
        """Test almacenar solución"""
        initial_count = len(training_manager.stored_solutions)
        
        training_manager.store_solution("test-challenge", sample_solution)
        
        assert len(training_manager.stored_solutions) == initial_count + 1
        stored = training_manager.stored_solutions[-1]
        assert stored['challenge_id'] == "test-challenge"
        assert stored['success'] is True
        assert stored['flag'] == "CTF{factored}"
    
    def test_update_patterns(self, training_manager):
        """Test actualizar patrones"""
        challenge_type = ChallengeType.RSA
        successful_methods = ["factorization", "wiener_attack"]
        
        training_manager.update_patterns(challenge_type, successful_methods)
        
        patterns = training_manager.get_success_patterns(challenge_type)
        assert 'successful_methods' in patterns
        assert 'factorization' in patterns['successful_methods']
        assert 'wiener_attack' in patterns['successful_methods']
    
    def test_get_recommended_methods(self, training_manager):
        """Test obtener métodos recomendados"""
        # Primero actualizar algunos patrones
        training_manager.update_patterns(ChallengeType.RSA, ["factorization"])
        training_manager.update_patterns(ChallengeType.RSA, ["factorization", "wiener_attack"])
        training_manager.update_patterns(ChallengeType.RSA, ["factorization"])
        
        recommendations = training_manager.get_recommended_methods(ChallengeType.RSA)
        
        assert len(recommendations) > 0
        # factorization debería ser el más recomendado (aparece 3 veces)
        assert recommendations[0][0] == "factorization"
        assert recommendations[0][1] > 0.5  # Más del 50% de probabilidad
    
    def test_predict_challenge_type_fallback(self, training_manager, sample_challenge):
        """Test predicción sin modelo entrenado (fallback)"""
        predicted_type, confidence, explanation = training_manager.predict_challenge_type(sample_challenge)
        
        assert isinstance(predicted_type, ChallengeType)
        assert 0.0 <= confidence <= 1.0
        assert 'method' in explanation
        # Debería usar heurísticas y detectar RSA por el nombre
        assert predicted_type == ChallengeType.RSA
    
    def test_get_statistics(self, training_manager, sample_challenge, sample_solution):
        """Test obtener estadísticas"""
        # Agregar algunos datos
        training_manager.store_challenge(sample_challenge, ChallengeType.RSA)
        training_manager.store_solution(sample_challenge.id, sample_solution)
        
        stats = training_manager.get_statistics()
        
        assert 'total_challenges' in stats
        assert 'total_solutions' in stats
        assert 'classifier_trained' in stats
        assert 'overall_success_rate' in stats
        assert stats['total_challenges'] >= 1
        assert stats['total_solutions'] >= 1
    
    def test_export_training_data(self, training_manager, sample_challenge):
        """Test exportar datos de entrenamiento"""
        training_manager.store_challenge(sample_challenge, ChallengeType.RSA)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            training_manager.export_training_data(tmp.name)
            
            # Verificar que el archivo se creó
            assert Path(tmp.name).exists()
            
            # Verificar contenido
            with open(tmp.name, 'r') as f:
                data = json.load(f)
            
            assert len(data) >= 1
            assert 'challenge' in data[0]
            assert 'type' in data[0]
            assert data[0]['type'] == ChallengeType.RSA.value


if __name__ == "__main__":
    pytest.main([__file__])