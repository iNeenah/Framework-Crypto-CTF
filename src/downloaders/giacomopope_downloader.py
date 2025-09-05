#!/usr/bin/env python3
"""
GiacomoPope GitHub Repository Downloader
========================================
Descarga y procesa writeups de criptografía del repositorio de GiacomoPope
"""

import requests
import json
import os
import re
from datetime import datetime
from pathlib import Path
import base64

class GiacomoPopeDownloader:
    def __init__(self, base_dir="training_data"):
        self.base_dir = base_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Framework-Crypto-CTF/2.0)',
            'Accept': 'application/vnd.github.v3+json'
        })
        self.github_api_base = "https://api.github.com"
        self.repo_owner = "GiacomoPope"
        self.repo_name = "giacomopope.github.io"
        
    def get_repository_structure(self):
        """Obtiene la estructura del repositorio"""
        print(f"🔍 Explorando repositorio: {self.repo_owner}/{self.repo_name}")
        
        try:
            # Obtener estructura de archivos
            url = f"{self.github_api_base}/repos/{self.repo_owner}/{self.repo_name}/git/trees/master?recursive=1"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            tree_data = response.json()
            files = tree_data.get('tree', [])
            
            # Filtrar archivos relevantes
            relevant_files = []
            for file_info in files:
                if file_info['type'] == 'blob':  # Solo archivos, no directorios
                    path = file_info['path']
                    
                    # Buscar archivos de writeups, blogs, implementaciones
                    if any(pattern in path.lower() for pattern in [
                        'writeup', 'write-up', 'blog', 'post', 'ctf',
                        '.md', '.py', '.sage', 'crypto', 'implement',
                        'attack', 'solution', 'challenge'
                    ]):
                        relevant_files.append({
                            'path': path,
                            'url': file_info['url'],
                            'size': file_info.get('size', 0)
                        })
            
            print(f"📁 Archivos relevantes encontrados: {len(relevant_files)}")
            return relevant_files
            
        except Exception as e:
            print(f"❌ Error explorando repositorio: {e}")
            return []
    
    def download_file_content(self, file_info):
        """Descarga el contenido de un archivo específico"""
        
        try:
            response = self.session.get(file_info['url'], timeout=30)
            response.raise_for_status()
            
            file_data = response.json()
            
            # El contenido está en base64
            if file_data.get('encoding') == 'base64':
                content = base64.b64decode(file_data['content']).decode('utf-8', errors='ignore')
            else:
                content = file_data.get('content', '')
            
            return content
            
        except Exception as e:
            print(f"⚠️  Error descargando {file_info['path']}: {e}")
            return None
    
    def classify_content_type(self, file_path, content):
        """Clasifica el tipo de contenido del archivo"""
        
        path_lower = file_path.lower()
        content_lower = content.lower()
        
        # Clasificación por extensión y contenido
        if '.md' in path_lower and any(keyword in content_lower for keyword in [
            'writeup', 'ctf', 'challenge', 'flag', 'crypto{'
        ]):
            return 'ctf_writeup'
        
        elif '.md' in path_lower and any(keyword in content_lower for keyword in [
            'blog', 'post', 'cryptography', 'implementation', 'research'
        ]):
            return 'blog_post'
        
        elif '.py' in path_lower or '.sage' in path_lower:
            if any(keyword in content_lower for keyword in [
                'attack', 'implement', 'crypto', 'elliptic', 'rsa', 'isogeny'
            ]):
                return 'crypto_implementation'
            else:
                return 'code'
        
        elif any(keyword in content_lower for keyword in [
            'cryptography', 'crypto', 'algorithm', 'cipher'
        ]):
            return 'crypto_content'
        
        else:
            return 'general'
    
    def extract_crypto_knowledge(self, content, content_type):
        """Extrae conocimiento criptográfico del contenido"""
        
        knowledge = {
            'techniques': [],
            'algorithms': [],
            'tools': [],
            'attacks': [],
            'flags': [],
            'learning_points': []
        }
        
        content_lower = content.lower()
        
        # Técnicas criptográficas
        crypto_techniques = [
            'elliptic curve', 'rsa', 'diffie-hellman', 'aes', 'des',
            'isogeny', 'lattice', 'discrete log', 'factorization',
            'sage', 'sagemath', 'python', 'gap', 'magma',
            'sqisign', 'sidh', 'sike', 'festa', 'castryck-decru',
            'pohlig-hellman', 'pollard', 'baby-step giant-step',
            'wiener', 'hastad', 'coppersmith', 'lll', 'babai'
        ]
        
        for technique in crypto_techniques:
            if technique in content_lower:
                knowledge['techniques'].append(technique)
        
        # Ataques específicos
        attack_patterns = [
            'key recovery', 'side channel', 'timing attack',
            'padding oracle', 'chosen plaintext', 'chosen ciphertext',
            'meet in the middle', 'birthday attack', 'collision'
        ]
        
        for attack in attack_patterns:
            if attack in content_lower:
                knowledge['attacks'].append(attack)
        
        # Extraer flags
        flag_patterns = [
            r'crypto\{[^}]+\}',
            r'flag\{[^}]+\}',
            r'ctf\{[^}]+\}',
            r'[a-zA-Z0-9_]+\{[^}]+\}'
        ]
        
        for pattern in flag_patterns:
            flags = re.findall(pattern, content, re.IGNORECASE)
            knowledge['flags'].extend(flags)
        
        # Herramientas mencionadas
        tools = ['sage', 'python', 'magma', 'gap', 'pari', 'mathematica', 'maple']
        for tool in tools:
            if tool in content_lower:
                knowledge['tools'].append(tool)
        
        # Puntos de aprendizaje específicos por tipo
        if content_type == 'ctf_writeup':
            knowledge['learning_points'].extend([
                'ctf_strategy', 'challenge_analysis', 'solution_methodology'
            ])
        elif content_type == 'crypto_implementation':
            knowledge['learning_points'].extend([
                'implementation_details', 'algorithmic_approach', 'optimization'
            ])
        elif content_type == 'blog_post':
            knowledge['learning_points'].extend([
                'theoretical_background', 'practical_application', 'research_insights'
            ])
        
        return knowledge
    
    def search_specific_blog_posts(self):
        """Busca los blog posts específicos mencionados en el README"""
        
        blog_posts = [
            "Learning to SQI: Implementing SQISign in SageMath",
            "Implementing the Castryck-Decru SIDH Key Recovery Attack in SageMath", 
            "Estimating the Bit Security of Pairing-Friendly Curves"
        ]
        
        print(f"🔍 Buscando blog posts específicos...")
        
        # Intentar diferentes rutas posibles
        possible_paths = [
            "_posts/",
            "posts/", 
            "blog/",
            "content/",
            "writeups/",
            ""
        ]
        
        found_content = []
        
        for path in possible_paths:
            try:
                url = f"{self.github_api_base}/repos/{self.repo_owner}/{self.repo_name}/contents/{path}"
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    contents = response.json()
                    if isinstance(contents, list):
                        for item in contents:
                            if item['type'] == 'file' and any(ext in item['name'].lower() for ext in ['.md', '.html', '.txt']):
                                found_content.append({
                                    'name': item['name'],
                                    'path': item['path'],
                                    'download_url': item.get('download_url'),
                                    'size': item.get('size', 0)
                                })
                                
            except:
                continue
        
        return found_content
    
    def process_repository(self):
        """Procesa todo el repositorio"""
        
        print(f"🚀 INICIANDO DESCARGA - GIACOMO POPE REPOSITORY")
        print("=" * 50)
        
        # Estrategia 1: Obtener estructura completa
        files = self.get_repository_structure()
        
        # Estrategia 2: Buscar blog posts específicos
        blog_files = self.search_specific_blog_posts()
        
        # Combinar resultados
        all_files = files + [{
            'path': bf['path'],
            'url': bf['download_url'],
            'size': bf['size']
        } for bf in blog_files if bf['download_url']]
        
        # Remover duplicados
        unique_files = {}
        for f in all_files:
            if f['path'] not in unique_files:
                unique_files[f['path']] = f
        
        files_list = list(unique_files.values())
        
        if not files_list:
            print("❌ No se pudieron obtener archivos del repositorio")
            print("📝 Intentando búsqueda alternativa...")
            return self.fallback_content_extraction()
        
        print(f"📁 Total archivos únicos encontrados: {len(files_list)}")
        
        # Procesar archivos
        processed_data = {
            'source': 'GiacomoPope GitHub Repository',
            'repository': f"{self.repo_owner}/{self.repo_name}",
            'url': f"https://github.com/{self.repo_owner}/{self.repo_name}",
            'download_date': datetime.now().isoformat(),
            'total_files': len(files),
            'files_processed': 0,
            'content_types': {},
            'knowledge_extracted': {
                'techniques': set(),
                'algorithms': set(),
                'tools': set(),
                'attacks': set(),
                'flags': [],
                'learning_points': set()
            },
            'files': []
        }
        
        # Limitar a los primeros 50 archivos para evitar rate limiting
        files_to_process = files_list[:50]
        print(f"📥 Procesando {len(files_to_process)} archivos...")
        
        for file_info in files_to_process:
            print(f"   📄 Descargando: {file_info['path']}")
            
            content = self.download_file_content(file_info)
            if content is None:
                continue
            
            # Clasificar contenido
            content_type = self.classify_content_type(file_info['path'], content)
            
            # Extraer conocimiento
            knowledge = self.extract_crypto_knowledge(content, content_type)
            
            # Agregar a datos procesados
            file_data = {
                'path': file_info['path'],
                'type': content_type,
                'size': file_info['size'],
                'content_preview': content[:500] if content else '',
                'knowledge': knowledge
            }
            
            processed_data['files'].append(file_data)
            processed_data['files_processed'] += 1
            
            # Actualizar estadísticas
            if content_type not in processed_data['content_types']:
                processed_data['content_types'][content_type] = 0
            processed_data['content_types'][content_type] += 1
            
            # Agregar conocimiento global
            for key in ['techniques', 'algorithms', 'tools', 'attacks', 'learning_points']:
                processed_data['knowledge_extracted'][key].update(knowledge[key])
            
            processed_data['knowledge_extracted']['flags'].extend(knowledge['flags'])
        
        # Convertir sets a listas para JSON
        for key in ['techniques', 'algorithms', 'tools', 'attacks', 'learning_points']:
            processed_data['knowledge_extracted'][key] = list(processed_data['knowledge_extracted'][key])
        
        # Guardar datos
        self.save_processed_data(processed_data)
        
        return processed_data
    
    def fallback_content_extraction(self):
        """Método de fallback para extraer contenido conocido"""
        
        print("🔄 MODO FALLBACK - Extrayendo contenido conocido")
        
        # Contenido conocido basado en la información del README
        known_content = {
            'source': 'GiacomoPope Research (Fallback)',
            'repository': f"{self.repo_owner}/{self.repo_name}",
            'url': f"https://github.com/{self.repo_owner}/{self.repo_name}",
            'download_date': datetime.now().isoformat(),
            'extraction_method': 'fallback_known_content',
            'knowledge_extracted': {
                'techniques': [
                    'isogeny-based cryptography', 'elliptic curves', 'sqisign',
                    'sidh', 'castryck-decru attack', 'sage mathematics',
                    'montgomery ladder', 'pairing-based cryptography',
                    'supersingular curves', 'key recovery attacks',
                    'festa encryption', 'theta model', 'sike protocol'
                ],
                'tools': ['sage', 'sagemath', 'python', 'magma'],
                'attacks': [
                    'castryck-decru sidh attack', 'key recovery attack',
                    'supersingular torsion attacks', 'festa attack'
                ],
                'research_areas': [
                    'post-quantum cryptography', 'isogeny cryptography',
                    'elliptic curve cryptography', 'quantum-resistant algorithms'
                ],
                'implementations': [
                    'SQISign implementation', 'Castryck-Decru attack implementation',
                    'FESTA implementation', 'Pairing estimation tools'
                ],
                'learning_points': [
                    'advanced_cryptographic_research', 'post_quantum_security',
                    'isogeny_mathematics', 'practical_attack_implementation',
                    'sage_advanced_usage', 'cryptographic_analysis'
                ]
            },
            'research_contributions': [
                {
                    'title': 'SQIsign2D-West: The Fast, the Small, and the Safer',
                    'venue': 'ASIACRYPT 2024',
                    'significance': 'Advanced isogeny signature scheme'
                },
                {
                    'title': 'FESTA: Fast Encryption from Supersingular Torsion Attacks',
                    'venue': 'ASIACRYPT 2023', 
                    'significance': 'Novel encryption scheme based on isogenies'
                },
                {
                    'title': 'A Direct Key Recovery Attack on SIDH',
                    'venue': 'EUROCRYPT 2023',
                    'significance': 'Breakthrough attack breaking SIDH security'
                }
            ],
            'blog_posts': [
                {
                    'title': 'Learning to SQI: Implementing SQISign in SageMath',
                    'focus': 'Practical implementation of advanced signature scheme',
                    'techniques': ['sqisign', 'sage', 'isogeny computation']
                },
                {
                    'title': 'Implementing the Castryck-Decru SIDH Key Recovery Attack in SageMath',
                    'focus': 'Practical implementation of groundbreaking attack',
                    'techniques': ['castryck-decru', 'sidh', 'key recovery', 'sage']
                },
                {
                    'title': 'Estimating the Bit Security of Pairing-Friendly Curves',
                    'focus': 'Security analysis of pairing-based cryptography',
                    'techniques': ['pairings', 'security estimation', 'elliptic curves']
                }
            ]
        }
        
        # Guardar contenido conocido
        self.save_processed_data(known_content)
        
        return known_content
    
    def save_processed_data(self, data):
        """Guarda los datos procesados"""
        
        # Crear directorio
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Archivo JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"giacomopope_crypto_{timestamp}.json"
        json_filepath = os.path.join(self.base_dir, json_filename)
        
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Archivo de texto legible
        txt_filename = f"giacomopope_crypto_{timestamp}.txt"
        txt_filepath = os.path.join(self.base_dir, txt_filename)
        
        with open(txt_filepath, 'w', encoding='utf-8') as f:
            f.write(f"GIACOMO POPE REPOSITORY ANALYSIS\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Repository: {data['repository']}\n")
            f.write(f"URL: {data['url']}\n")
            f.write(f"Download Date: {data['download_date']}\n")
            f.write(f"Files Processed: {data['files_processed']}/{data['total_files']}\n\n")
            
            f.write("CONTENT TYPES:\n")
            f.write("-" * 15 + "\n")
            for content_type, count in data['content_types'].items():
                f.write(f"{content_type}: {count} files\n")
            
            f.write("\nKNOWLEDGE EXTRACTED:\n")
            f.write("-" * 20 + "\n")
            knowledge = data['knowledge_extracted']
            f.write(f"Techniques: {len(knowledge['techniques'])} - {knowledge['techniques'][:10]}...\n")
            f.write(f"Tools: {len(knowledge['tools'])} - {knowledge['tools']}\n")
            f.write(f"Attacks: {len(knowledge['attacks'])} - {knowledge['attacks']}\n")
            f.write(f"Flags: {len(knowledge['flags'])}\n")
            f.write(f"Learning Points: {len(knowledge['learning_points'])}\n\n")
            
            f.write("FILES PROCESSED:\n")
            f.write("-" * 16 + "\n")
            for file_data in data['files'][:20]:  # Primeros 20
                f.write(f"- {file_data['path']} ({file_data['type']})\n")
                if file_data['knowledge']['techniques']:
                    f.write(f"  Techniques: {file_data['knowledge']['techniques'][:3]}...\n")
        
        print(f"💾 Datos guardados:")
        print(f"   📄 JSON: {json_filepath}")
        print(f"   📄 TXT: {txt_filepath}")
        
        return json_filepath

def main():
    """Función principal"""
    
    print("🚀 GIACOMO POPE REPOSITORY DOWNLOADER")
    print("=" * 40)
    
    downloader = GiacomoPopeDownloader("challenges/training_data")
    
    # Procesar repositorio
    result = downloader.process_repository()
    
    if result:
        print(f"\n✅ DESCARGA COMPLETADA EXITOSAMENTE")
        print(f"📊 Estadísticas:")
        print(f"   📁 Archivos procesados: {result['files_processed']}")
        print(f"   🧠 Técnicas encontradas: {len(result['knowledge_extracted']['techniques'])}")
        print(f"   🛠️  Herramientas: {len(result['knowledge_extracted']['tools'])}")
        print(f"   ⚔️  Ataques: {len(result['knowledge_extracted']['attacks'])}")
        print(f"   🏆 Flags: {len(result['knowledge_extracted']['flags'])}")
        
        print(f"\n🎯 LISTO PARA ENTRENAR EL EXPERT ML")
    else:
        print(f"\n❌ Error en la descarga")

if __name__ == "__main__":
    main()