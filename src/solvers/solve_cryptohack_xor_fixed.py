#!/usr/bin/env python3
"""
Solucionador XOR Corregido - CryptoHack Lemur XOR
================================================
"""

def solve_xor_challenge():
    """Resuelve el desafío XOR de manera simple y efectiva"""
    print("🎯 SOLUCIONADOR XOR CORREGIDO - CRYPTOHACK")
    print("=" * 42)
    
    # Datos del desafío
    encrypted_hex = "73626960647f6b206821204f21254f7d694f7624662065204f7c65"
    known_start = "crypto{"
    
    print(f"📋 Datos:")
    print(f"   Encrypted: {encrypted_hex}")
    print(f"   Known text: '{known_start}'")
    print()
    
    # Convertir a bytes
    encrypted = bytes.fromhex(encrypted_hex)
    known_bytes = known_start.encode('utf-8')
    
    print(f"🔍 Análisis:")
    print(f"   Encrypted length: {len(encrypted)} bytes")
    print(f"   Known text length: {len(known_bytes)} bytes")
    print()
    
    # Extraer clave parcial usando known plaintext
    print("🔧 Extrayendo clave...")
    key_partial = bytes(e ^ k for e, k in zip(encrypted[:len(known_bytes)], known_bytes))
    
    print(f"   Key partial (hex): {key_partial.hex()}")
    print(f"   Key partial (ASCII): {repr(key_partial.decode('utf-8', errors='ignore'))}")
    print()
    
    # Observar el patrón - parece que la clave es 0x10 repetido
    key_byte = 0x10
    print(f"🧪 Probando clave simple: 0x{key_byte:02x}")
    
    # Crear clave completa
    full_key = bytes([key_byte] * len(encrypted))
    
    # Descifrar
    decrypted = bytes(e ^ k for e, k in zip(encrypted, full_key))
    
    try:
        flag = decrypted.decode('utf-8')
        print(f"✅ Resultado: '{flag}'")
        
        if flag.startswith('crypto{') and flag.endswith('}'):
            print("✅ ¡FLAG VÁLIDA!")
            
            # Guardar resultado
            with open("challenges/solved/cryptohack_xor_fixed.txt", 'w') as f:
                f.write(f"Challenge: CryptoHack Lemur XOR\n")
                f.write(f"Method: Simple XOR with key 0x{key_byte:02x}\n")
                f.write(f"FLAG: {flag}\n")
            
            return flag
        else:
            print("⚠️  No termina correctamente, probando otras claves...")
            return try_other_patterns(encrypted)
            
    except UnicodeDecodeError:
        print("❌ Error de decodificación")
        return try_other_patterns(encrypted)

def try_other_patterns(encrypted):
    """Prueba otros patrones de clave"""
    print("\n🔄 Probando otros patrones...")
    
    # Patrones comunes
    patterns = [
        # Single byte keys
        *[bytes([i] * len(encrypted)) for i in range(1, 256)],
        # Patrón "lemur" (por el nombre del challenge)
        b'lemur' * (len(encrypted) // 5 + 1),
        # Otros patrones comunes
        b'key' * (len(encrypted) // 3 + 1),
        b'xor' * (len(encrypted) // 3 + 1),
    ]
    
    for i, pattern in enumerate(patterns[:20]):  # Limitar para no ser muy lento
        key = pattern[:len(encrypted)]
        decrypted = bytes(e ^ k for e, k in zip(encrypted, key))
        
        try:
            flag = decrypted.decode('utf-8')
            if flag.startswith('crypto{') and flag.endswith('}'):
                print(f"✅ ¡FLAG ENCONTRADA con patrón {i}!")
                print(f"🏆 FLAG: {flag}")
                
                with open("challenges/solved/cryptohack_xor_fixed.txt", 'w') as f:
                    f.write(f"Challenge: CryptoHack Lemur XOR\n")
                    f.write(f"Method: Pattern matching #{i}\n")
                    f.write(f"Key pattern: {key[:10].hex()}...\n")
                    f.write(f"FLAG: {flag}\n")
                
                return flag
                
        except UnicodeDecodeError:
            continue
    
    print("❌ No se encontró la flag con patrones simples")
    return None

def main():
    """Función principal"""
    print("🚀 Iniciando resolución de desafío XOR...")
    
    flag = solve_xor_challenge()
    
    if flag:
        print(f"\n🎉 ¡DESAFÍO RESUELTO!")
        print(f"🏆 FLAG: {flag}")
        print(f"✅ Guardado en challenges/solved/")
    else:
        print(f"\n❌ No se pudo resolver automáticamente")
        print(f"💡 Intenta analizar manualmente los patrones")

if __name__ == "__main__":
    main()