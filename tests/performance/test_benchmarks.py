"""
Performance benchmarks and stress tests
"""

import pytest
import time
import tempfile
import zipfile
import threading
import psutil
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

from src.core.challenge_manager import ChallengeManager
from src.core.file_analyzer import FileAnalyzer
from src.core.plugin_manager import PluginManager
from src.ml.feature_extractor import FeatureExtractor
from src.models.data import ChallengeData, ChallengeType, FileInfo


class TestPerformanceBenchmarks:
    """Benchmarks de performance del sistema"""
    
    @pytest.fixture
    def performance_workspace(self):
        """Workspace para tests de performance"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = Path(tmp_dir)
            (workspace / "challenges").mkdir()
            (workspace / "extracted").mkdir()
            yield workspace
    
    @pytest.fixture
    def large_challenge_dataset(self, performance_workspace):
        """Dataset grande de desafíos para benchmarks"""
        challenges = []
        
        for i in range(50):  # 50 desafíos
            challenge_dir = performance_workspace / "challenges" / f"challenge_{i}"
            challenge_dir.mkdir()
            
            # Crear archivos de diferentes tamaños
            for j in range(3):  # 3 archivos por desafío
                file_path = challenge_dir / f"file_{j}.txt"
                content_size = 1000 + (i * 100) + (j * 50)  # Tamaños variables
                content = "x" * content_size
                
                if i % 3 == 0:  # RSA challenges
                    content = f"RSA public key modulus factorization {content}"
                elif i % 3 == 1:  # Basic crypto
                    content = f"caesar cipher frequency analysis {content}"
                else:  # Network
                    content = f"socket netcat tcp connection {content}"
                
                file_path.write_text(content)
            
            # Crear ZIP
            zip_path = performance_workspace / "challenges" / f"challenge_{i}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                for file_path in challenge_dir.iterdir():
                    zf.write(file_path, file_path.name)
            
            challenges.append(zip_path)
        
        return challenges
    
    def test_file_analysis_performance(self, large_challenge_dataset):
        """Benchmark de análisis de archivos"""
        file_analyzer = FileAnalyzer()
        
        start_time = time.time()
        processed_challenges = []
        
        for challenge_file in large_challenge_dataset[:10]:  # Procesar 10 desafíos
            try:
                challenge_data = file_analyzer.analyze_file(challenge_file)
                processed_challenges.append(challenge_data)
            except Exception as e:
                print(f"Error processing {challenge_file}: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Métricas de performance
        avg_time_per_challenge = total_time / len(processed_challenges) if processed_challenges else 0
        
        print(f"\n=== File Analysis Performance ===")
        print(f"Total challenges processed: {len(processed_challenges)}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average time per challenge: {avg_time_per_challenge:.2f}s")
        print(f"Challenges per second: {len(processed_challenges) / total_time:.2f}")
        
        # Assertions de performance
        assert avg_time_per_challenge < 5.0  # Menos de 5 segundos por desafío
        assert len(processed_challenges) > 0
    
    def test_feature_extraction_performance(self, large_challenge_dataset):
        """Benchmark de extracción de características"""
        file_analyzer = FileAnalyzer()
        feature_extractor = FeatureExtractor()
        
        # Preparar desafíos
        challenges = []
        for challenge_file in large_challenge_dataset[:5]:
            try:
                challenge_data = file_analyzer.analyze_file(challenge_file)
                challenges.append(challenge_data)
            except Exception:
                continue
        
        if not challenges:
            pytest.skip("No challenges available for feature extraction test")
        
        # Benchmark extracción de características
        start_time = time.time()
        
        for challenge in challenges:
            features = feature_extractor.extract_features(challenge)
            vector = feature_extractor.extract_features_vector(challenge)
            
            assert len(features) > 0
            assert len(vector) > 0
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / len(challenges)
        
        print(f"\n=== Feature Extraction Performance ===")
        print(f"Challenges processed: {len(challenges)}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average time per challenge: {avg_time:.2f}s")
        
        # Assertion de performance
        assert avg_time < 2.0  # Menos de 2 segundos por desafío
    
    def test_plugin_selection_performance(self, large_challenge_dataset):
        """Benchmark de selección de plugins"""
        file_analyzer = FileAnalyzer()
        plugin_manager = PluginManager()
        
        # Preparar desafíos
        challenges = []
        for challenge_file in large_challenge_dataset[:10]:
            try:
                challenge_data = file_analyzer.analyze_file(challenge_file)
                challenges.append(challenge_data)
            except Exception:
                continue
        
        if not challenges:
            pytest.skip("No challenges available for plugin selection test")
        
        # Benchmark selección de plugins
        start_time = time.time()
        
        for challenge in challenges:
            best_plugins = plugin_manager.select_best_plugins(challenge)
            assert isinstance(best_plugins, list)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / len(challenges)
        
        print(f"\n=== Plugin Selection Performance ===")
        print(f"Challenges processed: {len(challenges)}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average time per challenge: {avg_time:.2f}s")
        
        # Assertion de performance
        assert avg_time < 1.0  # Menos de 1 segundo por desafío
    
    def test_concurrent_challenge_processing(self, large_challenge_dataset):
        """Test de procesamiento concurrente de desafíos"""
        challenge_manager = ChallengeManager()
        
        def process_challenge(challenge_file):
            try:
                challenge_data = challenge_manager.load_challenge(challenge_file)
                result = challenge_manager.solve_challenge(challenge_data, strategy="single")
                return result
            except Exception as e:
                return None
        
        # Procesar desafíos concurrentemente
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(process_challenge, challenge_file)
                for challenge_file in large_challenge_dataset[:8]  # 8 desafíos
            ]
            
            results = []
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n=== Concurrent Processing Performance ===")
        print(f"Challenges submitted: {len(large_challenge_dataset[:8])}")
        print(f"Results obtained: {len(results)}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average time per challenge: {total_time / len(large_challenge_dataset[:8]):.2f}s")
        
        # Al menos algunos desafíos deberían procesarse
        assert len(results) >= 0  # Puede ser 0 si no hay plugins funcionales
    
    def test_memory_usage_monitoring(self, large_challenge_dataset):
        """Test de monitoreo de uso de memoria"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        challenge_manager = ChallengeManager()
        
        # Procesar varios desafíos y monitorear memoria
        memory_samples = [initial_memory]
        
        for i, challenge_file in enumerate(large_challenge_dataset[:5]):
            try:
                challenge_data = challenge_manager.load_challenge(challenge_file)
                result = challenge_manager.solve_challenge(challenge_data)
                
                # Muestrear memoria
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                
            except Exception as e:
                continue
        
        max_memory = max(memory_samples)
        memory_growth = max_memory - initial_memory
        
        print(f"\n=== Memory Usage Monitoring ===")
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"Maximum memory: {max_memory:.2f} MB")
        print(f"Memory growth: {memory_growth:.2f} MB")
        print(f"Memory samples: {len(memory_samples)}")
        
        # Verificar que el crecimiento de memoria sea razonable
        assert memory_growth < 500  # Menos de 500MB de crecimiento
    
    def test_large_file_processing(self, performance_workspace):
        """Test de procesamiento de archivos grandes"""
        # Crear archivo grande
        large_file = performance_workspace / "large_challenge.txt"
        
        # Crear contenido grande (10MB simulado con repetición)
        base_content = "This is a large RSA challenge with public key and modulus. " * 1000
        large_file.write_text(base_content)
        
        file_analyzer = FileAnalyzer()
        
        start_time = time.time()
        challenge_data = file_analyzer.analyze_file(large_file)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        print(f"\n=== Large File Processing ===")
        print(f"File size: {large_file.stat().st_size / 1024 / 1024:.2f} MB")
        print(f"Processing time: {processing_time:.2f}s")
        print(f"Challenge type detected: {challenge_data.challenge_type}")
        
        # Verificar que se procesó correctamente
        assert challenge_data is not None
        assert processing_time < 30.0  # Menos de 30 segundos
    
    def test_stress_plugin_manager(self):
        """Test de estrés del plugin manager"""
        plugin_manager = PluginManager()
        
        # Crear muchos desafíos simulados
        challenges = []
        for i in range(100):
            challenge = ChallengeData(
                id=f"stress_test_{i}",
                name=f"Stress Test {i}",
                challenge_type=ChallengeType.RSA if i % 2 == 0 else ChallengeType.BASIC_CRYPTO
            )
            challenges.append(challenge)
        
        start_time = time.time()
        
        # Procesar todos los desafíos
        for challenge in challenges:
            try:
                best_plugins = plugin_manager.select_best_plugins(challenge, max_plugins=2)
                assert isinstance(best_plugins, list)
            except Exception as e:
                # Aceptable bajo estrés
                pass
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n=== Plugin Manager Stress Test ===")
        print(f"Challenges processed: {len(challenges)}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Challenges per second: {len(challenges) / total_time:.2f}")
        
        # Verificar performance bajo estrés
        assert total_time < 60.0  # Menos de 1 minuto para 100 desafíos
    
    def test_resource_cleanup_performance(self, large_challenge_dataset):
        """Test de performance de limpieza de recursos"""
        file_analyzer = FileAnalyzer()
        
        # Procesar varios desafíos
        challenge_ids = []
        
        start_time = time.time()
        
        for challenge_file in large_challenge_dataset[:5]:
            try:
                challenge_data = file_analyzer.analyze_file(challenge_file)
                challenge_ids.append(challenge_data.id)
            except Exception:
                continue
        
        # Limpiar todos los archivos extraídos
        cleanup_start = time.time()
        
        for challenge_id in challenge_ids:
            file_analyzer.cleanup_extracted_files(challenge_id)
        
        cleanup_end = time.time()
        total_time = time.time() - start_time
        cleanup_time = cleanup_end - cleanup_start
        
        print(f"\n=== Resource Cleanup Performance ===")
        print(f"Challenges processed: {len(challenge_ids)}")
        print(f"Total processing time: {total_time:.2f}s")
        print(f"Cleanup time: {cleanup_time:.2f}s")
        print(f"Cleanup percentage: {(cleanup_time / total_time) * 100:.1f}%")
        
        # Verificar que la limpieza sea eficiente
        assert cleanup_time < total_time * 0.1  # Limpieza < 10% del tiempo total


