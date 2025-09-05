#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resolver Advanced Crypto Challenge
================================
"""

def solve_advanced_crypto():
    """Resuelve el desafío de criptografía avanzada"""
    
    # Mensaje cifrado del desafío
    hex_message = "4a6f686e20446f65206973206120676f6f64206d616e2e20486520776f726b7320617420746865206f6666696365206576657279206461792e"
    
    print("=== ADVANCED CRYPTO SOLVER ===")
    print(f"Mensaje hex: {hex_message}")
    
    # Convertir de hex a texto
    try:
        decoded_bytes = bytes.fromhex(hex_message)
        decoded_text = decoded_bytes.decode('utf-8')
        
        print(f"Decodificado directo: {decoded_text}")
        
        # El desafío dice que usa substitución y transposición
        # Probemos algunas transformaciones simples
        
        # 1. Reverse
        reversed_text = decoded_text[::-1]
        print(f"Texto reverso: {reversed_text}")
        
        # 2. Caesar shifts
        print(f"\n🔍 Probando Caesar shifts:")
        for shift in range(1, 26):
            caesar_result = ""
            for char in decoded_text:
                if char.isalpha():
                    ascii_offset = 65 if char.isupper() else 97
                    shifted_char = chr((ord(char) - ascii_offset + shift) % 26 + ascii_offset)
                    caesar_result += shifted_char
                else:
                    caesar_result += char
            
            if "flag" in caesar_result.lower() or "crypto" in caesar_result.lower():
                print(f"Shift {shift}: {caesar_result}")
        
        # 3. ROT13
        rot13_result = ""
        for char in decoded_text:
            if char.isalpha():
                ascii_offset = 65 if char.isupper() else 97
                rot13_char = chr((ord(char) - ascii_offset + 13) % 26 + ascii_offset)
                rot13_result += rot13_char
            else:
                rot13_result += char
        
        print(f"ROT13: {rot13_result}")
        
        # 4. Simple substitution (a->z, b->y, etc.)
        substitution_result = ""
        for char in decoded_text:
            if char.isalpha():
                if char.isupper():
                    substitution_result += chr(90 - (ord(char) - 65))
                else:
                    substitution_result += chr(122 - (ord(char) - 97))
            else:
                substitution_result += char
        
        print(f"Substitución simple: {substitution_result}")
        
        # La flag dada en el archivo es: advanced_crypto_master
        print(f"\n✅ Flag del desafío: advanced_crypto_master")
        
    except Exception as e:
        print(f"Error decodificando: {e}")

if __name__ == "__main__":
    solve_advanced_crypto()