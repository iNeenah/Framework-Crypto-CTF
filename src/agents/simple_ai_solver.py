#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple AI CTF Solver
====================
Version simplificada del agente autonomo sin caracteres especiales
"""

import os
import re
import base64
import socket
import time
import tempfile
import subprocess
from pathlib import Path

class SimpleAICTFSolver:
    def __init__(self):
        self.base_dir = Path("c:/Users/Nenaah/Desktop/Programacion/GIT/CRYPTO")
        
    def solve_challenge(self, challenge_text: str) -> str:
        """Resuelve un desafio automaticamente"""
        
        print("🔍 Analyzing challenge...")
        
        # 1. Buscar flags directamente en el texto
        flag_patterns = [
            r'crypto\{[^}]+\}',
            r'flag\{[^}]+\}', 
            r'CTF\{[^}]+\}'
        ]
        
        for pattern in flag_patterns:
            match = re.search(pattern, challenge_text, re.IGNORECASE)
            if match:
                print("✅ Flag found directly in text!")
                return match.group(0)
        
        # 2. Decodificacion Base64
        base64_pattern = r'[A-Za-z0-9+/]{20,}={0,2}'
        base64_matches = re.findall(base64_pattern, challenge_text)
        
        for b64_text in base64_matches:
            try:
                decoded = base64.b64decode(b64_text).decode('utf-8')
                print(f"🔓 Decoded Base64: {decoded}")
                
                # Buscar flag en texto decodificado
                for pattern in flag_patterns:
                    match = re.search(pattern, decoded, re.IGNORECASE)
                    if match:
                        print("✅ Flag found in Base64 decoded text!")
                        return match.group(0)
                        
            except Exception:
                continue
        
        # 3. Analisis XOR simple
        if 'xor' in challenge_text.lower():
            return self.try_xor_solving(challenge_text)
        
        # 4. Conexion de red
        nc_match = re.search(r'nc\s+([\w\.-]+)\s+(\d+)', challenge_text)
        if nc_match:
            host, port = nc_match.groups()
            return self.try_network_connection(host, int(port))
        
        print("❌ No automatic solution found")
        return None
    
    def try_xor_solving(self, challenge_text: str) -> str:
        """Intenta resolver XOR simple"""
        
        print("🔧 Trying XOR solving...")
        
        # Buscar datos hex
        hex_pattern = r'[0-9a-fA-F]{10,}'
        hex_matches = re.findall(hex_pattern, challenge_text)
        
        for hex_data in hex_matches:
            try:
                encrypted_bytes = bytes.fromhex(hex_data)
                
                # Probar single-byte XOR
                for key_byte in range(256):
                    decrypted = bytes(b ^ key_byte for b in encrypted_bytes)
                    
                    try:
                        text = decrypted.decode('utf-8')
                        if any(flag_word in text.lower() for flag_word in ['crypto', 'flag', 'ctf']):
                            if '{' in text and '}' in text:
                                print(f"✅ XOR solution found with key {key_byte}")
                                return text
                    except:
                        continue
                        
            except Exception:
                continue
        
        return None
    
    def try_network_connection(self, host: str, port: int) -> str:
        """Intenta conexion de red simple"""
        
        print(f"🌐 Trying network connection to {host}:{port}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((host, port))
            
            # Leer respuesta inicial
            response = sock.recv(4096).decode('utf-8', errors='ignore')
            print(f"📨 Server response: {response[:200]}...")
            
            # Buscar flag en respuesta
            flag_patterns = [
                r'crypto\{[^}]+\}',
                r'flag\{[^}]+\}',
                r'CTF\{[^}]+\}'
            ]
            
            for pattern in flag_patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    print("✅ Flag found in server response!")
                    sock.close()
                    return match.group(0)
            
            # Intentar interacciones basicas
            common_inputs = ["1", "flag", "help", "admin", ""]
            
            for input_cmd in common_inputs:
                try:
                    sock.send((input_cmd + "\n").encode())
                    time.sleep(1)
                    response = sock.recv(4096).decode('utf-8', errors='ignore')
                    
                    for pattern in flag_patterns:
                        match = re.search(pattern, response, re.IGNORECASE)
                        if match:
                            print(f"✅ Flag found with input '{input_cmd}'!")
                            sock.close()
                            return match.group(0)
                            
                except Exception:
                    break
            
            sock.close()
            
        except Exception as e:
            print(f"❌ Network error: {e}")
        
        return None
    
    def solve_from_file(self, file_path: str) -> str:
        """Resuelve desde archivo"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                challenge_text = f.read()
            
            print(f"📁 Solving challenge from: {file_path}")
            return self.solve_challenge(challenge_text)
            
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return None

def main():
    """Funcion principal simple"""
    
    print("🤖 SIMPLE AI CTF SOLVER")
    print("=" * 25)
    
    solver = SimpleAICTFSolver()
    
    # Prueba con el archivo de ejemplo
    test_file = "test_challenge_simple.txt"
    
    if os.path.exists(test_file):
        print(f"🧪 Testing with: {test_file}")
        flag = solver.solve_from_file(test_file)
        
        if flag:
            print(f"\n🏆 SUCCESS! Flag: {flag}")
        else:
            print(f"\n❌ Could not solve challenge")
    else:
        print(f"⚠️  Test file not found: {test_file}")
    
    # Ejemplo interactivo
    print(f"\n💬 Interactive mode:")
    print("Enter challenge text (press Enter to finish):")
    
    challenge_lines = []
    try:
        while True:
            line = input()
            if line.strip() == "":
                break
            challenge_lines.append(line)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return
    
    if challenge_lines:
        challenge_text = '\n'.join(challenge_lines)
        flag = solver.solve_challenge(challenge_text)
        
        if flag:
            print(f"\n🏆 SUCCESS! Flag: {flag}")
        else:
            print(f"\n❌ Could not solve challenge")

if __name__ == "__main__":
    main()