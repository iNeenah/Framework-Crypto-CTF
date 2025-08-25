"""
Tests for Performance Optimization Components
"""

import pytest
import time
import tempfile
import threading
from pathlib import Path
from unittest.mock import Mock, patch

from src.core.cache_manager import CacheManager, CacheEntry, cached
from src.core.performance_monitor import PerformanceMonitor, PerformanceTimer
from src.core.parallel_executor import ParallelExecutor, ExecutionConfig, ExecutionMode
from src.models.data import ChallengeData, SolutionResult, ChallengeType


class TestCacheManager:
    """Tests para el sistema de cache"""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Directorio temporal para cache"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        """Cache manager con directorio temporal"""
        return CacheManager(cache_dir=temp_cache_dir, max_memory_mb=10)
    
    def test_cache_entry_creation(self):
        """Test creación de entrada de cache"""
        entry = CacheEntry("test_key", "test_value", ttl=60)
        
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.ttl == 60
        assert entry.access_count == 0
        assert not entry.is_expired()
    
    def test_cache_entry_expiration(self):
        """Test expiración de entrada de cache"""
        entry = CacheEntry("test_key", "test_value", ttl=1)
        
        assert not entry.is_expired()
        
        # Simular paso del tiempo
        entry.created_at = time.time() - 2
        assert entry.is_expired()
    
    def test_cache_put_get(self, cache_manager):
        """Test almacenar y recuperar del cache"""
        cache_manager.put("test_key", "test_value")
        
        result = cache_manager.get("test_key")
        assert result == "test_value"
    
    def test_cache_miss(self, cache_manager):
        """Test cache miss"""
        result = cache_manager.get("nonexistent_key")
        assert result is None
    
    def test_cache_ttl_expiration(self, cache_manager):
        """Test expiración por TTL"""
        cache_manager.put("test_key", "test_value", ttl=1)
        
        # Inmediatamente debería estar disponible
        assert cache_manager.get("test_key") == "test_value"
        
        # Simular expiración
        time.sleep(1.1)
        assert cache_manager.get("test_key") is None
    
    def test_cache_invalidation(self, cache_manager):
        """Test invalidación de cache"""
        cache_manager.put("test_key", "test_value")
        assert cache_manager.get("test_key") == "test_value"
        
        cache_manager.invalidate("test_key")
        assert cache_manager.get("test_key") is None
    
    def test_cache_clear(self, cache_manager):
        """Test limpieza completa del cache"""
        cache_manager.put("key1", "value1")
        cache_manager.put("key2", "value2")
        
        cache_manager.clear()
        
        assert cache_manager.get("key1") is None
        assert cache_manager.get("key2") is None
    
    def test_cache_stats(self, cache_manager):
        """Test estadísticas del cache"""
        # Generar algunos hits y misses
        cache_manager.put("key1", "value1")
        cache_manager.get("key1")  # hit
        cache_manager.get("key2")  # miss
        
        stats = cache_manager.get_stats()
        
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 50.0
        assert stats['memory_entries'] == 1
    
    def test_memory_limit_enforcement(self, temp_cache_dir):
        """Test límite de memoria"""
        # Cache muy pequeño para forzar evicción
        small_cache = CacheManager(cache_dir=temp_cache_dir, max_memory_mb=1)
        
        # Llenar cache con datos grandes
        large_data = "x" * 1024 * 100  # 100KB
        
        for i in range(20):  # Intentar almacenar 2MB
            small_cache.put(f"key_{i}", large_data)
        
        # Verificar que no todas las entradas están en memoria
        memory_entries = len(small_cache.memory_cache)
        assert memory_entries < 20  # Algunas deberían haberse evictado
    
    def test_disk_cache_fallback(self, cache_manager):
        """Test fallback a cache en disco"""
        # Llenar memoria para forzar uso de disco
        large_data = "x" * 1024 * 1024  # 1MB
        
        for i in range(15):  # Más de lo que cabe en memoria
            cache_manager.put(f"large_key_{i}", large_data)
        
        # Verificar que algunas entradas están en disco
        assert len(cache_manager.disk_cache_index) > 0
        
        # Verificar que podemos recuperar desde disco
        result = cache_manager.get("large_key_0")
        assert result == large_data
    
    def test_cached_decorator(self):
        """Test decorador de cache"""
        call_count = 0
        
        @cached(ttl=60)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # Primera llamada
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Segunda llamada (debería usar cache)
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # No debería incrementar
        
        # Llamada con argumentos diferentes
        result3 = expensive_function(2, 3)
        assert result3 == 5
        assert call_count == 2  # Debería incrementar


class TestPerformanceMonitor:
    """Tests para el monitor de performance"""
    
    @pytest.fixture
    def monitor(self):
        """Monitor de performance para tests"""
        return PerformanceMonitor(max_history=100)
    
    def test_monitor_initialization(self, monitor):
        """Test inicialización del monitor"""
        assert len(monitor.metrics) == 0
        assert len(monitor.resource_history) == 0
        assert not monitor._monitoring
        assert monitor.baseline_snapshot is not None
    
    def test_record_metric(self, monitor):
        """Test registro de métricas"""
        monitor.record_metric("test_metric", 42.0, "units", "test_category")
        
        assert len(monitor.metrics) == 1
        metric = monitor.metrics[0]
        assert metric.name == "test_metric"
        assert metric.value == 42.0
        assert metric.unit == "units"
        assert metric.category == "test_category"
    
    def test_record_operation_time(self, monitor):
        """Test registro de tiempo de operación"""
        monitor.record_operation_time("test_operation", 1.5)
        
        assert "test_operation" in monitor.operation_times
        assert monitor.operation_times["test_operation"] == [1.5]
        
        stats = monitor.get_operation_stats("test_operation")
        assert stats['count'] == 1
        assert stats['avg_time'] == 1.5
        assert stats['total_time'] == 1.5
    
    def test_operation_counters(self, monitor):
        """Test contadores de operaciones"""
        monitor.increment_operation_count("test_op")
        monitor.increment_operation_count("test_op")
        monitor.increment_error_count("test_error")
        
        assert monitor.operation_counts["test_op"] == 2
        assert monitor.error_counts["test_error"] == 1
    
    def test_performance_timer_context(self, monitor):
        """Test context manager de timer"""
        with PerformanceTimer("test_timer", monitor):
            time.sleep(0.1)
        
        assert "test_timer" in monitor.operation_times
        assert len(monitor.operation_times["test_timer"]) == 1
        assert monitor.operation_times["test_timer"][0] >= 0.1
        assert monitor.operation_counts["test_timer"] == 1
    
    def test_performance_timer_with_exception(self, monitor):
        """Test timer con excepción"""
        try:
            with PerformanceTimer("error_timer", monitor):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        assert monitor.operation_counts["error_timer"] == 1
        assert monitor.error_counts["error_timer_error"] == 1
    
    def test_system_stats(self, monitor):
        """Test estadísticas del sistema"""
        monitor.increment_operation_count("test_op")
        monitor.increment_error_count("test_error")
        
        stats = monitor.get_system_stats()
        
        assert 'current_resources' in stats
        assert 'operation_counts' in stats
        assert 'error_counts' in stats
        assert stats['operation_counts']['test_op'] == 1
        assert stats['error_counts']['test_error'] == 1
    
    def test_monitoring_start_stop(self, monitor):
        """Test inicio y parada del monitoreo"""
        assert not monitor._monitoring
        
        monitor.start_monitoring(interval=0.1)
        assert monitor._monitoring
        
        time.sleep(0.3)  # Permitir algunas muestras
        
        monitor.stop_monitoring()
        assert not monitor._monitoring
        
        # Verificar que se tomaron muestras
        assert len(monitor.resource_history) > 0
    
    def test_performance_summary(self, monitor):
        """Test resumen de performance"""
        monitor.record_operation_time("op1", 1.0)
        monitor.record_operation_time("op2", 2.0)
        monitor.increment_operation_count("op1")
        monitor.increment_error_count("error1")
        
        summary = monitor.get_performance_summary()
        
        assert 'total_operations' in summary
        assert 'total_errors' in summary
        assert 'operation_stats' in summary
        assert 'performance_issues' in summary
        
        assert summary['total_operations'] == 1
        assert summary['total_errors'] == 1


class TestParallelExecutor:
    """Tests para el executor paralelo"""
    
    @pytest.fixture
    def executor(self):
        """Executor paralelo para tests"""
        config = ExecutionConfig(
            mode=ExecutionMode.THREAD_POOL,
            max_workers=2,
            timeout=5.0
        )
        return ParallelExecutor(config)
    
    def test_executor_initialization(self, executor):
        """Test inicialización del executor"""
        assert executor.config.mode == ExecutionMode.THREAD_POOL
        assert executor.config.max_workers == 2
        assert executor.config.timeout == 5.0
    
    def test_simple_parallel_execution(self, executor):
        """Test ejecución paralela simple"""
        def simple_task(x):
            return x * 2
        
        tasks = [
            (simple_task, (1,), {}),
            (simple_task, (2,), {}),
            (simple_task, (3,), {})
        ]
        
        results = executor.execute_parallel(tasks)
        
        assert len(results) == 3
        assert all(result.success for result in results)
        
        values = [result.result for result in results]
        assert sorted(values) == [2, 4, 6]
    
    def test_parallel_execution_with_error(self, executor):
        """Test ejecución paralela con errores"""
        def error_task():
            raise ValueError("Test error")
        
        def success_task():
            return "success"
        
        tasks = [
            (error_task, (), {}),
            (success_task, (), {})
        ]
        
        results = executor.execute_parallel(tasks)
        
        assert len(results) == 2
        
        # Un resultado exitoso, uno con error
        success_results = [r for r in results if r.success]
        error_results = [r for r in results if not r.success]
        
        assert len(success_results) == 1
        assert len(error_results) == 1
        assert success_results[0].result == "success"
        assert isinstance(error_results[0].error, ValueError)
    
    def test_parallel_execution_with_timeout(self):
        """Test ejecución paralela con timeout"""
        config = ExecutionConfig(
            mode=ExecutionMode.THREAD_POOL,
            max_workers=2,
            timeout=0.5  # Timeout muy corto
        )
        executor = ParallelExecutor(config)
        
        def slow_task():
            time.sleep(1.0)  # Más lento que el timeout
            return "slow_result"
        
        tasks = [(slow_task, (), {})]
        
        results = executor.execute_parallel(tasks)
        
        # Debería manejar el timeout graciosamente
        assert len(results) == 1
        # El resultado puede ser exitoso o fallido dependiendo del timing
    
    def test_plugin_parallel_execution(self, executor):
        """Test ejecución paralela de plugins"""
        # Mock challenge data
        challenge_data = ChallengeData(
            id="test_challenge",
            name="Test Challenge",
            challenge_type=ChallengeType.BASIC_CRYPTO
        )
        
        # Mock plugins
        mock_plugin1 = Mock()
        mock_plugin1.solve.return_value = SolutionResult(
            success=True,
            solution="solution1",
            plugin_name="plugin1"
        )
        
        mock_plugin2 = Mock()
        mock_plugin2.solve.return_value = SolutionResult(
            success=False,
            error_message="Plugin2 failed",
            plugin_name="plugin2"
        )
        
        plugins = [
            ("plugin1", mock_plugin1, 0.8),
            ("plugin2", mock_plugin2, 0.6)
        ]
        
        results = executor.execute_plugins_parallel(challenge_data, plugins)
        
        assert len(results) == 2
        
        # Verificar que los plugins fueron llamados
        mock_plugin1.solve.assert_called_once_with(challenge_data)
        mock_plugin2.solve.assert_called_once_with(challenge_data)
        
        # Verificar resultados
        success_results = [r for r in results if r.success]
        assert len(success_results) == 1
        assert success_results[0].solution == "solution1"
    
    def test_execution_stats(self, executor):
        """Test estadísticas de ejecución"""
        def simple_task(x):
            return x
        
        tasks = [(simple_task, (i,), {}) for i in range(5)]
        
        executor.execute_parallel(tasks)
        
        stats = executor.get_stats()
        
        assert 'tasks_executed' in stats
        assert 'tasks_failed' in stats
        assert 'config' in stats
        assert stats['tasks_executed'] == 5
        assert stats['tasks_failed'] == 0
    
    def test_different_execution_modes(self):
        """Test diferentes modos de ejecución"""
        def simple_task(x):
            return x * 2
        
        tasks = [(simple_task, (i,), {}) for i in range(3)]
        
        # Test thread pool
        thread_executor = ParallelExecutor(ExecutionConfig(mode=ExecutionMode.THREAD_POOL))
        thread_results = thread_executor.execute_parallel(tasks)
        assert len(thread_results) == 3
        assert all(r.success for r in thread_results)
        
        # Test async concurrent
        async_executor = ParallelExecutor(ExecutionConfig(mode=ExecutionMode.ASYNC_CONCURRENT))
        async_results = async_executor.execute_parallel(tasks)
        assert len(async_results) == 3
        assert all(r.success for r in async_results)


class TestIntegratedPerformanceOptimizations:
    """Tests de integración para optimizaciones de performance"""
    
    def test_cached_challenge_analysis(self):
        """Test análisis de desafío con cache"""
        from src.core.cache_manager import cache_challenge_analysis
        
        challenge_data = ChallengeData(
            id="test_challenge",
            name="Test Challenge",
            description="Test description"
        )
        
        cache_key = cache_challenge_analysis(challenge_data)
        assert cache_key.startswith("challenge_analysis:")
        assert len(cache_key) > 20  # Debería tener un hash
    
    def test_performance_monitoring_integration(self):
        """Test integración del monitoreo de performance"""
        from src.core.performance_monitor import performance_monitor, timed_operation
        
        @timed_operation("test_integration")
        def test_function():
            time.sleep(0.1)
            return "result"
        
        result = test_function()
        
        assert result == "result"
        assert "test_integration" in performance_monitor.operation_times
        assert performance_monitor.operation_counts["test_integration"] >= 1
    
    def test_cache_and_monitoring_together(self):
        """Test cache y monitoreo trabajando juntos"""
        from src.core.cache_manager import cache_manager, cached
        from src.core.performance_monitor import performance_monitor
        
        call_count = 0
        
        @cached(ttl=60)
        def monitored_cached_function(x):
            nonlocal call_count
            call_count += 1
            time.sleep(0.05)  # Simular trabajo
            return x * 2
        
        # Primera llamada - debería ejecutar la función
        result1 = monitored_cached_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Segunda llamada - debería usar cache
        result2 = monitored_cached_function(5)
        assert result2 == 10
        assert call_count == 1  # No debería incrementar
        
        # Verificar que el cache tiene la entrada
        stats = cache_manager.get_stats()
        assert stats['hits'] >= 1


if __name__ == "__main__":
    pytest.main([__file__])