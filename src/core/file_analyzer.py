"""
File Analyzer - Analizador de archivos para Crypto CTF Solver
"""

import os
import hashlib
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
import shutil
import tempfile
import zipfile
import tarfile
try:
    import py7zr
    HAS_7Z = True
except ImportError:
    HAS_7Z = False
try:
    import rarfile
    HAS_RAR = True
except ImportError:
    HAS_RAR = False
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
import logging

from ..models.data import ChallengeData, FileInfo, ChallengeType
from ..models.exceptions import FileExtractionError, ValidationError
from ..utils.logging import get_logger


class FileAnalyzer:
    """Analizador de archivos y extractor de contenido comprimido"""
    
    def __init__(self, work_dir: Optional[str] = None):
        self.logger = get_logger(__name__)
        self.work_dir = Path(work_dir) if work_dir else Path("challenges/extracted")
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar rarfile para usar unrar si está disponible
        if HAS_RAR:
            rarfile.UNRAR_TOOL = self._find_unrar_tool()
        
        # Extensiones soportadas
        self.supported_archives = {
            '.zip': self._extract_zip,
            '.rar': self._extract_rar,
            '.tar': self._extract_tar,
            '.tar.gz': self._extract_tar,
            '.tgz': self._extract_tar,
            '.tar.bz2': self._extract_tar,
            '.tar.xz': self._extract_tar,
            '.7z': self._extract_7z,
        }
        
        # Patrones para detección de tipo de desafío
        self.challenge_patterns = {
            ChallengeType.RSA: [
                'rsa', 'public_key', 'private_key', 'modulus', 'exponent',
                'factorization', 'wiener', 'hastad', 'common_modulus'
            ],
            ChallengeType.BASIC_CRYPTO: [
                'caesar', 'vigenere', 'substitution', 'frequency',
                'xor', 'base64', 'rot13', 'atbash'
            ],
            ChallengeType.ELLIPTIC_CURVE: [
                'elliptic', 'curve', 'ecc', 'ecdsa', 'point',
                'smart_attack', 'invalid_curve'
            ],
            ChallengeType.NETWORK: [
                'socket', 'netcat', 'nc', 'server', 'client',
                'tcp', 'udp', 'port', 'connect'
            ]
        }
    
    def _find_unrar_tool(self) -> Optional[str]:
        """Buscar herramienta unrar en el sistema"""
        possible_paths = [
            'unrar',
            '/usr/bin/unrar',
            '/usr/local/bin/unrar',
            'C:\\Program Files\\WinRAR\\unrar.exe',
            'C:\\Program Files (x86)\\WinRAR\\unrar.exe'
        ]
        
        for path in possible_paths:
            if shutil.which(path):
                return path
        
        self.logger.warning("unrar no encontrado. Los archivos RAR no se podrán extraer.")
        return None
    
    def analyze_file(self, file_path: Union[str, Path]) -> ChallengeData:
        """Analizar un archivo y crear ChallengeData"""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        self.logger.info(f"Analizando archivo: {file_path}")
        
        # Crear ID único basado en el nombre del archivo
        challenge_id = self._generate_challenge_id(file_path)
        
        # Crear ChallengeData inicial
        challenge = ChallengeData(
            id=challenge_id,
            name=file_path.stem,
            description=f"Desafío extraído de {file_path.name}"
        )
        
        # Verificar si es archivo comprimido
        if self._is_archive(file_path):
            self.logger.info(f"Archivo comprimido detectado: {file_path.suffix}")
            extracted_files = self._extract_archive(file_path, challenge_id)
            
            # Analizar archivos extraídos
            for extracted_file in extracted_files:
                file_info = self._analyze_single_file(extracted_file)
                file_info.extracted_from = str(file_path)
                challenge.files.append(file_info)
        else:
            # Analizar archivo individual
            file_info = self._analyze_single_file(file_path)
            challenge.files.append(file_info)
        
        # Detectar tipo de desafío
        challenge.challenge_type = self._detect_challenge_type(challenge)
        
        # Extraer metadatos adicionales
        challenge.metadata = self._extract_metadata(challenge)
        
        # Organizar archivos por tipo
        self._organize_files(challenge)
        
        self.logger.info(f"Análisis completado. Tipo detectado: {challenge.challenge_type}")
        return challenge
    
    def _generate_challenge_id(self, file_path: Path) -> str:
        """Generar ID único para el desafío"""
        # Usar hash del nombre y timestamp
        import time
        content = f"{file_path.name}_{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _is_archive(self, file_path: Path) -> bool:
        """Verificar si el archivo es un archivo comprimido"""
        suffix = file_path.suffix.lower()
        
        # Verificar extensiones compuestas como .tar.gz
        if file_path.name.lower().endswith(('.tar.gz', '.tar.bz2', '.tar.xz')):
            return True
        
        return suffix in self.supported_archives
    
    def _extract_archive(self, archive_path: Path, challenge_id: str) -> List[Path]:
        """Extraer archivo comprimido"""
        extract_dir = self.work_dir / challenge_id
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Extrayendo a: {extract_dir}")
        
        try:
            # Determinar método de extracción
            if archive_path.name.lower().endswith(('.tar.gz', '.tar.bz2', '.tar.xz')):
                extractor = self.supported_archives['.tar']
            else:
                suffix = archive_path.suffix.lower()
                extractor = self.supported_archives.get(suffix)
            
            if not extractor:
                raise FileExtractionError(f"Formato no soportado: {archive_path.suffix}")
            
            # Extraer archivo
            extracted_files = extractor(archive_path, extract_dir)
            
            self.logger.info(f"Extraídos {len(extracted_files)} archivos")
            return extracted_files
            
        except Exception as e:
            raise FileExtractionError(f"Error extrayendo {archive_path}: {str(e)}")
    
    def _extract_zip(self, archive_path: Path, extract_dir: Path) -> List[Path]:
        """Extraer archivo ZIP"""
        extracted_files = []
        
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            # Verificar archivos maliciosos (zip bombs, path traversal)
            self._validate_zip_safety(zip_ref)
            
            zip_ref.extractall(extract_dir)
            
            for file_info in zip_ref.filelist:
                if not file_info.is_dir():
                    extracted_path = extract_dir / file_info.filename
                    if extracted_path.exists():
                        extracted_files.append(extracted_path)
        
        return extracted_files
    
    def _extract_rar(self, archive_path: Path, extract_dir: Path) -> List[Path]:
        """Extraer archivo RAR"""
        if not HAS_RAR:
            raise FileExtractionError("rarfile library not available for RAR extraction")
        
        if not rarfile.UNRAR_TOOL:
            raise FileExtractionError("unrar no disponible para extraer archivos RAR")
        
        extracted_files = []
        
        with rarfile.RarFile(archive_path, 'r') as rar_ref:
            rar_ref.extractall(extract_dir)
            
            for file_info in rar_ref.infolist():
                if not file_info.is_dir():
                    extracted_path = extract_dir / file_info.filename
                    if extracted_path.exists():
                        extracted_files.append(extracted_path)
        
        return extracted_files
    
    def _extract_tar(self, archive_path: Path, extract_dir: Path) -> List[Path]:
        """Extraer archivo TAR (y variantes)"""
        extracted_files = []
        
        with tarfile.open(archive_path, 'r:*') as tar_ref:
            # Verificar seguridad
            self._validate_tar_safety(tar_ref)
            
            tar_ref.extractall(extract_dir)
            
            for member in tar_ref.getmembers():
                if member.isfile():
                    extracted_path = extract_dir / member.name
                    if extracted_path.exists():
                        extracted_files.append(extracted_path)
        
        return extracted_files
    
    def _extract_7z(self, archive_path: Path, extract_dir: Path) -> List[Path]:
        """Extraer archivo 7Z"""
        if not HAS_7Z:
            raise FileExtractionError("py7zr library not available for 7Z extraction")
        
        extracted_files = []
        
        with py7zr.SevenZipFile(archive_path, 'r') as sz_ref:
            sz_ref.extractall(extract_dir)
            
            # Listar archivos extraídos
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    extracted_files.append(Path(root) / file)
        
        return extracted_files
    
    def _validate_zip_safety(self, zip_ref: zipfile.ZipFile) -> None:
        """Validar seguridad del archivo ZIP"""
        total_size = 0
        max_size = 1024 * 1024 * 1024  # 1GB límite
        
        for file_info in zip_ref.filelist:
            # Verificar path traversal
            if '..' in file_info.filename or file_info.filename.startswith('/'):
                raise FileExtractionError(f"Archivo peligroso detectado: {file_info.filename}")
            
            # Verificar tamaño total
            total_size += file_info.file_size
            if total_size > max_size:
                raise FileExtractionError("Archivo demasiado grande (posible zip bomb)")
    
    def _validate_tar_safety(self, tar_ref: tarfile.TarFile) -> None:
        """Validar seguridad del archivo TAR"""
        for member in tar_ref.getmembers():
            # Verificar path traversal
            if '..' in member.name or member.name.startswith('/'):
                raise FileExtractionError(f"Archivo peligroso detectado: {member.name}")
            
            # Verificar enlaces simbólicos peligrosos
            if member.issym() or member.islnk():
                if '..' in member.linkname or member.linkname.startswith('/'):
                    raise FileExtractionError(f"Enlace peligroso detectado: {member.linkname}")
    
    def _analyze_single_file(self, file_path: Path) -> FileInfo:
        """Analizar un archivo individual"""
        try:
            # Obtener información básica
            stat = file_path.stat()
            
            # Detectar tipo MIME
            mime_type = None
            try:
                if HAS_MAGIC:
                    mime_type = magic.from_file(str(file_path), mime=True)
                else:
                    # Fallback to mimetypes module
                    import mimetypes
                    mime_type, _ = mimetypes.guess_type(str(file_path))
                    if not mime_type:
                        mime_type = "application/octet-stream"
            except Exception as e:
                self.logger.warning(f"Error detectando MIME type para {file_path}: {e}")
                mime_type = "application/octet-stream"
            
            # Calcular hashes
            md5_hash, sha256_hash = self._calculate_hashes(file_path)
            
            return FileInfo(
                path=file_path,
                size=stat.st_size,
                mime_type=mime_type,
                hash_md5=md5_hash,
                hash_sha256=sha256_hash
            )
            
        except Exception as e:
            self.logger.error(f"Error analizando archivo {file_path}: {e}")
            # Retornar FileInfo básico en caso de error
            return FileInfo(
                path=file_path,
                size=file_path.stat().st_size if file_path.exists() else 0
            )
    
    def _calculate_hashes(self, file_path: Path) -> Tuple[str, str]:
        """Calcular hashes MD5 y SHA256 del archivo"""
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                # Leer en chunks para archivos grandes
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
                    sha256_hash.update(chunk)
            
            return md5_hash.hexdigest(), sha256_hash.hexdigest()
            
        except Exception as e:
            self.logger.warning(f"Error calculando hashes para {file_path}: {e}")
            return "", ""
    
    def _detect_challenge_type(self, challenge: ChallengeData) -> ChallengeType:
        """Detectar tipo de desafío basado en contenido"""
        scores = {challenge_type: 0 for challenge_type in ChallengeType}
        
        # Analizar nombres de archivos
        for file_info in challenge.files:
            filename_lower = file_info.path.name.lower()
            
            for challenge_type, patterns in self.challenge_patterns.items():
                for pattern in patterns:
                    if pattern in filename_lower:
                        scores[challenge_type] += 2
        
        # Analizar contenido de archivos de texto
        for file_info in challenge.files:
            if self._is_text_file(file_info):
                content = self._read_file_content(file_info.path)
                if content:
                    content_lower = content.lower()
                    
                    for challenge_type, patterns in self.challenge_patterns.items():
                        for pattern in patterns:
                            if pattern in content_lower:
                                scores[challenge_type] += 1
        
        # Retornar tipo con mayor puntuación
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return ChallengeType.UNKNOWN
    
    def _is_text_file(self, file_info: FileInfo) -> bool:
        """Verificar si el archivo es de texto"""
        if file_info.mime_type:
            return file_info.mime_type.startswith('text/') or 'text' in file_info.mime_type
        
        # Verificar por extensión
        text_extensions = {'.txt', '.py', '.c', '.cpp', '.java', '.js', '.html', '.xml', '.json', '.md'}
        return file_info.path.suffix.lower() in text_extensions
    
    def _read_file_content(self, file_path: Path, max_size: int = 1024 * 1024) -> Optional[str]:
        """Leer contenido de archivo de texto"""
        try:
            if file_path.stat().st_size > max_size:
                self.logger.warning(f"Archivo demasiado grande para análisis de contenido: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
                
        except Exception as e:
            self.logger.warning(f"Error leyendo contenido de {file_path}: {e}")
            return None
    
    def _extract_metadata(self, challenge: ChallengeData) -> Dict[str, Any]:
        """Extraer metadatos adicionales del desafío"""
        metadata = {
            'total_files': len(challenge.files),
            'total_size': sum(f.size for f in challenge.files),
            'file_types': {},
            'extensions': set(),
            'has_executables': False,
            'has_images': False,
            'has_documents': False
        }
        
        for file_info in challenge.files:
            # Contar tipos MIME
            if file_info.mime_type:
                mime_category = file_info.mime_type.split('/')[0]
                metadata['file_types'][mime_category] = metadata['file_types'].get(mime_category, 0) + 1
                
                # Detectar categorías especiales
                if mime_category == 'application' and any(x in file_info.mime_type for x in ['executable', 'x-executable']):
                    metadata['has_executables'] = True
                elif mime_category == 'image':
                    metadata['has_images'] = True
                elif 'document' in file_info.mime_type or mime_category == 'application':
                    metadata['has_documents'] = True
            
            # Recopilar extensiones
            if file_info.path.suffix:
                metadata['extensions'].add(file_info.path.suffix.lower())
        
        # Convertir set a lista para serialización
        metadata['extensions'] = list(metadata['extensions'])
        
        return metadata
    
    def _organize_files(self, challenge: ChallengeData) -> None:
        """Organizar archivos por categorías"""
        # Agregar tags basados en tipos de archivo
        tags = set(challenge.tags)
        
        for file_info in challenge.files:
            if file_info.mime_type:
                if 'image' in file_info.mime_type:
                    tags.add('images')
                elif 'text' in file_info.mime_type:
                    tags.add('text')
                elif 'executable' in file_info.mime_type:
                    tags.add('executable')
                elif 'python' in file_info.mime_type or file_info.path.suffix == '.py':
                    tags.add('python')
        
        challenge.tags = list(tags)
    
    def cleanup_extracted_files(self, challenge_id: str) -> None:
        """Limpiar archivos extraídos de un desafío"""
        extract_dir = self.work_dir / challenge_id
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
            self.logger.info(f"Archivos extraídos limpiados: {extract_dir}")
    
    def get_supported_formats(self) -> List[str]:
        """Obtener lista de formatos soportados"""
        return list(self.supported_archives.keys())