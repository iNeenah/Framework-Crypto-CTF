#!/usr/bin/env python3
"""
Solver universal para múltiples tipos de desafíos criptográficos
"""
import sys
import os
import re
import base64
import string
from pathlib import Path

# Agregar src al path
sys.path.append('src')

# Importar nuestras herramientas
from plugins.rsa.rsa_math import RSAMath

class UniversalCryptoSolver:
    """Solver universal para desafíos criptográficos"""
    
    def __init__(self):
        self.solved_challenges = []
        self.methods_tried = []
    
    def analyze_content(self, content):
        """Analizar contenido para determinar tipo de desafío"""
        content_lower = content.lower()
        
        analysis = {
            'type': 'UNKNOWN',
            'confidence': 0.0,
            'indicators': [],
            'extracted_data': {}
        }
        
        # Detectar RSA
        if re.search(r'n\s*=\s*\d+', content) and re.search(r'e\s*=\s*\d+', content):
            analysis['type'] = 'RSA'
            analysis['confidence'] = 0.95
            analysis['indicators'].append('RSA parameters found')
            
            # Extraer parámetros
            n_match = re.search(r'n\s*=\s*(\d+)', content)
            e_match = re.search(r'e\s*=\s*(\d+)', content)
            c_match = re.search(r'c\s*=\s*(\d+)', content)
            
            if n_match:
                analysis['extracted_data']['n'] = int(n_match.group(1))
            if e_match:
                analysis['extracted_data']['e'] = int(e_match.group(1))
            if c_match:
                analysis['extracted_data']['c'] = int(c_match.group(1))
        
        # Detectar XOR
        elif re.search(r'[0-9a-fA-F]{20,}', content) and 'xor' in content_lower:
            analysis['type'] = 'XOR'
            analysis['confidence'] = 0.90
            analysis['indicators'].append('Hex data with XOR mention')
            
            hex_match = re.search(r'([0-9a-fA-F]{20,})', content)
            if hex_match:
                analysis['extracted_data']['hex'] = hex_match.group(1)
        
        # Detectar Vigenère
        elif 'vigenere' in content_lower or 'vigenère' in content_lower:
            analysis['type'] = 'VIGENERE'
            analysis['confidence'] = 0.85
            analysis['indicators'].append('Vigenère cipher mentioned')
            
            # Buscar ciphertext
            cipher_match = re.search(r'ciphertext:\s*([A-Z]+)', content, re.IGNORECASE)
            if cipher_match:
                analysis['extracted_data']['ciphertext'] = cipher_match.group(1).upper()
        
        # Detectar Caesar
        elif re.search(r'[A-Z\s]{10,}', content) and ('caesar' in content_lower or 'shift' in content_lower):
            analysis['type'] = 'CAESAR'
            analysis['confidence'] = 0.80
            analysis['indicators'].append('Caesar cipher pattern')
            
            # Extraer texto cifrado
            cipher_match = re.search(r'([A-Z\s]{10,})', content)
            if cipher_match:
                analysis['extracted_data']['ciphertext'] = cipher_match.group(1).strip()
        
        # Detectar Base64
        elif re.search(r'[A-Za-z0-9+/]{20,}={0,2}', content):
            analysis['type'] = 'BASE64'
            analysis['confidence'] = 0.75
            analysis['indicators'].append('Base64 pattern detected')
            
            b64_match = re.search(r'([A-Za-z0-9+/]{20,}={0,2})', content)
            if b64_match:
                analysis['extracted_data']['base64'] = b64_match.group(1)
        
        return analysis
    
    def solve_rsa(self, n, e, c):
        """Resolver desafío RSA"""
        print(f"🔢 RESOLVIENDO RSA")
        print(f"   n = {n}")
        print(f"   e = {e}")
        print(f"   c = {c}")
        
        # Método 1: Factorización directa (para n pequeños)
        if n < 10000:
            print("🔧 Intentando factorización directa...")
            factors = RSAMath.factorize(n)
            
            if len(factors) >= 2:
                p, q = factors[0], factors[1]
                print(f"✅ Factores encontrados: p = {p}, q = {q}")
                
                # Calcular phi(n)
                phi_n = (p - 1) * (q - 1)
                
                # Calcular d
                d = RSAMath.mod_inverse(e, phi_n)
                if d:
                    print(f"🔑 Clave privada: d = {d}")
                    
                    # Descifrar
                    m = RSAMath.pow_mod(c, d, n)
                    print(f"📝 Mensaje descifrado: {m}")
                    
                    # Intentar convertir a ASCII
                    try:
                        if 32 <= m <= 126:
                            char = chr(m)
                            print(f"🔤 Carácter ASCII: '{char}'")
                            return char
                        else:
                            return str(m)
                    except:
                        return str(m)
        
        # Método 2: Exponente pequeño
        if e <= 10:
            print("🔧 Intentando ataque de exponente pequeño...")
            # Si c < n, podría ser que m^e < n
            if c < n:
                m = RSAMath.nth_root(c, e)
                if m and pow(m, e) == c:
                    print(f"✅ Mensaje encontrado: {m}")
                    try:
                        if 32 <= m <= 126:
                            return chr(m)
                        else:
                            return str(m)
                    except:
                        return str(m)
        
        return None
    
    def solve_xor(self, hex_data, known_start="crypto{", known_end="}"):
        """Resolver desafío XOR"""
        print(f"⚡ RESOLVIENDO XOR")
        print(f"   Hex: {hex_data}")
        
        try:
            ciphertext = bytes.fromhex(hex_data.replace(' ', ''))
            print(f"   Longitud: {len(ciphertext)} bytes")
            
            # Método 1: Known plaintext attack
            if known_start:
                print(f"🔧 Usando known plaintext: '{known_start}'")
                
                for key_len in range(1, min(20, len(ciphertext))):
                    key = []
                    
                    # Extraer clave usando known start
                    for i in range(min(len(known_start), key_len)):
                        if i < len(ciphertext):
                            key.append(ciphertext[i] ^ ord(known_start[i]))
                    
                    # Completar clave
                    while len(key) < key_len:
                        key.append(key[0] if key else 0)
                    
                    # Descifrar
                    plaintext = ""
                    for i in range(len(ciphertext)):
                        plaintext += chr(ciphertext[i] ^ key[i % key_len])
                    
                    # Verificar
                    if known_start in plaintext and (not known_end or known_end in plaintext):
                        print(f"✅ Resuelto con clave de longitud {key_len}")
                        print(f"🔑 Clave: {bytes(key)}")
                        return plaintext
            
            # Método 2: Single byte XOR
            print(f"🔧 Probando single byte XOR...")
            for key in range(256):
                try:
                    plaintext = ''.join(chr(b ^ key) for b in ciphertext)
                    if plaintext.isprintable() and len(plaintext) > 5:
                        if known_start in plaintext or 'flag' in plaintext.lower():
                            print(f"✅ Single byte XOR con clave {key}")
                            return plaintext
                except:
                    continue
                    
        except Exception as e:
            print(f"❌ Error en XOR: {e}")
        
        return None
    
    def solve_vigenere(self, ciphertext, key_hint=None):
        """Resolver cifrado Vigenère"""
        print(f"🔤 RESOLVIENDO VIGENÈRE")
        print(f"   Ciphertext: {ciphertext}")
        
        # Método 1: Usar pista de clave
        if key_hint and "3-letter" in key_hint and "crypto" in key_hint.lower():
            # Probar claves relacionadas con CRYPTO
            possible_keys = ["KEY", "CTF", "RSA", "XOR", "AES", "DES", "MD5", "SHA"]
            
            for key in possible_keys:
                print(f"🔧 Probando clave: {key}")
                plaintext = self.vigenere_decrypt(ciphertext, key)
                
                # Verificar si es inglés válido
                if self.is_english_text(plaintext):
                    print(f"✅ Texto válido encontrado con clave '{key}'")
                    return plaintext
        
        # Método 2: Análisis de frecuencia para longitud de clave
        print(f"🔧 Analizando longitud de clave...")
        for key_len in range(1, min(10, len(ciphertext))):
            # Análisis de coincidencias
            coincidences = 0
            for i in range(len(ciphertext) - key_len):
                if ciphertext[i] == ciphertext[i + key_len]:
                    coincidences += 1
            
            if coincidences > len(ciphertext) * 0.1:  # Umbral arbitrario
                print(f"   Posible longitud de clave: {key_len}")
                
                # Intentar descifrar con esta longitud
                result = self.crack_vigenere_length(ciphertext, key_len)
                if result:
                    return result
        
        return None
    
    def vigenere_decrypt(self, ciphertext, key):
        """Descifrar Vigenère con clave conocida"""
        plaintext = ""
        key = key.upper()
        
        for i, char in enumerate(ciphertext):
            if char.isalpha():
                key_char = key[i % len(key)]
                shift = ord(key_char) - ord('A')
                
                if char.isupper():
                    plaintext += chr((ord(char) - ord('A') - shift) % 26 + ord('A'))
                else:
                    plaintext += chr((ord(char) - ord('a') - shift) % 26 + ord('a'))
            else:
                plaintext += char
        
        return plaintext
    
    def crack_vigenere_length(self, ciphertext, key_len):
        """Intentar crackear Vigenère con longitud conocida"""
        # Análisis de frecuencia por posición
        key = ""
        
        for pos in range(key_len):
            # Extraer caracteres en esta posición
            chars = []
            for i in range(pos, len(ciphertext), key_len):
                if ciphertext[i].isalpha():
                    chars.append(ciphertext[i])
            
            if not chars:
                continue
            
            # Probar cada posible carácter de clave
            best_score = -1
            best_char = 'A'
            
            for test_key_char in string.ascii_uppercase:
                # Descifrar estos caracteres
                decrypted = []
                for char in chars:
                    shift = ord(test_key_char) - ord('A')
                    if char.isupper():
                        decrypted.append(chr((ord(char) - ord('A') - shift) % 26 + ord('A')))
                    else:
                        decrypted.append(chr((ord(char) - ord('a') - shift) % 26 + ord('a')))
                
                # Calcular score basado en frecuencia de letras en inglés
                score = self.english_frequency_score(''.join(decrypted))
                
                if score > best_score:
                    best_score = score
                    best_char = test_key_char
            
            key += best_char
        
        if key:
            plaintext = self.vigenere_decrypt(ciphertext, key)
            if self.is_english_text(plaintext):
                print(f"✅ Clave encontrada: {key}")
                return plaintext
        
        return None
    
    def solve_caesar(self, ciphertext):
        """Resolver cifrado César"""
        print(f"🔤 RESOLVIENDO CAESAR")
        print(f"   Ciphertext: {ciphertext}")
        
        for shift in range(1, 26):
            plaintext = ""
            for char in ciphertext:
                if char.isalpha():
                    if char.isupper():
                        plaintext += chr((ord(char) - ord('A') - shift) % 26 + ord('A'))
                    else:
                        plaintext += chr((ord(char) - ord('a') - shift) % 26 + ord('a'))
                else:
                    plaintext += char
            
            # Verificar si es texto válido
            if self.is_english_text(plaintext):
                print(f"✅ Shift {shift}: {plaintext}")
                return plaintext
        
        return None
    
    def solve_base64(self, b64_data):
        """Resolver Base64"""
        print(f"📦 RESOLVIENDO BASE64")
        print(f"   Data: {b64_data}")
        
        try:
            decoded = base64.b64decode(b64_data).decode('utf-8')
            print(f"✅ Decodificado: {decoded}")
            return decoded
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def is_english_text(self, text):
        """Verificar si el texto parece inglés"""
        if not text:
            return False
        
        # Verificar caracteres imprimibles
        if not all(c.isprintable() for c in text):
            return False
        
        # Verificar palabras comunes
        common_words = ['THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'BY', 'WORD', 'FLAG', 'CRYPTO']
        text_upper = text.upper()
        
        word_count = sum(1 for word in common_words if word in text_upper)
        return word_count > 0
    
    def english_frequency_score(self, text):
        """Calcular score basado en frecuencia de letras en inglés"""
        if not text:
            return 0
        
        # Frecuencias esperadas en inglés
        english_freq = {
            'E': 12.7, 'T': 9.1, 'A': 8.2, 'O': 7.5, 'I': 7.0, 'N': 6.7,
            'S': 6.3, 'H': 6.1, 'R': 6.0, 'D': 4.3, 'L': 4.0, 'C': 2.8,
            'U': 2.8, 'M': 2.4, 'W': 2.4, 'F': 2.2, 'G': 2.0, 'Y': 2.0,
            'P': 1.9, 'B': 1.3, 'V': 1.0, 'K': 0.8, 'J': 0.15, 'X': 0.15,
            'Q': 0.10, 'Z': 0.07
        }
        
        # Contar frecuencias en el texto
        text_freq = {}
        total_letters = 0
        
        for char in text.upper():
            if char.isalpha():
                text_freq[char] = text_freq.get(char, 0) + 1
                total_letters += 1
        
        if total_letters == 0:
            return 0
        
        # Calcular score
        score = 0
        for char, expected_freq in english_freq.items():
            actual_freq = (text_freq.get(char, 0) / total_letters) * 100
            score -= abs(actual_freq - expected_freq)
        
        return score
    
    def solve_challenge(self, content):
        """Resolver desafío basado en análisis"""
        print(f"🎮 ANALIZANDO DESAFÍO")
        print("="*50)
        
        analysis = self.analyze_content(content)
        
        print(f"📊 Tipo detectado: {analysis['type']}")
        print(f"📊 Confianza: {analysis['confidence']:.2f}")
        print(f"📊 Indicadores: {', '.join(analysis['indicators'])}")
        
        result = None
        
        if analysis['type'] == 'RSA' and 'n' in analysis['extracted_data']:
            result = self.solve_rsa(
                analysis['extracted_data']['n'],
                analysis['extracted_data']['e'],
                analysis['extracted_data']['c']
            )
        
        elif analysis['type'] == 'XOR' and 'hex' in analysis['extracted_data']:
            result = self.solve_xor(analysis['extracted_data']['hex'])
        
        elif analysis['type'] == 'VIGENERE' and 'ciphertext' in analysis['extracted_data']:
            result = self.solve_vigenere(analysis['extracted_data']['ciphertext'], content)
        
        elif analysis['type'] == 'CAESAR' and 'ciphertext' in analysis['extracted_data']:
            result = self.solve_caesar(analysis['extracted_data']['ciphertext'])
        
        elif analysis['type'] == 'BASE64' and 'base64' in analysis['extracted_data']:
            result = self.solve_base64(analysis['extracted_data']['base64'])
        
        if result:
            print(f"\n✅ ¡DESAFÍO RESUELTO!")
            print(f"🏁 Resultado: {result}")
            self.solved_challenges.append({
                'type': analysis['type'],
                'result': result,
                'confidence': analysis['confidence']
            })
            return result
        else:
            print(f"\n❌ No se pudo resolver automáticamente")
            return None

def solve_all_challenges():
    """Resolver todos los desafíos en la carpeta"""
    print("🎮 UNIVERSAL CRYPTO SOLVER")
    print("="*80)
    
    solver = UniversalCryptoSolver()
    challenges_dir = Path("challenges/uploaded")
    
    if not challenges_dir.exists():
        print("❌ Directorio de desafíos no encontrado")
        return
    
    # Buscar archivos de desafío
    challenge_files = list(challenges_dir.glob("*.txt"))
    
    print(f"📁 Encontrados {len(challenge_files)} archivos de desafío")
    
    for i, challenge_file in enumerate(challenge_files, 1):
        print(f"\n{'='*80}")
        print(f"📋 DESAFÍO {i}/{len(challenge_files)}: {challenge_file.name}")
        print(f"{'='*80}")
        
        try:
            with open(challenge_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"📄 Contenido:")
            print(content[:200] + "..." if len(content) > 200 else content)
            print()
            
            # Resolver desafío
            result = solver.solve_challenge(content)
            
            if result:
                print(f"🎉 ¡Resuelto!")
            else:
                print(f"⚠️ No resuelto")
                
        except Exception as e:
            print(f"❌ Error procesando {challenge_file.name}: {e}")
    
    # Resumen final
    print(f"\n{'='*80}")
    print(f"🎉 RESUMEN FINAL")
    print(f"{'='*80}")
    
    print(f"📊 Desafíos procesados: {len(challenge_files)}")
    print(f"📊 Desafíos resueltos: {len(solver.solved_challenges)}")
    print(f"📊 Tasa de éxito: {len(solver.solved_challenges)/len(challenge_files)*100:.1f}%")
    
    if solver.solved_challenges:
        print(f"\n🏆 DESAFÍOS RESUELTOS:")
        for i, challenge in enumerate(solver.solved_challenges, 1):
            print(f"   {i}. {challenge['type']}: {challenge['result']}")

def main():
    """Función principal"""
    solve_all_challenges()

if __name__ == "__main__":
    main()