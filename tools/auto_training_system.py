#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Training System - Sistema de Entrenamiento Automático
==========================================================
Sistema que entrena continuamente al agente con nuevos writeups y desafíos.
"""

import os
import sys
import json
import requests
import time
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import subprocess

# Añadir al path
sys.path.append(str(Path(__file__).parent))

class AutoTrainingSystem:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.training_stats = {
            'sessions_completed': 0,
            'writeups_processed': 0,
            'new_techniques_learned': 0,
            'improvement_rate': 0.0,
            'last_training': None
        }
        
        print("🎓 Auto Training System iniciado")
        print(f"📁 Base directory: {self.base_dir}")
    
    def start_continuous_training(self):
        """Inicia entrenamiento continuo"""
        
        print("\n🚀 === ENTRENAMIENTO CONTINUO ACTIVADO ===")
        
        while True:
            try:
                print(f"\n⏰ Sesión de entrenamiento: {datetime.now()}")
                
                # 1. Buscar nuevos writeups
                new_writeups = self.discover_new_writeups()
                
                # 2. Procesar writeups encontrados
                if new_writeups:
                    self.process_new_writeups(new_writeups)
                
                # 3. Re-entrenar modelo si es necesario
                self.retrain_if_needed()
                
                # 4. Validar mejoras
                self.validate_improvements()
                
                # 5. Actualizar estadísticas
                self.update_training_stats()
                
                print(f"✅ Sesión completada. Próxima en 1 hora...")
                time.sleep(3600)  # Esperar 1 hora
                
            except KeyboardInterrupt:
                print("\n🛑 Entrenamiento detenido por usuario")
                break
            except Exception as e:
                print(f"❌ Error en entrenamiento: {e}")
                time.sleep(300)  # Esperar 5 minutos antes de reintentar
    
    def discover_new_writeups(self) -> List[Dict]:
        """Descubre nuevos writeups de múltiples fuentes"""
        
        print("🔍 Buscando nuevos writeups...")
        
        new_writeups = []
        
        # 1. Buscar en challenges/uploaded/
        uploaded_dir = self.base_dir / "challenges" / "uploaded"
        if uploaded_dir.exists():
            for file in uploaded_dir.glob("*.txt"):
                if not self._is_already_processed(file):
                    new_writeups.append({
                        'source': 'local_upload',
                        'path': str(file),
                        'type': 'challenge_file'
                    })
        
        # 2. Descargar de HackMD (usando URLs conocidas)
        hackmd_urls = self._get_hackmd_urls()
        for url in hackmd_urls:
            if not self._is_url_processed(url):
                content = self._download_hackmd_content(url)
                if content:
                    new_writeups.append({
                        'source': 'hackmd',
                        'url': url,
                        'content': content,
                        'type': 'writeup'
                    })
        
        # 3. Buscar en GitHub (repositorios conocidos)
        github_repos = [
            'GiacomoPope/giacomopope.github.io',
            'DownUnderCTF/Challenges_2025_Public',
            'kalmarunionenctf/kalmarctf'
        ]
        
        for repo in github_repos:
            new_content = self._check_github_updates(repo)
            if new_content:
                new_writeups.extend(new_content)
        
        print(f"📊 Encontrados {len(new_writeups)} nuevos writeups")
        return new_writeups
    
    def _get_hackmd_urls(self) -> List[str]:
        """Obtiene URLs de HackMD conocidas"""
        
        # URLs de writeups profesionales conocidas
        return [
            "https://hackmd.io/@CayCon/BkDkrc8TT",  # CryptoHack EC
            "https://hackmd.io/@maple3142/ByLYn_8tt",  # CTF writeups
            "https://hackmd.io/@Saint_1ne/rkTsKvUKo"   # Crypto challenges
        ]
    
    def _download_hackmd_content(self, url: str) -> str:
        """Descarga contenido de HackMD"""
        
        try:
            # Convertir URL de HackMD a formato raw
            if "hackmd.io" in url:
                raw_url = url.replace("hackmd.io", "hackmd.io") + "/download"
            
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                print(f"✅ Descargado: {url[:50]}...")
                return response.text
            else:
                print(f"⚠️  Error descargando {url}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error descargando HackMD {url}: {e}")
            return None
    
    def _check_github_updates(self, repo: str) -> List[Dict]:
        """Verifica actualizaciones en repositorios GitHub"""
        
        try:
            api_url = f"https://api.github.com/repos/{repo}/commits"
            response = requests.get(api_url, timeout=30)
            
            if response.status_code == 200:
                commits = response.json()
                recent_commits = [c for c in commits[:5]]  # Últimos 5 commits
                
                new_content = []
                for commit in recent_commits:
                    if not self._is_commit_processed(commit['sha']):
                        new_content.append({
                            'source': 'github',
                            'repo': repo,
                            'commit': commit['sha'],
                            'message': commit['commit']['message'],
                            'type': 'commit_update'
                        })
                
                return new_content
            
        except Exception as e:
            print(f"❌ Error verificando GitHub {repo}: {e}")
        
        return []
    
    def process_new_writeups(self, writeups: List[Dict]):
        """Procesa nuevos writeups encontrados"""
        
        print(f"📝 Procesando {len(writeups)} nuevos writeups...")
        
        processed_count = 0
        
        for writeup in writeups:
            try:
                if writeup['type'] == 'challenge_file':
                    self._process_challenge_file(writeup)
                elif writeup['type'] == 'writeup':
                    self._process_writeup_content(writeup)
                elif writeup['type'] == 'commit_update':
                    self._process_github_commit(writeup)
                
                processed_count += 1
                
            except Exception as e:
                print(f"❌ Error procesando writeup: {e}")
        
        print(f"✅ Procesados {processed_count}/{len(writeups)} writeups")
        self.training_stats['writeups_processed'] += processed_count
    
    def _process_challenge_file(self, writeup: Dict):
        """Procesa archivo de desafío local"""
        
        file_path = Path(writeup['path'])
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extraer información del desafío
            challenge_info = self._extract_challenge_info(content)
            
            # Guardar en training data
            output_file = self.base_dir / "challenges/training_data" / f"{file_path.stem}_processed.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(challenge_info, f, indent=2, ensure_ascii=False)
            
            # Marcar como procesado
            self._mark_as_processed(file_path)
            
            print(f"✅ Procesado: {file_path.name}")
            
        except Exception as e:
            print(f"❌ Error procesando {file_path}: {e}")
    
    def _extract_challenge_info(self, content: str) -> Dict:
        """Extrae información estructurada del desafío"""
        
        import re
        
        info = {
            'id': f"auto_processed_{int(time.time())}",
            'description': content[:500],  # Primeros 500 caracteres
            'labels': [],
            'techniques': [],
            'source': 'auto_training',
            'timestamp': datetime.now().isoformat()
        }
        
        # Detectar técnicas basadas en contenido
        techniques_map = {
            'rsa': ['rsa', 'factorization', 'modulus', 'public key'],
            'elliptic_curve': ['elliptic', 'curve', 'sage', 'point'],
            'xor': ['xor', 'cipher', 'key'],
            'base64': ['base64', 'decode', 'encode'],
            'network': ['nc', 'netcat', 'socket', 'server'],
            'hash': ['hash', 'md5', 'sha', 'collision']
        }
        
        content_lower = content.lower()
        for technique, keywords in techniques_map.items():
            if any(keyword in content_lower for keyword in keywords):
                info['labels'].append(technique)
                info['techniques'].append(technique)
        
        # Buscar flags para validación
        flag_matches = re.findall(r'crypto\{[^}]+\}|flag\{[^}]+\}', content)
        if flag_matches:
            info['expected_flags'] = flag_matches
        
        return info
    
    def retrain_if_needed(self):
        """Re-entrena el modelo si hay suficientes datos nuevos"""
        
        # Verificar si hay suficientes datos nuevos
        training_data_dir = self.base_dir / "challenges/training_data"
        new_files = list(training_data_dir.glob("*_processed.json"))
        
        if len(new_files) >= 5:  # Re-entrenar cada 5 archivos nuevos
            print("🔄 Re-entrenando modelo con nuevos datos...")
            
            try:
                # Ejecutar script de entrenamiento
                training_script = self.base_dir / "src/ml/train_classifier.py"
                if training_script.exists():
                    result = subprocess.run(
                        [sys.executable, str(training_script)],
                        capture_output=True,
                        text=True,
                        cwd=str(self.base_dir)
                    )
                    
                    if result.returncode == 0:
                        print("✅ Modelo re-entrenado exitosamente")
                        self.training_stats['sessions_completed'] += 1
                    else:
                        print(f"❌ Error re-entrenando: {result.stderr}")
                
            except Exception as e:
                print(f"❌ Error en re-entrenamiento: {e}")
    
    def validate_improvements(self):
        """Valida si el entrenamiento mejoró el rendimiento"""
        
        print("📊 Validando mejoras...")
        
        try:
            # Ejecutar algunos challenges de prueba
            test_challenges = [
                "Challenge: Base64\nY3J5cHRve2Jhc2U2NF9pc19lYXN5fQ==",
                "Challenge: XOR\nkey: crypto\ncipher: 1a2b3c4d5e6f"
            ]
            
            success_count = 0
            
            # Importar agente para pruebas
            from conversational_ctf_agent import ConversationalCTFAgent
            
            agent = ConversationalCTFAgent()
            
            for challenge in test_challenges:
                result = agent.solve_challenge_conversational(challenge)
                if result['success']:
                    success_count += 1
            
            improvement_rate = success_count / len(test_challenges)
            self.training_stats['improvement_rate'] = improvement_rate
            
            print(f"📈 Tasa de éxito: {improvement_rate:.2f}")
            
        except Exception as e:
            print(f"❌ Error validando mejoras: {e}")
    
    def update_training_stats(self):
        """Actualiza estadísticas de entrenamiento"""
        
        self.training_stats['last_training'] = datetime.now().isoformat()
        
        # Guardar estadísticas
        stats_file = self.base_dir / "data/ml/training_stats.json"
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.training_stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Error guardando estadísticas: {e}")
    
    def _is_already_processed(self, file_path: Path) -> bool:
        """Verifica si un archivo ya fue procesado"""
        processed_file = self.base_dir / "data/ml/processed_files.json"
        
        if not processed_file.exists():
            return False
        
        try:
            with open(processed_file, 'r', encoding='utf-8') as f:
                processed = json.load(f)
            return str(file_path) in processed.get('files', [])
        except:
            return False
    
    def _mark_as_processed(self, file_path: Path):
        """Marca un archivo como procesado"""
        processed_file = self.base_dir / "data/ml/processed_files.json"
        
        try:
            if processed_file.exists():
                with open(processed_file, 'r', encoding='utf-8') as f:
                    processed = json.load(f)
            else:
                processed = {'files': []}
            
            processed['files'].append(str(file_path))
            processed['last_update'] = datetime.now().isoformat()
            
            with open(processed_file, 'w', encoding='utf-8') as f:
                json.dump(processed, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️  Error marcando archivo procesado: {e}")
    
    def _is_url_processed(self, url: str) -> bool:
        """Verifica si una URL ya fue procesada"""
        # Similar a _is_already_processed pero para URLs
        return False  # Por simplicidad, siempre procesar URLs
    
    def _is_commit_processed(self, commit_sha: str) -> bool:
        """Verifica si un commit ya fue procesado"""
        # Similar a _is_already_processed pero para commits
        return False  # Por simplicidad, siempre procesar commits recientes
    
    def get_training_summary(self) -> Dict:
        """Obtiene resumen del entrenamiento"""
        return self.training_stats.copy()

def run_training_session():
    """Ejecuta una sesión de entrenamiento única"""
    
    print("🎓 === SESIÓN DE ENTRENAMIENTO ÚNICO ===")
    
    trainer = AutoTrainingSystem()
    
    # Ejecutar una sesión
    print("🔍 Buscando nuevos writeups...")
    new_writeups = trainer.discover_new_writeups()
    
    if new_writeups:
        print(f"📝 Procesando {len(new_writeups)} writeups...")
        trainer.process_new_writeups(new_writeups)
        
        print("🔄 Re-entrenando modelo...")
        trainer.retrain_if_needed()
        
        print("📊 Validando mejoras...")
        trainer.validate_improvements()
        
        trainer.update_training_stats()
        
        print("✅ Sesión de entrenamiento completada")
        
        summary = trainer.get_training_summary()
        print("\n📈 Resumen:")
        for key, value in summary.items():
            print(f"  • {key}: {value}")
    else:
        print("ℹ️  No se encontraron nuevos writeups")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Sistema de Entrenamiento Automático")
    parser.add_argument("--continuous", action="store_true", help="Entrenamiento continuo")
    parser.add_argument("--single", action="store_true", help="Sesión única")
    
    args = parser.parse_args()
    
    if args.continuous:
        trainer = AutoTrainingSystem()
        trainer.start_continuous_training()
    elif args.single:
        run_training_session()
    else:
        print("Uso: python auto_training_system.py --continuous | --single")
        print("  --continuous: Entrenamiento continuo cada hora")
        print("  --single: Una sesión de entrenamiento")