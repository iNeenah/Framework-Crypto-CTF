#!/usr/bin/env python3
"""
Solucionador Especializado para Cipher.txt
Análisis exhaustivo con técnicas avanzadas
"""

import base64
import urllib.parse
import codecs
import string
import re
import binascii
from collections import Counter

def safe_decode(func, data):
    """Ejecuta función de decodificación de forma segura"""
    try:
        result = func(data)
        return result if result and result != data else None
    except:
        return None

def is_likely_flag(text):
    """Detecta si el texto parece una flag"""
    if not text:
        return False
    
    flag_patterns = [
        r'flag\{[^}]+\}',
        r'ctf\{[^}]+\}', 
        r'crypto\{[^}]+\}',
        r'[a-zA-Z]+\{[^}]{5,}\}',
        r'\{[a-fA-F0-9]{16,}\}',
        r'\{[a-zA-Z0-9_]{8,}\}'
    ]
    
    for pattern in flag_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def is_printable_text(text):
    """Verifica si el texto es completamente ASCII imprimible"""
    try:
        return all(32 <= ord(c) <= 126 for c in text) and len(text) > 5
    except:
        return False

def try_base64_variations(data):
    """Prueba múltiples variaciones de Base64"""
    variations = []
    
    # Base64 estándar
    for padding in ['', '=', '==', '===']:
        test_data = data + padding
        try:
            decoded = base64.b64decode(test_data).decode('utf-8', errors='ignore')
            if is_printable_text(decoded):
                variations.append(('base64_standard', decoded))
        except:
            pass
    
    # Base64 URL-safe
    try:
        decoded = base64.urlsafe_b64decode(data + '==').decode('utf-8', errors='ignore')
        if is_printable_text(decoded):
            variations.append(('base64_urlsafe', decoded))
    except:
        pass
    
    return variations

def try_hex_variations(data):
    """Prueba múltiples variaciones de hexadecimal"""
    variations = []
    
    # Hex directo
    cleaned = re.sub(r'[^0-9a-fA-F]', '', data)
    if len(cleaned) % 2 == 0 and len(cleaned) > 0:
        try:
            decoded = bytes.fromhex(cleaned).decode('utf-8', errors='ignore')
            if is_printable_text(decoded):
                variations.append(('hex_direct', decoded))
        except:
            pass
    
    # ASCII hex
    try:
        hex_string = ''.join(f'{ord(c):02x}' for c in data)
        decoded = bytes.fromhex(hex_string).decode('utf-8', errors='ignore')
        if is_printable_text(decoded):
            variations.append(('ascii_to_hex', decoded))
    except:
        pass
    
    return variations

def try_caesar_all_shifts(data):
    """Prueba todos los shifts de Caesar"""
    variations = []
    
    for shift in range(1, 26):
        try:
            decoded = ""
            for char in data:
                if char.isalpha():
                    base = ord('A') if char.isupper() else ord('a')
                    decoded += chr((ord(char) - base - shift) % 26 + base)
                else:
                    decoded += char
            
            if is_printable_text(decoded):
                variations.append((f'caesar_shift_{shift}', decoded))
        except:
            pass
    
    return variations

def try_ascii_shifts(data):
    """Prueba shifts en el rango ASCII completo"""
    variations = []
    
    for shift in range(1, 95):
        try:
            decoded = ""
            for char in data:
                if 32 <= ord(char) <= 126:
                    new_char = chr(((ord(char) - 32 - shift) % 95) + 32)
                    decoded += new_char
                else:
                    decoded += char
            
            if is_printable_text(decoded) or is_likely_flag(decoded):
                variations.append((f'ascii_shift_{shift}', decoded))
        except:
            pass
    
    return variations

def try_xor_single_byte(data):
    """Prueba XOR con single byte"""
    variations = []
    
    try:
        data_bytes = data.encode('utf-8')
    except:
        return variations
    
    for key in range(1, 256):
        try:
            decoded_bytes = bytes(b ^ key for b in data_bytes)
            decoded = decoded_bytes.decode('utf-8', errors='ignore')
            
            if is_printable_text(decoded) or is_likely_flag(decoded):
                variations.append((f'xor_key_{key}', decoded))
        except:
            pass
    
    return variations

def try_substitution_ciphers(data):
    """Prueba cifrados de sustitución especiales"""
    variations = []
    
    # Atbash
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
        
        if is_printable_text(decoded):
            variations.append(('atbash', decoded))
    except:
        pass
    
    # Reverse
    try:
        decoded = data[::-1]
        if is_printable_text(decoded):
            variations.append(('reverse', decoded))
    except:
        pass
    
    return variations

