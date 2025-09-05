#!/usr/bin/env python3
"""
Solucionador avanzado para cipher.txt - Desafío de múltiples capas
Incluye múltiples técnicas de decodificación y criptoanálisis
"""

import base64
import string
import binascii
from urllib.parse import unquote
from collections import Counter

def try_base64_decode(data):
    """Intenta decodificar base64"""
    try:
        # Agregar padding si es necesario
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)
        
        result = base64.b64decode(data).decode('utf-8', errors='ignore')
        if result != data and result.isprintable():
            print(f"  ✅ Base64 decode: {result[:50]}...")
            return result
    except:
        pass
    return None

def try_url_decode(data):
    """Intenta decodificar URL"""
    try:
        result = unquote(data)
        if result != data:  # Solo si hubo cambios
            print(f"  ✅ URL decode: {result[:50]}...")
            return result
    except:
        pass
    return None

def try_hex_decode(data):
    """Intenta decodificar hexadecimal"""
    try:
        # Verificar si parece hex
        if all(c in '0123456789abcdefABCDEF' for c in data.replace(' ', '')):
            hex_data = data.replace(' ', '')
            if len(hex_data) % 2 == 0:
                result = bytes.fromhex(hex_data).decode('utf-8', errors='ignore')
                if result.isprintable():
                    print(f"  ✅ Hex decode: {result[:50]}...")
                    return result
    except:
        pass
    return None

def try_rot13(data):
    """Intenta ROT13"""
    import codecs
    try:
        result = codecs.decode(data, 'rot13')
        if result != data:
            print(f"  ✅ ROT13: {result[:50]}...")
            return result
    except:
        pass
    return None

def try_caesar_cipher(text, shift):
    """Intenta descifrar César con un desplazamiento específico"""
    result = ""
    for char in text:
        if char.isalpha():
            ascii_offset = 65 if char.isupper() else 97
            result += chr((ord(char) - ascii_offset - shift) % 26 + ascii_offset)
        else:
            result += char
    return result

def try_all_caesar(data):
    """Prueba todos los desplazamientos César posibles"""
    best_results = []
    
    for shift in range(1, 26):
        result = try_caesar_cipher(data, shift)
        
        # Buscar patrones que sugieran texto válido o flags
        if 'crypto{' in result.lower() or 'flag{' in result.lower() or 'ctf{' in result.lower():
            print(f"  ✅ Caesar cipher (shift {shift}): {result}")
            return result
        elif any(word in result.lower() for word in ['the', 'and', 'flag', 'crypto', 'challenge']):
            best_results.append((shift, result))
    
    # Si no encontramos flags, mostrar el mejor resultado
    if best_results:
        shift, result = best_results[0]
        print(f"  🔍 Caesar cipher (shift {shift}): {result[:50]}...")
        return result
        
    return None

def try_single_byte_xor(data):
    """Prueba XOR con un solo byte"""
    if isinstance(data, str):
        data = data.encode('latin-1', errors='ignore')
    
    best_results = []
    
    for key in range(256):
        try:
            result = bytes(b ^ key for b in data).decode('utf-8', errors='ignore')
            if 'crypto{' in result.lower() or 'flag{' in result.lower():
                print(f"  ✅ Single XOR (key {key}): {result}")
                return result
            elif len(result) > 10 and result.isprintable():
                # Verificar si parece texto válido
                score = sum(1 for word in ['the', 'and', 'flag', 'crypto', 'of', 'to', 'is'] 
                          if word in result.lower())
                if score > 0:
                    best_results.append((score, key, result))
        except:
            continue
    
    # Devolver el mejor resultado
    if best_results:
        best_results.sort(reverse=True)
        score, key, result = best_results[0]
        print(f"  🔍 Single XOR (key {key}): {result[:50]}...")
        return result
        
    return None

def try_ascii_shift(data):
    """Prueba diferentes desplazamientos ASCII"""
    for shift in range(1, 95):  # Caracteres ASCII imprimibles
        try:
            # Shift positivo
            result = ''.join(chr(((ord(c) - 32 + shift) % 95) + 32) for c in data if 32 <= ord(c) <= 126)
            if 'crypto{' in result.lower() or 'flag{' in result.lower():
                print(f"  ✅ ASCII shift (+{shift}): {result}")
                return result
            
            # Shift negativo
            result = ''.join(chr(((ord(c) - 32 - shift) % 95) + 32) for c in data if 32 <= ord(c) <= 126)
            if 'crypto{' in result.lower() or 'flag{' in result.lower():
                print(f"  ✅ ASCII shift (-{shift}): {result}")
                return result
        except:
            continue
    return None

