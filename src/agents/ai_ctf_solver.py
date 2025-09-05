#!/usr/bin/env python3
"""
AI CTF Solver - Main Interface
==============================
Interfaz principal para el agente autónomo de resolución de CTF
Combina Expert ML Knowledge + LLM + Network Handling
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from typing import Dict, List, Optional

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

try:
    from autonomous_ctf_agent import AutonomousCTFAgent
    from setup_ai_agent import AIAgentConfigurator
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("💡 Asegúrate de que todos los archivos están en el directorio correcto")
    sys.exit(1)

class AICTFSolver:
    def __init__(self):
        self.base_dir = Path("c:/Users/Nenaah/Desktop/Programacion/GIT/CRYPTO")
        self.agent = None
        self.configurator = AIAgentConfigurator()
        
    def initialize_agent(self) -> bool:
        """Inicializa el agente autónomo"""
        
        print("🤖 Inicializando Agente Autónomo...")
        
        try:
            # Cargar configuración
            config_file = self.base_dir / "config/ai_agent_config.json"
            gemini_key = None
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    if config.get('ai_providers', {}).get('gemini', {}).get('enabled'):
                        gemini_key = config['ai_providers']['gemini']['api_key']
            
            # Inicializar agente
            self.agent = AutonomousCTFAgent(gemini_api_key=gemini_key)
            print("✅ Agente inicializado exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando agente: {e}")
            return False
    
    def solve_from_file(self, file_path: str) -> Optional[str]:
        """Resuelve un desafío desde archivo"""
        
        if not self.agent:
            if not self.initialize_agent():
                return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                challenge_content = f.read()
            
            challenge_name = Path(file_path).stem
            
            print(f"📁 Resolviendo desafío desde archivo: {file_path}")
            
            result = self.agent.solve_challenge_autonomous(
                challenge_content, 
                challenge_name
            )
            
            return result.get('flag')
            
        except Exception as e:
            print(f"❌ Error procesando archivo: {e}")
            return None
    
    def solve_from_network(self, host: str, port: int) -> Optional[str]:
        """Resuelve un desafío de red"""
        
        if not self.agent:
            if not self.initialize_agent():
                return None
        
        network_challenge = f"""
Network Challenge:
Connect to: nc {host} {port}

Instructions: Connect to the server and interact to get the flag.
The agent will handle the connection and interaction automatically.
"""
        
        print(f"🌐 Resolviendo desafío de red: {host}:{port}")
        
        result = self.agent.solve_challenge_autonomous(
            network_challenge,
            f"network_{host}_{port}"
        )
        
        return result.get('flag')
    
    def solve_interactive(self):
        """Modo interactivo de resolución"""
        
        if not self.agent:
            if not self.initialize_agent():
                return
        
        print("🎮 MODO INTERACTIVO")
        print("=" * 20)
        print("Ingresa el desafío (presiona Enter dos veces para terminar):")
        
        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        
        challenge_content = '\n'.join(lines[:-1])  # Remover última línea vacía
        
        if challenge_content.strip():
            print("\n🚀 Procesando desafío...")
            
            result = self.agent.solve_challenge_autonomous(
                challenge_content,
                "interactive_challenge"
            )
            
            if result.get('flag'):
                print(f"\n🏆 FLAG ENCONTRADA: {result['flag']}")
            else:
                print(f"\n❌ No se pudo resolver el desafío")
                if result.get('solution_code'):
                    print("💡 Código generado disponible en los logs")
        else:
            print("⚠️  No se ingresó ningún desafío")
    
    def batch_solve(self, directory: str):
        """Resuelve múltiples desafíos en lote"""
        
        if not self.agent:
            if not self.initialize_agent():
                return
        
        challenge_dir = Path(directory)
        
        if not challenge_dir.exists():
            print(f"❌ Directorio no encontrado: {directory}")
            return
        
        # Buscar archivos de desafíos
        challenge_files = []
        for ext in ['*.txt', '*.md', '*.py']:
            challenge_files.extend(challenge_dir.glob(ext))
        
        if not challenge_files:
            print(f"⚠️  No se encontraron archivos de desafíos en: {directory}")
            return
        
        print(f"📦 PROCESAMIENTO EN LOTE")
        print(f"📁 Directorio: {directory}")
        print(f"📄 Archivos encontrados: {len(challenge_files)}")
        print("=" * 40)
        
        results = []
        
        for i, file_path in enumerate(challenge_files, 1):
            print(f"\n[{i}/{len(challenge_files)}] Procesando: {file_path.name}")
            
            flag = self.solve_from_file(str(file_path))
            
            results.append({
                'file': file_path.name,
                'flag': flag,
                'solved': flag is not None
            })
            
            time.sleep(1)  # Pausa entre archivos
        
        # Resumen de resultados
        solved_count = sum(1 for r in results if r['solved'])
        
        print(f"\n📊 RESUMEN DEL LOTE")
        print("=" * 20)
        print(f"Total archivos: {len(results)}")
        print(f"Resueltos: {solved_count}")
        print(f"Tasa de éxito: {(solved_count/len(results)*100):.1f}%")
        
        if solved_count > 0:
            print(f"\n🏆 FLAGS ENCONTRADAS:")
            for r in results:
                if r['solved']:
                    print(f"   {r['file']}: {r['flag']}")
    
    def show_stats(self):
        """Muestra estadísticas del agente"""
        
        if not self.agent:
            print("⚠️  Agente no inicializado")
            return
        
        self.agent.print_session_stats()
        
        # Estadísticas adicionales del knowledge base
        kb = self.agent.knowledge_base
        
        print(f"\n🧠 KNOWLEDGE BASE STATS")
        print("=" * 25)
        print(f"Total writeups: {kb.get('writeups_count', 0)}")
        
        ec_info = kb.get('elliptic_curves', {})
        print(f"EC techniques: {len(ec_info.get('techniques', []))}")
        print(f"EC tools: {len(ec_info.get('tools', []))}")
        
        # Archivos recientes
        solved_dir = self.base_dir / "challenges/solved"
        if solved_dir.exists():
            recent_files = sorted(
                [f for f in solved_dir.glob("autonomous_*.txt")],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )[:5]
            
            if recent_files:
                print(f"\n📁 SOLUCIONES RECIENTES:")
                for f in recent_files:
                    print(f"   {f.name}")
    
    def setup_environment(self):
        """Configura el entorno del agente"""
        
        print("⚙️  CONFIGURANDO ENTORNO DEL AGENTE")
        print("=" * 35)
        
        self.configurator.run_full_setup()
    
    def run_tests(self):
        """Ejecuta pruebas del sistema"""
        
        print("🧪 EJECUTANDO PRUEBAS DEL SISTEMA")
        print("=" * 35)
        
        # Crear directorio de pruebas si no existe
        test_dir = self.base_dir / "challenges/test_ai"
        test_dir.mkdir(exist_ok=True)
        
        # Crear desafíos de prueba
        test_challenges = {
            "base64_test.txt": "Decode this Base64: Y3J5cHRve2Jhc2U2NF9pc19lYXN5fQ==",
            "xor_test.txt": """XOR Challenge:
