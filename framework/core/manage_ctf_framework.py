#!/usr/bin/env python3
"""
MANAGE CTF FRAMEWORK - Gestión Completa del Framework CTF con IA
================================================================

Script principal para gestionar todo el framework:
- Agregar desafíos
- Entrenar IA automáticamente
- Resolver desafíos
- Monitorear progreso

Este es el punto de entrada principal para tu framework.
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime


def show_main_menu():
    """Mostrar menú principal"""
    print("""
🎯 CRYPTO CTF FRAMEWORK - GESTIÓN COMPLETA
==========================================

1. 📁 Agregar nuevo desafío
2. 🧠 Entrenar IA con desafíos actuales
3. 🔧 Resolver desafío específico
4. 🔄 Entrenamiento automático completo
5. 📊 Ver estadísticas del framework
6. 🧪 Probar IA con test challenges
7. 📋 Listar desafíos subidos
8. 🎓 EXPERT ML: Aprender de writeups profesionales
9. 🔮 EXPERT ML: Predecir con conocimiento experto
10. ❌ Salir

Selecciona una opción (1-10):""")


def add_challenge():
    """Agregar nuevo desafío interactivamente"""
    print("\n🎯 AGREGAR NUEVO DESAFÍO")
    print("=" * 30)
    
    print("Opciones:")
    print("1. Crear desde plantilla")
    print("2. Desde archivo existente")
    print("3. Desafío de red (host:puerto)")
    
    choice = input("\nSelecciona (1-3): ").strip()
    
    if choice == "1":
        os.system("python framework/core/add_challenge.py --interactive")
    elif choice == "2":
        file_path = input("Ruta del archivo: ").strip()
        os.system(f'python framework/core/add_challenge.py --file "{file_path}"')
    elif choice == "3":
        network = input("Host:Puerto (ej: 127.0.0.1:1337): ").strip()
        os.system(f'python framework/core/add_challenge.py --network "{network}"')
    else:
        print("❌ Opción inválida")


def train_ai():
    """Entrenar IA con desafíos actuales"""
    print("\n🧠 ENTRENANDO IA...")
    print("=" * 20)
    
    # Primero recopilar datos
    print("1. Recopilando datos de desafíos...")
    os.system("python tools/auto_train_framework.py")
    
    # Luego entrenar IA
    print("\n2. Entrenando modelo de IA...")
    os.system("python tools/integrated_ai_framework.py --train")
    
    print("\n✅ Entrenamiento completado!")


def solve_challenge():
    """Resolver desafío específico"""
    print("\n🔧 RESOLVER DESAFÍO")
    print("=" * 18)
    
    file_path = input("Ruta del desafío a resolver: ").strip()
    
    if not file_path:
        print("❌ Debe especificar un archivo")
        return
    
    print(f"\n🎯 Resolviendo: {file_path}")
    print("-" * 40)
    
    # Intentar con IA primero
    print("🧠 Intentando con IA...")
    os.system(f'python integrated_ai_framework.py --solve "{file_path}"')
    
    # Alternativa simple
    print("\n🔧 Alternativa con solucionador simple...")
    os.system(f'python solve_ctf.py "{file_path}"')


def auto_training():
    """Entrenamiento automático completo"""
    print("\n🔄 ENTRENAMIENTO AUTOMÁTICO COMPLETO")
    print("=" * 40)
    
    print("Ejecutando ciclo completo...")
    os.system("python integrated_ai_framework.py --auto")


def show_stats():
    """Mostrar estadísticas del framework"""
    print("\n📊 ESTADÍSTICAS DEL FRAMEWORK")
    print("=" * 30)
    
    # Contar desafíos subidos
    uploaded_dir = Path("challenges/uploaded")
    if uploaded_dir.exists():
        challenges = list(uploaded_dir.rglob("*.txt"))
        print(f"📁 Desafíos subidos: {len(challenges)}")
    else:
        print("📁 Desafíos subidos: 0")
    
    # Contar desafíos resueltos
    solved_dir = Path("challenges/solved")
    if solved_dir.exists():
        solved = list(solved_dir.glob("*.json"))
        print(f"✅ Desafíos resueltos: {len(solved)}")
    else:
        print("✅ Desafíos resueltos: 0")
    
    # Estado de IA
    model_file = Path("models/ai_model.json")
    if model_file.exists():
        try:
            with open(model_file, 'r') as f:
                model_data = json.load(f)
            print(f"🧠 Modelo IA: Entrenado con {model_data['total_samples']} samples")
            print(f"📊 Tipos conocidos: {', '.join(model_data['classification_rules'].keys())}")
        except:
            print("🧠 Modelo IA: Error leyendo modelo")
    else:
        print("🧠 Modelo IA: No entrenado")
    
    # Datos de entrenamiento
    training_file = Path("data/ml/ml_dataset.json")
    if training_file.exists():
        try:
            with open(training_file, 'r') as f:
                training_data = json.load(f)
            print(f"📚 Dataset ML: {training_data['total_samples']} samples")
            print("📊 Distribución:")
            for challenge_type, count in training_data['type_distribution'].items():
                print(f"   {challenge_type}: {count}")
        except:
            print("📚 Dataset ML: Error leyendo datos")
    else:
        print("📚 Dataset ML: No disponible")


def test_ai():
    """Probar IA con desafíos de test"""
    print("\n🧪 PROBANDO IA")
    print("=" * 14)
    
    os.system("python integrated_ai_framework.py --test")


def list_challenges():
    """Listar desafíos subidos"""
    print("\n📋 DESAFÍOS SUBIDOS")
    print("=" * 18)
    
    os.system("python add_challenge.py --list")


def expert_ml_learning():
    """Entrenamiento Expert ML con writeups profesionales"""
    print("\n🎓 EXPERT ML - APRENDIZAJE DE WRITEUPS PROFESIONALES")
    print("=" * 55)
    
    print("""Este modo te permite entrenar el framework con writeups de profesionales.
    
