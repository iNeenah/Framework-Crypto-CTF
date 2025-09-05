#!/usr/bin/env python3
"""
Solucionador Basado en Patrones Específicos
Usando los hallazgos del análisis alternativo
"""

import re

def extract_specific_patterns(text):
    """Extrae patrones específicos basados en el análisis"""
    results = {}
    
    # Patrones encontrados en el análisis
    results['letters_only'] = ''.join(c for c in text if c.isalpha())
    results['digits_only'] = ''.join(c for c in text if c.isdigit())
    results['uppercase_only'] = ''.join(c for c in text if c.isupper())
    results['lowercase_only'] = ''.join(c for c in text if c.islower())
    
    # Extracción posicional prometedora
    results['every_2nd'] = text[::2]
    results['every_3rd'] = text[::3]
    results['odd_positions'] = text[1::2]
    results['even_positions'] = text[::2]
    
    # Mensaje oculto de primeras letras
    words = re.split(r'[^a-zA-Z0-9]', text)
    words = [w for w in words if w]
    if words:
        results['first_letters'] = ''.join(w[0] for w in words if w)
    
    return results

def try_reverse_combinations(text):
    """Prueba combinaciones con reverse"""
    results = {}
    
    # Reverse completo
    results['reverse_full'] = text[::-1]
    
    # Reverse por mitades
    mid = len(text) // 2
    first_half = text[:mid]
    second_half = text[mid:]
    
    results['reverse_halves'] = first_half[::-1] + second_half[::-1]
    results['reverse_first_half'] = first_half[::-1] + second_half
    results['reverse_second_half'] = first_half + second_half[::-1]
    
    # Reverse por palabras (separadas por caracteres especiales)
    words = re.findall(r'[a-zA-Z0-9]+', text)
    if words:
        reversed_words = [word[::-1] for word in words]
        results['reverse_words'] = ''.join(reversed_words)
    
    return results

def apply_modular_arithmetic(text):
    """Aplica aritmética modular basada en patrones numéricos"""
    results = {}
    
    # Suma de números encontrados: 115 (del análisis)
    # Producto: 178
    # Posiciones especiales: [32, 40, 49, 63, 68, 75]
    
    # Usar suma como clave Caesar
    caesar_key = 115 % 26  # 11
    caesar_result = ""
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            caesar_result += chr((ord(char) - base + caesar_key) % 26 + base)
        else:
            caesar_result += char
    results['caesar_sum'] = caesar_result
    
    # Usar producto como clave ASCII
    ascii_key = 178 % 95  # 83
    ascii_result = ""
    for char in text:
        if 32 <= ord(char) <= 126:
            ascii_result += chr(((ord(char) - 32 + ascii_key) % 95) + 32)
        else:
            ascii_result += char
    results['ascii_product'] = ascii_result
    
    return results

def extract_by_special_positions(text):
    """Extrae caracteres en posiciones especiales encontradas"""
    results = {}
    
    # Posiciones de caracteres especiales: [32, 40, 49, 63, 68, 75]
    special_positions = [32, 40, 49, 63, 68, 75]
    
    # Extraer caracteres en esas posiciones
    special_chars = ""
    for pos in special_positions:
        if pos < len(text):
            special_chars += text[pos]
    results['at_special_positions'] = special_chars
    
    # Extraer caracteres entre posiciones especiales
    between_chars = ""
    for i in range(len(special_positions) - 1):
        start = special_positions[i] + 1
        end = special_positions[i + 1]
        if start < len(text) and end <= len(text):
            between_chars += text[start:end]
    results['between_special_positions'] = between_chars
    
    return results

def try_frequency_based_substitution(text):
    """Intenta sustitución basada en frecuencia de caracteres"""
    results = {}
    
    # Caracteres más frecuentes del análisis: #, &, N, _, ', ;, h, +, ), 4, `
    # Intentar mapearlos a letras comunes en inglés: e, t, a, o, i, n, s, h, r, d, l
    
    common_english = 'etaoinshrdl'
    most_frequent_cipher = '#&N_;h+)4`='  # Los más frecuentes del cipher
    
    # Crear mapeo
    substitution_map = {}
    for i, cipher_char in enumerate(most_frequent_cipher):
        if i < len(common_english):
            substitution_map[cipher_char] = common_english[i]
    
    # Aplicar sustitución
    substituted = ""
    for char in text:
        if char in substitution_map:
            substituted += substitution_map[char]
        else:
            substituted += char.lower()
    
    results['frequency_substitution'] = substituted
    
    return results

