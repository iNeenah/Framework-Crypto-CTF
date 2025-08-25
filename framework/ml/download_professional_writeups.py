#!/usr/bin/env python3
"""
Professional Writeups Downloader
Descarga writeups de CTFs profesionales para entrenar Expert ML
"""

import os
import sys
import requests
import time
import json
from urllib.parse import urlparse
from pathlib import Path

class ProfessionalWriteupsDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.base_dir = Path(__file__).parent.parent.parent
        self.writeups_dir = self.base_dir / "data" / "expert_writeups"
        self.writeups_dir.mkdir(parents=True, exist_ok=True)
        
    def download_from_github_crypto_dir(self, github_url):
        """Descarga writeups desde directorio crypto de GitHub"""
        print(f"🔽 Descargando desde: {github_url}")
        
        # Convertir URL web a API URL
        parts = github_url.replace("https://github.com/", "").split("/")
        if len(parts) >= 5 and "tree" in parts:
            owner = parts[0]
            repo = parts[1]
            branch = parts[3]
            path = "/".join(parts[4:])
            
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
            
            try:
                response = self.session.get(api_url)
                if response.status_code == 200:
                    files = response.json()
                    downloaded = 0
                    
                    for file_info in files:
                        if file_info["type"] == "dir":
                            # Descargar contenido de subdirectorio
                            subdir_files = self._get_files_from_dir(file_info["url"])
                            for subfile in subdir_files:
                                if self._download_file_content(subfile, f"{repo}_{parts[3]}"):
                                    downloaded += 1
                                    time.sleep(0.2)  # Rate limiting más agresivo
                        elif file_info["name"].endswith(('.md', '.py', '.txt')):
                            if self._download_file_content(file_info, f"{repo}_{parts[3]}"):
                                downloaded += 1
                                time.sleep(0.2)  # Rate limiting más agresivo
                    
                    print(f"✅ Descargados {downloaded} archivos desde {repo}")
                    return downloaded
                elif response.status_code == 403:
                    print(f"⚠️  Rate limit alcanzado para {repo}. Intentando método alternativo...")
                    return self._download_via_raw_github(github_url)
                else:
                    print(f"❌ Error al acceder a {api_url}: {response.status_code}")
                    return 0
                    
            except Exception as e:
                print(f"❌ Error descargando desde {github_url}: {e}")
                print(f"🔄 Intentando método alternativo...")
                return self._download_via_raw_github(github_url)
        
        return 0
    
    def _get_files_from_dir(self, dir_api_url):
        """Obtiene archivos de un directorio via API"""
        try:
            response = self.session.get(dir_api_url)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"❌ Error accediendo directorio: {e}")
        return []
    
    def _download_file_content(self, file_info, prefix):
        """Descarga contenido de un archivo específico"""
        try:
            if file_info.get("download_url"):
                response = self.session.get(file_info["download_url"])
                if response.status_code == 200:
                    filename = f"{prefix}_{file_info['name']}"
                    filepath = self.writeups_dir / filename
                    
                    with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                        f.write(response.text)
                    
                    print(f"  📄 {filename}")
                    return True
        except Exception as e:
            print(f"❌ Error descargando {file_info.get('name', 'unknown')}: {e}")
        return False
    
    def _download_via_raw_github(self, github_url):
        """Método alternativo para descargar desde GitHub usando URLs raw"""
        print(f"🔄 Intentando descarga alternativa...")
        
        # Generar algunos archivos comunes que suelen estar en crypto challenges
        common_files = [
            "README.md", "solution.py", "solve.py", "writeup.md", 
            "challenge.py", "server.py", "exploit.py", "flag.txt"
        ]
        
        # Convertir a URL raw de GitHub
        raw_base = github_url.replace("github.com", "raw.githubusercontent.com").replace("/tree/", "/")
        downloaded = 0
        
        for filename in common_files:
            try:
                raw_url = f"{raw_base}/{filename}"
                response = self.session.get(raw_url)
                if response.status_code == 200:
                    # Extraer info del repo
                    parts = github_url.split("/")
                    repo_name = parts[4] if len(parts) > 4 else "unknown"
                    branch = parts[6] if len(parts) > 6 else "main"
                    
                    local_filename = f"{repo_name}_{branch}_{filename}"
                    filepath = self.writeups_dir / local_filename
                    
                    with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                        f.write(response.text)
                    
                    print(f"  📄 {local_filename}")
                    downloaded += 1
                    time.sleep(0.3)  # Rate limiting
            except Exception:
                continue  # Archivo no existe, continuar
        
        if downloaded > 0:
            print(f"✅ Descargados {downloaded} archivos via método alternativo")
        
        return downloaded
    
    def download_from_thebusfactor(self, writeup_url):
        """Descarga writeup desde TheBusFactor"""
        print(f"🔽 Descargando TheBusFactor: {writeup_url}")
        
        try:
            response = self.session.get(writeup_url)
            if response.status_code == 200:
                # Extraer nombre del writeup desde URL
                url_parts = writeup_url.split('/')
                writeup_name = url_parts[-1] if url_parts else "unknown"
                
                filename = f"thebusfactor_{writeup_name}.md"
                filepath = self.writeups_dir / filename
                
                with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(response.text)
                
                print(f"  📄 {filename}")
                return True
        except Exception as e:
            print(f"❌ Error descargando TheBusFactor: {e}")
        
        return False
    
    def process_writeups_file(self, writeups_file_path):
        """Procesa archivo con URLs de writeups"""
        if not os.path.exists(writeups_file_path):
            print(f"❌ Archivo no encontrado: {writeups_file_path}")
            return 0
        
        print(f"🚀 Procesando writeups desde: {writeups_file_path}")
        print("=" * 60)
        
        total_downloaded = 0
        
        with open(writeups_file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        for url in urls:
            print(f"\n🎯 Procesando: {url}")
            
            if "github.com" in url and "/tree/" in url:
                downloaded = self.download_from_github_crypto_dir(url)
                total_downloaded += downloaded
            elif "thebusfactor-writeups.vercel.app" in url:
                if self.download_from_thebusfactor(url):
                    total_downloaded += 1
            else:
                print(f"⚠️  Tipo de URL no soportado: {url}")
            
            time.sleep(1)  # Rate limiting entre URLs
        
        print(f"\n🏆 RESUMEN: {total_downloaded} writeups descargados exitosamente")
        print(f"📁 Ubicación: {self.writeups_dir}")
        
        return total_downloaded

def main():
    """Función principal"""
    if len(sys.argv) > 1:
        writeups_file = sys.argv[1]
    else:
        # Usar archivo por defecto
        base_dir = Path(__file__).parent.parent.parent
        writeups_file = base_dir / "challenges" / "uploaded" / "writeupsSolutions.txt"
    
    downloader = ProfessionalWriteupsDownloader()
    total = downloader.process_writeups_file(writeups_file)
    
    if total > 0:
        print(f"\n🧠 Writeups listos para entrenar Expert ML")
        print(f"🔥 Ejecuta: python framework/ml/expert_ml_framework.py --learn-dir data/expert_writeups")
    else:
        print(f"\n❌ No se descargaron writeups")

if __name__ == "__main__":
    main()