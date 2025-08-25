#!/usr/bin/env python3
"""
AUTO TRAIN FRAMEWORK - Entrenamiento Automático con IA
======================================================

Este script procesa automáticamente todos los desafíos en challenges/uploaded/
y entrena el framework con machine learning para mejorar continuamente.

Flujo:
1. Escanea challenges/uploaded/ en busca de nuevos desafíos
2. Los procesa con el framework completo (plugins + IA)
3. Almacena resultados para entrenamiento
4. Re-entrena el modelo de IA automáticamente
5. Mejora la precisión del framework continuamente

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

# Importar framework completo
from src.core.challenge_manager import ChallengeManager
from src.core.file_analyzer import FileAnalyzer
from src.core.plugin_manager import plugin_manager
from src.ml.training.training_manager import TrainingManager
from src.ml.models.challenge_classifier import ChallengeClassifier
from src.models.data import ChallengeData, ChallengeType, SolutionResult
from src.utils.logging import setup_logging, get_logger


class AutoTrainingFramework:
    """Framework de entrenamiento automático con IA"""
    
    def __init__(self):
        setup_logging(level='INFO')
        self.logger = get_logger(__name__)
        
        # Componentes principales
        self.challenge_manager = ChallengeManager()
        self.training_manager = TrainingManager()
        self.file_analyzer = FileAnalyzer()
        
        # Directorios
        self.uploaded_dir = Path("challenges/uploaded")
        self.processed_dir = Path("challenges/extracted")
        self.solved_dir = Path("challenges/solved")
        
        # Crear directorios si no existen
        for dir_path in [self.processed_dir, self.solved_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Estadísticas
        self.stats = {
            'total_processed': 0,
            'successfully_solved': 0,
            'failed_solutions': 0,
            'new_training_data': 0,
            'models_retrained': 0,
            'start_time': time.time()
        }
        
        # Control de procesamiento
        self.processed_files = self._load_processed_list()
        
        self.logger.info("🚀 Framework de Entrenamiento Automático iniciado")
    
    def _load_processed_list(self) -> set:
        """Cargar lista de archivos ya procesados"""
        processed_file = Path("data/ml/processed_files.json")
        if processed_file.exists():
            try:
                with open(processed_file, 'r') as f:
                    return set(json.load(f))
            except:
                pass
        return set()
    
    def _save_processed_list(self):
        """Guardar lista de archivos procesados"""
        processed_file = Path("data/ml/processed_files.json")
        processed_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(processed_file, 'w') as f:
            json.dump(list(self.processed_files), f, indent=2)
    
    def scan_for_new_challenges(self) -> List[Path]:
        """Escanear challenges/uploaded/ en busca de nuevos desafíos"""
        self.logger.info(f"🔍 Escaneando {self.uploaded_dir} en busca de nuevos desafíos...")
        
        new_challenges = []
        
        if not self.uploaded_dir.exists():
            self.logger.warning(f"Directorio {self.uploaded_dir} no existe")
            return new_challenges
        
        # Buscar archivos de texto (desafíos)
        for file_path in self.uploaded_dir.rglob("*.txt"):
            try:
                relative_path = str(file_path.relative_to(self.uploaded_dir.parent.parent))
            except ValueError:
                # Si no se puede calcular ruta relativa, usar la absoluta
                relative_path = str(file_path)
            
            if relative_path not in self.processed_files:
                new_challenges.append(file_path)
        
        # Buscar directorios con archivos (desafíos complejos)
        for dir_path in self.uploaded_dir.iterdir():
            if dir_path.is_dir() and not dir_path.name.startswith('.'):
                try:
                    relative_path = str(dir_path.relative_to(self.uploaded_dir.parent.parent))
                except ValueError:
                    relative_path = str(dir_path)
                
                if relative_path not in self.processed_files:
                    # Verificar si tiene archivos
                    if any(dir_path.iterdir()):
                        new_challenges.append(dir_path)
        
        self.logger.info(f"✅ Encontrados {len(new_challenges)} nuevos desafíos")
        return new_challenges
    
    def process_challenge(self, challenge_path: Path) -> Optional[Dict[str, Any]]:
        """Procesar un desafío individual con el framework completo"""
        self.logger.info(f"📝 Procesando: {challenge_path}")
        
        try:
            # Cargar desafío con el framework
            challenge_data = self.challenge_manager.load_challenge(challenge_path)
            
            # Usar IA para pre-clasificar si está disponible (opcional)
            # Esta funcionalidad está deshabilitada temporalmente para evitar errores
            # try:
            #     classifier = ChallengeClassifier()
            #     if classifier.is_trained:
            #         content = self._extract_content_for_ai(challenge_data)
            #         prediction = classifier.predict(content)
            #         if prediction['success'] and prediction['confidence'] > 0.8:
            #             challenge_data.challenge_type = ChallengeType(prediction['predicted_type'])
            # except Exception as e:
            #     self.logger.debug(f"No se pudo usar IA para pre-clasificación: {e}")
            
            # Resolver con el framework completo
            start_time = time.time()
            solution_result = self.challenge_manager.solve_challenge(challenge_data, strategy="auto")
            solve_time = time.time() - start_time
            
            # Procesar resultado
            result_data = {
                'challenge_path': str(challenge_path),
                'challenge_id': challenge_data.id,
                'challenge_name': challenge_data.name,
                'challenge_type': challenge_data.challenge_type.value,
                'solution_success': solution_result.success,
                'solution_method': solution_result.method_used,
                'plugin_used': solution_result.plugin_name,
                'confidence': solution_result.confidence,
                'execution_time': solve_time,
                'flag_found': solution_result.flag,
                'error_message': solution_result.error_message,
                'processing_timestamp': datetime.now().isoformat()
            }
            
            # Almacenar en training manager para IA
            self.training_manager.store_challenge(challenge_data, challenge_data.challenge_type)
            self.training_manager.store_solution(challenge_data.id, solution_result)
            
            # Actualizar estadísticas
            self.stats['total_processed'] += 1
            if solution_result.success:
                self.stats['successfully_solved'] += 1
                self.logger.info(f"✅ RESUELTO: {solution_result.flag}")
                
                # Mover a solved si fue exitoso
                self._move_to_solved(challenge_path, challenge_data, solution_result)
            else:
                self.stats['failed_solutions'] += 1
                self.logger.warning(f"❌ NO RESUELTO: {solution_result.error_message}")
            
            # Marcar como procesado
            try:
                relative_path = str(challenge_path.relative_to(self.uploaded_dir.parent.parent))
            except ValueError:
                relative_path = str(challenge_path)
            
            self.processed_files.add(relative_path)
            self._save_processed_list()
            
            return result_data
            
        except Exception as e:
            self.logger.error(f"Error procesando {challenge_path}: {e}")
            self.stats['failed_solutions'] += 1
            return None
    
    def _extract_content_for_ai(self, challenge_data: ChallengeData) -> str:
        """Extraer contenido para análisis de IA"""
        content_parts = []
        
        # Agregar descripción
        if challenge_data.description:
            content_parts.append(challenge_data.description)
        
        # Agregar contenido de archivos
        for file_info in challenge_data.files:
            if file_info.path.exists() and file_info.size < 10000:  # Solo archivos pequeños
                try:
                    with open(file_info.path, 'r', encoding='utf-8', errors='ignore') as f:
                        content_parts.append(f.read()[:1000])  # Primeros 1000 caracteres
                except:
                    pass
        
        return ' '.join(content_parts)
    
    def _move_to_solved(self, original_path: Path, challenge_data: ChallengeData, 
                       solution_result: SolutionResult):
        """Mover desafío resuelto a challenges/solved/"""
        try:
            solved_file = self.solved_dir / f"{challenge_data.id}_solved.json"
            
            solved_info = {
                'original_path': str(original_path),
                'challenge_id': challenge_data.id,
                'challenge_name': challenge_data.name,
                'challenge_type': challenge_data.challenge_type.value if challenge_data.challenge_type else 'unknown',
                'flag': solution_result.flag,
                'method_used': solution_result.method_used,
                'plugin_name': solution_result.plugin_name,
                'confidence': solution_result.confidence,
                'execution_time': solution_result.execution_time,
                'solved_timestamp': datetime.now().isoformat()
            }
            
            with open(solved_file, 'w', encoding='utf-8') as f:
                json.dump(solved_info, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"💾 Guardado en: {solved_file}")
            
        except Exception as e:
            self.logger.error(f"Error guardando resultado resuelto: {e}")
    
    def retrain_ai_models(self) -> bool:
        """Re-entrenar modelos de IA con nuevos datos"""
        self.logger.info("🧠 Iniciando re-entrenamiento de modelos de IA...")
        
        try:
            # Obtener datos de entrenamiento actualizados
            training_data = self.training_manager.get_training_data()
            
            if len(training_data) < 10:
                self.logger.warning("Pocos datos para re-entrenamiento, se requieren al menos 10 muestras")
                return False
            
            # Re-entrenar clasificador principal
            classifier = ChallengeClassifier()
            
            # Preparar datos en formato correcto
            formatted_data = []
            for challenge_data, challenge_type in training_data:
                content = self._extract_content_for_ai(challenge_data)
                formatted_data.append({
                    'content': content,
                    'challenge_type': challenge_type.value,
                    'metadata': {
                        'challenge_id': challenge_data.id,
                        'source': 'auto_training'
                    }
                })
            
            # Entrenar modelo
            training_result = classifier.train(formatted_data)
            
            if training_result['success']:
                self.logger.info(f"✅ IA re-entrenada exitosamente")
                self.logger.info(f"   📊 Precisión: {training_result['accuracy']:.3f}")
                self.logger.info(f"   📊 Muestras: {len(formatted_data)}")
                self.stats['models_retrained'] += 1
                return True
            else:
                self.logger.error(f"❌ Error re-entrenando IA: {training_result.get('error', 'Unknown')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error en re-entrenamiento: {e}")
            return False
    
    def run_auto_training(self, retrain_threshold: int = 5) -> Dict[str, Any]:
        """Ejecutar proceso completo de entrenamiento automático"""
        self.logger.info("🚀 INICIANDO ENTRENAMIENTO AUTOMÁTICO COMPLETO")
        self.logger.info("=" * 60)
        
        # Escanear nuevos desafíos
        new_challenges = self.scan_for_new_challenges()
        
        if not new_challenges:
            self.logger.info("ℹ️  No hay nuevos desafíos para procesar")
            return self._generate_summary()
        
        # Procesar cada desafío
        processed_results = []
        for challenge_path in new_challenges:
            result = self.process_challenge(challenge_path)
            if result:
                processed_results.append(result)
                self.stats['new_training_data'] += 1
        
        # Re-entrenar IA si hay suficientes datos nuevos
        if self.stats['new_training_data'] >= retrain_threshold:
            self.logger.info(f"🔄 Re-entrenando IA ({self.stats['new_training_data']} nuevas muestras)")
            self.retrain_ai_models()
        else:
            self.logger.info(f"ℹ️  Esperando más datos para re-entrenamiento ({self.stats['new_training_data']}/{retrain_threshold})")
        
        return self._generate_summary()
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generar resumen del proceso"""
        total_time = time.time() - self.stats['start_time']
        
        summary = {
            'execution_time': total_time,
            'total_processed': self.stats['total_processed'],
            'successfully_solved': self.stats['successfully_solved'],
            'failed_solutions': self.stats['failed_solutions'],
            'success_rate': (self.stats['successfully_solved'] / max(1, self.stats['total_processed'])) * 100,
            'new_training_data': self.stats['new_training_data'],
            'models_retrained': self.stats['models_retrained'],
            'processed_files_total': len(self.processed_files)
        }
        
        self.logger.info("📊 RESUMEN DE ENTRENAMIENTO AUTOMÁTICO")
        self.logger.info("-" * 50)
        self.logger.info(f"⏱️  Tiempo total: {total_time:.2f}s")
        self.logger.info(f"📝 Desafíos procesados: {summary['total_processed']}")
        self.logger.info(f"✅ Resueltos exitosamente: {summary['successfully_solved']}")
        self.logger.info(f"❌ Fallidos: {summary['failed_solutions']}")
        self.logger.info(f"📈 Tasa de éxito: {summary['success_rate']:.1f}%")
        self.logger.info(f"🧠 Datos de entrenamiento nuevos: {summary['new_training_data']}")
        self.logger.info(f"🔄 Modelos re-entrenados: {summary['models_retrained']}")
        self.logger.info(f"📁 Total archivos procesados: {summary['processed_files_total']}")
        
        return summary


def main():
    """Función principal"""
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        print("🔄 MODO CONTINUO - Ctrl+C para detener")
        framework = AutoTrainingFramework()
        
        try:
            while True:
                framework.run_auto_training()
                print(f"😴 Esperando 300 segundos antes del próximo ciclo...")
                time.sleep(300)  # Esperar 5 minutos
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo entrenamiento continuo...")
    else:
        print("🎯 CRYPTO CTF FRAMEWORK - ENTRENAMIENTO AUTOMÁTICO")
        print("=" * 60)
        
        framework = AutoTrainingFramework()
        summary = framework.run_auto_training()
        
        print(f"\n🏁 COMPLETADO!")
        print(f"📊 Resumen: {summary['successfully_solved']}/{summary['total_processed']} resueltos ({summary['success_rate']:.1f}%)")


if __name__ == "__main__":
    main()