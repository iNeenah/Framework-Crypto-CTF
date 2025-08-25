"""
Cache Manager for Performance Optimization
Implements intelligent caching for intermediate results and computations
"""

import pickle
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timedelta
import threading
import logging

from ..models.data import ChallengeData, SolutionResult
from ..utils.config import config


class CacheEntry:
    """Entrada individual del cache"""
    
    def __init__(self, key: str, value: Any, ttl: Optional[int] = None):
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl or config.cache.default_ttl
        self.access_count = 0
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """Verificar si la entrada ha expirado"""
        if self.ttl <= 0:  # TTL 0 = nunca expira
            return False
        return time.time() - self.created_at > self.ttl
    
    def access(self) -> Any:
        """Acceder al valor y actualizar estadísticas"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value
    
    def size_estimate(self) -> int:
        """Estimar tamaño en bytes"""
        try:
            return len(pickle.dumps(self.value))
        except:
            return 1024  # Estimación por defecto


class CacheManager:
    """Gestor de cache inteligente para optimización de performance"""
    
    def __init__(self, cache_dir: Optional[Path] = None, max_memory_mb: int = 100):
        self.cache_dir = cache_dir or Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.disk_cache_index: Dict[str, Dict] = {}
        
        self._lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        # Estadísticas
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'disk_reads': 0,
            'disk_writes': 0
        }
        
        # Cargar índice de cache en disco
        self._load_disk_index()
        
        # Limpiar entradas expiradas al inicializar
        self._cleanup_expired()
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache"""
        with self._lock:
            # Buscar en memoria primero
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if not entry.is_expired():
                    self.stats['hits'] += 1
                    return entry.access()
                else:
                    # Entrada expirada, eliminar
                    del self.memory_cache[key]
            
            # Buscar en disco
            if key in self.disk_cache_index:
                disk_entry = self.disk_cache_index[key]
                if time.time() - disk_entry['created_at'] <= disk_entry['ttl']:
                    try:
                        value = self._load_from_disk(key)
                        if value is not None:
                            # Promover a memoria si hay espacio
                            self._promote_to_memory(key, value, disk_entry['ttl'])
                            self.stats['hits'] += 1
                            self.stats['disk_reads'] += 1
                            return value
                    except Exception as e:
                        self.logger.warning(f"Error loading from disk cache: {e}")
                        # Eliminar entrada corrupta
                        self._remove_from_disk(key)
            
            self.stats['misses'] += 1
            return None
    
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Almacenar valor en cache"""
        with self._lock:
            entry = CacheEntry(key, value, ttl)
            
            # Verificar si cabe en memoria
            if self._can_fit_in_memory(entry):
                self.memory_cache[key] = entry
                self._ensure_memory_limit()
            else:
                # Almacenar en disco
                self._store_to_disk(key, value, ttl or config.cache.default_ttl)
    
    def invalidate(self, key: str) -> bool:
        """Invalidar entrada específica"""
        with self._lock:
            found = False
            
            if key in self.memory_cache:
                del self.memory_cache[key]
                found = True
            
            if key in self.disk_cache_index:
                self._remove_from_disk(key)
                found = True
            
            return found
    
    def clear(self) -> None:
        """Limpiar todo el cache"""
        with self._lock:
            self.memory_cache.clear()
            self.disk_cache_index.clear()
            
            # Limpiar archivos de disco
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    self.logger.warning(f"Error removing cache file {cache_file}: {e}")
            
            self._save_disk_index()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        with self._lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            memory_usage = sum(entry.size_estimate() for entry in self.memory_cache.values())
            
            return {
                'hit_rate': hit_rate,
                'total_requests': total_requests,
                'memory_entries': len(self.memory_cache),
                'disk_entries': len(self.disk_cache_index),
                'memory_usage_mb': memory_usage / 1024 / 1024,
                'memory_limit_mb': self.max_memory_bytes / 1024 / 1024,
                **self.stats
            }
    
    def cleanup_expired(self) -> int:
        """Limpiar entradas expiradas"""
        with self._lock:
            return self._cleanup_expired()
    
    def _cleanup_expired(self) -> int:
        """Limpiar entradas expiradas (interno)"""
        expired_count = 0
        
        # Limpiar memoria
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
            expired_count += 1
        
        # Limpiar disco
        current_time = time.time()
        expired_disk_keys = [
            key for key, entry in self.disk_cache_index.items()
            if current_time - entry['created_at'] > entry['ttl']
        ]
        
        for key in expired_disk_keys:
            self._remove_from_disk(key)
            expired_count += 1
        
        return expired_count
    
    def _can_fit_in_memory(self, entry: CacheEntry) -> bool:
        """Verificar si una entrada cabe en memoria"""
        current_usage = sum(e.size_estimate() for e in self.memory_cache.values())
        entry_size = entry.size_estimate()
        return current_usage + entry_size <= self.max_memory_bytes
    
    def _ensure_memory_limit(self) -> None:
        """Asegurar que el uso de memoria esté dentro del límite"""
        while True:
            current_usage = sum(e.size_estimate() for e in self.memory_cache.values())
            if current_usage <= self.max_memory_bytes:
                break
            
            # Encontrar entrada menos usada para evicción (LRU)
            if not self.memory_cache:
                break
            
            lru_key = min(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k].last_accessed
            )
            
            # Mover a disco antes de evictar
            entry = self.memory_cache[lru_key]
            self._store_to_disk(lru_key, entry.value, entry.ttl)
            
            del self.memory_cache[lru_key]
            self.stats['evictions'] += 1
    
    def _promote_to_memory(self, key: str, value: Any, ttl: int) -> None:
        """Promover entrada de disco a memoria"""
        entry = CacheEntry(key, value, ttl)
        if self._can_fit_in_memory(entry):
            self.memory_cache[key] = entry
            self._ensure_memory_limit()
    
    def _store_to_disk(self, key: str, value: Any, ttl: int) -> None:
        """Almacenar valor en disco"""
        try:
            cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
            
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
            
            self.disk_cache_index[key] = {
                'file': cache_file.name,
                'created_at': time.time(),
                'ttl': ttl
            }
            
            self._save_disk_index()
            self.stats['disk_writes'] += 1
            
        except Exception as e:
            self.logger.error(f"Error storing to disk cache: {e}")
    
    def _load_from_disk(self, key: str) -> Optional[Any]:
        """Cargar valor desde disco"""
        if key not in self.disk_cache_index:
            return None
        
        try:
            cache_file = self.cache_dir / self.disk_cache_index[key]['file']
            
            if not cache_file.exists():
                # Archivo no existe, limpiar índice
                del self.disk_cache_index[key]
                self._save_disk_index()
                return None
            
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
                
        except Exception as e:
            self.logger.error(f"Error loading from disk cache: {e}")
            return None
    
    def _remove_from_disk(self, key: str) -> None:
        """Eliminar entrada del disco"""
        if key not in self.disk_cache_index:
            return
        
        try:
            cache_file = self.cache_dir / self.disk_cache_index[key]['file']
            if cache_file.exists():
                cache_file.unlink()
        except Exception as e:
            self.logger.warning(f"Error removing disk cache file: {e}")
        
        del self.disk_cache_index[key]
        self._save_disk_index()
    
    def _hash_key(self, key: str) -> str:
        """Generar hash para clave"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def _load_disk_index(self) -> None:
        """Cargar índice de cache en disco"""
        index_file = self.cache_dir / "cache_index.json"
        
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    self.disk_cache_index = json.load(f)
            except Exception as e:
                self.logger.warning(f"Error loading disk cache index: {e}")
                self.disk_cache_index = {}
    
    def _save_disk_index(self) -> None:
        """Guardar índice de cache en disco"""
        index_file = self.cache_dir / "cache_index.json"
        
        try:
            with open(index_file, 'w') as f:
                json.dump(self.disk_cache_index, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving disk cache index: {e}")


# Instancia global del cache manager
cache_manager = CacheManager()


def cached(ttl: Optional[int] = None, key_func: Optional[callable] = None):
    """
    Decorador para cachear resultados de funciones
    
    Args:
        ttl: Tiempo de vida en segundos
        key_func: Función para generar clave de cache personalizada
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generar clave de cache
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Clave por defecto basada en función y argumentos
                func_name = f"{func.__module__}.{func.__name__}"
                args_str = str(args) + str(sorted(kwargs.items()))
                cache_key = f"{func_name}:{hashlib.md5(args_str.encode()).hexdigest()}"
            
            # Intentar obtener del cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            cache_manager.put(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_challenge_analysis(challenge_data: ChallengeData) -> str:
    """Generar clave de cache para análisis de desafío"""
    # Usar hash de archivos y metadatos para generar clave única
    content_hash = hashlib.md5()
    
    for file_info in challenge_data.files:
        if file_info.hash_sha256:
            content_hash.update(file_info.hash_sha256.encode())
        else:
            content_hash.update(str(file_info.path).encode())
    
    if challenge_data.description:
        content_hash.update(challenge_data.description.encode())
    
    return f"challenge_analysis:{content_hash.hexdigest()}"


def cache_plugin_result(challenge_data: ChallengeData, plugin_name: str) -> str:
    """Generar clave de cache para resultado de plugin"""
    challenge_key = cache_challenge_analysis(challenge_data)
    return f"plugin_result:{plugin_name}:{challenge_key.split(':')[1]}"