🎯 ¿Cómo funciona?
- Analiza writeups de expertos en CTF
- Extrae técnicas, herramientas y patrones
- Entrena modelos ML/DL para predecir estrategias
- Aprende como resuelven los profesionales

📂 Opciones de entrada:
1. Archivo de writeup individual
2. Directorio con múltiples writeups
3. URL de writeup online""")
    
    print("\nSelecciona opción:")
    print("1. Entrenar con archivo writeup")
    print("2. Entrenar con directorio de writeups")
    print("3. Entrenar con URL")
    print("4. Ver estado del modelo expert")
    
    choice = input("\nOpción (1-4): ").strip()
    
    if choice == "1":
        file_path = input("Ruta del archivo writeup: ").strip()
        if file_path:
            print(f"\n🧠 Analizando writeup: {file_path}")
            os.system(f'python framework/ml/expert_ml_framework.py --learn-file "{file_path}"')
        else:
            print("❌ Debe especificar un archivo")
            
    elif choice == "2":
        dir_path = input("Ruta del directorio: ").strip()
        if dir_path:
            print(f"\n🧠 Analizando writeups en: {dir_path}")
            os.system(f'python framework/ml/expert_ml_framework.py --learn-dir "{dir_path}"')
        else:
            print("❌ Debe especificar un directorio")
            
    elif choice == "3":
        url = input("URL del writeup: ").strip()
        if url:
            print(f"\n🧠 Descargando y analizando: {url}")
            os.system(f'python framework/ml/expert_ml_framework.py --learn-url "{url}"')
        else:
            print("❌ Debe especificar una URL")
            
    elif choice == "4":
        print("\n📊 Estado del modelo Expert ML:")
        os.system("python framework/ml/expert_ml_framework.py --status")
        
    else:
        print("❌ Opción inválida")


def expert_ml_prediction():
    """Predicción Expert ML para resolver desafíos complejos"""
    print("\n🔮 EXPERT ML - PREDICCIÓN CON CONOCIMIENTO EXPERTO")
    print("=" * 52)
    
    print("""Este modo usa el conocimiento aprendido de writeups profesionales
para resolver desafíos complejos de criptografía.
    