Encrypted (hex): 1a1b1c1d1e1f
Key: single byte
Hint: flag starts with 'crypto{'""",
            "network_test.txt": "Connect to: nc example.com 1337\nGet the flag from the server."
        }
        
        # Escribir archivos de prueba
        for filename, content in test_challenges.items():
            test_file = test_dir / filename
            with open(test_file, 'w') as f:
                f.write(content)
        
        print(f"📝 Archivos de prueba creados en: {test_dir}")
        
        # Ejecutar pruebas
        if not self.agent:
            if not self.initialize_agent():
                return
        
        print("\n🚀 Ejecutando pruebas...")
        
        for filename in test_challenges.keys():
            test_file = test_dir / filename
            print(f"\n🧪 Prueba: {filename}")
            
            flag = self.solve_from_file(str(test_file))
            
            if flag:
                print(f"   ✅ Éxito: {flag}")
            else:
                print(f"   ❌ Falló")

def main():
    """Función principal con argumentos de línea de comandos"""
    
    parser = argparse.ArgumentParser(
        description="AI CTF Solver - Agente autónomo para resolver desafíos CTF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python ai_ctf_solver.py --file challenge.txt
  python ai_ctf_solver.py --network example.com 1337
  python ai_ctf_solver.py --interactive
  python ai_ctf_solver.py --batch challenges/test_challenges/
  python ai_ctf_solver.py --setup
  python ai_ctf_solver.py --test
        """
    )
    
    parser.add_argument('--file', '-f', 
                       help='Resolver desafío desde archivo')
    
    parser.add_argument('--network', '-n', nargs=2, 
                       metavar=('HOST', 'PORT'),
                       help='Resolver desafío de red (host puerto)')
    
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Modo interactivo')
    
    parser.add_argument('--batch', '-b',
                       help='Resolver múltiples desafíos desde directorio')
    
    parser.add_argument('--stats', '-s', action='store_true',
                       help='Mostrar estadísticas')
    
    parser.add_argument('--setup', action='store_true',
                       help='Configurar entorno del agente')
    
    parser.add_argument('--test', '-t', action='store_true',
                       help='Ejecutar pruebas del sistema')
    
    args = parser.parse_args()
    
    # Crear solver
    solver = AICTFSolver()
    
    # Header
    print("🤖 AI CTF SOLVER v2.0")
    print("=" * 25)
    print("🧠 Expert ML + LLM + Network Automation")
    print()
    
    # Ejecutar acción solicitada
    if args.setup:
        solver.setup_environment()
    
    elif args.test:
        solver.run_tests()
    
    elif args.file:
        flag = solver.solve_from_file(args.file)
        if flag:
            print(f"🏆 FLAG: {flag}")
        else:
            print("❌ No se pudo resolver el desafío")
    
    elif args.network:
        host, port = args.network
        flag = solver.solve_from_network(host, int(port))
        if flag:
            print(f"🏆 FLAG: {flag}")
        else:
            print("❌ No se pudo resolver el desafío")
    
    elif args.interactive:
        solver.solve_interactive()
    
    elif args.batch:
        solver.batch_solve(args.batch)
    
    elif args.stats:
        solver.show_stats()
    
    else:
        # Modo por defecto: mostrar ayuda
        parser.print_help()
        print("\n💡 Usa --setup para configurar el entorno por primera vez")
        print("💡 Usa --test para probar el sistema")

if __name__ == "__main__":
    main()