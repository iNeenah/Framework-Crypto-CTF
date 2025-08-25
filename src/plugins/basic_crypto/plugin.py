"""
Plugin de Criptografía Básica - Cifrados clásicos y técnicas básicas
"""

import re
import string
import itertools
from collections import Counter
from typing import List, Dict, Any, Optional, Tuple
import base64
import binascii

from ..base import MultiTechniquePlugin
from ...models.data import ChallengeData, SolutionResult, PluginInfo, ChallengeType
from ...utils.logging import get_logger


class BasicCryptoPlugin(MultiTechniquePlugin):
    """Plugin para resolver desafíos de criptografía básica"""
    
    def __init__(self):
        super().__init__()
        
        # Frecuencias del español (más común en CTFs latinos)
        self.spanish_freq = {
            'a': 12.53, 'e': 13.68, 'i': 6.25, 'o': 8.68, 'u': 3.93,
            'n': 6.71, 'r': 6.87, 's': 7.98, 't': 4.63, 'l': 4.97,
            'd': 5.86, 'c': 4.68, 'm': 3.15, 'p': 2.51, 'b': 1.42,
            'g': 1.01, 'v': 0.90, 'y': 0.90, 'f': 0.70, 'h': 0.70,
            'q': 0.88, 'j': 0.44, 'z': 0.52, 'x': 0.22, 'k': 0.02, 'w': 0.02
        }
        
        # Frecuencias del inglés (backup)
        self.english_freq = {
            'a': 8.12, 'b': 1.49, 'c': 2.78, 'd': 4.25, 'e': 12.02,
            'f': 2.23, 'g': 2.02, 'h': 6.09, 'i': 6.97, 'j': 0.15,
            'k': 0.77, 'l': 4.03, 'm': 2.41, 'n': 6.75, 'o': 7.51,
            'p': 1.93, 'q': 0.10, 'r': 5.99, 's': 6.33, 't': 9.06,
            'u': 2.76, 'v': 0.98, 'w': 2.36, 'x': 0.15, 'y': 1.97, 'z': 0.07
        }
        
        # Palabras comunes para validación
        self.common_words_spanish = [
            'que', 'de', 'la', 'el', 'en', 'y', 'a', 'es', 'se', 'no',
            'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para',
            'flag', 'ctf', 'clave', 'password', 'bandera'
        ]
        
        self.common_words_english = [
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
            'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has',
            'flag', 'ctf', 'key', 'password', 'cipher'
        ]
    
    def _create_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="basic_crypto",
            version="1.0.0",
            description="Plugin para criptografía básica y cifrados clásicos",
            supported_types=[ChallengeType.BASIC_CRYPTO, ChallengeType.MIXED],
            techniques=[
                "caesar_cipher", "vigenere_cipher", "atbash_cipher",
                "substitution_cipher", "xor_cipher", "base64_decode",
                "rot13", "frequency_analysis", "brute_force"
            ],
            priority=70
        )
    
    def can_solve(self, challenge_data: ChallengeData) -> float:
        """Evaluar si puede manejar el desafío"""
        confidence = 0.0
        
        # Verificar tipo de desafío
        if challenge_data.challenge_type == ChallengeType.BASIC_CRYPTO:
            confidence += 0.8
        elif challenge_data.challenge_type == ChallengeType.MIXED:
            confidence += 0.4
        
        # Analizar archivos
        for file_info in challenge_data.files:
            filename = file_info.path.name.lower()
            
            # Patrones en nombres de archivo
            basic_patterns = [
                'caesar', 'vigenere', 'substitution', 'cipher', 'encode',
                'decode', 'xor', 'base64', 'rot13', 'atbash', 'frequency'
            ]
            
            for pattern in basic_patterns:
                if pattern in filename:
                    confidence += 0.2
                    break
            
            # Analizar contenido si es texto
            if self._is_text_file(file_info):
                content = self._read_file_content(file_info.path)
                if content:
                    content_confidence = self._analyze_content_for_basic_crypto(content)
                    confidence += content_confidence * 0.3
        
        return min(confidence, 1.0)
    
    def _initialize_techniques(self) -> Dict[str, callable]:
        """Inicializar técnicas disponibles"""
        return {
            "base64_decode": self._try_base64_decode,
            "caesar_cipher": self._try_caesar_cipher,
            "rot13": self._try_rot13,
            "atbash_cipher": self._try_atbash_cipher,
            "xor_cipher": self._try_xor_cipher,
            "vigenere_cipher": self._try_vigenere_cipher,
            "substitution_cipher": self._try_substitution_cipher,
            "frequency_analysis": self._try_frequency_analysis
        }
    
    def _get_ordered_techniques(self, challenge_data: ChallengeData) -> Dict[str, callable]:
        """Ordenar técnicas por probabilidad de éxito"""
        techniques = self._techniques.copy()
        
        # Analizar contenido para priorizar técnicas
        content_hints = []
        for file_info in challenge_data.files:
            if self._is_text_file(file_info):
                content = self._read_file_content(file_info.path)
                if content:
                    content_hints.extend(self._get_content_hints(content))
        
        # Reordenar basado en hints
        ordered_techniques = {}
        
        # Técnicas de alta prioridad basadas en hints
        if 'base64' in content_hints or self._looks_like_base64(str(content_hints)):
            ordered_techniques["base64_decode"] = techniques.pop("base64_decode", None)
        
        if 'caesar' in content_hints or 'shift' in content_hints:
            ordered_techniques["caesar_cipher"] = techniques.pop("caesar_cipher", None)
        
        if 'rot13' in content_hints:
            ordered_techniques["rot13"] = techniques.pop("rot13", None)
        
        if 'xor' in content_hints:
            ordered_techniques["xor_cipher"] = techniques.pop("xor_cipher", None)
        
        if 'vigenere' in content_hints or 'key' in content_hints:
            ordered_techniques["vigenere_cipher"] = techniques.pop("vigenere_cipher", None)
        
        # Agregar técnicas restantes
        ordered_techniques.update(techniques)
        
        # Filtrar None values
        return {k: v for k, v in ordered_techniques.items() if v is not None}
    
    def _is_text_file(self, file_info) -> bool:
        """Verificar si es archivo de texto"""
        if file_info.mime_type and 'text' in file_info.mime_type:
            return True
        
        text_extensions = {'.txt', '.md', '.py', '.c', '.cpp', '.java', '.js', '.html'}
        return file_info.path.suffix.lower() in text_extensions
    
    def _analyze_content_for_basic_crypto(self, content: str) -> float:
        """Analizar contenido para detectar criptografía básica"""
        confidence = 0.0
        content_lower = content.lower()
        
        # Patrones de criptografía básica
        patterns = [
            'cipher', 'encode', 'decode', 'encrypt', 'decrypt',
            'caesar', 'vigenere', 'substitution', 'xor', 'base64',
            'rot13', 'atbash', 'frequency', 'shift', 'key'
        ]
        
        for pattern in patterns:
            if pattern in content_lower:
                confidence += 0.1
        
        # Detectar posibles textos cifrados
        if self._looks_like_base64(content):
            confidence += 0.3
        elif self._looks_like_hex(content):
            confidence += 0.2
        elif self._has_unusual_frequency(content):
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _get_content_hints(self, content: str) -> List[str]:
        """Extraer hints del contenido"""
        hints = []
        content_lower = content.lower()
        
        hint_patterns = {
            'base64': ['base64', 'b64'],
            'caesar': ['caesar', 'shift', 'rot'],
            'rot13': ['rot13', 'rot 13'],
            'xor': ['xor', 'exclusive or'],
            'vigenere': ['vigenere', 'vigenère', 'key'],
            'substitution': ['substitution', 'replace'],
            'atbash': ['atbash']
        }
        
        for hint_type, patterns in hint_patterns.items():
            for pattern in patterns:
                if pattern in content_lower:
                    hints.append(hint_type)
                    break
        
        return hints
    
    def _looks_like_base64(self, text: str) -> bool:
        """Verificar si el texto parece Base64"""
        # Limpiar whitespace
        text = re.sub(r'\s', '', text)
        
        # Verificar caracteres válidos
        if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', text):
            return False
        
        # Verificar longitud múltiplo de 4
        if len(text) % 4 != 0:
            return False
        
        # Verificar que no sea demasiado corto
        return len(text) >= 4
    
    def _looks_like_hex(self, text: str) -> bool:
        """Verificar si el texto parece hexadecimal"""
        text = re.sub(r'\s', '', text)
        return bool(re.match(r'^[0-9a-fA-F]+$', text)) and len(text) % 2 == 0
    
    def _has_unusual_frequency(self, text: str) -> bool:
        """Verificar si tiene distribución de frecuencia inusual"""
        if len(text) < 50:  # Muy corto para análisis
            return False
        
        # Contar letras
        letter_count = Counter(c.lower() for c in text if c.isalpha())
        if not letter_count:
            return False
        
        total_letters = sum(letter_count.values())
        
        # Calcular chi-cuadrado con frecuencias esperadas del español
        chi_squared = 0
        for letter in string.ascii_lowercase:
            observed = letter_count.get(letter, 0)
            expected = (self.spanish_freq.get(letter, 0.1) / 100) * total_letters
            if expected > 0:
                chi_squared += ((observed - expected) ** 2) / expected
        
        # Si chi-cuadrado es muy alto, la distribución es inusual
        return chi_squared > 50
    
    def _try_base64_decode(self, challenge_data: ChallengeData) -> SolutionResult:
        """Intentar decodificación Base64"""
        self.logger.info("Probando decodificación Base64")
        
        for file_info in challenge_data.files:
            content = self._read_file_content(file_info.path)
            if not content:
                continue
            
            # Buscar strings que parezcan Base64
            base64_candidates = self._extract_base64_candidates(content)
            
            for candidate in base64_candidates:
                try:
                    decoded = base64.b64decode(candidate).decode('utf-8', errors='ignore')
                    
                    # Verificar si el resultado parece válido
                    if self._looks_like_valid_text(decoded):
                        flag = self._extract_flag(decoded)
                        if flag:
                            return self._create_success_result(
                                flag=flag,
                                method="base64_decode",
                                confidence=0.9,
                                decoded_text=decoded,
                                original_encoded=candidate
                            )
                        
                        # Si no hay flag pero el texto parece válido, reportar
                        if len(decoded) > 10:
                            return self._create_success_result(
                                flag=decoded.strip(),
                                method="base64_decode",
                                confidence=0.7,
                                decoded_text=decoded
                            )
                            
                except Exception:
                    continue
        
        return self._create_failure_result("No se encontraron decodificaciones Base64 válidas")
    
    def _try_caesar_cipher(self, challenge_data: ChallengeData) -> SolutionResult:
        """Intentar cifrado César con todos los desplazamientos"""
        self.logger.info("Probando cifrado César")
        
        for file_info in challenge_data.files:
            content = self._read_file_content(file_info.path)
            if not content:
                continue
            
            # Extraer texto cifrado
            cipher_text = self._extract_cipher_text(content)
            if not cipher_text:
                continue
            
            # Probar todos los desplazamientos
            best_result = None
            best_score = 0
            
            for shift in range(1, 26):
                decrypted = self._caesar_decrypt(cipher_text, shift)
                score = self._score_text_quality(decrypted)
                
                if score > best_score:
                    best_score = score
                    best_result = (decrypted, shift)
                
                # Buscar flag directamente
                flag = self._extract_flag(decrypted)
                if flag:
                    return self._create_success_result(
                        flag=flag,
                        method="caesar_cipher",
                        confidence=0.95,
                        shift=shift,
                        decrypted_text=decrypted
                    )
            
            # Si encontramos un buen resultado sin flag explícita
            if best_result and best_score > 0.3:
                decrypted, shift = best_result
                return self._create_success_result(
                    flag=decrypted.strip(),
                    method="caesar_cipher",
                    confidence=best_score,
                    shift=shift,
                    decrypted_text=decrypted
                )
        
        return self._create_failure_result("No se encontraron descifraciones César válidas")
    
    def _try_rot13(self, challenge_data: ChallengeData) -> SolutionResult:
        """Intentar ROT13"""
        self.logger.info("Probando ROT13")
        
        for file_info in challenge_data.files:
            content = self._read_file_content(file_info.path)
            if not content:
                continue
            
            # ROT13 es César con shift 13
            cipher_text = self._extract_cipher_text(content)
            if cipher_text:
                decrypted = self._caesar_decrypt(cipher_text, 13)
                
                flag = self._extract_flag(decrypted)
                if flag:
                    return self._create_success_result(
                        flag=flag,
                        method="rot13",
                        confidence=0.9,
                        decrypted_text=decrypted
                    )
                
                # Verificar calidad del texto
                if self._score_text_quality(decrypted) > 0.4:
                    return self._create_success_result(
                        flag=decrypted.strip(),
                        method="rot13",
                        confidence=0.7,
                        decrypted_text=decrypted
                    )
        
        return self._create_failure_result("ROT13 no produjo resultados válidos")
    
    def _try_atbash_cipher(self, challenge_data: ChallengeData) -> SolutionResult:
        """Intentar cifrado Atbash"""
        self.logger.info("Probando cifrado Atbash")
        
        for file_info in challenge_data.files:
            content = self._read_file_content(file_info.path)
            if not content:
                continue
            
            cipher_text = self._extract_cipher_text(content)
            if cipher_text:
                decrypted = self._atbash_decrypt(cipher_text)
                
                flag = self._extract_flag(decrypted)
                if flag:
                    return self._create_success_result(
                        flag=flag,
                        method="atbash_cipher",
                        confidence=0.9,
                        decrypted_text=decrypted
                    )
                
                if self._score_text_quality(decrypted) > 0.4:
                    return self._create_success_result(
                        flag=decrypted.strip(),
                        method="atbash_cipher",
                        confidence=0.7,
                        decrypted_text=decrypted
                    )
        
        return self._create_failure_result("Atbash no produjo resultados válidos")
    
    def _try_xor_cipher(self, challenge_data: ChallengeData) -> SolutionResult:
        """Intentar cifrado XOR con claves comunes"""
        self.logger.info("Probando cifrado XOR")
        
        # Claves comunes para probar
        common_keys = [
            b'key', b'password', b'secret', b'ctf', b'flag',
            *[bytes([i]) for i in range(1, 256)],  # Single byte keys
            b'abc', b'123', b'xyz'
        ]
        
        for file_info in challenge_data.files:
            # Intentar leer como binario primero
            binary_content = self._read_file_bytes(file_info.path)
            if binary_content:
                for key in common_keys:
                    try:
                        decrypted = self._xor_decrypt(binary_content, key)
                        decoded_text = decrypted.decode('utf-8', errors='ignore')
                        
                        flag = self._extract_flag(decoded_text)
                        if flag:
                            return self._create_success_result(
                                flag=flag,
                                method="xor_cipher",
                                confidence=0.9,
                                key=key.hex() if isinstance(key, bytes) else str(key),
                                decrypted_text=decoded_text
                            )
                        
                        if self._score_text_quality(decoded_text) > 0.4:
                            return self._create_success_result(
                                flag=decoded_text.strip(),
                                method="xor_cipher",
                                confidence=0.7,
                                key=key.hex() if isinstance(key, bytes) else str(key),
                                decrypted_text=decoded_text
                            )
                    except Exception:
                        continue
            
            # También probar con contenido de texto convertido a hex
            text_content = self._read_file_content(file_info.path)
            if text_content and self._looks_like_hex(text_content):
                try:
                    hex_bytes = bytes.fromhex(text_content.replace(' ', '').replace('\n', ''))
                    for key in common_keys:
                        try:
                            decrypted = self._xor_decrypt(hex_bytes, key)
                            decoded_text = decrypted.decode('utf-8', errors='ignore')
                            
                            flag = self._extract_flag(decoded_text)
                            if flag:
                                return self._create_success_result(
                                    flag=flag,
                                    method="xor_cipher",
                                    confidence=0.9,
                                    key=key.hex(),
                                    decrypted_text=decoded_text
                                )
                        except Exception:
                            continue
                except ValueError:
                    continue
        
        return self._create_failure_result("XOR no produjo resultados válidos")
    
    def _try_vigenere_cipher(self, challenge_data: ChallengeData) -> SolutionResult:
        """Intentar cifrado Vigenère con claves comunes"""
        self.logger.info("Probando cifrado Vigenère")
        
        common_keys = [
            'key', 'password', 'secret', 'ctf', 'flag', 'crypto',
            'vigenere', 'cipher', 'code', 'hack'
        ]
        
        for file_info in challenge_data.files:
            content = self._read_file_content(file_info.path)
            if not content:
                continue
            
            cipher_text = self._extract_cipher_text(content)
            if not cipher_text:
                continue
            
            for key in common_keys:
                decrypted = self._vigenere_decrypt(cipher_text, key)
                
                flag = self._extract_flag(decrypted)
                if flag:
                    return self._create_success_result(
                        flag=flag,
                        method="vigenere_cipher",
                        confidence=0.9,
                        key=key,
                        decrypted_text=decrypted
                    )
                
                if self._score_text_quality(decrypted) > 0.5:
                    return self._create_success_result(
                        flag=decrypted.strip(),
                        method="vigenere_cipher",
                        confidence=0.7,
                        key=key,
                        decrypted_text=decrypted
                    )
        
        return self._create_failure_result("Vigenère no produjo resultados válidos")
    
    def _try_substitution_cipher(self, challenge_data: ChallengeData) -> SolutionResult:
        """Intentar cifrado de sustitución usando análisis de frecuencia"""
        self.logger.info("Probando cifrado de sustitución")
        
        for file_info in challenge_data.files:
            content = self._read_file_content(file_info.path)
            if not content:
                continue
            
            cipher_text = self._extract_cipher_text(content)
            if not cipher_text or len(cipher_text) < 50:  # Necesitamos texto suficiente
                continue
            
            # Análisis de frecuencia básico
            decrypted = self._frequency_analysis_substitution(cipher_text)
            
            flag = self._extract_flag(decrypted)
            if flag:
                return self._create_success_result(
                    flag=flag,
                    method="substitution_cipher",
                    confidence=0.8,
                    decrypted_text=decrypted
                )
            
            if self._score_text_quality(decrypted) > 0.3:
                return self._create_success_result(
                    flag=decrypted.strip(),
                    method="substitution_cipher",
                    confidence=0.6,
                    decrypted_text=decrypted
                )
        
        return self._create_failure_result("Sustitución no produjo resultados válidos")
    
    def _try_frequency_analysis(self, challenge_data: ChallengeData) -> SolutionResult:
        """Realizar análisis de frecuencia general"""
        self.logger.info("Realizando análisis de frecuencia")
        
        analysis_results = {}
        
        for file_info in challenge_data.files:
            content = self._read_file_content(file_info.path)
            if not content:
                continue
            
            # Análisis de frecuencia
            freq_analysis = self._analyze_frequency(content)
            analysis_results[str(file_info.path)] = freq_analysis
            
            # Intentar detectar patrones
            patterns = self._detect_patterns(content)
            if patterns:
                analysis_results[f"{file_info.path}_patterns"] = patterns
        
        if analysis_results:
            return SolutionResult(
                success=False,  # Es análisis, no solución directa
                method_used="frequency_analysis",
                confidence=0.5,
                details=analysis_results
            )
        
        return self._create_failure_result("No se pudo realizar análisis de frecuencia")
    
    # Métodos auxiliares de criptografía
    
    def _extract_base64_candidates(self, content: str) -> List[str]:
        """Extraer candidatos Base64 del contenido"""
        candidates = []
        
        # Buscar bloques que parezcan Base64
        base64_pattern = r'[A-Za-z0-9+/]{4,}={0,2}'
        matches = re.findall(base64_pattern, content)
        
        for match in matches:
            if self._looks_like_base64(match):
                candidates.append(match)
        
        # También considerar todo el contenido si parece Base64
        clean_content = re.sub(r'\s', '', content)
        if self._looks_like_base64(clean_content):
            candidates.append(clean_content)
        
        return candidates
    
    def _extract_cipher_text(self, content: str) -> str:
        """Extraer texto cifrado del contenido"""
        # Remover comentarios y líneas que parecen instrucciones
        lines = content.split('\n')
        cipher_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Saltar líneas que parecen comentarios o instrucciones
            if line.startswith('#') or line.startswith('//'):
                continue
            if any(word in line.lower() for word in ['decrypt', 'cipher', 'key', 'hint']):
                continue
            
            # Si la línea tiene solo letras/números, probablemente es texto cifrado
            if re.match(r'^[A-Za-z0-9\s]+$', line):
                cipher_lines.append(line)
        
        return ' '.join(cipher_lines) if cipher_lines else content
    
    def _caesar_decrypt(self, text: str, shift: int) -> str:
        """Descifrar texto con César"""
        result = []
        for char in text:
            if char.isalpha():
                base = ord('A') if char.isupper() else ord('a')
                shifted = (ord(char) - base - shift) % 26
                result.append(chr(base + shifted))
            else:
                result.append(char)
        return ''.join(result)
    
    def _atbash_decrypt(self, text: str) -> str:
        """Descifrar texto con Atbash"""
        result = []
        for char in text:
            if char.isalpha():
                if char.isupper():
                    result.append(chr(ord('Z') - (ord(char) - ord('A'))))
                else:
                    result.append(chr(ord('z') - (ord(char) - ord('a'))))
            else:
                result.append(char)
        return ''.join(result)
    
    def _xor_decrypt(self, data: bytes, key: bytes) -> bytes:
        """Descifrar datos con XOR"""
        result = bytearray()
        key_len = len(key)
        
        for i, byte in enumerate(data):
            result.append(byte ^ key[i % key_len])
        
        return bytes(result)
    
    def _vigenere_decrypt(self, text: str, key: str) -> str:
        """Descifrar texto con Vigenère"""
        result = []
        key = key.upper()
        key_len = len(key)
        key_index = 0
        
        for char in text:
            if char.isalpha():
                base = ord('A') if char.isupper() else ord('a')
                key_shift = ord(key[key_index % key_len]) - ord('A')
                shifted = (ord(char.upper()) - ord('A') - key_shift) % 26
                
                if char.isupper():
                    result.append(chr(ord('A') + shifted))
                else:
                    result.append(chr(ord('a') + shifted))
                
                key_index += 1
            else:
                result.append(char)
        
        return ''.join(result)
    
    def _frequency_analysis_substitution(self, cipher_text: str) -> str:
        """Análisis de frecuencia básico para sustitución"""
        # Contar frecuencias
        letter_freq = Counter(c.lower() for c in cipher_text if c.isalpha())
        
        if not letter_freq:
            return cipher_text
        
        # Ordenar por frecuencia
        sorted_cipher = sorted(letter_freq.items(), key=lambda x: x[1], reverse=True)
        sorted_spanish = sorted(self.spanish_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Crear mapeo básico
        substitution_map = {}
        for i, (cipher_char, _) in enumerate(sorted_cipher):
            if i < len(sorted_spanish):
                substitution_map[cipher_char] = sorted_spanish[i][0]
        
        # Aplicar sustitución
        result = []
        for char in cipher_text:
            if char.isalpha():
                lower_char = char.lower()
                if lower_char in substitution_map:
                    new_char = substitution_map[lower_char]
                    result.append(new_char.upper() if char.isupper() else new_char)
                else:
                    result.append(char)
            else:
                result.append(char)
        
        return ''.join(result)
    
    def _analyze_frequency(self, text: str) -> Dict[str, Any]:
        """Analizar frecuencia de caracteres"""
        letter_count = Counter(c.lower() for c in text if c.isalpha())
        total_letters = sum(letter_count.values())
        
        if total_letters == 0:
            return {}
        
        frequency_percent = {
            char: (count / total_letters) * 100
            for char, count in letter_count.items()
        }
        
        return {
            'letter_frequencies': frequency_percent,
            'total_letters': total_letters,
            'unique_letters': len(letter_count),
            'most_common': letter_count.most_common(5)
        }
    
    def _detect_patterns(self, text: str) -> Dict[str, Any]:
        """Detectar patrones en el texto"""
        patterns = {}
        
        # Patrones de repetición
        repeated_patterns = re.findall(r'(.{2,10})\1+', text)
        if repeated_patterns:
            patterns['repeated_sequences'] = repeated_patterns[:5]
        
        # Longitud de palabras
        words = re.findall(r'[A-Za-z]+', text)
        if words:
            word_lengths = [len(word) for word in words]
            patterns['word_length_stats'] = {
                'average': sum(word_lengths) / len(word_lengths),
                'min': min(word_lengths),
                'max': max(word_lengths)
            }
        
        return patterns
    
    def _score_text_quality(self, text: str) -> float:
        """Puntuar calidad del texto (qué tan probable es que sea texto real)"""
        if not text or len(text) < 5:
            return 0.0
        
        score = 0.0
        text_lower = text.lower()
        
        # Verificar palabras comunes
        words = re.findall(r'[a-z]+', text_lower)
        if words:
            common_word_count = sum(1 for word in words 
                                  if word in self.common_words_spanish or 
                                     word in self.common_words_english)
            score += (common_word_count / len(words)) * 0.5
        
        # Verificar distribución de frecuencia
        letter_count = Counter(c for c in text_lower if c.isalpha())
        if letter_count:
            total_letters = sum(letter_count.values())
            
            # Calcular similitud con frecuencias esperadas
            chi_squared = 0
            for letter in string.ascii_lowercase:
                observed = letter_count.get(letter, 0)
                expected = (self.spanish_freq.get(letter, 0.1) / 100) * total_letters
                if expected > 0:
                    chi_squared += ((observed - expected) ** 2) / expected
            
            # Convertir chi-cuadrado a score (menor chi-cuadrado = mejor score)
            freq_score = max(0, 1 - (chi_squared / 100))
            score += freq_score * 0.3
        
        # Verificar caracteres imprimibles
        printable_ratio = sum(1 for c in text if c.isprintable()) / len(text)
        score += printable_ratio * 0.2
        
        return min(score, 1.0)
    
    def _looks_like_valid_text(self, text: str) -> bool:
        """Verificar si el texto parece válido"""
        if not text or len(text) < 3:
            return False
        
        # Verificar que tenga caracteres imprimibles
        printable_ratio = sum(1 for c in text if c.isprintable()) / len(text)
        if printable_ratio < 0.8:
            return False
        
        # Verificar que no sea solo números o símbolos
        alpha_ratio = sum(1 for c in text if c.isalpha()) / len(text)
        if alpha_ratio < 0.3:
            return False
        
        return True
    
    def _extract_flag(self, text: str) -> Optional[str]:
        """Extraer flag del texto"""
        # Patrones comunes de flags
        flag_patterns = [
            r'CTF\{[^}]+\}',
            r'FLAG\{[^}]+\}',
            r'flag\{[^}]+\}',
            r'ctf\{[^}]+\}',
            r'\{[^}]{10,}\}',  # Cualquier cosa entre llaves con longitud mínima
        ]
        
        for pattern in flag_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        # Si no hay flag explícita pero el texto parece ser la respuesta
        if len(text.strip()) < 100 and self._looks_like_valid_text(text):
            return text.strip()
        
        return None