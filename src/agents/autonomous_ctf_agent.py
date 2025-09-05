#!/usr/bin/env python3
"""
Autonomous CTF Agent - AI-Powered Challenge Solver
=================================================
Agente autónomo que combina el conocimiento Expert ML con modelos LLM
para resolver desafíos CTF de manera completamente automática
"""

import os
import json
import socket
import time
import subprocess
import tempfile
import re
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import google.generativeai as genai
from datetime import datetime

class AutonomousCTFAgent:
    def __init__(self, gemini_api_key: str = None):
        self.base_dir = Path("c:/Users/Nenaah/Desktop/Programacion/GIT/CRYPTO")
        self.knowledge_base = self.load_expert_knowledge()
        self.gemini_api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            print("✅ Gemini AI configurado exitosamente")
        else:
            print("⚠️  Gemini API key no encontrada. Usando modo offline.")
            self.model = None
        
        self.solved_challenges = []
        self.session_stats = {
            'challenges_attempted': 0,
            'challenges_solved': 0,
            'flags_found': [],
            'techniques_used': [],
            'start_time': datetime.now()
        }
    
    def load_expert_knowledge(self) -> Dict:
        """Carga la base de conocimiento Expert ML"""
        
        kb_file = self.base_dir / "framework/ml/knowledge_base.json"
        
        if kb_file.exists():
            with open(kb_file, 'r', encoding='utf-8') as f:
                knowledge = json.load(f)
                print(f"🧠 Knowledge Base cargada: {knowledge['writeups_count']} writeups")
                return knowledge
        else:
            print("⚠️  Knowledge Base no encontrada, usando conocimiento básico")
            return self._create_basic_knowledge()
    
    def _create_basic_knowledge(self) -> Dict:
        """Crea conocimiento básico de fallback"""
        return {
            'writeups_count': 0,
            'elliptic_curves': {'techniques': ['sage', 'python'], 'tools': ['sage']},
            'rsa': {'techniques': ['factorization', 'wiener'], 'attacks': []},
            'symmetric': {'techniques': ['xor', 'aes'], 'ciphers': ['xor']}
        }
    
    def analyze_challenge(self, challenge_input: str, challenge_type: str = "auto") -> Dict:
        """Analiza un desafío y determina la estrategia de resolución"""
        
        print(f"🔍 Analizando desafío...")
        
        analysis = {
            'input': challenge_input,
            'type': challenge_type,
            'detected_patterns': [],
            'suggested_techniques': [],
            'confidence': 0.0,
            'requires_network': False,
            'estimated_difficulty': 'medium'
        }
        
        # Análisis de patrones básicos
        if re.search(r'nc\s+[\w\.]+\s+\d+', challenge_input):
            analysis['requires_network'] = True
            analysis['detected_patterns'].append('network_challenge')
        
        if 'crypto{' in challenge_input or 'flag{' in challenge_input:
            analysis['detected_patterns'].append('flag_format')
        
        # Detectar tipo de criptografía
        crypto_indicators = {
            'rsa': ['rsa', 'public key', 'private key', 'modulus', 'exponent'],
            'elliptic_curve': ['elliptic', 'curve', 'point', 'ecdlp', 'sage'],
            'xor': ['xor', 'key', 'cipher', 'plaintext'],
            'caesar': ['caesar', 'shift', 'alphabet'],
            'base64': ['base64', 'encoding', 'decode'],
            'hash': ['hash', 'md5', 'sha', 'collision']
        }
        
        challenge_lower = challenge_input.lower()
        for crypto_type, indicators in crypto_indicators.items():
            if any(indicator in challenge_lower for indicator in indicators):
                analysis['detected_patterns'].append(crypto_type)
                analysis['suggested_techniques'].extend(
                    self.knowledge_base.get(crypto_type, {}).get('techniques', [])
                )
        
        # Calcular confianza
        if analysis['detected_patterns']:
            analysis['confidence'] = min(0.9, len(analysis['detected_patterns']) * 0.3)
        
        return analysis
    
    def generate_ai_solution(self, challenge: str, analysis: Dict) -> str:
        """Genera una solución usando Gemini AI"""
        
        if not self.model:
            return self._generate_offline_solution(challenge, analysis)
        
        print("🤖 Generando solución con Gemini AI...")
        
        # Crear prompt con conocimiento contextual
        prompt = self._create_expert_prompt(challenge, analysis)
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"⚠️  Error con Gemini AI: {e}")
            return self._generate_offline_solution(challenge, analysis)
    
    def _create_expert_prompt(self, challenge: str, analysis: Dict) -> str:
        """Crea un prompt experto usando el conocimiento acumulado"""
        
        # Extraer técnicas relevantes del knowledge base
        relevant_techniques = []
        for pattern in analysis['detected_patterns']:
            if pattern in self.knowledge_base:
                relevant_techniques.extend(
                    self.knowledge_base[pattern].get('techniques', [])
                )
        
        prompt = f"""
You are an expert CTF cryptography solver with access to a vast knowledge base of {self.knowledge_base['writeups_count']} professional writeups and solutions.

CHALLENGE TO SOLVE:
{challenge}

ANALYSIS RESULTS:
- Detected patterns: {analysis['detected_patterns']}
- Suggested techniques: {analysis['suggested_techniques']}
- Requires network: {analysis['requires_network']}
- Confidence: {analysis['confidence']}

EXPERT KNOWLEDGE AVAILABLE:
- Elliptic Curves: {self.knowledge_base.get('elliptic_curves', {}).get('techniques', [])}
- RSA Techniques: {self.knowledge_base.get('rsa', {}).get('techniques', [])}
- Symmetric Crypto: {self.knowledge_base.get('symmetric', {}).get('techniques', [])}

INSTRUCTIONS:
1. Analyze the challenge using the expert knowledge base
2. Generate complete Python code to solve it
3. If it requires network connection (nc), handle socket communication
4. Include all necessary imports and error handling
5. Return the flag in format: crypto{{...}} or flag{{...}}
6. Make the code executable and self-contained

IMPORTANT PATTERNS FROM EXPERT WRITEUPS:
- For elliptic curves: Use Sage for complex operations
- For RSA: Check for small exponents, factor large numbers
- For XOR: Use known plaintext attacks when possible
- For network challenges: Implement robust socket handling

Generate the complete Python solution code:
"""
        
        return prompt
    
    def _generate_offline_solution(self, challenge: str, analysis: Dict) -> str:
        """Genera solución usando templates offline"""
        
        print("🔧 Generando solución offline con templates...")
        
        if 'rsa' in analysis['detected_patterns']:
            return self._generate_rsa_template(challenge)
        elif 'xor' in analysis['detected_patterns']:
            return self._generate_xor_template(challenge)
        elif 'elliptic_curve' in analysis['detected_patterns']:
            return self._generate_ec_template(challenge)
        elif analysis['requires_network']:
            return self._generate_network_template(challenge)
        else:
            return self._generate_generic_template(challenge)
    
    def _generate_rsa_template(self, challenge: str) -> str:
        """Template para desafíos RSA"""
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import gmpy2
from Crypto.Util.number import *
import sympy

