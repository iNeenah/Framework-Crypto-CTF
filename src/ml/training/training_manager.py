"""
Training Manager - Gestor de entrenamiento para modelos ML
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from ...models.data import ChallengeData, ChallengeType, SolutionResult
from ..models.challenge_classifier import ChallengeClassifier
from ..models.advanced_classifier import AdvancedChallengeClassifier
from ...utils.logging import get_logger
from ...utils.config import config


class TrainingManager:
    """Gestor de entrenamiento y almacenamiento de patrones"""
    
    def __init__(self, data_dir: str = "data/ml"):
        self.logger = get_logger(__name__)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivos de datos
        self.challenges_file = self.data_dir / "challenges.json"
        self.solutions_file = self.data_dir / "solutions.json"
        self.patterns_file = self.data_dir / "patterns.json"
        self.model_file = self.data_dir / "classifier_model.joblib"
        
        # Datos en memoria
        self.stored_challenges: List[Dict[str, Any]] = []
        self.stored_solutions: List[Dict[str, Any]] = []
        self.patterns: Dict[str, Any] = {}
        
        # Cargar datos existentes
        self._load_data()
        
        # Clasificador
        self.classifier = ChallengeClassifier(
            model_path=str(self.model_file) if self.model_file.exists() else None
        )
    
    def _load_data(self) -> None:
        """Cargar datos almacenados"""
        try:
            if self.challenges_file.exists():
                with open(self.challenges_file, 'r', encoding='utf-8') as f:
                    self.stored_challenges = json.load(f)
                self.logger.info(f"Cargados {len(self.stored_challenges)} desafíos históricos")
            
            if self.solutions_file.exists():
                with open(self.solutions_file, 'r', encoding='utf-8') as f:
                    self.stored_solutions = json.load(f)
                self.logger.info(f"Cargadas {len(self.stored_solutions)} soluciones históricas")
            
            if self.patterns_file.exists():
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    self.patterns = json.load(f)
                self.logger.info(f"Cargados patrones de {len(self.patterns)} tipos de desafío")
        
        except Exception as e:
            self.logger.error(f"Error cargando datos: {e}")
    
    def _save_data(self) -> None:
        """Guardar datos en archivos"""
        try:
            with open(self.challenges_file, 'w', encoding='utf-8') as f:
                json.dump(self.stored_challenges, f, indent=2, ensure_ascii=False)
            
            with open(self.solutions_file, 'w', encoding='utf-8') as f:
                json.dump(self.stored_solutions, f, indent=2, ensure_ascii=False)
            
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, indent=2, ensure_ascii=False)
            
            self.logger.debug("Datos guardados exitosamente")
        
        except Exception as e:
            self.logger.error(f"Error guardando datos: {e}")
    
    def store_challenge(self, challenge_data: ChallengeData, actual_type: Optional[ChallengeType] = None) -> None:
        """
        Almacenar un desafío para entrenamiento.
        
        Args:
            challenge_data: Datos del desafío
            actual_type: Tipo real del desafío (si se conoce)
        """
        challenge_dict = {
            'id': challenge_data.id,
            'name': challenge_data.name,
            'description': challenge_data.description,
            'challenge_type': actual_type.value if actual_type else challenge_data.challenge_type.value,
            'tags': challenge_data.tags,
            'metadata': challenge_data.metadata,
            'timestamp': datetime.now().isoformat(),
            'files': [
                {
                    'path': str(f.path),
                    'size': f.size,
                    'mime_type': f.mime_type,
                    'hash_md5': f.hash_md5,
                    'hash_sha256': f.hash_sha256
                }
                for f in challenge_data.files
            ]
        }
        
        # Evitar duplicados
        existing_ids = {c['id'] for c in self.stored_challenges}
        if challenge_data.id not in existing_ids:
            self.stored_challenges.append(challenge_dict)
            self._save_data()
            self.logger.info(f"Desafío almacenado: {challenge_data.id}")
    
    def store_solution(self, challenge_id: str, solution_result: SolutionResult) -> None:
        """
        Almacenar resultado de solución.
        
        Args:
            challenge_id: ID del desafío
            solution_result: Resultado de la solución
        """
        solution_dict = {
            'challenge_id': challenge_id,
            'success': solution_result.success,
            'flag': solution_result.flag,
            'method_used': solution_result.method_used,
            'confidence': solution_result.confidence,
            'execution_time': solution_result.execution_time,
            'plugin_name': solution_result.plugin_name,
            'error_message': solution_result.error_message,
            'timestamp': datetime.now().isoformat(),
            'details': solution_result.details
        }
        
        self.stored_solutions.append(solution_dict)
        self._save_data()
        self.logger.info(f"Solución almacenada para desafío: {challenge_id}")
    
    def update_patterns(self, challenge_type: ChallengeType, successful_methods: List[str]) -> None:
        """
        Actualizar patrones de éxito para un tipo de desafío.
        
        Args:
            challenge_type: Tipo de desafío
            successful_methods: Métodos que fueron exitosos
        """
        type_key = challenge_type.value
        
        if type_key not in self.patterns:
            self.patterns[type_key] = {
                'successful_methods': {},
                'total_attempts': 0,
                'success_rate': 0.0,
                'last_updated': datetime.now().isoformat()
            }
        
        pattern = self.patterns[type_key]
        
        # Actualizar conteos de métodos exitosos
        for method in successful_methods:
            if method not in pattern['successful_methods']:
                pattern['successful_methods'][method] = 0
            pattern['successful_methods'][method] += 1
        
        pattern['total_attempts'] += 1
        pattern['last_updated'] = datetime.now().isoformat()
        
        # Calcular tasa de éxito
        successful_solutions = sum(
            1 for s in self.stored_solutions 
            if s['success'] and self._get_challenge_type(s['challenge_id']) == challenge_type
        )
        total_solutions = sum(
            1 for s in self.stored_solutions 
            if self._get_challenge_type(s['challenge_id']) == challenge_type
        )
        
        if total_solutions > 0:
            pattern['success_rate'] = successful_solutions / total_solutions
        
        self._save_data()
        self.logger.info(f"Patrones actualizados para {type_key}")
    
    def _get_challenge_type(self, challenge_id: str) -> Optional[ChallengeType]:
        """Obtener tipo de desafío por ID"""
        for challenge in self.stored_challenges:
            if challenge['id'] == challenge_id:
                return ChallengeType(challenge['challenge_type'])
        return None
    
    def get_training_data(self) -> List[Tuple[ChallengeData, ChallengeType]]:
        """
        Obtener datos de entrenamiento.
        
        Returns:
            List[Tuple[ChallengeData, ChallengeType]]: Datos para entrenamiento
        """
        training_data = []
        
        for challenge_dict in self.stored_challenges:
            try:
                # Reconstruir ChallengeData (simplificado para ML)
                challenge_data = ChallengeData(
                    id=challenge_dict['id'],
                    name=challenge_dict['name'],
                    description=challenge_dict.get('description', ''),
                    challenge_type=ChallengeType(challenge_dict['challenge_type']),
                    tags=challenge_dict.get('tags', []),
                    metadata=challenge_dict.get('metadata', {})
                )
                
                # Tipo real
                actual_type = ChallengeType(challenge_dict['challenge_type'])
                
                training_data.append((challenge_data, actual_type))
                
            except Exception as e:
                self.logger.warning(f"Error procesando desafío {challenge_dict.get('id', 'unknown')}: {e}")
                continue
        
        return training_data
    
    def train_classifier(self, min_examples: int = 10) -> Dict[str, Any]:
        """
        Entrenar el clasificador con datos almacenados.
        
        Args:
            min_examples: Número mínimo de ejemplos para entrenar
            
        Returns:
            Dict[str, Any]: Métricas de entrenamiento
        """
        training_data = self.get_training_data()
        
        if len(training_data) < min_examples:
            raise ValueError(f"Insuficientes datos de entrenamiento: {len(training_data)} < {min_examples}")
        
        self.logger.info(f"Entrenando clasificador con {len(training_data)} ejemplos")
        
        # Entrenar modelo
        metrics = self.classifier.train(training_data)
        
        # Guardar modelo
        self.classifier.save_model(str(self.model_file))
        
        # Actualizar estadísticas
        training_stats = {
            'training_date': datetime.now().isoformat(),
            'n_examples': len(training_data),
            'metrics': metrics,
            'model_info': self.classifier.get_model_info()
        }
        
        # Guardar estadísticas
        stats_file = self.data_dir / "training_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(training_stats, f, indent=2, ensure_ascii=False)
        
        self.logger.info("Entrenamiento completado exitosamente")
        return metrics
    
    def predict_challenge_type(self, challenge_data: ChallengeData) -> Tuple[ChallengeType, float, Dict[str, Any]]:
        """
        Predecir tipo de desafío usando el clasificador entrenado.
        
        Args:
            challenge_data: Datos del desafío
            
        Returns:
            Tuple[ChallengeType, float, Dict[str, Any]]: Tipo predicho, confianza y explicación
        """
        if not self.classifier.is_trained:
            # Si no hay modelo entrenado, usar heurísticas básicas
            return self._fallback_prediction(challenge_data)
        
        predicted_type, confidence = self.classifier.predict(challenge_data)
        explanation = self.classifier.explain_prediction(challenge_data)
        
        return predicted_type, confidence, explanation
    
    def _fallback_prediction(self, challenge_data: ChallengeData) -> Tuple[ChallengeType, float, Dict[str, Any]]:
        """Predicción de respaldo usando heurísticas simples"""
        # Usar el tipo detectado por el FileAnalyzer si está disponible
        if challenge_data.challenge_type != ChallengeType.UNKNOWN:
            return challenge_data.challenge_type, 0.5, {'method': 'file_analyzer_heuristic'}
        
        # Heurísticas básicas basadas en nombres y tags
        name_lower = challenge_data.name.lower()
        tags_lower = [tag.lower() for tag in challenge_data.tags]
        all_text = name_lower + ' ' + ' '.join(tags_lower)
        
        if any(word in all_text for word in ['rsa', 'factorization', 'modulus']):
            return ChallengeType.RSA, 0.3, {'method': 'name_heuristic'}
        elif any(word in all_text for word in ['caesar', 'vigenere', 'cipher', 'crypto']):
            return ChallengeType.BASIC_CRYPTO, 0.3, {'method': 'name_heuristic'}
        elif any(word in all_text for word in ['network', 'socket', 'netcat', 'server']):
            return ChallengeType.NETWORK, 0.3, {'method': 'name_heuristic'}
        elif any(word in all_text for word in ['elliptic', 'curve', 'ecc']):
            return ChallengeType.ELLIPTIC_CURVE, 0.3, {'method': 'name_heuristic'}
        
        return ChallengeType.UNKNOWN, 0.1, {'method': 'fallback'}
    
    def get_success_patterns(self, challenge_type: ChallengeType) -> Dict[str, Any]:
        """
        Obtener patrones de éxito para un tipo de desafío.
        
        Args:
            challenge_type: Tipo de desafío
            
        Returns:
            Dict[str, Any]: Patrones de éxito
        """
        type_key = challenge_type.value
        return self.patterns.get(type_key, {})
    
    def get_recommended_methods(self, challenge_type: ChallengeType, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Obtener métodos recomendados para un tipo de desafío.
        
        Args:
            challenge_type: Tipo de desafío
            top_n: Número de métodos a retornar
            
        Returns:
            List[Tuple[str, float]]: Lista de (método, probabilidad_éxito)
        """
        patterns = self.get_success_patterns(challenge_type)
        
        if not patterns or 'successful_methods' not in patterns:
            return []
        
        successful_methods = patterns['successful_methods']
        total_successes = sum(successful_methods.values())
        
        if total_successes == 0:
            return []
        
        # Calcular probabilidades
        method_probs = [
            (method, count / total_successes)
            for method, count in successful_methods.items()
        ]
        
        # Ordenar por probabilidad
        method_probs.sort(key=lambda x: x[1], reverse=True)
        
        return method_probs[:top_n]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema de ML"""
        stats = {
            'total_challenges': len(self.stored_challenges),
            'total_solutions': len(self.stored_solutions),
            'classifier_trained': self.classifier.is_trained,
            'patterns_count': len(self.patterns)
        }
        
        # Estadísticas por tipo
        type_stats = {}
        for challenge in self.stored_challenges:
            challenge_type = challenge['challenge_type']
            if challenge_type not in type_stats:
                type_stats[challenge_type] = 0
            type_stats[challenge_type] += 1
        
        stats['challenges_by_type'] = type_stats
        
        # Tasa de éxito general
        successful_solutions = sum(1 for s in self.stored_solutions if s['success'])
        if self.stored_solutions:
            stats['overall_success_rate'] = successful_solutions / len(self.stored_solutions)
        else:
            stats['overall_success_rate'] = 0.0
        
        # Información del modelo
        if self.classifier.is_trained:
            stats['model_info'] = self.classifier.get_model_info()
        
        return stats
    
    def export_training_data(self, output_file: str) -> None:
        """Exportar datos de entrenamiento a archivo"""
        training_data = self.get_training_data()
        
        export_data = []
        for challenge_data, challenge_type in training_data:
            export_data.append({
                'challenge': {
                    'id': challenge_data.id,
                    'name': challenge_data.name,
                    'description': challenge_data.description,
                    'tags': challenge_data.tags,
                    'metadata': challenge_data.metadata
                },
                'type': challenge_type.value
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Datos de entrenamiento exportados a: {output_file}")
    
    def clear_data(self, confirm: bool = False) -> None:
        """Limpiar todos los datos almacenados"""
        if not confirm:
            raise ValueError("Debe confirmar la limpieza de datos con confirm=True")
        
        self.stored_challenges.clear()
        self.stored_solutions.clear()
        self.patterns.clear()
        
        # Eliminar archivos
        for file_path in [self.challenges_file, self.solutions_file, self.patterns_file, self.model_file]:
            if file_path.exists():
                file_path.unlink()
        
        self.logger.warning("Todos los datos de ML han sido eliminados")