#!/usr/bin/env python3
"""
Solucionador Avanzado para Desafíos Multicapa
Diseñado específicamente para cipher.txt - múltiples capas de codificación
"""

import base64
import urllib.parse
import codecs
import string
import re
from collections import Counter

class MultilayerCipherSolver:
    def __init__(self):
        self.iterations_log = []
        self.current_data = ""
        
    def log_iteration(self, method, input_data, output_data, success=True):
        """Registra cada iteración de decodificación"""
        self.iterations_log.append({
            'method': method,
            'input': input_data[:50] + "..." if len(input_data) > 50 else input_data,
            'output': output_data[:50] + "..." if len(output_data) > 50 else output_data,
            'success': success,
            'input_length': len(input_data),
            'output_length': len(output_data)
        })
        
    def is_likely_flag(self, text):
        """Detecta si el texto parece una flag"""
        flag_patterns = [
            r'flag\{[^}]+\}',
            r'ctf\{[^}]+\}', 
            r'crypto\{[^}]+\}',
            r'[a-zA-Z]+\{[^}]+\}',
            r'\{[^}]{10,}\}'
        ]
        
        for pattern in flag_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def is_printable_ascii(self, text):
        """Verifica si el texto es ASCII imprimible"""
        try:
            return all(ord(c) >= 32 and ord(c) <= 126 for c in text)
        except:
            return False
    
    def try_base64_decode(self, data):
        """Intenta decodificar Base64"""
        try:
            # Agregar padding si es necesario
            missing_padding = len(data) % 4
            if missing_padding:
                data += '=' * (4 - missing_padding)
            
            decoded = base64.b64decode(data).decode('utf-8', errors='ignore')
            if self.is_printable_ascii(decoded) and len(decoded) > 0:
                return decoded
        except:
            pass
        return None
    
    def try_url_decode(self, data):
        """Intenta decodificar URL encoding"""
        try:
            decoded = urllib.parse.unquote(data)
            if decoded != data and self.is_printable_ascii(decoded):
                return decoded
        except:
            pass
        return None
    
    def try_hex_decode(self, data):
        """Intenta decodificar hexadecimal"""
        try:
            # Remover espacios y caracteres no hex
            cleaned = re.sub(r'[^0-9a-fA-F]', '', data)
            if len(cleaned) % 2 == 0 and len(cleaned) > 0:
                decoded = bytes.fromhex(cleaned).decode('utf-8', errors='ignore')
                if self.is_printable_ascii(decoded):
                    return decoded
        except:
            pass
        return None
    
    def try_rot_decode(self, data, rotation=13):
        """Intenta decodificar ROT (default ROT13)"""
        try:
            if rotation == 13:
                decoded = codecs.decode(data, 'rot13')
            else:
                decoded = ""
                for char in data:
                    if char.isalpha():
                        base = ord('A') if char.isupper() else ord('a')
                        decoded += chr((ord(char) - base - rotation) % 26 + base)
                    else:
                        decoded += char
            
            if self.is_printable_ascii(decoded):
                return decoded
        except:
            pass
        return None
    
    def try_caesar_decode(self, data):
        """Intenta todas las posibles rotaciones Caesar"""
        best_result = None
        best_score = 0
        
        for shift in range(1, 26):
            try:
                decoded = ""
                for char in data:
                    if char.isalpha():
                        base = ord('A') if char.isupper() else ord('a')
                        decoded += chr((ord(char) - base - shift) % 26 + base)
                    else:
                        decoded += char
                
                # Calcular score basado en frecuencia de letras comunes
                score = self.calculate_english_score(decoded)
                if score > best_score:
                    best_score = score
                    best_result = (decoded, shift)
            except:
                continue
        
        return best_result[0] if best_result and best_score > 0.3 else None
    
    def calculate_english_score(self, text):
        """Calcula score basado en frecuencia de letras en inglés"""
        common_letters = 'etaoinshrdlcumwfgypbvkjxqz'
        text_lower = text.lower()
        letter_count = Counter(c for c in text_lower if c.isalpha())
        
        if not letter_count:
            return 0
        
        total_letters = sum(letter_count.values())
        score = 0
        
        for i, letter in enumerate(common_letters):
            frequency = letter_count.get(letter, 0) / total_letters
            # Las letras más comunes tienen mayor peso
            weight = (len(common_letters) - i) / len(common_letters)
            score += frequency * weight
        
        return score
    
    def try_xor_decode(self, data):
        """Intenta decodificar XOR con claves comunes"""
        common_keys = [
            b'key', b'password', b'secret', b'ctf', b'flag'
        ]
        # Agregar single byte XOR keys
        common_keys.extend([bytes([i]) for i in range(1, 256)])
        
        try:
            data_bytes = data.encode('utf-8')
        except:
            return None
        
        for key in common_keys:
            try:
                decoded_bytes = bytes(a ^ key[i % len(key)] for i, a in enumerate(data_bytes))
                decoded = decoded_bytes.decode('utf-8', errors='ignore')
                
                if self.is_printable_ascii(decoded) and len(decoded) > 5:
                    return decoded
            except:
                continue
        
        return None
    
    def try_atbash_decode(self, data):
        """Intenta decodificar Atbash cipher"""
        try:
            decoded = ""
            for char in data:
                if char.isalpha():
                    if char.isupper():
                        decoded += chr(ord('Z') - (ord(char) - ord('A')))
                    else:
                        decoded += chr(ord('z') - (ord(char) - ord('a')))
                else:
                    decoded += char
            
            if self.is_printable_ascii(decoded):
                return decoded
        except:
            pass
        return None
    
    def try_keyboard_shift_decode(self, data):
        """Intenta decodificar keyboard shift"""
        keyboard_map = {
            '1': '`', '2': '1', '3': '2', '4': '3', '5': '4', '6': '5', '7': '6', '8': '7', '9': '8', '0': '9', '-': '0', '=': '-',
            'q': 'q', 'w': 'q', 'e': 'w', 'r': 'e', 't': 'r', 'y': 't', 'u': 'y', 'i': 'u', 'o': 'i', 'p': 'o', '[': 'p', ']': '[',
            'a': 'a', 's': 'a', 'd': 's', 'f': 'd', 'g': 'f', 'h': 'g', 'j': 'h', 'k': 'j', 'l': 'k', ';': 'l', "'": ';',
            'z': 'z', 'x': 'z', 'c': 'x', 'v': 'c', 'b': 'v', 'n': 'b', 'm': 'n', ',': 'm', '.': ',', '/': '.'
        }
        
        try:
            decoded = ""
            for char in data.lower():
                decoded += keyboard_map.get(char, char)
            
            if self.is_printable_ascii(decoded):
                return decoded
        except:
            pass
        return None
    
    def try_ascii_shift_decode(self, data):
        """Intenta decodificar ASCII shift"""
        for shift in range(1, 95):  # Printable ASCII range
            try:
                decoded = ""
                for char in data:
                    if 32 <= ord(char) <= 126:  # Printable ASCII
                        new_char = chr(((ord(char) - 32 - shift) % 95) + 32)
                        decoded += new_char
                    else:
                        decoded += char
                
                if self.is_likely_flag(decoded) or (self.is_printable_ascii(decoded) and 'flag' in decoded.lower()):
                    return decoded
            except:
                continue
        
        return None
    
    def decode_single_layer(self, data):
        """Intenta decodificar una sola capa usando múltiples métodos"""
        methods = [
            ('Base64', self.try_base64_decode),
            ('URL Decode', self.try_url_decode),
            ('Hex Decode', self.try_hex_decode),
            ('ROT13', lambda x: self.try_rot_decode(x, 13)),
            ('Caesar Cipher', self.try_caesar_decode),
            ('XOR', self.try_xor_decode),
            ('ASCII Shift', self.try_ascii_shift_decode),
            ('Atbash', self.try_atbash_decode),
            ('Keyboard Shift', self.try_keyboard_shift_decode)
        ]
        
        for method_name, method_func in methods:
            try:
                result = method_func(data)
                if result and result != data:
                    self.log_iteration(method_name, data, result, True)
                    return result
                else:
                    self.log_iteration(method_name, data, "No result", False)
            except Exception as e:
                self.log_iteration(method_name, data, f"Error: {e}", False)
        
        return None
    
    def solve_multilayer(self, initial_data, max_iterations=20):
        """Resuelve desafío multicapa iterativamente"""
        print(f"🔍 Iniciando análisis multicapa del texto cifrado...")
        print(f"📝 Texto inicial: {initial_data}")
        print("=" * 80)
        
        current = initial_data.strip()
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n🔄 Iteración {iteration}:")
            print(f"📥 Entrada: {current[:60]}{'...' if len(current) > 60 else ''}")
            
            # Verificar si ya tenemos una flag
            if self.is_likely_flag(current):
                print(f"🎉 ¡FLAG ENCONTRADA EN ITERACIÓN {iteration}!")
                print(f"🏆 FLAG: {current}")
                return current
            
            # Intentar decodificar
            decoded = self.decode_single_layer(current)
            
            if decoded and decoded != current:
                print(f"✅ Decodificado: {decoded[:60]}{'...' if len(decoded) > 60 else ''}")
                current = decoded
                
                # Verificar inmediatamente si es una flag
                if self.is_likely_flag(current):
                    print(f"🎉 ¡FLAG ENCONTRADA!")
                    print(f"🏆 FLAG: {current}")
                    return current
            else:
                print(f"❌ No se pudo decodificar más en iteración {iteration}")
                break
        
        print(f"\n📊 Análisis completado después de {iteration} iteraciones")
        print(f"📤 Resultado final: {current}")
        
        # Mostrar resumen de iteraciones
        self.show_iterations_summary()
        
        return current
    
    def show_iterations_summary(self):
        """Muestra resumen de todas las iteraciones"""
        print("\n📋 RESUMEN DE ITERACIONES:")
        print("=" * 50)
        
        for i, log in enumerate(self.iterations_log, 1):
            status = "✅" if log['success'] else "❌"
            print(f"{status} {log['method']}: {log['input'][:30]}... → {log['output'][:30]}...")
        
        successful_methods = [log['method'] for log in self.iterations_log if log['success']]
        if successful_methods:
            print(f"\n🎯 Métodos exitosos: {', '.join(successful_methods)}")