def solve_rsa_challenge():
    """RSA Challenge Solver usando técnicas del Expert ML"""
    
    # Extraer parámetros del desafío
    # TODO: Parse challenge parameters (n, e, c)
    
    # Técnicas RSA del knowledge base:
    # 1. Factorización
    # 2. Wiener attack
    # 3. Small exponent attack
    
    try:
        # Método 1: Factorización directa
        # factors = factor_n(n)
        
        # Método 2: Wiener attack si e es grande
        # if e > n**0.5:
        #     d = wiener_attack(n, e)
        
        # Método 3: Small exponent
        # if e == 3:
        #     m = gmpy2.iroot(c, 3)[0]
        
        # Decodificar mensaje
        # flag = long_to_bytes(m).decode()
        # return flag
        
        pass
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    result = solve_rsa_challenge()
    if result:
        print(f"Flag: {result}")
'''
    
    def _generate_xor_template(self, challenge: str) -> str:
        """Template para desafíos XOR"""
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
def solve_xor_challenge():
    """XOR Challenge Solver usando técnicas del Expert ML"""
    
    # Datos del desafío
    encrypted_data = ""  # TODO: Extract from challenge
    
    # Técnicas XOR del knowledge base:
    # 1. Known plaintext attack
    # 2. Frequency analysis
    # 3. Key length detection
    
    try:
        # Método 1: Known plaintext (crypto{, flag{)
        known_starts = [b"crypto{", b"flag{", b"CTF{"]
        
        for known in known_starts:
            # Try single-byte XOR
            for key_byte in range(256):
                decrypted = bytes(b ^ key_byte for b in encrypted_data)
                if decrypted.startswith(known):
                    try:
                        flag = decrypted.decode('utf-8')
                        if flag.endswith('}'):
                            return flag
                    except:
                        continue
        
        # Método 2: Multi-byte key
        # Implement key length detection and cryptanalysis
        
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    result = solve_xor_challenge()
    if result:
        print(f"Flag: {result}")
'''
    
    def _generate_ec_template(self, challenge: str) -> str:
        """Template para curvas elípticas"""
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
try:
    from sage.all import *