🎯 ¿Qué hace?
- Analiza el desafío con técnicas de expertos
- Predice la mejor estrategia de resolución
- Aplica patrones aprendidos de profesionales
- Sugiere herramientas y técnicas específicas""")
    
    print("\nOpciones:")
    print("1. Resolver desafío con Expert ML")
    print("2. Analizar desafío (solo predicción)")
    print("3. Resolver con explicación detallada")
    
    choice = input("\nOpción (1-3): ").strip()
    
    if choice in ["1", "2", "3"]:
        file_path = input("Ruta del desafío: ").strip()
        
        if not file_path:
            print("❌ Debe especificar un archivo")
            return
            
        print(f"\n🔮 Analizando con Expert ML: {file_path}")
        print("-" * 40)
        
        if choice == "1":
            # Resolución completa
            os.system(f'python expert_ml_framework.py --solve "{file_path}"')
        elif choice == "2":
            # Solo análisis/predicción
            os.system(f'python expert_ml_framework.py --analyze "{file_path}"')
        elif choice == "3":
            # Resolución con explicación
            os.system(f'python expert_ml_framework.py --solve-verbose "{file_path}"')
            
    else:
        print("❌ Opción inválida")


def show_quick_guide():
    """Mostrar guía rápida"""
    print("""
🚀 GUÍA RÁPIDA - CÓMO USAR EL FRAMEWORK
=======================================

1. AGREGAR DESAFÍOS:
   - Opción 1: Crear desafíos desde plantillas
   - Opción 2: Subir archivos de desafíos existentes
   - Los desafíos se guardan en challenges/uploaded/

2. ENTRENAR IA:
   - Opción 2: Entrena automáticamente con todos los desafíos
   - La IA aprende a clasificar tipos de criptografía
   - Mejora la precisión con más datos

3. RESOLVER DESAFÍOS:
   - Opción 3: Resolver desafíos específicos
   - Usa IA + plugins para resolver automáticamente
   - Devuelve flags en formato crypto{...}

4. FLUJO RECOMENDADO:
   📁 Agregar varios desafíos (1)
   🧠 Entrenar IA (2)
   🔧 Resolver desafíos nuevos (3)
   🔄 Repetir para mejorar

5. ARCHIVOS IMPORTANTES:
   - challenges/uploaded/ : Tus desafíos
   - models/ai_model.json : Modelo entrenado
   - data/ml/ : Datos de entrenamiento
   - challenges/solved/ : Desafíos resueltos

¡Empieza agregando algunos desafíos y entrenando la IA!
    """)


def main():
    """Función principal"""
    print("🎯 CRYPTO CTF FRAMEWORK - SISTEMA COMPLETO CON IA")
    print("=" * 50)
    
    # Verificar estructura de directorios
    required_dirs = [
        "challenges/uploaded",
        "challenges/solved", 
        "data/ml",
        "models"
    ]
    
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    while True:
        show_main_menu()
        
        try:
            choice = input().strip()
            
            if choice == "1":
                add_challenge()
            elif choice == "2":
                train_ai()
            elif choice == "3":
                solve_challenge()
            elif choice == "4":
                auto_training()
            elif choice == "5":
                show_stats()
            elif choice == "6":
                test_ai()
            elif choice == "7":
                list_challenges()
            elif choice == "8":
                expert_ml_learning()
            elif choice == "9":
                expert_ml_prediction()
            elif choice == "10":
                print("\n👋 ¡Hasta luego!")
                break
            elif choice.lower() in ['help', 'h', '?']:
                show_quick_guide()
            else:
                print("❌ Opción inválida. Usa 1-10.")
            
            # Solo pedir Enter si no es salida
            if choice != "10":
                try:
                    input("\n📝 Presiona Enter para continuar...")
                except (KeyboardInterrupt, EOFError):
                    print("\n\n👋 ¡Hasta luego!")
                    break
            
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            try:
                input("📝 Presiona Enter para continuar...")
            except (KeyboardInterrupt, EOFError):
                print("\n\n👋 ¡Hasta luego!")
                break


if __name__ == "__main__":
    main()