#!/usr/bin/env python3
"""
Solucionador específico para cipher.txt - Desafío de múltiples capas
"""

import base64
import string
import binascii
from urllib.parse import unquote

def try_base64_decode(data):
    """Intenta decodificar base64"""
    try:
        # Agregar padding si es necesario
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)
        
        result = base64.b64decode(data).decode('utf-8', errors='ignore')
        print(f"  ✅ Base64 decode: {result[:50]}...")
        return result
    except:
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
        if all(c in '0123456789abcdefABCDEF' for c in data):
            result = bytes.fromhex(data).decode('utf-8', errors='ignore')
            print(f"  ✅ Hex decode: {result[:50]}...")
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
    for shift in range(1, 26):
        result = try_caesar_cipher(data, shift)
        # Buscar patrones que sugieran texto válido o flags
        if 'crypto{' in result.lower() or 'flag{' in result.lower() or 'ctf{' in result.lower():
            print(f"  ✅ Caesar cipher (shift {shift}): {result}")
            return result
        elif any(word in result.lower() for word in ['the', 'and', 'flag', 'crypto', 'challenge']):
            print(f"  🔍 Caesar cipher (shift {shift}): {result[:50]}...")
            return result
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

def try_ascii_shift(data):
    """Prueba diferentes desplazamientos ASCII"""
    for shift in range(1, 128):
        try:
            result = ''.join(chr((ord(c) + shift) % 128) for c in data if ord(c) < 128)
            if 'crypto{' in result.lower() or 'flag{' in result.lower():
                print(f"  ✅ ASCII shift (+{shift}): {result}")
                return result
            
            # También probar shift negativo
            result = ''.join(chr((ord(c) - shift) % 128) for c in data if ord(c) < 128)
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
    from collections import Counter
    freq = Counter(data)
    print(f"  📈 Caracteres más frecuentes: {freq.most_common(5)}")
    print(f"  📈 Longitud total: {len(data)}")
    print(f"  📈 Caracteres únicos: {len(set(data))}")
    
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
            
        # También probar shift negativo
        result = ""
        for char in data:
            if char.lower() in qwerty:
                idx = qwerty.index(char.lower())
                new_idx = (idx - shift) % len(qwerty)
                if char.isupper():
                    result += qwerty_upper[new_idx]
                else:
                    result += qwerty[new_idx]
            else:
                result += char
        
        if 'crypto{' in result.lower() or 'flag{' in result.lower():
            print(f"  ✅ Keyboard shift (-{shift}): {result}")
            return result
    
    return None
    """Prueba XOR con un solo byte"""
    if isinstance(data, str):
        data = data.encode()
    
    for key in range(256):
        try:
            result = bytes(b ^ key for b in data).decode('utf-8', errors='ignore')
            if 'crypto{' in result.lower() or 'flag{' in result.lower():
                print(f"  ✅ Single XOR (key {key}): {result}")
                return result
            elif len(result) > 10 and result.isprintable():
                # Verificar si parece texto válido
                if any(word in result.lower() for word in ['the', 'and', 'flag', 'crypto']):
                    print(f"  🔍 Single XOR (key {key}): {result[:50]}...")
                    return result
        except:
            continue
    return None

def solve_multilayer_cipher(cipher_text):
    """Resuelve cifrado de múltiples capas"""
    print("🔍 Resolviendo cifrado de múltiples capas...")
    print(f"📝 Texto original: {cipher_text}")
    
    current = cipher_text.strip()
    layer = 1
    
    while layer <= 10:  # Máximo 10 capas para evitar bucles infinitos
        print(f"\n🔄 Capa {layer}:")
        print(f"   Datos actuales: {current[:50]}...")
        
        original = current
        
        # Intentar diferentes decodificaciones
        
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
            
        # 4. Single byte XOR
        decoded = try_single_byte_xor(current)
        if decoded and decoded != current:
            current = decoded
            layer += 1
            continue
            
        # 5. Caesar cipher
        decoded = try_all_caesar(current)
        if decoded and decoded != current:
            current = decoded
            layer += 1
            continue
        
        # Si no hubo cambios, intentar con interpretación diferente
        if current == original:
            print("  ❌ No se detectaron más capas")
            break
    
    print(f"\n🎉 Resultado final: {current}")
    
    # Buscar flags en el resultado final
    if 'crypto{' in current.lower():
        flag_start = current.lower().find('crypto{')
        flag_end = current.find('}', flag_start) + 1
        if flag_end > flag_start:
            flag = current[flag_start:flag_end]
            print(f"🏁 FLAG ENCONTRADA: {flag}")
            return flag
    
    return current

def main():
    # Leer el desafío
    try:
        with open('challenges/uploaded/ctf/cipher.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraer el texto cifrado (primera línea)
        lines = content.strip().split('\n')
        cipher_text = lines[0]
        
        print("🎯 SOLUCIONADOR DE DESAFÍO MULTICAPA")
        print("=" * 50)
        print(f"📄 Archivo: challenges/uploaded/ctf/cipher.txt")
        print(f"📝 Descripción: {' '.join(lines[2:])}")
        
        # Resolver
        result = solve_multilayer_cipher(cipher_text)
        
        if 'crypto{' in result.lower() or 'flag{' in result.lower():
            print(f"\n✅ ¡DESAFÍO RESUELTO!")
            print(f"🏆 FLAG: {result}")
        else:
            print(f"\n⚠️ Resultado obtenido pero no se detectó flag clara:")
            print(f"📝 {result}")
            
    except FileNotFoundError:
        print("❌ Archivo cipher.txt no encontrado")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()