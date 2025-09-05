import os
import json
import glob
import re
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import argparse
from tqdm import tqdm
import logging
import time

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constantes y Configuración ---
# Navegamos dos niveles arriba desde tools/ para llegar a la raíz del proyecto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WRITEUP_DIRECTORIES = [
    os.path.join(PROJECT_ROOT, "data", "expert_writeups"),
    os.path.join(PROJECT_ROOT, "data", "professional_writeups"),
    os.path.join(PROJECT_ROOT, "data", "sekai_writeups"),
]
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "knowledge_base", "processed")
SUPPORTED_EXTENSIONS = ["*.md", "*.txt", "*.py", "*.sage"]

# --- Prompt para el Modelo de IA ---
MODEL_PROMPT = """
You are an expert CTF challenge analyst. Your task is to analyze the content of a write-up and structure it into a clean JSON format.

**Instructions:**
1.  Analyze the provided text, which comes from a file named `{filename}`.
2.  Extract the following fields:
    *   `challenge_category`: Infer the main category (e.g., "rsa", "ecc", "pwn", "web", "forensics"). The filename might contain hints.
    *   `challenge_name`: The official name of the challenge (e.g., "baby-rsa-DICECTF-2022"). The filename is a good source for this.
    *   `ctf_event`: The event where the challenge appeared (e.g., "DICECTF 2022").
    *   `tools_used`: A list of specific tools mentioned (e.g., "cado-nfs", "z3", "pwntools").
    *   `key_concepts`: A list of key cryptographic or technical concepts discussed (e.g., "Chinese Remainder Theorem", "padding oracle attack").
    *   `summary`: A concise, one-paragraph summary of the challenge's core problem and the solution strategy.
    *   `solution_code`: The full, runnable solution code as a single string. If no code is present, or it's fragmented, return `null`.
3.  Return **only** the JSON object, with no other text or explanations.

**Filename:** `{filename}`
**Content:**
---
{content}
---
"""

def get_api_key():
    """Obtiene la clave de API de la variable de entorno."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("La variable de entorno GEMINI_API_KEY no está configurada.")
    return api_key

def is_url(content):
    """Comprueba si el contenido de un archivo es principalmente una URL."""
    # Regex simple para encontrar URLs
    url_pattern = re.compile(r'https?://[^\s]+')
    return url_pattern.match(content.strip())

def get_content_from_url(url):
    """Obtiene y extrae el texto principal de una URL."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # Elimina elementos de script y style
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        # Obtiene el texto
        text = soup.get_text()
        # Limpia el texto
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text
    except requests.RequestException as e:
        logging.error(f"Error al obtener la URL {url}: {e}")
        return None

def find_writeup_files():
    """Encuentra todos los archivos de write-ups en los directorios configurados."""
    all_files = []
    for directory in WRITEUP_DIRECTORIES:
        for extension in SUPPORTED_EXTENSIONS:
            all_files.extend(glob.glob(os.path.join(directory, "**", extension), recursive=True))
    return all_files

def parse_content_with_ai(content, filename, model):
    """Formatea el prompt y llama al modelo de IA para parsear el contenido."""
    prompt = MODEL_PROMPT.format(filename=os.path.basename(filename), content=content)
    try:
        response = model.generate_content(prompt)
        # Limpiar la respuesta para extraer solo el JSON
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(json_text)
    except Exception as e:
        logging.error(f"Error al procesar el archivo {filename} con la IA: {e}")
        # La variable 'response' puede no existir aquí, así que no la registramos.
        # La excepción 'e' ya contiene el mensaje de error relevante de la API.
        return None

def main(args):
    """Función principal para orquestar el proceso de construcción de la base de conocimiento."""
    try:
        api_key = get_api_key()
        genai.configure(api_key=api_key)
    except ValueError as e:
        logging.error(e)
        logging.error("Por favor, configura la variable de entorno GEMINI_API_KEY con tu clave de API.")
        return

    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    logging.info("Buscando archivos de write-ups...")
    writeup_files = find_writeup_files()
    logging.info(f"Se encontraron {len(writeup_files)} archivos.")

    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)

    for filepath in tqdm(writeup_files, desc="Procesando Write-ups"):
        output_filename = os.path.basename(filepath).rsplit('.', 1)[0] + ".json"
        output_path = os.path.join(PROCESSED_DIR, output_filename)

        if os.path.exists(output_path) and not args.force_rebuild:
            logging.info(f"El archivo {output_filename} ya existe. Saltando.")
            continue

        logging.info(f"Procesando: {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if is_url(content):
                logging.info(f"Contenido detectado como URL. Obteniendo de: {content.strip()}")
                content = get_content_from_url(content.strip())
                if not content:
                    continue
            
            parsed_data = parse_content_with_ai(content, filepath, model)

            if parsed_data:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(parsed_data, f, indent=2, ensure_ascii=False)
                logging.info(f"Guardado exitosamente en {output_path}")

        except Exception as e:
            logging.error(f"No se pudo procesar el archivo {filepath}: {e}")

        finally:
            # Pausa de 4 segundos para respetar el límite de la API (15 peticiones/minuto)
            time.sleep(4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Construir la base de conocimiento a partir de archivos de write-ups usando un modelo de IA.")
    parser.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Forzar el reprocesamiento de archivos aunque ya existan en la base de conocimiento."
    )
    args = parser.parse_args()
    main(args)
