#!/usr/bin/env python3
"""
Solucionador XOR Específico - Clave variable detectada
=====================================================
"""

def solve_variable_key_xor():
    """Resuelve el XOR con clave variable usando conocimiento parcial"""
    print("🎯 SOLUCIONADOR XOR VARIABLE - CRYPTOHACK LEMUR")
    print("=" * 48)
    
    # Datos del desafío  
    encrypted_hex = "73626960647f6b206821204f21254f7d694f7624662065204f7c65"
    encrypted = bytes.fromhex(encrypted_hex)
    
    print(f"📋 Datos:")
    print(f"   Encrypted: {encrypted_hex}")
    print(f"   Length: {len(encrypted)} bytes")
    print()
    
    # Conocimiento: crypto{ al inicio, } al final
    known_start = "crypto{"
    known_end = "}"
    
    # Análisis de clave basado en posiciones conocidas
    print("🔍 Extrayendo clave en posiciones conocidas:")
    
    # Extraer bytes de clave donde conocemos el plaintext
    key_bytes = [None] * len(encrypted)
    
    # Inicio: crypto{
    start_bytes = known_start.encode('utf-8')
    for i in range(len(start_bytes)):
        key_bytes[i] = encrypted[i] ^ start_bytes[i]
        print(f"   Pos {i:2d}: enc=0x{encrypted[i]:02x} ^ plain=0x{start_bytes[i]:02x} = key=0x{key_bytes[i]:02x}")
    
    # Final: }
    end_byte = ord(known_end)
    key_bytes[-1] = encrypted[-1] ^ end_byte
    print(f"   Pos {len(encrypted)-1:2d}: enc=0x{encrypted[-1]:02x} ^ plain=0x{end_byte:02x} = key=0x{key_bytes[-1]:02x}")
    print()
    
    # Detectar patrón en la clave
    print("🔍 Analizando patrón de clave:")
    known_key_positions = [i for i, k in enumerate(key_bytes) if k is not None]
    known_key_values = [key_bytes[i] for i in known_key_positions]
    
    print(f"   Posiciones conocidas: {known_key_positions}")
    print(f"   Valores de clave: {[hex(k) for k in known_key_values]}")
    
    # Buscar patrón
    # Patrón 1: Incremento constante
    if len(known_key_values) >= 2:
        diffs = [known_key_values[i+1] - known_key_values[i] for i in range(len(known_key_values)-1)]
        print(f"   Diferencias: {diffs}")
        
        # Si la diferencia es constante o hay un patrón
        if len(set(diffs)) == 1:
            # Incremento constante
            diff = diffs[0]
            base_key = known_key_values[0]
            
            print(f"   ✅ Patrón detectado: incremento de {diff}")
            print(f"   Base: 0x{base_key:02x}")
            
            # Reconstruir clave completa
            full_key = []
            for i in range(len(encrypted)):
                key_val = (base_key + i * diff) & 0xFF  # Mantener en rango byte
                full_key.append(key_val)
            
            # Descifrar
            decrypted = bytes(e ^ k for e, k in zip(encrypted, full_key))
            
            try:
                flag = decrypted.decode('utf-8')
                print(f"   🏆 FLAG: '{flag}'")
                
                if flag.startswith('crypto{') and flag.endswith('}'):
                    print("   ✅ ¡FLAG VÁLIDA!")
                    save_result(flag, "incremental", full_key[:10])
                    return flag
                    
            except UnicodeDecodeError:
                print("   ❌ Error de decodificación")
    
    # Patrón 2: Intentar patrones comunes
    print("\n🔄 Probando patrones alternativos...")
    
    patterns_to_try = [
        # Patrón basado en posición
        lambda i: (0x10 + i) & 0xFF,
        lambda i: (0x10 + i * 2) & 0xFF,
        lambda i: (0x10 + i * 8) & 0xFF,
        lambda i: 0x10 if i < 20 else 0x18,
        # Patrón alternante
        lambda i: 0x10 if i % 2 == 0 else 0x18,
        # Patrón cíclico
        lambda i: [0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18][i % 9],
    ]
    
    for p_idx, pattern_func in enumerate(patterns_to_try):
        print(f"   Patrón {p_idx + 1}...")
        
        try:
            full_key = [pattern_func(i) for i in range(len(encrypted))]
            decrypted = bytes(e ^ k for e, k in zip(encrypted, full_key))
            flag = decrypted.decode('utf-8')
            
            if flag.startswith('crypto{') and flag.endswith('}'):
                print(f"   ✅ ¡PATRÓN {p_idx + 1} EXITOSO!")
                print(f"   🏆 FLAG: '{flag}'")
                save_result(flag, f"pattern_{p_idx + 1}", full_key[:10])
                return flag
                
        except:
            continue
    
    # Patrón 3: Fuerza bruta inteligente para posiciones faltantes
    print("\n🔥 Fuerza bruta inteligente...")
    return brute_force_missing_positions(encrypted, key_bytes)

