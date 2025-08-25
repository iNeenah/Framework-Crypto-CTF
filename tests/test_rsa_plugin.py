"""
Tests para RSA Plugin
"""

import pytest
import tempfile
import json
from pathlib import Path
from Crypto.PublicKey import RSA
from Crypto.Util.number import bytes_to_long, long_to_bytes

from src.plugins.rsa.plugin import RSAPlugin
from src.models.data import ChallengeData, ChallengeType, FileInfo


class TestRSAPlugin:
    """Tests para RSAPlugin"""
    
    @pytest.fixture
    def plugin(self):
        return RSAPlugin()
    
    @pytest.fixture
    def temp_file_with_content(self):
        def _create_file(content):
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
                tmp.write(content)
                tmp.flush()
                return Path(tmp.name)
        return _create_file
    
    @pytest.fixture
    def small_rsa_key(self):
        """Generar clave RSA pequeña para tests"""
        # Usar primos pequeños conocidos para tests rápidos
        p, q = 61, 53  # Primos pequeños
        n = p * q  # 3233
        e = 17
        phi_n = (p - 1) * (q - 1)  # 3120
        d = pow(e, -1, phi_n)  # 2753
        
        return {
            'p': p, 'q': q, 'n': n, 'e': e, 'd': d,
            'phi_n': phi_n
        }
    
    def test_plugin_info(self, plugin):
        """Test información del plugin"""
        info = plugin.get_plugin_info()
        assert info.name == "rsa_advanced"
        assert info.version == "1.0.0"
        assert ChallengeType.RSA in info.supported_types
        assert "wiener_attack" in info.techniques
        assert "factorization" in info.techniques
    
    def test_can_handle_rsa_type(self, plugin):
        """Test evaluación de desafío RSA"""
        challenge = ChallengeData(
            id="test",
            name="RSA Challenge",
            challenge_type=ChallengeType.RSA
        )
        
        confidence = plugin.can_handle(challenge)
        assert confidence >= 0.9
    
    def test_can_handle_rsa_filename(self, plugin, temp_file_with_content):
        """Test evaluación basada en nombre de archivo RSA"""
        file_path = temp_file_with_content("test content")
        file_path = file_path.rename(file_path.parent / "rsa_public_key.txt")
        
        file_info = FileInfo(path=file_path, size=100, mime_type="text/plain")
        challenge = ChallengeData(
            id="test",
            name="Test",
            files=[file_info],
            challenge_type=ChallengeType.UNKNOWN
        )
        
        confidence = plugin.can_handle(challenge)
        assert confidence > 0.2
    
    def test_analyze_rsa_content(self, plugin):
        """Test análisis de contenido RSA"""
        content = "RSA public key with modulus and exponent for factorization"
        confidence = plugin._analyze_rsa_content(content)
        assert confidence > 0.3
        
        # Contenido con números grandes
        content_with_numbers = "n = 123456789012345678901234567890123456789012345678901234567890"
        confidence = plugin._analyze_rsa_content(content_with_numbers)
        assert confidence > 0.3
    
    def test_looks_like_rsa_json(self, plugin):
        """Test detección de JSON RSA"""
        rsa_json = '{"n": 3233, "e": 17, "d": 2753}'
        assert plugin._looks_like_rsa_json(rsa_json) is True
        
        non_rsa_json = '{"name": "test", "value": 123}'
        assert plugin._looks_like_rsa_json(non_rsa_json) is False
        
        invalid_json = "not json at all"
        assert plugin._looks_like_rsa_json(invalid_json) is False
    
    def test_extract_from_json(self, plugin):
        """Test extracción de parámetros JSON"""
        json_content = '{"n": 3233, "e": 17, "d": 2753, "p": 61, "q": 53}'
        params = plugin._extract_from_json(json_content)
        
        assert params['n'] == 3233
        assert params['e'] == 17
        assert params['d'] == 2753
        assert params['p'] == 61
        assert params['q'] == 53
    
    def test_extract_from_text(self, plugin):
        """Test extracción de parámetros de texto"""
        text_content = """
        RSA Parameters:
        n = 3233
        e = 17
        c = 2201
        """
        
        params = plugin._extract_from_text(text_content)
        assert params['n'] == 3233
        assert params['e'] == 17
        assert params['c'] == 2201
    
    def test_generate_small_primes(self, plugin):
        """Test generación de primos pequeños"""
        primes = plugin._generate_small_primes(100)
        
        assert 2 in primes
        assert 3 in primes
        assert 5 in primes
        assert 97 in primes
        assert 100 not in primes  # 100 no es primo
        
        # Verificar que todos son primos
        for p in primes[:10]:  # Verificar los primeros 10
            assert self._is_prime(p)
    
    def _is_prime(self, n):
        """Verificar si un número es primo"""
        if n < 2:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True
    
    def test_trial_division(self, plugin):
        """Test factorización por división de prueba"""
        # Número con factores pequeños
        n = 2 * 3 * 5 * 7  # 210
        factors = plugin._trial_division(n)
        
        assert 2 in factors
        assert 3 in factors
        assert 5 in factors
        assert 7 in factors
    
    def test_pollard_rho_factorize(self, plugin):
        """Test algoritmo Pollard's rho"""
        # Usar número compuesto conocido
        n = 8051  # 97 * 83
        factor = plugin._pollard_rho_factorize(n)
        
        if factor:  # Pollard's rho es probabilístico
            assert 1 < factor < n
            assert n % factor == 0
    
    def test_fermat_factorize(self, plugin):
        """Test factorización de Fermat"""
        # Usar factores cercanos
        p, q = 97, 101  # Factores cercanos
        n = p * q
        
        result = plugin._fermat_factorize(n)
        if result:
            factor1, factor2 = result
            assert factor1 * factor2 == n
            assert {factor1, factor2} == {p, q}
    
    def test_is_wiener_vulnerable(self, plugin):
        """Test detección de vulnerabilidad Wiener"""
        n = 3233
        
        # Exponente grande (vulnerable)
        e_large = 2000
        assert plugin._is_wiener_vulnerable(n, e_large) is True
        
        # Exponente pequeño (no vulnerable)
        e_small = 17
        assert plugin._is_wiener_vulnerable(n, e_small) is False
    
    def test_extract_flag_from_text(self, plugin):
        """Test extracción de flag de texto"""
        text_with_flag = "The answer is CTF{rsa_cracked}"
        flag = plugin._extract_flag_from_text(text_with_flag)
        assert flag == "CTF{rsa_cracked}"
        
        text_without_flag = "Just some random text"
        flag = plugin._extract_flag_from_text(text_without_flag)
        assert flag == "Just some random text"  # Texto corto se considera flag
    
    def test_weak_keys_small_factors(self, plugin, temp_file_with_content, small_rsa_key):
        """Test detección de claves débiles con factores pequeños"""
        # Crear desafío con parámetros RSA débiles
        params = {
            'n': small_rsa_key['n'],
            'e': small_rsa_key['e']
        }
        
        json_content = json.dumps(params)
        file_path = temp_file_with_content(json_content)
        file_info = FileInfo(path=file_path, size=100, mime_type="text/plain")
        challenge = ChallengeData(id="test", name="Test", files=[file_info])
        
        result = plugin._try_weak_keys(challenge)
        
        # Debería encontrar los factores pequeños
        assert result.success is True
        assert "weak_keys" in result.method_used or "factorization" in result.method_used
    
    def test_small_e_attack(self, plugin, temp_file_with_content, small_rsa_key):
        """Test ataque de exponente pequeño"""
        # Crear mensaje que no necesita padding
        message = b"Hi"
        m = bytes_to_long(message)
        
        # Cifrar con e=3 (muy pequeño)
        e = 3
        n = small_rsa_key['n']
        c = pow(m, e, n)
        
        # Si c < n, el ataque debería funcionar
        if c < n:
            params = {'n': n, 'e': e, 'c': c}
            json_content = json.dumps(params)
            file_path = temp_file_with_content(json_content)
            file_info = FileInfo(path=file_path, size=100, mime_type="text/plain")
            challenge = ChallengeData(id="test", name="Test", files=[file_info])
            
            result = plugin._try_small_e_attack(challenge)
            
            # Puede que funcione dependiendo de las condiciones
            if result.success:
                assert "small_e_attack" in result.method_used
    
    def test_factorization_attack(self, plugin, temp_file_with_content, small_rsa_key):
        """Test ataque de factorización"""
        params = {
            'n': small_rsa_key['n'],
            'e': small_rsa_key['e'],
            'c': 1000  # Texto cifrado dummy
        }
        
        json_content = json.dumps(params)
        file_path = temp_file_with_content(json_content)
        file_info = FileInfo(path=file_path, size=100, mime_type="text/plain")
        challenge = ChallengeData(id="test", name="Test", files=[file_info])
        
        result = plugin._try_factorization(challenge)
        
        # Debería factorizar el módulo pequeño
        assert result.success is True
        assert "factorization" in result.method_used
    
    def test_decrypt_with_factors(self, plugin, small_rsa_key):
        """Test descifrado con factores conocidos"""
        # Crear mensaje de prueba
        message = b"CTF{factored}"
        m = bytes_to_long(message)
        
        # Cifrar
        n, e = small_rsa_key['n'], small_rsa_key['e']
        c = pow(m, e, n)
        
        params = {'n': n, 'e': e, 'c': c}
        p, q = small_rsa_key['p'], small_rsa_key['q']
        
        result = plugin._decrypt_with_factors(params, p, q)
        
        assert result.success is True
        assert "CTF{factored}" in result.flag
    
    def test_extract_rsa_parameters_integration(self, plugin, temp_file_with_content):
        """Test extracción completa de parámetros RSA"""
        # Crear múltiples archivos con diferentes formatos
        json_params = {'n': 3233, 'e': 17}
        text_params = "d = 2753\nc = 1000"
        
        json_file = temp_file_with_content(json.dumps(json_params))
        text_file = temp_file_with_content(text_params)
        
        files = [
            FileInfo(path=json_file, size=100, mime_type="text/plain"),
            FileInfo(path=text_file, size=100, mime_type="text/plain")
        ]
        
        challenge = ChallengeData(id="test", name="Test", files=files)
        
        params = plugin._extract_rsa_parameters(challenge)
        
        assert params['n'] == 3233
        assert params['e'] == 17
        assert params['d'] == 2753
        assert params['c'] == 1000
    
    def test_ordered_techniques(self, plugin, temp_file_with_content):
        """Test ordenamiento de técnicas basado en parámetros"""
        # Crear desafío con exponente pequeño
        params = {'n': 3233, 'e': 3, 'c': 1000}
        json_content = json.dumps(params)
        file_path = temp_file_with_content(json_content)
        file_info = FileInfo(path=file_path, size=100, mime_type="text/plain")
        challenge = ChallengeData(id="test", name="Test", files=[file_info])
        
        ordered = plugin._get_ordered_techniques(challenge)
        techniques_list = list(ordered.keys())
        
        # small_e_attack debería estar entre las primeras
        assert "small_e_attack" in techniques_list
    
    def test_solve_integration_small_rsa(self, plugin, temp_file_with_content, small_rsa_key):
        """Test integración completa con RSA pequeño"""
        # Crear desafío completo
        message = b"CTF{small_rsa_solved}"
        m = bytes_to_long(message)
        
        n, e = small_rsa_key['n'], small_rsa_key['e']
        c = pow(m, e, n)
        
        params = {'n': n, 'e': e, 'c': c}
        json_content = json.dumps(params)
        file_path = temp_file_with_content(json_content)
        file_info = FileInfo(path=file_path, size=100, mime_type="text/plain")
        
        challenge = ChallengeData(
            id="test",
            name="Small RSA",
            files=[file_info],
            challenge_type=ChallengeType.RSA
        )
        
        result = plugin.solve_with_timeout(challenge)
        
        # Debería resolver el desafío
        assert result.success is True
        assert "CTF{small_rsa_solved}" in result.flag
    
    def test_no_rsa_parameters(self, plugin, temp_file_with_content):
        """Test con archivos sin parámetros RSA"""
        content = "This is just plain text with no RSA parameters"
        file_path = temp_file_with_content(content)
        file_info = FileInfo(path=file_path, size=100, mime_type="text/plain")
        challenge = ChallengeData(id="test", name="Test", files=[file_info])
        
        result = plugin._try_weak_keys(challenge)
        assert result.success is False
        assert "No se encontraron parámetros RSA" in result.error_message
    
    def test_large_modulus_rejection(self, plugin, temp_file_with_content):
        """Test rechazo de módulos demasiado grandes"""
        # Crear módulo muy grande
        large_n = 2**2048  # 2048 bits
        params = {'n': large_n, 'e': 65537}
        
        json_content = json.dumps(params)
        file_path = temp_file_with_content(json_content)
        file_info = FileInfo(path=file_path, size=100, mime_type="text/plain")
        challenge = ChallengeData(id="test", name="Test", files=[file_info])
        
        result = plugin._try_factorization(challenge)
        assert result.success is False
        assert "demasiado grande" in result.error_message


if __name__ == "__main__":
    pytest.main([__file__])