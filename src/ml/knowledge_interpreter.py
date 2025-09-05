#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge Interpreter - Puente Inteligente entre Datos y Soluciones
==================================================================
Este módulo interpreta los datos de entrenamiento procesados y los convierte
en estrategias de resolución más efectivas para el agente autónomo.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import Counter, defaultdict

class KnowledgeInterpreter:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.processed_data = None
        self.pattern_library = {}
        self.technique_effectiveness = {}
        self.solution_templates = {}
        self.load_knowledge_data()
        
    def load_knowledge_data(self):
        """Carga y procesa todos los datos de conocimiento disponibles"""
        
        # Cargar datos procesados
        processed_file = self.base_path / "data/ml/processed_challenges.json"
        if processed_file.exists():
            with open(processed_file, 'r', encoding='utf-8') as f:
                self.processed_data = json.load(f)
            print(f"🧠 Cargados {len(self.processed_data)} challenges procesados")
        
        # Construir biblioteca de patrones
        self._build_pattern_library()
        
        # Analizar efectividad de técnicas
        self._analyze_technique_effectiveness()
        
        # Crear templates de solución
        self._create_solution_templates()
    
    def _build_pattern_library(self):
        """Construye una biblioteca de patrones a partir de los datos"""
        
        if not self.processed_data:
            return
        
        self.pattern_library = {
            'rsa_patterns': [],
            'elliptic_curve_patterns': [],
            'xor_patterns': [],
            'network_patterns': [],
            'encoding_patterns': [],
            'hash_patterns': []
        }
        
        for challenge in self.processed_data:
            description = challenge['description'].lower()
            labels = challenge['labels']
            
            # Clasificar por tipo de criptografía
            if any(label in ['sage', 'ellipticcurve', 'gf'] for label in labels):
                self.pattern_library['elliptic_curve_patterns'].append({
                    'description_keywords': self._extract_keywords(description),
                    'techniques': labels,
                    'source': challenge['id']
                })
            
            elif any(keyword in description for keyword in ['rsa', 'factorization', 'modulus']):
                self.pattern_library['rsa_patterns'].append({
                    'description_keywords': self._extract_keywords(description),
                    'techniques': labels,
                    'source': challenge['id']
                })
            
            elif any(keyword in description for keyword in ['xor', 'cipher', 'key']):
                self.pattern_library['xor_patterns'].append({
                    'description_keywords': self._extract_keywords(description),
                    'techniques': labels,
                    'source': challenge['id']
                })
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrae palabras clave técnicas del texto"""
        
        # Palabras clave técnicas comunes en CTF
        technical_keywords = [
            'elliptic', 'curve', 'point', 'scalar', 'multiplication', 'sage',
            'rsa', 'factorization', 'modulus', 'exponent', 'private', 'public',
            'xor', 'cipher', 'key', 'plaintext', 'ciphertext',
            'hash', 'sha1', 'md5', 'collision',
            'base64', 'encoding', 'decode',
            'nc', 'socket', 'network', 'server'
        ]
        
        found_keywords = []
        for keyword in technical_keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _analyze_technique_effectiveness(self):
        """Analiza qué técnicas son más efectivas para cada tipo de problema"""
        
        if not self.processed_data:
            return
        
        technique_usage = Counter()
        technique_success = defaultdict(int)
        
        for challenge in self.processed_data:
            for technique in challenge['labels']:
                technique_usage[technique] += 1
                # Asumimos que si está en los datos, fue exitoso
                technique_success[technique] += 1
        
        # Calcular efectividad
        for technique in technique_usage:
            success_rate = technique_success[technique] / technique_usage[technique]
            self.technique_effectiveness[technique] = {
                'usage_count': technique_usage[technique],
                'success_rate': success_rate,
                'confidence': min(technique_usage[technique] / 10, 1.0)
            }
    
    def _create_solution_templates(self):
        """Crea templates de solución basados en patrones exitosos"""
        
        self.solution_templates = {
            'elliptic_curve': {
                'imports': ['from sage.all import *', 'import hashlib'],
                'setup': 'E = EllipticCurve(GF(p), [a, b])',
                'common_operations': [
                    'point_addition', 'scalar_multiplication', 'discrete_log'
                ],
                'success_indicators': ['sage', 'gf', 'ellipticcurve']
            },
            
            'rsa': {
                'imports': ['from Crypto.Util.number import *', 'import gmpy2'],
                'setup': 'n, e = ...',
                'common_operations': [
                    'factorization', 'wiener_attack', 'common_modulus'
                ],
                'success_indicators': ['factorization', 'wiener']
            },
            
            'xor': {
                'imports': ['import itertools', 'from pwn import xor'],
                'setup': 'ciphertext = bytes.fromhex(...)',
                'common_operations': [
                    'key_bruteforce', 'frequency_analysis', 'known_plaintext'
                ],
                'success_indicators': ['xor', 'key']
            }
        }
    
    def interpret_challenge(self, challenge_text: str) -> Dict:
        """Interpreta un desafío nuevo usando el conocimiento acumulado"""
        
        interpretation = {
            'challenge_type': 'unknown',
            'confidence': 0.0,
            'recommended_techniques': [],
            'solution_template': None,
            'expected_imports': [],
            'complexity_level': 'medium',
            'similar_challenges': []
        }
        
        challenge_lower = challenge_text.lower()
        keywords = self._extract_keywords(challenge_lower)
        
        # Clasificar tipo de desafío
        type_scores = {
            'elliptic_curve': 0,
            'rsa': 0,
            'xor': 0,
            'network': 0,
            'encoding': 0
        }
        
        # Puntuación basada en palabras clave
        ec_keywords = ['elliptic', 'curve', 'point', 'sage', 'scalar']
        rsa_keywords = ['rsa', 'factorization', 'modulus', 'exponent']
        xor_keywords = ['xor', 'cipher', 'key']
        
        for keyword in keywords:
            if keyword in ec_keywords:
                type_scores['elliptic_curve'] += 1
            elif keyword in rsa_keywords:
                type_scores['rsa'] += 1
            elif keyword in xor_keywords:
                type_scores['xor'] += 1
        
        # Determinar tipo principal
        main_type = max(type_scores, key=type_scores.get)
        if type_scores[main_type] > 0:
            interpretation['challenge_type'] = main_type
            interpretation['confidence'] = min(type_scores[main_type] / 3, 1.0)
        
        # Buscar desafíos similares
        interpretation['similar_challenges'] = self._find_similar_challenges(keywords)
        
        # Recomendar técnicas basadas en efectividad
        if main_type in self.solution_templates:
            template = self.solution_templates[main_type]
            interpretation['solution_template'] = template
            interpretation['expected_imports'] = template['imports']
            
            # Recomendar técnicas más efectivas
            relevant_techniques = []
            for technique in self.technique_effectiveness:
                if (self.technique_effectiveness[technique]['confidence'] > 0.5 and
                    technique in template['success_indicators']):
                    relevant_techniques.append({
                        'technique': technique,
                        'effectiveness': self.technique_effectiveness[technique]['success_rate'],
                        'usage_count': self.technique_effectiveness[technique]['usage_count']
                    })
            
            interpretation['recommended_techniques'] = sorted(
                relevant_techniques, 
                key=lambda x: x['effectiveness'], 
                reverse=True
            )
        
        return interpretation
    
    def _find_similar_challenges(self, keywords: List[str]) -> List[Dict]:
        """Encuentra desafíos similares basados en palabras clave"""
        
        if not self.processed_data:
            return []
        
        similar = []
        for challenge in self.processed_data:
            challenge_keywords = self._extract_keywords(challenge['description'].lower())
            overlap = len(set(keywords) & set(challenge_keywords))
            
            if overlap >= 2:  # Al menos 2 palabras clave en común
                similarity_score = overlap / max(len(keywords), len(challenge_keywords))
                similar.append({
                    'id': challenge['id'],
                    'similarity': similarity_score,
                    'techniques': challenge['labels'],
                    'keywords_overlap': list(set(keywords) & set(challenge_keywords))
                })
        
        return sorted(similar, key=lambda x: x['similarity'], reverse=True)[:3]
    
    def generate_enhanced_solution_code(self, interpretation: Dict, challenge_text: str) -> str:
        """Genera código de solución mejorado basado en la interpretación"""
        
        if interpretation['challenge_type'] == 'unknown':
            return self._generate_generic_solution(challenge_text)
        
        template = interpretation.get('solution_template', {})
        similar_challenges = interpretation.get('similar_challenges', [])
        
        # Construir código basado en template y casos similares
        code_parts = []
        
        # Imports
        imports = template.get('imports', ['import os', 'import sys'])
        code_parts.append('\n'.join(imports))
        code_parts.append('')
        
        # Función principal
        code_parts.append('def solve_challenge():')
        code_parts.append('    """Solución generada automáticamente basada en conocimiento experto"""')
        code_parts.append('')
        
        # Agregar lógica específica basada en casos similares
        if similar_challenges:
            top_similar = similar_challenges[0]
            techniques = top_similar['techniques']
            
            if 'sage' in techniques:
                code_parts.append('    # Configuración Sage (basado en casos similares exitosos)')
                code_parts.append('    from sage.all import *')
                code_parts.append('')
            
            if 'ellipticcurve' in techniques:
                code_parts.append('    # Configuración de curva elíptica')
                code_parts.append('    p = 9739  # Ajustar según el problema')
                code_parts.append('    E = EllipticCurve(GF(p), [497, 1768])  # Ajustar parámetros')
                code_parts.append('')
            
            if 'sha1' in techniques:
                code_parts.append('    # Hash SHA1 para flag')
                code_parts.append('    import hashlib')
                code_parts.append('    result_hash = hashlib.sha1(str(result).encode()).hexdigest()')
                code_parts.append('    flag = f"crypto{{{result_hash}}}"')
                code_parts.append('')
        
        # Lógica de búsqueda de flag
        code_parts.append('    # Buscar flag en el texto del desafío')
        code_parts.append('    import re')
        code_parts.append('    challenge_text = """')
        code_parts.append(challenge_text)
        code_parts.append('    """')
        code_parts.append('')
        code_parts.append('    # Patrón de flag')
        code_parts.append('    flag_pattern = r"crypto\\{[^}]+\\}|flag\\{[^}]+\\}"')
        code_parts.append('    flags = re.findall(flag_pattern, challenge_text)')
        code_parts.append('    if flags:')
        code_parts.append('        return flags[0]')
        code_parts.append('')
        code_parts.append('    return "Flag no encontrada"')
        code_parts.append('')
        code_parts.append('if __name__ == "__main__":')
        code_parts.append('    result = solve_challenge()')
        code_parts.append('    print(f"FLAG: {result}")')
        
        return '\n'.join(code_parts)
    
    def _generate_generic_solution(self, challenge_text: str) -> str:
        """Genera una solución genérica cuando no se puede clasificar el desafío"""
        
        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import base64
