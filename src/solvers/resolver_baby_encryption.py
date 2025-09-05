#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resolver Baby Encryption Challenge
=================================
Cifrado afín con parámetros conocidos
"""

def resolver_baby_encryption():
    """Resuelve el desafío Baby Encryption"""
    
    print("🍼 === BABY ENCRYPTION CHALLENGE SOLVER ===")
    
    # Datos del desafío
    ciphertext_hex = "6e0a9372ec49a3f6930ed8723f9df6f6720ed8d89dc4937222ec7214d89d1e0e352ce0aa6ec82bf622227bb70e7fb7352249b7d893c493d8539dec8fb7935d490e7f9d22ec89b7a322ec8fd80e7f8921"
    a = 123  # multiplicador
    b = 18   # desplazamiento
    m = 256  # módulo
    
    print(f"📊 Parámetros del cifrado afín:")
    print(f"   • Multiplicador (a): {a}")
    print(f"   • Desplazamiento (b): {b}")
    print(f"   • Módulo (m): {m}")
    print(f"   • Ciphertext: {ciphertext_hex[:50]}...")
    
    # Convertir hex a bytes
    try:
        ciphertext_bytes = bytes.fromhex(ciphertext_hex)
        print(f"✅ Ciphertext convertido: {len(ciphertext_bytes)} bytes")
    except ValueError as e:
        print(f"❌ Error convirtiendo hex: {e}")
        return
    
    # Calcular inverso multiplicativo de 123 módulo 256
    def extended_gcd(a, b):
        if a == 0:
            return b, 0, 1
        gcd, x1, y1 = extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return gcd, x, y
    
    def mod_inverse(a, m):
        gcd, x, _ = extended_gcd(a, m)
        if gcd != 1:
            return None  # No existe inverso
        return (x % m + m) % m
    
    # Encontrar inverso de 123 mod 256
    inv_a = mod_inverse(a, m)
    
    if inv_a is None:
        print(f"❌ No existe inverso multiplicativo de {a} módulo {m}")
        return
    
    print(f"🔑 Inverso multiplicativo de {a} mod {m}: {inv_a}")
    
    # Verificar que el inverso es correcto
    verification = (a * inv_a) % m
    print(f"✅ Verificación: {a} * {inv_a} mod {m} = {verification}")
    
    if verification != 1:
        print(f"❌ Error: El inverso no es correcto")
        return
    
    # Descifrar usando la función inversa: pt = (inv_a * (ct - b)) % m
    print(f"\n🔓 Descifrando mensaje...")
    
    plaintext_bytes = []
    for ct_byte in ciphertext_bytes:
        # Aplicar función inversa del cifrado afín
        pt_byte = (inv_a * (ct_byte - b)) % m
        plaintext_bytes.append(pt_byte)
    
    plaintext = bytes(plaintext_bytes)
    
    # Intentar decodificar como texto
    try:
        decoded_text = plaintext.decode('utf-8', errors='ignore')
        print(f"📝 Texto descifrado: {decoded_text}")
        
        # Buscar flag
        import re
        flag_match = re.search(r'HTB\{[^}]+\}|htb\{[^}]+\}|flag\{[^}]+\}|crypto\{[^}]+\}', decoded_text, re.IGNORECASE)
        
        if flag_match:
            print(f"🎉 ¡FLAG ENCONTRADA!")
            print(f"🏁 FLAG: {flag_match.group(0)}")
        else:
            print(f"⚠️  No se encontró flag en formato estándar")
            print(f"   Texto completo: {decoded_text}")
            
            # Buscar patrones que puedan ser flags
            possible_flags = re.findall(r'\b[A-Za-z0-9_]{10,}\b', decoded_text)
            if possible_flags:
                print(f"   Posibles flags: {possible_flags}")
    
    except UnicodeDecodeError:
        print(f"❌ Error decodificando como UTF-8")
        print(f"   Bytes descifrados: {plaintext[:50]}...")
        
        # Intentar otros encodings
        for encoding in ['latin-1', 'ascii', 'cp1252']:
            try:
                decoded_text = plaintext.decode(encoding, errors='ignore')
                print(f"   {encoding}: {decoded_text[:100]}...")
                
                # Buscar flag en este encoding
                flag_match = re.search(r'HTB\{[^}]+\}|htb\{[^}]+\}', decoded_text, re.IGNORECASE)
                if flag_match:
                    print(f"🎉 ¡FLAG ENCONTRADA en {encoding}!")
                    print(f"🏁 FLAG: {flag_match.group(0)}")
                    break
            except:
                continue
    
    # Análisis de bytes
    print(f"\n📊 Análisis de bytes descifrados:")
    print(f"   • Longitud: {len(plaintext)} bytes")
    print(f"   • Primeros 20 bytes: {plaintext[:20]}")
    print(f"   • Últimos 20 bytes: {plaintext[-20:]}")
    
    # Buscar patrones comunes de flags en bytes
    hex_representation = plaintext.hex()
    print(f"   • Representación hex: {hex_representation[:50]}...")
    
    return plaintext

if __name__ == "__main__":
    resultado = resolver_baby_encryption()
    print(f"\n✅ Resolución completada")