def try_reverse(data):
    """Intenta reversar el texto"""
    result = data[::-1]
    if 'crypto{' in result.lower() or 'flag{' in result.lower():
        print(f"  ✅ Reverse: {result}")
        return result
    return None

def try_atbash_cipher(data):
    """Intenta cifrado Atbash (A=Z, B=Y, etc.)"""
    result = ""
    for char in data:
        if char.isalpha():
            if char.isupper():
                result += chr(ord('Z') - (ord(char) - ord('A')))
            else:
                result += chr(ord('z') - (ord(char) - ord('a')))
        else:
            result += char
    
    if 'crypto{' in result.lower() or 'flag{' in result.lower():
        print(f"  ✅ Atbash: {result}")
        return result
    return None

def analyze_character_frequency(data):
    """Analiza frecuencia de caracteres para pistas"""
    freq = Counter(data)
    print(f"  📊 Caracteres más frecuentes: {freq.most_common(5)}")
    print(f"  📊 Longitud total: {len(data)}")
    print(f"  📊 Caracteres únicos: {len(set(data))}")
    
    # Verificar si podría ser una codificación específica
    if all(c in string.printable for c in data):
        print(f"  ℹ️ Todos los caracteres son imprimibles")
    
    # Verificar patrones
    if data.count('{') > 0 and data.count('}') > 0:
        print(f"  ℹ️ Contiene llaves {{ }} - posible flag")

def try_keyboard_shift(data):
    """Prueba desplazamientos de teclado QWERTY"""
    qwerty = "qwertyuiopasdfghjklzxcvbnm"
    qwerty_upper = qwerty.upper()
    
    for shift in range(1, len(qwerty)):
        result = ""
        for char in data:
            if char.lower() in qwerty:
                idx = qwerty.index(char.lower())
                new_idx = (idx + shift) % len(qwerty)
                if char.isupper():
                    result += qwerty_upper[new_idx]
                else:
                    result += qwerty[new_idx]
            else:
                result += char
        
        if 'crypto{' in result.lower() or 'flag{' in result.lower():
            print(f"  ✅ Keyboard shift (+{shift}): {result}")
            return result
    
    return None

def try_custom_substitution(data):
    """Prueba sustituciones personalizadas comunes en CTF"""
    # Común en CTFs: números como letras
    leet_map = {
        '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', 
        '7': 't', '8': 'b', '9': 'g'
    }
    
    result = data
    for num, letter in leet_map.items():
        result = result.replace(num, letter)
    
    if result != data and ('crypto{' in result.lower() or 'flag{' in result.lower()):
        print(f"  ✅ Leet substitution: {result}")
        return result
    
    return None

