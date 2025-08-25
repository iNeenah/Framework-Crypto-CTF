"""
Advanced Parallel Execution System
Implements intelligent parallelization for plugin execution and task processing
"""

import asyncio
import threading
import multiprocessing
import concurrent.futures
import time
import logging
from typing import List, Dict, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import queue
import psutil

from ..models.data import ChallengeData, SolutionResult
from ..utils.config import config
from .performance_monitor import performance_monitor, PerformanceTimer


class ExecutionMode(Enum):
    """Modos de ejecución paralela"""
    THREAD_POOL = "thread_pool"
    PROCESS_POOL = "process_pool"
    ASYNC_CONCURRENT = "async_concurrent"
    HYBRID = "hybrid"


@dataclass
class TaskResult:
    """Resultado de ejecución de tarea"""
    task_id: str
    success: bool
    result: Any
    execution_time: float
    error: Optional[Exception] = None
    worker_id: Optional[str] = None


@dataclass
class ExecutionConfig:
    """Configuración de ejecución paralela"""
    mode: ExecutionMode = ExecutionMode.THREAD_POOL
    max_workers: Optional[int] = None
    timeout: Optional[float] = None
    memory_limit_mb: Optional[int] = None
    cpu_limit_percent: Optional[float] = None
    priority_scheduling: bool = True
    load_balancing: bool = True