def brute_force_missing_positions(encrypted, partial_key):
    """Fuerza bruta para encontrar bytes de clave faltantes"""
    
    # Posiciones que necesitan fuerza bruta
    missing_positions = [i for i, k in enumerate(partial_key) if k is None]
    
    if len(missing_positions) > 10:  # Limitar para no hacer fuerza bruta excesiva
        print(f"   Demasiadas posiciones faltantes ({len(missing_positions)})")
        return None
    
    print(f"   Probando {len(missing_positions)} posiciones faltantes...")
    
    # Generar todas las combinaciones posibles para posiciones faltantes
    from itertools import product
    
    # Limitar a valores razonables (caracteres imprimibles y algunos de control)
    possible_values = list(range(256))
    
    # Para cada combinación de valores en posiciones faltantes
    for combination in product(possible_values, repeat=min(len(missing_positions), 3)):  # Limitar a 3 para ser práctico
        # Crear clave de prueba
        test_key = partial_key[:]
        for i, pos in enumerate(missing_positions[:len(combination)]):
            test_key[pos] = combination[i]
        
        # Rellenar posiciones restantes con valores por defecto
        for i, k in enumerate(test_key):
            if k is None:
                test_key[i] = 0x10  # Valor por defecto
        
        # Descifrar
        try:
            decrypted = bytes(e ^ k for e, k in zip(encrypted, test_key))
            flag = decrypted.decode('utf-8')
            
            # Verificar si es una flag válida
            if flag.startswith('crypto{') and flag.endswith('}') and len(flag) > 10:
                print(f"   ✅ ¡FLAG ENCONTRADA POR FUERZA BRUTA!")
                print(f"   🏆 FLAG: '{flag}'")
                save_result(flag, "brute_force", test_key[:10])
                return flag
                
        except:
            continue
    
    return None

def save_result(flag, method, key_sample):
    """Guarda el resultado"""
    with open("challenges/solved/cryptohack_xor_lemur.txt", 'w') as f:
        f.write(f"Challenge: CryptoHack Lemur XOR - SOLVED\n")
        f.write(f"Method: {method}\n")
        f.write(f"Key sample: {[hex(k) for k in key_sample]}\n")
        f.write(f"FLAG: {flag}\n")
        f.write(f"Status: COMPLETE\n")
    
    print(f"💾 Resultado guardado en challenges/solved/cryptohack_xor_lemur.txt")

def main():
    """Función principal"""
    print("🚀 INICIANDO RESOLUCIÓN XOR VARIABLE\n")
    
    result = solve_variable_key_xor()
    
    if result:
        print(f"\n" + "🎉" * 20)
        print(f"DESAFÍO CRYPTOHACK LEMUR XOR RESUELTO")
        print(f"FLAG: {result}")
        print(f"🎉" * 20)
    else:
        print(f"\n❌ No se pudo resolver el desafío")
        print(f"💡 El desafío puede requerir análisis manual adicional")

if __name__ == "__main__":
    main()