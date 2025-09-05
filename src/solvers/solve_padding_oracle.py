#!/usr/bin/env python3
"""
Solucionador para Padding Oracle Attack - chall.py
================================================

Desafío: AES-CBC Padding Oracle
Host: 185.207.251.177:1600
Objetivo: Extraer la flag usando Padding Oracle Attack
"""

import socket
import binascii
from Crypto.Util.Padding import pad, unpad

class PaddingOracleAttacker:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        
    def connect(self):
        """Conecta al servidor oracle"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            
            # Leer la respuesta inicial y extraer la prophecy
            response = b""
            while b"Prophecy (HEX): " not in response:
                chunk = self.socket.recv(4096)
                if not chunk:
                    break
                response += chunk
            
            # Extraer la prophecy hex
            lines = response.decode().split('\n')
            for line in lines:
                if "Prophecy (HEX): " in line:
                    hex_prophecy = line.split("Prophecy (HEX): ")[1].strip()
                    return bytes.fromhex(hex_prophecy)
            
            return None
            
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            return None
    
    def check_padding(self, ciphertext_hex):
        """Envía ciphertext al oracle y verifica respuesta"""
        try:
            # Enviar el ciphertext
            self.socket.sendall(ciphertext_hex.encode() + b'\n')
            
            # Leer la respuesta completa
            response = b""
            while True:
                chunk = self.socket.recv(1024)
                if not chunk:
                    break
                response += chunk
                
                # Verificar si tenemos una respuesta completa
                response_str = response.decode('utf-8', errors='ignore')
                if "Valid Padding" in response_str:
                    return True
                elif "Invalid Padding" in response_str or "chaotic" in response_str:
                    return False
                elif "Provide new ciphertext" in response_str:
                    # Es el prompt para la siguiente consulta
                    break
                    
            return False
                
        except Exception as e:
            print(f"❌ Error en check_padding: {e}")
            return False
    
    def decrypt_block(self, c1, c2):
        """Descifra un bloque usando padding oracle attack"""
        print(f"🔓 Descifrando bloque...")
        
        # El bloque descifrado
        decrypted = bytearray(16)
        
        # Para cada byte del bloque (de derecha a izquierda)
        for i in range(15, -1, -1):
            print(f"  📍 Descifrando byte {15-i+1}/16...", end="", flush=True)
            
            # Para cada posible valor del byte
            for guess in range(256):
                # Crear el bloque modificado
                modified_c1 = bytearray(c1)
                
                # Calcular el padding deseado
                padding_value = 16 - i
                
                # Modificar bytes ya conocidos para que produzcan el padding correcto
                for j in range(i + 1, 16):
                    modified_c1[j] = c1[j] ^ decrypted[j] ^ padding_value
                
                # Probar con el guess actual
                modified_c1[i] = guess
                
                # Crear ciphertext completo para probar
                test_ciphertext = bytes(modified_c1) + c2
                test_hex = test_ciphertext.hex()
                
                # Verificar con el oracle
                if self.check_padding(test_hex):
                    # Encontramos el byte correcto
                    decrypted[i] = guess ^ c1[i] ^ padding_value
                    print(f" ✅ Byte encontrado: {decrypted[i]:02x}")
                    break
            else:
                print(f" ❌ No se pudo encontrar byte {i}")
                return None
        
        return bytes(decrypted)
    
    def padding_oracle_attack(self, ciphertext):
        """Ejecuta el ataque completo de padding oracle"""
        print(f"🎯 PADDING ORACLE ATTACK")
        print(f"📏 Longitud del ciphertext: {len(ciphertext)} bytes")
        print(f"🔢 Número de bloques: {len(ciphertext) // 16}")
        print("=" * 50)
        
        # Separar IV y bloques
        iv = ciphertext[:16]
        blocks = []
        
        for i in range(16, len(ciphertext), 16):
            blocks.append(ciphertext[i:i+16])
        
        print(f"📋 IV: {iv.hex()}")
        for i, block in enumerate(blocks):
            print(f"📋 Bloque {i+1}: {block.hex()}")
        
        # Descifrar cada bloque
        decrypted_blocks = []
        
        for i in range(len(blocks)):
            print(f"\n🔓 Descifrando bloque {i+1}/{len(blocks)}:")
            
            if i == 0:
                # Primer bloque usa IV
                prev_block = iv
            else:
                # Bloques siguientes usan el bloque anterior
                prev_block = blocks[i-1]
            
            current_block = blocks[i]
            
            # Descifrar el bloque
            decrypted_block = self.decrypt_block(prev_block, current_block)
            
            if decrypted_block is None:
                print(f"❌ Error descifrando bloque {i+1}")
                return None
                
            decrypted_blocks.append(decrypted_block)
            print(f"✅ Bloque {i+1} descifrado: {decrypted_block}")
        
        # Unir todos los bloques descifrados
        full_decrypted = b''.join(decrypted_blocks)
        
        try:
            # Remover padding PKCS7
            unpadded = unpad(full_decrypted, 16)
            return unpadded
        except ValueError:
            print("⚠️  Error removiendo padding, devolviendo datos sin procesar")
            return full_decrypted
    
    def close(self):
        """Cierra la conexión"""
        if self.socket:
            self.socket.close()

def main():
    print("🎯 SOLUCIONADOR PADDING ORACLE ATTACK")
    print("=" * 40)
    print("🌐 Host: 185.207.251.177:1600")
    print("🎮 Desafío: chall.py")
    print()
    
    # Crear atacante
    attacker = PaddingOracleAttacker("185.207.251.177", 1600)
    
    try:
        # Conectar y obtener prophecy
        print("🔗 Conectando al servidor...")
        prophecy = attacker.connect()
        
        if prophecy is None:
            print("❌ No se pudo obtener la prophecy del servidor")
            return
        
        print(f"📜 Prophecy obtenida: {prophecy.hex()}")
        print(f"📏 Longitud: {len(prophecy)} bytes")
        print()
        
        # Ejecutar padding oracle attack
        print("🚀 Iniciando Padding Oracle Attack...")
        decrypted_flag = attacker.padding_oracle_attack(prophecy)
        
        if decrypted_flag:
            print(f"\n🎉 ¡FLAG DESCIFRADA!")
            print(f"🏆 FLAG: {decrypted_flag.decode('utf-8', errors='ignore')}")
            
            # Guardar resultado
            solved_file = "challenges/solved/chall_padding_oracle_solution.txt"
            with open(solved_file, 'w', encoding='utf-8') as f:
                f.write(f"Challenge: chall.py (Padding Oracle Attack)\n")
                f.write(f"Host: 185.207.251.177:1600\n")
                f.write(f"Prophecy: {prophecy.hex()}\n")
                f.write(f"Flag: {decrypted_flag.decode('utf-8', errors='ignore')}\n")
            
            print(f"💾 Solución guardada en: {solved_file}")
            
        else:
            print("❌ No se pudo descifrar la flag")
    
    except KeyboardInterrupt:
        print("\n⚠️  Ataque interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error durante el ataque: {e}")
    finally:
        attacker.close()
        print("🔌 Conexión cerrada")

if __name__ == "__main__":
    main()