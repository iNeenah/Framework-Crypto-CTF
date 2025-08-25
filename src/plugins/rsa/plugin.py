"""
Plugin RSA Avanzado - Ataques y técnicas para RSA
"""

import re
import math
from typing import List, Dict, Any, Optional, Tuple
import base64
import json

try:
    import gmpy2
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_OAEP
    from Crypto.Util.number import inverse, long_to_bytes, bytes_to_long
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from .rsa_math import RSAMath

from ..base import MultiTechniquePlugin
from ...models.data import ChallengeData, SolutionResult, PluginInfo, ChallengeType
from ...utils.logging import get_logger


class RSAPlugin(MultiTechniquePlugin):
    """Plugin para ataques RSA avanzados"""
    
    def __init__(self):
        super().__init__()
        
        # Límites para diferentes técnicas
        self.max_factorization_bits = 512  # Máximo para factorización directa
        self.max_wiener_bits = 1024       # Máximo para ataque Wiener
        self.max_small_e = 65537          # Máximo exponente para ataques de e pequeño
        
        # Primos pequeños para factorización rápida
        self.small_primes = self._generate_small_primes(10000)
    
    def _create_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="rsa_advanced",
            version="1.0.0",
            description="Plugin para ataques RSA avanzados y factorización",
            supported_types=[ChallengeType.RSA, ChallengeType.MIXED],
            techniques=[
                "weak_keys", "small_e_attack", "wiener_attack", "hastad_attack",
                "common_modulus", "factorization", "pollard_rho", "fermat_factorization",
                "low_public_exponent", "partial_key_recovery"
            ],
            priority=85
        )
    
    def can_solve(self, challenge_data: ChallengeData) -> float:
        """Evaluar si puede manejar el desafío RSA"""
        confidence = 0.0
        
        # Verificar tipo de desafío
        if challenge_data.challenge_type == ChallengeType.RSA:
            confidence += 0.9
        elif challenge_data.challenge_type == ChallengeType.MIXED:
            confidence += 0.5
        
        # Buscar indicadores RSA en archivos
        rsa_indicators = 0
        for file_info in challenge_data.files:
            filename = file_info.path.name.lower()
            
            # Patrones en nombres de archivo
            if any(pattern in filename for pattern in ['rsa', 'public', 'private', 'key', 'pem']):
                rsa_indicators += 1
                confidence += 0.2
            
            # Analizar contenido
            if self._is_text_file(file_info):
                content = self._read_file_content(file_info.path)
                if content:
                    rsa_content_score = self._analyze_rsa_content(content)
                    confidence += rsa_content_score * 0.3
                    if rsa_content_score > 0.5:
                        rsa_indicators += 1
        
        # Bonus si hay múltiples indicadores RSA
        if rsa_indicators >= 2:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _initialize_techniques(self) -> Dict[str, callable]:
        """Inicializar técnicas RSA"""
        return {
            "weak_keys": self._try_weak_keys,
            "small_e_attack": self._try_small_e_attack,
            "factorization": self._try_factorization,
            "wiener_attack": self._try_wiener_attack,
            "hastad_attack": self._try_hastad_attack,
            "common_modulus": self._try_common_modulus,
            "pollard_rho": self._try_pollard_rho,
            "fermat_factorization": self._try_fermat_factorization,
            "low_public_exponent": self._try_low_public_exponent
        }
    
    def _get_ordered_techniques(self, challenge_data: ChallengeData) -> Dict[str, callable]:
        """Ordenar técnicas RSA por probabilidad de éxito"""
        techniques = self._techniques.copy()
        ordered_techniques = {}
        
        # Analizar parámetros RSA para priorizar técnicas
        rsa_params = self._extract_rsa_parameters(challenge_data)
        
        if rsa_params:
            n = rsa_params.get('n')
            e = rsa_params.get('e')
            
            # Priorizar basado en características
            if e and e <= 3:
                ordered_techniques["small_e_attack"] = techniques.pop("small_e_attack", None)
                ordered_techniques["hastad_attack"] = techniques.pop("hastad_attack", None)
            
            if n and n.bit_length() <= self.max_factorization_bits:
                ordered_techniques["factorization"] = techniques.pop("factorization", None)
                ordered_techniques["pollard_rho"] = techniques.pop("pollard_rho", None)
                ordered_techniques["fermat_factorization"] = techniques.pop("fermat_factorization", None)
            
            if e and self._is_wiener_vulnerable(n, e):
                ordered_techniques["wiener_attack"] = techniques.pop("wiener_attack", None)
        
        # Técnicas generales al final
        ordered_techniques["weak_keys"] = techniques.pop("weak_keys", None)
        ordered_techniques.update(techniques)
        
        return {k: v for k, v in ordered_techniques.items() if v is not None}
    
    def _is_text_file(self, file_info) -> bool:
        """Verificar si es archivo de texto"""
        if file_info.mime_type and 'text' in file_info.mime_type:
            return True
        
        text_extensions = {'.txt', '.pem', '.key', '.pub', '.json', '.py', '.c'}
        return file_info.path.suffix.lower() in text_extensions
    
    def _analyze_rsa_content(self, content: str) -> float:
        """Analizar contenido para detectar elementos RSA"""
        confidence = 0.0
        content_lower = content.lower()
        
        # Patrones RSA
        rsa_patterns = [
            'rsa', 'modulus', 'exponent', 'public key', 'private key',
            'factorization', 'prime', 'wiener', 'hastad', 'common modulus'
        ]
        
        for pattern in rsa_patterns:
            if pattern in content_lower:
                confidence += 0.1
        
        # Detectar claves PEM
        if '-----BEGIN' in content and 'KEY-----' in content:
            confidence += 0.4
        
        # Detectar números grandes (posibles parámetros RSA)
        large_numbers = re.findall(r'\b\d{50,}\b', content)
        if large_numbers:
            confidence += 0.3
        
        # Detectar formato JSON con parámetros RSA
        if self._looks_like_rsa_json(content):
            confidence += 0.5
        
        return min(confidence, 1.0)
    
    def _looks_like_rsa_json(self, content: str) -> bool:
        """Verificar si parece JSON con parámetros RSA"""
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                rsa_keys = {'n', 'e', 'd', 'p', 'q', 'dp', 'dq', 'qi'}
                return len(set(data.keys()) & rsa_keys) >= 2
        except:
            pass
        return False
    
    def _extract_rsa_parameters(self, challenge_data: ChallengeData) -> Dict[str, Any]:
        """Extraer parámetros RSA de los archivos"""
        params = {}
        
        for file_info in challenge_data.files:
            content = self._read_file_content(file_info.path)
            if not content:
                continue
            
            # Intentar extraer de diferentes formatos
            file_params = {}
            
            # Formato PEM
            pem_params = self._extract_from_pem(content)
            if pem_params:
                file_params.update(pem_params)
            
            # Formato JSON
            json_params = self._extract_from_json(content)
            if json_params:
                file_params.update(json_params)
            
            # Formato texto plano
            text_params = self._extract_from_text(content)
            if text_params:
                file_params.update(text_params)
            
            # Combinar parámetros
            params.update(file_params)
        
        return params
    
    def _extract_from_pem(self, content: str) -> Dict[str, Any]:
        """Extraer parámetros de formato PEM"""
        params = {}
        
        try:
            # Intentar cargar como clave RSA
            if '-----BEGIN RSA' in content or '-----BEGIN PUBLIC KEY' in content:
                key = RSA.import_key(content)
                params['n'] = key.n
                params['e'] = key.e
                if hasattr(key, 'd') and key.d:
                    params['d'] = key.d
                if hasattr(key, 'p') and key.p:
                    params['p'] = key.p
                if hasattr(key, 'q') and key.q:
                    params['q'] = key.q
        except Exception as e:
            self.logger.debug(f"Error extrayendo PEM: {e}")
        
        return params
    
    def _extract_from_json(self, content: str) -> Dict[str, Any]:
        """Extraer parámetros de formato JSON"""
        params = {}
        
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                # Convertir strings a enteros si es necesario
                for key in ['n', 'e', 'd', 'p', 'q', 'dp', 'dq', 'qi']:
                    if key in data:
                        value = data[key]
                        if isinstance(value, str):
                            # Intentar diferentes bases
                            try:
                                if value.startswith('0x'):
                                    params[key] = int(value, 16)
                                else:
                                    params[key] = int(value)
                            except ValueError:
                                continue
                        elif isinstance(value, int):
                            params[key] = value
        except Exception as e:
            self.logger.debug(f"Error extrayendo JSON: {e}")
        
        return params
    
    def _extract_from_text(self, content: str) -> Dict[str, Any]:
        """Extraer parámetros de texto plano"""
        params = {}
        
        # Patrones para diferentes parámetros
        patterns = {
            'n': [r'n\s*[=:]\s*(\d+)', r'modulus\s*[=:]\s*(\d+)', r'N\s*[=:]\s*(\d+)'],
            'e': [r'e\s*[=:]\s*(\d+)', r'exponent\s*[=:]\s*(\d+)', r'E\s*[=:]\s*(\d+)'],
            'd': [r'd\s*[=:]\s*(\d+)', r'private\s*[=:]\s*(\d+)', r'D\s*[=:]\s*(\d+)'],
            'p': [r'p\s*[=:]\s*(\d+)', r'P\s*[=:]\s*(\d+)'],
            'q': [r'q\s*[=:]\s*(\d+)', r'Q\s*[=:]\s*(\d+)'],
            'c': [r'c\s*[=:]\s*(\d+)', r'ciphertext\s*[=:]\s*(\d+)', r'cipher\s*[=:]\s*(\d+)']
        }
        
        for param, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    try:
                        params[param] = int(matches[0])
                        break
                    except ValueError:
                        continue
        
        return params
    
    def _generate_small_primes(self, limit: int) -> List[int]:
        """Generar lista de primos pequeños usando criba de Eratóstenes"""
        sieve = [True] * (limit + 1)
        sieve[0] = sieve[1] = False
        
        for i in range(2, int(math.sqrt(limit)) + 1):
            if sieve[i]:
                for j in range(i * i, limit + 1, i):
                    sieve[j] = False
        
        return [i for i in range(2, limit + 1) if sieve[i]]
    
    def _try_weak_keys(self, challenge_data: ChallengeData) -> SolutionResult:
        """Detectar claves RSA débiles"""
        self.logger.info("Verificando claves RSA débiles")
        
        params = self._extract_rsa_parameters(challenge_data)
        if not params.get('n') or not params.get('e'):
            return self._create_failure_result("No se encontraron parámetros RSA válidos")
        
        n, e = params['n'], params['e']
        
        # Verificar factores pequeños
        for prime in self.small_primes[:1000]:  # Primeros 1000 primos
            if n % prime == 0:
                p = prime
                q = n // prime
                if p * q == n:
                    self.logger.info(f"Factor pequeño encontrado: {p}")
                    return self._decrypt_with_factors(params, p, q)
        
        # Verificar si n es un cuadrado perfecto
        sqrt_n = int(n ** 0.5)
        if sqrt_n * sqrt_n == n:
            self.logger.info("n es un cuadrado perfecto")
            return self._decrypt_with_factors(params, sqrt_n, sqrt_n)
        
        # Verificar exponente público débil
        if e == 1:
            return self._create_failure_result("Exponente público e=1 (trivial pero inválido)")
        
        if e == 2:
            return self._create_failure_result("Exponente público e=2 (par, inválido)")
        
        return self._create_failure_result("No se detectaron debilidades obvias")
    
    def _try_small_e_attack(self, challenge_data: ChallengeData) -> SolutionResult:
        """Ataque de exponente público pequeño"""
        self.logger.info("Probando ataque de exponente pequeño")
        
        params = self._extract_rsa_parameters(challenge_data)
        if not all(k in params for k in ['n', 'e', 'c']):
            return self._create_failure_result("Faltan parámetros para ataque de e pequeño")
        
        n, e, c = params['n'], params['e'], params['c']
        
        if e > 10:  # Solo para exponentes muy pequeños
            return self._create_failure_result(f"Exponente {e} no es suficientemente pequeño")
        
        # Si c < n, el mensaje podría no estar envuelto por el módulo
        if c < n:
            # Intentar raíz e-ésima directa
            try:
                m = RSAMath.nth_root(c, e)
                if m and pow(m, e) == c:
                    plaintext = self._int_to_bytes(m)
                    flag = self._extract_flag_from_bytes(plaintext)
                    if flag:
                        return self._create_success_result(
                            flag=flag,
                            method="small_e_attack",
                            confidence=0.95,
                            message=plaintext.decode('utf-8', errors='ignore')
                        )
            except Exception as e:
                self.logger.debug(f"Error en raíz directa: {e}")
        
        return self._create_failure_result("Ataque de exponente pequeño no exitoso")
    
    def _try_factorization(self, challenge_data: ChallengeData) -> SolutionResult:
        """Factorización directa para módulos pequeños"""
        self.logger.info("Probando factorización directa")
        
        params = self._extract_rsa_parameters(challenge_data)
        if not params.get('n'):
            return self._create_failure_result("No se encontró módulo n")
        
        n = params['n']
        
        if n.bit_length() > self.max_factorization_bits:
            return self._create_failure_result(f"Módulo demasiado grande ({n.bit_length()} bits)")
        
        # Factorización por división de prueba
        factors = self._trial_division(n)
        if len(factors) >= 2:
            p, q = factors[0], factors[1]
            self.logger.info(f"Factorización exitosa: {p} * {q}")
            return self._decrypt_with_factors(params, p, q)
        
        return self._create_failure_result("Factorización directa no exitosa")
    
    def _try_pollard_rho(self, challenge_data: ChallengeData) -> SolutionResult:
        """Algoritmo Pollard's rho para factorización"""
        self.logger.info("Probando algoritmo Pollard's rho")
        
        params = self._extract_rsa_parameters(challenge_data)
        if not params.get('n'):
            return self._create_failure_result("No se encontró módulo n")
        
        n = params['n']
        
        if n.bit_length() > 1024:  # Límite práctico
            return self._create_failure_result("Módulo demasiado grande para Pollard's rho")
        
        factor = self._pollard_rho_factorize(n)
        if factor and 1 < factor < n:
            p = factor
            q = n // factor
            if p * q == n:
                self.logger.info(f"Pollard's rho exitoso: {p} * {q}")
                return self._decrypt_with_factors(params, p, q)
        
        return self._create_failure_result("Pollard's rho no encontró factores")
    
    def _try_fermat_factorization(self, challenge_data: ChallengeData) -> SolutionResult:
        """Factorización de Fermat para factores cercanos"""
        self.logger.info("Probando factorización de Fermat")
        
        params = self._extract_rsa_parameters(challenge_data)
        if not params.get('n'):
            return self._create_failure_result("No se encontró módulo n")
        
        n = params['n']
        
        factors = self._fermat_factorize(n)
        if factors:
            p, q = factors
            self.logger.info(f"Fermat exitoso: {p} * {q}")
            return self._decrypt_with_factors(params, p, q)
        
        return self._create_failure_result("Factorización de Fermat no exitosa")
    
    def _try_wiener_attack(self, challenge_data: ChallengeData) -> SolutionResult:
        """Ataque de Wiener para exponente privado pequeño"""
        self.logger.info("Probando ataque de Wiener")
        
        params = self._extract_rsa_parameters(challenge_data)
        if not all(k in params for k in ['n', 'e']):
            return self._create_failure_result("Faltan parámetros para ataque de Wiener")
        
        n, e = params['n'], params['e']
        
        if not self._is_wiener_vulnerable(n, e):
            return self._create_failure_result("No parece vulnerable a ataque de Wiener")
        
        # Implementar ataque de Wiener usando fracciones continuas
        d = self._wiener_attack_implementation(n, e)
        if d:
            # Verificar si d es correcto
            if (e * d) % self._euler_phi_estimate(n) == 1:
                params['d'] = d
                if 'c' in params:
                    return self._decrypt_with_private_key(params)
                else:
                    return self._create_success_result(
                        flag=f"d = {d}",
                        method="wiener_attack",
                        confidence=0.9,
                        private_exponent=d
                    )
        
        return self._create_failure_result("Ataque de Wiener no exitoso")
    
    def _try_hastad_attack(self, challenge_data: ChallengeData) -> SolutionResult:
        """Ataque de Håstad para múltiples cifrados con e=3"""
        self.logger.info("Probando ataque de Håstad")
        
        # Este ataque requiere múltiples cifrados del mismo mensaje
        # con diferentes módulos pero mismo exponente pequeño
        
        return self._create_failure_result("Ataque de Håstad requiere múltiples cifrados")
    
    def _try_common_modulus(self, challenge_data: ChallengeData) -> SolutionResult:
        """Ataque de módulo común"""
        self.logger.info("Probando ataque de módulo común")
        
        # Este ataque requiere dos cifrados del mismo mensaje
        # con el mismo módulo pero diferentes exponentes
        
        return self._create_failure_result("Ataque de módulo común requiere múltiples cifrados")
    
    def _try_low_public_exponent(self, challenge_data: ChallengeData) -> SolutionResult:
        """Ataque para exponente público bajo con padding débil"""
        self.logger.info("Probando ataque de exponente público bajo")
        
        params = self._extract_rsa_parameters(challenge_data)
        if not all(k in params for k in ['n', 'e', 'c']):
            return self._create_failure_result("Faltan parámetros para ataque de exponente bajo")
        
        n, e, c = params['n'], params['e'], params['c']
        
        if e > 65537:
            return self._create_failure_result("Exponente no es suficientemente bajo")
        
        # Intentar diferentes variaciones del ataque
        for k in range(0, 100):  # Probar diferentes valores de k
            try:
                # c + k*n podría ser una raíz perfecta
                candidate = c + k * n
                m = RSAMath.nth_root(candidate, e)
                if m and pow(m, e) == candidate:
                    plaintext = self._int_to_bytes(m)
                    flag = self._extract_flag_from_bytes(plaintext)
                    if flag:
                        return self._create_success_result(
                            flag=flag,
                            method="low_public_exponent",
                            confidence=0.9,
                            k_value=k,
                            message=plaintext.decode('utf-8', errors='ignore')
                        )
            except Exception:
                continue
        
        return self._create_failure_result("Ataque de exponente bajo no exitoso")
    
    # Métodos auxiliares de factorización y criptoanálisis
    
    def _trial_division(self, n: int, limit: int = None) -> List[int]:
        """Factorización por división de prueba usando RSAMath"""
        return RSAMath.factorize(n)
    
    def _pollard_rho_factorize(self, n: int) -> Optional[int]:
        """Implementación de Pollard's rho usando nuestra clase RSAMath"""
        return RSAMath.pollard_rho(n)
    
    def _fermat_factorize(self, n: int, max_iterations: int = 10000) -> Optional[Tuple[int, int]]:
        """Factorización de Fermat para factores cercanos"""
        if n % 2 == 0:
            return (2, n // 2)
        
        a = int(n ** 0.5) + 1
        b_squared = a * a - n
        
        for _ in range(max_iterations):
            b = int(b_squared ** 0.5)
            if b * b == b_squared:
                p = a - b
                q = a + b
                if p * q == n and p > 1 and q > 1:
                    return (int(p), int(q))
            
            a += 1
            b_squared = a * a - n
        
        return None
    
    def _is_wiener_vulnerable(self, n: int, e: int) -> bool:
        """Verificar si es vulnerable al ataque de Wiener"""
        # Condición aproximada: e > n^1.5 / 3
        return e > (n ** 1.5) / 3
    
    def _euler_phi_estimate(self, n: int) -> int:
        """Estimación de φ(n) cuando no conocemos p y q"""
        # Para RSA, φ(n) ≈ n cuando n es grande
        return n - 1
    
    def _wiener_attack_implementation(self, n: int, e: int) -> Optional[int]:
        """Implementación simplificada del ataque de Wiener"""
        # Esta es una implementación básica
        # En la práctica, se usarían fracciones continuas
        
        # Buscar d pequeño tal que ed ≡ 1 (mod φ(n))
        for d in range(1, min(10000, int(n**0.25) + 1)):
            if (e * d) % (n - 1) == 1:  # Aproximación
                return d
        
        return None
    
    def _decrypt_with_factors(self, params: Dict[str, Any], p: int, q: int) -> SolutionResult:
        """Descifrar usando factores p y q"""
        if 'c' not in params or 'e' not in params:
            return self._create_success_result(
                flag=f"p = {p}, q = {q}",
                method="factorization",
                confidence=0.9,
                factors=(p, q)
            )
        
        n, e, c = params['n'], params['e'], params['c']
        
        # Calcular φ(n) = (p-1)(q-1)
        phi_n = (p - 1) * (q - 1)
        
        # Calcular d = e^(-1) mod φ(n)
        try:
            d = RSAMath.mod_inverse(e, phi_n)
            if d is None:
                return self._create_failure_result("No se pudo calcular el inverso modular")
            
            # Descifrar
            m = RSAMath.pow_mod(c, d, n)
            plaintext = self._int_to_bytes(m)
            
            flag = self._extract_flag_from_bytes(plaintext)
            if flag:
                return self._create_success_result(
                    flag=flag,
                    method="factorization_decrypt",
                    confidence=0.95,
                    factors=(p, q),
                    private_exponent=d,
                    message=plaintext.decode('utf-8', errors='ignore')
                )
            else:
                return self._create_success_result(
                    flag=plaintext.decode('utf-8', errors='ignore'),
                    method="factorization_decrypt",
                    confidence=0.8,
                    factors=(p, q),
                    private_exponent=d
                )
                
        except Exception as e:
            self.logger.error(f"Error en descifrado: {e}")
            return self._create_failure_result(f"Error calculando clave privada: {str(e)}")
    
    def _decrypt_with_private_key(self, params: Dict[str, Any]) -> SolutionResult:
        """Descifrar usando clave privada conocida"""
        if not all(k in params for k in ['n', 'e', 'd', 'c']):
            return self._create_failure_result("Faltan parámetros para descifrado")
        
        n, e, d, c = params['n'], params['e'], params['d'], params['c']
        
        try:
            m = RSAMath.pow_mod(c, d, n)
            plaintext = self._int_to_bytes(m)
            
            flag = self._extract_flag_from_bytes(plaintext)
            if flag:
                return self._create_success_result(
                    flag=flag,
                    method="private_key_decrypt",
                    confidence=0.95,
                    message=plaintext.decode('utf-8', errors='ignore')
                )
            else:
                return self._create_success_result(
                    flag=plaintext.decode('utf-8', errors='ignore'),
                    method="private_key_decrypt",
                    confidence=0.8
                )
                
        except Exception as e:
            return self._create_failure_result(f"Error en descifrado: {str(e)}")
    
    def _extract_flag_from_bytes(self, data: bytes) -> Optional[str]:
        """Extraer flag de datos binarios"""
        try:
            text = data.decode('utf-8', errors='ignore')
            return self._extract_flag_from_text(text)
        except:
            return None
    
    def _extract_flag_from_text(self, text: str) -> Optional[str]:
        """Extraer flag de texto"""
        # Patrones comunes de flags
        flag_patterns = [
            r'CTF\{[^}]+\}',
            r'FLAG\{[^}]+\}',
            r'flag\{[^}]+\}',
            r'ctf\{[^}]+\}',
            r'\{[^}]{10,}\}',
        ]
        
        for pattern in flag_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        # Si el texto es corto y parece ser la respuesta
        if len(text.strip()) < 100 and len(text.strip()) > 5:
            return text.strip()
        
        return None
    
    def _int_to_bytes(self, n: int) -> bytes:
        """Convertir entero a bytes (alternativa a long_to_bytes)"""
        if n == 0:
            return b'\x00'
        
        byte_length = (n.bit_length() + 7) // 8
        return n.to_bytes(byte_length, 'big')
    
    def _bytes_to_int(self, data: bytes) -> int:
        """Convertir bytes a entero (alternativa a bytes_to_long)"""
        return int.from_bytes(data, 'big')