def solve_multilayer_cipher(cipher_text):
    """Resuelve cifrado de múltiples capas"""
    print("🔍 Resolviendo cifrado de múltiples capas...")
    print(f"📝 Texto original: {cipher_text}")
    
    current = cipher_text.strip()
    layer = 1
    
    # Primero analizar el texto
    print(f"\n📊 ANÁLISIS INICIAL:")
    analyze_character_frequency(current)
    
    while layer <= 15:  # Máximo 15 capas
        print(f"\n🔄 Capa {layer}:")
        print(f"   Datos actuales: {current[:50]}...")
        
        original = current
        
        # Intentar diferentes decodificaciones en orden de probabilidad
        
        # 1. Base64
        decoded = try_base64_decode(current)
        if decoded and decoded != current:
            current = decoded
            layer += 1
            continue
            
        # 2. URL decode
        decoded = try_url_decode(current)
        if decoded and decoded != current:
            current = decoded
            layer += 1
            continue
            
        # 3. Hex decode
        decoded = try_hex_decode(current)
        if decoded and decoded != current:
            current = decoded
            layer += 1
            continue
            
        # 4. ROT13
        decoded = try_rot13(current)
        if decoded and decoded != current:
            current = decoded
            layer += 1
            continue
            
        # 5. Caesar cipher (todos los shifts)
        decoded = try_all_caesar(current)
        if decoded and decoded != current:
            current = decoded
            layer += 1
            continue
            
        # 6. Single byte XOR
        decoded = try_single_byte_xor(current)
        if decoded and decoded != current:
            current = decoded
            layer += 1
            continue
            
        # 7. ASCII shift
        decoded = try_ascii_shift(current)
        if decoded and decoded != current:
            current = decoded
            layer += 1
            continue
            
        # 8. Keyboard shift
        decoded = try_keyboard_shift(current)
        if decoded and decoded != current:
            current = decoded
            layer += 1
            continue
            
        # 9. Atbash cipher
        decoded = try_atbash_cipher(current)
        if decoded and decoded != current:
            current = decoded
            layer += 1
            continue
            
        # 10. Reverse
        decoded = try_reverse(current)
        if decoded and decoded != current:
            current = decoded
            layer += 1
            continue
            
        # 11. Custom substitutions
        decoded = try_custom_substitution(current)
        if decoded and decoded != current:
            current = decoded
            layer += 1
            continue
        
        # Si no hubo cambios, intentar técnicas más avanzadas
        if current == original:
            print("  ❌ No se detectaron más capas con técnicas estándar")
            
            # Intentar interpretaciones alternativas
            print("  🔎 Probando interpretaciones alternativas...")
            
            # Probar como si fuera un array de bytes
            if ',' in current:
                try:
                    numbers = [int(x.strip()) for x in current.split(',') if x.strip().isdigit()]
                    if numbers:
                        byte_result = ''.join(chr(n) for n in numbers if 0 <= n <= 255)
                        print(f"  🔢 Interpretación como bytes: {byte_result[:50]}...")
                        if 'crypto{' in byte_result.lower():
                            current = byte_result
                            layer += 1
                            continue
                except:
                    pass
            
            # Último intento: mostrar resultado parcial
            break
    
    print(f"\n🎉 Resultado final (capa {layer-1}): {current}")
    
    # Buscar flags en el resultado final
    flag_patterns = ['crypto{', 'flag{', 'ctf{', 'htb{']
    for pattern in flag_patterns:
        if pattern in current.lower():
            flag_start = current.lower().find(pattern)
            flag_end = current.find('}', flag_start) + 1
            if flag_end > flag_start:
                flag = current[flag_start:flag_end]
                print(f"🏁 FLAG ENCONTRADA: {flag}")
                return flag
    
    # Si no se encontró flag, buscar patrones similares
    if '{' in current and '}' in current:
        start = current.find('{')
        end = current.find('}', start) + 1
        if end > start:
            possible_flag = current[start-10:end+10]  # Contexto ampliado
            print(f"🔍 Posible flag detectada: {possible_flag}")
    
    return current

def main():
    # Leer el desafío
    try:
        with open('challenges/uploaded/ctf/cipher.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraer el texto cifrado (primera línea)
        lines = content.strip().split('\n')
        cipher_text = lines[0]
        
        print("🎯 SOLUCIONADOR AVANZADO DE DESAFÍO MULTICAPA")
        print("=" * 55)
        print(f"📄 Archivo: challenges/uploaded/ctf/cipher.txt")
        print(f"📝 Descripción: {' '.join(lines[2:])}")
        
        # Resolver
        result = solve_multilayer_cipher(cipher_text)
        
        flag_found = False
        for pattern in ['crypto{', 'flag{', 'ctf{']:
            if pattern in result.lower():
                flag_found = True
                break
        
        if flag_found:
            print(f"\n✅ ¡DESAFÍO RESUELTO!")
            print(f"🏆 FLAG: {result}")
        else:
            print(f"\n⚠️ Resultado obtenido pero no se detectó flag clara:")
            print(f"📝 {result}")
            print(f"\n🔍 Intentando búsqueda manual de patrones...")
            
            # Búsqueda más exhaustiva
            if len(result) > 10:
                # Buscar cualquier cosa entre llaves
                import re
                matches = re.findall(r'\{[^}]+\}', result)
                if matches:
                    print(f"🔍 Patrones encontrados: {matches}")
            
    except FileNotFoundError:
        print("❌ Archivo cipher.txt no encontrado")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()