#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo Conversational Agent - Demostración del Agente Conversacional
================================================================
Script para probar y demostrar las capacidades del agente conversacional.
"""

import os
import sys
from pathlib import Path
import time

# Añadir al path
sys.path.append(str(Path(__file__).parent))

def demo_agente_conversacional():
    """Demonstración completa del agente conversacional"""
    
    print("🚀 === DEMO AGENTE CONVERSACIONAL CTF ===")
    print("Probando las nuevas capacidades de IA conversacional")
    
    try:
        from conversational_ctf_agent import ConversationalCTFAgent
        print("✅ Agente conversacional importado exitosamente")
    except ImportError as e:
        print(f"❌ Error importando agente: {e}")
        return
    
    # Inicializar agente con tu API key de Gemini
    print("\n🤖 Inicializando agente con Gemini 2.0...")
    agent = ConversationalCTFAgent()
    
    # Casos de prueba
    test_cases = [
        {
            'name': 'Base64 Simple',
            'challenge': """
Challenge: Decode the Message
Can you decode this Base64 string?
Y3J5cHRve2Jhc2U2NF9pc19lYXN5fQ==
            """,
            'expected_flag': 'crypto{base64_is_easy}'
        },
        {
            'name': 'Flag Directo',
            'challenge': """
Challenge: Find the Flag
Here's your flag: crypto{direct_flag_found}
Can you spot it?
            """,
            'expected_flag': 'crypto{direct_flag_found}'
        },
        {
            'name': 'Desafío de Red Simulado',
            'challenge': """
Challenge: Network Challenge
Connect to the server: nc challenges.example.com 1337
Interact with the server to get the flag.
            """,
            'expected_flag': None  # No podemos conectar realmente
        },
        {
            'name': 'XOR Simple',
            'challenge': """
