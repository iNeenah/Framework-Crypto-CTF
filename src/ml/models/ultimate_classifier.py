#!/usr/bin/env python3
"""
Clasificador ML Ultra-Avanzado para Crypto CTF Solver
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier, ExtraTreesClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.feature_selection import SelectKBest, f_classif
import joblib
import logging
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path
import re
import math

class UltimateClassifier:
    """Clasificador ML Ultra-Avanzado con ensemble optimizado"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # === ENSEMBLE DE ALGORITMOS OPTIMIZADOS ===
        self.rf_model = RandomForestClassifier(
            n_estimators=300,
            max_depth=20,
            min_samples_split=2,
            min_samples_leaf=1,
            max_features='sqrt',
            bootstrap=True,
            random_state=42,
            n_jobs=-1
        )
        
        self.et_model = ExtraTreesClassifier(
            n_estimators=300,
            max_depth=20,
            min_samples_split=2,
            min_samples_leaf=1,
            max_features='sqrt',
            bootstrap=False,
            random_state=42,
            n_jobs=-1
        )
        
        self.gb_model = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=15,
            learning_rate=0.1,
            subsample=0.8,
            random_state=42
        )
        
        self.svm_model = SVC(
            kernel='rbf',
            C=10.0,
            gamma='scale',
            probability=True,
            random_state=42
        )
        
        self.nn_model = MLPClassifier(
            hidden_layer_sizes=(200, 100, 50),
            activation='relu',
            solver='adam',
            alpha=0.001,
            learning_rate='adaptive',
            max_iter=2000,
            random_state=42
        )
        
        self.lr_model = LogisticRegression(
            C=1.0,
            solver='liblinear',
            multi_class='ovr',
            random_state=42,
            max_iter=1000
        )
        
        self.nb_model = GaussianNB()
        
        # === ENSEMBLE VOTING CLASSIFIER ===
        self.ensemble_model = VotingClassifier(
            estimators=[
                ('rf', self.rf_model),
                ('et', self.et_model),
                ('gb', self.gb_model),
                ('svm', self.svm_model),
                ('nn', self.nn_model),
                ('lr', self.lr_model),
                ('nb', self.nb_model)
            ],
            voting='soft',
            n_jobs=-1
        )
        
        # === PREPROCESSING ===
        self.scaler = RobustScaler()  # Más robusto a outliers
        self.feature_selector = SelectKBest(f_classif, k='all')
        
        # === METADATOS ===
        self.feature_names = []
        self.label_encoder = {}
        self.reverse_label_encoder = {}
        self.is_trained = False
        self.training_history = []
        self.feature_importance = {}
        
    def calculate_entropy(self, text: str) -> float:
        """Calcular entropía de Shannon optimizada"""
        if not text:
            return 0
        
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        entropy = 0
        text_len = len(text)
        for count in char_counts.values():
            probability = count / text_len
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def extract_ultimate_features(self, content: str) -> np.ndarray:
        """Extraer características ultra-avanzadas optimizadas"""
        features = []
        content_lower = content.lower()
        
        # === CARACTERÍSTICAS BÁSICAS OPTIMIZADAS ===
        features.append(len(content))  # 0: length
        features.append(len(content.split('\n')))  # 1: lines
        features.append(len(content.split()))  # 2: words
        features.append(self.calculate_entropy(content))  # 3: entropy
        features.append(len(set(content)))  # 4: unique_chars
        
        # === RATIOS OPTIMIZADOS ===
        total_chars = len(content) if content else 1
        features.append(sum(1 for c in content if c.isdigit()) / total_chars)  # 5: digit_ratio
        features.append(sum(1 for c in content if c.isalpha()) / total_chars)  # 6: alpha_ratio
        features.append(sum(1 for c in content if c.isupper()) / total_chars)  # 7: upper_ratio
        features.append(sum(1 for c in content if c.islower()) / total_chars)  # 8: lower_ratio
        features.append(sum(1 for c in content if c in '0123456789abcdefABCDEF') / total_chars)  # 9: hex_ratio
        
        # === PATRONES ESPECÍFICOS ULTRA-OPTIMIZADOS ===
        # Patrones hexadecimales
        hex_matches = re.findall(r'[0-9a-fA-F]{16,}', content)
        features.append(len(hex_matches))  # 10: hex_pattern_count
        features.append(sum(len(match) for match in hex_matches))  # 11: hex_total_length
        features.append(1 if any(len(match) > 100 for match in hex_matches) else 0)  # 12: has_very_long_hex
        
        # Patrones Base64
        b64_matches = re.findall(r'[A-Za-z0-9+/]{20,}={0,2}', content)
        features.append(len(b64_matches))  # 13: base64_count
        features.append(sum(len(match) for match in b64_matches))  # 14: base64_total_length
        
        # Números grandes
        big_numbers = re.findall(r'\d{30,}', content)
        features.append(len(big_numbers))  # 15: big_number_count
        features.append(max(len(n) for n in big_numbers) if big_numbers else 0)  # 16: biggest_number_length
        
        # === PALABRAS CLAVE ULTRA-ESPECÍFICAS ===
        crypto_keywords = {
            'rsa': ['rsa', 'modulus', 'exponent', 'factorization', 'prime', 'n =', 'e =', 'c ='],
            'stream': ['chacha', 'salsa', 'stream', 'nonce', 'keystream', 'known plaintext', 'reuse'],
            'hash': ['hash', 'md5', 'sha', 'digest', 'collision', 'rainbow', 'crack'],
            'ecc': ['elliptic', 'curve', 'ecdsa', 'point', 'discrete log'],
            'classical': ['caesar', 'vigenere', 'substitution', 'affine', 'shift', 'rot'],
            'base64': ['base64', 'b64', 'encoding', 'decode'],
            'xor': ['xor', 'exclusive', 'otp', 'single byte'],
            'network': ['tcp', 'http', 'ssl', 'packet', 'pcap']
        }
        
        for category, keywords in crypto_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            features.append(score)  # 17-24: keyword scores
        
        # === CARACTERÍSTICAS ESTRUCTURALES ===
        features.append(1 if re.search(r'[nec]\s*=\s*\d+', content) else 0)  # 25: has_rsa_params
        features.append(1 if 'nonce' in content_lower and 'reuse' in content_lower else 0)  # 26: has_nonce_reuse
        features.append(1 if 'known' in content_lower and 'plaintext' in content_lower else 0)  # 27: has_known_plaintext
        features.append(1 if any(pattern in content for pattern in ['def ', 'class ', 'import ']) else 0)  # 28: has_code
        features.append(1 if re.search(r'e\s*=\s*[35]', content) else 0)  # 29: has_small_exponent
        
        # === ANÁLISIS AVANZADO ===
        words = content.split()
        features.append(sum(len(word) for word in words) / len(words) if words else 0)  # 30: avg_word_length
        
        lines = content.split('\n')
        features.append(max(len(line) for line in lines) if lines else 0)  # 31: max_line_length
        
        # Distribución de caracteres únicos
        features.append(len(set(content)) / total_chars if total_chars > 0 else 0)  # 32: unique_char_ratio
        
        # Patrones repetitivos
        features.append(sum(1 for i, line1 in enumerate(lines) 
                          for line2 in lines[i+1:] 
                          if len(line1) > 10 and line1 == line2))  # 33: repeated_patterns
        
        # Formato específico
        features.append(1 if re.search(r'flag\{|htb\{|ctf\{', content_lower) else 0)  # 34: has_flag_format
        
        return np.array(features)
    
    def prepare_training_data(self, training_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Preparar datos de entrenamiento optimizado"""
        X = []
        y = []
        
        for sample in training_data:
            if 'features' in sample and 'metadata' in sample:
                # Usar contenido del dataset
                content = sample.get('content_preview', '')
                challenge_type = sample['metadata']['challenge_type']
            else:
                # Formato legacy
                content = sample.get('content', '')
                challenge_type = sample.get('type', 'UNKNOWN')
            
            features = self.extract_ultimate_features(content)
            X.append(features)
            y.append(challenge_type)
        
        # Crear codificación de etiquetas
        unique_labels = sorted(set(y))
        self.label_encoder = {label: idx for idx, label in enumerate(unique_labels)}
        self.reverse_label_encoder = {idx: label for label, idx in self.label_encoder.items()}
        
        # Convertir etiquetas a números
        y_encoded = [self.label_encoder[label] for label in y]
        
        return np.array(X), np.array(y_encoded)
    
    def optimize_hyperparameters(self, X_train, y_train):
        """Optimizar hiperparámetros usando Grid Search"""
        print("🔧 Optimizando hiperparámetros...")
        
        # Optimizar Random Forest
        rf_params = {
            'n_estimators': [200, 300],
            'max_depth': [15, 20, None],
            'min_samples_split': [2, 5]
        }
        
        rf_grid = GridSearchCV(
            RandomForestClassifier(random_state=42, n_jobs=-1),
            rf_params,
            cv=3,
            scoring='accuracy',
            n_jobs=-1
        )
        
        rf_grid.fit(X_train, y_train)
        self.rf_model = rf_grid.best_estimator_
        
        print(f"✅ Mejores parámetros RF: {rf_grid.best_params_}")
        
        # Actualizar ensemble
        self.ensemble_model = VotingClassifier(
            estimators=[
                ('rf', self.rf_model),
                ('et', self.et_model),
                ('gb', self.gb_model),
                ('svm', self.svm_model),
                ('nn', self.nn_model),
                ('lr', self.lr_model),
                ('nb', self.nb_model)
            ],
            voting='soft',
            n_jobs=-1
        )
    
    def train(self, training_data: List[Dict], optimize=True) -> Dict:
        """Entrenar el modelo ultra-avanzado"""
        try:
            if len(training_data) < 10:
                return {
                    'success': False,
                    'error': 'Insuficientes datos de entrenamiento (mínimo 10)',
                    'training_samples': len(training_data)
                }
            
            print(f"🚀 Iniciando entrenamiento ultra-avanzado...")
            print(f"📊 Muestras de entrenamiento: {len(training_data)}")
            
            X, y = self.prepare_training_data(training_data)
            print(f"📊 Características extraídas: {X.shape[1]}")
            print(f"📊 Clases detectadas: {len(set(y))}")
            
            # Normalizar características
            X_scaled = self.scaler.fit_transform(X)
            
            # Selección de características
            if X.shape[1] > 20:
                k_best = min(25, X.shape[1])
                self.feature_selector = SelectKBest(f_classif, k=k_best)
                X_scaled = self.feature_selector.fit_transform(X_scaled, y)
                print(f"📊 Características seleccionadas: {X_scaled.shape[1]}")
            
            # Dividir datos
            if len(X) > 30:
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y, test_size=0.2, random_state=42, stratify=y
                )
            else:
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y, test_size=0.3, random_state=42
                )
            
            # Optimizar hiperparámetros
            if optimize and len(X_train) > 20:
                self.optimize_hyperparameters(X_train, y_train)
            
            # Entrenar ensemble
            print("🎯 Entrenando ensemble de modelos...")
            self.ensemble_model.fit(X_train, y_train)
            
            # Evaluar
            y_pred = self.ensemble_model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Validación cruzada
            cv_scores = cross_val_score(self.ensemble_model, X_scaled, y, cv=min(5, len(X)//4))
            cv_mean = cv_scores.mean()
            cv_std = cv_scores.std()
            
            # Entrenar modelos individuales para comparación
            individual_scores = {}
            models = [
                ('RandomForest', self.rf_model),
                ('ExtraTrees', self.et_model),
                ('GradientBoosting', self.gb_model),
                ('SVM', self.svm_model),
                ('NeuralNetwork', self.nn_model),
                ('LogisticRegression', self.lr_model),
                ('NaiveBayes', self.nb_model)
            ]
            
            for name, model in models:
                try:
                    model.fit(X_train, y_train)
                    score = model.score(X_test, y_test)
                    individual_scores[name] = score
                except Exception as e:
                    individual_scores[name] = 0.0
                    print(f"⚠️ Error entrenando {name}: {e}")
            
            # Importancia de características
            if hasattr(self.rf_model, 'feature_importances_'):
                feature_importance = self.rf_model.feature_importances_
                self.feature_importance = {
                    f'feature_{i}': importance 
                    for i, importance in enumerate(feature_importance)
                }
            
            self.is_trained = True
            
            # Guardar historial
            training_info = {
                'timestamp': str(Path().cwd()),
                'samples': len(training_data),
                'accuracy': accuracy,
                'cv_mean': cv_mean,
                'cv_std': cv_std,
                'features_count': X_scaled.shape[1],
                'classes': list(self.reverse_label_encoder.values()),
                'individual_scores': individual_scores,
                'feature_importance': self.feature_importance
            }
            self.training_history.append(training_info)
            
            print(f"✅ Entrenamiento completado!")
            print(f"📊 Precisión: {accuracy:.3f}")
            print(f"📊 Validación cruzada: {cv_mean:.3f} (±{cv_std:.3f})")
            
            return {
                'success': True,
                'accuracy': accuracy,
                'cv_accuracy_mean': cv_mean,
                'cv_accuracy_std': cv_std,
                'training_samples': len(training_data),
                'features_count': X_scaled.shape[1],
                'classes': list(self.reverse_label_encoder.values()),
                'individual_model_scores': individual_scores,
                'ensemble_improvement': accuracy - max(individual_scores.values()) if individual_scores else 0,
                'feature_importance': self.feature_importance
            }
            
        except Exception as e:
            self.logger.error(f"Error en entrenamiento ultra-avanzado: {e}")
            return {
                'success': False,
                'error': str(e),
                'training_samples': len(training_data)
            }
    
    def predict(self, content: str) -> Dict:
        """Predecir con confianza ultra-alta"""
        if not self.is_trained:
            return {
                'success': False,
                'error': 'Modelo no entrenado'
            }
        
        try:
            features = self.extract_ultimate_features(content).reshape(1, -1)
            features_scaled = self.scaler.transform(features)
            
            # Aplicar selección de características si se usó
            if hasattr(self.feature_selector, 'transform'):
                features_scaled = self.feature_selector.transform(features_scaled)
            
            # Predicción del ensemble
            prediction = self.ensemble_model.predict(features_scaled)[0]
            probabilities = self.ensemble_model.predict_proba(features_scaled)[0]
            
            predicted_type = self.reverse_label_encoder[prediction]
            confidence = max(probabilities)
            
            # Predicciones individuales
            individual_predictions = {}
            models = [
                ('RandomForest', self.rf_model),
                ('ExtraTrees', self.et_model),
                ('GradientBoosting', self.gb_model),
                ('SVM', self.svm_model),
                ('NeuralNetwork', self.nn_model),
                ('LogisticRegression', self.lr_model),
                ('NaiveBayes', self.nb_model)
            ]
            
            for name, model in models:
                try:
                    pred = model.predict(features_scaled)[0]
                    individual_predictions[name] = self.reverse_label_encoder[pred]
                except:
                    individual_predictions[name] = 'ERROR'
            
            # Análisis de consenso
            consensus_count = sum(1 for pred in individual_predictions.values() 
                                if pred == predicted_type)
            consensus_ratio = consensus_count / len(individual_predictions)
            
            # Análisis de confianza
            confidence_level = "HIGH" if confidence > 0.8 else "MEDIUM" if confidence > 0.6 else "LOW"
            
            return {
                'success': True,
                'predicted_type': predicted_type,
                'confidence': confidence,
                'confidence_level': confidence_level,
                'consensus_ratio': consensus_ratio,
                'probabilities': {
                    self.reverse_label_encoder[i]: prob 
                    for i, prob in enumerate(probabilities)
                },
                'individual_predictions': individual_predictions,
                'features_extracted': len(features[0]),
                'model_version': 'Ultimate v3.0'
            }
            
        except Exception as e:
            self.logger.error(f"Error en predicción ultra-avanzada: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_model_info(self) -> Dict:
        """Información completa del modelo"""
        return {
            'is_trained': self.is_trained,
            'model_type': 'Ultimate Ensemble Classifier v3.0',
            'algorithms': ['RandomForest', 'ExtraTrees', 'GradientBoosting', 'SVM', 'NeuralNetwork', 'LogisticRegression', 'NaiveBayes'],
            'classes': list(self.reverse_label_encoder.values()) if self.is_trained else [],
            'training_history': self.training_history,
            'feature_count': len(self.extract_ultimate_features("test")) if self.is_trained else 0,
            'feature_importance': self.feature_importance,
            'preprocessing': ['RobustScaler', 'SelectKBest'],
            'optimization': 'GridSearchCV'
        }
    
    def save_model(self, filepath: str):
        """Guardar modelo ultra-avanzado"""
        model_data = {
            'ensemble_model': self.ensemble_model,
            'scaler': self.scaler,
            'feature_selector': self.feature_selector,
            'label_encoder': self.label_encoder,
            'reverse_label_encoder': self.reverse_label_encoder,
            'is_trained': self.is_trained,
            'training_history': self.training_history,
            'feature_importance': self.feature_importance,
            'version': '3.0'
        }
        joblib.dump(model_data, filepath)
        
    def load_model(self, filepath: str):
        """Cargar modelo ultra-avanzado"""
        if Path(filepath).exists():
            model_data = joblib.load(filepath)
            self.ensemble_model = model_data['ensemble_model']
            self.scaler = model_data['scaler']
            self.feature_selector = model_data.get('feature_selector', SelectKBest())
            self.label_encoder = model_data['label_encoder']
            self.reverse_label_encoder = model_data['reverse_label_encoder']
            self.is_trained = model_data['is_trained']
            self.training_history = model_data.get('training_history', [])
            self.feature_importance = model_data.get('feature_importance', {})