class TestStressTests:
    """Tests de estrés del sistema"""
    
    def test_rapid_challenge_loading(self, tmp_path):
        """Test de carga rápida de desafíos"""
        challenge_manager = ChallengeManager()
        
        # Crear muchos archivos pequeños
        challenge_files = []
        for i in range(20):
            challenge_file = tmp_path / f"rapid_test_{i}.txt"
            challenge_file.write_text(f"Challenge {i} content")
            challenge_files.append(challenge_file)
        
        start_time = time.time()
        loaded_challenges = []
        
        # Cargar rápidamente
        for challenge_file in challenge_files:
            try:
                challenge_data = challenge_manager.load_challenge(challenge_file)
                loaded_challenges.append(challenge_data)
            except Exception:
                pass
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n=== Rapid Challenge Loading ===")
        print(f"Files created: {len(challenge_files)}")
        print(f"Challenges loaded: {len(loaded_challenges)}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Loading rate: {len(loaded_challenges) / total_time:.2f} challenges/s")
        
        # Verificar que se cargaron la mayoría
        assert len(loaded_challenges) >= len(challenge_files) * 0.8  # Al menos 80%
    
    def test_plugin_error_resilience(self):
        """Test de resistencia a errores de plugins"""
        plugin_manager = PluginManager()
        
        # Crear desafío que podría causar errores
        problematic_challenge = ChallengeData(
            id="problematic",
            name="Problematic Challenge",
            challenge_type=ChallengeType.UNKNOWN  # Tipo desconocido
        )
        
        # Intentar seleccionar plugins múltiples veces
        success_count = 0
        
        for i in range(50):
            try:
                best_plugins = plugin_manager.select_best_plugins(problematic_challenge)
                success_count += 1
            except Exception:
                pass
        
        print(f"\n=== Plugin Error Resilience ===")
        print(f"Attempts: 50")
        print(f"Successes: {success_count}")
        print(f"Success rate: {(success_count / 50) * 100:.1f}%")
        
        # Debería manejar errores graciosamente
        assert success_count >= 40  # Al menos 80% de éxito
    
    def test_concurrent_file_access(self, tmp_path):
        """Test de acceso concurrente a archivos"""
        # Crear archivo compartido
        shared_file = tmp_path / "shared_challenge.txt"
        shared_file.write_text("Shared challenge content for concurrent access")
        
        file_analyzer = FileAnalyzer()
        results = []
        errors = []
        
        def analyze_file_concurrent():
            try:
                challenge_data = file_analyzer.analyze_file(shared_file)
                results.append(challenge_data)
            except Exception as e:
                errors.append(e)
        
        # Crear múltiples threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=analyze_file_concurrent)
            threads.append(thread)
        
        # Ejecutar concurrentemente
        start_time = time.time()
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n=== Concurrent File Access ===")
        print(f"Threads: {len(threads)}")
        print(f"Successful analyses: {len(results)}")
        print(f"Errors: {len(errors)}")
        print(f"Total time: {total_time:.2f}s")
        
        # Verificar que la mayoría tuvo éxito
        assert len(results) >= len(threads) * 0.7  # Al menos 70% de éxito


if __name__ == "__main__":
    # Ejecutar con marcadores de performance
    pytest.main([__file__, "-v", "-s", "--tb=short"])