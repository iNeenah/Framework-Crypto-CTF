#!/usr/bin/env python3
"""
Web Writeups Downloader - Connor McCartney & HTML writeups
Descarga writeups desde páginas web HTML especializadas
"""

import os
import sys
import requests
import time
from pathlib import Path
from bs4 import BeautifulSoup

class WebWriteupsDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_dir = Path(__file__).parent.parent.parent
        self.writeups_dir = self.base_dir / "data" / "expert_writeups"
        self.writeups_dir.mkdir(parents=True, exist_ok=True)
        
    def download_connor_mccartney_writeup(self, url):
        """Descarga writeup desde connor-mccartney.github.io"""
        print(f"🔽 Descargando Connor McCartney: {url}")
        
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                # Usar BeautifulSoup para extraer contenido
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extraer contenido principal (artículo/post)
                    content = ""
                    
                    # Buscar contenido en varios elementos comunes
                    for selector in ['article', '.post-content', '.content', 'main', '.markdown-body']:
                        element = soup.select_one(selector)
                        if element:
                            content = element.get_text(strip=True, separator='\n')
                            break
                    
                    # Si no encuentra contenido específico, usar todo el texto
                    if not content:
                        content = soup.get_text(strip=True, separator='\n')
                    
                    # Filtrar contenido relevante (eliminar navegación, etc.)
                    lines = content.split('\n')
                    filtered_lines = [line for line in lines if len(line) > 10 and 
                                    not line.startswith(('Navigation', 'Menu', 'Home', 'About', 'Contact'))]
                    content = '\n'.join(filtered_lines)
                    
                except ImportError:
                    # Si BeautifulSoup no está disponible, usar texto plano
                    content = response.text
                
                # Generar nombre de archivo
                url_parts = url.split('/')
                challenge_name = url_parts[-1] if url_parts else "unknown"
                crypto_type = url_parts[-2] if len(url_parts) > 1 else "crypto"
                
                filename = f"connor_{crypto_type}_{challenge_name}.md"
                filepath = self.writeups_dir / filename
                
                with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(content)
                
                print(f"  📄 {filename}")
                return True
                
        except Exception as e:
            print(f"❌ Error descargando {url}: {e}")
        
        return False
    
    def process_web_writeups_from_file(self, writeups_file_path):
        """Procesa URLs web desde archivo de writeups"""
        if not os.path.exists(writeups_file_path):
            print(f"❌ Archivo no encontrado: {writeups_file_path}")
            return 0
        
        print(f"🌐 Procesando writeups web desde: {writeups_file_path}")
        print("=" * 60)
        
        total_downloaded = 0
        
        with open(writeups_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Solo procesar URLs de Connor McCartney por ahora
            if "connor-mccartney.github.io" in line:
                print(f"\\n🎯 Procesando Connor McCartney: {line}")
                if self.download_connor_mccartney_writeup(line):
                    total_downloaded += 1
                time.sleep(0.5)  # Rate limiting
        
        print(f"\\n🏆 RESUMEN WEB: {total_downloaded} writeups web descargados")
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
    
    try:
        # Intentar importar BeautifulSoup
        from bs4 import BeautifulSoup
        print("✅ BeautifulSoup disponible - descarga HTML optimizada")
    except ImportError:
        print("⚠️  BeautifulSoup no disponible - usando texto plano")
        print("💡 Instalar con: pip install beautifulsoup4")
    
    downloader = WebWriteupsDownloader()
    total = downloader.process_web_writeups_from_file(writeups_file)
    
    if total > 0:
        print(f"\\n🧠 Writeups web listos para entrenar Expert ML")
        print(f"🔥 Ejecuta: python framework/ml/expert_ml_framework.py --learn-dir data/expert_writeups")
    else:
        print(f"\\n❌ No se descargaron writeups web")

if __name__ == "__main__":
    main()