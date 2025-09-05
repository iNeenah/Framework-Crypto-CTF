#!/usr/bin/env python3
"""
Solucionador Completo de Padding Oracle Attack
==============================================
Implementación completa del algoritmo de Padding Oracle
"""

import socket
import time
import re

class PaddingOracleComplete:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        
    def connect_and_get_prophecy(self):
        """Conecta y obtiene la prophecy"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(15)
            
            print(f"🔗 Conectando a {self.host}:{self.port}...")
            self.socket.connect((self.host, self.port))
            
            # Leer respuesta inicial
            response = b""
            time.sleep(2)
            
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
            
            # Extraer prophecy
            match = re.search(r'Prophecy \(HEX\): ([a-fA-F0-9]+)', text)
            if match:
                hex_data = match.group(1)
                prophecy = bytes.fromhex(hex_data)
                return prophecy
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            return None
    
    def check_padding(self, ciphertext_hex):
        """Verifica padding con el oracle"""
        try:
            self.socket.sendall((ciphertext_hex + "\n").encode())
            
            response = b""
            time.sleep(0.1)
            
            while True:
                try:
                    chunk = self.socket.recv(1024)
                    if not chunk:
                        break
                    response += chunk
                    
                    text = response.decode('utf-8', errors='ignore')
                    if "well-formed" in text:
                        return True
                    elif "chaotic" in text:
                        return False
                    elif "Provide new ciphertext" in text:
                        break
                        
                except socket.timeout:
                    break
            
            return False
            
        except Exception as e:
            return False
    
    def decrypt_byte(self, c1, c2, position, known_bytes):
        """Descifra un byte en la posición específica"""
        padding_value = 16 - position
        
        for guess in range(256):
            # Crear bloque modificado
            modified_c1 = bytearray(c1)
            
            # Configurar bytes ya conocidos
            for i in range(position + 1, 16):
                modified_c1[i] = c1[i] ^ known_bytes[i] ^ padding_value
            
            # Probar guess actual
            modified_c1[position] = guess
            
            # Crear ciphertext de prueba
            test_cipher = bytes(modified_c1) + c2
            
            if self.check_padding(test_cipher.hex()):
                # Byte encontrado
                original_byte = guess ^ c1[position] ^ padding_value
                return original_byte
        
        return None
    
    def decrypt_block(self, c1, c2):
        """Descifra un bloque completo"""
        print(f"🔓 Descifrando bloque...")
        
        decrypted = [0] * 16
        
        # Descifrar de derecha a izquierda
        for pos in range(15, -1, -1):
            print(f"  📍 Posición {pos+1}/16...", end="", flush=True)
            
            byte_val = self.decrypt_byte(c1, c2, pos, decrypted)
            
            if byte_val is not None:
                decrypted[pos] = byte_val
                char = chr(byte_val) if 32 <= byte_val <= 126 else '.'
                print(f" ✅ {byte_val:02x} ('{char}')")
            else:
                print(f" ❌ Falló")
                return None
        
        return bytes(decrypted)
    
    def full_attack(self, ciphertext):
        """Ataque completo a todos los bloques"""
        print(f"\n🎯 PADDING ORACLE ATTACK COMPLETO")
        print(f"📏 Ciphertext: {len(ciphertext)} bytes")
        
        # Dividir en bloques
        blocks = []
        for i in range(0, len(ciphertext), 16):
            blocks.append(ciphertext[i:i+16])
        
        print(f"🔢 Bloques: {len(blocks)}")
        
        # Mostrar bloques
        for i, block in enumerate(blocks):
            if i == 0:
                print(f"📋 IV: {block.hex()}")
            else:
                print(f"📋 Bloque {i}: {block.hex()}")
        
        # Descifrar cada bloque
        decrypted_blocks = []
        
        for i in range(1, len(blocks)):  # Empezar desde bloque 1 (saltamos IV)
            print(f"\n🔓 Descifrando bloque {i}/{len(blocks)-1}")
            
            prev_block = blocks[i-1]  # Bloque anterior (IV para el primero)
            current_block = blocks[i]
            
            decrypted = self.decrypt_block(prev_block, current_block)
            
            if decrypted is None:
                print(f"❌ Error en bloque {i}")
                return None
            
            decrypted_blocks.append(decrypted)
            
            # Mostrar progreso
            text = decrypted.decode('utf-8', errors='ignore')
            print(f"✅ Bloque {i} descifrado: '{text}'")
        
        # Unir bloques
        full_plaintext = b''.join(decrypted_blocks)
        
        # Remover padding
        if full_plaintext:
            padding_len = full_plaintext[-1]
            if 1 <= padding_len <= 16:
                # Verificar que el padding sea válido
                padding_bytes = full_plaintext[-padding_len:]
                if all(b == padding_len for b in padding_bytes):
                    return full_plaintext[:-padding_len]
        
        return full_plaintext
    
    def close(self):
        if self.socket:
            self.socket.close()

def main():
    print("🎯 PADDING ORACLE ATTACK - VERSIÓN COMPLETA")
    print("=" * 50)
    print("🌐 Target: 185.207.251.177:1600")
    print("🎮 Challenge: chall.py")
    print()
    
    attacker = PaddingOracleComplete("185.207.251.177", 1600)
    
    try:
        # Obtener prophecy
        prophecy = attacker.connect_and_get_prophecy()
        
        if prophecy is None:
            print("❌ No se pudo obtener prophecy")
            return
        
        print(f"📜 Prophecy: {prophecy.hex()}")
        print(f"📏 Longitud: {len(prophecy)} bytes")
        
        # Ejecutar ataque completo
        print("\n🚀 Iniciando ataque...")
        flag = attacker.full_attack(prophecy)
        
        if flag:
            flag_text = flag.decode('utf-8', errors='ignore')
            print(f"\n🎉 ¡FLAG DESCIFRADA!")
            print(f"🏆 FLAG: {flag_text}")
            
            # Guardar resultado
            solved_file = "challenges/solved/chall_padding_oracle_flag.txt"
            with open(solved_file, 'w', encoding='utf-8') as f:
                f.write(f"Challenge: chall.py (Padding Oracle Attack)\n")
                f.write(f"Host: 185.207.251.177:1600\n")
                f.write(f"Method: Padding Oracle Attack - AES CBC\n")
                f.write(f"Prophecy: {prophecy.hex()}\n")
                f.write(f"Flag: {flag_text}\n")
            
            print(f"💾 Solución guardada en: {solved_file}")
            
            # Intentar submitir la flag al servidor
            print(f"\n📤 Intentando submitir flag al servidor...")
            try:
                submit_cmd = f"submit {flag_text}"
                attacker.socket.sendall((submit_cmd + "\n").encode())
                
                response = b""
                time.sleep(1)
                
                while True:
                    try:
                        chunk = attacker.socket.recv(1024)
                        if not chunk:
                            break
                        response += chunk
                        
                        text = response.decode('utf-8', errors='ignore')
                        if "INCREDIBLE" in text or "deciphered" in text:
                            print("🎉 ¡FLAG ACEPTADA POR EL SERVIDOR!")
                            break
                        elif "not what the runes foretell" in text:
                            print("❌ Flag rechazada por el servidor")
                            break
                            
                    except socket.timeout:
                        break
                
                print(f"📨 Respuesta del servidor: {response.decode('utf-8', errors='ignore')}")
                
            except Exception as e:
                print(f"⚠️  Error enviando flag: {e}")
        else:
            print("❌ No se pudo descifrar la flag")
    
    except KeyboardInterrupt:
        print("\n⚠️  Ataque interrumpido")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        attacker.close()
        print("🔌 Conexión cerrada")

if __name__ == "__main__":
    main()