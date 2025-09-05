import os
import json
import faiss
import numpy as np
import google.generativeai as genai
import logging

# --- Constantes ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_PATH = os.path.join(PROJECT_ROOT, "data", "knowledge_base")
INDEX_FILE = os.path.join(KB_PATH, "faiss_index.bin")
MAPPING_FILE = os.path.join(KB_PATH, "index_to_path.json")
EMBEDDING_MODEL = 'models/text-embedding-004'
GENERATIVE_MODEL = 'gemini-1.5-flash-latest'

# --- Nuevo Prompt Template para Desafíos de Red ---
FINAL_PROMPT_TEMPLATE = """
**ROLE:** You are a world-class cybersecurity expert and CTF player, specializing in cryptography.

**TASK:** Write a Python script to solve the following live network-based cryptography challenge.

**CONTEXT:** To help you, I have found {num_examples} similar challenges that were solved in the past. Use them as a reference for techniques, tools, and code patterns.

**--- SIMILAR EXAMPLES ---

{context}

**--- NEW LIVE CHALLENGE TO SOLVE ---

**Challenge Description:**
{description}

**Connection Details:**
- **Host:** {host}
- **Port:** {port}

**INSTRUCTIONS:**
1.  Analyze the new challenge description and the provided examples.
2.  Formulate a clear, step-by-step plan to solve it.
3.  **Write a final, complete, and runnable Python script.**
4.  The script **MUST** use the `pwntools` library to connect to the server at `{host}:{port}`.
5.  The script should perform the necessary interactions, solve the cryptographic puzzle, and print the flag.
6.  If you need other libraries like `PyCryptodome` or `sympy`, import them in the script.
7.  Present your final answer clearly, with the explanation first, followed by the complete Python code block.
"""

class CryptoAgent:
    def __init__(self):
        """Inicializa el agente, cargando la base de conocimiento y los modelos de IA."""
        logging.info("Inicializando CryptoAgent...")
        self.api_key = self._get_api_key()
        genai.configure(api_key=self.api_key)
        
        self.index = self._load_faiss_index()
        self.path_mapping = self._load_path_mapping()
        
        self.generative_model = genai.GenerativeModel(GENERATIVE_MODEL)
        logging.info("CryptoAgent inicializado exitosamente.")

    def _get_api_key(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logging.error("La variable de entorno GEMINI_API_KEY no está configurada.")
            raise ValueError("No se encontró la clave de API.")
        return api_key

    def _load_faiss_index(self):
        if not os.path.exists(INDEX_FILE):
            logging.error(f"No se encontró el archivo de índice FAISS en {INDEX_FILE}")
            raise FileNotFoundError("El índice FAISS no existe. Ejecuta create_vector_index.py primero.")
        logging.info("Cargando índice FAISS...")
        return faiss.read_index(INDEX_FILE)

    def _load_path_mapping(self):
        if not os.path.exists(MAPPING_FILE):
            logging.error(f"No se encontró el archivo de mapeo en {MAPPING_FILE}")
            raise FileNotFoundError("El archivo de mapeo no existe.")
        logging.info("Cargando mapeo de rutas...")
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _embed_query(self, text):
        """Genera un embedding para un texto de consulta."""
        return genai.embed_content(model=EMBEDDING_MODEL, content=text, task_type="RETRIEVAL_QUERY")['embedding']

    def _search_knowledge_base(self, query_vector, k=3):
        """Busca en el índice FAISS y devuelve las rutas y las distancias."""
        logging.info(f"Buscando los {k} write-ups más similares...")
        distances, indices = self.index.search(np.array([query_vector], dtype='float32'), k)
        
        results = []
        if indices.size == 0:
            return results
            
        for i, dist in zip(indices[0], distances[0]):
            if i == -1: continue # Ignorar resultados inválidos
            similarity = max(0, 100 * (1 - dist / 2))
            results.append({
                "path": self.path_mapping[i],
                "similarity": similarity
            })
        return results

    def _get_retrieved_context(self, file_paths):
        """Lee y formatea el contenido de los archivos JSON recuperados."""
        context_str = ""
        for i, path in enumerate(file_paths):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                context_str += f"--- Example {i+1}: {data.get('challenge_name', 'N/A')} ---\n"
                context_str += f"Summary: {data.get('summary', 'N/A')}\n"
                if data.get('solution_code'):
                    context_str += f"Solution Code:\n```python\n{data['solution_code']}\n```\n\n"
            except Exception as e:
                logging.warning(f"No se pudo leer o procesar el archivo de contexto {path}: {e}")
        return context_str

    def _build_final_prompt(self, description, host, port, context, num_examples):
        """Construye el prompt final para el modelo generativo."""
        return FINAL_PROMPT_TEMPLATE.format(
            num_examples=num_examples, 
            context=context, 
            description=description,
            host=host,
            port=port
        )

    def solve(self, description, host, port):
        """
        Orquesta el proceso RAG como un generador para resolver un desafío de red.
        """
        # 1. Embed query (usando la descripción del desafío)
        yield {"status": "embedding_query", "message": "Analizando y vectorizando la descripción del desafío..."}
        query_vector = self._embed_query(description)
        
        # 2. Search
        yield {"status": "searching_kb", "message": "Buscando en la base de conocimiento..."}
        search_results = self._search_knowledge_base(query_vector, k=3)
        yield {"status": "found_results", "data": search_results, "message": f"Se encontraron {len(search_results)} write-ups relevantes."}
        
        # 3. Retrieve
        yield {"status": "retrieving_context", "message": "Recuperando y formateando el contexto..."}
        similar_paths = [res["path"] for res in search_results]
        context = self._get_retrieved_context(similar_paths)
        
        # 4. Augment & Generate
        yield {"status": "generating_solution", "message": "Construyendo prompt final y consultando al modelo generativo..."}
        final_prompt = self._build_final_prompt(description, host, port, context, len(similar_paths))
        
        response_stream = self.generative_model.generate_content(final_prompt, stream=True)
        
        # 5. Stream solution
        yield {"status": "streaming_solution", "message": "Recibiendo respuesta del agente..."}
        for chunk in response_stream:
            if chunk and chunk.text:
                yield {"status": "solution_chunk", "data": chunk.text}
        
        yield {"status": "done", "message": "Proceso completado."}