except ImportError:
    print("Sage not available, using basic implementation")

def solve_elliptic_curve_challenge():
    """Elliptic Curve Challenge Solver usando técnicas del Expert ML"""
    
    # Técnicas EC del knowledge base:
    # 1. Scalar multiplication (Double and Add)
    # 2. ECDLP solving
    # 3. Smart attacks
    # 4. Point operations
    
    try:
        # TODO: Extract curve parameters (p, a, b, G, etc.)
        
        # Usar Sage si está disponible
        if 'sage' in globals():
            # E = EllipticCurve(GF(p), [a, b])
            # G = E(Gx, Gy)
            # result = scalar_multiply(n, G)
            pass
        else:
            # Implementación manual
            pass
        
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    result = solve_elliptic_curve_challenge()
    if result:
        print(f"Flag: {result}")
'''
    
    def _generate_network_template(self, challenge: str) -> str:
        """Template para desafíos de red"""
        
        # Extraer host y puerto
        nc_match = re.search(r'nc\s+([\w\.-]+)\s+(\d+)', challenge)
        
        if nc_match:
            host, port = nc_match.groups()
        else:
            host, port = "localhost", "1337"
        
        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import time
import re

def solve_network_challenge():
    """Network Challenge Solver usando técnicas del Expert ML"""
    
    host = "{host}"
    port = {port}
    
    try:
        print(f"Conectando a {{host}}:{{port}}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.connect((host, port))
        
        # Leer respuesta inicial
        initial_response = sock.recv(4096).decode('utf-8', errors='ignore')
        print(f"Respuesta inicial: {{initial_response}}")
        
        # Buscar flag en respuesta inicial
        flag_match = re.search(r'(crypto|flag|CTF){{[^}}]+}}', initial_response, re.IGNORECASE)
        if flag_match:
            return flag_match.group(0)
        
        # Interacción automática basada en patrones comunes
        common_inputs = ["1", "A", "admin", "flag", "help", "?"]
        
        for input_cmd in common_inputs:
            try:
                sock.send((input_cmd + "\\n").encode())
                time.sleep(1)
                response = sock.recv(4096).decode('utf-8', errors='ignore')
                print(f"Input: {{input_cmd}} -> Response: {{response[:100]}}...")
                
                # Buscar flag en respuesta
                flag_match = re.search(r'(crypto|flag|CTF){{[^}}]+}}', response, re.IGNORECASE)
                if flag_match:
                    return flag_match.group(0)
                    
            except Exception as e:
                print(f"Error con input {{input_cmd}}: {{e}}")
                continue
        
        sock.close()
        return None
        
    except Exception as e:
        print(f"Error de conexión: {{e}}")
        return None

if __name__ == "__main__":
    result = solve_network_challenge()
    if result:
        print(f"Flag: {{result}}")
'''
    
    def _generate_generic_template(self, challenge: str) -> str:
        """Template genérico"""
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.number import *

