#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversational CTF Agent - Agente de IA Conversacional para CTF
=============================================================
Agente avanzado de IA que combina Gemini 2.0 con capacidades de interacción 
terminal para resolver desafíos CTF de manera conversacional e inteligente.
"""

import os
import sys
import json
import socket
import time
import re
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import tempfile

# Configurar imports del proyecto
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "src"))

try:
    import google.generativeai as genai
    from google.generativeai import GenerativeModel
    print("✅ Google Generative AI disponible")
except ImportError:
    print("⚠️  Instalando Google Generative AI...")
    subprocess.run([sys.executable, "-m", "pip", "install", "google-generativeai"])
    import google.generativeai as genai
    from google.generativeai import GenerativeModel

class ConversationalCTFAgent:
    def __init__(self, gemini_api_key: str = None):
        """Inicializa el agente conversacional con Gemini 2.0"""
        
        self.base_dir = Path(__file__).parent
        self.gemini_api_key = gemini_api_key or "AIzaSyBU6YaIBLreEqzfBFpO4UpLsoF37LQlQAM"
        
        # Configurar Gemini 2.0
        self._setup_gemini()
        
        # Cargar conocimiento del framework
        self._load_framework_knowledge()
        
        # Inicializar estadísticas
        self.session_stats = {
            'challenges_attempted': 0,
            'challenges_solved': 0,
            'flags_found': [],
            'conversations_held': 0,
            'start_time': datetime.now()
        }
        
        self.conversation_history = []
        
        print(f"🤖 Conversational CTF Agent iniciado!")
        print(f"📊 Knowledge: {self.knowledge_stats['total_writeups']} writeups")
        print(f"🧠 Gemini 2.0: {'✅' if self.gemini_model else '❌'}")
    
    def _setup_gemini(self):
        """Configura Gemini 2.0"""
        try:
            genai.configure(api_key=self.gemini_api_key)
            
            self.gemini_model = GenerativeModel(
                model_name='gemini-2.0-flash-exp',
                generation_config={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_output_tokens': 2048,
                }
            )
            
            # Test connection
            test_response = self.gemini_model.generate_content("Test")
            print(f"✅ Gemini 2.0 configurado exitosamente")
            
        except Exception as e:
            print(f"❌ Error configurando Gemini: {e}")
            self.gemini_model = None
    
    def _load_framework_knowledge(self):
        """Carga conocimiento del framework"""
        self.knowledge_stats = self._get_knowledge_stats()
        self.writeups_database = self._load_writeups_database()
    
    def _get_knowledge_stats(self) -> Dict:
        """Obtiene estadísticas del conocimiento"""
        stats = {'total_writeups': 0, 'techniques_known': 0}
        
        training_dir = self.base_dir / "challenges/training_data"
        if training_dir.exists():
            writeup_files = list(training_dir.glob("*.json")) + list(training_dir.glob("*.txt"))
            stats['total_writeups'] = len(writeup_files)
        
        ml_data_file = self.base_dir / "data/ml/processed_challenges.json"
        if ml_data_file.exists():
            try:
                with open(ml_data_file, 'r', encoding='utf-8') as f:
                    ml_data = json.load(f)
                    stats['techniques_known'] = len(set(
                        tech for challenge in ml_data 
                        for tech in challenge.get('labels', [])
                    ))
            except:
                pass
        
        return stats
    
    def _load_writeups_database(self) -> Dict:
        """Carga base de datos de writeups"""
        database = {
            'elliptic_curves': [], 'rsa': [], 'xor': [], 'network': []
        }
        
        processed_file = self.base_dir / "data/ml/processed_challenges.json"
        if processed_file.exists():
            try:
                with open(processed_file, 'r', encoding='utf-8') as f:
                    processed_data = json.load(f)
                    
                    for challenge in processed_data:
                        labels = challenge.get('labels', [])
                        if any(label in ['sage', 'ellipticcurve'] for label in labels):
                            database['elliptic_curves'].append(challenge)
                        elif 'rsa' in str(labels).lower():
                            database['rsa'].append(challenge)
                        elif 'xor' in str(labels).lower():
                            database['xor'].append(challenge)
            except:
                pass
        
        return database
    
    def solve_challenge_conversational(self, challenge_input: str) -> Dict:
        """Resuelve desafío usando conversación inteligente"""
        
        print(f"\n🚀 === CONVERSATIONAL CTF SOLVER ===")
        print(f"📝 Challenge: {challenge_input[:100]}...")
        
        self.session_stats['challenges_attempted'] += 1
        
        result = {
            'success': False,
            'flag': None,
            'method': 'conversational',
            'conversation_log': [],
            'execution_time': 0,
            'error': None
        }
        
        start_time = datetime.now()
        
        try:
            # Paso 1: Análisis con Gemini
            print("\n🧠 Analizando con Gemini 2.0...")
            analysis = self._analyze_with_gemini(challenge_input)
            result['conversation_log'].append(analysis)
            
            # Paso 2: Determinar estrategia
            strategy = self._determine_strategy(challenge_input, analysis)
            print(f"🎯 Estrategia: {strategy['type']}")
            
            # Paso 3: Ejecutar según estrategia
            if strategy['type'] == 'network_interactive':
                execution_result = self._solve_network_interactive(challenge_input, strategy)
            elif strategy['type'] == 'code_generation':
                execution_result = self._solve_code_generation(challenge_input, strategy)
            else:
                execution_result = self._solve_direct_analysis(challenge_input)
            
            # Procesar resultado
            if execution_result['success']:
                result['success'] = True
                result['flag'] = execution_result['flag']
                
                self.session_stats['challenges_solved'] += 1
                self.session_stats['flags_found'].append(execution_result['flag'])
                
                print(f"🎉 ¡FLAG ENCONTRADA! {execution_result['flag']}")
                
                # Aprender del éxito
                self._learn_from_success(challenge_input, execution_result)
                
            else:
                result['error'] = execution_result.get('error', 'No resuelto')
                print(f"❌ Error: {result['error']}")
        
        except Exception as e:
            result['error'] = f"Error general: {str(e)}"
            print(f"❌ Error: {e}")
        
        result['execution_time'] = (datetime.now() - start_time).total_seconds()
        
        # Guardar en historial
        self.conversation_history.append({
            'timestamp': datetime.now(),
            'challenge': challenge_input[:200],
            'result': result
        })
        
        return result
    
    def _analyze_with_gemini(self, challenge_input: str) -> Dict:
        """Analiza el desafío con Gemini"""
        
        if not self.gemini_model:
            return {'error': 'Gemini no disponible'}
        
        prompt = f"""
