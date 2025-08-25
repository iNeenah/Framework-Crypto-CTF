#!/usr/bin/env python3
"""
EXPERT ML FRAMEWORK - Aprendizaje de Writeups y Técnicas Expertas
================================================================

Sistema que aprende de writeups de CTF para resolver desafíos complejos:
1. Analiza writeups de profesionales
2. Extrae técnicas y patrones
3. Entrena modelos ML/DL
4. Predice estrategias para nuevos desafíos

"""
import sys
import os
import json
import re
import pickle
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Agregar src al path
sys.path.append('src')

class ExpertKnowledgeExtractor:
    """Extractor de conocimiento de writeups expertos"""
    
    def analyze_writeup(self, writeup_text: str, challenge_info: Dict) -> Dict:
        """Analizar writeup y extraer conocimiento experto"""
        
        # Extraer técnicas mencionadas
        techniques = self._extract_techniques(writeup_text)
        
        # Extraer pasos de solución
        steps = self._extract_solution_steps(writeup_text)
        
        # Extraer código/herramientas
        tools = self._extract_tools(writeup_text)
        code = self._extract_code(writeup_text)
        
        # Analizar complejidad
        complexity = self._analyze_complexity(writeup_text)
        
        return {
            'challenge_type': challenge_info.get('type', 'unknown'),
            'difficulty': challenge_info.get('difficulty', 'medium'),
            'techniques': techniques,
            'solution_steps': steps,
            'tools_used': tools,
            'code_snippets': code,
            'complexity_level': complexity,
            'timestamp': datetime.now().isoformat()
        }
    
    def _extract_techniques(self, text: str) -> List[str]:
        """Extraer técnicas criptográficas del writeup"""
        techniques = []
        text_lower = text.lower()
        
        # Técnicas RSA
        rsa_techniques = [
            'wiener attack', 'hastad attack', 'common modulus',
            'factorization', 'small exponent', 'broadcast attack',
            'coppersmith', 'franklin-reiter'
        ]
        
        # Técnicas clásicas
        classical = [
            'frequency analysis', 'caesar cipher', 'vigenere',
            'substitution cipher', 'kasiski'
        ]
        
        # Técnicas modernas
        modern = [
            'invalid curve attack', 'length extension', 'padding oracle',
            'timing attack', 'side channel'
        ]
        
        all_techniques = rsa_techniques + classical + modern
        
        for technique in all_techniques:
            if technique in text_lower:
                techniques.append(technique)
        
        return techniques
    
    def _extract_solution_steps(self, text: str) -> List[str]:
        """Extraer pasos de la solución"""
        steps = []
        
        # Buscar pasos numerados
        step_patterns = [
            r'(\d+)\.\s*([^\n]{10,})',
            r'Step\s+(\d+)[:\s]*([^\n]{10,})',
            r'([•\-\*])\s*([^\n]{10,})'
        ]
        
        for pattern in step_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                step_text = match[1] if len(match) > 1 else match[0]
                if len(step_text.strip()) > 10:
                    steps.append(step_text.strip())
        
        return steps
    
    def _extract_tools(self, text: str) -> List[str]:
        """Extraer herramientas mencionadas"""
        tools = []
        text_lower = text.lower()
        
        common_tools = [
            'sage', 'python', 'factordb', 'openssl', 'john', 'hashcat',
            'wireshark', 'burp', 'gmpy2', 'pycryptodome', 'sympy'
        ]
        
        for tool in common_tools:
            if tool in text_lower:
                tools.append(tool)
        
        return tools
    
    def _extract_code(self, text: str) -> List[str]:
        """Extraer fragmentos de código"""
        code_snippets = []
        
        # Buscar bloques de código
        code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', text, re.DOTALL)
        inline_code = re.findall(r'`([^`]{10,})`', text)
        
        code_snippets.extend(code_blocks)
        code_snippets.extend(inline_code)
        
        return [code.strip() for code in code_snippets if len(code.strip()) > 10]
    
    def _analyze_complexity(self, text: str) -> int:
        """Analizar nivel de complejidad (1-10)"""
        complexity_score = 1
        text_lower = text.lower()
        
        # Indicadores de alta complejidad
        if 'theorem' in text_lower or 'algorithm' in text_lower:
            complexity_score += 2
        if 'polynomial' in text_lower or 'exponential' in text_lower:
            complexity_score += 2
        if len(re.findall(r'import|def |class ', text)) > 5:
            complexity_score += 2
        if 'sage' in text_lower or 'mathematica' in text_lower:
            complexity_score += 1
        
        return min(complexity_score, 10)