import hashlib

def solve_challenge():
    """Solucion generica con tecnicas comunes"""
    
    challenge_text = """{challenge_text}"""
    
    # 1. Buscar flags directamente
    flag_pattern = r"crypto\\{{[^}}]+\\}}|flag\\{{[^}}]+\\}}"
    flags = re.findall(flag_pattern, challenge_text)
    if flags:
        return flags[0]
    
    # 2. Intentar decodificación Base64
    try:
        import base64
        potential_b64 = re.findall(r'[A-Za-z0-9+/]{{20,}}=*', challenge_text)
        for b64_str in potential_b64:
            try:
                decoded = base64.b64decode(b64_str).decode('utf-8')
                flag_in_decoded = re.findall(flag_pattern, decoded)
                if flag_in_decoded:
                    return flag_in_decoded[0]
            except:
                continue
    except:
        pass
    
    # 3. Análisis XOR simple
    try:
        hex_pattern = r'[0-9a-fA-F]{{20,}}'
        hex_strings = re.findall(hex_pattern, challenge_text)
        for hex_str in hex_strings:
            if len(hex_str) % 2 == 0:
                try:
                    data = bytes.fromhex(hex_str)
                    # Probar XOR con keys comunes
                    for key in [b'A', b'key', b'flag']:
                        result = bytes(a ^ key[i % len(key)] for i, a in enumerate(data))
                        if b'crypto{{' in result or b'flag{{' in result:
                            return result.decode('utf-8', errors='ignore')
                except:
                    continue
    except:
        pass
    
    return "Flag no encontrada con métodos genéricos"

if __name__ == "__main__":
    result = solve_challenge()
    print(f"FLAG: {{result}}")
'''
    
    def get_knowledge_stats(self) -> Dict:
        """Retorna estadísticas del conocimiento interpretado"""
        
        stats = {
            'total_challenges_processed': len(self.processed_data) if self.processed_data else 0,
            'pattern_categories': len(self.pattern_library),
            'technique_count': len(self.technique_effectiveness),
            'solution_templates': len(self.solution_templates),
            'top_techniques': []
        }
        
        # Top técnicas por efectividad
        if self.technique_effectiveness:
            sorted_techniques = sorted(
                self.technique_effectiveness.items(),
                key=lambda x: x[1]['success_rate'] * x[1]['confidence'],
                reverse=True
            )
            stats['top_techniques'] = [
                {
                    'technique': tech,
                    'effectiveness': data['success_rate'],
                    'usage_count': data['usage_count'],
                    'confidence': data['confidence']
                }
                for tech, data in sorted_techniques[:10]
            ]
        
        return stats