def analyze_cipher_exhaustive(cipher_text):
    """Análisis exhaustivo del texto cifrado"""
    print(f"🔍 ANÁLISIS EXHAUSTIVO")
    print(f"📝 Texto cifrado: {cipher_text}")
    print(f"📊 Longitud: {len(cipher_text)} caracteres")
    print("=" * 80)
    
    all_results = []
    
    # Análisis de caracteres
    char_analysis = Counter(cipher_text)
    print(f"🔤 Caracteres únicos: {len(char_analysis)}")
    print(f"🔢 Distribución de caracteres más comunes:")
    for char, count in char_analysis.most_common(10):
        print(f"   '{char}': {count} veces")
    
    print("\n🧪 PROBANDO TÉCNICAS DE DECODIFICACIÓN:")
    print("-" * 50)
    
    # 1. Base64 variations
    print("🟦 Base64 variations...")
    b64_results = try_base64_variations(cipher_text)
    all_results.extend(b64_results)
    for method, result in b64_results:
        print(f"   ✅ {method}: {result[:60]}...")
        if is_likely_flag(result):
            print(f"   🎉 POSIBLE FLAG: {result}")
    
    # 2. Hex variations
    print("\n🟨 Hexadecimal variations...")
    hex_results = try_hex_variations(cipher_text)
    all_results.extend(hex_results)
    for method, result in hex_results:
        print(f"   ✅ {method}: {result[:60]}...")
        if is_likely_flag(result):
            print(f"   🎉 POSIBLE FLAG: {result}")
    
    # 3. Caesar cipher
    print("\n🟩 Caesar cipher (todos los shifts)...")
    caesar_results = try_caesar_all_shifts(cipher_text)
    all_results.extend(caesar_results)
    for method, result in caesar_results[:5]:  # Solo mostrar primeros 5
        print(f"   ✅ {method}: {result[:60]}...")
        if is_likely_flag(result):
            print(f"   🎉 POSIBLE FLAG: {result}")
    
    # 4. ASCII shifts
    print(f"\n🟪 ASCII shifts (mostrando resultados prometedores)...")
    ascii_results = try_ascii_shifts(cipher_text)
    all_results.extend(ascii_results)
    promising_ascii = [r for r in ascii_results if is_likely_flag(r[1]) or 'flag' in r[1].lower()]
    for method, result in promising_ascii:
        print(f"   ✅ {method}: {result[:60]}...")
        if is_likely_flag(result):
            print(f"   🎉 POSIBLE FLAG: {result}")
    
    # 5. XOR single byte
    print(f"\n🟥 XOR single byte (resultados prometedores)...")
    xor_results = try_xor_single_byte(cipher_text)
    all_results.extend(xor_results)
    promising_xor = [r for r in xor_results if is_likely_flag(r[1]) or 'flag' in r[1].lower()]
    for method, result in promising_xor:
        print(f"   ✅ {method}: {result[:60]}...")
        if is_likely_flag(result):
            print(f"   🎉 POSIBLE FLAG: {result}")
    
    # 6. Substitution ciphers
    print(f"\n🟫 Substitution ciphers...")
    sub_results = try_substitution_ciphers(cipher_text)
    all_results.extend(sub_results)
    for method, result in sub_results:
        print(f"   ✅ {method}: {result[:60]}...")
        if is_likely_flag(result):
            print(f"   🎉 POSIBLE FLAG: {result}")
    
    # Buscar flags en todos los resultados
    print(f"\n🎯 BÚSQUEDA DE FLAGS EN TODOS LOS RESULTADOS:")
    print("-" * 50)
    
    flags_found = []
    for method, result in all_results:
        if is_likely_flag(result):
            flags_found.append((method, result))
            print(f"🏆 FLAG CANDIDATA ({method}): {result}")
    
    if not flags_found:
        print("❌ No se encontraron flags obvias")
        
        # Mostrar resultados más prometedores
        print(f"\n💡 RESULTADOS MÁS PROMETEDORES:")
        print("-" * 35)
        
        interesting = []
        for method, result in all_results:
            if (len(result) > 10 and 
                any(c.isalpha() for c in result) and 
                not all(c == result[0] for c in result)):
                interesting.append((method, result))
        
        for method, result in interesting[:10]:  # Top 10
            print(f"   {method}: {result[:50]}...")
    
    return flags_found

def main():
    # Leer el desafío
    cipher_file = "challenges/uploaded/ctf/cipher.txt"
    
    try:
        with open(cipher_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Extraer el texto cifrado (primera línea)
        cipher_text = lines[0].strip()
        
        print("🎯 SOLUCIONADOR ESPECIALIZADO CIPHER.TXT")
        print("=" * 45)
        print(f"📁 Archivo: {cipher_file}")
        print()
        
        # Análisis exhaustivo
        flags = analyze_cipher_exhaustive(cipher_text)
        
        if flags:
            print(f"\n🎉 ¡ÉXITO! Se encontraron {len(flags)} flag(s) candidata(s):")
            for i, (method, flag) in enumerate(flags, 1):
                print(f"   {i}. {method}: {flag}")
                
                # Guardar la primera flag encontrada
                if i == 1:
                    solved_file = "challenges/solved/cipher_solution_exhaustive.txt"
                    with open(solved_file, 'w', encoding='utf-8') as f:
                        f.write(f"Original: {cipher_text}\n")
                        f.write(f"Flag: {flag}\n")
                        f.write(f"Method: {method}\n")
                    print(f"💾 Solución guardada en: {solved_file}")
        else:
            print(f"\n⚠️  No se encontraron flags definitivas con técnicas estándar")
            print("💡 El desafío podría requerir:")
            print("   - Múltiples capas de codificación")
            print("   - Cifrados personalizados")
            print("   - Claves específicas")
            print("   - Algoritmos no estándar")
    
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {cipher_file}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()