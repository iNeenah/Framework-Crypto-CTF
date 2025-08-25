"""
Modelos de datos centrales para Crypto CTF Solver
"""

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator


class ChallengeType(str, Enum):
    """Tipos de desafío soportados"""
    BASIC_CRYPTO = "basic_crypto"
    RSA = "rsa"
    ELLIPTIC_CURVE = "elliptic_curve"
    NETWORK = "network"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class DifficultyLevel(int, Enum):
    """Niveles de dificultad"""
    BEGINNER = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    EXPERT = 5


@dataclass
class NetworkInfo:
    """Información de conexión de red"""
    host: str
    port: int
    protocol: str = "tcp"
    timeout: int = 30
    ssl: bool = False
    credentials: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.protocol not in ["tcp", "udp", "http", "https"]:
            raise ValueError(f"Protocolo no soportado: {self.protocol}")
        
        if not (1 <= self.port <= 65535):
            raise ValueError(f"Puerto inválido: {self.port}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NetworkInfo':
        """Crear desde diccionario"""
        return cls(**data)


@dataclass
class FileInfo:
    """Información de archivo"""
    path: Path
    size: int
    mime_type: Optional[str] = None
    hash_md5: Optional[str] = None
    hash_sha256: Optional[str] = None
    extracted_from: Optional[str] = None
    
    def __post_init__(self):
        if isinstance(self.path, str):
            self.path = Path(self.path)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        data = asdict(self)
        data['path'] = str(self.path)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileInfo':
        """Crear desde diccionario"""
        return cls(**data)


@dataclass
class ChallengeData:
    """Datos de un desafío de criptografía/CTF"""
    id: str
    name: str
    files: List[FileInfo] = field(default_factory=list)
    network_info: Optional[NetworkInfo] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    challenge_type: Optional[ChallengeType] = None
    difficulty: Optional[DifficultyLevel] = None
    description: Optional[str] = None
    hints: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    
    def __post_init__(self):
        # Validar ID
        if not self.id or not isinstance(self.id, str):
            raise ValueError("ID del desafío debe ser una cadena no vacía")
        
        # Convertir strings a enums si es necesario
        if isinstance(self.challenge_type, str):
            try:
                self.challenge_type = ChallengeType(self.challenge_type)
            except ValueError:
                self.challenge_type = ChallengeType.UNKNOWN
        
        if isinstance(self.difficulty, int):
            try:
                self.difficulty = DifficultyLevel(self.difficulty)
            except ValueError:
                self.difficulty = None
    
    def add_file(self, file_path: Union[str, Path], **kwargs) -> None:
        """Agregar archivo al desafío"""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        file_info = FileInfo(
            path=file_path,
            size=file_path.stat().st_size,
            **kwargs
        )
        self.files.append(file_info)
    
    def get_files_by_extension(self, extension: str) -> List[FileInfo]:
        """Obtener archivos por extensión"""
        return [f for f in self.files if f.path.suffix.lower() == extension.lower()]
    
    def has_network_component(self) -> bool:
        """Verificar si tiene componente de red"""
        return self.network_info is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización"""
        data = {
            'id': self.id,
            'name': self.name,
            'files': [f.to_dict() for f in self.files],
            'network_info': self.network_info.to_dict() if self.network_info else None,
            'metadata': self.metadata,
            'challenge_type': self.challenge_type.value if self.challenge_type else None,
            'difficulty': self.difficulty.value if self.difficulty else None,
            'description': self.description,
            'hints': self.hints,
            'tags': self.tags,
            'created_at': self.created_at
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChallengeData':
        """Crear desde diccionario"""
        # Procesar archivos
        files = []
        if 'files' in data:
            files = [FileInfo.from_dict(f) for f in data['files']]
        
        # Procesar network_info
        network_info = None
        if data.get('network_info'):
            network_info = NetworkInfo.from_dict(data['network_info'])
        
        return cls(
            id=data['id'],
            name=data['name'],
            files=files,
            network_info=network_info,
            metadata=data.get('metadata', {}),
            challenge_type=data.get('challenge_type'),
            difficulty=data.get('difficulty'),
            description=data.get('description'),
            hints=data.get('hints', []),
            tags=data.get('tags', []),
            created_at=data.get('created_at', time.time())
        )
    
    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Guardar a archivo JSON"""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> 'ChallengeData':
        """Cargar desde archivo JSON"""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls.from_dict(data)


@dataclass
class SolutionResult:
    """Resultado de la resolución de un desafío"""
    success: bool
    flag: Optional[str] = None
    method_used: str = ""
    execution_time: float = 0.0
    confidence: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    intermediate_results: List[Dict[str, Any]] = field(default_factory=list)
    plugin_name: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        # Validar confidence
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence debe estar entre 0.0 y 1.0")
        
        # Si no hay éxito, no debería haber flag
        if not self.success and self.flag:
            raise ValueError("No puede haber flag si success es False")
    
    def add_intermediate_result(self, step: str, result: Any, confidence: float = 0.0) -> None:
        """Agregar resultado intermedio"""
        self.intermediate_results.append({
            'step': step,
            'result': result,
            'confidence': confidence,
            'timestamp': time.time()
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SolutionResult':
        """Crear desde diccionario"""
        return cls(**data)
    
    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Guardar resultado a archivo"""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> 'SolutionResult':
        """Cargar resultado desde archivo"""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls.from_dict(data)


@dataclass
class PluginInfo:
    """Información de un plugin"""
    name: str
    version: str
    description: str
    supported_types: List[ChallengeType]
    techniques: List[str] = field(default_factory=list)
    enabled: bool = True
    priority: int = 50  # 0-100, mayor = más prioridad
    
    def can_handle_type(self, challenge_type: ChallengeType) -> bool:
        """Verificar si puede manejar un tipo de desafío"""
        return challenge_type in self.supported_types or ChallengeType.MIXED in self.supported_types
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        data = asdict(self)
        data['supported_types'] = [t.value for t in self.supported_types]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginInfo':
        """Crear desde diccionario"""
        supported_types = [ChallengeType(t) for t in data.get('supported_types', [])]
        data_copy = data.copy()
        data_copy['supported_types'] = supported_types
        return cls(**data_copy)