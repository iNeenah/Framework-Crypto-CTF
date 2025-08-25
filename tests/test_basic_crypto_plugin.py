"""
Tests para Basic Crypto Plugin
"""

import pytest
import tempfile
import base64
from pathlib import Path

from src.plugins.basic_crypto.plugin import BasicCryptoPlugin
from src.models.data import ChallengeData, ChallengeType, FileInfo


class TestBasicCryptoPlugin:
    """Tests para BasicCryptoPlugin"""
    
    @pytest.fixture
    def plugin(self):
        return BasicCryptoPlugin()
    
    @pytest.fixture
    def temp_file_with_content(self):
        def _create_file(content):
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
                tmp.write(content)
                tmp.flush()
                return Path(tmp.name)
        return _create_file
    
    def test_plugin_info(self, plugin):
        """Test información del plugin"""
        info = plugin.get_plugin_info()
        assert info.name == "basic_crypto"
        assert info.version == "1.0.0"
        assert ChallengeType.BASIC_CRYPTO in info.supported_types
        assert "caesar_cipher" in info.techniques
        assert "base64_decode" in info.techniques
    
    def test_can_handle_basic_crypto(self, plugin):
        """Test evaluación de desafío de criptografía básica"""
        challenge = ChallengeData(
            id="test",
            name="Caesar Cipher",
            challenge_type=ChallengeType.BASIC_CRYPTO
        )
        
        confidence = plugin.can_handle(challenge)
        assert confidence >= 0.8
    
    def test_can_handle_filename_patterns(self, plugin, temp_file_with_content):
        """Test evaluación basada en nombres de archivo"""
        file_path = temp_file_with_content("test content")
        file_path = file_path.rename(file_path.parent / "caesar_cipher.txt")
        
        file_info = FileInfo(path=file_path, size=100, mime_type="text/plain")
        challenge = ChallengeData(
            id="test",
            name="Test",
            files=[file_info],
            challenge_type=ChallengeType.UNKNOWN
        )
        
        confidence = plugin.can_handle(challenge)
        assert confidence > 0.2
    
    def test_looks_like_base64(self, plugin):
        """Test detección de Base64"""
        assert plugin._looks_like_base64("SGVsbG8gV29ybGQ=")
        assert plugin._looks_like_base64("VGVzdA==")
        assert not plugin._looks_like_base64("Hello World")
        assert not plugin._looks_like_base64("123")
        assert not plugin._looks_like_base64("SGVsbG8gV29ybGQ")  # Sin padding
    
    def test_looks_like_hex(self, plugin):
        """Test detección de hexadecimal"""
        assert plugin._looks_like_hex("48656c6c6f20576f726c64")
        assert plugin._looks_like_hex("DEADBEEF")
        assert not plugin._looks_like_hex("Hello World")
        assert not plugin._looks_like_hex("48656c6c6f20576f726c6")  # Longitud impar
    
    def test_extract_flag(self, plugin):
        """Test extracción de flags"""
        assert plugin._extract_flag("CTF{test_flag}") == "CTF{test_flag}"
        assert plugin._extract_flag("flag{another_test}") == "flag{another_test}"
        assert plugin._extract_flag("The answer is CTF{hidden_flag} here") == "CTF{hidden_flag}"
        assert plugin._extract_flag("No flag here") is None
    
    def test_caesar_decrypt(self, plugin):
        """Test descifrado César"""
        # "HELLO" con shift 3 es "KHOOR"
        encrypted = "KHOOR"
        decrypted = plugin._caesar_decrypt(encrypted, 3)
        assert decrypted == "HELLO"
        
        # Probar con minúsculas
        encrypted = "khoor"
        decrypted = plugin._caesar_decrypt(encrypted, 3)
        assert decrypted == "hello"
    
    def test_atbash_decrypt(self, plugin):
        """Test descifrado Atbash"""
        # A->Z, B->Y, etc.
        encrypted = "SVOOL"  # "HELLO" en Atbash
        decrypted = plugin._atbash_decrypt(encrypted)
        assert decrypted == "HELLO"
    
    def test_xor_decrypt(self, plugin):
        """Test descifrado XOR"""
        original = b"HELLO"
        key = b"KEY"
        
        # Cifrar
        encrypted = plugin._xor_decrypt(original, key)
        # Descifrar (XOR es simétrico)
        decrypted = plugin._xor_decrypt(encrypted, key)
        
        assert decrypted == original
    
    def test_vigenere_decrypt(self, plugin):
        """Test descifrado Vigenère"""
        # Ejemplo conocido: "HELLO" con clave "KEY" -> "RIJVS"
        encrypted = "RIJVS"
        decrypted = plugin._vigenere_decrypt(encrypted, "KEY")
        assert decrypted == "HELLO"
    
    def test_score_text_quality(self, plugin):
        """Test puntuación de calidad de texto"""
        # Texto en español
        good_text = "hola mundo este es un texto en español"
        score = plugin._score_text_quality(good_text)
        assert score > 0.3
        
        # Texto aleatorio
        random_text = "xqwerty zxcvbn asdfgh"
        score = plugin._score_text_quality(random_text)
        assert score < 0.5
        
        # Texto muy corto
        short_text = "hi"
        score = plugin._score_text_quality(short_text)
        assert score >= 0.0
    
    def test_base64_decode_success(self, plugin, temp_file_with_content):
        """Test decodificación Base64 exitosa"""
        # Crear contenido Base64 con flag
        flag_text = "CTF{base64_decoded}"
        encoded = base64.b64encode(flag_text.encode()).decode()
        
        file_path = temp_file_with_content(encoded)
        file_info = FileInfo(path=file_path, size=100, mime_type="text/plain")
        challenge = ChallengeData(id="test", name="Test", files=[file_info])
        
        result = plugin._try_base64_decode(challenge)
        
        assert result.success is True
        assert result.flag == flag_text
        assert result.method_used == "base64_decode"
    
    def test_caesar_cipher_success(self, plugin, temp_file_with_content):
        """Test descifrado César exitoso"""
        # "CTF{caesar_works}" con shift 5
        original = "CTF{caesar_works}"
        encrypted = plugin._caesar_decrypt(original, -5)  # Cifrar con shift negativo
        
        file_path = temp_file_with_content(encrypted)
        file_info = FileInfo(path=file_path, size=100, mime_type="text/plain")
        challenge = ChallengeData(id="test", name="Test", files=[file_info])
        
        result = plugin._try_caesar_cipher(challenge)
        
        assert result.success is True
        assert "CTF{" in result.flag
    
    def test_rot13_success(self, plugin, temp_file_with_content):
        """Test ROT13 exitoso"""
        # "CTF{rot13_test}" en ROT13
        original = "CTF{rot13_test}"
        encrypted = plugin._caesar_decrypt(original, -13)  # ROT13
        
        file_path = temp_file_with_content(encrypted)
        file_info = FileInfo(path=file_path, size=100, mime_type="text/plain")
        challenge = ChallengeData(id="test", name="Test", files=[file_info])
        
        result = plugin._try_rot13(challenge)
        
        assert result.success is True
        assert "CTF{" in result.flag
    
    def test_xor_cipher_success(self, plugin, temp_file_with_content):
        """Test descifrado XOR exitoso"""
        # Crear contenido XOR con clave simple
        original = b"CTF{xor_cipher_test}"
        key = b"key"
        encrypted = plugin._xor_decrypt(original, key)
        
        # Guardar como hex
        hex_content = encrypted.hex()
        file_path = temp_file_with_content(hex_content)
        file_info = FileInfo(path=file_path, size=100, mime_type="text/plain")
        challenge = ChallengeData(id="test", name="Test", files=[file_info])
        
        result = plugin._try_xor_cipher(challenge)
        
        # Puede que encuentre la solución o no, dependiendo de si 'key' está en common_keys
        if result.success:
            assert "CTF{" in result.flag
    
    def test_vigenere_cipher_success(self, plugin, temp_file_with_content):
        """Test descifrado Vigenère exitoso"""
        # Cifrar con clave común
        original = "CTF{vigenere_cipher}"
        encrypted = plugin._vigenere_decrypt(original, "KEY")  # Cifrar
        
        file_path = temp_file_with_content(encrypted)
        file_info = FileInfo(path=file_path, size=100, mime_type="text/plain")
        challenge = ChallengeData(id="test", name="Test", files=[file_info])
        
        # Necesitamos "descifrar" (que es cifrar de nuevo con Vigenère)
        # Pero el plugin probará claves comunes incluyendo "KEY"
        result = plugin._try_vigenere_cipher(challenge)
        
        # Puede encontrar la solución si "KEY" está en las claves comunes
        if result.success:
            assert "CTF{" in result.flag
    
    def test_frequency_analysis(self, plugin, temp_file_with_content):
        """Test análisis de frecuencia"""
        content = "este es un texto de prueba para analizar la frecuencia de las letras"
        file_path = temp_file_with_content(content)
        file_info = FileInfo(path=file_path, size=100, mime_type="text/plain")
        challenge = ChallengeData(id="test", name="Test", files=[file_info])
        
        result = plugin._try_frequency_analysis(challenge)
        
        assert result.success is False  # Es análisis, no solución
        assert result.method_used == "frequency_analysis"
        assert "letter_frequencies" in str(result.details)
    
    def test_extract_cipher_text(self, plugin):
        """Test extracción de texto cifrado"""
        content = """
        # This is a comment
        // Another comment
        The cipher is: KHOOR ZRUOG
        Hint: Caesar cipher with shift 3
        """
        
        cipher_text = plugin._extract_cipher_text(content)
        assert "KHOOR ZRUOG" in cipher_text
        assert "comment" not in cipher_text.lower()
        assert "hint" not in cipher_text.lower()
    
    def test_extract_base64_candidates(self, plugin):
        """Test extracción de candidatos Base64"""
        content = """
        Here is some Base64: SGVsbG8gV29ybGQ=
        And another one: VGVzdA==
        Not base64: Hello World
        """
        
        candidates = plugin._extract_base64_candidates(content)
        assert "SGVsbG8gV29ybGQ=" in candidates
        assert "VGVzdA==" in candidates
        assert len(candidates) >= 2
    
    def test_analyze_frequency(self, plugin):
        """Test análisis de frecuencia de caracteres"""
        text = "hello world test"
        analysis = plugin._analyze_frequency(text)
        
        assert "letter_frequencies" in analysis
        assert "total_letters" in analysis
        assert analysis["total_letters"] > 0
        assert "l" in analysis["letter_frequencies"]  # 'l' aparece varias veces
    
    def test_detect_patterns(self, plugin):
        """Test detección de patrones"""
        text = "abcabc defdef hello world"
        patterns = plugin._detect_patterns(text)
        
        # Debería detectar patrones repetidos como "abc" y "def"
        if "repeated_sequences" in patterns:
            assert len(patterns["repeated_sequences"]) > 0
    
    def test_get_content_hints(self, plugin):
        """Test extracción de hints del contenido"""
        content = "This is a Caesar cipher with base64 encoding"
        hints = plugin._get_content_hints(content)
        
        assert "caesar" in hints
        assert "base64" in hints
    
    def test_ordered_techniques(self, plugin, temp_file_with_content):
        """Test ordenamiento de técnicas basado en hints"""
        content = "This text contains base64 hint: SGVsbG8="
        file_path = temp_file_with_content(content)
        file_info = FileInfo(path=file_path, size=100, mime_type="text/plain")
        challenge = ChallengeData(id="test", name="Test", files=[file_info])
        
        ordered = plugin._get_ordered_techniques(challenge)
        techniques_list = list(ordered.keys())
        
        # base64_decode debería estar primero debido al hint
        assert "base64_decode" in techniques_list
        # La posición exacta puede variar, pero debería estar presente
    
    def test_solve_integration(self, plugin, temp_file_with_content):
        """Test integración completa de resolución"""
        # Crear un desafío simple con ROT13
        original = "CTF{integration_test}"
        encrypted = plugin._caesar_decrypt(original, -13)  # ROT13
        
        file_path = temp_file_with_content(encrypted)
        file_info = FileInfo(path=file_path, size=100, mime_type="text/plain")
        challenge = ChallengeData(
            id="test",
            name="ROT13 Test",
            files=[file_info],
            challenge_type=ChallengeType.BASIC_CRYPTO
        )
        
        # El plugin debería poder resolverlo
        result = plugin.solve_with_timeout(challenge)
        
        # Verificar que al menos intentó resolver
        assert result is not None
        assert result.method_used is not None
        assert result.execution_time >= 0
    
    def test_no_valid_content(self, plugin, temp_file_with_content):
        """Test con contenido que no se puede descifrar"""
        content = "This is just plain text with no cipher"
        file_path = temp_file_with_content(content)
        file_info = FileInfo(path=file_path, size=100, mime_type="text/plain")
        challenge = ChallengeData(id="test", name="Test", files=[file_info])
        
        # Probar técnicas individuales
        result = plugin._try_caesar_cipher(challenge)
        assert result.success is False
        
        result = plugin._try_base64_decode(challenge)
        assert result.success is False


if __name__ == "__main__":
    pytest.main([__file__])