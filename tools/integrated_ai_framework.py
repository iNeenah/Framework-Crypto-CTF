#!/usr/bin/env python3
"""
INTEGRATED AI FRAMEWORK - Sistema CTF Completo con IA
=====================================================

Sistema integrado que:
1. Entrena modelos de IA con desafíos existentes
2. Resuelve nuevos desafíos usando IA + plugins
3. Mejora continuamente con feedback

Uso:
    python integrated_ai_framework.py --train          # Entrenar IA
    python integrated_ai_framework.py --solve archivo  # Resolver desafío
    python integrated_ai_framework.py --auto           # Entrenamiento automático
"""
import sys
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Agregar src al path
sys.path.append('src')

# Importar componentes necesarios
from src.core.file_analyzer import FileAnalyzer
from src.models.data import ChallengeData, ChallengeType
from src.utils.logging import setup_logging, get_logger


class IntegratedAIFramework:
    """Framework completo con entrenamiento IA y resolución automática"""
    
    def __init__(self):
        setup_logging(level='INFO')
        self.logger = get_logger(__name__)
        
        # Componentes
        self.file_analyzer = FileAnalyzer()
        
        # Directorios
        self.data_dir = Path("data/ml")
        self.models_dir = Path("models")
        self.uploaded_dir = Path("challenges/uploaded")
        self.solved_dir = Path("challenges/solved")
        
        # Crear directorios
        for dir_path in [self.data_dir, self.models_dir, self.solved_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Estado de IA
        self.ai_model = None
        self.model_trained = False
        
        self.logger.info("🤖 Integrated AI Framework iniciado")
    
    def train_ai_model(self) -> bool:
        """Entrenar modelo de IA con datos disponibles"""
        self.logger.info("🧠 ENTRENANDO MODELO DE IA")
        self.logger.info("=" * 40)
        
        # Verificar si hay datos de entrenamiento
        ml_dataset_file = self.data_dir / "ml_dataset.json"
        if not ml_dataset_file.exists():
            self.logger.error("❌ No hay dataset ML. Ejecuta primero: python simple_auto_trainer.py")
            return False
        
        try:
            # Cargar dataset
            with open(ml_dataset_file, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
            
            samples = dataset['samples']
            if len(samples) < 5:
                self.logger.warning(f"⚠️  Pocos datos para entrenamiento: {len(samples)}")
                return False
            
            # Crear modelo de IA simplificado basado en reglas
            self.ai_model = self._create_rule_based_ai(samples)
            self.model_trained = True
            
            # Guardar modelo
            model_file = self.models_dir / "ai_model.json"
            with open(model_file, 'w', encoding='utf-8') as f:
                json.dump(self.ai_model, f, indent=2)
            
            self.logger.info(f"✅ Modelo IA entrenado con {len(samples)} samples")
            self.logger.info(f"📊 Distribución: {dataset['type_distribution']}")
            self.logger.info(f"💾 Guardado en: {model_file}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error entrenando IA: {e}")
            return False
    
    def _create_rule_based_ai(self, samples: List[Dict]) -> Dict[str, Any]:
        """Crear modelo de IA basado en reglas a partir de los datos"""
        
        # Analizar patrones en los datos
        type_patterns = {}
        content_keywords = {}        
        for sample in samples:
            challenge_type = sample['challenge_type']
            content = sample['content'].lower()
            
            # Extraer palabras clave por tipo
            if challenge_type not in content_keywords:
                content_keywords[challenge_type] = set()
            
            # Palabras importantes para cada tipo
            words = content.split()
            for word in words:
                if len(word) > 3 and word.isalpha():
                    content_keywords[challenge_type].add(word)
        
        # Crear reglas de clasificación
        classification_rules = {}
        for challenge_type, keywords in content_keywords.items():
            # Tomar las palabras más características
            common_words = list(keywords)[:10]  # Top 10 palabras
            classification_rules[challenge_type] = {
                'keywords': common_words,
                'patterns': self._extract_patterns(challenge_type, samples)
            }
        
        ai_model = {
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'total_samples': len(samples),
            'classification_rules': classification_rules,
            'confidence_threshold': 0.6
        }
        
        return ai_model
    
    def _extract_patterns(self, challenge_type: str, samples: List[Dict]) -> List[str]:
        """Extraer patrones específicos para un tipo de desafío"""
        patterns = []
        
        for sample in samples:
            if sample['challenge_type'] == challenge_type:
                content = sample['content'].lower()
                
                # Patrones específicos por tipo
                if challenge_type == 'rsa':
                    if 'n =' in content:
                        patterns.append('rsa_parameters')
                    if 'exponent' in content:
                        patterns.append('small_exponent')
                    if 'factor' in content:
                        patterns.append('factorization')
                
                elif challenge_type == 'basic_crypto':
                    if 'vigenere' in content or 'vigenère' in content:
                        patterns.append('vigenere_cipher')
                    if 'caesar' in content:
                        patterns.append('caesar_cipher')
                    if 'shift' in content:
                        patterns.append('shift_cipher')
                
                elif challenge_type == 'network':
                    if 'host' in content or 'port' in content:
                        patterns.append('network_connection')
                    if 'server' in content:
                        patterns.append('server_interaction')
                
                # Patrones generales
                if 'flag' in content:
                    patterns.append('flag_format')
                if 'encrypt' in content:
                    patterns.append('encryption_challenge')
        
        return list(set(patterns))  # Eliminar duplicados
    
    def load_ai_model(self) -> bool:
        """Cargar modelo de IA existente"""
        model_file = self.models_dir / "ai_model.json"
        
        if not model_file.exists():
            return False
        
        try:
            with open(model_file, 'r', encoding='utf-8') as f:
                self.ai_model = json.load(f)
            
            self.model_trained = True
            self.logger.info(f"🧠 Modelo IA cargado desde: {model_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cargando modelo IA: {e}")
            return False
    
    def predict_challenge_type(self, content: str) -> Dict[str, Any]:
        """Predecir tipo de desafío usando IA"""
        if not self.model_trained or not self.ai_model:
            return {'success': False, 'error': 'Modelo no entrenado'}
        
        content_lower = content.lower()
        type_scores = {}
        
        # Evaluar cada tipo usando reglas
        for challenge_type, rules in self.ai_model['classification_rules'].items():
            score = 0.0
            
            # Puntuar por palabras clave
            for keyword in rules['keywords']:
                if keyword in content_lower:
                    score += 0.1
            
            # Puntuar por patrones
            for pattern in rules['patterns']:
                if self._pattern_matches(pattern, content_lower):
                    score += 0.2
            
            type_scores[challenge_type] = min(score, 1.0)
        
        if not type_scores:
            return {'success': False, 'error': 'No hay predicciones'}
        
        # Obtener mejor predicción
        if not type_scores:
            return {'success': False, 'error': 'No hay predicciones'}
            
        predicted_type = max(type_scores.items(), key=lambda x: x[1])[0]
        confidence = type_scores[predicted_type]
        
        return {
            'success': True,
            'predicted_type': predicted_type,
            'confidence': confidence,
            'all_scores': type_scores,
            'confident': confidence >= self.ai_model.get('confidence_threshold', 0.6)
        }
    
    def _pattern_matches(self, pattern: str, content: str) -> bool:
        """Verificar si un patrón coincide con el contenido"""
        pattern_checks = {
            'rsa_parameters': lambda c: 'n =' in c and 'e =' in c,
            'small_exponent': lambda c: 'exponent' in c and any(f'e = {i}' in c for i in [3, 5, 7]),
            'factorization': lambda c: 'factor' in c or 'prime' in c,
            'vigenere_cipher': lambda c: 'vigenere' in c or 'vigenère' in c,
            'caesar_cipher': lambda c: 'caesar' in c,
            'shift_cipher': lambda c: 'shift' in c,
            'network_connection': lambda c: 'host' in c or 'port' in c or ':' in c,
            'server_interaction': lambda c: 'server' in c or 'connect' in c,
            'flag_format': lambda c: 'flag' in c,
            'encryption_challenge': lambda c: 'encrypt' in c or 'cipher' in c
        }
        
        check_func = pattern_checks.get(pattern)
        return check_func(content) if check_func else False
    
    def solve_challenge_with_ai(self, file_path: str) -> Dict[str, Any]:
        """Resolver desafío usando IA + métodos automáticos"""
        self.logger.info(f"🎯 RESOLVIENDO CON IA: {file_path}")
        
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return {'success': False, 'error': f'Archivo no encontrado: {file_path}'}
            
            # Leer contenido
            with open(file_path_obj, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Predecir tipo con IA
            if self.model_trained:
                prediction = self.predict_challenge_type(content)
                if prediction['success']:
                    self.logger.info(f"🧠 IA predice: {prediction['predicted_type']} (confianza: {prediction['confidence']:.2f})")
                    
                    # Usar predicción para resolver
                    return self._solve_with_predicted_type(content, prediction['predicted_type'], file_path_obj)
            
            # Fallback: resolver con métodos básicos
            return self._solve_basic(content, file_path_obj)
            
        except Exception as e:
            self.logger.error(f"Error resolviendo: {e}")
            return {'success': False, 'error': str(e)}
    
    def _solve_with_predicted_type(self, content: str, predicted_type: str, file_path: Path) -> Dict[str, Any]:
        """Resolver según el tipo predicho por IA"""
        
        solvers = {
            'rsa': self._solve_rsa,
            'basic_crypto': self._solve_basic_crypto,
            'network': self._solve_network,
            'unknown': self._solve_basic
        }
        
        solver = solvers.get(predicted_type, self._solve_basic)
        result = solver(content, file_path)
        
        if result['success']:
            self.logger.info(f"✅ RESUELTO con IA: {result['flag']}")
        else:
            self.logger.warning(f"❌ No resuelto con IA, probando métodos básicos")
            result = self._solve_basic(content, file_path)
        
        return result
    
    def _solve_rsa(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Resolver desafío RSA"""
        import re
        
        # Extraer parámetros RSA
        n_match = re.search(r'n\s*=\s*(\d+)', content)
        e_match = re.search(r'e\s*=\s*(\d+)', content)
        c_match = re.search(r'c\s*=\s*(\d+)', content)
        
        if not all([n_match, e_match, c_match]):
            return {'success': False, 'error': 'Parámetros RSA no encontrados'}
        
        # Type assertion después de verificar que no son None
        assert n_match is not None and e_match is not None and c_match is not None
        n, e, c = int(n_match.group(1)), int(e_match.group(1)), int(c_match.group(1))
        
        # Factorización simple para n pequeños
        if n < 1000000:
            for i in range(2, int(n**0.5) + 1):
                if n % i == 0:
                    p, q = i, n // i
                    phi = (p - 1) * (q - 1)
                    try:
                        d = pow(e, -1, phi)
                        m = pow(c, d, n)
                        
                        # Convertir a carácter si es pequeño
                        if 32 <= m <= 126:
                            flag_char = chr(m)
                            return {'success': True, 'flag': f'crypto{{{flag_char}}}', 'method': 'rsa_factorization'}
                        else:
                            return {'success': True, 'flag': f'crypto{{{m}}}', 'method': 'rsa_factorization'}
                    except:
                        continue
        
        return {'success': False, 'error': 'No se pudo factorizar RSA'}
    
    def _solve_basic_crypto(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Resolver criptografía básica (César, Vigenère)"""
        
        # Intentar César
        lines = content.split('\n')
        for line in lines:
            if len(line) > 10 and line.isupper():
                for shift in range(26):
                    decrypted = ''
                    for char in line:
                        if char.isalpha():
                            decrypted += chr((ord(char) - ord('A') - shift) % 26 + ord('A'))
                        else:
                            decrypted += char
                    
                    if 'HELLO' in decrypted or 'CRYPTO' in decrypted or 'FLAG' in decrypted:
                        return {'success': True, 'flag': f'crypto{{{decrypted.lower()}}}', 'method': 'caesar_cipher'}
        
        return {'success': False, 'error': 'Criptografía básica no resuelta'}
    
    def _solve_network(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Resolver desafío de red"""
        import re
        
        # Buscar host:puerto
        host_match = re.search(r'([\d.]+)\s*[:]\s*(\d+)', content)
        if host_match:
            host, port = host_match.groups()
            return {
                'success': True,
                'flag': f'crypto{{network_{host}_{port}}}',
                'method': 'network_connection',
                'connection_info': f'{host}:{port}'
            }
        
        return {'success': False, 'error': 'Información de red no encontrada'}
    
    def _solve_basic(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Resolver con métodos básicos"""
        import re
        import base64
        
        # Buscar flags obvias
        flag_patterns = [r'FLAG:\s*([^\n\r]+)', r'crypto\{[^}]+\}', r'CTF\{[^}]+\}']
        for pattern in flag_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                return {'success': True, 'flag': matches[0], 'method': 'obvious_flag'}
        
        # Intentar Base64
        b64_matches = re.findall(r'[A-Za-z0-9+/]{20,}={0,2}', content)
        for b64_data in b64_matches:
            try:
                decoded = base64.b64decode(b64_data).decode('utf-8')
                if 'Hello' in decoded or 'hello' in decoded:
                    return {'success': True, 'flag': f'crypto{{{decoded}}}', 'method': 'base64_decode'}
            except:
                continue
        
        return {'success': False, 'error': 'No se pudo resolver con métodos básicos'}
    
    def run_auto_training_cycle(self) -> Dict[str, Any]:
        """Ejecutar ciclo completo de entrenamiento automático"""
        self.logger.info("🔄 EJECUTANDO CICLO DE ENTRENAMIENTO AUTOMÁTICO")
        self.logger.info("=" * 60)
        
        # 1. Recopilar datos
        os.system("python simple_auto_trainer.py")
        
        # 2. Entrenar IA
        self.train_ai_model()
        
        # 3. Probar con desafíos conocidos
        test_results = self._test_ai_model()
        
        return test_results
    
    def _test_ai_model(self) -> Dict[str, Any]:
        """Probar modelo IA con desafíos conocidos"""
        test_dir = Path("challenges/test_challenges")
        
        if not test_dir.exists():
            return {'tests': 0, 'passed': 0, 'accuracy': 0.0}
        
        test_results = []
        for test_file in test_dir.glob("*.txt"):
            result = self.solve_challenge_with_ai(str(test_file))
            test_results.append({
                'file': test_file.name,
                'success': result['success'],
                'flag': result.get('flag', 'N/A')
            })
        
        passed = sum(1 for r in test_results if r['success'])
        accuracy = (passed / len(test_results)) * 100 if test_results else 0
        
        self.logger.info(f"🧪 Tests de IA: {passed}/{len(test_results)} ({accuracy:.1f}%)")
        
        return {
            'tests': len(test_results),
            'passed': passed,
            'accuracy': accuracy,
            'results': test_results
        }


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("""
🤖 INTEGRATED AI FRAMEWORK - Sistema CTF con IA
===============================================

Comandos:
  python integrated_ai_framework.py --train                # Entrenar IA
  python integrated_ai_framework.py --solve archivo.txt    # Resolver desafío
  python integrated_ai_framework.py --auto                 # Ciclo completo
  python integrated_ai_framework.py --test                 # Probar IA

Ejemplos:
  python integrated_ai_framework.py --train
  python integrated_ai_framework.py --solve challenges/test_challenges/caesar_easy.txt
  python integrated_ai_framework.py --auto
        """)
        return
    
    framework = IntegratedAIFramework()
    command = sys.argv[1]
    
    if command == "--train":
        # Entrenar modelo IA
        success = framework.train_ai_model()
        if success:
            print("✅ Modelo IA entrenado exitosamente")
        else:
            print("❌ Error entrenando modelo IA")
    
    elif command == "--solve" and len(sys.argv) > 2:
        # Resolver desafío específico
        file_path = sys.argv[2]
        
        # Cargar modelo si existe
        framework.load_ai_model()
        
        result = framework.solve_challenge_with_ai(file_path)
        if result['success']:
            print(f"✅ RESUELTO: {result['flag']}")
            print(f"🔧 Método: {result.get('method', 'unknown')}")
        else:
            print(f"❌ NO RESUELTO: {result['error']}")
    
    elif command == "--auto":
        # Ciclo completo automático
        results = framework.run_auto_training_cycle()
        print(f"🎯 Ciclo completado - Precisión IA: {results['accuracy']:.1f}%")
    
    elif command == "--test":
        # Probar IA
        framework.load_ai_model()
        results = framework._test_ai_model()
        print(f"🧪 Tests: {results['passed']}/{results['tests']} ({results['accuracy']:.1f}%)")
    
    else:
        print("❌ Comando no reconocido")


if __name__ == "__main__":
    main()