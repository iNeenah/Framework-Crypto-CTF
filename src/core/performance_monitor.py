"""
Performance Monitor for System Optimization
Monitors resource usage, execution times, and system performance
"""

import time
import psutil
import threading
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
import json
from pathlib import Path

from ..utils.config import config


@dataclass
class PerformanceMetric:
    """Métrica individual de performance"""
    name: str
    value: float
    timestamp: float
    unit: str = ""
    category: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceSnapshot:
    """Snapshot de recursos del sistema"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    thread_count: int
    process_count: int


class PerformanceMonitor:
    """Monitor de performance del sistema"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics: deque = deque(maxlen=max_history)
        self.resource_history: deque = deque(maxlen=max_history)
        self.operation_times: defaultdict = defaultdict(list)
        
        self.logger = logging.getLogger(__name__)
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # Contadores de operaciones
        self.operation_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        
        # Baseline del sistema
        self.baseline_snapshot: Optional[ResourceSnapshot] = None
        self._take_baseline()
    
    def start_monitoring(self, interval: float = 1.0) -> None:
        """Iniciar monitoreo continuo de recursos"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self) -> None:
        """Detener monitoreo continuo"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        self.logger.info("Performance monitoring stopped")
    
    def record_metric(self, name: str, value: float, unit: str = "", 
                     category: str = "general", **metadata) -> None:
        """Registrar métrica de performance"""
        with self._lock:
            metric = PerformanceMetric(
                name=name,
                value=value,
                timestamp=time.time(),
                unit=unit,
                category=category,
                metadata=metadata
            )
            self.metrics.append(metric)
    
    def record_operation_time(self, operation: str, duration: float) -> None:
        """Registrar tiempo de operación"""
        with self._lock:
            self.operation_times[operation].append(duration)
            # Mantener solo las últimas N mediciones
            if len(self.operation_times[operation]) > 100:
                self.operation_times[operation] = self.operation_times[operation][-100:]
            
            self.record_metric(
                f"{operation}_time",
                duration,
                "seconds",
                "operations"
            )
    
    def increment_operation_count(self, operation: str) -> None:
        """Incrementar contador de operación"""
        with self._lock:
            self.operation_counts[operation] += 1
    
    def increment_error_count(self, error_type: str) -> None:
        """Incrementar contador de errores"""
        with self._lock:
            self.error_counts[error_type] += 1
    
    def get_operation_stats(self, operation: str) -> Dict[str, float]:
        """Obtener estadísticas de operación"""
        with self._lock:
            times = self.operation_times.get(operation, [])
            if not times:
                return {}
            
            return {
                'count': len(times),
                'total_time': sum(times),
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times),
                'median_time': sorted(times)[len(times) // 2]
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema"""
        current_snapshot = self._take_resource_snapshot()
        
        stats = {
            'current_resources': {
                'cpu_percent': current_snapshot.cpu_percent,
                'memory_mb': current_snapshot.memory_mb,
                'memory_percent': current_snapshot.memory_percent,
                'thread_count': current_snapshot.thread_count
            },
            'operation_counts': dict(self.operation_counts),
            'error_counts': dict(self.error_counts),
            'total_metrics': len(self.metrics),
            'monitoring_active': self._monitoring
        }
        
        # Comparar con baseline si está disponible
        if self.baseline_snapshot:
            stats['resource_delta'] = {
                'cpu_delta': current_snapshot.cpu_percent - self.baseline_snapshot.cpu_percent,
                'memory_delta_mb': current_snapshot.memory_mb - self.baseline_snapshot.memory_mb,
                'thread_delta': current_snapshot.thread_count - self.baseline_snapshot.thread_count
            }
        
        return stats
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Obtener resumen de performance"""
        with self._lock:
            summary = {
                'monitoring_duration': time.time() - (self.baseline_snapshot.timestamp if self.baseline_snapshot else time.time()),
                'total_operations': sum(self.operation_counts.values()),
                'total_errors': sum(self.error_counts.values()),
                'operation_stats': {},
                'resource_trends': self._analyze_resource_trends(),
                'top_operations': self._get_top_operations(),
                'performance_issues': self._detect_performance_issues()
            }
            
            # Estadísticas por operación
            for operation in self.operation_times:
                summary['operation_stats'][operation] = self.get_operation_stats(operation)
            
            return summary
    
    def export_metrics(self, file_path: Path) -> None:
        """Exportar métricas a archivo"""
        with self._lock:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'baseline': self.baseline_snapshot.__dict__ if self.baseline_snapshot else None,
                'metrics': [
                    {
                        'name': m.name,
                        'value': m.value,
                        'timestamp': m.timestamp,
                        'unit': m.unit,
                        'category': m.category,
                        'metadata': m.metadata
                    }
                    for m in self.metrics
                ],
                'resource_history': [
                    snapshot.__dict__ for snapshot in self.resource_history
                ],
                'operation_times': dict(self.operation_times),
                'operation_counts': dict(self.operation_counts),
                'error_counts': dict(self.error_counts)
            }
            
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Performance metrics exported to {file_path}")
    
    def _monitor_loop(self, interval: float) -> None:
        """Loop principal de monitoreo"""
        while self._monitoring:
            try:
                snapshot = self._take_resource_snapshot()
                with self._lock:
                    self.resource_history.append(snapshot)
                
                # Registrar métricas de recursos
                self.record_metric("cpu_percent", snapshot.cpu_percent, "%", "resources")
                self.record_metric("memory_mb", snapshot.memory_mb, "MB", "resources")
                self.record_metric("memory_percent", snapshot.memory_percent, "%", "resources")
                self.record_metric("thread_count", snapshot.thread_count, "count", "resources")
                
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def _take_baseline(self) -> None:
        """Tomar snapshot baseline del sistema"""
        self.baseline_snapshot = self._take_resource_snapshot()
        self.logger.info("Baseline performance snapshot taken")
    
    def _take_resource_snapshot(self) -> ResourceSnapshot:
        """Tomar snapshot de recursos actuales"""
        try:
            process = psutil.Process()
            
            # CPU y memoria del proceso
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # Memoria del sistema
            system_memory = psutil.virtual_memory()
            memory_percent = system_memory.percent
            
            # I/O de disco
            try:
                io_counters = process.io_counters()
                disk_read_mb = io_counters.read_bytes / 1024 / 1024
                disk_write_mb = io_counters.write_bytes / 1024 / 1024
            except (AttributeError, psutil.AccessDenied):
                disk_read_mb = disk_write_mb = 0
            
            # Red (del sistema)
            try:
                net_io = psutil.net_io_counters()
                net_sent_mb = net_io.bytes_sent / 1024 / 1024
                net_recv_mb = net_io.bytes_recv / 1024 / 1024
            except (AttributeError, psutil.AccessDenied):
                net_sent_mb = net_recv_mb = 0
            
            # Threads y procesos
            thread_count = process.num_threads()
            process_count = len(psutil.pids())
            
            return ResourceSnapshot(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_sent_mb=net_sent_mb,
                network_recv_mb=net_recv_mb,
                thread_count=thread_count,
                process_count=process_count
            )
            
        except Exception as e:
            self.logger.error(f"Error taking resource snapshot: {e}")
            return ResourceSnapshot(
                timestamp=time.time(),
                cpu_percent=0, memory_mb=0, memory_percent=0,
                disk_io_read_mb=0, disk_io_write_mb=0,
                network_sent_mb=0, network_recv_mb=0,
                thread_count=0, process_count=0
            )
    
    def _analyze_resource_trends(self) -> Dict[str, str]:
        """Analizar tendencias de recursos"""
        if len(self.resource_history) < 10:
            return {"status": "insufficient_data"}
        
        recent_snapshots = list(self.resource_history)[-10:]
        
        # Analizar tendencia de memoria
        memory_values = [s.memory_mb for s in recent_snapshots]
        memory_trend = "stable"
        if memory_values[-1] > memory_values[0] * 1.2:
            memory_trend = "increasing"
        elif memory_values[-1] < memory_values[0] * 0.8:
            memory_trend = "decreasing"
        
        # Analizar tendencia de CPU
        cpu_values = [s.cpu_percent for s in recent_snapshots]
        avg_cpu = sum(cpu_values) / len(cpu_values)
        cpu_trend = "high" if avg_cpu > 80 else "normal" if avg_cpu > 20 else "low"
        
        return {
            "memory_trend": memory_trend,
            "cpu_trend": cpu_trend,
            "avg_cpu": avg_cpu,
            "current_memory_mb": memory_values[-1]
        }
    
    def _get_top_operations(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Obtener operaciones más frecuentes"""
        sorted_ops = sorted(
            self.operation_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {
                "operation": op,
                "count": count,
                "stats": self.get_operation_stats(op)
            }
            for op, count in sorted_ops[:limit]
        ]
    
    def _detect_performance_issues(self) -> List[Dict[str, str]]:
        """Detectar problemas de performance"""
        issues = []
        
        # Verificar uso de memoria
        if self.resource_history:
            latest = self.resource_history[-1]
            if latest.memory_percent > 90:
                issues.append({
                    "type": "high_memory_usage",
                    "severity": "critical",
                    "description": f"Memory usage at {latest.memory_percent:.1f}%"
                })
            elif latest.memory_percent > 75:
                issues.append({
                    "type": "elevated_memory_usage",
                    "severity": "warning",
                    "description": f"Memory usage at {latest.memory_percent:.1f}%"
                })
        
        # Verificar operaciones lentas
        for operation, times in self.operation_times.items():
            if times:
                avg_time = sum(times) / len(times)
                if avg_time > 10.0:  # Más de 10 segundos promedio
                    issues.append({
                        "type": "slow_operation",
                        "severity": "warning",
                        "description": f"Operation '{operation}' averaging {avg_time:.1f}s"
                    })
        
        # Verificar tasa de errores
        total_ops = sum(self.operation_counts.values())
        total_errors = sum(self.error_counts.values())
        if total_ops > 0:
            error_rate = total_errors / total_ops
            if error_rate > 0.1:  # Más del 10% de errores
                issues.append({
                    "type": "high_error_rate",
                    "severity": "critical",
                    "description": f"Error rate at {error_rate * 100:.1f}%"
                })
        
        return issues


class PerformanceTimer:
    """Context manager para medir tiempo de operaciones"""
    
    def __init__(self, operation_name: str, monitor: Optional[PerformanceMonitor] = None):
        self.operation_name = operation_name
        self.monitor = monitor or performance_monitor
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.monitor.increment_operation_count(self.operation_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.monitor.record_operation_time(self.operation_name, duration)
            
            if exc_type:
                self.monitor.increment_error_count(f"{self.operation_name}_error")


def timed_operation(operation_name: str):
    """Decorador para medir tiempo de operaciones"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            with PerformanceTimer(operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Instancia global del monitor de performance
performance_monitor = PerformanceMonitor()