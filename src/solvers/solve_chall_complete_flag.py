#!/usr/bin/env python3
"""
Solucionador Completo para obtener la FLAG de chall.py
====================================================
Padding Oracle Attack optimizado para extraer la flag completa
"""

import socket
import time
import re
from Crypto.Util.Padding import unpad

class CompleteFlag:
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
            
            # Leer respuesta inicial
            response = b""
            time.sleep(1)
            
            response = self.socket.recv(4096)
            text = response.decode('utf-8', errors='ignore')
            
            match = re.search(r'Prophecy \(HEX\): ([a-fA-F0-9]+)', text)
            if match:
                return bytes.fromhex(match.group(1))
            return None
                
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            return None
    
    def oracle_query(self, ciphertext_hex):
        """Query optimizado al oracle"""
        try:
            self.socket.sendall((ciphertext_hex + "\n").encode())
            time.sleep(0.05)  # Pausa mínima
            
            response = self.socket.recv(1024).decode('utf-8', errors='ignore')
            return "well-formed" in response
            
        except Exception:
            return False
    
    def decrypt_byte_optimized(self, c1, c2, position, known_intermediate):
        """Descifra un byte específico optimizado"""
        padding_value = 16 - position
        
        # Crear bloque base con valores conocidos
        modified_c1 = bytearray(c1)
        
        # Configurar bytes conocidos para el padding correcto
        for i in range(position + 1, 16):
            modified_c1[i] = known_intermediate[i] ^ padding_value
        
        # Probar cada valor posible para este byte
        for guess in range(256):
            modified_c1[position] = guess
            
            test_cipher = bytes(modified_c1) + c2
            
            if self.oracle_query(test_cipher.hex()):
                # Calcular el valor intermedio
                intermediate_value = guess ^ padding_value
                return intermediate_value
        
        return None
    
    def decrypt_block_optimized(self, c1, c2, block_num):
        """Descifra un bloque completo optimizado"""
        print(f"\n🔓 Descifrando bloque {block_num}...")
        
        intermediate_values = [0] * 16
        
        # Descifrar de derecha a izquierda
        for pos in range(15, -1, -1):
            print(f"  📍 Byte {16-pos}/16...", end="", flush=True)
            
            intermediate = self.decrypt_byte_optimized(c1, c2, pos, intermediate_values)
            
            if intermediate is not None:
                intermediate_values[pos] = intermediate
                # Calcular el plaintext real
                plaintext_byte = intermediate ^ c1[pos]
                char = chr(plaintext_byte) if 32 <= plaintext_byte <= 126 else '.'
                print(f" ✅ {plaintext_byte:02x} ('{char}')")
            else:
                print(f" ❌")
                intermediate_values[pos] = 0
        
        # Convertir intermediate values a plaintext
        plaintext = bytes(intermediate_values[i] ^ c1[i] for i in range(16))
        return plaintext
    
    def extract_complete_flag(self, ciphertext):
        """Extrae la flag completa usando padding oracle"""
        print(f"\n🎯 EXTRAYENDO FLAG COMPLETA")
        print(f"📏 Ciphertext: {len(ciphertext)} bytes")
        
        # Dividir en bloques
        blocks = [ciphertext[i:i+16] for i in range(0, len(ciphertext), 16)]
        print(f"🔢 Bloques totales: {len(blocks)}")
        
        if len(blocks) < 2:
            print("❌ Necesitamos al menos 2 bloques")
            return None
        
        # Descifrar todos los bloques de cifrado (saltando el IV)
        all_plaintext = []
        
        for i in range(1, len(blocks)):
            prev_block = blocks[i-1]  # IV o bloque anterior
            current_block = blocks[i]
            
            plaintext_block = self.decrypt_block_optimized(prev_block, current_block, i)
            
            if plaintext_block:
                all_plaintext.append(plaintext_block)
                text_preview = plaintext_block.decode('utf-8', errors='ignore')
                print(f"✅ Bloque {i}: '{text_preview}'")
            else:
                print(f"❌ Error en bloque {i}")
                return None
        
        # Unir todos los bloques
        full_plaintext = b''.join(all_plaintext)
        
        # Remover padding PKCS7
        try:
            unpadded = unpad(full_plaintext, 16)
            return unpadded.decode('utf-8', errors='ignore').strip()
        except:
            # Si falla el unpad, intentar manualmente
            if full_plaintext and full_plaintext[-1] <= 16:
                padding_len = full_plaintext[-1]
                if all(b == padding_len for b in full_plaintext[-padding_len:]):
                    return full_plaintext[:-padding_len].decode('utf-8', errors='ignore').strip()
            
            return full_plaintext.decode('utf-8', errors='ignore').strip()
    
    def submit_flag(self, flag):
        """Envía la flag al servidor para verificación"""
        try:
            print(f"\n📤 Enviando flag: {flag}")
            submit_cmd = f"submit {flag}"
            self.socket.sendall((submit_cmd + "\n").encode())
            
            time.sleep(2)
            response = self.socket.recv(4096).decode('utf-8', errors='ignore')
            
            if "INCREDIBLE" in response or "deciphered" in response:
                print("🎉 ¡FLAG ACEPTADA!")
                return True
            else:
                print(f"❌ Flag rechazada: {response}")
                return False
                
        except Exception as e:
            print(f"⚠️  Error enviando flag: {e}")
            return False
    
    def close(self):
        if self.socket:
            self.socket.close()

