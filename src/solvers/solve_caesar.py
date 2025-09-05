#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resolver Caesar Cipher
=====================
"""

def caesar_decrypt(text, shift):
    """Desencripta texto con cifrado César"""
    result = ""
    for char in text:
        if char.isalpha():
            ascii_offset = 65 if char.isupper() else 97
            decrypted_char = chr((ord(char) - ascii_offset - shift) % 26 + ascii_offset)
            result += decrypted_char
        else:
            result += char
    return result

def solve_caesar():
    """Resuelve el desafío Caesar"""
    
    # Texto cifrado del desafío
    encrypted_text = "WKLV LV D VLPSOH FDHVDU FLSKHU ZLWK VKLIW 3"
    encrypted_flag = "FDHVDU_HDVB_FKDOOHQJH"
    
    print("=== CAESAR CIPHER SOLVER ===")
    print(f"Texto cifrado: {encrypted_text}")
    print(f"Flag cifrada: {encrypted_flag}")
    
    # El hint dice shift 3, así que probamos shift 3
    print(f"\n🔍 Probando con shift 3:")
    
    decrypted_text = caesar_decrypt(encrypted_text, 3)
    decrypted_flag = caesar_decrypt(encrypted_flag, 3)
    
    print(f"Texto descifrado: {decrypted_text}")
    print(f"Flag descifrada: {decrypted_flag}")
    
    # También probemos otros shifts por si acaso
    print(f"\n🔍 Probando otros shifts:")
    for shift in range(1, 26):
        test_flag = caesar_decrypt(encrypted_flag, shift)
        if "flag" in test_flag.lower() or "caesar" in test_flag.lower():
            print(f"Shift {shift}: {test_flag}")

if __name__ == "__main__":
    solve_caesar()