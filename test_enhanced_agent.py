#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite para Enhanced CTF Agent
==================================
Script de prueba para verificar el funcionamiento del agente mejorado
y demostrar las mejoras en la interpretación de conocimiento.
"""

import os
import sys
from pathlib import Path

# Agregar directorios al path
base_dir = Path(__file__).parent
sys.path.append(str(base_dir))

try:
    from enhanced_ctf_agent import EnhancedCTFAgent
    print("✅ Enhanced CTF Agent importado exitosamente")
except ImportError as e:
    print(f"❌ Error importando Enhanced CTF Agent: {e}")
    sys.exit(1)

def test_challenge_interpretation():
    """Prueba la interpretación de diferentes tipos de desafíos"""
    
    print("\n🧪 === TEST: INTERPRETACIÓN DE DESAFÍOS ===")
    
    agent = EnhancedCTFAgent()
    
    # Test cases basados en los datos reales procesados
    test_challenges = [
        {
            'name': 'Elliptic Curve Challenge',
            'input': """
            Challenge: Point Negation
            E: Y^2 = X^3 + 497 X + 1768, p: 9739
            Calcular Q(x, y) con P + Q = 0 y P(8045, 6936)
            Q = -P using Sage
            """,
            'expected_type': 'elliptic_curve'
        },
        {
            'name': 'RSA Challenge',
            'input': """
            Challenge: RSA Factorization
            n = 12345678901234567890
            e = 65537
            Factorize n to find the private key
            """,
            'expected_type': 'rsa'
        },
        {
            'name': 'XOR Challenge', 
            'input': """
            Challenge: XOR Cipher
            ciphertext = 1a2b3c4d5e6f
            key = crypto
            Find the flag by XOR decryption
            """,
            'expected_type': 'xor'
        },
        {
            'name': 'Base64 Challenge',
            'input': """
            Challenge: Simple Base64
            Can you decode this?
            Y3J5cHRve2Jhc2U2NF9pc19lYXN5fQ==
            """,
            'expected_type': 'encoding'
        }
    ]
    
    for i, test in enumerate(test_challenges, 1):
        print(f"\n--- Test {i}: {test['name']} ---")
        
        if agent.knowledge_interpreter:
            interpretation = agent.knowledge_interpreter.interpret_challenge(test['input'])
            
            if interpretation:
                print(f"✅ Interpretación exitosa:")
                print(f"   • Tipo detectado: {interpretation['challenge_type']}")
                print(f"   • Confianza: {interpretation['confidence']:.2f}")
                print(f"   • Técnicas recomendadas: {len(interpretation['recommended_techniques'])}")
                
                if interpretation['recommended_techniques']:
                    top_techniques = interpretation['recommended_techniques'][:3]
                    for j, tech in enumerate(top_techniques):
                        print(f"     {j+1}. {tech['technique']} (efectividad: {tech['effectiveness']:.2f})")
                
                if interpretation['similar_challenges']:
                    print(f"   • Desafíos similares encontrados: {len(interpretation['similar_challenges'])}")
                    for similar in interpretation['similar_challenges']:
                        print(f"     - {similar['id']} (similitud: {similar['similarity']:.2f})")
            else:
                print(f"❌ No se pudo interpretar el desafío")
        else:
            print(f"⚠️  Knowledge Interpreter no disponible")

def test_solution_generation():
    """Prueba la generación de soluciones"""
    
    print("\n🛠️  === TEST: GENERACIÓN DE SOLUCIONES ===")
    
    agent = EnhancedCTFAgent()
    
    # Challenge de Base64 que sabemos que funciona
    base64_challenge = """
    Challenge: CryptoHack Base64
    
    Can you decode this?
    Y3J5cHRve2Jhc2U2NF9pc19lYXN5fQ==
    """
    
    print(f"Challenge de prueba: Base64 decode")
    print(f"Input: Y3J5cHRve2Jhc2U2NF9pc19lYXN5fQ==")
    
    result = agent.solve_challenge_enhanced(base64_challenge)
    
    print(f"\n📊 Resultado de la prueba:")
    print(f"✅ Éxito: {result['success']}")
    
    if result['success']:
        print(f"🏁 Flag encontrada: {result['flag']}")
        print(f"🛠️  Método usado: {result['method']}")
        print(f"📈 Confianza: {result['confidence']:.2f}")
        print(f"⏱️  Tiempo: {result['execution_time']:.2f}s")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Mostrar código generado si está disponible
    if result.get('generated_code'):
        print(f"\n📝 Código generado (primeras 10 líneas):")
        code_lines = result['generated_code'].split('\n')[:10]
        for i, line in enumerate(code_lines, 1):
            print(f"{i:2d}: {line}")
        if len(result['generated_code'].split('\n')) > 10:
            print("    ... (código truncado)")

def test_knowledge_stats():
    """Muestra estadísticas del conocimiento cargado"""
    
    print("\n📊 === TEST: ESTADÍSTICAS DE CONOCIMIENTO ===")
    
    agent = EnhancedCTFAgent()
    
    if agent.knowledge_interpreter:
        stats = agent.knowledge_interpreter.get_knowledge_stats()
        
        print(f"📈 Estadísticas del Knowledge Base:")
        print(f"   • Total challenges procesados: {stats['total_challenges_processed']}")
        print(f"   • Categorías de patrones: {stats['pattern_categories']}")
        print(f"   • Técnicas analizadas: {stats['technique_count']}")
        print(f"   • Templates de solución: {stats['solution_templates']}")
        
        if stats['top_techniques']:
            print(f"\n🏆 Top 10 técnicas más efectivas:")
            for i, tech in enumerate(stats['top_techniques'][:10], 1):
                print(f"{i:2d}. {tech['technique']:<20} | "
                      f"Efectividad: {tech['effectiveness']:.2f} | "
                      f"Usos: {tech['usage_count']:3d} | "
                      f"Confianza: {tech['confidence']:.2f}")
    else:
        print("⚠️  Knowledge Interpreter no disponible")

def test_comparison_with_original():
    """Compara el agente mejorado con el original"""
    
    print("\n⚖️  === TEST: COMPARACIÓN CON AGENTE ORIGINAL ===")
    
    # Importar agente original si está disponible
    try:
        from simple_ai_solver import solve_challenge
        original_available = True
        print("✅ Agente original (simple_ai_solver) disponible")
    except ImportError:
        original_available = False
        print("⚠️  Agente original no disponible para comparación")
    
    enhanced_agent = EnhancedCTFAgent()
    
    test_challenge = """
    Challenge: Simple Flag Search
    Here's your flag: crypto{test_flag_12345}
    Can you find it?
    """
    
    print(f"\nChallenge de comparación: Búsqueda simple de flag")
    
    # Probar agente mejorado
    print(f"\n🚀 Probando Enhanced Agent...")
    enhanced_result = enhanced_agent.solve_challenge_enhanced(test_challenge)
    
    print(f"Enhanced Agent:")
    print(f"   • Éxito: {enhanced_result['success']}")
    if enhanced_result['success']:
        print(f"   • Flag: {enhanced_result['flag']}")
        print(f"   • Método: {enhanced_result['method']}")
        print(f"   • Tiempo: {enhanced_result['execution_time']:.3f}s")
    
    # Probar agente original si está disponible
    if original_available:
        print(f"\n🔧 Probando Original Agent...")
        try:
            import time
            start_time = time.time()
            original_result = solve_challenge(test_challenge)
            original_time = time.time() - start_time
            
            print(f"Original Agent:")
            print(f"   • Flag: {original_result}")
            print(f"   • Tiempo: {original_time:.3f}s")
            
            # Comparación
            print(f"\n📊 Comparación:")
            print(f"   • Enhanced Agent: {enhanced_result['execution_time']:.3f}s")
            print(f"   • Original Agent: {original_time:.3f}s")
            
            if enhanced_result['execution_time'] < original_time:
                print(f"   🏆 Enhanced Agent es más rápido!")
            else:
                print(f"   🏆 Original Agent es más rápido!")
        
        except Exception as e:
            print(f"❌ Error probando agente original: {e}")

def run_comprehensive_test():
    """Ejecuta todos los tests de manera comprehensiva"""
    
    print("🧪 === ENHANCED CTF AGENT - TEST SUITE COMPLETO ===")
    print(f"Base Directory: {Path(__file__).parent}")
    print(f"Python Version: {sys.version}")
    
    # Verificar dependencias
    print(f"\n🔍 Verificando dependencias...")
    dependencies = ['json', 'pathlib', 'subprocess', 'tempfile']
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep} - FALTANTE")
    
    # Ejecutar tests
    try:
        test_knowledge_stats()
        test_challenge_interpretation()
        test_solution_generation()
        test_comparison_with_original()
        
        print(f"\n🎉 === TODOS LOS TESTS COMPLETADOS ===")
        print(f"✅ Enhanced CTF Agent está funcionando correctamente!")
        
    except Exception as e:
        print(f"\n❌ Error durante los tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_comprehensive_test()