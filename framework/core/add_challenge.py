#!/usr/bin/env python3
"""
ADD CHALLENGE - Agregar Nuevos Desafíos CTF
===========================================

Script para agregar fácilmente nuevos desafíos al framework.
Formatos soportados:
- Archivo de texto con descripción y datos
- Conexión de red (host:puerto)  
- Plantilla de desafío

"""
import sys
import os
from pathlib import Path
from datetime import datetime


def create_challenge_template(challenge_type: str = "general") -> str:
    """Crear plantilla para nuevo desafío"""
    
    templates = {
        "caesar": """# Desafío César CTF
Descripción: Cifrado César con shift desconocido
Tipo: CLASSICAL_CRYPTO
Dificultad: EASY

Texto cifrado:
WKLV LV D FDHVDU FLSKHU ZLWK VKLIW 3

FLAG: {flag_aqui}
""",
        
        "rsa": """# Desafío RSA CTF  
Descripción: Factorización RSA con números pequeños
Tipo: PUBLIC_KEY_CRYPTO
Dificultad: MEDIUM

Parámetros RSA:
n = 143
e = 7
c = 123

FLAG: {flag_aqui}
""",

        "base64": """# Desafío Base64 CTF
Descripción: Mensaje codificado en Base64
Tipo: ENCODING  
Dificultad: EASY

Mensaje codificado:
SGVsbG8gV29ybGQhIFRoaXMgaXMgYSBiYXNlNjQgZW5jb2RlZCBtZXNzYWdl

FLAG: {flag_aqui}
""",

        "xor": """# Desafío XOR CTF
Descripción: Cifrado XOR con clave desconocida
Tipo: SYMMETRIC_CRYPTO
Dificultad: MEDIUM

Datos cifrados (hex):
1c0e0a1c1c151b1c1a0c0a1c1b1c1a0c0a1c

FLAG: {flag_aqui}
""",

        "network": """# Desafío de Red CTF
Descripción: Servicio remoto con flag oculta
Tipo: NETWORK
Dificultad: MEDIUM

Conexión:
Host: ejemplo.com
Puerto: 1337
Protocolo: TCP

Instrucciones:
Conectarse al servicio y extraer la flag

FLAG: {flag_aqui}
""",

        "general": """# Nuevo Desafío CTF
Descripción: [Describe aquí el desafío]
Tipo: [CLASSICAL_CRYPTO | PUBLIC_KEY_CRYPTO | SYMMETRIC_CRYPTO | ENCODING | NETWORK | FORENSICS]
Dificultad: [EASY | MEDIUM | HARD | EXTREME]

Datos del desafío:
[Pon aquí los datos cifrados, código, archivos, etc.]

Pistas (opcional):
- [Pista 1]
- [Pista 2]

FLAG: {flag_aqui}
"""
    }
    
    return templates.get(challenge_type, templates["general"])


def add_challenge_from_file(file_path: str) -> bool:
    """Agregar desafío desde archivo existente"""
    source_path = Path(file_path)
    
    if not source_path.exists():
        print(f"❌ Archivo no encontrado: {file_path}")
        return False
    
    # Crear nombre único
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_name = f"{source_path.stem}_{timestamp}.txt"
    dest_path = Path("challenges/uploaded") / dest_name
    
    # Crear directorio si no existe
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Copiar archivo
        import shutil
        shutil.copy2(source_path, dest_path)
        
        print(f"✅ Desafío agregado: {dest_path}")
        print(f"🔧 Ejecuta: python auto_train_framework.py")
        return True
        
    except Exception as e:
        print(f"❌ Error copiando archivo: {e}")
        return False


