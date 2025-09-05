#!/usr/bin/env python3
"""
Solucionador Refinado para Cipher.txt
Búsqueda enfocada en flags válidas y técnicas multicapa
"""

import base64
import urllib.parse
import codecs
import string
import re
import binascii
from collections import Counter

def is_valid_flag_format(text):
    """Verifica si el texto tiene formato de flag válido"""
    if not text:
        return False
    
    # Patrones de flags válidas más estrictos
    valid_patterns = [
        r'^[a-zA-Z]{3,8}\{[a-zA-Z0-9_]{8,}\}$',  # formato: prefix{content}
        r'^\{[a-zA-Z0-9_]{10,}\}$',               # formato: {content}
        r'^flag\{[^}]{8,}\}$',                    # formato: flag{content}
        r'^ctf\{[^}]{8,}\}$',                     # formato: ctf{content}
        r'^crypto\{[^}]{8,}\}$'                   # formato: crypto{content}
    ]
    
    for pattern in valid_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    
    return False

def is_readable_text(text):
    """Verifica si el texto es legible (principalmente ASCII)"""
    if not text or len(text) < 5:
        return False
    
    try:
        # Debe ser principalmente ASCII imprimible
        printable_count = sum(1 for c in text if 32 <= ord(c) <= 126)
        ratio = printable_count / len(text)
        
        # Al menos 80% debe ser ASCII imprimible
        return ratio >= 0.8
    except:
        return False

def apply_base64_decode(data):
    """Aplica decodificación Base64 con padding automático"""
    try:
        # Agregar padding si es necesario
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)
        
        decoded = base64.b64decode(data).decode('utf-8', errors='ignore')
        return decoded if is_readable_text(decoded) else None
    except:
        return None

def apply_url_decode(data):
    """Aplica decodificación URL"""
    try:
        decoded = urllib.parse.unquote(data)
        return decoded if decoded != data and is_readable_text(decoded) else None
    except:
        return None

def apply_hex_decode(data):
    """Aplica decodificación hexadecimal"""
    try:
        # Remover caracteres no hex
        cleaned = re.sub(r'[^0-9a-fA-F]', '', data)
        if len(cleaned) % 2 == 0 and len(cleaned) >= 8:
            decoded = bytes.fromhex(cleaned).decode('utf-8', errors='ignore')
            return decoded if is_readable_text(decoded) else None
    except:
        return None

def apply_rot13(data):
    """Aplica ROT13"""
    try:
        decoded = codecs.decode(data, 'rot13')
        return decoded if is_readable_text(decoded) else None
    except:
        return None

def apply_ascii_shift(data, shift):
    """Aplica shift ASCII"""
    try:
        decoded = ""
        for char in data:
            if 32 <= ord(char) <= 126:
                new_char = chr(((ord(char) - 32 - shift) % 95) + 32)
                decoded += new_char
            else:
                decoded += char
        
        return decoded if is_readable_text(decoded) else None
    except:
        return None

def apply_atbash(data):
    """Aplica cifrado Atbash"""
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
        
        return decoded if is_readable_text(decoded) else None
    except:
        return None

def apply_reverse(data):
    """Aplica reverse"""
    try:
        decoded = data[::-1]
        return decoded if is_readable_text(decoded) else None
    except:
        return None

