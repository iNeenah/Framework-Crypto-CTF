#!/usr/bin/env python3
"""
Solucionador XOR Completo - Análisis detallado
==============================================
"""

def analyze_xor_challenge():
    """Análisis completo del desafío XOR"""
    print("🎯 ANÁLISIS COMPLETO XOR - CRYPTOHACK LEMUR")
    print("=" * 45)
    
    # Datos del desafío
    encrypted_hex = "73626960647f6b206821204f21254f7d694f7624662065204f7c65"
    known_start = "crypto{"
    known_end = "}"
    
    print(f"📋 Datos del desafío:")
    print(f"   Encrypted (hex): {encrypted_hex}")
    print(f"   Encrypted length: {len(encrypted_hex)//2} bytes")
    print(f"   Known start: '{known_start}'")
    print(f"   Known end: '{known_end}'")
    print()
    
    # Convertir a bytes
    encrypted = bytes.fromhex(encrypted_hex)
    
    # Análisis del inicio (crypto{)
    print("🔍 Análisis del inicio:")
    known_bytes = known_start.encode('utf-8')
    key_start = bytes(e ^ k for e, k in zip(encrypted[:len(known_bytes)], known_bytes))
    
    print(f"   Known bytes: {known_bytes.hex()} ('{known_start}')")
    print(f"   Encrypted start: {encrypted[:len(known_bytes)].hex()}")
    print(f"   Key pattern: {key_start.hex()}")
    print()
    
    # Análisis del final (})
    print("🔍 Análisis del final:")
    last_byte = encrypted[-1:]
    end_byte = known_end.encode('utf-8')
    key_end = bytes([last_byte[0] ^ end_byte[0]])
    
    print(f"   End byte: {end_byte.hex()} ('}}')")
    print(f"   Encrypted end: {last_byte.hex()}")
    print(f"   Key for end: {key_end.hex()}")
    print()
    
    # Verificar si es una clave simple
    if all(b == key_start[0] for b in key_start) and key_end[0] == key_start[0]:
        key_byte = key_start[0]
        print(f"✅ Clave detectada: 0x{key_byte:02x} (decimal: {key_byte})")
        
        # Descifrar todo
        full_key = bytes([key_byte] * len(encrypted))
        decrypted = bytes(e ^ k for e, k in zip(encrypted, full_key))
        
        try:
            flag = decrypted.decode('utf-8')
            print(f"🏆 FLAG COMPLETA: '{flag}'")
            
            # Verificar formato
            if flag.startswith('crypto{') and flag.endswith('}'):
                print("✅ ¡FLAG VÁLIDA!")
                
                # Guardar resultado
                with open("challenges/solved/cryptohack_xor_complete.txt", 'w') as f:
                    f.write(f"Challenge: CryptoHack Lemur XOR - SOLVED\n")
                    f.write(f"Method: Single-byte XOR key\n")
                    f.write(f"Key: 0x{key_byte:02x} ({key_byte})\n")
                    f.write(f"Encrypted: {encrypted_hex}\n")
                    f.write(f"FLAG: {flag}\n")
                    f.write(f"Status: COMPLETE\n")
                
                return flag
            else:
                print("⚠️  Formato de flag incorrecto")
                
        except UnicodeDecodeError:
            print("❌ Error de decodificación UTF-8")
    
    # Si la clave simple no funciona, intentar análisis más complejo
    print("\n🔄 Intentando análisis de clave variable...")
    
    # Probar longitudes de clave comunes
    for key_len in [1, 2, 3, 4, 5, 7, 8, 13, 16]:
        print(f"   Probando longitud de clave: {key_len}")
        
        if key_len <= len(known_bytes):
            # Extraer patrón de clave
            pattern = key_start[:key_len]
            
            # Crear clave completa repitiendo el patrón
            full_key = (pattern * (len(encrypted) // key_len + 1))[:len(encrypted)]
            
            # Descifrar
            decrypted = bytes(e ^ k for e, k in zip(encrypted, full_key))
            
            try:
                flag = decrypted.decode('utf-8')
                if flag.startswith('crypto{') and flag.endswith('}'):
                    print(f"   ✅ ¡FLAG ENCONTRADA! Key length: {key_len}")
                    print(f"   🏆 FLAG: '{flag}'")
                    
                    with open("challenges/solved/cryptohack_xor_complete.txt", 'w') as f:
                        f.write(f"Challenge: CryptoHack Lemur XOR - SOLVED\n")
                        f.write(f"Method: Multi-byte XOR key\n")
                        f.write(f"Key length: {key_len}\n")
                        f.write(f"Key pattern: {pattern.hex()}\n")
                        f.write(f"FLAG: {flag}\n")
                        f.write(f"Status: COMPLETE\n")
                    
                    return flag
                    
            except UnicodeDecodeError:
                continue
    
    print("❌ No se pudo resolver con métodos automáticos")
    return None

def brute_force_analysis():
    """Análisis de fuerza bruta como último recurso"""
    print("\n🔥 ANÁLISIS DE FUERZA BRUTA")
    
    encrypted_hex = "73626960647f6b206821204f21254f7d694f7624662065204f7c65"
    encrypted = bytes.fromhex(encrypted_hex)
    
    # Probar todas las claves de un byte
    for key_byte in range(256):
        full_key = bytes([key_byte] * len(encrypted))
        decrypted = bytes(e ^ k for e, k in zip(encrypted, full_key))
        
        try:
            flag = decrypted.decode('utf-8', errors='ignore')
            if 'crypto{' in flag and '}' in flag:
                # Limpiar caracteres extraños
                start = flag.find('crypto{')
                end = flag.find('}', start) + 1
                clean_flag = flag[start:end]
                
                if clean_flag.startswith('crypto{') and clean_flag.endswith('}'):
                    print(f"🎯 Candidato encontrado con clave 0x{key_byte:02x}:")
                    print(f"   FLAG: '{clean_flag}'")
                    return clean_flag, key_byte
                    
        except:
            continue
    
    return None, None

def main():
    """Función principal"""
    print("🚀 INICIANDO RESOLUCIÓN COMPLETA XOR\n")
    
    # Intentar análisis inteligente primero
    result = analyze_xor_challenge()
    
    if not result:
        # Si falla, usar fuerza bruta
        result, key = brute_force_analysis()
        
        if result:
            print(f"\n🎉 ¡DESAFÍO RESUELTO POR FUERZA BRUTA!")
            print(f"🔑 Clave: 0x{key:02x}")
            print(f"🏆 FLAG: {result}")
            
            with open("challenges/solved/cryptohack_xor_complete.txt", 'w') as f:
                f.write(f"Challenge: CryptoHack Lemur XOR - SOLVED\n")
                f.write(f"Method: Brute force single-byte XOR\n")
                f.write(f"Key: 0x{key:02x} ({key})\n")
                f.write(f"FLAG: {result}\n")
                f.write(f"Status: COMPLETE\n")
    
    if result:
        print(f"\n" + "🎉" * 20)
        print(f"DESAFÍO CRYPTOHACK XOR RESUELTO")
        print(f"FLAG: {result}")
        print(f"🎉" * 20)
    else:
        print(f"\n❌ No se pudo resolver el desafío")

if __name__ == "__main__":
    main()