#!/usr/bin/env python3
"""
Analizador Alternativo para Cipher.txt
Perspectivas no convencionales: esteganografía, patrones ocultos, etc.
"""

import re
import string
from collections import Counter, defaultdict

def analyze_character_patterns(text):
    """Analiza patrones de caracteres en el texto"""
    print("🔍 ANÁLISIS DE PATRONES DE CARACTERES")
    print("-" * 40)
    
    # Análisis de frecuencia
    char_freq = Counter(text)
    print(f"📊 Frecuencia de caracteres:")
    for char, count in char_freq.most_common():
        print(f"   '{char}': {count}")
    
    # Análisis de posiciones
    print(f"\n📍 Análisis de posiciones:")
    char_positions = defaultdict(list)
    for i, char in enumerate(text):
        char_positions[char].append(i)
    
    for char in ['#', '&', '_', "'", ';']:
        if char in char_positions:
            positions = char_positions[char]
            print(f"   '{char}': posiciones {positions}")
            if len(positions) > 1:
                gaps = [positions[i+1] - positions[i] for i in range(len(positions)-1)]
                print(f"        gaps: {gaps}")

def analyze_substitution_patterns(text):
    """Analiza posibles patrones de sustitución"""
    print("\n🔤 ANÁLISIS DE PATRONES DE SUSTITUCIÓN")
    print("-" * 45)
    
    # Buscar repeticiones de secuencias
    print("🔍 Secuencias repetidas:")
    for length in [2, 3, 4, 5]:
        found = set()
        for i in range(len(text) - length + 1):
            seq = text[i:i+length]
            if text.count(seq) > 1 and seq not in found:
                positions = [j for j in range(len(text) - length + 1) if text[j:j+length] == seq]
                print(f"   '{seq}' (longitud {length}): aparece en posiciones {positions}")
                found.add(seq)

def extract_by_character_types(text):
    """Extrae caracteres por tipos específicos"""
    print("\n📋 EXTRACCIÓN POR TIPOS DE CARACTERES")
    print("-" * 40)
    
    extractions = {
        'letters_only': ''.join(c for c in text if c.isalpha()),
        'digits_only': ''.join(c for c in text if c.isdigit()),
        'symbols_only': ''.join(c for c in text if not c.isalnum()),
        'uppercase_only': ''.join(c for c in text if c.isupper()),
        'lowercase_only': ''.join(c for c in text if c.islower())
    }
    
    for extraction_type, result in extractions.items():
        if result:
            print(f"   {extraction_type}: {result}")
            
            # Verificar si parece una flag
            if (len(result) > 8 and 
                ('{' in result and '}' in result) or 
                any(word in result.lower() for word in ['flag', 'ctf', 'crypto'])):
                print(f"      🎯 POSIBLE FLAG: {result}")

