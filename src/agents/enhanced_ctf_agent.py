#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced CTF Agent - Agente CTF Mejorado con Interpretación Inteligente
=====================================================================
Versión mejorada del agente autónomo que integra el Knowledge Interpreter
para una mejor conexión entre los datos de entrenamiento y las soluciones.
"""

import os
import sys
import json
import socket
import subprocess
import tempfile
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Agregar el directorio src al path para imports
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from src.ml.knowledge_interpreter import KnowledgeInterpreter
    print("✅ Knowledge Interpreter importado exitosamente")
except ImportError as e:
    print(f"⚠️  Error importando Knowledge Interpreter: {e}")
    print("Usando modo básico sin interpretación avanzada")

class EnhancedCTFAgent:
    def __init__(self, api_key: str = None):
        self.base_dir = Path("c:/Users/Nenaah/Desktop/Programacion/GIT/CRYPTO")
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        # Inicializar Knowledge Interpreter
        try:
            self.knowledge_interpreter = KnowledgeInterpreter(str(self.base_dir))
            print("🧠 Knowledge Interpreter inicializado")
            self._show_knowledge_stats()
        except Exception as e:
            print(f"⚠️  Error inicializando Knowledge Interpreter: {e}")
            self.knowledge_interpreter = None
        
        # Configurar IA si está disponible
        self.ai_model = None
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.ai_model = genai.GenerativeModel('gemini-1.5-pro')
                print("✅ Gemini AI configurado")
            except Exception as e:
                print(f"⚠️  Error configurando Gemini: {e}")
        
        # Estadísticas de sesión
        self.session_stats = {
            'challenges_attempted': 0,
            'challenges_solved': 0,
            'flags_found': [],
            'techniques_used': [],
            'interpretations_successful': 0,
            'start_time': datetime.now()
        }
    
    def _show_knowledge_stats(self):
        """Muestra estadísticas del conocimiento cargado"""
        if self.knowledge_interpreter:
            stats = self.knowledge_interpreter.get_knowledge_stats()
            print(f"📊 Knowledge Stats:")
            print(f"   • Challenges procesados: {stats['total_challenges_processed']}")
            print(f"   • Categorías de patrones: {stats['pattern_categories']}")
            print(f"   • Técnicas analizadas: {stats['technique_count']}")
            print(f"   • Templates disponibles: {stats['solution_templates']}")
            
            if stats['top_techniques']:
                print(f"   • Top 3 técnicas más efectivas:")
                for i, tech in enumerate(stats['top_techniques'][:3]):
                    print(f"     {i+1}. {tech['technique']} (efectividad: {tech['effectiveness']:.2f})")
    
    def solve_challenge_enhanced(self, challenge_input: str, challenge_type: str = "auto") -> Dict:
        """
        Resuelve un desafío usando interpretación inteligente de conocimiento
        """
        
        print(f"\n🚀 === ENHANCED CTF SOLVER ===")
        print(f"Challenge Type: {challenge_type}")
        print(f"Input: {challenge_input[:100]}{'...' if len(challenge_input) > 100 else ''}")
        
        self.session_stats['challenges_attempted'] += 1
        
        result = {
            'success': False,
            'flag': None,
            'method': 'unknown',
            'confidence': 0.0,
            'execution_time': 0,
            'interpretation': None,
            'generated_code': None,
            'error': None
        }
        
        start_time = datetime.now()
        
        try:
            # Paso 1: Interpretación inteligente del desafío
            print("\n🔍 Paso 1: Interpretación inteligente...")
            interpretation = self._interpret_challenge_smart(challenge_input)
            result['interpretation'] = interpretation
            
            if interpretation:
                self.session_stats['interpretations_successful'] += 1
                print(f"✅ Interpretación exitosa:")
                print(f"   • Tipo: {interpretation['challenge_type']}")
                print(f"   • Confianza: {interpretation['confidence']:.2f}")
                print(f"   • Técnicas recomendadas: {[t['technique'] for t in interpretation['recommended_techniques'][:3]]}")
            
            # Paso 2: Generación de solución basada en interpretación
            print("\n🛠️  Paso 2: Generación de solución...")
            generated_code = self._generate_solution_smart(challenge_input, interpretation)
            result['generated_code'] = generated_code
            
            # Paso 3: Ejecución de la solución
            print("\n⚡ Paso 3: Ejecutando solución...")
            execution_result = self._execute_solution_safe(generated_code)
            
            if execution_result['success']:
                result['success'] = True
                result['flag'] = execution_result['output']
                result['method'] = 'enhanced_interpretation'
                result['confidence'] = interpretation['confidence'] if interpretation else 0.5
                
                self.session_stats['challenges_solved'] += 1
                self.session_stats['flags_found'].append(execution_result['output'])
                
                print(f"🎉 ¡FLAG ENCONTRADA!")
                print(f"🏁 FLAG: {execution_result['output']}")
            else:
                result['error'] = execution_result.get('error', 'Ejecución fallida')
                print(f"❌ Error en ejecución: {result['error']}")
                
                # Fallback: Intentar métodos simples
                print("\n🔄 Intentando métodos de fallback...")
                fallback_result = self._try_fallback_methods(challenge_input)
                if fallback_result['success']:
                    result.update(fallback_result)
                    result['method'] = 'fallback'
        
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Error general: {e}")
        
        # Calcular tiempo de ejecución
        result['execution_time'] = (datetime.now() - start_time).total_seconds()
        
        return result
    
    def _interpret_challenge_smart(self, challenge_input: str) -> Optional[Dict]:
        """Interpreta el desafío usando el Knowledge Interpreter"""
        
        if not self.knowledge_interpreter:
            print("⚠️  Knowledge Interpreter no disponible")
            return None
        
        try:
            interpretation = self.knowledge_interpreter.interpret_challenge(challenge_input)
            return interpretation
        except Exception as e:
            print(f"❌ Error en interpretación: {e}")
            return None
    
    def _generate_solution_smart(self, challenge_input: str, interpretation: Optional[Dict]) -> str:
        """Genera solución usando interpretación inteligente"""
        
        if not interpretation:
            return self._generate_basic_solution(challenge_input)
        
        try:
            # Usar Knowledge Interpreter para generar código mejorado
            if self.knowledge_interpreter:
                enhanced_code = self.knowledge_interpreter.generate_enhanced_solution_code(
                    interpretation, challenge_input
                )
                return enhanced_code
            else:
                return self._generate_template_solution(interpretation, challenge_input)
        
        except Exception as e:
            print(f"⚠️  Error generando solución inteligente: {e}")
            return self._generate_basic_solution(challenge_input)
    
    def _generate_template_solution(self, interpretation: Dict, challenge_input: str) -> str:
        """Genera solución basada en templates de interpretación"""
        
        challenge_type = interpretation.get('challenge_type', 'unknown')
        
        if challenge_type == 'elliptic_curve':
            return self._generate_ec_solution(challenge_input, interpretation)
        elif challenge_type == 'rsa':
            return self._generate_rsa_solution(challenge_input, interpretation)
        elif challenge_type == 'xor':
            return self._generate_xor_solution(challenge_input, interpretation)
        else:
            return self._generate_basic_solution(challenge_input)
    
    def _generate_ec_solution(self, challenge_input: str, interpretation: Dict) -> str:
        """Genera solución específica para curvas elípticas"""
        
        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Solución automática para Elliptic Curves
# Basada en interpretación: {interpretation['challenge_type']}
# Confianza: {interpretation['confidence']:.2f}

def solve_elliptic_curve():
    import re
    import hashlib
    
    challenge_text = """{challenge_input}"""
    
    # Buscar flags directamente
    flag_pattern = r"crypto\\{{[^}}]+\\}}|flag\\{{[^}}]+\\}}"
    flags = re.findall(flag_pattern, challenge_text)
    if flags:
        return flags[0]
    
    try:
        # Configuración Sage si está disponible
        from sage.all import *
        
        # Parámetros comunes de CryptoHack
        p = 9739
        E = EllipticCurve(GF(p), [497, 1768])
        
        # Buscar puntos en el texto
        point_pattern = r"\\((\\d+),\\s*(\\d+)\\)"
        points = re.findall(point_pattern, challenge_text)
        
        if points:
            x, y = int(points[0][0]), int(points[0][1])
            P = E(x, y)
            
            # Operaciones comunes
            # Negación: -P
            result = -P
            print(f"Negación: {{result}}")
            
            # Multiplicación escalar si hay número
            numbers = re.findall(r'\\b(\\d{{4,}})\\b', challenge_text)
            if numbers:
                scalar = int(numbers[0])
                result = scalar * P
                print(f"Multiplicación {{scalar}} * P = {{result}}")
            
            # Hash SHA1 de coordenada x
            x_coord = int(result[0])
            flag_hash = hashlib.sha1(str(x_coord).encode()).hexdigest()
            return f"crypto{{{flag_hash}}}"
    
    except ImportError:
        print("Sage no disponible, usando métodos básicos")
    except Exception as e:
        print(f"Error en cálculo EC: {{e}}")
    
    return "Flag no encontrada"

if __name__ == "__main__":
    result = solve_elliptic_curve()
    print(f"FLAG: {{result}}")
'''
    
    def _generate_rsa_solution(self, challenge_input: str, interpretation: Dict) -> str:
        """Genera solución específica para RSA"""
        
        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Solución automática para RSA
# Basada en interpretación: {interpretation['challenge_type']}

def solve_rsa():
    import re
    from math import gcd
    
    challenge_text = """{challenge_input}"""
    
    # Buscar flags directamente
    flag_pattern = r"crypto\\{{[^}}]+\\}}|flag\\{{[^}}]+\\}}"
    flags = re.findall(flag_pattern, challenge_text)
    if flags:
        return flags[0]
    
    try:
        # Buscar parámetros RSA
        numbers = re.findall(r'\\b(\\d{{10,}})\\b', challenge_text)
        
        if len(numbers) >= 2:
            n = int(numbers[0])
            e = int(numbers[1])
            
            print(f"n = {{n}}")
            print(f"e = {{e}}")
            
            # Intentar factorización simple
            import gmpy2
            
            # Verificar si n es pequeño
            if n < 10**20:
                for i in range(2, int(n**0.5) + 1):
                    if n % i == 0:
                        p, q = i, n // i
                        phi = (p - 1) * (q - 1)
                        d = gmpy2.invert(e, phi)
                        print(f"Factorización encontrada: p={{p}}, q={{q}}")
                        print(f"d = {{d}}")
                        break
        
    except Exception as e:
        print(f"Error en RSA: {{e}}")
    
    return "Flag no encontrada"

if __name__ == "__main__":
    result = solve_rsa()
    print(f"FLAG: {{result}}")
'''
    
    def _generate_xor_solution(self, challenge_input: str, interpretation: Dict) -> str:
        """Genera solución específica para XOR"""
        
        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Solución automática para XOR
# Basada en interpretación: {interpretation['challenge_type']}

def solve_xor():
    import re
    
    challenge_text = """{challenge_input}"""
    
    # Buscar flags directamente
    flag_pattern = r"crypto\\{{[^}}]+\\}}|flag\\{{[^}}]+\\}}"
    flags = re.findall(flag_pattern, challenge_text)
    if flags:
        return flags[0]
    
    try:
        # Buscar datos hex
        hex_pattern = r'[0-9a-fA-F]{{20,}}'
        hex_data = re.findall(hex_pattern, challenge_text)
        
        for hex_str in hex_data:
            if len(hex_str) % 2 == 0:
                data = bytes.fromhex(hex_str)
                
                # XOR con keys comunes
                common_keys = [b'flag', b'key', b'crypto', b'A', b'\\x00']
                
                for key in common_keys:
                    try:
                        result = bytes(a ^ key[i % len(key)] for i, a in enumerate(data))
                        result_str = result.decode('utf-8', errors='ignore')
                        
                        if 'crypto{{' in result_str or 'flag{{' in result_str:
                            flag_match = re.search(flag_pattern, result_str)
                            if flag_match:
                                return flag_match.group(0)
                    except:
                        continue
    
    except Exception as e:
        print(f"Error en XOR: {{e}}")
    
    return "Flag no encontrada"

if __name__ == "__main__":
    result = solve_xor()
    print(f"FLAG: {{result}}")
'''
    
    def _generate_basic_solution(self, challenge_input: str) -> str:
        """Genera solución básica cuando no hay interpretación específica"""
        
        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Solución básica automática

def solve_basic():
    import re
    import base64
    
    challenge_text = """{challenge_input}"""
    
    # 1. Buscar flags directamente
    flag_pattern = r"crypto\\{{[^}}]+\\}}|flag\\{{[^}}]+\\}}"
    flags = re.findall(flag_pattern, challenge_text)
    if flags:
        return flags[0]
    
    # 2. Decodificación Base64
    try:
        b64_pattern = r'[A-Za-z0-9+/]{{20,}}=*'
        b64_matches = re.findall(b64_pattern, challenge_text)
        for b64_str in b64_matches:
            try:
                decoded = base64.b64decode(b64_str).decode('utf-8')
                flag_in_decoded = re.findall(flag_pattern, decoded)
                if flag_in_decoded:
                    return flag_in_decoded[0]
            except:
                continue
    except:
        pass
    
    return "Flag no encontrada"

if __name__ == "__main__":
    result = solve_basic()
    print(f"FLAG: {{result}}")
'''
    
    def _execute_solution_safe(self, code: str) -> Dict:
        """Ejecuta la solución de manera segura"""
        
        try:
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Ejecutar con timeout
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Limpiar archivo temporal
            os.unlink(temp_file)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                # Extraer flag del output
                flag_match = re.search(r'FLAG: (.+)', output)
                if flag_match:
                    return {'success': True, 'output': flag_match.group(1)}
                else:
                    return {'success': True, 'output': output}
            else:
                return {'success': False, 'error': result.stderr}
        
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Timeout en ejecución'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _try_fallback_methods(self, challenge_input: str) -> Dict:
        """Métodos de fallback cuando falla la interpretación principal"""
        
        print("🔄 Intentando métodos de fallback...")
        
        # Método 1: Búsqueda directa de flags
        flag_pattern = r'crypto\{[^}]+\}|flag\{[^}]+\}'
        flags = re.findall(flag_pattern, challenge_input, re.IGNORECASE)
        if flags:
            return {'success': True, 'flag': flags[0], 'method': 'direct_search'}
        
        # Método 2: Base64 decode
        try:
            import base64
            b64_pattern = r'[A-Za-z0-9+/]{20,}=*'
            b64_matches = re.findall(b64_pattern, challenge_input)
            for b64_str in b64_matches:
                try:
                    decoded = base64.b64decode(b64_str).decode('utf-8')
                    flag_in_decoded = re.findall(flag_pattern, decoded, re.IGNORECASE)
                    if flag_in_decoded:
                        return {'success': True, 'flag': flag_in_decoded[0], 'method': 'base64_decode'}
                except:
                    continue
        except:
            pass
        
        return {'success': False, 'error': 'Todos los métodos de fallback fallaron'}
    
    def get_session_summary(self) -> Dict:
        """Retorna resumen de la sesión actual"""
        
        duration = (datetime.now() - self.session_stats['start_time']).total_seconds()
        
        return {
            'session_duration_seconds': duration,
            'challenges_attempted': self.session_stats['challenges_attempted'],
            'challenges_solved': self.session_stats['challenges_solved'],
            'success_rate': self.session_stats['challenges_solved'] / max(self.session_stats['challenges_attempted'], 1),
            'interpretations_successful': self.session_stats['interpretations_successful'],
            'flags_found': self.session_stats['flags_found'],
            'techniques_used': list(set(self.session_stats['techniques_used']))
        }

# Función de conveniencia para uso directo
def solve_ctf_challenge(challenge_input: str, api_key: str = None) -> Dict:
    """
    Función conveniente para resolver un desafío CTF
    """
    agent = EnhancedCTFAgent(api_key=api_key)
    return agent.solve_challenge_enhanced(challenge_input)

if __name__ == "__main__":
    # Ejemplo de uso
    test_challenge = """
    Challenge: CryptoHack Base64
    
    Can you decode this?
    Y3J5cHRve2Jhc2U2NF9pc19lYXN5fQ==
    """
    
    print("🧪 Probando Enhanced CTF Agent...")
    agent = EnhancedCTFAgent()
    result = agent.solve_challenge_enhanced(test_challenge)
    
    print(f"\n📊 Resultado:")
    print(f"✅ Éxito: {result['success']}")
    if result['success']:
        print(f"🏁 Flag: {result['flag']}")
        print(f"🛠️  Método: {result['method']}")
        print(f"📈 Confianza: {result['confidence']:.2f}")
    else:
        print(f"❌ Error: {result['error']}")
    
    print(f"\n⏱️  Tiempo de ejecución: {result['execution_time']:.2f}s")
    
    # Mostrar resumen de sesión
    summary = agent.get_session_summary()
    print(f"\n📈 Resumen de sesión:")
    print(f"   • Challenges intentados: {summary['challenges_attempted']}")
    print(f"   • Challenges resueltos: {summary['challenges_solved']}")
    print(f"   • Tasa de éxito: {summary['success_rate']:.2f}")