class MLChallengePredictor:
    """Predictor ML para estrategias de resolución"""
    
    def __init__(self, models_dir: Path = None):
        self.model = None
        self.feature_names = []
        self.challenge_types = []
        self.models_dir = models_dir or Path("models/expert")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Intentar cargar modelo existente
        self._load_model()
    
    def _save_model(self):
        """Guardar modelo entrenado"""
        if self.model is not None:
            model_file = self.models_dir / "expert_model.pkl"
            try:
                with open(model_file, 'wb') as f:
                    pickle.dump({
                        'model': self.model,
                        'feature_names': self.feature_names,
                        'challenge_types': self.challenge_types
                    }, f)
                print(f"💾 Modelo guardado en: {model_file}")
            except Exception as e:
                print(f"⚠️ Error guardando modelo: {e}")
    
    def _load_model(self):
        """Cargar modelo existente"""
        model_file = self.models_dir / "expert_model.pkl"
        if model_file.exists():
            try:
                with open(model_file, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.feature_names = data['feature_names']
                    self.challenge_types = data['challenge_types']
                print(f"📥 Modelo cargado desde: {model_file}")
            except Exception as e:
                print(f"⚠️ Error cargando modelo: {e}")
                self.model = None
    
    def train_from_knowledge(self, knowledge_data: List[Dict]) -> Dict:
        """Entrenar modelo con conocimiento experto extraído"""
        
        if len(knowledge_data) < 3:
            return {'error': 'Se necesitan al menos 3 writeups'}
        
        try:
            import numpy as np
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score
            
            # Preparar características
            features = []
            labels = []
            
            for knowledge in knowledge_data:
                feature_vector = self._create_feature_vector(knowledge)
                features.append(feature_vector)
                labels.append(knowledge['challenge_type'])
            
            X = np.array(features)
            y = np.array(labels)
            
            # Entrenar modelo
            if len(set(labels)) > 1:  # Multiple classes
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
                
                self.model = RandomForestClassifier(n_estimators=50, random_state=42)
                self.model.fit(X_train, y_train)
                
                predictions = self.model.predict(X_test)
                accuracy = accuracy_score(y_test, predictions)
            else:
                # Single class - train on all data
                self.model = RandomForestClassifier(n_estimators=50, random_state=42)
                self.model.fit(X, y)
                accuracy = 1.0
            
            self.challenge_types = list(set(labels))
            
            # Guardar modelo entrenado
            self._save_model()
            
            return {
                'success': True,
                'accuracy': accuracy,
                'samples': len(knowledge_data),
                'challenge_types': self.challenge_types
            }
            
        except ImportError:
            return {'error': 'Instala scikit-learn: pip install scikit-learn'}
        except Exception as e:
            return {'error': f'Error entrenando: {str(e)}'}
    
    def _create_feature_vector(self, knowledge: Dict) -> List[float]:
        """Crear vector de características"""
        features = []
        
        # Técnicas conocidas
        known_techniques = [
            'wiener attack', 'factorization', 'frequency analysis',
            'invalid curve attack', 'length extension'
        ]
        
        for technique in known_techniques:
            features.append(1.0 if technique in knowledge.get('techniques', []) else 0.0)
        
        # Herramientas
        known_tools = ['sage', 'python', 'factordb', 'openssl']
        for tool in known_tools:
            features.append(1.0 if tool in knowledge.get('tools_used', []) else 0.0)
        
        # Características numéricas
        features.append(float(len(knowledge.get('solution_steps', []))))
        features.append(float(knowledge.get('complexity_level', 1)))
        features.append(float(len(knowledge.get('code_snippets', []))))
        
        return features
    
    def predict_strategy(self, challenge_text: str) -> Dict:
        """Predecir estrategia para nuevo desafío"""
        
        if self.model is None:
            return {'error': 'Modelo no entrenado'}
        
        try:
            # Análisis básico del desafío
            mock_knowledge = {
                'techniques': self._detect_challenge_techniques(challenge_text),
                'tools_used': [],
                'solution_steps': [],
                'complexity_level': self._estimate_complexity(challenge_text),
                'code_snippets': []
            }
            
            # Crear vector de características
            features = self._create_feature_vector(mock_knowledge)
            
            # Predecir
            prediction = self.model.predict([features])[0]
            probabilities = self.model.predict_proba([features])[0] if hasattr(self.model, 'predict_proba') else [1.0]
            
            return {
                'predicted_type': prediction,
                'confidence': float(max(probabilities)),
                'suggested_techniques': mock_knowledge['techniques']
            }
            
        except Exception as e:
            return {'error': f'Error prediciendo: {str(e)}'}
    
    def _detect_challenge_techniques(self, text: str) -> List[str]:
        """Detectar técnicas posibles en el desafío"""
        techniques = []
        text_lower = text.lower()
        
        if 'rsa' in text_lower:
            if 'factor' in text_lower:
                techniques.append('factorization')
            if 'small' in text_lower and 'exponent' in text_lower:
                techniques.append('wiener attack')
        
        if 'frequency' in text_lower or 'letter' in text_lower:
            techniques.append('frequency analysis')
        
        return techniques
    
    def _estimate_complexity(self, text: str) -> int:
        """Estimar complejidad del desafío"""
        complexity = 1
        
        if len(text) > 1000:
            complexity += 2
        if 'rsa' in text.lower() and any(x in text for x in ['1024', '2048', '4096']):
            complexity += 3
        if any(word in text.lower() for word in ['theorem', 'algorithm', 'proof']):
            complexity += 2
        
        return min(complexity, 10)


class ExpertMLFramework:
    """Framework principal ML que aprende de expertos"""
    
    def __init__(self):
        self.knowledge_extractor = ExpertKnowledgeExtractor()
        
        # Directorios
        self.writeups_dir = Path("data/expert_writeups")
        self.knowledge_dir = Path("data/expert_knowledge")
        self.models_dir = Path("models/expert")
        
        for dir_path in [self.writeups_dir, self.knowledge_dir, self.models_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Inicializar predictor ML con directorio de modelos
        self.ml_predictor = MLChallengePredictor(self.models_dir)
        
        print("🧠 Expert ML Framework iniciado")
    
    def add_expert_writeup(self, writeup_text: str, challenge_info: Dict) -> bool:
        """Agregar writeup de experto al sistema"""
        
        try:
            # Extraer conocimiento
            knowledge = self.knowledge_extractor.analyze_writeup(writeup_text, challenge_info)
            
            # Guardar conocimiento
            writeup_id = f"expert_{len(list(self.knowledge_dir.glob('*.json'))) + 1}"
            knowledge_file = self.knowledge_dir / f"{writeup_id}.json"
            
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(knowledge, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Writeup experto procesado: {writeup_id}")
            print(f"   Técnicas extraídas: {knowledge['techniques']}")
            print(f"   Complejidad: {knowledge['complexity_level']}/10")
            
            return True
            
        except Exception as e:
            print(f"❌ Error procesando writeup: {e}")
            return False
    
    def train_expert_model(self) -> Dict:
        """Entrenar modelo con conocimiento de expertos"""
        
        print("🚀 Entrenando con conocimiento de expertos...")
        
        # Cargar todo el conocimiento
        knowledge_data = []
        for knowledge_file in self.knowledge_dir.glob("*.json"):
            try:
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    knowledge_data.append(json.load(f))
            except Exception as e:
                print(f"⚠️ Error cargando {knowledge_file}: {e}")
        
        if not knowledge_data:
            return {'error': 'No hay conocimiento experto disponible'}
        
        # Entrenar modelo
        result = self.ml_predictor.train_from_knowledge(knowledge_data)
        
        if result.get('success'):
            # Guardar modelo
            model_info = {
                'trained_at': datetime.now().isoformat(),
                'writeups_used': len(knowledge_data),
                'accuracy': result['accuracy'],
                'challenge_types': result['challenge_types']
            }
            
            info_file = self.models_dir / "expert_model_info.json"
            with open(info_file, 'w') as f:
                json.dump(model_info, f, indent=2)
            
            print(f"✅ Modelo experto entrenado")
            print(f"   Precisión: {result['accuracy']:.3f}")
            print(f"   Writeups: {len(knowledge_data)}")
        
        return result
    
    def predict_expert_strategy(self, challenge_text: str) -> Dict:
        """Predecir estrategia usando conocimiento experto"""
        
        print("🔮 Prediciendo estrategia experta...")
        
        prediction = self.ml_predictor.predict_strategy(challenge_text)
        
        if 'error' not in prediction:
            print(f"📊 Tipo predicho: {prediction['predicted_type']}")
            print(f"📊 Confianza: {prediction['confidence']:.3f}")
            print(f"🔧 Técnicas sugeridas: {prediction['suggested_techniques']}")
        
        return prediction


def main():
    """Función principal"""
    
    framework = ExpertMLFramework()
    
    if len(sys.argv) < 2:
        print("""
🧠 EXPERT ML FRAMEWORK - Aprendizaje de Writeups Expertos
=========================================================

Comandos:
  python expert_ml_framework.py add        # Agregar writeup experto
  python expert_ml_framework.py train      # Entrenar con expertos
  python expert_ml_framework.py predict <archivo>  # Predecir estrategia
  python expert_ml_framework.py --learn-file <archivo>  # Aprender de archivo
  python expert_ml_framework.py --learn-dir <directorio>  # Aprender de directorio
  python expert_ml_framework.py --learn-url <url>  # Aprender de URL
  python expert_ml_framework.py --solve <archivo>  # Resolver con Expert ML
  python expert_ml_framework.py --analyze <archivo>  # Solo análisis
  python expert_ml_framework.py --solve-verbose <archivo>  # Resolver con explicación
  python expert_ml_framework.py --status  # Estado del modelo

Flujo recomendado:
1. Agregar varios writeups de expertos (add o --learn-file)
2. Entrenar modelo (train)  
3. Predecir estrategias para nuevos desafíos (predict o --solve)
        """)
        return
    
    command = sys.argv[1]
    
    # Comandos del sistema de gestión
    if command == "--learn-file" and len(sys.argv) > 2:
        file_path = sys.argv[2]
        print(f"📖 Aprendiendo de archivo: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                writeup_text = f.read()
            
            # Detectar tipo automáticamente
            challenge_type = "crypto"
            if "rsa" in writeup_text.lower():
                challenge_type = "rsa"
            elif "web" in writeup_text.lower():
                challenge_type = "web"
            elif "network" in writeup_text.lower():
                challenge_type = "network"
            
            challenge_info = {'type': challenge_type, 'difficulty': 'medium'}
            success = framework.add_expert_writeup(writeup_text, challenge_info)
            
            if success:
                print("🔄 Re-entrenando modelo automáticamente...")
                framework.train_expert_model()
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif command == "--learn-dir" and len(sys.argv) > 2:
        dir_path = Path(sys.argv[2])
        print(f"📚 Aprendiendo de directorio: {dir_path}")
        
        count = 0
        # Buscar archivos .txt, .md y .py
        file_patterns = ["*.txt", "*.md", "*.py"]
        
        for pattern in file_patterns:
            for file_path in dir_path.rglob(pattern):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        writeup_text = f.read()
                    
                    # Detectar tipo automáticamente
                    challenge_type = "crypto"
                    writeup_lower = writeup_text.lower()
                    
                    if "rsa" in writeup_lower:
                        challenge_type = "rsa"
                    elif "elliptic" in writeup_lower or "ecc" in writeup_lower:
                        challenge_type = "elliptic_curve"
                    elif "aes" in writeup_lower or "symmetric" in writeup_lower:
                        challenge_type = "symmetric"
                    elif "hash" in writeup_lower or "sha" in writeup_lower:
                        challenge_type = "hash"
                    
                    challenge_info = {'type': challenge_type, 'difficulty': 'medium'}
                    if framework.add_expert_writeup(writeup_text, challenge_info):
                        count += 1
                        print(f"  📝 {file_path.name} -> {challenge_type}")
                except Exception as e:
                    print(f"⚠️ Error con {file_path}: {e}")
        
        print(f"✅ Procesados {count} writeups")
        if count > 0:
            print("🔄 Re-entrenando modelo...")
            result = framework.train_expert_model()
            if result.get('success'):
                print(f"✨ Modelo actualizado - Precisión: {result['accuracy']:.3f}")
            else:
                print(f"❌ Error entrenando: {result.get('error', 'Unknown')}")
    
    elif command == "--learn-url" and len(sys.argv) > 2:
        url = sys.argv[2]
        print(f"🌐 Descargando writeup de: {url}")
        print("⚠️ Funcionalidad de URL pendiente de implementación")
        print("   Por ahora, descarga el contenido manualmente y usa --learn-file")
    
    elif command == "--solve" and len(sys.argv) > 2:
        challenge_file = sys.argv[2]
        print(f"🔮 Resolviendo con Expert ML: {challenge_file}")
        try:
            with open(challenge_file, 'r', encoding='utf-8') as f:
                challenge_text = f.read()
            
            prediction = framework.predict_expert_strategy(challenge_text)
            if 'error' not in prediction:
                print("\n🏆 ESTRATEGIA EXPERTA SUGERIDA:")
                print(f"📊 Tipo: {prediction['predicted_type']}")
                print(f"📊 Confianza: {prediction['confidence']:.3f}")
                print(f"🔧 Técnicas: {', '.join(prediction['suggested_techniques'])}")
                print("\n💡 Aplica estas técnicas manualmente o usa el framework integrado")
            else:
                print(f"❌ {prediction['error']}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif command == "--analyze" and len(sys.argv) > 2:
        challenge_file = sys.argv[2]
        print(f"🔍 Analizando desafío: {challenge_file}")
        try:
            with open(challenge_file, 'r', encoding='utf-8') as f:
                challenge_text = f.read()
            
            prediction = framework.predict_expert_strategy(challenge_text)
            if 'error' not in prediction:
                print("\n📊 ANÁLISIS EXPERTO:")
                print(f"📈 Tipo predicho: {prediction['predicted_type']}")
                print(f"📈 Nivel de confianza: {prediction['confidence']:.3f}")
                print(f"🔧 Técnicas recomendadas: {', '.join(prediction['suggested_techniques'])}")
                print(f"⚡ Complejidad estimada: {prediction.get('complexity', 'N/A')}")
            else:
                print(f"❌ {prediction['error']}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif command == "--solve-verbose" and len(sys.argv) > 2:
        challenge_file = sys.argv[2]
        print(f"🔮 Resolviendo con explicación detallada: {challenge_file}")
        try:
            with open(challenge_file, 'r', encoding='utf-8') as f:
                challenge_text = f.read()
            
            prediction = framework.predict_expert_strategy(challenge_text)
            if 'error' not in prediction:
                print("\n🎯 RESOLUCIÓN EXPERTA DETALLADA:")
                print("=" * 40)
                print(f"📊 Tipo de desafío: {prediction['predicted_type']}")
                print(f"📊 Confianza del modelo: {prediction['confidence']:.3f}")
                print(f"🔧 Técnicas principales: {', '.join(prediction['suggested_techniques'])}")
                print("\n📋 PASOS RECOMENDADOS:")
                for i, technique in enumerate(prediction['suggested_techniques'], 1):
                    print(f"  {i}. Aplicar {technique}")
                print("\n💡 Nota: Esta es una predicción basada en patrones de expertos")
                print("   Combina con el framework integrado para resolución automática")
            else:
                print(f"❌ {prediction['error']}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif command == "--status":
        print("\n📊 ESTADO DEL MODELO EXPERT ML")
        print("=" * 35)
        
        # Verificar archivos de conocimiento
        knowledge_files = list(framework.knowledge_dir.glob("*.json"))
        print(f"📚 Writeups expertos: {len(knowledge_files)}")
        
        # Verificar modelo entrenado
        model_info_file = framework.models_dir / "expert_model_info.json"
        if model_info_file.exists():
            try:
                with open(model_info_file, 'r') as f:
                    model_info = json.load(f)
                print(f"🧠 Modelo entrenado: Sí")
                print(f"📊 Precisión: {model_info['accuracy']:.3f}")
                print(f"📊 Writeups usados: {model_info['writeups_used']}")
                print(f"📊 Tipos conocidos: {', '.join(model_info['challenge_types'])}")
                print(f"📅 Última actualización: {model_info['trained_at'][:19]}")
            except Exception as e:
                print(f"🧠 Modelo: Error leyendo info - {e}")
        else:
            print("🧠 Modelo entrenado: No")
            print("💡 Ejecuta 'train' para entrenar el modelo")
        
        # Directorios
        print(f"\n📁 Directorios:")
        print(f"   Writeups: {framework.writeups_dir}")
        print(f"   Conocimiento: {framework.knowledge_dir}")
        print(f"   Modelos: {framework.models_dir}")
    
    # Comandos originales
    elif command == "add":
        print("📝 AGREGAR WRITEUP EXPERTO")
        print("=" * 30)
        
        # Obtener writeup
        source = input("¿Archivo o pegar texto? (file/paste): ").strip().lower()
        
        if source == "file":
            file_path = input("Ruta del archivo: ").strip()
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    writeup_text = f.read()
            except FileNotFoundError:
                print(f"❌ Archivo no encontrado: {file_path}")
                return
        else:
            print("Pega el writeup (termina con línea vacía):")
            lines = []
            while True:
                try:
                    line = input()
                    if not line:
                        break
                    lines.append(line)
                except KeyboardInterrupt:
                    break
            writeup_text = '\n'.join(lines)
        
        # Información del desafío
        challenge_type = input("Tipo (rsa/crypto/network/web/etc): ").strip() or "crypto"
        difficulty = input("Dificultad (easy/medium/hard/expert): ").strip() or "medium"
        
        challenge_info = {
            'type': challenge_type,
            'difficulty': difficulty
        }
        
        framework.add_expert_writeup(writeup_text, challenge_info)
    
    elif command == "train":
        result = framework.train_expert_model()
        if 'error' in result:
            print(f"❌ {result['error']}")
    
    elif command == "predict" and len(sys.argv) > 2:
        challenge_file = sys.argv[2]
        try:
            with open(challenge_file, 'r', encoding='utf-8') as f:
                challenge_text = f.read()
            
            prediction = framework.predict_expert_strategy(challenge_text)
            if 'error' in prediction:
                print(f"❌ {prediction['error']}")
        
        except FileNotFoundError:
            print(f"❌ Archivo no encontrado: {challenge_file}")
    
    else:
        print("❌ Comando no reconocido")


if __name__ == "__main__":
    main()