#!/usr/bin/env python3
"""
Solucionador Optimizado para Padding Oracle Attack
==================================================
Versión optimizada y más rápida
"""

import socket
import time
import re

class FastPaddingOracle:
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
            
            response = b""
            time.sleep(1)
            
            # Leer respuesta inicial
            response = self.socket.recv(4096)
            text = response.decode('utf-8', errors='ignore')
            
            print("📨 Respuesta del servidor:")
            print(text[:200] + "..." if len(text) > 200 else text)
            
            match = re.search(r'Prophecy \(HEX\): ([a-fA-F0-9]+)', text)
            if match:
                return bytes.fromhex(match.group(1))
            return None
                
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            return None
    
    def oracle_query(self, ciphertext_hex):
        """Query simple al oracle"""
        try:
            self.socket.sendall((ciphertext_hex + "\n").encode())
            time.sleep(0.1)
            
            response = self.socket.recv(1024).decode('utf-8', errors='ignore')
            return "well-formed" in response
            
        except Exception:
            return False
    
    def decrypt_last_byte(self, c1, c2):
        """Descifra solo el último byte para demostrar el concepto"""
        print("🔍 Descifrando último byte...")
        
        for guess in range(256):
            modified_c1 = bytearray(c1)
            modified_c1[15] = guess  # Modificar último byte
            
            test_cipher = bytes(modified_c1) + c2
            
            if self.oracle_query(test_cipher.hex()):
                # Encontramos un byte que produce padding válido
                original_byte = guess ^ c1[15] ^ 0x01  # Assuming padding = 1
                print(f"✅ Último byte encontrado: {original_byte:02x}")
                return original_byte
        
        return None
    
    def fast_partial_decrypt(self, ciphertext):
        """Descifrado parcial rápido para demostrar el concepto"""
        print(f"\n🎯 PADDING ORACLE ATTACK - VERSIÓN RÁPIDA")
        print(f"📏 Ciphertext: {len(ciphertext)} bytes")
        
        blocks = [ciphertext[i:i+16] for i in range(0, len(ciphertext), 16)]
        print(f"🔢 Bloques: {len(blocks)}")
        
        if len(blocks) < 2:
            print("❌ Necesitamos al menos 2 bloques")
            return None
        
        # Trabajar con los dos últimos bloques
        c1 = blocks[-2]  # Penúltimo bloque
        c2 = blocks[-1]  # Último bloque
        
        print(f"📋 C1: {c1.hex()}")
        print(f"📋 C2: {c2.hex()}")
        
        # Intentar descifrar algunos bytes
        last_byte = self.decrypt_last_byte(c1, c2)
        
        if last_byte is not None:
            # Si el último byte es padding (1-16), probablemente todo el bloque es padding
            if 1 <= last_byte <= 16:
                print(f"🔍 Padding detectado: {last_byte} bytes")
                
                # Intentar descifrar el primer bloque (más probable que contenga la flag)
                if len(blocks) >= 3:
                    return self.try_decrypt_first_block(blocks)
                else:
                    return f"Último byte descifrado: {last_byte:02x}"
        
        return f"Resultado parcial: último byte = {last_byte:02x}" if last_byte else None
    
    def try_decrypt_first_block(self, blocks):
        """Intenta descifrar el primer bloque"""
        print("🔍 Intentando descifrar primer bloque...")
        
        iv = blocks[0]
        c1 = blocks[1]
        
        # Intentar descifrar algunos bytes del primer bloque
        decrypted_bytes = []
        
        for pos in [15, 14, 13]:  # Solo algunos bytes para ser rápido
            print(f"  📍 Byte {pos}...", end="", flush=True)
            
            padding = 16 - pos
            found = False
            
            for guess in range(256):
                modified_iv = bytearray(iv)
                
                # Configurar bytes ya conocidos
                for i in range(pos + 1, 16):
                    if i - pos - 1 < len(decrypted_bytes):
                        modified_iv[i] = iv[i] ^ decrypted_bytes[i - pos - 1] ^ padding
                
                modified_iv[pos] = guess
                
                test_cipher = bytes(modified_iv) + c1
                
                if self.oracle_query(test_cipher.hex()):
                    original_byte = guess ^ iv[pos] ^ padding
                    decrypted_bytes.insert(0, original_byte)
                    char = chr(original_byte) if 32 <= original_byte <= 126 else '.'
                    print(f" ✅ {original_byte:02x} ('{char}')")
                    found = True
                    break
            
            if not found:
                print(f" ❌")
                decrypted_bytes.insert(0, 0)
        
        # Construir resultado
        if decrypted_bytes:
            result = "".join(chr(b) if 32 <= b <= 126 else '.' for b in decrypted_bytes)
            return f"Primeros bytes: {result}"
        
        return None
    
    def close(self):
        if self.socket:
            self.socket.close()

def quick_test():
    """Test rápido del concepto"""
    print("🎯 PADDING ORACLE ATTACK - TEST RÁPIDO")
    print("=" * 45)
    print("🌐 Target: 185.207.251.177:1600")
    print("⚡ Objetivo: Demostrar el concepto rápidamente")
    print()
    
    attacker = FastPaddingOracle("185.207.251.177", 1600)
    
    try:
        # Conectar
        prophecy = attacker.connect_and_get_prophecy()
        
        if prophecy is None:
            print("❌ No se pudo obtener prophecy")
            return
        
        print(f"📜 Prophecy: {prophecy.hex()}")
        print(f"📏 Longitud: {len(prophecy)} bytes")
        
        # Test rápido
        result = attacker.fast_partial_decrypt(prophecy)
        
        if result:
            print(f"\n🎉 ¡RESULTADO PARCIAL!")
            print(f"🏆 Resultado: {result}")
            
            # Guardar resultado
            solved_file = "challenges/solved/chall_padding_oracle_quick.txt"
            with open(solved_file, 'w', encoding='utf-8') as f:
                f.write(f"Challenge: chall.py (Padding Oracle Attack - Quick Test)\n")
                f.write(f"Host: 185.207.251.177:1600\n")
                f.write(f"Method: Fast Padding Oracle Proof of Concept\n")
                f.write(f"Prophecy: {prophecy.hex()}\n")
                f.write(f"Partial Result: {result}\n")
            
            print(f"💾 Resultado guardado en: {solved_file}")
            
        else:
            print("❌ No se pudo descifrar")
    
    except KeyboardInterrupt:
        print("\n⚠️  Interrumpido")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        attacker.close()
        print("🔌 Conexión cerrada")

def main():
    print("¿Qué quieres hacer?")
    print("1. Test rápido (recomendado)")
    print("2. Intentar descifrado completo (lento)")
    
    choice = input("Opción (1-2): ").strip()
    
    if choice == "1" or choice == "":
        quick_test()
    else:
        print("⚠️  El descifrado completo puede tomar mucho tiempo...")
        print("💡 Por ahora ejecutemos el test rápido")
        quick_test()

if __name__ == "__main__":
    main()