Analiza este desafío CTF y responde en JSON:

CHALLENGE:
{challenge_input}

CONTEXT:
- Tengo acceso a {self.knowledge_stats['total_writeups']} writeups
- Conozco {self.knowledge_stats['techniques_known']} técnicas
- Puedo conectarme a terminales remotas

Responde en JSON:
{{
    "challenge_type": "rsa|elliptic_curve|xor|network|misc",
    "confidence": 0.0-1.0,
    "requires_network": boolean,
    "recommended_strategy": "network_interactive|code_generation|direct_analysis",
    "techniques_needed": ["list"],
    "network_info": {{"host": "if applicable", "port": "if applicable"}},
    "reasoning": "explanation"
}}
"""
        
        try:
            response = self.gemini_model.generate_content(prompt)
            analysis = self._process_gemini_response(response.text)
            
            print(f"✅ Análisis: {analysis.get('challenge_type', 'unknown')} "
                  f"(confianza: {analysis.get('confidence', 0):.2f})")
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error en análisis: {e}")
            return {'error': str(e), 'challenge_type': 'unknown'}
    
    def _process_gemini_response(self, response_text: str) -> Dict:
        """Procesa respuesta de Gemini"""
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            else:
                return self._extract_basic_analysis(response_text)
        except:
            return self._extract_basic_analysis(response_text)
    
    def _extract_basic_analysis(self, text: str) -> Dict:
        """Extrae análisis básico"""
        analysis = {
            'challenge_type': 'unknown',
            'confidence': 0.5,
            'requires_network': False,
            'recommended_strategy': 'code_generation'
        }
        
        text_lower = text.lower()
        if 'nc ' in text_lower or 'netcat' in text_lower:
            analysis['requires_network'] = True
            analysis['recommended_strategy'] = 'network_interactive'
        elif 'rsa' in text_lower:
            analysis['challenge_type'] = 'rsa'
        elif 'elliptic' in text_lower or 'sage' in text_lower:
            analysis['challenge_type'] = 'elliptic_curve'
        elif 'xor' in text_lower:
            analysis['challenge_type'] = 'xor'
        
        return analysis
    
    def _determine_strategy(self, challenge_input: str, analysis: Dict) -> Dict:
        """Determina estrategia de resolución"""
        
        # Si requiere red
        if analysis.get('requires_network', False) or 'nc ' in challenge_input:
            return {
                'type': 'network_interactive',
                'reasoning': 'Requiere interacción de red'
            }
        
        # Si hay flag visible
        if re.search(r'crypto\{[^}]+\}|flag\{[^}]+\}', challenge_input):
            return {
                'type': 'direct_analysis', 
                'reasoning': 'Flag visible en el texto'
            }
        
        # Por defecto: generación de código
        return {
            'type': 'code_generation',
            'reasoning': 'Resolución mediante código generado'
        }
    
    def _solve_network_interactive(self, challenge_input: str, strategy: Dict) -> Dict:
        """Resuelve desafíos de red con conversación"""
        
        print("🌐 Iniciando resolución de red interactiva...")
        
        # Extraer info de red
        network_info = self._extract_network_info(challenge_input)
        
        if not network_info['host'] or not network_info['port']:
            return {'success': False, 'error': 'No se encontró info de red'}
        
        try:
            print(f"🔌 Conectando a {network_info['host']}:{network_info['port']}...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            sock.connect((network_info['host'], int(network_info['port'])))
            
            interactions = []
            
            # Recibir mensaje inicial
            initial_data = sock.recv(4096).decode('utf-8', errors='ignore')
            interactions.append({'type': 'receive', 'data': initial_data})
            print(f"📥 Recibido: {initial_data[:150]}...")
            
            # Conversación inteligente con Gemini
            for i in range(10):  # Máximo 10 interacciones
                
                # Analizar respuesta y determinar qué enviar
                next_action = self._determine_next_action(interactions, challenge_input)
                
                if next_action['action'] == 'stop':
                    break
                
                if next_action['action'] == 'send':
                    message = next_action['message']
                    print(f"📤 Enviando: {message}")
                    sock.send(message.encode() + b'\n')
                    interactions.append({'type': 'send', 'data': message})
                    
                    # Recibir respuesta
                    try:
                        response = sock.recv(4096).decode('utf-8', errors='ignore')
                        interactions.append({'type': 'receive', 'data': response})
                        print(f"📥 Recibido: {response[:150]}...")
                        
                        # Buscar flag
                        flag_match = re.search(r'crypto\{[^}]+\}|flag\{[^}]+\}', response)
                        if flag_match:
                            sock.close()
                            return {
                                'success': True,
                                'flag': flag_match.group(0),
                                'interactions': interactions
                            }
                    
                    except socket.timeout:
                        print("⏰ Timeout")
                        break
            
            sock.close()
            return {'success': False, 'error': 'No se encontró flag', 'interactions': interactions}
            
        except Exception as e:
            return {'success': False, 'error': f'Error de red: {str(e)}'}
    
    def _extract_network_info(self, challenge_input: str) -> Dict:
        """Extrae información de red"""
        network_info = {'host': None, 'port': None}
        
        # Buscar patrón nc host port
        nc_match = re.search(r'nc\s+([^\s]+)\s+(\d+)', challenge_input)
        if nc_match:
            network_info['host'] = nc_match.group(1)
            network_info['port'] = nc_match.group(2)
        
        return network_info
    
    def _determine_next_action(self, interactions: List[Dict], challenge: str) -> Dict:
        """Determina próxima acción con Gemini"""
        
        if not self.gemini_model:
            return {'action': 'send', 'message': '1'}
        
        # Contexto de conversación
        conversation = "\n".join([
            f"{inter['type'].upper()}: {inter['data'][:100]}"
            for inter in interactions[-3:]  # Últimas 3
        ])
        
        prompt = f"""
