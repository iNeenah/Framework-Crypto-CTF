#!/usr/bin/env python3
"""
AI Agent Configuration & Network Enhancement
===========================================
Configurador para APIs de IA y mejoras de conectividad para el agente autónomo
"""

import os
import json
import socket
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

class AIAgentConfigurator:
    def __init__(self):
        self.base_dir = Path("c:/Users/Nenaah/Desktop/Programacion/GIT/CRYPTO")
        self.config_file = self.base_dir / "config/ai_agent_config.json"
        self.config = self.load_or_create_config()
        
    def load_or_create_config(self) -> Dict:
        """Carga o crea la configuración del agente"""
        
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return self.create_default_config()
    
    def create_default_config(self) -> Dict:
        """Crea configuración por defecto"""
        
        default_config = {
            "ai_providers": {
                "gemini": {
                    "api_key": "",
                    "model": "gemini-1.5-pro",
                    "enabled": False
                },
                "openai": {
                    "api_key": "",
                    "model": "gpt-4",
                    "enabled": False
                },
                "anthropic": {
                    "api_key": "",
                    "model": "claude-3-sonnet",
                    "enabled": False
                }
            },
            "network_settings": {
                "default_timeout": 30,
                "max_retries": 3,
                "retry_delay": 1,
                "buffer_size": 4096,
                "common_ports": [1337, 8080, 9999, 31337, 12345]
            },
            "solver_settings": {
                "max_execution_time": 60,
                "auto_save_solutions": True,
                "verbose_output": True,
                "parallel_solving": False
            },
            "expert_knowledge": {
                "use_knowledge_base": True,
                "confidence_threshold": 0.6,
                "max_techniques_per_challenge": 5
            }
        }
        
        # Crear directorio de config si no existe
        self.config_file.parent.mkdir(exist_ok=True)
        
        # Guardar configuración por defecto
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)
        
        print(f"✅ Configuración por defecto creada: {self.config_file}")
        return default_config
    
    def setup_ai_providers(self):
        """Configura los proveedores de IA"""
        
        print("🤖 CONFIGURACIÓN DE PROVEEDORES DE IA")
        print("=" * 40)
        
        providers = {
            "gemini": "Google Gemini (Recomendado para CTF)",
            "openai": "OpenAI GPT-4",
            "anthropic": "Anthropic Claude"
        }
        
        for provider, description in providers.items():
            print(f"\n📋 {description}")
            
            current_key = self.config["ai_providers"][provider]["api_key"]
            current_status = "✅ Configurado" if current_key else "❌ No configurado"
            
            print(f"   Estado actual: {current_status}")
            
            if not current_key:
                print(f"   Para obtener API key:")
                if provider == "gemini":
                    print("   🔗 https://makersuite.google.com/app/apikey")
                elif provider == "openai":
                    print("   🔗 https://platform.openai.com/api-keys")
                elif provider == "anthropic":
                    print("   🔗 https://console.anthropic.com/")
                
                api_key = input(f"   Ingresa tu API key de {provider} (Enter para omitir): ").strip()
                
                if api_key:
                    self.config["ai_providers"][provider]["api_key"] = api_key
                    self.config["ai_providers"][provider]["enabled"] = True
                    print(f"   ✅ {provider} configurado exitosamente")
                else:
                    self.config["ai_providers"][provider]["enabled"] = False
                    print(f"   ⏭️  {provider} omitido")
        
        self.save_config()
    
    def test_network_connectivity(self):
        """Prueba la conectividad de red"""
        
        print("\n🌐 PRUEBA DE CONECTIVIDAD DE RED")
        print("=" * 35)
        
        test_servers = [
            ("google.com", 80),
            ("github.com", 443),
            ("cryptohack.org", 443)
        ]
        
        for host, port in test_servers:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    print(f"   ✅ {host}:{port} - Conectado")
                else:
                    print(f"   ❌ {host}:{port} - Error de conexión")
                    
            except Exception as e:
                print(f"   ❌ {host}:{port} - Error: {e}")
    
    def install_ai_dependencies(self):
        """Instala dependencias de IA"""
        
        print("\n📦 INSTALACIÓN DE DEPENDENCIAS DE IA")
        print("=" * 38)
        
        ai_packages = [
            "google-generativeai",  # Gemini
            "openai",              # OpenAI
            "anthropic",           # Claude
            "requests",            # HTTP requests
            "websockets"           # WebSocket support
        ]
        
        for package in ai_packages:
            try:
                print(f"📦 Instalando {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"   ✅ {package} instalado")
            except subprocess.CalledProcessError:
                print(f"   ❌ Error instalando {package}")
            except Exception as e:
                print(f"   ⚠️  {package}: {e}")
    
    def create_enhanced_network_handler(self):
        """Crea un manejador de red mejorado"""
        
        network_handler_code = '''#!/usr/bin/env python3
"""
Enhanced Network Handler for CTF Challenges
==========================================
Manejador de red robusto con reintentos automáticos y detección inteligente
"""

import socket
import time
import re
import threading
from typing import Optional, Dict, List, Tuple

class EnhancedNetworkHandler:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.timeout = self.config.get('default_timeout', 30)
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1)
        self.buffer_size = self.config.get('buffer_size', 4096)
        
    def connect_with_retry(self, host: str, port: int) -> Optional[socket.socket]:
        """Conecta con reintentos automáticos"""
        
        for attempt in range(self.max_retries):
            try:
                print(f"🔌 Intento {attempt + 1}/{self.max_retries}: Conectando a {host}:{port}")
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                sock.connect((host, port))
                
                print(f"✅ Conectado exitosamente a {host}:{port}")
                return sock
                
            except socket.timeout:
                print(f"⏰ Timeout en intento {attempt + 1}")
            except socket.error as e:
                print(f"❌ Error de socket en intento {attempt + 1}: {e}")
            except Exception as e:
                print(f"⚠️  Error inesperado en intento {attempt + 1}: {e}")
            
            if attempt < self.max_retries - 1:
                print(f"⏳ Esperando {self.retry_delay}s antes del siguiente intento...")
                time.sleep(self.retry_delay)
        
        print(f"💥 No se pudo conectar a {host}:{port} después de {self.max_retries} intentos")
        return None
    
    def intelligent_interaction(self, sock: socket.socket, challenge_hints: List[str] = None) -> Optional[str]:
        """Interacción inteligente con el servidor"""
        
        try:
            # Leer respuesta inicial
            initial_response = self.receive_data(sock)
            print(f"📨 Respuesta inicial: {initial_response[:200]}...")
            
            # Buscar flag en respuesta inicial
            flag = self.extract_flag(initial_response)
            if flag:
                return flag
            
            # Analizar respuesta para determinar tipo de interacción
            interaction_type = self.analyze_server_response(initial_response)
            print(f"🔍 Tipo de interacción detectado: {interaction_type}")
            
            # Estrategias de interacción basadas en el tipo
            if interaction_type == "menu":
                return self.handle_menu_interaction(sock, initial_response)
            elif interaction_type == "prompt":
                return self.handle_prompt_interaction(sock, initial_response, challenge_hints)
            elif interaction_type == "math":
                return self.handle_math_interaction(sock, initial_response)
            else:
                return self.handle_generic_interaction(sock, initial_response)
                
        except Exception as e:
            print(f"❌ Error en interacción: {e}")
            return None
    
    def receive_data(self, sock: socket.socket, timeout: float = None) -> str:
        """Recibe datos del socket con timeout"""
        
        if timeout:
            sock.settimeout(timeout)
        
        try:
            data = sock.recv(self.buffer_size)
            return data.decode('utf-8', errors='ignore')
        except socket.timeout:
            print("⏰ Timeout recibiendo datos")
            return ""
        except Exception as e:
            print(f"❌ Error recibiendo datos: {e}")
            return ""
    
    def send_data(self, sock: socket.socket, data: str) -> bool:
        """Envía datos al socket"""
        
        try:
            sock.send((data + "\\n").encode())
            return True
        except Exception as e:
            print(f"❌ Error enviando datos: {e}")
            return False
    
    def extract_flag(self, text: str) -> Optional[str]:
        """Extrae flag del texto"""
        
        flag_patterns = [
            r'crypto\\{[^}]+\\}',
            r'flag\\{[^}]+\\}',
            r'CTF\\{[^}]+\\}',
            r'[a-zA-Z0-9_]+\\{[^}]+\\}'
        ]
        
        for pattern in flag_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def analyze_server_response(self, response: str) -> str:
        """Analiza la respuesta del servidor para determinar el tipo"""
        
        response_lower = response.lower()
        
        if any(keyword in response_lower for keyword in ['menu', 'option', 'choice', 'select']):
            return "menu"
        elif any(keyword in response_lower for keyword in ['enter', 'input', 'type', 'password']):
            return "prompt"
        elif any(keyword in response_lower for keyword in ['calculate', 'solve', 'equation', 'number']):
            return "math"
        else:
            return "generic"
    
    def handle_menu_interaction(self, sock: socket.socket, response: str) -> Optional[str]:
        """Maneja interacciones de menú"""
        
        print("🍽️  Manejando interacción de menú")
        
        # Buscar opciones numéricas
        menu_options = re.findall(r'(\\d+)[.):]', response)
        
        for option in menu_options:
            print(f"🔢 Probando opción: {option}")
            
            if self.send_data(sock, option):
                time.sleep(1)
                response = self.receive_data(sock)
                print(f"📨 Respuesta: {response[:100]}...")
                
                flag = self.extract_flag(response)
                if flag:
                    return flag
        
        return None
    
    def handle_prompt_interaction(self, sock: socket.socket, response: str, hints: List[str] = None) -> Optional[str]:
        """Maneja interacciones de prompt"""
        
        print("💬 Manejando interacción de prompt")
        
        # Usar hints si están disponibles
        inputs_to_try = hints or []
        
        # Agregar inputs comunes
        inputs_to_try.extend([
            "admin", "password", "flag", "help", "?", "ls", "cat flag.txt",
            "1", "yes", "y", "n", "no", "exit", "quit"
        ])
        
        for input_text in inputs_to_try:
            print(f"⌨️  Probando input: {input_text}")
            
            if self.send_data(sock, input_text):
                time.sleep(1)
                response = self.receive_data(sock)
                print(f"📨 Respuesta: {response[:100]}...")
                
                flag = self.extract_flag(response)
                if flag:
                    return flag
        
        return None
    
    def handle_math_interaction(self, sock: socket.socket, response: str) -> Optional[str]:
        """Maneja interacciones matemáticas"""
        
        print("🧮 Manejando interacción matemática")
        
        # Buscar ecuaciones simples
        math_patterns = [
            r'(\\d+)\\s*\\+\\s*(\\d+)',  # suma
            r'(\\d+)\\s*\\-\\s*(\\d+)',  # resta
            r'(\\d+)\\s*\\*\\s*(\\d+)',  # multiplicación
            r'(\\d+)\\s*\\/\\s*(\\d+)'   # división
        ]
        
        for pattern in math_patterns:
            match = re.search(pattern, response)
            if match:
                try:
                    a, b = map(int, match.groups())
                    
                    if '+' in pattern:
                        result = a + b
                    elif '-' in pattern:
                        result = a - b
                    elif '*' in pattern:
                        result = a * b
                    elif '/' in pattern:
                        result = a // b
                    
                    print(f"🧮 Calculando: {a} op {b} = {result}")
                    
                    if self.send_data(sock, str(result)):
                        time.sleep(1)
                        response = self.receive_data(sock)
                        
                        flag = self.extract_flag(response)
                        if flag:
                            return flag
                            
                except ValueError:
                    continue
        
        return None
    
    def handle_generic_interaction(self, sock: socket.socket, response: str) -> Optional[str]:
        """Maneja interacciones genéricas"""
        
        print("🔧 Manejando interacción genérica")
        
        # Estrategias genéricas
        generic_inputs = [
            "",           # Enter vacío
            "\\n",        # Newline
            "a",          # Carácter simple
            "test",       # Texto simple
            "flag",       # Solicitar flag directamente
        ]
        
        for input_text in generic_inputs:
            if self.send_data(sock, input_text):
                time.sleep(1)
                response = self.receive_data(sock)
                
                flag = self.extract_flag(response)
                if flag:
                    return flag
        
        return None

def test_enhanced_handler():
    """Prueba el manejador mejorado"""
    
    print("🧪 PRUEBA DEL MANEJADOR DE RED MEJORADO")
    print("=" * 45)
    
    config = {
        'default_timeout': 30,
        'max_retries': 3,
        'retry_delay': 1,
        'buffer_size': 4096
    }
    
    handler = EnhancedNetworkHandler(config)
    
    # Probar conectividad básica
    test_connections = [
        ("google.com", 80),
        ("httpbin.org", 80)
    ]
    
    for host, port in test_connections:
        sock = handler.connect_with_retry(host, port)
        if sock:
            print(f"✅ Conexión exitosa a {host}:{port}")
            sock.close()
        else:
            print(f"❌ Falló conexión a {host}:{port}")

if __name__ == "__main__":
    test_enhanced_handler()
'''
        
        # Guardar el manejador de red
        network_file = self.base_dir / "framework/network_handler.py"
        with open(network_file, 'w', encoding='utf-8') as f:
            f.write(network_handler_code)
        
        print(f"✅ Manejador de red mejorado creado: {network_file}")
    
    def create_ai_integration_examples(self):
        """Crea ejemplos de integración con diferentes APIs"""
        
        examples_dir = self.base_dir / "examples/ai_integration"
        examples_dir.mkdir(exist_ok=True)
        
        # Ejemplo Gemini
        gemini_example = '''#!/usr/bin/env python3
"""
Ejemplo de integración con Google Gemini
========================================
"""

import google.generativeai as genai
import os

def setup_gemini():
    """Configura Gemini AI"""
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY no encontrada en variables de entorno")
        return None
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    return model

def solve_with_gemini(challenge_text: str):
    """Resuelve un desafío usando Gemini"""
    
    model = setup_gemini()
    if not model:
        return None
    
    prompt = f"""
You are an expert CTF solver. Analyze this challenge and provide a complete Python solution:

CHALLENGE:
{challenge_text}

REQUIREMENTS:
1. Analyze the challenge type
2. Generate complete Python code
3. Include all necessary imports
4. Handle errors gracefully
5. Return the flag in format crypto{{...}}

SOLUTION:
"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error with Gemini: {e}")
        return None

if __name__ == "__main__":
    test_challenge = "Decode this Base64: Y3J5cHRve2Jhc2U2NF9pc19lYXN5fQ=="
    solution = solve_with_gemini(test_challenge)
    if solution:
        print("Generated solution:")
        print(solution)
'''
        
        with open(examples_dir / "gemini_example.py", 'w') as f:
            f.write(gemini_example)
        
        print(f"✅ Ejemplos de integración creados en: {examples_dir}")
    
    def save_config(self):
        """Guarda la configuración"""
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
        
        print(f"💾 Configuración guardada: {self.config_file}")
    
    def run_full_setup(self):
        """Ejecuta la configuración completa"""
        
        print("🚀 CONFIGURACIÓN COMPLETA DEL AGENTE AUTÓNOMO")
        print("=" * 50)
        
        # 1. Instalar dependencias
        self.install_ai_dependencies()
        
        # 2. Configurar APIs
        self.setup_ai_providers()
        
        # 3. Probar conectividad
        self.test_network_connectivity()
        
        # 4. Crear componentes
        self.create_enhanced_network_handler()
        self.create_ai_integration_examples()
        
        print(f"\n✅ CONFIGURACIÓN COMPLETADA")
        print(f"🎯 El agente autónomo está listo para usar!")
        print(f"📝 Configuración guardada en: {self.config_file}")

def main():
    """Función principal"""
    
    print("⚙️  AI AGENT CONFIGURATOR")
    print("=" * 25)
    
    configurator = AIAgentConfigurator()
    
    print("Opciones disponibles:")
    print("1. Configuración completa")
    print("2. Solo configurar APIs de IA")
    print("3. Solo probar conectividad")
    print("4. Solo instalar dependencias")
    
    choice = input("\nSelecciona una opción (1-4): ").strip()
    
    if choice == "1":
        configurator.run_full_setup()
    elif choice == "2":
        configurator.setup_ai_providers()
    elif choice == "3":
        configurator.test_network_connectivity()
    elif choice == "4":
        configurator.install_ai_dependencies()
    else:
        print("Opción inválida")

if __name__ == "__main__":
    main()