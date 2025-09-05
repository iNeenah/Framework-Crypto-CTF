#!/usr/bin/env python3
"""
Solucionador Específico para Padding Oracle - Enfoque en Flag
=============================================================
Se enfoca en descifrar los bloques que contienen la flag real
"""

import socket
import time
import re

class FocusedPaddingOracle:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        
    def connect_and_get_prophecy(self):
        """Conecta y obtiene la prophecy"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(20)
            
            print(f"🔗 Conectando a {self.host}:{self.port}...")
            self.socket.connect((self.host, self.port))
            
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
            match = re.search(r'Prophecy \(HEX\): ([a-fA-F0-9]+)', text)
            if match:
                return bytes.fromhex(match.group(1))
            return None
                
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            return None
    
    def check_padding(self, ciphertext_hex):
        """Verifica padding"""
        try:
            self.socket.sendall((ciphertext_hex + "\n").encode())
            
            response = b""
            time.sleep(0.2)
            
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
            
        except Exception:
            return False
    
    def find_padding_length(self, c1, c2):
        """Encuentra la longitud del padding en el último bloque"""
        print("🔍 Determinando longitud del padding...")
        
        # Probar modificar el último byte del bloque anterior
        for i in range(1, 17):
            modified_c1 = bytearray(c1)
            modified_c1[-i] = (modified_c1[-i] + 1) % 256
            
            test_cipher = bytes(modified_c1) + c2
            
            if not self.check_padding(test_cipher.hex()):
                print(f"✅ Padding detectado: {i} bytes")
                return i
        
        print("⚠️  No se pudo determinar padding")
        return 1  # Asumir padding mínimo
    
    def decrypt_byte_smart(self, c1, c2, position):
        """Descifra un byte específico con lógica inteligente"""
        padding_value = 16 - position
        
        candidates = []
        
        for guess in range(256):
            modified_c1 = bytearray(c1)
            modified_c1[position] = guess
            
            test_cipher = bytes(modified_c1) + c2
            
            if self.check_padding(test_cipher.hex()):
                original_byte = guess ^ c1[position] ^ padding_value
                candidates.append(original_byte)
        
        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) == 0:
            return None
        else:
            # Múltiples candidatos - elegir el más probable
            # Para texto ASCII, priorizar caracteres imprimibles
            printable_candidates = [b for b in candidates if 32 <= b <= 126]
            if printable_candidates:
                return printable_candidates[0]
            else:
                return candidates[0]
    
    def decrypt_block_focused(self, c1, c2, is_last_block=False):
        """Descifra un bloque con enfoque específico"""
        print(f"🔓 Descifrando bloque {'(último)' if is_last_block else ''}...")
        
        decrypted = [0] * 16
        
        if is_last_block:
            # Para el último bloque, determinar padding primero
            padding_len = self.find_padding_length(c1, c2)
            
            # Los últimos padding_len bytes deberían ser padding_len
            for i in range(16 - padding_len, 16):
                decrypted[i] = padding_len
                print(f"  📍 Posición {i+1}/16: {padding_len:02x} (padding)")
            
            # Descifrar solo los bytes de contenido
            for pos in range(16 - padding_len - 1, -1, -1):
                print(f"  📍 Posición {pos+1}/16...", end="", flush=True)
                
                byte_val = self.decrypt_byte_smart(c1, c2, pos)
                
                if byte_val is not None:
                    decrypted[pos] = byte_val
                    char = chr(byte_val) if 32 <= byte_val <= 126 else '.'
                    print(f" ✅ {byte_val:02x} ('{char}')")
                else:
                    print(f" ❌ Falló")
                    decrypted[pos] = 0
        else:
            # Para bloques normales, descifrar todos los bytes
            for pos in range(15, -1, -1):
                print(f"  📍 Posición {pos+1}/16...", end="", flush=True)
                
                byte_val = self.decrypt_byte_smart(c1, c2, pos)
                
                if byte_val is not None:
                    decrypted[pos] = byte_val
                    char = chr(byte_val) if 32 <= byte_val <= 126 else '.'
                    print(f" ✅ {byte_val:02x} ('{char}')")
                else:
                    print(f" ❌ Falló")
                    decrypted[pos] = 0
        
        return bytes(decrypted)
    
    def focused_attack(self, ciphertext):
        """Ataque enfocado en encontrar la flag"""
        print(f"\n🎯 PADDING ORACLE ATTACK - ENFOQUE EN FLAG")
        print(f"📏 Ciphertext: {len(ciphertext)} bytes")
        
        blocks = [ciphertext[i:i+16] for i in range(0, len(ciphertext), 16)]
        print(f"🔢 Bloques: {len(blocks)}")
        
        # Mostrar estructura
        for i, block in enumerate(blocks):
            if i == 0:
                print(f"📋 IV: {block.hex()}")
            else:
                print(f"📋 Bloque {i}: {block.hex()}")
        
        # Estrategia: descifrar los primeros bloques (más probable que contengan la flag)
        decrypted_blocks = []
        
        for i in range(1, min(3, len(blocks))):  # Descifrar los primeros 2 bloques
            prev_block = blocks[i-1]
            current_block = blocks[i]
            is_last = (i == len(blocks) - 1)
            
            print(f"\n🔓 Descifrando bloque {i}/{len(blocks)-1}")
            decrypted = self.decrypt_block_focused(prev_block, current_block, is_last)
            
            if decrypted:
                text = decrypted.decode('utf-8', errors='ignore')
                print(f"✅ Bloque {i}: '{text}'")
                decrypted_blocks.append(decrypted)
                
                # Si encontramos algo que parece una flag, paramos
                if any(pattern in text.lower() for pattern in ['n3xt{', 'flag{', 'ctf{']):
                    print("🎯 Flag detectada!")
                    break
            else:
                print(f"❌ Error en bloque {i}")
                decrypted_blocks.append(b'\\x00' * 16)
        
        if decrypted_blocks:
            full_text = b''.join(decrypted_blocks)
            
            # Limpiar y extraer flag
            text = full_text.decode('utf-8', errors='ignore').strip()
            
            # Buscar patrón de flag
            flag_match = re.search(r'n3xt\{[^}]+\}', text)
            if flag_match:
                return flag_match.group(0)
            
            # Si no encontramos patrón específico, devolver texto limpio
            clean_text = ''.join(c for c in text if 32 <= ord(c) <= 126)
            return clean_text
        
        return None
    
    def close(self):
        if self.socket:
            self.socket.close()

def main():
    print("🎯 PADDING ORACLE ATTACK - ENFOQUE EN FLAG")
    print("=" * 50)
    print("🌐 Target: 185.207.251.177:1600")
    print("🎮 Challenge: chall.py")
    print()
    
    attacker = FocusedPaddingOracle("185.207.251.177", 1600)
    
    try:
        prophecy = attacker.connect_and_get_prophecy()
        
        if prophecy is None:
            print("❌ No se pudo obtener prophecy")
            return
        
        print(f"📜 Prophecy: {prophecy.hex()}")
        print(f"📏 Longitud: {len(prophecy)} bytes")
        
        # Ejecutar ataque enfocado
        flag = attacker.focused_attack(prophecy)
        
        if flag:
            print(f"\n🎉 ¡FLAG ENCONTRADA!")
            print(f"🏆 FLAG: {flag}")
            
            # Guardar resultado
            solved_file = "challenges/solved/chall_padding_oracle_focused.txt"
            with open(solved_file, 'w', encoding='utf-8') as f:
                f.write(f"Challenge: chall.py (Padding Oracle Attack - Focused)\n")
                f.write(f"Host: 185.207.251.177:1600\n")
                f.write(f"Method: Focused Padding Oracle Attack\n")
                f.write(f"Prophecy: {prophecy.hex()}\n")
                f.write(f"Flag: {flag}\n")
            
            print(f"💾 Solución guardada en: {solved_file}")
            
            # Intentar submitir
            if flag and len(flag) > 4:
                print(f"\n📤 Submitting flag...")
                try:
                    submit_cmd = f"submit {flag}"
                    attacker.socket.sendall((submit_cmd + "\n").encode())
                    
                    time.sleep(2)
                    response = attacker.socket.recv(4096).decode('utf-8', errors='ignore')
                    print(f"📨 Respuesta: {response}")
                    
                    if "INCREDIBLE" in response:
                        print("🎉 ¡FLAG ACEPTADA!")
                    
                except Exception as e:
                    print(f"⚠️  Error submitting: {e}")
        else:
            print("❌ No se pudo encontrar la flag")
    
    except KeyboardInterrupt:
        print("\n⚠️  Interrumpido")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        attacker.close()
        print("🔌 Conexión cerrada")

if __name__ == "__main__":
    main()