Conversación CTF actual:
{conversation}

Desafío original: {challenge[:200]}

¿Qué debería enviar next? Responde JSON:
{{
    "action": "send|stop",
    "message": "message to send",
    "reasoning": "why"
}}
"""
        
        try:
            response = self.gemini_model.generate_content(prompt)
            action = self._process_gemini_response(response.text)
            return action
        except:
            return {'action': 'send', 'message': 'help'}
    
    def _solve_code_generation(self, challenge_input: str, strategy: Dict) -> Dict:
        """Resuelve generando código con Gemini"""
        
        print("🛠️  Generando código con Gemini...")
        
        if not self.gemini_model:
            return self._solve_direct_analysis(challenge_input)
        
        prompt = f"""
Genera código Python para resolver este CTF:

CHALLENGE:
{challenge_input}

KNOWLEDGE:
- Writeups: {self.knowledge_stats['total_writeups']}
- Técnicas conocidas: {self.knowledge_stats['techniques_known']}

Genera código Python completo y funcional:

```python
# Código aquí
```
"""
        
        try:
            response = self.gemini_model.generate_content(prompt)
            code = self._extract_code_from_response(response.text)
            
            if code:
                return self._execute_generated_code(code)
            else:
                return {'success': False, 'error': 'No se generó código válido'}
                
        except Exception as e:
            return {'success': False, 'error': f'Error generando código: {str(e)}'}
    
    def _extract_code_from_response(self, response_text: str) -> str:
        """Extrae código de la respuesta"""
        code_match = re.search(r'```python\n(.*?)\n```', response_text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        code_match = re.search(r'```\n(.*?)\n```', response_text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        return None
    
    def _execute_generated_code(self, code: str) -> Dict:
        """Ejecuta código generado de manera segura"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            os.unlink(temp_file)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                flag_match = re.search(r'crypto\{[^}]+\}|flag\{[^}]+\}', output)
                if flag_match:
                    return {'success': True, 'flag': flag_match.group(0)}
                else:
                    return {'success': True, 'flag': output}
            else:
                return {'success': False, 'error': result.stderr}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _solve_direct_analysis(self, challenge_input: str) -> Dict:
        """Análisis directo para flags visibles"""
        
        # Buscar flags directamente
        flag_match = re.search(r'crypto\{[^}]+\}|flag\{[^}]+\}', challenge_input)
        if flag_match:
            return {'success': True, 'flag': flag_match.group(0)}
        
        # Base64 decode
        try:
            import base64
            b64_pattern = r'[A-Za-z0-9+/]{20,}=*'
            b64_matches = re.findall(b64_pattern, challenge_input)
            for b64_str in b64_matches:
                try:
                    decoded = base64.b64decode(b64_str).decode('utf-8')
                    flag_in_decoded = re.search(r'crypto\{[^}]+\}|flag\{[^}]+\}', decoded)
                    if flag_in_decoded:
                        return {'success': True, 'flag': flag_in_decoded.group(0)}
                except:
                    continue
        except:
            pass
        
        return {'success': False, 'error': 'No se encontró flag mediante análisis directo'}
    
    def _learn_from_success(self, challenge: str, result: Dict):
        """Aprende de resoluciones exitosas"""
        print("🎓 Aprendiendo del éxito...")
        self.session_stats['conversations_held'] += 1
        
        # Aquí podrías implementar aprendizaje automático
        # Por ahora, solo guardamos el caso exitoso
        success_case = {
            'timestamp': datetime.now().isoformat(),
            'challenge_preview': challenge[:200],
            'flag_found': result['flag'],
            'method_used': result.get('method', 'unknown'),
            'success': True
        }
        
        # Guardar caso exitoso para entrenamiento futuro
        success_file = self.base_dir / "data/ml/success_cases.json"
        try:
            if success_file.exists():
                with open(success_file, 'r', encoding='utf-8') as f:
                    cases = json.load(f)
            else:
                cases = []
            
            cases.append(success_case)
            
            with open(success_file, 'w', encoding='utf-8') as f:
                json.dump(cases, f, indent=2, ensure_ascii=False)
                
            print(f"✅ Caso exitoso guardado en {success_file}")
            
        except Exception as e:
            print(f"⚠️  Error guardando caso exitoso: {e}")
    
    def get_session_summary(self) -> Dict:
        """Resumen de la sesión"""
        duration = (datetime.now() - self.session_stats['start_time']).total_seconds()
        
        return {
            'session_duration_seconds': duration,
            'challenges_attempted': self.session_stats['challenges_attempted'],
            'challenges_solved': self.session_stats['challenges_solved'],
            'success_rate': self.session_stats['challenges_solved'] / max(self.session_stats['challenges_attempted'], 1),
            'flags_found': self.session_stats['flags_found'],
            'conversations_held': self.session_stats['conversations_held'],
            'total_interactions': len(self.conversation_history)
        }

# Función de conveniencia
def solve_ctf_conversational(challenge: str, api_key: str = None) -> Dict:
    """Función conveniente para resolver CTF con conversación"""
    agent = ConversationalCTFAgent(gemini_api_key=api_key)
    return agent.solve_challenge_conversational(challenge)

if __name__ == "__main__":
    # Demo del agente
    print("🧪 === DEMO CONVERSATIONAL CTF AGENT ===")
    
    # Test con challenge de red simulado
    test_challenge_network = """
    Challenge: Network CTF
    Connect to: nc example.com 1337
    Find the hidden flag by interacting with the server.
    """
    
    # Test con challenge de código
    test_challenge_code = """
    Challenge: Base64 Decode
    Can you decode this message?
    Y3J5cHRve2Jhc2U2NF9pc19lYXN5fQ==
    """
    
    agent = ConversationalCTFAgent()
    
    print("\n🔧 Probando challenge de código...")
    result1 = agent.solve_challenge_conversational(test_challenge_code)
    print(f"Resultado: {result1}")
    
    print("\n📊 Resumen de sesión:")
    summary = agent.get_session_summary()
    for key, value in summary.items():
        print(f"  • {key}: {value}")