#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resolver XOR Challenge - Sin dependencia de Gemini API
====================================================
"""

def solve_xor_challenge():
    """Resuelve el desafío XOR usando fuerza bruta"""
    
    # Datos del desafío
    hex_data = "1c0e1b0a1f1b0e1a1f1b0e1a1f1b0e1a"
    
    # Convertir hex a bytes
    encrypted_bytes = bytes.fromhex(hex_data)
    print(f"Datos cifrados: {encrypted_bytes}")
    print(f"Longitud: {len(encrypted_bytes)} bytes")
    
    # Probar todas las claves de un byte (caracteres imprimibles ASCII)
    for key in range(32, 127):  # ASCII imprimibles
        try:
            # XOR con la clave
            decrypted = bytes(b ^ key for b in encrypted_bytes)
            decrypted_text = decrypted.decode('utf-8', errors='ignore')
            
            # Verificar si el resultado tiene sentido
            if decrypted_text.isprintable() and len(decrypted_text.strip()) > 0:
                print(f"Clave {key} ({chr(key)}): {decrypted_text}")
                
                # Verificar si el resultado tiene sentido y buscar patrones
                if all(c.isprintable() for c in decrypted_text) and decrypted_text.strip():
                    # Buscar si contiene palabras comunes o patrones de flag
                    if (any(word in decrypted_text.lower() for word in ['flag', 'crypto', 'ctf', 'the', 'this', 'key']) or
                        '{' in decrypted_text or '}' in decrypted_text):
                        print(f"🎉 ¡Posible solución encontrada!")
                        print(f"Clave: {key} ({chr(key)})")
                        print(f"Texto: {decrypted_text}")
                    
        except:
            continue

if __name__ == "__main__":
    solve_xor_challenge()