#!/usr/bin/env python3
"""
Solucionador Robusto de Padding Oracle Attack
=============================================
Versión que maneja falsos positivos y es más resiliente
"""

import socket
import time
import re

class RobustPaddingOracle:
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
    
    def check_padding_robust(self, ciphertext_hex, retries=3):
        """Verifica padding con reintentos para mayor robustez"""
        for attempt in range(retries):
            try:
                self.socket.sendall((ciphertext_hex + "\n").encode())
                
                response = b""
                time.sleep(0.15)  # Pausa más larga
                
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
                
                # Si llegamos aquí, reintentamos
                if attempt < retries - 1:
                    time.sleep(0.5)
                    continue
                else:
                    return False
                    
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(1)
                    continue
                else:
                    return False
        
        return False
    
    def find_valid_padding_byte(self, c1, c2, position, known_bytes):
        """Encuentra un byte que produzca padding válido"""
        padding_value = 16 - position
        candidates = []
        
        print(f"    🔍 Buscando byte para posición {position} (padding {padding_value})...")
        
        for guess in range(256):
            modified_c1 = bytearray(c1)
            
            # Configurar bytes conocidos
            for i in range(position + 1, 16):
                modified_c1[i] = c1[i] ^ known_bytes[i] ^ padding_value
            
            # Probar guess
            modified_c1[position] = guess
            
            test_cipher = bytes(modified_c1) + c2
            
            if self.check_padding_robust(test_cipher.hex()):
                original_byte = guess ^ c1[position] ^ padding_value
                candidates.append((guess, original_byte))
                print(f"    ✓ Candidato encontrado: guess={guess:02x} -> byte={original_byte:02x}")
        
        if len(candidates) == 1:
            return candidates[0][1]
        elif len(candidates) > 1:
            # Múltiples candidatos - necesitamos validar
            print(f"    ⚠️  {len(candidates)} candidatos, validando...")
            return self.validate_candidate(c1, c2, position, candidates, known_bytes)
        else:
            return None
    
    def validate_candidate(self, c1, c2, position, candidates, known_bytes):
        """Valida candidatos cuando hay múltiples opciones"""
        if position == 15:
            # Para el último byte, elegimos el que produce padding=1
            for guess, byte_val in candidates:
                if byte_val == 1:  # Padding de 1 byte
                    return byte_val
            # Si no hay byte=1, tomamos el primero
            return candidates[0][1]
        
        # Para otros bytes, probamos modificar el siguiente byte
        next_pos = position + 1
        next_padding = 16 - position + 1
        
        for guess, byte_val in candidates:
            # Configurar con este candidato
            modified_c1 = bytearray(c1)
            
            # Configurar bytes conocidos
            for i in range(position, 16):
                if i == position:
                    target_byte = byte_val ^ c1[i] ^ next_padding
                else:
                    target_byte = known_bytes[i] ^ c1[i] ^ next_padding
                modified_c1[i] = target_byte
            
            # Modificar el siguiente byte para romper el padding
            if next_pos < 16:
                modified_c1[next_pos] = (modified_c1[next_pos] + 1) % 256
            
            test_cipher = bytes(modified_c1) + c2
            
            # Si el padding se rompe, este candidato es válido
            if not self.check_padding_robust(test_cipher.hex()):
                return byte_val
        
        # Si no podemos validar, tomamos el primer candidato
        return candidates[0][1]
    
    def decrypt_block_robust(self, c1, c2, block_num):
        """Descifra un bloque con manejo robusto de errores"""
        print(f"\n🔓 Descifrando bloque {block_num} (robusto)...")
        
        decrypted = [0] * 16
        
        for pos in range(15, -1, -1):
            print(f"  📍 Posición {pos+1}/16...", end="", flush=True)
            
            byte_val = self.find_valid_padding_byte(c1, c2, pos, decrypted)
            
            if byte_val is not None:
                decrypted[pos] = byte_val
                char = chr(byte_val) if 32 <= byte_val <= 126 else '.'
                print(f" ✅ {byte_val:02x} ('{char}')")
            else:
                print(f" ❌ Falló - intentando continuar")
                # Ponemos un valor placeholder y continuamos
                decrypted[pos] = 0
        
        return bytes(decrypted)
    
    def attack_with_fallback(self, ciphertext):
        """Ataque con estrategias de fallback"""
        print(f"\n🎯 PADDING ORACLE ATTACK ROBUSTO")
        print(f"📏 Ciphertext: {len(ciphertext)} bytes")
        
        blocks = [ciphertext[i:i+16] for i in range(0, len(ciphertext), 16)]
        print(f"🔢 Bloques: {len(blocks)}")
        
        # Mostrar estructura
        for i, block in enumerate(blocks):
            if i == 0:
                print(f"📋 IV: {block.hex()}")
            else:
                print(f"📋 Bloque {i}: {block.hex()}")
        
        # Intentar descifrar solo el último bloque primero (suele tener la flag)
        print(f"\n🎯 Estrategia: empezar por el último bloque")
        
        if len(blocks) >= 2:
            last_block_idx = len(blocks) - 1
            prev_block = blocks[last_block_idx - 1]
            last_block = blocks[last_block_idx]
            
            print(f"🔓 Descifrando último bloque ({last_block_idx})...")
            decrypted_last = self.decrypt_block_robust(prev_block, last_block, last_block_idx)
            
            if decrypted_last:
                text = decrypted_last.decode('utf-8', errors='ignore')
                print(f"✅ Último bloque: '{text}'")
                
                # Si parece contener una flag, intentamos con otros bloques
                if any(keyword in text.lower() for keyword in ['n3xt', 'flag', 'ctf', '{']):
                    print("🎯 Posible flag detectada, descifrando otros bloques...")
                    
                    all_decrypted = [b''] * (len(blocks) - 1)
                    all_decrypted[-1] = decrypted_last
                    
                    # Descifrar otros bloques
                    for i in range(len(blocks) - 2, 0, -1):
                        prev_block = blocks[i-1]
                        current_block = blocks[i]
                        
                        decrypted = self.decrypt_block_robust(prev_block, current_block, i)
                        if decrypted:
                            all_decrypted[i-1] = decrypted
                    
                    # Construir mensaje completo
                    full_message = b''.join(all_decrypted)
                    
                    # Remover padding
                    if full_message and full_message[-1] <= 16:
                        padding_len = full_message[-1]
                        full_message = full_message[:-padding_len]
                    
                    return full_message
                else:
                    return decrypted_last
        
        return None
    
    def close(self):
        if self.socket:
            self.socket.close()

