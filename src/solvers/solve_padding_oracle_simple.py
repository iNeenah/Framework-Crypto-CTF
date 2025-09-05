#!/usr/bin/env python3
"""
Solucionador Simple y Robusto para Padding Oracle Attack
========================================================
"""

import socket
import time
import re

class PaddingOracleAttacker:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        
    def connect_and_get_prophecy(self):
        """Conecta y obtiene la prophecy"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(15)
            
            print(f"Conectando a {self.host}:{self.port}...")
            self.socket.connect((self.host, self.port))
            
            # Leer respuesta inicial
            response = b""
            time.sleep(2)  # Dar tiempo al servidor
            
            while True:
                try:
                    chunk = self.socket.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                    
                    text = response.decode('utf-8', errors='ignore')
                    if "Prophecy (HEX):" in text and "> " in text:
                        break
                        
                except socket.timeout:
                    break
            
            text = response.decode('utf-8', errors='ignore')
            print("Respuesta del servidor:")
            print(text)
            
            # Extraer prophecy
            match = re.search(r'Prophecy \(HEX\): ([a-fA-F0-9]+)', text)
            if match:
                hex_data = match.group(1)
                prophecy = bytes.fromhex(hex_data)
                print(f"Prophecy extraida: {hex_data}")
                return prophecy
            else:
                print("No se pudo extraer prophecy")
                return None
                
        except Exception as e:
            print(f"Error conectando: {e}")
            return None
    
    def check_padding(self, ciphertext_hex):
        """Verifica padding con el oracle"""
        try:
            # Enviar ciphertext
            self.socket.sendall((ciphertext_hex + "\n").encode())
            
            # Leer respuesta
            response = b""
            time.sleep(0.2)
            
            while True:
                try:
                    chunk = self.socket.recv(1024)
                    if not chunk:
                        break
                    response += chunk
                    
                    text = response.decode('utf-8', errors='ignore')
                    if "well-formed" in text or "Valid Padding" in text:
                        return True
                    elif "chaotic" in text or "Invalid Padding" in text:
                        return False
                    elif "Provide new ciphertext" in text:
                        break
                        
                except socket.timeout:
                    break
            
            return False
            
        except Exception as e:
            print(f"Error en check_padding: {e}")
            return False
    
    def simple_attack(self, ciphertext):
        """Ataque simplificado - solo para demostrar concepto"""
        print(f"Iniciando ataque simplificado...")
        print(f"Ciphertext: {ciphertext.hex()}")
        print(f"Longitud: {len(ciphertext)} bytes")
        
        # Solo vamos a intentar descifrar el ultimo bloque para demostrar
        if len(ciphertext) < 32:
            print("Ciphertext muy corto")
            return None
        
        # Tomar los dos ultimos bloques
        block_size = 16
        c1 = ciphertext[-32:-16]  # Penultimo bloque 
        c2 = ciphertext[-16:]     # Ultimo bloque
        
        print(f"C1 (penultimo): {c1.hex()}")
        print(f"C2 (ultimo): {c2.hex()}")
        
        # Intentar descifrar el ultimo byte del ultimo bloque
        print("Intentando descifrar ultimo byte...")
        
        for guess in range(256):
            # Modificar el ultimo byte de C1
            modified_c1 = bytearray(c1)
            modified_c1[-1] = guess
            
            # Crear ciphertext de prueba
            test_cipher = bytes(modified_c1) + c2
            test_hex = test_cipher.hex()
            
            if self.check_padding(test_hex):
                print(f"Posible byte encontrado: {guess:02x}")
                # El byte original seria: guess XOR c1[-1] XOR 0x01
                original_byte = guess ^ c1[-1] ^ 0x01
                print(f"Byte descifrado: {original_byte:02x} ('{chr(original_byte) if 32 <= original_byte <= 126 else '.'}')")
                
                # Intentar descifrar mas bytes...
                return self.decrypt_more_bytes(ciphertext, c1, c2, original_byte)
        
        print("No se pudo descifrar")
        return None
    
    def decrypt_more_bytes(self, full_cipher, c1, c2, last_byte):
        """Intenta descifrar mas bytes del bloque"""
        print("Intentando descifrar mas bytes...")
        
        decrypted = [0] * 16
        decrypted[15] = last_byte
        
        # Intentar descifrar byte 14
        for padding_len in [2, 3, 4]:  # Probar diferentes padding lengths
            for guess in range(256):
                modified_c1 = bytearray(c1)
                
                # Configurar bytes conocidos
                for i in range(16 - padding_len, 16):
                    if i == 15:
                        modified_c1[i] = c1[i] ^ decrypted[i] ^ padding_len
                    elif i == 14 and padding_len >= 2:
                        modified_c1[i] = guess
                
                test_cipher = bytes(modified_c1) + c2
                test_hex = test_cipher.hex()
                
                if self.check_padding(test_hex) and padding_len == 2:
                    byte_14 = guess ^ c1[14] ^ 2
                    decrypted[14] = byte_14
                    print(f"Byte 14: {byte_14:02x} ('{chr(byte_14) if 32 <= byte_14 <= 126 else '.'}')")
                    break
        
        # Mostrar lo que tenemos
        result = bytes(decrypted)
        readable = "".join(chr(b) if 32 <= b <= 126 else '.' for b in result)
        print(f"Descifrado parcial: {result.hex()}")
        print(f"Como texto: {readable}")
        
        return result

    def close(self):
        if self.socket:
            self.socket.close()

def main():
    print("PADDING ORACLE ATTACK - VERSION SIMPLE")
    print("=" * 40)
    print("Target: 185.207.251.177:1600")
    print()
    
    attacker = PaddingOracleAttacker("185.207.251.177", 1600)
    
    try:
        # Obtener prophecy
        prophecy = attacker.connect_and_get_prophecy()
        
        if prophecy is None:
            print("No se pudo obtener prophecy")
            return
        
        print(f"\nProphecy obtenida: {prophecy.hex()}")
        print(f"Longitud: {len(prophecy)} bytes")
        
        # Intentar ataque simplificado
        result = attacker.simple_attack(prophecy)
        
        if result:
            print(f"\nAlgo descifrado: {result.hex()}")
            text = result.decode('utf-8', errors='ignore')
            print(f"Como texto: {text}")
        else:
            print("No se pudo descifrar")
    
    except KeyboardInterrupt:
        print("\nAtaque interrumpido")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        attacker.close()
        print("Conexion cerrada")

if __name__ == "__main__":
    main()