#!/usr/bin/env python3
"""
CRYPTO CTF FRAMEWORK - Advanced ML-Powered CTF Solver
======================================================

Un framework avanzado de Machine Learning que resuelve desafíos CTF de criptografía
aprendiendo de writeups profesionales y aplicando técnicas expertas.

Autor: iNeenah
Repositorio: https://github.com/iNeenah/Framework-Crypto-CTF
Licencia: MIT
"""
import os
import sys
from pathlib import Path

# Agregar framework al path
framework_path = Path(__file__).parent / "framework"
sys.path.insert(0, str(framework_path))

def main():
    """Punto de entrada principal del framework"""
    print("""
🚀 CRYPTO CTF FRAMEWORK - ML-POWERED SOLVER
===========================================

Framework avanzado de Machine Learning para resolver desafíos CTF
que aprende de writeups profesionales y aplica técnicas expertas.

Iniciando sistema de gestión...
    """)
    
    # Importar y ejecutar el framework de gestión
    try:
        # Cambiar al directorio del script para rutas relativas
        os.chdir(Path(__file__).parent)
        
        # Importar desde framework.core
        sys.path.insert(0, "framework")
        from core.manage_ctf_framework import main as manage_main
        manage_main()
    except ImportError as e:
        print(f"❌ Error importando framework: {e}")
        print("   Asegúrate de que la estructura del proyecto esté correcta")
        print("   Verifica que existan los archivos:")
        print("   - framework/core/manage_ctf_framework.py")
        print("   - framework/ml/expert_ml_framework.py")
    except Exception as e:
        print(f"❌ Error ejecutando framework: {e}")

if __name__ == "__main__":
    main()