"""
Challenge Classifier - Clasificador de tipos de desafío usando ML
"""

import pickle
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
import joblib

from ...models.data import ChallengeData, ChallengeType
from ..feature_extractor import FeatureExtractor
from ...utils.logging import get_logger


class ChallengeClassifier:
    """Clasificador de tipos de desafío CTF usando Random Forest"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.logger = get_logger(__name__)
        self.feature_extractor = FeatureExtractor()
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.label_encoder = {}
        self.reverse_label_encoder = {}
        self.feature_names = []
        self.is_trained = False
        
        # Cargar modelo si existe
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
    
    def prepare_training_data(self, challenges: List[Tuple[ChallengeData, ChallengeType]]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preparar datos de entrenamiento.
        
        Args:
            challenges: Lista de tuplas (ChallengeData, ChallengeType)
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: Características y etiquetas
        """
        self.logger.info(f"Preparando datos de entrenamiento con {len(challenges)} ejemplos")
        
        # Extraer características
        features_list = []
        labels = []
        
        for challenge_data, challenge_type in challenges:
            try:
                features = self.feature_extractor.extract_features(challenge_data)
                features = self.feature_extractor.normalize_features(features)
                features_list.append(features)
                labels.append(challenge_type.value)
            except Exception as e:
                self.logger.warning(f"Error procesando desafío {challenge_data.id}: {e}")
                continue
        
        if not features_list:
            raise ValueError("No se pudieron extraer características de ningún desafío")
        
        # Obtener nombres de características consistentes
        self.feature_names = self.feature_extractor.get_feature_names()
        
        # Convertir a arrays numpy
        X = np.zeros((len(features_list), len(self.feature_names)))
        for i, features in enumerate(features_list):
            for j, feature_name in enumerate(self.feature_names):
                X[i, j] = features.get(feature_name, 0.0)
        
        # Codificar etiquetas
        unique_labels = sorted(set(labels))
        self.label_encoder = {label: i for i, label in enumerate(unique_labels)}
        self.reverse_label_encoder = {i: label for label, i in self.label_encoder.items()}
        
        y = np.array([self.label_encoder[label] for label in labels])
        
        self.logger.info(f"Datos preparados: {X.shape[0]} ejemplos, {X.shape[1]} características")
        self.logger.info(f"Clases: {list(self.label_encoder.keys())}")
        
        return X, y
    
    def train(self, challenges: List[Tuple[ChallengeData, ChallengeType]], 
              test_size: float = 0.2, validate: bool = True) -> Dict[str, Any]:
        """
        Entrenar el clasificador.
        
        Args:
            challenges: Datos de entrenamiento
            test_size: Proporción de datos para test
            validate: Si realizar validación cruzada
            
        Returns:
            Dict[str, Any]: Métricas de entrenamiento
        """
        self.logger.info("Iniciando entrenamiento del clasificador")
        
        # Preparar datos
        X, y = self.prepare_training_data(challenges)
        
        # Dividir en entrenamiento y test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Escalar características
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Entrenar modelo
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Evaluar modelo
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        self.logger.info(f"Precisión en entrenamiento: {train_score:.3f}")
        self.logger.info(f"Precisión en test: {test_score:.3f}")
        
        # Predicciones para métricas detalladas
        y_pred = self.model.predict(X_test_scaled)
        
        # Reporte de clasificación
        target_names = [self.reverse_label_encoder[i] for i in range(len(self.reverse_label_encoder))]
        class_report = classification_report(y_test, y_pred, target_names=target_names, output_dict=True)
        
        # Importancia de características
        feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
        top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
        
        self.logger.info("Top 10 características más importantes:")
        for feature, importance in top_features:
            self.logger.info(f"  {feature}: {importance:.3f}")
        
        metrics = {
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'classification_report': class_report,
            'feature_importance': feature_importance,
            'top_features': top_features,
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
        }
        
        # Validación cruzada
        if validate and len(challenges) > 10:
            cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
            metrics['cv_mean'] = cv_scores.mean()
            metrics['cv_std'] = cv_scores.std()
            self.logger.info(f"Validación cruzada: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
        
        return metrics
    
    def predict(self, challenge_data: ChallengeData) -> Tuple[ChallengeType, float]:
        """
        Predecir tipo de desafío.
        
        Args:
            challenge_data: Datos del desafío
            
        Returns:
            Tuple[ChallengeType, float]: Tipo predicho y confianza
        """
        if not self.is_trained:
            raise ValueError("El modelo no ha sido entrenado")
        
        # Extraer características
        features = self.feature_extractor.extract_features(challenge_data)
        features = self.feature_extractor.normalize_features(features)
        
        # Convertir a array numpy
        X = np.zeros((1, len(self.feature_names)))
        for i, feature_name in enumerate(self.feature_names):
            X[0, i] = features.get(feature_name, 0.0)
        
        # Escalar
        X_scaled = self.scaler.transform(X)
        
        # Predecir
        prediction = self.model.predict(X_scaled)[0]
        probabilities = self.model.predict_proba(X_scaled)[0]
        
        # Convertir a tipo de desafío
        predicted_type_str = self.reverse_label_encoder[prediction]
        predicted_type = ChallengeType(predicted_type_str)
        confidence = probabilities[prediction]
        
        return predicted_type, confidence
    
    def predict_proba(self, challenge_data: ChallengeData) -> Dict[ChallengeType, float]:
        """
        Obtener probabilidades para todos los tipos.
        
        Args:
            challenge_data: Datos del desafío
            
        Returns:
            Dict[ChallengeType, float]: Probabilidades por tipo
        """
        if not self.is_trained:
            raise ValueError("El modelo no ha sido entrenado")
        
        # Extraer características
        features = self.feature_extractor.extract_features(challenge_data)
        features = self.feature_extractor.normalize_features(features)
        
        # Convertir a array numpy
        X = np.zeros((1, len(self.feature_names)))
        for i, feature_name in enumerate(self.feature_names):
            X[0, i] = features.get(feature_name, 0.0)
        
        # Escalar
        X_scaled = self.scaler.transform(X)
        
        # Obtener probabilidades
        probabilities = self.model.predict_proba(X_scaled)[0]
        
        # Convertir a diccionario
        result = {}
        for i, prob in enumerate(probabilities):
            type_str = self.reverse_label_encoder[i]
            challenge_type = ChallengeType(type_str)
            result[challenge_type] = prob
        
        return result
    
    def save_model(self, model_path: str) -> None:
        """Guardar modelo entrenado"""
        if not self.is_trained:
            raise ValueError("No hay modelo entrenado para guardar")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'reverse_label_encoder': self.reverse_label_encoder,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained
        }
        
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model_data, model_path)
        self.logger.info(f"Modelo guardado en: {model_path}")
    
    def load_model(self, model_path: str) -> None:
        """Cargar modelo entrenado"""
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Archivo de modelo no encontrado: {model_path}")
        
        model_data = joblib.load(model_path)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.label_encoder = model_data['label_encoder']
        self.reverse_label_encoder = model_data['reverse_label_encoder']
        self.feature_names = model_data['feature_names']
        self.is_trained = model_data['is_trained']
        
        self.logger.info(f"Modelo cargado desde: {model_path}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Obtener información del modelo"""
        if not self.is_trained:
            return {'trained': False}
        
        return {
            'trained': True,
            'n_features': len(self.feature_names),
            'n_classes': len(self.label_encoder),
            'classes': list(self.label_encoder.keys()),
            'model_type': 'RandomForestClassifier',
            'n_estimators': self.model.n_estimators,
            'max_depth': self.model.max_depth
        }
    
    def explain_prediction(self, challenge_data: ChallengeData, top_n: int = 5) -> Dict[str, Any]:
        """
        Explicar una predicción mostrando las características más importantes.
        
        Args:
            challenge_data: Datos del desafío
            top_n: Número de características principales a mostrar
            
        Returns:
            Dict[str, Any]: Explicación de la predicción
        """
        if not self.is_trained:
            raise ValueError("El modelo no ha sido entrenado")
        
        # Hacer predicción
        predicted_type, confidence = self.predict(challenge_data)
        probabilities = self.predict_proba(challenge_data)
        
        # Extraer características
        features = self.feature_extractor.extract_features(challenge_data)
        features = self.feature_extractor.normalize_features(features)
        
        # Obtener importancia de características para esta predicción
        feature_values = []
        for feature_name in self.feature_names:
            value = features.get(feature_name, 0.0)
            importance = self.model.feature_importances_[self.feature_names.index(feature_name)]
            contribution = value * importance
            feature_values.append((feature_name, value, importance, contribution))
        
        # Ordenar por contribución
        feature_values.sort(key=lambda x: abs(x[3]), reverse=True)
        top_features = feature_values[:top_n]
        
        return {
            'predicted_type': predicted_type.value,
            'confidence': confidence,
            'all_probabilities': {t.value: p for t, p in probabilities.items()},
            'top_contributing_features': [
                {
                    'name': name,
                    'value': value,
                    'importance': importance,
                    'contribution': contribution
                }
                for name, value, importance, contribution in top_features
            ],
            'challenge_features': features
        }