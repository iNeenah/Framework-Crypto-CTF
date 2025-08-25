#!/usr/bin/env python3
"""
Clasificador avanzado de desafíos de criptografía usando Machine Learning
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path
import re
import math

class AdvancedChallengeClassifier:
    """Clasificador ML avanzado para tipos de desafíos de criptografía"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Ensemble de múltiples algoritmos
        self.rf_model = RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            max_depth=15,
            min_samples_split=2,
            min_samples_leaf=1
        )
        
        self.gb_model = GradientBoostingClassifier(
            n_estimators=100,
            random_state=42,
            max_depth=10,
            learning_rate=0.1
        )
        
        self.svm_model = SVC(
            kernel='rbf',
            probability=True,
            random_state=42
        )
        
        self.nn_model = MLPClassifier(
            hidden_layer_sizes=(100, 50),
            random_state=42,
            max_iter=1000
        )
        
        # Ensemble voting classifier
        self.ensemble_model = VotingClassifier(
            estimators=[
                ('rf', self.rf_model),
                ('gb', self.gb_model),
                ('svm', self.svm_model),
                ('nn', self.nn_model)
            ],
            voting='soft'
        )
        
        self.scaler = StandardScaler()
        self.feature_names = []
        self.label_encoder = {}
        self.reverse_label_encoder = {}
        self.is_trained = False
        self.training_history = []
        
    def calculate_entropy(self, text: str) -> float:
        """Calcular entropía de Shannon"""
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
    
    def extract_advanced_features(self, content: str) -> np.ndarray:
        """Extraer características avanzadas del contenido"""
        features = []
        content_lower = content.lower()
        
        # === CARACTERÍSTICAS BÁSICAS ===
        features.append(len(content))  # Longitud total
        features.append(len(content.split('\n')))  # Número de líneas
        features.append(len(content.split()))  # Número de palabras
        features.append(self.calculate_entropy(content))  # Entropía
        
        # === RATIOS DE CARACTERES ===
        total_chars = len(content) if content else 1
        features.append(sum(1 for c in content if c.isdigit()) / total_chars)  # Dígitos
        features.append(sum(1 for c in content if c.isalpha()) / total_chars)  # Letras
        features.append(sum(1 for c in content if c.isupper()) / total_chars)  # Mayúsculas
        features.append(sum(1 for c in content if c.islower()) / total_chars)  # Minúsculas
        features.append(sum(1 for c in content if c in '0123456789abcdefABCDEF') / total_chars)  # Hex
        
        # === PATRONES ESPECÍFICOS ===
        # Patrones hexadecimales largos
        hex_matches = re.findall(r'[0-9a-fA-F]{16,}', content)
        features.append(len(hex_matches))
        features.append(sum(len(match) for match in hex_matches))
        
        # Patrones Base64
        b64_matches = re.findall(r'[A-Za-z0-9+/]{20,}={0,2}', content)
        features.append(len(b64_matches))
        
        # Números grandes (posibles parámetros RSA)
        big_numbers = re.findall(r'\d{50,}', content)
        features.append(len(big_numbers))
        
        # === PALABRAS CLAVE ESPECÍFICAS POR CATEGORÍA ===
        crypto_keywords = {
            'rsa': ['rsa', 'modulus', 'exponent', 'factorization', 'prime', 'public key', 'private key'],
            'aes': ['aes', 'rijndael', 'block cipher', 'iv', 'cbc', 'ecb', 'gcm'],
            'stream': ['chacha', 'salsa', 'stream', 'nonce', 'keystream', 'rc4'],
            'hash': ['hash', 'md5', 'sha', 'digest', 'collision', 'rainbow'],
            'ecc': ['elliptic', 'curve', 'ecdsa', 'point', 'secp256k1'],
            'classical': ['caesar', 'vigenere', 'substitution', 'transposition', 'shift', 'rot'],
            'base64': ['base64', 'b64', 'encoding', 'decode'],
            'xor': ['xor', 'exclusive', 'otp', 'one time pad'],
            'ctf': ['flag', 'ctf', 'htb', 'challenge', 'crypto']
        }
        
        for category, keywords in crypto_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            features.append(score)
        
        # === CARACTERÍSTICAS ESTRUCTURALES ===
        # Presencia de parámetros típicos
        features.append(1 if re.search(r'[nec]\s*=\s*\d+', content) else 0)  # Parámetros RSA
        features.append(1 if 'known plaintext' in content_lower else 0)  # Known plaintext
        features.append(1 if 'nonce' in content_lower and 'reuse' in content_lower else 0)  # Nonce reuse
        features.append(1 if re.search(r'flag\{|htb\{|ctf\{', content_lower) else 0)  # Flag format
        
        # === ANÁLISIS DE DISTRIBUCIÓN ===
        # Distribución de caracteres únicos
        unique_chars = len(set(content))
        features.append(unique_chars)
        features.append(unique_chars / total_chars if total_chars > 0 else 0)
        
        # Longitud promedio de palabras
        words = content.split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        features.append(avg_word_length)
        
        # === CARACTERÍSTICAS AVANZADAS ===
        # Detección de patrones repetitivos
        lines = content.split('\n')
        similar_lines = sum(1 for i, line1 in enumerate(lines) 
                          for line2 in lines[i+1:] 
                          if len(line1) > 10 and line1 == line2)
        features.append(similar_lines)
        
        # Presencia de datos estructurados
        features.append(1 if ':' in content and '=' in content else 0)
        
        return np.array(features)
    
    def prepare_training_data(self, training_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Preparar datos de entrenamiento con características avanzadas"""
        X = []
        y = []
        
        for sample in training_data:
            if 'features' in sample and 'metadata' in sample:
                # Usar datos del dataset avanzado
                content = sample.get('content_preview', '')
                challenge_type = sample['metadata']['challenge_type']
            else:
                # Formato legacy
                content = sample.get('content', '')
                challenge_type = sample.get('type', 'UNKNOWN')
            
            features = self.extract_advanced_features(content)
            X.append(features)
            y.append(challenge_type)
        
        # Crear codificación de etiquetas
        unique_labels = list(set(y))
        self.label_encoder = {label: idx for idx, label in enumerate(unique_labels)}
        self.reverse_label_encoder = {idx: label for label, idx in self.label_encoder.items()}
        
        # Convertir etiquetas a números
        y_encoded = [self.label_encoder[label] for label in y]
        
        return np.array(X), np.array(y_encoded)
    
    def train(self, training_data: List[Dict]) -> Dict:
        """Entrenar el modelo con validación cruzada"""
        try:
            if len(training_data) < 5:
                return {
                    'success': False,
                    'error': 'Insuficientes datos de entrenamiento (mínimo 5)',
                    'training_samples': len(training_data)
                }
            
            X, y = self.prepare_training_data(training_data)
            
            # Normalizar características
            X_scaled = self.scaler.fit_transform(X)
            
            # Dividir datos
            if len(X) > 20:
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y, test_size=0.2, random_state=42, stratify=y
                )
            elif len(X) > 10:
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y, test_size=0.3, random_state=42
                )
            else:
                X_train, X_test, y_train, y_test = X_scaled, X_scaled, y, y
            
            # Entrenar ensemble
            self.ensemble_model.fit(X_train, y_train)
            
            # Evaluar
            y_pred = self.ensemble_model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Validación cruzada
            cv_scores = cross_val_score(self.ensemble_model, X_scaled, y, cv=min(5, len(X)))
            cv_mean = cv_scores.mean()
            cv_std = cv_scores.std()
            
            # Entrenar modelos individuales para comparación
            individual_scores = {}
            for name, model in [('RandomForest', self.rf_model), 
                              ('GradientBoosting', self.gb_model),
                              ('SVM', self.svm_model),
                              ('NeuralNetwork', self.nn_model)]:
                try:
                    model.fit(X_train, y_train)
                    score = model.score(X_test, y_test)
                    individual_scores[name] = score
                except:
                    individual_scores[name] = 0.0
            
            self.is_trained = True
            
            # Guardar historial de entrenamiento
            training_info = {
                'timestamp': str(Path().cwd()),
                'samples': len(training_data),
                'accuracy': accuracy,
                'cv_mean': cv_mean,
                'cv_std': cv_std,
                'features_count': X.shape[1],
                'classes': list(self.reverse_label_encoder.values()),
                'individual_scores': individual_scores
            }
            self.training_history.append(training_info)
            
            return {
                'success': True,
                'accuracy': accuracy,
                'cv_accuracy_mean': cv_mean,
                'cv_accuracy_std': cv_std,
                'training_samples': len(training_data),
                'features_count': X.shape[1],
                'classes': list(self.reverse_label_encoder.values()),
                'individual_model_scores': individual_scores,
                'ensemble_improvement': max(individual_scores.values()) - accuracy if individual_scores else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error en entrenamiento avanzado: {e}")
            return {
                'success': False,
                'error': str(e),
                'training_samples': len(training_data)
            }
    
    def predict(self, content: str) -> Dict:
        """Predecir tipo de desafío con confianza mejorada"""
        if not self.is_trained:
            return {
                'success': False,
                'error': 'Modelo no entrenado'
            }
        
        try:
            features = self.extract_advanced_features(content).reshape(1, -1)
            features_scaled = self.scaler.transform(features)
            
            # Predicción del ensemble
            prediction = self.ensemble_model.predict(features_scaled)[0]
            probabilities = self.ensemble_model.predict_proba(features_scaled)[0]
            
            predicted_type = self.reverse_label_encoder[prediction]
            confidence = max(probabilities)
            
            # Predicciones individuales para análisis
            individual_predictions = {}
            for name, model in [('RandomForest', self.rf_model), 
                              ('GradientBoosting', self.gb_model),
                              ('SVM', self.svm_model),
                              ('NeuralNetwork', self.nn_model)]:
                try:
                    pred = model.predict(features_scaled)[0]
                    individual_predictions[name] = self.reverse_label_encoder[pred]
                except:
                    individual_predictions[name] = 'ERROR'
            
            # Análisis de consenso
            consensus_count = sum(1 for pred in individual_predictions.values() 
                                if pred == predicted_type)
            consensus_ratio = consensus_count / len(individual_predictions)
            
            return {
                'success': True,
                'predicted_type': predicted_type,
                'confidence': confidence,
                'consensus_ratio': consensus_ratio,
                'probabilities': {
                    self.reverse_label_encoder[i]: prob 
                    for i, prob in enumerate(probabilities)
                },
                'individual_predictions': individual_predictions,
                'features_extracted': len(features[0])
            }
            
        except Exception as e:
            self.logger.error(f"Error en predicción avanzada: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_model_info(self) -> Dict:
        """Obtener información detallada del modelo"""
        return {
            'is_trained': self.is_trained,
            'model_type': 'Advanced Ensemble Classifier',
            'algorithms': ['RandomForest', 'GradientBoosting', 'SVM', 'NeuralNetwork'],
            'classes': list(self.reverse_label_encoder.values()) if self.is_trained else [],
            'training_history': self.training_history,
            'feature_count': len(self.extract_advanced_features("test")) if self.is_trained else 0
        }
    
    def save_model(self, filepath: str):
        """Guardar modelo entrenado completo"""
        model_data = {
            'ensemble_model': self.ensemble_model,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'reverse_label_encoder': self.reverse_label_encoder,
            'is_trained': self.is_trained,
            'training_history': self.training_history
        }
        joblib.dump(model_data, filepath)
        
    def load_model(self, filepath: str):
        """Cargar modelo entrenado completo"""
        if Path(filepath).exists():
            model_data = joblib.load(filepath)
            self.ensemble_model = model_data['ensemble_model']
            self.scaler = model_data['scaler']
            self.label_encoder = model_data['label_encoder']
            self.reverse_label_encoder = model_data['reverse_label_encoder']
            self.is_trained = model_data['is_trained']
            self.training_history = model_data.get('training_history', [])