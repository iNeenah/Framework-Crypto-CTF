#!/usr/bin/env python3
"""
Extractor Eficiente de Flag - chall.py
=====================================
Se enfoca en los bloques más probables de contener la flag
"""

import socket
import time
import re

class EfficientFlagExtractor:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        
    def connect_and_get_prophecy(self):
        """Conecta y obtiene la prophecy"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)
            
            print(f"🔗 Conectando a {self.host}:{self.port}...")
            self.socket.connect((self.host, self.port))
            
            response = self.socket.recv(4096)
            text = response.decode('utf-8', errors='ignore')
            
            match = re.search(r'Prophecy \(HEX\): ([a-fA-F0-9]+)', text)
            if match:
                return bytes.fromhex(match.group(1))
            return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def oracle(self, hex_data):
        """Oracle query optimizado"""
        try:
            self.socket.sendall((hex_data + "\n").encode())
            time.sleep(0.02)
            response = self.socket.recv(1024).decode('utf-8', errors='ignore')
            return "well-formed" in response
        except:
            return False
    
    def decrypt_block_fast(self, c1, c2):
        """Descifra bloque enfocado en caracteres ASCII"""
        print("🔓 Descifrando bloque...")
        
        plaintext = [0] * 16
        
        # Descifrar de derecha a izquierda
        for pos in range(15, -1, -1):
            padding = 16 - pos
            print(f"  Byte {16-pos}/16...", end="", flush=True)
            
            found = False
            
            # Optimización: probar primeros caracteres ASCII comunes
            common_chars = list(range(32, 127)) + list(range(0, 32)) + list(range(127, 256))
            
            for test_byte in common_chars:
                modified_c1 = bytearray(c1)
                
                # Configurar bytes conocidos
                for i in range(pos + 1, 16):
                    modified_c1[i] = c1[i] ^ plaintext[i] ^ padding
                
                # Valor a probar
                modified_c1[pos] = test_byte ^ c1[pos] ^ padding
                
                if self.oracle(bytes(modified_c1 + c2).hex()):
                    plaintext[pos] = test_byte
                    char = chr(test_byte) if 32 <= test_byte <= 126 else '.'
                    print(f" ✅{test_byte:02x}('{char}')")
                    found = True
                    break
            
            if not found:
                print(" ❌")
                plaintext[pos] = 0
        
        return bytes(plaintext)
    
    def extract_flag_smart(self, ciphertext):
        """Extrae flag de manera inteligente"""
        print(f"\n🎯 EXTRACCIÓN INTELIGENTE DE FLAG")
        
        blocks = [ciphertext[i:i+16] for i in range(0, len(ciphertext), 16)]
        print(f"📊 Bloques: {len(blocks)}")
        
        if len(blocks) < 2:
            return None
        
        # Estrategia: empezar por el primer bloque (más probable que contenga el inicio de la flag)
        results = []
        
        # Descifrar primer bloque
        iv = blocks[0]
        first_block = blocks[1]
        
        print(f"\n🔍 Descifrando primer bloque...")
        plaintext1 = self.decrypt_block_fast(iv, first_block)
        text1 = plaintext1.decode('utf-8', errors='ignore')
        results.append(text1)
        print(f"✅ Bloque 1: '{text1}'")
        
        # Si encontramos el inicio de una flag, continuar
        if any(pattern in text1.lower() for pattern in ['n3xt', 'flag', '{']):
            print("🎯 Posible flag detectada, continuando...")
            
            # Descifrar segundo bloque si es necesario
            if len(blocks) > 2:
                second_block = blocks[2]
                print(f"\n🔍 Descifrando segundo bloque...")
                plaintext2 = self.decrypt_block_fast(first_block, second_block)
                text2 = plaintext2.decode('utf-8', errors='ignore')
                results.append(text2)
                print(f"✅ Bloque 2: '{text2}'")
        
        # Construir resultado
        full_text = ''.join(results)
        
        # Buscar flag en el texto
        flag_patterns = [
            r'n3xt\{[^}]+\}',
            r'flag\{[^}]+\}',
            r'ctf\{[^}]+\}',
            r'\{[^}]{8,}\}'
        ]
        
        for pattern in flag_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        # Si no encontramos patrón, devolver texto limpio
        clean = ''.join(c for c in full_text if 32 <= ord(c) <= 126).strip()
        return clean if clean else full_text
    
    def test_flag(self, flag):
        """Prueba la flag con el servidor"""
        try:
            print(f"📤 Probando flag: {flag}")
            self.socket.sendall(f"submit {flag}\n".encode())
            time.sleep(1)
            response = self.socket.recv(2048).decode('utf-8', errors='ignore')
            
            if "INCREDIBLE" in response:
                return True
            else:
                print(f"❌ Respuesta: {response[:100]}...")
                return False
        except:
            return False
    
    def close(self):
        if self.socket:
            self.socket.close()

def get_flag_now():
    """Función principal para obtener la flag"""
    print("🎯 OBTENIENDO FLAG DE chall.py")
    print("=" * 35)
    
    extractor = EfficientFlagExtractor("185.207.251.177", 1600)
    
    try:
        # Conectar
        prophecy = extractor.connect_and_get_prophecy()
        if not prophecy:
            print("❌ No se pudo conectar")
            return None
        
        print(f"📜 Prophecy: {len(prophecy)} bytes")
        
        # Extraer flag
        flag = extractor.extract_flag_smart(prophecy)
        
        if flag:
            print(f"\n🎉 FLAG EXTRAÍDA: {flag}")
            
            # Probar con servidor
            if extractor.test_flag(flag):
                print("✅ ¡FLAG VERIFICADA!")
                
                # Guardar
                with open("challenges/solved/chall_final_flag.txt", 'w') as f:
                    f.write(f"FLAG: {flag}\n")
                    f.write(f"Challenge: chall.py\n")
                    f.write(f"Method: Efficient Padding Oracle\n")
                    f.write(f"Status: VERIFIED\n")
                
                return flag
            else:
                print("⚠️  Flag no verificada, pero extraída")
                return flag
        else:
            print("❌ No se pudo extraer flag")
            return None
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        extractor.close()

if __name__ == "__main__":
    final_flag = get_flag_now()
    
    if final_flag:
        print(f"\n🏆 FLAG FINAL: {final_flag}")
    else:
        print("❌ No se obtuvo la flag")