def check_for_flags(result_dict):
    """Verifica si algún resultado contiene una flag válida"""
    flags_found = []
    
    for method, result in result_dict.items():
        if not result:
            continue
            
        # Buscar patrones de flag
        flag_patterns = [
            r'flag\{[^}]+\}',
            r'ctf\{[^}]+\}',
            r'crypto\{[^}]+\}',
            r'\{[a-zA-Z0-9_]{8,}\}',
            r'[a-zA-Z]{3,8}\{[^}]{5,}\}'
        ]
        
        for pattern in flag_patterns:
            matches = re.findall(pattern, result, re.IGNORECASE)
            for match in matches:
                flags_found.append((method, match))
                
        # También buscar texto que contenga "flag" de manera obvia
        if 'flag' in result.lower() and len(result) > 10:
            flags_found.append((method, f"Contains 'flag': {result}"))
    
    return flags_found

def main():
    # Leer el desafío
    cipher_file = "challenges/uploaded/ctf/cipher.txt"
    
    try:
        with open(cipher_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Extraer el texto cifrado (primera línea)
        cipher_text = lines[0].strip()
        
        print("🎯 SOLUCIONADOR BASADO EN PATRONES ESPECÍFICOS")
        print("=" * 50)
        print(f"📁 Archivo: {cipher_file}")
        print(f"🔐 Texto cifrado: {cipher_text}")
        print()
        
        all_results = {}
        
        # 1. Extraer patrones específicos
        print("📋 EXTRAYENDO PATRONES ESPECÍFICOS...")
        pattern_results = extract_specific_patterns(cipher_text)
        all_results.update(pattern_results)
        for method, result in pattern_results.items():
            print(f"   {method}: {result}")
        
        # 2. Probar combinaciones con reverse
        print(f"\n🔄 PROBANDO COMBINACIONES CON REVERSE...")
        reverse_results = try_reverse_combinations(cipher_text)
        all_results.update(reverse_results)
        for method, result in reverse_results.items():
            print(f"   {method}: {result[:60]}...")
        
        # 3. Aplicar aritmética modular
        print(f"\n🧮 APLICANDO ARITMÉTICA MODULAR...")
        math_results = apply_modular_arithmetic(cipher_text)
        all_results.update(math_results)
        for method, result in math_results.items():
            print(f"   {method}: {result[:60]}...")
        
        # 4. Extraer por posiciones especiales
        print(f"\n📍 EXTRAYENDO POR POSICIONES ESPECIALES...")
        position_results = extract_by_special_positions(cipher_text)
        all_results.update(position_results)
        for method, result in position_results.items():
            print(f"   {method}: {result}")
        
        # 5. Sustitución basada en frecuencia
        print(f"\n🔤 SUSTITUCIÓN BASADA EN FRECUENCIA...")
        freq_results = try_frequency_based_substitution(cipher_text)
        all_results.update(freq_results)
        for method, result in freq_results.items():
            print(f"   {method}: {result[:60]}...")
        
        # 6. Buscar flags en todos los resultados
        print(f"\n🎯 BÚSQUEDA DE FLAGS...")
        flags_found = check_for_flags(all_results)
        
        if flags_found:
            print(f"🎉 ¡Se encontraron {len(flags_found)} posible(s) flag(s)!")
            for i, (method, flag) in enumerate(flags_found, 1):
                print(f"   {i}. {method}: {flag}")
                
            # Guardar la primera flag encontrada
            if flags_found:
                method, flag = flags_found[0]
                solved_file = "challenges/solved/cipher_solution_patterns.txt"
                with open(solved_file, 'w', encoding='utf-8') as f:
                    f.write(f"Original: {cipher_text}\n")
                    f.write(f"Flag: {flag}\n")
                    f.write(f"Method: {method}\n")
                print(f"💾 Solución guardada en: {solved_file}")
        else:
            print("❌ No se encontraron flags obvias en los patrones analizados")
            
            # Mostrar resultados más prometedores
            print(f"\n💡 RESULTADOS MÁS PROMETEDORES:")
            interesting = [(k, v) for k, v in all_results.items() 
                          if v and len(v) > 5 and any(c.isalpha() for c in v)]
            
            for method, result in interesting[:10]:
                print(f"   {method}: {result}")
                
            print(f"\n💭 SUGERENCIAS ADICIONALES:")
            print("   - El desafío podría requerir múltiples pasos combinados")
            print("   - Podría necesitar una clave específica o conocimiento del contexto")
            print("   - Intenta aplicar estas técnicas en secuencia")
            print("   - Considera que la descripción 'múltiples disfraces' indica capas complejas")
    
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {cipher_file}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()