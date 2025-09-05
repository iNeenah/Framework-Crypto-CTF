#!/usr/bin/env python3
"""
Solucionador para Desafío XOR - CryptoHack Lemur XOR
===================================================
Known Plaintext Attack contra cifrado XOR
"""

def hex_to_bytes(hex_string):
    """Convierte string hexadecimal a bytes"""
    return bytes.fromhex(hex_string)

def bytes_to_hex(data):
    """Convierte bytes a string hexadecimal"""
    return data.hex()

def xor_bytes(data1, data2):
    """XOR entre dos arrays de bytes"""
    return bytes(a ^ b for a, b in zip(data1, data2))

def solve_cryptohack_xor():
    """Resuelve el desafío XOR usando known plaintext attack"""
    print("🎯 SOLUCIONADOR XOR - CRYPTOHACK LEMUR XOR")
    print("=" * 45)
    
    # Datos del desafío
    encrypted_hex = "73626960647f6b206821204f21254f7d694f7624662065204f7c65"
    known_start = "crypto{"
    known_end = "}"
    
    print(f"📋 Datos del desafío:")
    print(f"   Encrypted (hex): {encrypted_hex}")
    print(f"   Known start: '{known_start}'")
    print(f"   Known end: '{known_end}'")
    print(f"   Encrypted length: {len(encrypted_hex)//2} bytes")
    print()
    
    # Convertir a bytes
    encrypted = hex_to_bytes(encrypted_hex)
    known_start_bytes = known_start.encode('utf-8')
    known_end_bytes = known_end.encode('utf-8')
    
    print(f"🔍 Análisis del cifrado:")
    print(f"   Encrypted bytes: {len(encrypted)} bytes")
    print(f"   Known start: {len(known_start_bytes)} bytes")
    print(f"   Known end: {len(known_end_bytes)} bytes")
    print()
    
    # Atacar usando known plaintext
    print("🚀 Ejecutando Known Plaintext Attack...")
    
    # Extraer la clave desde el inicio usando "crypto{"
    key_start = xor_bytes(encrypted[:len(known_start_bytes)], known_start_bytes)
    print(f"   Key start (from 'crypto{{'): {bytes_to_hex(key_start)}")
    print(f"   Key start (ASCII): '{key_start.decode('utf-8', errors='ignore')}'")
    
    # Extraer la clave desde el final usando "}"
    key_end = xor_bytes(encrypted[-len(known_end_bytes):], known_end_bytes)
    print(f"   Key end (from '}}'):  {bytes_to_hex(key_end)}")
    print(f"   Key end (ASCII): '{key_end.decode('utf-8', errors='ignore')}'")
    print()
    
    # Intentar reconstruir la clave completa
    print("🔧 Reconstruyendo la clave completa...")
    
    # Método 1: Asumir que la clave se repite
    key_pattern = key_start
    key_length = len(key_pattern)
    
    print(f"   Probando patrón de clave: '{key_pattern.decode('utf-8', errors='ignore')}'")
    print(f"   Longitud del patrón: {key_length}")
    
    # Extender la clave para que coincida con la longitud del mensaje cifrado
    full_key = b''
    for i in range(len(encrypted)):
        full_key += bytes([key_pattern[i % key_length]])
    
    print(f"   Clave completa (hex): {bytes_to_hex(full_key)}")
    print()
    
    # Descifrar el mensaje completo
    print("🔓 Descifrando mensaje completo...")
    decrypted = xor_bytes(encrypted, full_key)
    
    try:
        flag = decrypted.decode('utf-8')
        print(f"✅ Flag descifrada: '{flag}'")
        
        # Verificar que la flag tiene el formato correcto
        if flag.startswith('crypto{') and flag.endswith('}'):
            print("✅ Formato de flag CORRECTO")
            
            # Guardar resultado
            solved_file = "challenges/solved/cryptohack_xor_solution.txt"
            with open(solved_file, 'w', encoding='utf-8') as f:
                f.write(f"Challenge: CryptoHack - Lemur XOR\n")
                f.write(f"Method: Known Plaintext Attack\n")
                f.write(f"Encrypted (hex): {encrypted_hex}\n")
                f.write(f"Key pattern: {key_pattern.decode('utf-8', errors='ignore')}\n")
                f.write(f"Key (hex): {bytes_to_hex(full_key)}\n")
                f.write(f"FLAG: {flag}\n")
            
            print(f"💾 Solución guardada en: {solved_file}")
            return flag
            
        else:
            print("❌ Formato de flag INCORRECTO")
            print("🔄 Intentando otros métodos...")
            
            # Método 2: Intentar con diferentes longitudes de clave
            return try_different_key_lengths(encrypted, known_start_bytes, known_end_bytes)
            
    except UnicodeDecodeError:
        print("❌ Error decodificando como UTF-8")
        print("🔄 Intentando otros métodos...")
        return try_different_key_lengths(encrypted, known_start_bytes, known_end_bytes)

def try_different_key_lengths(encrypted, known_start, known_end):
    """Intenta diferentes longitudes de clave"""
    print("\n🔄 Probando diferentes longitudes de clave...")
    
    for key_len in range(1, min(20, len(encrypted) + 1)):
        print(f"   Probando longitud de clave: {key_len}")
        
        # Extraer clave parcial del inicio
        if len(known_start) >= key_len:
            key_partial = xor_bytes(encrypted[:key_len], known_start[:key_len])
        else:
            key_partial = xor_bytes(encrypted[:len(known_start)], known_start)
            # Completar con bytes del final si es necesario
            if key_len > len(known_start):
                end_start = len(encrypted) - (key_len - len(known_start))
                key_end_part = xor_bytes(encrypted[end_start:end_start + (key_len - len(known_start))], 
                                       known_end[:key_len - len(known_start)])
                key_partial += key_end_part
        
        # Construir clave completa
        full_key = b''
        for i in range(len(encrypted)):
            full_key += bytes([key_partial[i % key_len]])
        
        # Descifrar
        decrypted = xor_bytes(encrypted, full_key)
        
        try:
            flag = decrypted.decode('utf-8')
            if flag.startswith('crypto{') and flag.endswith('}'):
                print(f"✅ ¡FLAG ENCONTRADA con longitud {key_len}!")
                print(f"🏆 FLAG: {flag}")
                
                # Guardar resultado
                solved_file = "challenges/solved/cryptohack_xor_solution.txt"
                with open(solved_file, 'w', encoding='utf-8') as f:
                    f.write(f"Challenge: CryptoHack - Lemur XOR\n")
                    f.write(f"Method: Known Plaintext Attack (key length {key_len})\n")
                    f.write(f"Key pattern: {key_partial.decode('utf-8', errors='ignore')}\n")
                    f.write(f"Key (hex): {bytes_to_hex(full_key)}\n")
                    f.write(f"FLAG: {flag}\n")
                
                print(f"💾 Solución guardada en: {solved_file}")
                return flag
                
        except UnicodeDecodeError:
            continue
    
    print("❌ No se pudo encontrar la flag con ninguna longitud de clave")
    return None

def main():
    """Función principal"""
    flag = solve_cryptohack_xor()
    
    if flag:
        print(f"\n🎉 ¡DESAFÍO RESUELTO!")
        print(f"🎯 Desafío: CryptoHack Lemur XOR")
        print(f"🔧 Método: Known Plaintext Attack")
        print(f"🏆 FLAG: {flag}")
        print(f"✅ Estado: RESUELTO")
    else:
        print(f"\n❌ No se pudo resolver el desafío")

if __name__ == "__main__":
    main()