def analyze_positional_extraction(text):
    """Extrae caracteres basado en posiciones específicas"""
    print("\n📍 EXTRACCIÓN POSICIONAL")
    print("-" * 25)
    
    patterns = {
        'every_2nd': text[::2],
        'every_3rd': text[::3],
        'every_4th': text[::4],
        'every_5th': text[::5],
        'odd_positions': text[1::2],
        'even_positions': text[::2],
        'first_half': text[:len(text)//2],
        'second_half': text[len(text)//2:],
        'first_third': text[:len(text)//3],
        'middle_third': text[len(text)//3:2*len(text)//3],
        'last_third': text[2*len(text)//3:]
    }
    
    for pattern_name, result in patterns.items():
        print(f"   {pattern_name}: {result}")
        
        # Verificar si parece una flag
        if (len(result) > 8 and 
            ('{' in result and '}' in result)):
            print(f"      🎯 POSIBLE FLAG: {result}")

def analyze_ascii_values(text):
    """Analiza valores ASCII para buscar patrones"""
    print("\n🔢 ANÁLISIS DE VALORES ASCII")
    print("-" * 30)
    
    ascii_values = [ord(c) for c in text]
    print(f"   Rango ASCII: {min(ascii_values)} - {max(ascii_values)}")
    print(f"   Promedio: {sum(ascii_values) / len(ascii_values):.1f}")
    
    # Buscar secuencias numéricas en ASCII
    ascii_string = ''.join(str(ord(c)) for c in text)
    print(f"   ASCII concatenado: {ascii_string[:50]}...")
    
    # Intentar interpretarlo como decimal/hex
    try:
        # Cada carácter como 2 dígitos hex
        hex_pairs = [f"{ord(c):02x}" for c in text]
        hex_string = ''.join(hex_pairs)
        print(f"   Hex concatenado: {hex_string[:50]}...")
        
        # Intentar decodificar hex como texto
        if len(hex_string) % 2 == 0:
            try:
                decoded_hex = bytes.fromhex(hex_string).decode('utf-8', errors='ignore')
                if all(32 <= ord(c) <= 126 for c in decoded_hex):
                    print(f"   🎯 Hex decodificado: {decoded_hex}")
            except:
                pass
    except:
        pass

def analyze_mathematical_patterns(text):
    """Busca patrones matemáticos en el texto"""
    print("\n🧮 ANÁLISIS MATEMÁTICO")
    print("-" * 22)
    
    # Buscar números en el texto
    numbers = re.findall(r'\d+', text)
    if numbers:
        print(f"   Números encontrados: {numbers}")
        
        # Intentar operaciones matemáticas
        if len(numbers) >= 2:
            nums = [int(n) for n in numbers]
            print(f"   Suma: {sum(nums)}")
            print(f"   Producto: {nums[0] * nums[1] if len(nums) >= 2 else 'N/A'}")
    
    # Análisis de posiciones de caracteres especiales
    special_positions = []
    for i, char in enumerate(text):
        if char in '{}[]()':
            special_positions.append(i)
    
    if special_positions:
        print(f"   Posiciones de caracteres especiales: {special_positions}")

def try_keyboard_interpretations(text):
    """Intenta interpretaciones basadas en teclado"""
    print("\n⌨️  INTERPRETACIONES DE TECLADO")
    print("-" * 32)
    
    # Mapeo de teclado QWERTY
    qwerty_rows = [
        "`1234567890-=",
        "qwertyuiop[]\\",
        "asdfghjkl;'",
        "zxcvbnm,./"
    ]
    
    # Buscar patrones de teclado
    for i, row in enumerate(qwerty_rows):
        chars_in_row = [c for c in text.lower() if c in row]
        if len(chars_in_row) > 5:
            print(f"   Fila {i+1}: {''.join(chars_in_row)}")
    
    # Intentar shift de teclado
    keyboard_shift = {
        '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
        '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
        '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|',
        ';': ':', "'": '"', ',': '<', '.': '>', '/': '?'
    }
    
    shifted = ''
    for char in text:
        if char.lower() in keyboard_shift:
            shifted += keyboard_shift[char.lower()]
        else:
            shifted += char
    
    if shifted != text:
        print(f"   Keyboard shift aplicado: {shifted}")

def hidden_message_analysis(text):
    """Busca mensajes ocultos usando técnicas de esteganografía simple"""
    print("\n🕵️  BÚSQUEDA DE MENSAJES OCULTOS")
    print("-" * 35)
    
    # Primeras letras de palabras (si existen separadores)
    words = re.split(r'[^a-zA-Z0-9]', text)
    words = [w for w in words if w]
    if words:
        first_letters = ''.join(w[0] for w in words if w)
        print(f"   Primeras letras: {first_letters}")
        
        if len(first_letters) > 5:
            # Verificar si forma una palabra/flag
            print(f"   🎯 POSIBLE MENSAJE: {first_letters}")
    
    # Análisis de mayúsculas
    uppercase_chars = ''.join(c for c in text if c.isupper())
    if uppercase_chars:
        print(f"   Solo mayúsculas: {uppercase_chars}")
        if len(uppercase_chars) > 5:
            print(f"   🎯 POSIBLE MENSAJE: {uppercase_chars}")

def main():
    # Leer el desafío
    cipher_file = "challenges/uploaded/ctf/cipher.txt"
    
    try:
        with open(cipher_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Extraer el texto cifrado (primera línea)
        cipher_text = lines[0].strip()
        
        print("🎯 ANALIZADOR ALTERNATIVO CIPHER.TXT")
        print("=" * 40)
        print(f"📁 Archivo: {cipher_file}")
        print(f"🔐 Texto cifrado: {cipher_text}")
        print(f"📏 Longitud: {len(cipher_text)} caracteres")
        print()
        
        # Ejecutar todos los análisis
        analyze_character_patterns(cipher_text)
        analyze_substitution_patterns(cipher_text)
        extract_by_character_types(cipher_text)
        analyze_positional_extraction(cipher_text)
        analyze_ascii_values(cipher_text)
        analyze_mathematical_patterns(cipher_text)
        try_keyboard_interpretations(cipher_text)
        hidden_message_analysis(cipher_text)
        
        print(f"\n🎯 ANÁLISIS COMPLETO TERMINADO")
        print(f"💡 Revisa los resultados marcados con 🎯 para posibles flags")
        
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {cipher_file}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()