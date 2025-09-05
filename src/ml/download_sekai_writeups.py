#!/usr/bin/env python3
"""
DESCARGADOR DE WRITEUPS SEKAI CTF
=================================

Script para descargar writeups profesionales de los repositorios de SekaiCTF
y prepararlos para el entrenamiento del sistema Expert ML.

Repositorios objetivo:
- https://github.com/project-sekai-ctf/sekaictf-2025/tree/main/crypto
- https://github.com/project-sekai-ctf/sekaictf-2024/tree/main/crypto  
- https://github.com/project-sekai-ctf/sekaictf-2023/tree/main/crypto
"""
import os
import json
import requests
import base64
from pathlib import Path
from typing import List, Dict, Any
import time


class SekaiWriteupDownloader:
    """Descargador de writeups de SekaiCTF"""
    
    def __init__(self):
        self.base_url = "https://api.github.com/repos/project-sekai-ctf"
        self.writeups_dir = Path("data/sekai_writeups")
        self.writeups_dir.mkdir(parents=True, exist_ok=True)
        
        # Headers para GitHub API
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'SekaiCTF-Writeup-Downloader'
        }
        
        print("🌐 Descargador de Writeups SekaiCTF iniciado")
    
    def get_repo_contents(self, repo_year: str, path: str = "crypto") -> List[Dict]:
        """Obtener contenido de un repositorio"""
        repo_name = f"sekaictf-{repo_year}"
        url = f"{self.base_url}/{repo_name}/contents/{path}"
        
        print(f"📡 Consultando: {repo_name}/{path}")
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"❌ Error consultando {repo_name}: {e}")
            return []
    
    def download_file_content(self, download_url: str) -> str:
        """Descargar contenido de un archivo"""
        try:
            response = requests.get(download_url, headers=self.headers)
            response.raise_for_status()
            
            # Si es base64, decodificar
            if 'encoding' in response.headers.get('content-type', ''):
                content = base64.b64decode(response.content).decode('utf-8')
            else:
                content = response.text
            
            return content
        except Exception as e:
            print(f"⚠️ Error descargando archivo: {e}")
            return ""
    
    def is_writeup_file(self, filename: str) -> bool:
        """Verificar si un archivo es un writeup"""
        writeup_indicators = [
            'readme.md', 'writeup.md', 'solution.md',
            'solve.py', 'exploit.py', 'solution.py',
            'writeup.txt', 'solution.txt'
        ]
        
        filename_lower = filename.lower()
        return any(indicator in filename_lower for indicator in writeup_indicators)
    
    def process_directory(self, repo_year: str, items: List[Dict], parent_path: str = "") -> int:
        """Procesar directorio de desafíos"""
        downloaded_count = 0
        
        for item in items:
            item_name = item['name']
            item_type = item['type']
            
            # Evitar directorios obvios que no son desafíos
            skip_dirs = ['.git', '.github', 'node_modules', '__pycache__']
            if item_name in skip_dirs:
                continue
            
            if item_type == 'dir':
                # Es un directorio (probablemente un desafío)
                print(f"📁 Explorando desafío: {item_name}")
                
                # Obtener contenido del directorio
                subdir_contents = self.get_repo_contents(repo_year, item['path'])
                if subdir_contents:
                    challenge_writeups = self.extract_challenge_writeups(
                        repo_year, item_name, subdir_contents
                    )
                    downloaded_count += len(challenge_writeups)
                
                time.sleep(0.5)  # Rate limiting
                
            elif item_type == 'file' and self.is_writeup_file(item_name):
                # Es un archivo de writeup directo
                content = self.download_file_content(item['download_url'])
                if content and len(content) > 100:  # Filtrar archivos muy pequeños
                    filename = f"sekai{repo_year}_{parent_path}_{item_name}".replace("/", "_")
                    self.save_writeup(filename, content, repo_year, parent_path or "root")
                    downloaded_count += 1
        
        return downloaded_count
    
    def extract_challenge_writeups(self, repo_year: str, challenge_name: str, 
                                 contents: List[Dict]) -> List[str]:
        """Extraer writeups de un desafío específico"""
        writeups = []
        
        for item in contents:
            if item['type'] == 'file' and self.is_writeup_file(item['name']):
                print(f"  📄 Descargando: {item['name']}")
                
                content = self.download_file_content(item['download_url'])
                if content and len(content) > 100:
                    filename = f"sekai{repo_year}_{challenge_name}_{item['name']}"
                    self.save_writeup(filename, content, repo_year, challenge_name)
                    writeups.append(filename)
            
            elif item['type'] == 'dir':
                # Explorar subdirectorios
                subdir_contents = self.get_repo_contents(repo_year, item['path'])
                if subdir_contents:
                    sub_writeups = self.extract_challenge_writeups(
                        repo_year, f"{challenge_name}_{item['name']}", subdir_contents
                    )
                    writeups.extend(sub_writeups)
        
        return writeups
    
    def save_writeup(self, filename: str, content: str, year: str, challenge: str):
        """Guardar writeup procesado"""
        # Limpiar filename
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        if not safe_filename.endswith(('.md', '.txt', '.py')):
            safe_filename += '.txt'
        
        file_path = self.writeups_dir / safe_filename
        
        # Agregar metadata al inicio
        metadata_header = f"""# SekaiCTF {year} - {challenge}
# Fuente: https://github.com/project-sekai-ctf/sekaictf-{year}/tree/main/crypto
# Descargado: {time.strftime('%Y-%m-%d %H:%M:%S')}
# Desafío: {challenge}
# Año: {year}

---

"""
        
        try:
            with open(file_path, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(metadata_header + content)
            
            print(f"  ✅ Guardado: {safe_filename}")
            
        except Exception as e:
            print(f"  ❌ Error guardando {safe_filename}: {e}")
    
    def download_all_sekai_writeups(self) -> Dict[str, int]:
        """Descargar todos los writeups de SekaiCTF"""
        print("🚀 DESCARGANDO WRITEUPS DE SEKAICTF")
        print("=" * 50)
        
        years = ['2023', '2024', '2025']
        total_stats = {'total_downloaded': 0, 'by_year': {}}
        
        for year in years:
            print(f"\n📅 Procesando SekaiCTF {year}...")
            print("-" * 30)
            
            # Obtener contenido del directorio crypto
            crypto_contents = self.get_repo_contents(year, "crypto")
            
            if crypto_contents:
                downloaded = self.process_directory(year, crypto_contents)
                total_stats['by_year'][year] = downloaded
                total_stats['total_downloaded'] += downloaded
                
                print(f"✅ SekaiCTF {year}: {downloaded} writeups descargados")
            else:
                print(f"⚠️ No se pudo acceder a SekaiCTF {year}/crypto")
                total_stats['by_year'][year] = 0
            
            time.sleep(1)  # Rate limiting entre años
        
        return total_stats
    
    def generate_summary(self, stats: Dict[str, int]):
        """Generar resumen de descarga"""
        print("\n📊 RESUMEN DE DESCARGA")
        print("=" * 30)
        
        for year, count in stats['by_year'].items():
            print(f"📅 SekaiCTF {year}: {count} writeups")
        
        print(f"\n🎯 Total descargado: {stats['total_downloaded']} writeups")
        print(f"📁 Guardados en: {self.writeups_dir}")
        
        # Listar archivos descargados
        downloaded_files = list(self.writeups_dir.glob("*.txt")) + list(self.writeups_dir.glob("*.md"))
        print(f"\n📋 Archivos descargados ({len(downloaded_files)}):")
        for i, file_path in enumerate(downloaded_files[:10], 1):  # Mostrar solo los primeros 10
            print(f"  {i:2d}. {file_path.name}")
        
        if len(downloaded_files) > 10:
            print(f"  ... y {len(downloaded_files) - 10} más")
        
        return len(downloaded_files)


def main():
    """Función principal"""
    print("🌟 DESCARGADOR DE WRITEUPS PROFESIONALES SEKAI CTF")
    print("=" * 60)
    print("Este script descarga writeups de los repositorios oficiales de SekaiCTF")
    print("para entrenar el sistema Expert ML con conocimiento profesional.\n")
    
    downloader = SekaiWriteupDownloader()
    
    try:
        # Descargar writeups
        stats = downloader.download_all_sekai_writeups()
        
        # Generar resumen
        total_files = downloader.generate_summary(stats)
        
        if total_files > 0:
            print(f"\n🎉 ¡Descarga completada exitosamente!")
            print(f"🔧 Siguiente paso: Entrenar Expert ML con estos writeups")
            print(f"   python expert_ml_framework.py --learn-dir \"data/sekai_writeups\"")
        else:
            print(f"\n⚠️ No se descargaron writeups. Verifica la conexión a Internet.")
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 Descarga interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante la descarga: {e}")


if __name__ == "__main__":
    main()