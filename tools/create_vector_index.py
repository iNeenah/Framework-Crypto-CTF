import os
import json
import glob
import numpy as np
import faiss
import google.generativeai as genai
from tqdm import tqdm
import logging

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constantes y Configuración ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "knowledge_base", "processed")
INDEX_FILE = os.path.join(PROJECT_ROOT, "data", "knowledge_base", "faiss_index.bin")
MAPPING_FILE = os.path.join(PROJECT_ROOT, "data", "knowledge_base", "index_to_path.json")
EMBEDDING_MODEL = 'text-embedding-004'  # Modelo de embedding de Google

def get_api_key():
    """Obtiene la clave de API de la variable de entorno."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("La variable de entorno GEMINI_API_KEY no está configurada.")
    return api_key

def get_text_from_json(file_path):
    """Concatena campos de texto relevantes de un archivo JSON para crear un documento para embedding."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Unimos los campos de texto más importantes para dar contexto al embedding
        text_parts = [
            data.get('challenge_name', ''),
            data.get('challenge_category', ''),
            data.get('ctf_event', ''),
            data.get('summary', '')
        ]
        # Añadimos listas como strings
        key_concepts = data.get('key_concepts', [])
        if key_concepts:
            text_parts.append(", ".join(key_concepts))
            
        tools_used = data.get('tools_used', [])
        if tools_used:
            text_parts.append(", ".join(tools_used))
            
        return " \n ".join(filter(None, text_parts))
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Error al leer o parsear el archivo {file_path}: {e}")
        return None

def embed_texts(texts):
    """Genera embeddings para una lista de textos usando el modelo de Google."""
    try:
        # El modelo puede manejar lotes de texto directamente
        result = genai.embed_content(model=f'models/{EMBEDDING_MODEL}', content=texts, task_type="RETRIEVAL_DOCUMENT")
        return result['embedding']
    except Exception as e:
        logging.error(f"Error al generar embeddings: {e}")
        return None

def main():
    """Función principal para crear y guardar el índice FAISS y el mapeo."""
    try:
        api_key = get_api_key()
        genai.configure(api_key=api_key)
    except ValueError as e:
        logging.error(e)
        return

    json_files = glob.glob(os.path.join(PROCESSED_DIR, "*.json"))
    if not json_files:
        logging.warning("No se encontraron archivos JSON en el directorio de procesados. Ejecuta primero build_knowledge_base.py")
        return

    logging.info(f"Se encontraron {len(json_files)} archivos JSON para indexar.")

    # Extraer texto y guardar las rutas de los archivos correspondientes
    texts_to_embed = []
    valid_file_paths = []
    for file_path in tqdm(json_files, desc="Leyendo archivos JSON"):
        text = get_text_from_json(file_path)
        if text:
            texts_to_embed.append(text)
            valid_file_paths.append(file_path)

    if not texts_to_embed:
        logging.error("No se pudo extraer texto de ningún archivo JSON.")
        return

    # Generar embeddings en un solo lote
    logging.info(f"Generando embeddings para {len(texts_to_embed)} documentos...")
    embeddings = embed_texts(texts_to_embed)
    if not embeddings:
        logging.error("Falló la generación de embeddings. Abortando.")
        return
    
    embeddings_np = np.array(embeddings, dtype='float32')
    
    # Crear y construir el índice FAISS
    dimension = embeddings_np.shape[1]
    logging.info(f"Creando índice FAISS con dimensión {dimension}.")
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_np)

    # Guardar el índice y el mapeo
    logging.info(f"Guardando el índice FAISS en {INDEX_FILE}")
    faiss.write_index(index, INDEX_FILE)

    logging.info(f"Guardando el mapeo de índice a ruta en {MAPPING_FILE}")
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(valid_file_paths, f, indent=2)

    logging.info("¡La base de conocimiento vectorial ha sido creada exitosamente!")

if __name__ == "__main__":
    main()