def solve_generic_challenge():
    """Generic Challenge Solver usando técnicas del Expert ML"""
    
    challenge_text = """''' + challenge + '''"""
    
    # Buscar flags ya presentes
    flag_patterns = [
        r'crypto\\{[^}]+\\}',
        r'flag\\{[^}]+\\}',
        r'CTF\\{[^}]+\\}'
    ]
    
    for pattern in flag_patterns:
        match = re.search(pattern, challenge_text, re.IGNORECASE)
        if match:
            return match.group(0)
    
    # Decodificación automática
    try:
        # Base64
        if re.search(r'[A-Za-z0-9+/]{20,}={0,2}', challenge_text):
            decoded = base64.b64decode(challenge_text).decode('utf-8', errors='ignore')
            for pattern in flag_patterns:
                match = re.search(pattern, decoded, re.IGNORECASE)
                if match:
                    return match.group(0)
    except:
        pass
    
    return None

if __name__ == "__main__":
    result = solve_generic_challenge()
    if result:
        print(f"Flag: {result}")
'''
    
    def execute_solution(self, solution_code: str) -> Optional[str]:
        """Ejecuta el código de solución y extrae la flag"""
        
        print("⚙️  Ejecutando solución generada...")
        
        try:
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(solution_code)
                temp_file = f.name
            
            # Ejecutar código
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.base_dir)
            )
            
            # Limpiar archivo temporal
            os.unlink(temp_file)
            
            if result.returncode == 0:
                output = result.stdout
                print(f"✅ Ejecución exitosa:\n{output}")
                
                # Extraer flag del output
                flag_match = re.search(r'(crypto|flag|CTF)\{[^}]+\}', output, re.IGNORECASE)
                if flag_match:
                    return flag_match.group(0)
                else:
                    print("⚠️  No se encontró flag en el output")
                    return None
            else:
                print(f"❌ Error en ejecución:\n{result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("⏰ Timeout en ejecución")
            return None
        except Exception as e:
            print(f"❌ Error ejecutando solución: {e}")
            return None
    
    def solve_challenge_autonomous(self, challenge_input: str, challenge_name: str = None) -> Dict:
        """Resuelve un desafío de manera completamente autónoma"""
        
        challenge_name = challenge_name or f"challenge_{len(self.solved_challenges) + 1}"
        
        print(f"\n🎯 RESOLVIENDO DESAFÍO AUTÓNOMO: {challenge_name}")
        print("=" * 60)
        
        start_time = time.time()
        self.session_stats['challenges_attempted'] += 1
        
        # 1. Análisis del desafío
        analysis = self.analyze_challenge(challenge_input)
        print(f"📊 Análisis completado: {analysis['detected_patterns']}")
        
        # 2. Generación de solución con IA
        solution_code = self.generate_ai_solution(challenge_input, analysis)
        print(f"🤖 Solución generada ({len(solution_code)} caracteres)")
        
        # 3. Ejecución de la solución
        flag = self.execute_solution(solution_code)
        
        # 4. Resultado
        elapsed_time = time.time() - start_time
        
        result = {
            'challenge_name': challenge_name,
            'input': challenge_input,
            'analysis': analysis,
            'solution_code': solution_code,
            'flag': flag,
            'solved': flag is not None,
            'execution_time': elapsed_time,
            'timestamp': datetime.now().isoformat()
        }
        
        if flag:
            print(f"🏆 DESAFÍO RESUELTO: {flag}")
            self.session_stats['challenges_solved'] += 1
            self.session_stats['flags_found'].append(flag)
            self.session_stats['techniques_used'].extend(analysis['suggested_techniques'])
            
            # Guardar solución
            self.save_solution(result)
        else:
            print(f"❌ Desafío no resuelto")
        
        self.solved_challenges.append(result)
        return result
    
    def save_solution(self, result: Dict):
        """Guarda la solución en el directorio de solved"""
        
        solved_dir = self.base_dir / "challenges/solved"
        solved_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"autonomous_{result['challenge_name']}_{timestamp}.txt"
        filepath = solved_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"AUTONOMOUS SOLUTION - {result['challenge_name']}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Timestamp: {result['timestamp']}\n")
            f.write(f"Execution Time: {result['execution_time']:.2f}s\n")
            f.write(f"Flag: {result['flag']}\n")
            f.write(f"Detected Patterns: {result['analysis']['detected_patterns']}\n\n")
            f.write("ORIGINAL CHALLENGE:\n")
            f.write("-" * 20 + "\n")
            f.write(result['input'] + "\n\n")
            f.write("GENERATED SOLUTION:\n")
            f.write("-" * 20 + "\n")
            f.write(result['solution_code'] + "\n")
        
        print(f"💾 Solución guardada: {filepath}")
    
    def print_session_stats(self):
        """Muestra estadísticas de la sesión"""
        
        elapsed = datetime.now() - self.session_stats['start_time']
        success_rate = (self.session_stats['challenges_solved'] / 
                       max(1, self.session_stats['challenges_attempted'])) * 100
        
        print(f"\n📊 ESTADÍSTICAS DE SESIÓN AUTÓNOMA")
        print("=" * 40)
        print(f"⏱️  Tiempo total: {elapsed}")
        print(f"🎯 Desafíos intentados: {self.session_stats['challenges_attempted']}")
        print(f"✅ Desafíos resueltos: {self.session_stats['challenges_solved']}")
        print(f"📈 Tasa de éxito: {success_rate:.1f}%")
        print(f"🏆 Flags encontradas: {len(self.session_stats['flags_found'])}")
        
        if self.session_stats['flags_found']:
            print(f"\n🏆 FLAGS ENCONTRADAS:")
            for i, flag in enumerate(self.session_stats['flags_found'], 1):
                print(f"   {i}. {flag}")

def main():
    """Función principal para demostrar el agente autónomo"""
    
    print("🤖 AUTONOMOUS CTF AGENT - AI-POWERED SOLVER")
    print("=" * 50)
    print("🎯 Combinando Expert ML Knowledge + Gemini AI")
    print()
    
    # Inicializar agente
    agent = AutonomousCTFAgent()
    
    # Ejemplos de desafíos para probar
    test_challenges = [
        {
            'name': 'xor_simple',
            'content': '''
Challenge: Simple XOR
The flag has been XOR encrypted with a single byte key.
Encrypted (hex): 63727970746f7b4a4f495f5a4f527d
Hint: The flag starts with "crypto{"
'''
        },
        {
            'name': 'network_test',
            'content': '''
Challenge: Connect to the server
nc challenges.example.com 1337
The server will give you the flag directly.
'''
        },
        {
            'name': 'base64_simple',
            'content': '''
Challenge: Decode this
Y3J5cHRve2Jhc2U2NF9pc19lYXN5fQ==
'''
        }
    ]
    
    # Resolver desafíos de prueba
    for challenge in test_challenges:
        result = agent.solve_challenge_autonomous(
            challenge['content'], 
            challenge['name']
        )
        time.sleep(2)  # Pausa entre desafíos
    
    # Mostrar estadísticas finales
    agent.print_session_stats()
    
    print(f"\n🎉 SESIÓN AUTÓNOMA COMPLETADA")
    print(f"🚀 El agente está listo para resolver desafíos reales!")

if __name__ == "__main__":
    main()