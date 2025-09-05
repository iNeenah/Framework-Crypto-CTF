#!/usr/bin/env python3
"""
Expert ML System Updater
========================
Actualiza el sistema Expert ML con nuevos writeups y conocimiento
"""

import json
import os
import glob
from datetime import datetime
from pathlib import Path

class ExpertMLUpdater:
    def __init__(self):
        self.knowledge_base = {
            'writeups_count': 231,  # Contador actual
            'elliptic_curves': {
                'techniques': set(),
                'attacks': set(),
                'tools': set(),
                'difficulty_levels': {},
                'common_patterns': []
            },
            'rsa': {
                'techniques': set(),
                'attacks': set(),
                'small_roots': [],
                'factorization_methods': []
            },
            'diffie_hellman': {
                'attacks': set(),
                'discrete_log_methods': []
            },
            'symmetric': {
                'ciphers': set(),
                'attacks': set(),
                'key_recovery': []
            },
            'recent_updates': []
        }
        
    def load_existing_knowledge(self):
        """Carga conocimiento existente si existe"""
        kb_file = "framework/ml/knowledge_base.json"
        
        if os.path.exists(kb_file):
            try:
                with open(kb_file, 'r', encoding='utf-8') as f:
                    loaded_kb = json.load(f)
                    # Convertir sets de vuelta
                    for category in ['elliptic_curves', 'rsa', 'diffie_hellman', 'symmetric']:
                        if category in loaded_kb:
                            for key, value in loaded_kb[category].items():
                                if isinstance(value, list) and key in ['techniques', 'attacks', 'tools', 'ciphers']:
                                    self.knowledge_base[category][key] = set(value)
                                else:
                                    self.knowledge_base[category][key] = value
                    
                    self.knowledge_base['writeups_count'] = loaded_kb.get('writeups_count', 231)
                    self.knowledge_base['recent_updates'] = loaded_kb.get('recent_updates', [])
                    
                    print(f"📚 Conocimiento existente cargado: {self.knowledge_base['writeups_count']} writeups")
                    
            except Exception as e:
                print(f"⚠️  Error cargando conocimiento existente: {e}")
    
    def process_training_data(self):
        """Procesa todos los datos de entrenamiento disponibles"""
        
        training_dir = "challenges/training_data"
        if not os.path.exists(training_dir):
            print(f"❌ Directorio de entrenamiento no encontrado: {training_dir}")
            return
        
        # Buscar archivos JSON de entrenamiento
        json_files = glob.glob(os.path.join(training_dir, "*.json"))
        
        print(f"🔍 Encontrados {len(json_files)} archivos de entrenamiento")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.process_writeup_data(data, json_file)
                    
            except Exception as e:
                print(f"⚠️  Error procesando {json_file}: {e}")
    
    def process_writeup_data(self, data, source_file):
        """Procesa datos de un writeup específico"""
        
        source_name = os.path.basename(source_file)
        print(f"📖 Procesando: {source_name}")
        
        # Actualizar contador
        challenges_count = data.get('challenges_count', 0)
        self.knowledge_base['writeups_count'] += challenges_count
        
        # Procesar desafíos por categoría
        for challenge in data.get('challenges', []):
            challenge_type = challenge.get('type', 'general_crypto')
            techniques = challenge.get('techniques', [])
            
            if challenge_type == 'elliptic_curves':
                self.update_elliptic_curves_knowledge(challenge)
            elif challenge_type == 'rsa':
                self.update_rsa_knowledge(challenge)
            elif challenge_type == 'diffie_hellman':
                self.update_diffie_hellman_knowledge(challenge)
            elif challenge_type in ['symmetric', 'cipher']:
                self.update_symmetric_knowledge(challenge)
        
        # Registrar actualización
        update_info = {
            'date': datetime.now().isoformat(),
            'source': source_name,
            'challenges_added': challenges_count,
            'source_url': data.get('url', 'unknown')
        }
        
        self.knowledge_base['recent_updates'].append(update_info)
        
        # Mantener solo las últimas 10 actualizaciones
        if len(self.knowledge_base['recent_updates']) > 10:
            self.knowledge_base['recent_updates'] = self.knowledge_base['recent_updates'][-10:]
    
    def update_elliptic_curves_knowledge(self, challenge):
        """Actualiza conocimiento específico de curvas elípticas"""
        
        # Técnicas
        for technique in challenge.get('techniques', []):
            self.knowledge_base['elliptic_curves']['techniques'].add(technique)
        
        # Herramientas
        if 'sage' in str(challenge.get('solution_codes', [])).lower():
            self.knowledge_base['elliptic_curves']['tools'].add('sage')
        if 'python' in str(challenge.get('solution_codes', [])).lower():
            self.knowledge_base['elliptic_curves']['tools'].add('python')
        
        # Ataques específicos
        challenge_name = challenge.get('name', '').lower()
        if 'smart attack' in challenge_name or 'smart' in challenge.get('techniques', []):
            self.knowledge_base['elliptic_curves']['attacks'].add('smart_attack')
        if 'pohlig' in challenge_name or 'pohlig' in ' '.join(challenge.get('techniques', [])):
            self.knowledge_base['elliptic_curves']['attacks'].add('pohlig_hellman')
        if 'smooth' in challenge_name:
            self.knowledge_base['elliptic_curves']['attacks'].add('smooth_order_attack')
        
        # Dificultad
        difficulty = challenge.get('difficulty', 'intermediate')
        if difficulty not in self.knowledge_base['elliptic_curves']['difficulty_levels']:
            self.knowledge_base['elliptic_curves']['difficulty_levels'][difficulty] = 0
        self.knowledge_base['elliptic_curves']['difficulty_levels'][difficulty] += 1
        
        # Patrones comunes
        patterns = []
        if 'point addition' in challenge.get('techniques', []):
            patterns.append('basic_point_operations')
        if 'scalar multiplication' in challenge.get('techniques', []):
            patterns.append('scalar_multiplication_attacks')
        if 'discrete log' in challenge.get('techniques', []):
            patterns.append('ecdlp_solving')
        
        for pattern in patterns:
            if pattern not in self.knowledge_base['elliptic_curves']['common_patterns']:
                self.knowledge_base['elliptic_curves']['common_patterns'].append(pattern)
    
    def update_rsa_knowledge(self, challenge):
        """Actualiza conocimiento específico de RSA"""
        
        for technique in challenge.get('techniques', []):
            self.knowledge_base['rsa']['techniques'].add(technique)
        
        # Ataques específicos
        challenge_name = challenge.get('name', '').lower()
        if 'small' in challenge_name or 'roots' in challenge_name:
            self.knowledge_base['rsa']['attacks'].add('small_roots')
        if 'factorization' in challenge_name:
            self.knowledge_base['rsa']['attacks'].add('factorization')
        if 'wiener' in challenge_name:
            self.knowledge_base['rsa']['attacks'].add('wiener_attack')
    
    def update_diffie_hellman_knowledge(self, challenge):
        """Actualiza conocimiento específico de Diffie-Hellman"""
        
        for technique in challenge.get('techniques', []):
            self.knowledge_base['diffie_hellman']['attacks'].add(technique)
        
        challenge_name = challenge.get('name', '').lower()
        if 'pohlig' in challenge_name:
            if 'pohlig_hellman' not in self.knowledge_base['diffie_hellman']['discrete_log_methods']:
                self.knowledge_base['diffie_hellman']['discrete_log_methods'].append('pohlig_hellman')
    
    def update_symmetric_knowledge(self, challenge):
        """Actualiza conocimiento específico de criptografía simétrica"""
        
        for technique in challenge.get('techniques', []):
            self.knowledge_base['symmetric']['attacks'].add(technique)
        
        # Identificar cifrados
        challenge_content = str(challenge.get('description', '')).lower()
        if 'aes' in challenge_content:
            self.knowledge_base['symmetric']['ciphers'].add('aes')
        if 'xor' in challenge_content:
            self.knowledge_base['symmetric']['ciphers'].add('xor')
    
    def save_knowledge_base(self):
        """Guarda la base de conocimiento actualizada"""
        
        # Crear directorio si no existe
        os.makedirs("framework/ml", exist_ok=True)
        
        # Convertir sets a listas para JSON
        kb_serializable = {}
        for key, value in self.knowledge_base.items():
            if isinstance(value, dict):
                kb_serializable[key] = {}
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, set):
                        kb_serializable[key][subkey] = list(subvalue)
                    else:
                        kb_serializable[key][subkey] = subvalue
            else:
                kb_serializable[key] = value
        
        # Guardar JSON
        kb_file = "framework/ml/knowledge_base.json"
        with open(kb_file, 'w', encoding='utf-8') as f:
            json.dump(kb_serializable, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Base de conocimiento guardada: {kb_file}")
        
        # Crear resumen legible
        self.create_knowledge_summary()
    
    def create_knowledge_summary(self):
        """Crea un resumen legible de la base de conocimiento"""
        
        summary_file = "framework/ml/knowledge_summary.txt"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("EXPERT ML SYSTEM - KNOWLEDGE BASE SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total Writeups Processed: {self.knowledge_base['writeups_count']}\n")
            f.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Curvas Elípticas
            ec = self.knowledge_base['elliptic_curves']
            f.write("ELLIPTIC CURVES KNOWLEDGE:\n")
            f.write("-" * 30 + "\n")
            f.write(f"Techniques: {len(ec['techniques'])} - {list(ec['techniques'])}\n")
            f.write(f"Attacks: {len(ec['attacks'])} - {list(ec['attacks'])}\n")
            f.write(f"Tools: {len(ec['tools'])} - {list(ec['tools'])}\n")
            f.write(f"Difficulty Distribution: {ec['difficulty_levels']}\n")
            f.write(f"Common Patterns: {ec['common_patterns']}\n\n")
            
            # RSA
            rsa = self.knowledge_base['rsa']
            f.write("RSA KNOWLEDGE:\n")
            f.write("-" * 15 + "\n")
            f.write(f"Techniques: {len(rsa['techniques'])} - {list(rsa['techniques'])}\n")
            f.write(f"Attacks: {len(rsa['attacks'])} - {list(rsa['attacks'])}\n\n")
            
            # Actualizaciones recientes
            f.write("RECENT UPDATES:\n")
            f.write("-" * 16 + "\n")
            for update in self.knowledge_base['recent_updates'][-5:]:
                f.write(f"- {update['date'][:10]}: {update['source']} (+{update['challenges_added']} challenges)\n")
        
        print(f"📋 Resumen creado: {summary_file}")

def main():
    """Función principal"""
    
    print("🧠 EXPERT ML SYSTEM UPDATER")
    print("=" * 30)
    
    updater = ExpertMLUpdater()
    
    # Cargar conocimiento existente
    updater.load_existing_knowledge()
    
    # Procesar nuevos datos de entrenamiento
    updater.process_training_data()
    
    # Guardar conocimiento actualizado
    updater.save_knowledge_base()
    
    print(f"\n✅ Sistema Expert ML actualizado exitosamente")
    print(f"📊 Total writeups: {updater.knowledge_base['writeups_count']}")
    print(f"🎯 Listo para resolver nuevos desafíos con conocimiento ampliado")

if __name__ == "__main__":
    main()