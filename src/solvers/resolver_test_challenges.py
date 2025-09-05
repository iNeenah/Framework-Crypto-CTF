#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resolver Desafíos de Test Challenges
===================================
Script para resolver todos los desafíos criptográficos usando el agente conversacional.
"""

import os
import sys
from pathlib import Path
import time

# Añadir al path
sys.path.append(str(Path(__file__).parent))

def resolver_todos_los_desafios():
    """Resuelve todos los desafíos en test_challenges usando el agente conversacional"""
    
    print("🚀 === RESOLVIENDO DESAFÍOS CRIPTOGRÁFICOS REALES ===")
    
    try:
        from conversational_ctf_agent import ConversationalCTFAgent
        print("✅ Agente conversacional cargado")
    except ImportError as e:
        print(f"❌ Error cargando agente: {e}")
        return
    
    # Inicializar agente
    agent = ConversationalCTFAgent()
    
    # Directorio de desafíos
    challenges_dir = Path(__file__).parent / "challenges" / "test_challenges"
    
    if not challenges_dir.exists():
        print(f"❌ Directorio no encontrado: {challenges_dir}")
        return
    
    # Obtener todos los archivos de desafío
    challenge_files = list(challenges_dir.glob("*.txt"))
    
    if not challenge_files:
        print(f"❌ No se encontraron archivos de desafío en {challenges_dir}")
        return
    
    print(f"📊 Encontrados {len(challenge_files)} desafíos para resolver")
    
    results = []
    
    for i, challenge_file in enumerate(challenge_files, 1):
        print(f"\n" + "="*80)
        print(f"🔬 DESAFÍO {i}/{len(challenge_files)}: {challenge_file.name}")
        print("="*80)
        
        try:
            # Leer el desafío
            with open(challenge_file, 'r', encoding='utf-8') as f:
                challenge_content = f.read()
            
            print(f"📝 Contenido del desafío:")
            print("-" * 40)
            print(challenge_content[:300] + ("..." if len(challenge_content) > 300 else ""))
            print("-" * 40)
            
            # Resolver con el agente
            print(f"\n⚡ Resolviendo con agente conversacional...")
            start_time = time.time()
            
            result = agent.solve_challenge_conversational(challenge_content)
            
            end_time = time.time()
            
            # Mostrar resultado
            print(f"\n📊 RESULTADO:")
            print(f"   ✅ Éxito: {result['success']}")
            
            if result['success']:
                print(f"   🏁 Flag encontrada: {result['flag']}")
                print(f"   🛠️  Método: {result.get('method', 'unknown')}")
                print(f"   📈 Confianza: {result.get('confidence', 0):.2f}")
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
            
            print(f"   ⏱️  Tiempo: {end_time - start_time:.2f}s")
            
            # Agregar detalles del análisis si están disponibles
            if result.get('conversation_log'):
                analysis = result['conversation_log'][0] if result['conversation_log'] else {}
                if 'challenge_type' in analysis:
                    print(f"   🔍 Tipo detectado: {analysis['challenge_type']}")
                if 'confidence' in analysis:
                    print(f"   📊 Confianza del análisis: {analysis['confidence']:.2f}")
            
            # Guardar resultado
            results.append({
                'file': challenge_file.name,
                'success': result['success'],
                'flag': result.get('flag'),
                'time': end_time - start_time,
                'method': result.get('method'),
                'error': result.get('error')
            })
            
        except Exception as e:
            print(f"❌ Error procesando {challenge_file.name}: {e}")
            results.append({
                'file': challenge_file.name,
                'success': False,
                'error': str(e),
                'time': 0
            })
        
        # Pausa entre desafíos
        time.sleep(1)
    
    # Resumen final
    print(f"\n" + "="*80)
    print("🏆 RESUMEN FINAL DE RESULTADOS")
    print("="*80)
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    success_rate = successful / total if total > 0 else 0
    
    print(f"📊 Total de desafíos: {total}")
    print(f"✅ Resueltos exitosamente: {successful}")
    print(f"❌ Fallaron: {total - successful}")
    print(f"📈 Tasa de éxito: {success_rate:.1%}")
    
    print(f"\n📋 Detalle por desafío:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"  {status} {result['file']:<25} | {result['time']:.2f}s")
        if result['success']:
            print(f"      🏁 Flag: {result['flag']}")
            print(f"      🛠️  Método: {result.get('method', 'unknown')}")
        else:
            print(f"      ❌ Error: {result['error']}")
    
    # Estadísticas del agente
    print(f"\n📈 Estadísticas del agente:")
    session_stats = agent.get_session_summary()
    for key, value in session_stats.items():
        print(f"  • {key}: {value}")
    
    print(f"\n🎉 ¡Resolución completada!")
    return results

if __name__ == "__main__":
    resolver_todos_los_desafios()