def solve_multilayer_refined(cipher_text, max_depth=10):
    """Resuelve desafío multicapa con búsqueda refinada de flags"""
    
    # Técnicas de decodificación disponibles
    techniques = [
        ('base64', apply_base64_decode),
        ('url_decode', apply_url_decode),
        ('hex_decode', apply_hex_decode),
        ('rot13', apply_rot13),
        ('atbash', apply_atbash),
        ('reverse', apply_reverse)
    ]
    
    # Agregar ASCII shifts prometedores (basado en análisis anterior)
    promising_shifts = [3, 9, 10, 11, 29, 31, 50, 58]
    for shift in promising_shifts:
        techniques.append((f'ascii_shift_{shift}', lambda x, s=shift: apply_ascii_shift(x, s)))
    
    print(f"🎯 BÚSQUEDA REFINADA DE FLAGS MULTICAPA")
    print(f"📝 Texto inicial: {cipher_text}")
    print(f"🔧 Técnicas disponibles: {len(techniques)}")
    print("=" * 70)
    
    # Función recursiva para explorar combinaciones
    def explore_combinations(current_text, depth=0, path=[]):
        if depth >= max_depth:
            return []
        
        results = []
        
        # Verificar si el texto actual es una flag
        if is_valid_flag_format(current_text):
            results.append({
                'flag': current_text,
                'path': path.copy(),
                'depth': depth
            })
            print(f"🎉 FLAG ENCONTRADA (profundidad {depth}): {current_text}")
            print(f"📍 Camino: {' → '.join(path)}")
        
        # Si llegamos aquí y ya encontramos una flag, no seguir explorando
        if results:
            return results
        
        # Probar cada técnica
        for technique_name, technique_func in techniques:
            try:
                decoded = technique_func(current_text)
                
                if decoded and decoded != current_text:
                    # Verificar inmediatamente si es flag
                    if is_valid_flag_format(decoded):
                        new_path = path + [technique_name]
                        results.append({
                            'flag': decoded,
                            'path': new_path,
                            'depth': depth + 1
                        })
                        print(f"🎉 FLAG ENCONTRADA (profundidad {depth + 1}): {decoded}")
                        print(f"📍 Camino: {' → '.join(new_path)}")
                    else:
                        # Explorar más profundo solo si el texto parece prometedor
                        if depth < 3 and is_readable_text(decoded):
                            new_path = path + [technique_name]
                            deeper_results = explore_combinations(decoded, depth + 1, new_path)
                            results.extend(deeper_results)
                            
            except Exception as e:
                continue
        
        return results
    
    # Ejecutar búsqueda
    all_flags = explore_combinations(cipher_text)
    
    print(f"\n📊 RESUMEN DE BÚSQUEDA:")
    print("-" * 30)
    
    if all_flags:
        print(f"🎉 Se encontraron {len(all_flags)} flag(s) válida(s):")
        
        for i, result in enumerate(all_flags, 1):
            print(f"\n{i}. {result['flag']}")
            print(f"   Profundidad: {result['depth']}")
            print(f"   Camino: {' → '.join(result['path'])}")
            
        return all_flags[0]  # Retornar la primera flag encontrada
    else:
        print("❌ No se encontraron flags con formato válido")
        
        # Intentar búsqueda menos estricta
        print("\n🔍 Búsqueda menos estricta de texto legible...")
        readable_results = find_readable_results(cipher_text)
        
        if readable_results:
            print("💡 Textos legibles encontrados:")
            for technique, result in readable_results[:5]:
                print(f"   {technique}: {result[:50]}...")
        
        return None

def find_readable_results(cipher_text):
    """Encuentra resultados legibles aunque no sean flags perfectas"""
    techniques = [
        ('base64', apply_base64_decode),
        ('url_decode', apply_url_decode),
        ('hex_decode', apply_hex_decode),
        ('rot13', apply_rot13),
        ('atbash', apply_atbash),
        ('reverse', apply_reverse)
    ]
    
    # Agregar algunos ASCII shifts
    for shift in [1, 2, 3, 5, 10, 13, 25]:
        techniques.append((f'ascii_shift_{shift}', lambda x, s=shift: apply_ascii_shift(x, s)))
    
    readable_results = []
    
    for technique_name, technique_func in techniques:
        try:
            result = technique_func(cipher_text)
            if result and is_readable_text(result) and len(result) > 10:
                readable_results.append((technique_name, result))
        except:
            continue
    
    return readable_results

def main():
    # Leer el desafío
    cipher_file = "challenges/uploaded/ctf/cipher.txt"
    
    try:
        with open(cipher_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Extraer el texto cifrado (primera línea)
        cipher_text = lines[0].strip()
        
        print("🎯 SOLUCIONADOR REFINADO CIPHER.TXT")
        print("=" * 38)
        print(f"📁 Archivo: {cipher_file}")
        print(f"🔐 Texto cifrado: {cipher_text}")
        print(f"📏 Longitud: {len(cipher_text)} caracteres")
        print()
        
        # Análisis rápido de caracteres
        char_analysis = Counter(cipher_text)
        print(f"🔤 Caracteres únicos: {len(char_analysis)}")
        print(f"🔢 Caracteres más frecuentes: {dict(char_analysis.most_common(5))}")
        print()
        
        # Resolver
        result = solve_multilayer_refined(cipher_text)
        
        if result:
            print(f"\n✅ ¡ÉXITO! Flag encontrada:")
            print(f"🏆 FLAG: {result['flag']}")
            print(f"📊 Profundidad: {result['depth']} capas")
            print(f"🛠️  Técnicas usadas: {' → '.join(result['path'])}")
            
            # Guardar resultado
            solved_file = "challenges/solved/cipher_solution_refined.txt"
            with open(solved_file, 'w', encoding='utf-8') as f:
                f.write(f"Original: {cipher_text}\n")
                f.write(f"Flag: {result['flag']}\n")
                f.write(f"Depth: {result['depth']}\n")
                f.write(f"Techniques: {' → '.join(result['path'])}\n")
            
            print(f"💾 Solución guardada en: {solved_file}")
            
        else:
            print(f"\n⚠️  No se encontró flag con formato estándar")
            print("💡 Posibles razones:")
            print("   - El desafío requiere claves específicas")
            print("   - Usa algoritmos de cifrado no estándar")
            print("   - Necesita múltiples capas específicas")
            print("   - Requiere conocimiento adicional del contexto")
    
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {cipher_file}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()