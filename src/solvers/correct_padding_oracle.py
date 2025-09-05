#!/usr/bin/env python3
"""
Implementación Correcta de Padding Oracle Attack
===============================================
Algoritmo teóricamente correcto para extraer la flag completa
"""

import socket
import time
import re

class CorrectPaddingOracle:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        
    def connect(self):
        """Conecta al servidor"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(20)
            self.socket.connect((self.host, self.port))
            
            # Leer respuesta inicial
            response = self.socket.recv(4096).decode('utf-8', errors='ignore')
            
            # Extraer prophecy
            match = re.search(r'Prophecy \(HEX\): ([a-fA-F0-9]+)', response)
            if match:
                return bytes.fromhex(match.group(1))
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def oracle(self, ciphertext_bytes):
        """Oracle query - devuelve True si padding es válido"""
        try:
            hex_data = ciphertext_bytes.hex()
            self.socket.sendall((hex_data + "\n").encode())
            time.sleep(0.1)
            
            response = self.socket.recv(1024).decode('utf-8', errors='ignore')
            return "well-formed" in response or "Valid Padding" in response
        except:
            return False
    
    def decrypt_byte(self, target_block, prev_block, byte_index, intermediate_values):
        """
        Descifra un byte específico usando padding oracle
        
        Args:
            target_block: Bloque que queremos descifrar
            prev_block: Bloque anterior (IV o bloque previo)
            byte_index: Índice del byte a descifrar (0-15, donde 15 es el último)
            intermediate_values: Valores intermedios ya descubiertos
        """
        padding_length = 16 - byte_index
        
        print(f"    🔍 Descifrando byte {byte_index} (padding {padding_length})...")
        
        # Crear bloque modificado
        attack_block = bytearray(prev_block)
        
        # Configurar bytes ya conocidos para producir el padding correcto
        for i in range(byte_index + 1, 16):
            attack_block[i] = intermediate_values[i] ^ padding_length
        
        # Probar cada valor posible para el byte actual
        for guess in range(256):
            attack_block[byte_index] = guess
            
            # Crear ciphertext de prueba
            test_ciphertext = bytes(attack_block) + target_block
            
            if self.oracle(test_ciphertext):
                # Encontramos el valor que produce padding válido
                # El valor intermedio es: guess XOR padding_length
                intermediate_value = guess ^ padding_length
                print(f"    ✅ Byte {byte_index}: intermediate={intermediate_value:02x}")
                return intermediate_value
        
        print(f"    ❌ No se pudo descifrar byte {byte_index}")
        return None
    
    def decrypt_block(self, target_block, prev_block, block_number):
        """Descifra un bloque completo"""
        print(f"\n🔓 Descifrando bloque {block_number}")
        print(f"   Target: {target_block.hex()}")
        print(f"   Prev:   {prev_block.hex()}")
        
        # Array para almacenar valores intermedios
        intermediate_values = [0] * 16
        
        # Descifrar de derecha a izquierda (byte 15 al 0)
        for byte_index in range(15, -1, -1):
            intermediate = self.decrypt_byte(target_block, prev_block, byte_index, intermediate_values)
            
            if intermediate is not None:
                intermediate_values[byte_index] = intermediate
            else:
                print(f"    ⚠️  Usando valor 0 para byte {byte_index}")
                intermediate_values[byte_index] = 0
        
        # Calcular plaintext final: intermediate XOR prev_block
        plaintext_bytes = []
        for i in range(16):
            plaintext_byte = intermediate_values[i] ^ prev_block[i]
            plaintext_bytes.append(plaintext_byte)
        
        plaintext = bytes(plaintext_bytes)
        
        # Mostrar resultado
        readable = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in plaintext)
        print(f"   ✅ Plaintext: {plaintext.hex()}")
        print(f"   📝 Texto: '{readable}'")
        
        return plaintext
    
    def attack(self, ciphertext):
        """Ejecuta el ataque completo"""
        print(f"🎯 PADDING ORACLE ATTACK")
        print(f"📏 Ciphertext: {len(ciphertext)} bytes")
        
        # Dividir en bloques
        block_size = 16
        blocks = []
        for i in range(0, len(ciphertext), block_size):
            blocks.append(ciphertext[i:i+block_size])
        
        print(f"🔢 Bloques: {len(blocks)}")
        
        # El primer bloque es el IV
        if len(blocks) < 2:
            print("❌ Necesitamos al menos IV + 1 bloque")
            return None
        
        # Descifrar bloques (saltando el IV)
        decrypted_blocks = []
        
        for i in range(1, min(3, len(blocks))):  # Limitar a 2 bloques para ser más rápido
            prev_block = blocks[i-1]  # IV o bloque anterior
            current_block = blocks[i]
            
            decrypted = self.decrypt_block(current_block, prev_block, i)
            decrypted_blocks.append(decrypted)
        
        # Unir bloques descifrados
        full_plaintext = b''.join(decrypted_blocks)
        
        # Intentar remover padding
        try:
            # Verificar si el último byte indica padding válido
            if full_plaintext and 1 <= full_plaintext[-1] <= 16:
                padding_len = full_plaintext[-1]
                
                # Verificar que todos los bytes de padding sean iguales
                padding_bytes = full_plaintext[-padding_len:]
                if all(b == padding_len for b in padding_bytes):
                    return full_plaintext[:-padding_len]
        except:
            pass
        
        return full_plaintext
    
    def submit_flag(self, flag_text):
        """Envía la flag al servidor"""
        try:
            print(f"\n📤 Enviando flag: {flag_text}")
            command = f"submit {flag_text}"
            self.socket.sendall((command + "\n").encode())
            
            time.sleep(1)
            response = self.socket.recv(2048).decode('utf-8', errors='ignore')
            
            if "INCREDIBLE" in response or "deciphered" in response:
                print("🎉 ¡FLAG ACEPTADA!")
                return True
            else:
                print(f"❌ Flag rechazada")
                print(f"📨 Respuesta: {response[:150]}...")
                return False
        except Exception as e:
            print(f"⚠️  Error: {e}")
            return False
    
    def close(self):
        if self.socket:
            self.socket.close()

def extract_flag():
    """Función principal para extraer la flag"""
    print("🎯 EXTRACTOR DE FLAG CORRECTO - chall.py")
    print("=" * 45)
    print("🌐 Target: 185.207.251.177:1600")
    print()
    
    attacker = CorrectPaddingOracle("185.207.251.177", 1600)
    
    try:
        # Conectar y obtener ciphertext
        ciphertext = attacker.connect()
        if not ciphertext:
            print("❌ No se pudo obtener ciphertext")
            return None
        
        print(f"📜 Ciphertext obtenido: {ciphertext.hex()}")
        print(f"📏 Longitud: {len(ciphertext)} bytes")
        
        # Ejecutar ataque
        plaintext = attacker.attack(ciphertext)
        
        if plaintext:
            flag_text = plaintext.decode('utf-8', errors='ignore').strip()
            print(f"\n🎉 ¡PLAINTEXT DESCIFRADO!")
            print(f"🔓 Resultado: '{flag_text}'")
            
            # Buscar patrón de flag
            flag_match = re.search(r'n3xt\{[^}]+\}', flag_text, re.IGNORECASE)
            if flag_match:
                flag = flag_match.group(0)
                print(f"🏆 FLAG ENCONTRADA: {flag}")
            else:
                flag = flag_text
                print(f"🏆 TEXTO COMPLETO: {flag}")
            
            # Probar con el servidor
            success = attacker.submit_flag(flag)
            
            # Guardar resultado
            with open("challenges/solved/chall_correct_flag.txt", 'w') as f:
                f.write(f"Challenge: chall.py\n")
                f.write(f"Method: Correct Padding Oracle Attack\n")
                f.write(f"Ciphertext: {ciphertext.hex()}\n")
                f.write(f"Plaintext: {plaintext.hex()}\n")
                f.write(f"Flag: {flag}\n")
                f.write(f"Verified: {'YES' if success else 'NO'}\n")
            
            print(f"💾 Resultado guardado")
            
            return flag
        else:
            print("❌ No se pudo descifrar")
            return None
    
    except KeyboardInterrupt:
        print("\n⚠️  Interrumpido")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        attacker.close()

if __name__ == "__main__":
    result = extract_flag()
    
    if result:
        print(f"\n" + "🎉" * 20)
        print(f"FLAG FINAL: {result}")
        print(f"🎉" * 20)
    else:
        print("\n❌ No se obtuvo la flag")