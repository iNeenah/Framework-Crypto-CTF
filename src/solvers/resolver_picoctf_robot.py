#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resolver PicoCTF Robot Challenge
==============================
Usando el agente conversacional para resolver el desafío del robot.
"""

import sys
from pathlib import Path

# Añadir al path
sys.path.append(str(Path(__file__).parent))

def resolver_picoctf_robot():
    """Resuelve el desafío del robot de PicoCTF"""
    
    print("🤖 === RESOLVIENDO DESAFÍO PICOCTF ROBOT ===")
    
    try:
        from conversational_ctf_agent import ConversationalCTFAgent
        print("✅ Agente conversacional cargado")
    except ImportError as e:
        print(f"❌ Error cargando agente: {e}")
        return
    
    # Leer los archivos del desafío
    picoctf_dir = Path("challenges/uploaded/picoCTF")
    
    # Leer descripción
    with open(picoctf_dir / "descripcion.txt", 'r', encoding='utf-8') as f:
        descripcion = f.read()
    
    # Leer código crypto
    with open(picoctf_dir / "crypto.py", 'r', encoding='utf-8') as f:
        crypto_code = f.read()
    
    # Crear el desafío completo
    challenge_completo = f"""
PicoCTF Robot Challenge
======================

DESCRIPCIÓN:
{descripcion}

CÓDIGO CRIPTOGRÁFICO (crypto.py):
{crypto_code}

ANÁLISIS REQUERIDO:
Este desafío requiere:
1. Análisis del protocolo de comunicación
2. Identificación de vulnerabilidades en el HMAC
3. Posible ataque de extensión de longitud o reutilización de nonce
4. Explotación de la función compute_hmac que usa un bucle de 32 iteraciones

OBJETIVO:
Encontrar una vulnerabilidad en el protocolo criptográfico para controlar el robot y obtener la flag.
"""
    
    print("📝 Desafío completo preparado:")
    print("-" * 50)
    print(challenge_completo[:500] + "..." if len(challenge_completo) > 500 else challenge_completo)
    print("-" * 50)
    
    # Inicializar agente
    print("\n🤖 Inicializando agente conversacional...")
    agent = ConversationalCTFAgent()
    
    # Resolver
    print("\n⚡ Resolviendo desafío con IA...")
    result = agent.solve_challenge_conversational(challenge_completo)
    
    # Mostrar resultado
    print(f"\n📊 RESULTADO:")
    print(f"   ✅ Éxito: {result['success']}")
    
    if result['success']:
        print(f"   🏁 Resultado: {result['flag']}")
        print(f"   🛠️  Método: {result.get('method', 'unknown')}")
        print(f"   📈 Confianza: {result.get('confidence', 0):.2f}")
    else:
        print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
    
    print(f"   ⏱️  Tiempo: {result['execution_time']:.2f}s")
    
    # Mostrar análisis detallado
    if result.get('conversation_log'):
        analysis = result['conversation_log'][0] if result['conversation_log'] else {}
        print(f"\n🔍 Análisis detallado:")
        print(f"   • Tipo detectado: {analysis.get('challenge_type', 'unknown')}")
        print(f"   • Estrategia: {analysis.get('recommended_strategy', 'unknown')}")
        print(f"   • Técnicas sugeridas: {analysis.get('techniques_needed', [])}")
    
    return result

if __name__ == "__main__":
    resolver_picoctf_robot()