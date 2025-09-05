#!/usr/bin/env python3
"""
CryptoHack Writeup Downloader
=============================
Descargador especializado para writeups de CryptoHack sobre curvas elípticas
"""

import requests
import re
import os
import json
from datetime import datetime

class CryptoHackDownloader:
    def __init__(self, base_dir="training_data"):
        self.base_dir = base_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def download_cryptohack_writeup(self, url):
        """Descarga y procesa writeup de CryptoHack"""
        print(f"🎯 Descargando CryptoHack writeup: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            content = response.text
            
            # Extraer título
            title_match = re.search(r'<title>(.*?)</title>', content)
            title = title_match.group(1) if title_match else "CryptoHack Writeup"
            
            # Extraer contenido principal
            writeup_data = self.extract_cryptohack_content(content)
            
            # Procesar y estructurar
            processed_data = self.process_cryptohack_data(writeup_data, url, title)
            
            # Guardar
            filename = self.save_cryptohack_data(processed_data)
            
            print(f"✅ CryptoHack writeup guardado: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error descargando {url}: {e}")
            return None
    
    def extract_cryptohack_content(self, html_content):
        """Extrae el contenido específico de CryptoHack"""
        
        # Buscar secciones principales
        sections = {
            'challenges': [],
            'techniques': [],
            'code_solutions': []
        }
        
        # Patrones para extraer información
        challenge_pattern = r'## (.*?)\n(.*?)(?=##|\Z)'
        code_pattern = r'```(\w+)?\n(.*?)```'
        flag_pattern = r'Flag[:\s]+`crypto\{[^}]+\}`'
        
        # Extraer desafíos
        challenges = re.findall(challenge_pattern, html_content, re.DOTALL)
        
        for challenge_title, challenge_content in challenges:
            
            # Extraer código
            codes = re.findall(code_pattern, challenge_content, re.DOTALL)
            
            # Extraer flags
            flags = re.findall(flag_pattern, challenge_content)
            
            # Extraer técnicas mencionadas
            techniques = self.extract_techniques(challenge_content)
            
            challenge_data = {
                'title': challenge_title.strip(),
                'content': challenge_content.strip(),
                'codes': codes,
                'flags': flags,
                'techniques': techniques,
                'type': self.classify_challenge_type(challenge_title, challenge_content)
            }
            
            sections['challenges'].append(challenge_data)
        
        return sections
    
    def extract_techniques(self, content):
        """Extrae técnicas criptográficas mencionadas"""
        
        technique_keywords = [
            'elliptic curve', 'point addition', 'scalar multiplication',
            'double and add', 'discrete log', 'ecdlp', 'sha1',
            'smart attack', 'smooth criminal', 'pohlig-hellman',
            'sage', 'gf', 'ellipticcurve', 'lift_x', 'order',
            'point negation', 'efficient exchange', 'parameter choice'
        ]
        
        found_techniques = []
        content_lower = content.lower()
        
        for technique in technique_keywords:
            if technique in content_lower:
                found_techniques.append(technique)
        
        return found_techniques
    
    def classify_challenge_type(self, title, content):
        """Clasifica el tipo de desafío"""
        
        title_lower = title.lower()
        content_lower = content.lower()
        
        if any(word in title_lower for word in ['point', 'elliptic', 'curve']):
            return 'elliptic_curves'
        elif any(word in title_lower for word in ['rsa', 'factorization']):
            return 'rsa'
        elif any(word in title_lower for word in ['diffie', 'hellman', 'dh']):
            return 'diffie_hellman'
        elif any(word in content_lower for word in ['xor', 'cipher']):
            return 'symmetric'
        else:
            return 'general_crypto'
    
    def process_cryptohack_data(self, raw_data, url, title):
        """Procesa los datos para el formato de entrenamiento"""
        
        processed = {
            'source': 'CryptoHack',
            'url': url,
            'title': title,
            'download_date': datetime.now().isoformat(),
            'type': 'educational_writeup',
            'challenges_count': len(raw_data['challenges']),
            'challenges': [],
            'techniques_summary': [],
            'metadata': {
                'difficulty': 'starter_to_advanced',
                'category': 'elliptic_curves',
                'language': 'python_sage',
                'tools': ['sage', 'python', 'cryptography']
            }
        }
        
        # Procesar cada desafío
        for challenge in raw_data['challenges']:
            processed_challenge = {
                'name': challenge['title'],
                'type': challenge['type'],
                'description': self.clean_content(challenge['content'][:500]),
                'solution_codes': challenge['codes'],
                'flags': challenge['flags'],
                'techniques': challenge['techniques'],
                'learning_points': self.extract_learning_points(challenge['content']),
                'difficulty': self.estimate_difficulty(challenge)
            }
            
            processed['challenges'].append(processed_challenge)
        
        # Resumen de técnicas
        all_techniques = set()
        for challenge in raw_data['challenges']:
            all_techniques.update(challenge['techniques'])
        
        processed['techniques_summary'] = list(all_techniques)
        
        return processed
    
    def clean_content(self, content):
        """Limpia el contenido de HTML y markdown"""
        
        # Remover HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Remover markdown excesivo
        content = re.sub(r'!\[.*?\]\(.*?\)', '[image]', content)
        content = re.sub(r'\[.*?\]\(.*?\)', '[link]', content)
        
        # Limpiar espacios
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content
    
    def extract_learning_points(self, content):
        """Extrae puntos de aprendizaje del contenido"""
        
        learning_points = []
        
        # Buscar explicaciones de algoritmos
        if 'algorithm' in content.lower():
            learning_points.append('algorithm_implementation')
        
        if 'double and add' in content.lower():
            learning_points.append('scalar_multiplication_optimization')
        
        if 'sage' in content.lower():
            learning_points.append('sage_mathematics_usage')
        
        if 'ellipticcurve' in content.lower():
            learning_points.append('elliptic_curve_operations')
        
        if 'discrete_log' in content.lower():
            learning_points.append('discrete_logarithm_problem')
        
        return learning_points
    
    def estimate_difficulty(self, challenge):
        """Estima la dificultad del desafío"""
        
        difficulty_indicators = {
            'beginner': ['point addition', 'point negation', 'basic'],
            'intermediate': ['scalar multiplication', 'double and add', 'efficient'],
            'advanced': ['smart attack', 'discrete log', 'pohlig-hellman', 'exceptional']
        }
        
        content_lower = challenge['content'].lower()
        title_lower = challenge['title'].lower()
        
        for level, indicators in difficulty_indicators.items():
            if any(indicator in content_lower or indicator in title_lower 
                   for indicator in indicators):
                return level
        
        return 'intermediate'  # Default
    
    def save_cryptohack_data(self, data):
        """Guarda los datos procesados"""
        
        # Crear directorio si no existe
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Nombre de archivo único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cryptohack_elliptic_curves_{timestamp}.json"
        filepath = os.path.join(self.base_dir, filename)
        
        # Guardar JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # También guardar versión de texto legible
        text_filename = f"cryptohack_elliptic_curves_{timestamp}.txt"
        text_filepath = os.path.join(self.base_dir, text_filename)
        
        with open(text_filepath, 'w', encoding='utf-8') as f:
            f.write(f"CryptoHack Writeup - {data['title']}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Source: {data['url']}\n")
            f.write(f"Date: {data['download_date']}\n")
            f.write(f"Challenges: {data['challenges_count']}\n\n")
            
            for challenge in data['challenges']:
                f.write(f"Challenge: {challenge['name']}\n")
                f.write(f"Type: {challenge['type']}\n")
                f.write(f"Difficulty: {challenge['difficulty']}\n")
                f.write(f"Techniques: {', '.join(challenge['techniques'])}\n")
                f.write(f"Description: {challenge['description']}\n")
                f.write(f"Flags: {challenge['flags']}\n")
                f.write("-" * 40 + "\n\n")
        
        return filepath

def main():
    """Función principal para probar el descargador"""
    
    print("🚀 CRYPTOHACK WRITEUP DOWNLOADER")
    print("=" * 35)
    
    downloader = CryptoHackDownloader("challenges/training_data")
    
    # URL del writeup de CryptoHack
    cryptohack_url = "https://hackmd.io/@CayCon/BkDkrc8TT#STARTER"
    
    # Descargar y procesar
    result = downloader.download_cryptohack_writeup(cryptohack_url)
    
    if result:
        print(f"\n✅ Writeup procesado exitosamente")
        print(f"📄 Archivo guardado: {result}")
        print(f"🎯 Datos listos para entrenar el Expert ML")
    else:
        print(f"\n❌ Error procesando el writeup")

if __name__ == "__main__":
    main()