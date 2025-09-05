import os
import json
import re
from pathlib import Path
import logging

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Directories to search for training data
DATA_SOURCE_DIRS = [
    'challenges/training_data',
    'data/sekai_writeups',
    'data/expert_writeups'
]

# File patterns for discovery
SOLUTION_PATTERNS = ['*_solve.py', '*_solver.py', '*.sage', 'solution.py']
DESCRIPTION_PATTERNS = ['*README.md', '*README', 'problem.txt', 'description.txt', 'descriptiion.txt']

# --- Helper Functions ---

def find_crypto_imports(content):
    """Extracts crypto-related imports from a Python/Sage script."""
    imports = []
    # This regex is designed to find common crypto libraries
    # It's not perfect but covers pycryptodome, cryptography, hashlib, etc.
    pattern = re.compile(r'from\s+(Crypto|cryptography)[\.\w]*\s+import\s+[\w, ]+|import\s+(hashlib|base64|secrets)')
    matches = pattern.findall(content)
    # The regex returns tuples, so we need to flatten and clean them
    for match in matches:
        if isinstance(match, tuple):
            imports.extend([item for item in match if item])
        else:
            imports.append(match)
    return list(set(imports))

# --- Data Processors ---

def process_structured_json(file_path):
    """Processes well-structured JSON files from challenges/training_data."""
    logging.info(f"Processing JSON file: {file_path}")
    dataset = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'challenges' not in data or not isinstance(data['challenges'], list):
            return []

        for challenge in data['challenges']:
            # We prefer the explicit 'techniques' field as labels
            # If not available, we fall back to parsing the solution code
            labels = challenge.get('techniques', [])
            if not labels and challenge.get('solution_codes'):
                # Assuming the first code block is the most relevant
                code = challenge['solution_codes'][0][1] if challenge['solution_codes'][0] else ""
                labels = find_crypto_imports(code)

            if challenge.get('description') and labels:
                dataset.append({
                    'id': f"{Path(file_path).stem}_{challenge.get('name', '').replace(' ', '_')}",
                    'description': challenge['description'],
                    'labels': labels,
                    'source': str(file_path)
                })
    except Exception as e:
        logging.error(f"Could not process JSON {file_path}: {e}")
    return dataset

def process_unstructured_dir(dir_path):
    """Processes directories with separate problem/solution files."""
    logging.info(f"Processing directory: {dir_path}")
    dataset = []
    solution_file = None
    description_file = None

    for pattern in SOLUTION_PATTERNS:
        found = list(dir_path.glob(pattern))
        if found:
            solution_file = found[0]
            break
    
    for pattern in DESCRIPTION_PATTERNS:
        found = list(dir_path.glob(pattern))
        if found:
            description_file = found[0]
            break

    if solution_file and description_file:
        try:
            with open(solution_file, 'r', encoding='utf-8') as f:
                solution_content = f.read()
            with open(description_file, 'r', encoding='utf-8') as f:
                description_content = f.read()
            
            labels = find_crypto_imports(solution_content)
            if description_content and labels:
                dataset.append({
                    'id': dir_path.name,
                    'description': description_content,
                    'labels': labels,
                    'source': str(dir_path)
                })
        except Exception as e:
            logging.error(f"Could not process directory {dir_path}: {e}")
    return dataset

# --- Main Orchestrator ---

def process_all_data(base_path):
    """Finds and processes all available training data sources."""
    project_root = Path(base_path)
    full_dataset = []

    for source_dir in DATA_SOURCE_DIRS:
        source_path = project_root / source_dir
        if not source_path.exists():
            logging.warning(f"Source directory not found, skipping: {source_path}")
            continue
        
        logging.info(f"Scanning source directory: {source_path}")
        for root, dirs, files in os.walk(source_path):
            # Prioritize structured JSONs
            for file in files:
                if file.endswith('.json'):
                    full_dataset.extend(process_structured_json(Path(root) / file))
            
            # Process unstructured directories
            # This logic assumes one challenge per directory
            if any(p.match(f) for p in [Path(pattern) for pattern in SOLUTION_PATTERNS] for f in files):
                 full_dataset.extend(process_unstructured_dir(Path(root)))

    # Remove duplicates by ID
    unique_dataset = {item['id']: item for item in full_dataset}.values()
    
    output_path = project_root / 'data' / 'ml'
    output_path.mkdir(exist_ok=True)
    output_file = output_path / 'processed_challenges.json'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(list(unique_dataset), f, indent=4)

    logging.info(f"TOTAL: Successfully processed {len(unique_dataset)} unique challenges.")
    logging.info(f"Dataset saved to {output_file}")

if __name__ == '__main__':
    project_root = os.getcwd()
    process_all_data(project_root)