Challenge: XOR Cipher
message: "hello"
key: "crypto"
Find the flag by XORing the message with the key.
            """,
            'expected_flag': None  # Requiere cálculo
        }
    ]
    
    print(f"\n🧪 Ejecutando {len(test_cases)} casos de prueba...")
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n" + "="*60)
        print(f"🔬 TEST {i}: {test_case['name']}")
        print("="*60)
        
        print(f"📝 Challenge:")
        print(test_case['challenge'].strip())
        
        print(f"\n⚡ Resolviendo con agente conversacional...")
        
        start_time = time.time()
        result = agent.solve_challenge_conversational(test_case['challenge'])
        end_time = time.time()
        
        # Mostrar resultado
        print(f"\n📊 RESULTADO:")
        print(f"   ✅ Éxito: {result['success']}")
        
        if result['success']:
            print(f"   🏁 Flag encontrada: {result['flag']}")
            if test_case['expected_flag']:
                if result['flag'] == test_case['expected_flag']:
                    print(f"   ✅ Flag correcta!")
                else:
                    print(f"   ⚠️  Flag inesperada (esperada: {test_case['expected_flag']})")
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
        
        print(f"   ⏱️  Tiempo: {end_time - start_time:.2f}s")
        print(f"   🛠️  Método: {result.get('method', 'unknown')}")
        
        # Mostrar log de conversación si existe
        if result.get('conversation_log'):
            print(f"   💬 Conversaciones: {len(result['conversation_log'])}")
        
        results.append({
            'test_name': test_case['name'],
            'success': result['success'],
            'flag': result.get('flag'),
            'time': end_time - start_time,
            'method': result.get('method'),
            'error': result.get('error')
        })
        
        # Pausa entre tests
        time.sleep(1)
    
    # Resumen final
    print(f"\n" + "="*60)
    print("📈 RESUMEN DE RESULTADOS")
    print("="*60)
    
    successful_tests = sum(1 for r in results if r['success'])
    total_tests = len(results)
    success_rate = successful_tests / total_tests
    
    print(f"📊 Tests ejecutados: {total_tests}")
    print(f"✅ Tests exitosos: {successful_tests}")
    print(f"❌ Tests fallidos: {total_tests - successful_tests}")
    print(f"📈 Tasa de éxito: {success_rate:.1%}")
    
    print(f"\n🔍 Detalle por test:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"  {status} {result['test_name']}: {result['time']:.2f}s")
        if result['success']:
            print(f"      Flag: {result['flag']}")
        else:
            print(f"      Error: {result['error']}")
    
    # Estadísticas de sesión
    print(f"\n📊 Estadísticas de sesión:")
    session_stats = agent.get_session_summary()
    for key, value in session_stats.items():
        print(f"  • {key}: {value}")
    
    print(f"\n🎉 Demo completado exitosamente!")
    
    return results

def demo_entrenamiento_automatico():
    """Demonstración del sistema de entrenamiento automático"""
    
    print("\n🎓 === DEMO ENTRENAMIENTO AUTOMÁTICO ===")
    
    try:
        from auto_training_system import AutoTrainingSystem
        print("✅ Sistema de entrenamiento importado exitosamente")
    except ImportError as e:
        print(f"❌ Error importando sistema de entrenamiento: {e}")
        return
    
    print("🔍 Iniciando sesión de entrenamiento de demostración...")
    
    trainer = AutoTrainingSystem()
    
    # Simular descubrimiento de writeups
    print("📝 Buscando nuevos writeups...")
    new_writeups = trainer.discover_new_writeups()
    
    if new_writeups:
        print(f"📊 Encontrados {len(new_writeups)} nuevos writeups")
        
        print("🔄 Procesando writeups...")
        trainer.process_new_writeups(new_writeups)
        
        print("📈 Validando mejoras...")
        trainer.validate_improvements()
        
        stats = trainer.get_training_summary()
        print("📊 Estadísticas de entrenamiento:")
        for key, value in stats.items():
            print(f"  • {key}: {value}")
    else:
        print("ℹ️  No se encontraron nuevos writeups para procesar")

def menu_interactivo():
    """Menú interactivo para probar diferentes funcionalidades"""
    
    while True:
        print("\n" + "="*50)
        print("🤖 MENÚ AGENTE CONVERSACIONAL CTF")
        print("="*50)
        print("1. 🧪 Demo completo del agente")
        print("2. 🎓 Demo entrenamiento automático")
        print("3. 💬 Resolver desafío personalizado")
        print("4. 📊 Ver estadísticas del sistema")
        print("5. 🚪 Salir")
        print("="*50)
        
        try:
            opcion = input("Selecciona una opción (1-5): ").strip()
            
            if opcion == '1':
                demo_agente_conversacional()
            
            elif opcion == '2':
                demo_entrenamiento_automatico()
            
            elif opcion == '3':
                resolver_desafio_personalizado()
            
            elif opcion == '4':
                mostrar_estadisticas_sistema()
            
            elif opcion == '5':
                print("👋 ¡Hasta luego!")
                break
            
            else:
                print("❌ Opción inválida. Por favor selecciona 1-5.")
                
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def resolver_desafio_personalizado():
    """Permite al usuario resolver un desafío personalizado"""
    
    print("\n💬 === RESOLVER DESAFÍO PERSONALIZADO ===")
    
    try:
        from conversational_ctf_agent import ConversationalCTFAgent
        
        agent = ConversationalCTFAgent()
        
        print("📝 Introduce tu desafío CTF:")
        print("(Puedes usar múltiples líneas, presiona Enter dos veces para terminar)")
        
        challenge_lines = []
        empty_count = 0
        
        while empty_count < 2:
            line = input()
            if line.strip() == "":
                empty_count += 1
            else:
                empty_count = 0
            challenge_lines.append(line)
        
        challenge = "\n".join(challenge_lines).strip()
        
        if not challenge:
            print("❌ No se introdujo ningún desafío")
            return
        
        print(f"\n⚡ Resolviendo desafío...")
        result = agent.solve_challenge_conversational(challenge)
        
        print(f"\n📊 RESULTADO:")
        print(f"   ✅ Éxito: {result['success']}")
        
        if result['success']:
            print(f"   🏁 Flag: {result['flag']}")
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
        
        print(f"   ⏱️  Tiempo: {result['execution_time']:.2f}s")
        print(f"   🛠️  Método: {result.get('method', 'unknown')}")
        
    except ImportError:
        print("❌ Agente conversacional no disponible")
    except Exception as e:
        print(f"❌ Error: {e}")

def mostrar_estadisticas_sistema():
    """Muestra estadísticas del sistema"""
    
    print("\n📊 === ESTADÍSTICAS DEL SISTEMA ===")
    
    base_dir = Path(__file__).parent
    
    # Estadísticas de archivos
    training_data = base_dir / "challenges/training_data"
    if training_data.exists():
        json_files = list(training_data.glob("*.json"))
        txt_files = list(training_data.glob("*.txt"))
        print(f"📁 Training data:")
        print(f"   • Archivos JSON: {len(json_files)}")
        print(f"   • Archivos TXT: {len(txt_files)}")
    
    # Estadísticas de ML
    ml_data = base_dir / "data/ml"
    if ml_data.exists():
        ml_files = list(ml_data.glob("*.json"))
        print(f"🧠 ML data:")
        print(f"   • Archivos de datos: {len(ml_files)}")
    
    # Modelos disponibles
    models_dir = base_dir / "models"
    if models_dir.exists():
        model_files = list(models_dir.glob("*.joblib")) + list(models_dir.glob("*.json"))
        print(f"🤖 Modelos:")
        print(f"   • Modelos entrenados: {len(model_files)}")
    
    # Verificar agentes disponibles
    agents = []
    agent_files = [
        "conversational_ctf_agent.py",
        "enhanced_ctf_agent.py", 
        "autonomous_ctf_agent.py",
        "simple_ai_solver.py"
    ]
    
    for agent_file in agent_files:
        if (base_dir / agent_file).exists():
            agents.append(agent_file)
    
    print(f"🤖 Agentes disponibles: {len(agents)}")
    for agent in agents:
        print(f"   • {agent}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Demo del Agente Conversacional CTF")
    parser.add_argument("--demo", action="store_true", help="Ejecutar demo completo")
    parser.add_argument("--training", action="store_true", help="Demo entrenamiento")
    parser.add_argument("--interactive", action="store_true", help="Menú interactivo")
    
    args = parser.parse_args()
    
    if args.demo:
        demo_agente_conversacional()
    elif args.training:
        demo_entrenamiento_automatico()
    elif args.interactive:
        menu_interactivo()
    else:
        print("🤖 Agente Conversacional CTF - Demo")
        print("Opciones:")
        print("  --demo: Ejecutar demo completo")
        print("  --training: Demo entrenamiento automático")
        print("  --interactive: Menú interactivo")
        print()
        print("¿Quieres ejecutar el menú interactivo? (y/n)")
        if input().lower().startswith('y'):
            menu_interactivo()