class ResourceMonitor:
    """Monitor de recursos para control de ejecución"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def check_resources(self, config: ExecutionConfig) -> bool:
        """Verificar si hay recursos suficientes para ejecución"""
        try:
            # Verificar memoria
            if config.memory_limit_mb:
                memory = psutil.virtual_memory()
                available_mb = memory.available / 1024 / 1024
                if available_mb < config.memory_limit_mb:
                    self.logger.warning(f"Insufficient memory: {available_mb:.1f}MB < {config.memory_limit_mb}MB")
                    return False
            
            # Verificar CPU
            if config.cpu_limit_percent:
                cpu_percent = psutil.cpu_percent(interval=1)
                if cpu_percent > config.cpu_limit_percent:
                    self.logger.warning(f"High CPU usage: {cpu_percent:.1f}% > {config.cpu_limit_percent}%")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking resources: {e}")
            return True  # Permitir ejecución si no se puede verificar


class TaskQueue:
    """Cola de tareas con prioridades"""
    
    def __init__(self):
        self.high_priority = queue.PriorityQueue()
        self.normal_priority = queue.Queue()
        self.low_priority = queue.Queue()
        self._lock = threading.Lock()
    
    def put(self, task: Tuple[Callable, tuple, dict], priority: str = "normal") -> None:
        """Agregar tarea a la cola"""
        with self._lock:
            if priority == "high":
                # Usar timestamp negativo para orden FIFO en PriorityQueue
                self.high_priority.put((-time.time(), task))
            elif priority == "low":
                self.low_priority.put(task)
            else:
                self.normal_priority.put(task)
    
    def get(self, timeout: Optional[float] = None) -> Optional[Tuple[Callable, tuple, dict]]:
        """Obtener siguiente tarea"""
        with self._lock:
            # Prioridad alta primero
            if not self.high_priority.empty():
                try:
                    _, task = self.high_priority.get_nowait()
                    return task
                except queue.Empty:
                    pass
            
            # Luego prioridad normal
            if not self.normal_priority.empty():
                try:
                    return self.normal_priority.get_nowait()
                except queue.Empty:
                    pass
            
            # Finalmente prioridad baja
            if not self.low_priority.empty():
                try:
                    return self.low_priority.get_nowait()
                except queue.Empty:
                    pass
        
        return None
    
    def size(self) -> int:
        """Obtener tamaño total de la cola"""
        return (self.high_priority.qsize() + 
                self.normal_priority.qsize() + 
                self.low_priority.qsize())
    
    def empty(self) -> bool:
        """Verificar si la cola está vacía"""
        return self.size() == 0


class ParallelExecutor:
    """Ejecutor paralelo avanzado"""
    
    def __init__(self, config: Optional[ExecutionConfig] = None):
        self.config = config or ExecutionConfig()
        self.resource_monitor = ResourceMonitor()
        self.task_queue = TaskQueue()
        self.logger = logging.getLogger(__name__)
        
        # Determinar número óptimo de workers
        if not self.config.max_workers:
            self.config.max_workers = self._calculate_optimal_workers()
        
        # Pools de ejecución
        self.thread_pool: Optional[concurrent.futures.ThreadPoolExecutor] = None
        self.process_pool: Optional[concurrent.futures.ProcessPoolExecutor] = None
        
        # Estadísticas
        self.stats = {
            'tasks_executed': 0,
            'tasks_failed': 0,
            'total_execution_time': 0.0,
            'average_execution_time': 0.0
        }
    
    def execute_parallel(self, tasks: List[Tuple[Callable, tuple, dict]], 
                        priorities: Optional[List[str]] = None) -> List[TaskResult]:
        """
        Ejecutar tareas en paralelo
        
        Args:
            tasks: Lista de (función, args, kwargs)
            priorities: Lista de prioridades para cada tarea
            
        Returns:
            Lista de resultados de tareas
        """
        if not tasks:
            return []
        
        # Verificar recursos
        if not self.resource_monitor.check_resources(self.config):
            self.logger.warning("Resource constraints detected, reducing parallelism")
            self.config.max_workers = max(1, self.config.max_workers // 2)
        
        with PerformanceTimer("parallel_execution"):
            if self.config.mode == ExecutionMode.THREAD_POOL:
                return self._execute_with_threads(tasks, priorities)
            elif self.config.mode == ExecutionMode.PROCESS_POOL:
                return self._execute_with_processes(tasks, priorities)
            elif self.config.mode == ExecutionMode.ASYNC_CONCURRENT:
                return self._execute_with_async(tasks, priorities)
            elif self.config.mode == ExecutionMode.HYBRID:
                return self._execute_hybrid(tasks, priorities)
            else:
                raise ValueError(f"Unsupported execution mode: {self.config.mode}")
    
    def execute_plugins_parallel(self, challenge_data: ChallengeData, 
                                plugins: List[Tuple[str, Any, float]]) -> List[SolutionResult]:
        """
        Ejecutar plugins en paralelo para un desafío
        
        Args:
            challenge_data: Datos del desafío
            plugins: Lista de (nombre, plugin, confianza)
            
        Returns:
            Lista de resultados de plugins
        """
        # Crear tareas para plugins
        tasks = []
        priorities = []
        
        for plugin_name, plugin, confidence in plugins:
            task = (self._execute_plugin_safe, (plugin, challenge_data), {'plugin_name': plugin_name})
            tasks.append(task)
            
            # Asignar prioridad basada en confianza
            if confidence > 0.8:
                priorities.append("high")
            elif confidence > 0.5:
                priorities.append("normal")
            else:
                priorities.append("low")
        
        # Ejecutar en paralelo
        results = self.execute_parallel(tasks, priorities)
        
        # Convertir a SolutionResult
        solution_results = []
        for i, result in enumerate(results):
            if result.success and isinstance(result.result, SolutionResult):
                solution_results.append(result.result)
            else:
                # Crear resultado de fallo
                plugin_name = plugins[i][0]
                error_msg = str(result.error) if result.error else "Plugin execution failed"
                
                solution_results.append(SolutionResult(
                    success=False,
                    error_message=error_msg,
                    plugin_name=plugin_name,
                    execution_time=result.execution_time
                ))
        
        return solution_results
    
    def _execute_with_threads(self, tasks: List[Tuple[Callable, tuple, dict]], 
                             priorities: Optional[List[str]] = None) -> List[TaskResult]:
        """Ejecutar con ThreadPoolExecutor"""
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Enviar tareas
            future_to_task = {}
            for i, (func, args, kwargs) in enumerate(tasks):
                task_id = f"task_{i}"
                future = executor.submit(self._execute_task_safe, task_id, func, args, kwargs)
                future_to_task[future] = task_id
            
            # Recopilar resultados
            for future in concurrent.futures.as_completed(future_to_task, timeout=self.config.timeout):
                try:
                    result = future.result()
                    results.append(result)
                except concurrent.futures.TimeoutError:
                    task_id = future_to_task[future]
                    results.append(TaskResult(
                        task_id=task_id,
                        success=False,
                        result=None,
                        execution_time=self.config.timeout or 0,
                        error=TimeoutError("Task timed out")
                    ))
                except Exception as e:
                    task_id = future_to_task[future]
                    results.append(TaskResult(
                        task_id=task_id,
                        success=False,
                        result=None,
                        execution_time=0,
                        error=e
                    ))
        
        return results
    
    def _execute_with_processes(self, tasks: List[Tuple[Callable, tuple, dict]], 
                               priorities: Optional[List[str]] = None) -> List[TaskResult]:
        """Ejecutar con ProcessPoolExecutor"""
        results = []
        
        # Filtrar tareas que pueden ejecutarse en procesos separados
        serializable_tasks = []
        for i, (func, args, kwargs) in enumerate(tasks):
            try:
                # Verificar si la función es serializable
                import pickle
                pickle.dumps(func)
                serializable_tasks.append((i, func, args, kwargs))
            except Exception:
                # Tarea no serializable, ejecutar en thread principal
                task_id = f"task_{i}"
                result = self._execute_task_safe(task_id, func, args, kwargs)
                results.append(result)
        
        if serializable_tasks:
            with concurrent.futures.ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_task = {}
                for i, func, args, kwargs in serializable_tasks:
                    task_id = f"task_{i}"
                    future = executor.submit(self._execute_task_safe, task_id, func, args, kwargs)
                    future_to_task[future] = task_id
                
                # Recopilar resultados
                for future in concurrent.futures.as_completed(future_to_task, timeout=self.config.timeout):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        task_id = future_to_task[future]
                        results.append(TaskResult(
                            task_id=task_id,
                            success=False,
                            result=None,
                            execution_time=0,
                            error=e
                        ))
        
        return results
    
    def _execute_with_async(self, tasks: List[Tuple[Callable, tuple, dict]], 
                           priorities: Optional[List[str]] = None) -> List[TaskResult]:
        """Ejecutar con asyncio"""
        async def run_tasks():
            semaphore = asyncio.Semaphore(self.config.max_workers)
            
            async def run_task(task_id: str, func: Callable, args: tuple, kwargs: dict):
                async with semaphore:
                    return await asyncio.get_event_loop().run_in_executor(
                        None, self._execute_task_safe, task_id, func, args, kwargs
                    )
            
            # Crear tareas asíncronas
            async_tasks = []
            for i, (func, args, kwargs) in enumerate(tasks):
                task_id = f"task_{i}"
                async_task = run_task(task_id, func, args, kwargs)
                async_tasks.append(async_task)
            
            # Ejecutar todas las tareas
            return await asyncio.gather(*async_tasks, return_exceptions=True)
        
        # Ejecutar en loop de eventos
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        results = loop.run_until_complete(run_tasks())
        
        # Procesar resultados
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(TaskResult(
                    task_id=f"task_{i}",
                    success=False,
                    result=None,
                    execution_time=0,
                    error=result
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _execute_hybrid(self, tasks: List[Tuple[Callable, tuple, dict]], 
                       priorities: Optional[List[str]] = None) -> List[TaskResult]:
        """Ejecutar con modo híbrido (threads + processes)"""
        # Dividir tareas entre CPU-intensivas e I/O-intensivas
        cpu_tasks = []
        io_tasks = []
        
        for i, (func, args, kwargs) in enumerate(tasks):
            # Heurística simple: funciones con "compute", "calculate", "analyze" son CPU-intensivas
            func_name = getattr(func, '__name__', str(func)).lower()
            if any(keyword in func_name for keyword in ['compute', 'calculate', 'analyze', 'factor']):
                cpu_tasks.append((i, func, args, kwargs))
            else:
                io_tasks.append((i, func, args, kwargs))
        
        results = [None] * len(tasks)
        
        # Ejecutar tareas CPU-intensivas en procesos
        if cpu_tasks:
            cpu_task_list = [(func, args, kwargs) for _, func, args, kwargs in cpu_tasks]
            cpu_results = self._execute_with_processes(cpu_task_list)
            for (original_index, _, _, _), result in zip(cpu_tasks, cpu_results):
                results[original_index] = result
        
        # Ejecutar tareas I/O-intensivas en threads
        if io_tasks:
            io_task_list = [(func, args, kwargs) for _, func, args, kwargs in io_tasks]
            io_results = self._execute_with_threads(io_task_list)
            for (original_index, _, _, _), result in zip(io_tasks, io_results):
                results[original_index] = result
        
        return [r for r in results if r is not None]
    
    def _execute_task_safe(self, task_id: str, func: Callable, args: tuple, kwargs: dict) -> TaskResult:
        """Ejecutar tarea de forma segura con manejo de errores"""
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            self.stats['tasks_executed'] += 1
            self.stats['total_execution_time'] += execution_time
            self.stats['average_execution_time'] = (
                self.stats['total_execution_time'] / self.stats['tasks_executed']
            )
            
            return TaskResult(
                task_id=task_id,
                success=True,
                result=result,
                execution_time=execution_time,
                worker_id=threading.current_thread().name
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.stats['tasks_failed'] += 1
            
            self.logger.error(f"Task {task_id} failed: {e}")
            
            return TaskResult(
                task_id=task_id,
                success=False,
                result=None,
                execution_time=execution_time,
                error=e,
                worker_id=threading.current_thread().name
            )
    
    def _execute_plugin_safe(self, plugin: Any, challenge_data: ChallengeData, 
                           plugin_name: str) -> SolutionResult:
        """Ejecutar plugin de forma segura"""
        try:
            return plugin.solve(challenge_data)
        except Exception as e:
            return SolutionResult(
                success=False,
                error_message=str(e),
                plugin_name=plugin_name,
                execution_time=0
            )
    
    def _calculate_optimal_workers(self) -> int:
        """Calcular número óptimo de workers"""
        cpu_count = multiprocessing.cpu_count()
        
        # Considerar tipo de tareas y recursos disponibles
        if self.config.mode == ExecutionMode.PROCESS_POOL:
            # Para procesos, usar menos workers para evitar overhead
            return min(cpu_count, 4)
        elif self.config.mode == ExecutionMode.THREAD_POOL:
            # Para threads, puede usar más workers para I/O
            return min(cpu_count * 2, 8)
        else:
            # Por defecto
            return min(cpu_count, 6)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de ejecución"""
        return {
            **self.stats,
            'config': {
                'mode': self.config.mode.value,
                'max_workers': self.config.max_workers,
                'timeout': self.config.timeout
            },
            'queue_size': self.task_queue.size()
        }
    
    def shutdown(self) -> None:
        """Cerrar executor y limpiar recursos"""
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)
        if self.process_pool:
            self.process_pool.shutdown(wait=True)


# Instancia global del executor paralelo
parallel_executor = ParallelExecutor()