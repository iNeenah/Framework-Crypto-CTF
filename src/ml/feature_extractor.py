"""
Feature Extractor - Extracción de características para ML
"""

import re
import hashlib
from collections import Counter
from typing import Dict, List, Any, Optional
import numpy as np
from pathlib import Path

from ..models.data import ChallengeData, ChallengeType, FileInfo
from ..utils.logging import get_logger


class FeatureExtractor:
    """Extractor de características para clasificación de desafíos"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Patrones para diferentes tipos de desafíos
        self.crypto_patterns = {
            'rsa': [r'rsa', r'modulus', r'exponent', r'factorization', r'prime'],
            'basic_crypto': [r'caesar', r'vigenere', r'xor', r'base64', r'rot13'],
            'elliptic_curve': [r'elliptic', r'curve', r'ecc', r'ecdsa', r'point'],
            'network': [r'netcat', r'socket', r'tcp', r'udp', r'server', r'client'],
            'hash': [r'md5', r'sha', r'hash', r'digest', r'collision'],
            'steganography': [r'stego', r'hidden', r'lsb', r'image', r'audio']
        }
        
        # Extensiones de archivo relevantes
        self.file_extensions = {
            'text': ['.txt', '.md', '.py', '.c', '.cpp', '.java', '.js'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'],
            'audio': ['.wav', '.mp3', '.ogg', '.flac'],
            'archive': ['.zip', '.rar', '.tar', '.gz', '.7z'],
            'crypto': ['.pem', '.key', '.pub', '.crt'],
            'binary': ['.exe', '.bin', '.so', '.dll']
        }
    
    def extract_features(self, challenge_data: ChallengeData) -> Dict[str, float]:
        """
        Extraer características de un desafío.
        
        Args:
            challenge_data: Datos del desafío
            
        Returns:
            Dict[str, float]: Diccionario de características
        """
        features = {}
        
        # Características básicas
        features.update(self._extract_basic_features(challenge_data))
        
        # Características de archivos
        features.update(self._extract_file_features(challenge_data))
        
        # Características de contenido
        features.update(self._extract_content_features(challenge_data))
        
        # Características de patrones
        features.update(self._extract_pattern_features(challenge_data))
        
        # Características de metadatos
        features.update(self._extract_metadata_features(challenge_data))
        
        return features
    
    def _extract_basic_features(self, challenge_data: ChallengeData) -> Dict[str, float]:
        """Extraer características básicas"""
        features = {}
        
        # Número de archivos
        features['file_count'] = float(len(challenge_data.files))
        
        # Tamaño total
        total_size = sum(f.size for f in challenge_data.files)
        features['total_size'] = float(total_size)
        features['avg_file_size'] = float(total_size / max(1, len(challenge_data.files)))
        
        # Longitud del nombre
        features['name_length'] = float(len(challenge_data.name))
        
        # Longitud de la descripción
        features['description_length'] = float(len(challenge_data.description or ''))
        
        # Número de tags
        features['tag_count'] = float(len(challenge_data.tags))
        
        # Tiene información de red
        features['has_network_info'] = 1.0 if challenge_data.network_info else 0.0
        
        return features
    
    def _extract_file_features(self, challenge_data: ChallengeData) -> Dict[str, float]:
        """Extraer características de archivos"""
        features = {}
        
        # Contar tipos de archivo por extensión
        extension_counts = Counter()
        mime_counts = Counter()
        
        for file_info in challenge_data.files:
            # Extensiones
            ext = file_info.path.suffix.lower()
            extension_counts[ext] += 1
            
            # MIME types
            if file_info.mime_type:
                mime_category = file_info.mime_type.split('/')[0]
                mime_counts[mime_category] += 1
        
        # Características por tipo de extensión
        for category, extensions in self.file_extensions.items():
            count = sum(extension_counts.get(ext, 0) for ext in extensions)
            features[f'has_{category}_files'] = 1.0 if count > 0 else 0.0
            features[f'{category}_file_ratio'] = float(count / max(1, len(challenge_data.files)))
        
        # Características por MIME type
        for mime_type, count in mime_counts.items():
            features[f'mime_{mime_type}_count'] = float(count)
            features[f'mime_{mime_type}_ratio'] = float(count / max(1, len(challenge_data.files)))
        
        # Diversidad de tipos de archivo
        features['file_type_diversity'] = float(len(extension_counts))
        
        return features
    
    def _extract_content_features(self, challenge_data: ChallengeData) -> Dict[str, float]:
        """Extraer características de contenido"""
        features = {}
        
        # Analizar contenido de archivos de texto
        text_contents = []
        for file_info in challenge_data.files:
            if self._is_text_file(file_info):
                content = self._read_file_content(file_info.path)
                if content:
                    text_contents.append(content)
        
        if text_contents:
            combined_content = ' '.join(text_contents).lower()
            
            # Características de texto
            features['total_text_length'] = float(len(combined_content))
            features['word_count'] = float(len(combined_content.split()))
            features['unique_chars'] = float(len(set(combined_content)))
            
            # Entropía del texto
            features['text_entropy'] = self._calculate_entropy(combined_content)
            
            # Ratio de caracteres especiales
            special_chars = sum(1 for c in combined_content if not c.isalnum() and not c.isspace())
            features['special_char_ratio'] = float(special_chars / max(1, len(combined_content)))
            
            # Detección de posibles datos codificados
            features['looks_like_base64'] = 1.0 if self._looks_like_base64(combined_content) else 0.0
            features['looks_like_hex'] = 1.0 if self._looks_like_hex(combined_content) else 0.0
            
            # Números grandes (posibles parámetros criptográficos)
            large_numbers = re.findall(r'\b\d{20,}\b', combined_content)
            features['has_large_numbers'] = 1.0 if large_numbers else 0.0
            features['large_number_count'] = float(len(large_numbers))
        else:
            # Sin contenido de texto
            for key in ['total_text_length', 'word_count', 'unique_chars', 'text_entropy',
                       'special_char_ratio', 'looks_like_base64', 'looks_like_hex',
                       'has_large_numbers', 'large_number_count']:
                features[key] = 0.0
        
        return features
    
    def _extract_pattern_features(self, challenge_data: ChallengeData) -> Dict[str, float]:
        """Extraer características basadas en patrones"""
        features = {}
        
        # Combinar todo el texto disponible
        all_text = []
        all_text.append(challenge_data.name.lower())
        if challenge_data.description:
            all_text.append(challenge_data.description.lower())
        all_text.extend(challenge_data.tags)
        
        # Agregar contenido de archivos
        for file_info in challenge_data.files:
            all_text.append(file_info.path.name.lower())
            if self._is_text_file(file_info):
                content = self._read_file_content(file_info.path)
                if content:
                    all_text.append(content.lower())
        
        combined_text = ' '.join(all_text)
        
        # Buscar patrones específicos
        for category, patterns in self.crypto_patterns.items():
            pattern_count = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, combined_text, re.IGNORECASE))
                pattern_count += matches
            
            features[f'{category}_pattern_count'] = float(pattern_count)
            features[f'has_{category}_patterns'] = 1.0 if pattern_count > 0 else 0.0
        
        return features
    
    def _extract_metadata_features(self, challenge_data: ChallengeData) -> Dict[str, float]:
        """Extraer características de metadatos"""
        features = {}
        
        if challenge_data.metadata:
            metadata = challenge_data.metadata
            
            # Características de metadatos existentes
            features['has_executables'] = 1.0 if metadata.get('has_executables', False) else 0.0
            features['has_images'] = 1.0 if metadata.get('has_images', False) else 0.0
            features['has_documents'] = 1.0 if metadata.get('has_documents', False) else 0.0
            
            # Diversidad de tipos de archivo
            file_types = metadata.get('file_types', {})
            features['file_type_count'] = float(len(file_types))
            
            # Extensiones únicas
            extensions = metadata.get('extensions', [])
            features['unique_extensions'] = float(len(extensions))
        else:
            # Sin metadatos
            for key in ['has_executables', 'has_images', 'has_documents',
                       'file_type_count', 'unique_extensions']:
                features[key] = 0.0
        
        return features
    
    def _is_text_file(self, file_info: FileInfo) -> bool:
        """Verificar si es archivo de texto"""
        if file_info.mime_type and 'text' in file_info.mime_type:
            return True
        
        text_extensions = {'.txt', '.md', '.py', '.c', '.cpp', '.java', '.js', '.html', '.xml', '.json'}
        return file_info.path.suffix.lower() in text_extensions
    
    def _read_file_content(self, file_path: Path, max_size: int = 1024 * 1024) -> Optional[str]:
        """Leer contenido de archivo de texto"""
        try:
            if file_path.stat().st_size > max_size:
                return None
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            return None
    
    def _calculate_entropy(self, text: str) -> float:
        """Calcular entropía de Shannon del texto"""
        if not text:
            return 0.0
        
        # Contar frecuencias de caracteres
        char_counts = Counter(text)
        text_length = len(text)
        
        # Calcular entropía
        entropy = 0.0
        for count in char_counts.values():
            probability = count / text_length
            if probability > 0:
                entropy -= probability * np.log2(probability)
        
        return entropy
    
    def _looks_like_base64(self, text: str) -> bool:
        """Verificar si el texto parece Base64"""
        # Buscar secuencias que parezcan Base64
        base64_pattern = r'[A-Za-z0-9+/]{20,}={0,2}'
        matches = re.findall(base64_pattern, text)
        
        # Verificar si hay suficientes coincidencias
        total_base64_chars = sum(len(match) for match in matches)
        return total_base64_chars > len(text) * 0.1  # Al menos 10% del texto
    
    def _looks_like_hex(self, text: str) -> bool:
        """Verificar si el texto parece hexadecimal"""
        # Buscar secuencias hexadecimales
        hex_pattern = r'[0-9a-fA-F]{20,}'
        matches = re.findall(hex_pattern, text)
        
        # Verificar si hay suficientes coincidencias
        total_hex_chars = sum(len(match) for match in matches)
        return total_hex_chars > len(text) * 0.1  # Al menos 10% del texto
    
    def get_feature_names(self) -> List[str]:
        """Obtener nombres de todas las características posibles"""
        feature_names = []
        
        # Características básicas
        basic_features = [
            'file_count', 'total_size', 'avg_file_size', 'name_length',
            'description_length', 'tag_count', 'has_network_info'
        ]
        feature_names.extend(basic_features)
        
        # Características de archivos
        for category in self.file_extensions.keys():
            feature_names.extend([f'has_{category}_files', f'{category}_file_ratio'])
        
        # MIME types comunes
        mime_types = ['text', 'image', 'application', 'audio', 'video']
        for mime_type in mime_types:
            feature_names.extend([f'mime_{mime_type}_count', f'mime_{mime_type}_ratio'])
        
        feature_names.append('file_type_diversity')
        
        # Características de contenido
        content_features = [
            'total_text_length', 'word_count', 'unique_chars', 'text_entropy',
            'special_char_ratio', 'looks_like_base64', 'looks_like_hex',
            'has_large_numbers', 'large_number_count'
        ]
        feature_names.extend(content_features)
        
        # Características de patrones
        for category in self.crypto_patterns.keys():
            feature_names.extend([f'{category}_pattern_count', f'has_{category}_patterns'])
        
        # Características de metadatos
        metadata_features = [
            'has_executables', 'has_images', 'has_documents',
            'file_type_count', 'unique_extensions'
        ]
        feature_names.extend(metadata_features)
        
        return feature_names
    
    def normalize_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """Normalizar características para ML"""
        normalized = features.copy()
        
        # Normalizar características numéricas grandes
        size_features = ['total_size', 'avg_file_size', 'total_text_length']
        for feature in size_features:
            if feature in normalized and normalized[feature] > 0:
                # Usar log para reducir el rango
                normalized[feature] = np.log10(normalized[feature] + 1)
        
        # Asegurar que todas las características estén en [0, 1] o sean conteos pequeños
        for key, value in normalized.items():
            if 'ratio' in key or key.startswith('has_') or key.startswith('looks_like_'):
                # Ya deberían estar en [0, 1]
                normalized[key] = max(0.0, min(1.0, value))
            elif 'count' in key and value > 100:
                # Normalizar conteos muy grandes
                normalized[key] = min(100.0, value)
        
        return normalized