def main():
    print("🎯 PADDING ORACLE ATTACK - VERSIÓN ROBUSTA")
    print("=" * 50)
    print("🌐 Target: 185.207.251.177:1600")
    print("🎮 Challenge: chall.py")
    print()
    
    attacker = RobustPaddingOracle("185.207.251.177", 1600)
    
    try:
        prophecy = attacker.connect_and_get_prophecy()
        
        if prophecy is None:
            print("❌ No se pudo obtener prophecy")
            return
        
        print(f"📜 Prophecy: {prophecy.hex()}")
        print(f"📏 Longitud: {len(prophecy)} bytes")
        
        # Ejecutar ataque robusto
        flag = attacker.attack_with_fallback(prophecy)
        
        if flag:
            flag_text = flag.decode('utf-8', errors='ignore').strip()
            print(f"\n🎉 ¡POSIBLE FLAG DESCIFRADA!")
            print(f"🏆 FLAG: {flag_text}")
            
            # Guardar resultado
            solved_file = "challenges/solved/chall_padding_oracle_robust.txt"
            with open(solved_file, 'w', encoding='utf-8') as f:
                f.write(f"Challenge: chall.py (Padding Oracle Attack - Robust)\n")
                f.write(f"Host: 185.207.251.177:1600\n")
                f.write(f"Method: Robust Padding Oracle Attack\n")
                f.write(f"Prophecy: {prophecy.hex()}\n")
                f.write(f"Flag: {flag_text}\n")
                f.write(f"Raw bytes: {flag.hex()}\n")
            
            print(f"💾 Solución guardada en: {solved_file}")
            
            # Intentar submitir
            if flag_text and len(flag_text) > 4:
                print(f"\n📤 Submitting flag...")
                try:
                    submit_cmd = f"submit {flag_text}"
                    attacker.socket.sendall((submit_cmd + "\n").encode())
                    
                    time.sleep(2)
                    response = attacker.socket.recv(4096).decode('utf-8', errors='ignore')
                    print(f"📨 Respuesta: {response}")
                    
                except Exception as e:
                    print(f"⚠️  Error submitting: {e}")
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

if __name__ == "__main__":
    main()