def add_challenge_interactive() -> bool:
    """Agregar desafío de forma interactiva"""
    print("🎯 AGREGAR NUEVO DESAFÍO CTF")
    print("=" * 40)
    
    # Preguntar tipo
    print("\nTipos disponibles:")
    print("1. caesar - Cifrado César")
    print("2. rsa - RSA")
    print("3. base64 - Base64") 
    print("4. xor - XOR")
    print("5. network - Red/Netcat")
    print("6. general - Plantilla general")
    
    type_choice = input("\nSelecciona tipo (1-6): ").strip()
    type_map = {"1": "caesar", "2": "rsa", "3": "base64", "4": "xor", "5": "network", "6": "general"}
    challenge_type = type_map.get(type_choice, "general")
    
    # Preguntar nombre
    challenge_name = input("Nombre del desafío: ").strip()
    if not challenge_name:
        challenge_name = f"challenge_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Crear archivo
    template = create_challenge_template(challenge_type)
    dest_path = Path("challenges/uploaded") / f"{challenge_name}.txt"
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(template)
        
        print(f"\n✅ Plantilla creada: {dest_path}")
        print(f"📝 Edita el archivo para completar los datos")
        print(f"🔧 Después ejecuta: python auto_train_framework.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando plantilla: {e}")
        return False


def add_challenge_from_text(content: str, name: str = None) -> bool:
    """Agregar desafío desde texto directo"""
    if not name:
        name = f"text_challenge_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    dest_path = Path("challenges/uploaded") / f"{name}.txt"
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Desafío agregado: {dest_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error guardando desafío: {e}")
        return False


def add_network_challenge(host: str, port: int, description: str = "") -> bool:
    """Agregar desafío de red"""
    content = f"""# Desafío de Red CTF
Descripción: {description or f"Conexión a {host}:{port}"}
Tipo: NETWORK
Dificultad: MEDIUM

Conexión:
Host: {host}
Puerto: {port}
Protocolo: TCP

Instrucciones:
Conectarse al servicio y extraer la flag usando netcat o similar:
nc {host} {port}

FLAG: {{flag_pendiente}}
"""
    
    name = f"network_{host}_{port}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return add_challenge_from_text(content, name)


def list_uploaded_challenges():
    """Listar desafíos subidos"""
    uploaded_dir = Path("challenges/uploaded")
    
    if not uploaded_dir.exists():
        print("❌ Directorio challenges/uploaded no existe")
        return
    
    challenges = list(uploaded_dir.rglob("*.txt"))
    
    print(f"📁 DESAFÍOS SUBIDOS ({len(challenges)}):")
    print("-" * 40)
    
    for i, challenge_path in enumerate(challenges, 1):
        # Leer primera línea para obtener descripción
        try:
            with open(challenge_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
            description = first_line.replace('#', '').strip()[:50]
        except:
            description = "Sin descripción"
        
        print(f"{i:2d}. {challenge_path.name}")
        print(f"    {description}")
    
    if challenges:
        print(f"\n🔧 Para procesar: python auto_train_framework.py")


def main():
    """Función principal"""
    if len(sys.argv) == 1:
        print("""
🎯 ADD CHALLENGE - Agregar Desafíos CTF
======================================

Opciones:
  python add_challenge.py --interactive     # Modo interactivo
  python add_challenge.py --file archivo    # Desde archivo
  python add_challenge.py --network host:puerto  # Desafío de red
  python add_challenge.py --list            # Listar subidos
  python add_challenge.py --text "contenido"  # Desde texto

Ejemplos:
  python add_challenge.py --interactive
  python add_challenge.py --file mi_desafio.txt
  python add_challenge.py --network "127.0.0.1:1337"
  python add_challenge.py --text "Caesar cipher: WKLV LV D WHVW"
        """)
        return
    
    command = sys.argv[1]
    
    if command == "--interactive":
        add_challenge_interactive()
        
    elif command == "--file" and len(sys.argv) > 2:
        add_challenge_from_file(sys.argv[2])
        
    elif command == "--network" and len(sys.argv) > 2:
        network_info = sys.argv[2]
        if ':' in network_info:
            host, port = network_info.split(':')
            add_network_challenge(host, int(port))
        else:
            print("❌ Formato: host:puerto")
            
    elif command == "--text" and len(sys.argv) > 2:
        content = sys.argv[2]
        add_challenge_from_text(content)
        
    elif command == "--list":
        list_uploaded_challenges()
        
    else:
        print("❌ Comando no reconocido. Usa --help para ver opciones.")


if __name__ == "__main__":
    main()