def main():
    # Leer el desafío
    cipher_file = "challenges/uploaded/ctf/cipher.txt"
    
    try:
        with open(cipher_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Extraer el texto cifrado (primera línea no vacía que no sea descripción)
        cipher_text = None
        for line in lines:
            line = line.strip()
            if line and not line.startswith('description') and not line.startswith('This flag') and not line.startswith('Can you'):
                cipher_text = line
                break
        
        if not cipher_text:
            print("❌ No se pudo extraer el texto cifrado del archivo")
            return
        
        print("🎯 SOLUCIONADOR DE CIFRADO MULTICAPA")
        print("=" * 40)
        print(f"📁 Archivo: {cipher_file}")
        print(f"🔐 Texto cifrado detectado: {cipher_text}")
        print()
        
        # Resolver
        solver = MultilayerCipherSolver()
        result = solver.solve_multilayer(cipher_text)
        
        if solver.is_likely_flag(result):
            print(f"\n🎉 ¡ÉXITO! Flag encontrada: {result}")
            
            # Guardar resultado
            solved_file = "challenges/solved/cipher_solution.txt"
            with open(solved_file, 'w', encoding='utf-8') as f:
                f.write(f"Original: {cipher_text}\n")
                f.write(f"Flag: {result}\n")
                f.write(f"Métodos usados: {', '.join([log['method'] for log in solver.iterations_log if log['success']])}\n")
            
            print(f"💾 Solución guardada en: {solved_file}")
        else:
            print(f"\n⚠️  No se encontró flag definitiva. Resultado final: {result}")
            print("💡 El desafío podría requerir técnicas más avanzadas")
    
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {cipher_file}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()