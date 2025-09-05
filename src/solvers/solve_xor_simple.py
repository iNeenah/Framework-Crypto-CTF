#!/usr/bin/env python3
"""
Solucionador XOR Simple - Todas las claves posibles
===================================================
"""

def solve_all_single_byte_keys():
    """Prueba todas las claves de un solo byte"""
    print("🎯 SOLUCIONADOR XOR SIMPLE - TODAS LAS CLAVES")
    print("=" * 45)
    
    # Datos del desafío
    encrypted_hex = "73626960647f6b206821204f21254f7d694f7624662065204f7c65"
    encrypted = bytes.fromhex(encrypted_hex)
    
    print(f"📋 Probando todas las claves de un byte (0x00 - 0xFF)...")
    print()
    
    valid_flags = []
    
    for key_byte in range(256):
        # Crear clave completa
        full_key = bytes([key_byte] * len(encrypted))
        
        # Descifrar
        decrypted = bytes(e ^ k for e, k in zip(encrypted, full_key))
        
        try:
            # Intentar decodificar como UTF-8
            flag = decrypted.decode('utf-8')
            
            # Verificar si parece una flag válida
            if flag.startswith('crypto{') and flag.endswith('}'):
                # Verificar que todos los caracteres son imprimibles
                if all(32 <= ord(c) <= 126 for c in flag):
                    print(f"🎯 Clave 0x{key_byte:02x}: '{flag}'")
                    valid_flags.append((key_byte, flag))
                    
        except UnicodeDecodeError:
            # Ignorar si no se puede decodificar
            continue
    
    if valid_flags:
        print(f"\n✅ Flags válidas encontradas: {len(valid_flags)}")
        
        # Tomar la más probable (la que se ve más como una flag real)
        best_flag = None
        best_key = None
        
        for key, flag in valid_flags:
            # Heurísticas para determinar la mejor flag:
            # 1. Debe tener contenido razonable entre crypto{ y }
            # 2. Debe tener longitud razonable
            # 3. Debe usar caracteres alfanuméricos principalmente
            
            content = flag[7:-1]  # Remover crypto{ y }
            
            if len(content) > 5:  # Debe tener contenido mínimo
                # Contar caracteres alfanuméricos
                alnum_count = sum(1 for c in content if c.isalnum() or c in '_{}')
                score = alnum_count / len(content)
                
                print(f"   Clave 0x{key:02x}: score {score:.2f} - '{flag}'")
                
                if score > 0.7:  # Mayoría de caracteres válidos
                    best_key = key
                    best_flag = flag
        
        if best_flag:
            print(f"\n🏆 MEJOR FLAG: '{best_flag}' (clave 0x{best_key:02x})")
            
            # Guardar resultado
            with open("challenges/solved/cryptohack_xor_simple.txt", 'w') as f:
                f.write(f"Challenge: CryptoHack Lemur XOR - SIMPLE\n")
                f.write(f"Method: Single-byte XOR key\n")
                f.write(f"Key: 0x{best_key:02x} ({best_key})\n")
                f.write(f"FLAG: {best_flag}\n")
                f.write(f"All valid flags: {valid_flags}\n")
                f.write(f"Status: SOLVED\n")
            
            return best_flag
        else:
            print(f"⚠️  Múltiples candidatos, revisar manualmente")
            return valid_flags[0][1] if valid_flags else None
    
    else:
        print("❌ No se encontraron flags válidas con claves de un byte")
        return None

def solve_repeating_key_patterns():
    """Prueba patrones de clave repetitiva"""
    print("\n🔄 PROBANDO PATRONES DE CLAVE REPETITIVA...")
    
    encrypted_hex = "73626960647f6b206821204f21254f7d694f7624662065204f7c65"
    encrypted = bytes.fromhex(encrypted_hex)
    
    # Patrones comunes
    common_patterns = [
        "key",
        "xor", 
        "lemur",  # Basado en el nombre del challenge
        "cryptohack",
        "flag",
        "secret",
        "0123456789",
        "abcdef"
    ]
    
    for pattern in common_patterns:
        print(f"   Probando patrón: '{pattern}'")
        
        # Crear clave repitiendo el patrón
        pattern_bytes = pattern.encode('utf-8')
        full_key = (pattern_bytes * (len(encrypted) // len(pattern_bytes) + 1))[:len(encrypted)]
        
        # Descifrar
        decrypted = bytes(e ^ k for e, k in zip(encrypted, full_key))
        
        try:
            flag = decrypted.decode('utf-8')
            if flag.startswith('crypto{') and flag.endswith('}'):
                if all(32 <= ord(c) <= 126 for c in flag):
                    print(f"      ✅ FLAG: '{flag}'")
                    return flag
                    
        except UnicodeDecodeError:
            continue
    
    return None

def main():
    """Función principal"""
    print("🚀 SOLUCIONADOR XOR EXHAUSTIVO\n")
    
    # Intentar claves de un byte primero
    result = solve_all_single_byte_keys()
    
    # Si no funciona, intentar patrones repetitivos
    if not result:
        result = solve_repeating_key_patterns()
    
    if result:
        print(f"\n" + "🎉" * 30)
        print(f"CRYPTOHACK LEMUR XOR RESUELTO")
        print(f"FLAG: {result}")
        print(f"🎉" * 30)
    else:
        print(f"\n❌ No se pudo resolver con métodos automáticos")
        print(f"💡 Puede requerir análisis manual más profundo")

if __name__ == "__main__":
    main()