def main():
    print("🎯 EXTRACTOR COMPLETO DE FLAG - chall.py")
    print("=" * 45)
    print("🌐 Target: 185.207.251.177:1600")
    print("🎮 Challenge: Padding Oracle Attack")
    print("🎯 Objetivo: Obtener la flag completa")
    print()
    
    extractor = CompleteFlag("185.207.251.177", 1600)
    
    try:
        # Conectar y obtener prophecy
        prophecy = extractor.connect_and_get_prophecy()
        
        if prophecy is None:
            print("❌ No se pudo obtener la prophecy")
            return
        
        print(f"📜 Prophecy obtenida: {prophecy.hex()}")
        print(f"📏 Longitud: {len(prophecy)} bytes")
        
        # Extraer flag completa
        print("\n🚀 Iniciando extracción de flag completa...")
        flag = extractor.extract_complete_flag(prophecy)
        
        if flag:
            print(f"\n🎉 ¡FLAG EXTRAÍDA!")
            print(f"🏆 FLAG: {flag}")
            
            # Verificar con el servidor
            if extractor.submit_flag(flag):
                print("✅ Flag verificada por el servidor!")
            
            # Guardar resultado final
            solved_file = "challenges/solved/chall_complete_flag.txt"
            with open(solved_file, 'w', encoding='utf-8') as f:
                f.write(f"Challenge: chall.py (Padding Oracle Attack - COMPLETE)\n")
                f.write(f"Host: 185.207.251.177:1600\n")
                f.write(f"Method: Complete Padding Oracle Attack\n")
                f.write(f"Prophecy: {prophecy.hex()}\n")
                f.write(f"FINAL FLAG: {flag}\n")
                f.write(f"Status: SOLVED\n")
            
            print(f"💾 Flag guardada en: {solved_file}")
            
            return flag
            
        else:
            print("❌ No se pudo extraer la flag")
            return None
    
    except KeyboardInterrupt:
        print("\n⚠️  Proceso interrumpido")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        extractor.close()
        print("🔌 Conexión cerrada")

if __name__ == "__main__":
    final_flag = main()
    
    if final_flag:
        print(f"\n" + "="*50)
        print(f"🎉 ¡DESAFÍO COMPLETAMENTE RESUELTO!")
        print(f"🏆 FLAG FINAL: {final_flag}")
        print(f"✅ Framework funcionando perfectamente")
        print(f"="*50)
    else:
        print(f"\n❌ No se pudo completar el desafío")