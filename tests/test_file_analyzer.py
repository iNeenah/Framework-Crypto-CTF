"""
Tests para File Analyzer
"""

import pytest
import tempfile
import zipfile
import tarfile
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from src.core.file_analyzer import FileAnalyzer
from src.models.data import ChallengeType, FileInfo
from src.models.exceptions import FileExtractionError


class TestFileAnalyzer:
    """Tests para FileAnalyzer"""
    
    @pytest.fixture
    def temp_dir(self):
        """Crear directorio temporal para tests"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    @pytest.fixture
    def file_analyzer(self, temp_dir):
        """Crear instancia de FileAnalyzer"""
        work_dir = temp_dir / "work"
        return FileAnalyzer(work_dir=str(work_dir))
    
    @pytest.fixture
    def sample_text_file(self, temp_dir):
        """Crear archivo de texto de muestra"""
        file_path = temp_dir / "sample.txt"
        with open(file_path, 'w') as f:
            f.write("This is a sample RSA challenge with public key and modulus")
        return file_path
    
    @pytest.fixture
    def sample_zip_file(self, temp_dir):
        """Crear archivo ZIP de muestra"""
        zip_path = temp_dir / "challenge.zip"
        
        # Crear archivos para el ZIP
        file1 = temp_dir / "rsa_key.txt"
        file2 = temp_dir / "cipher.txt"
        
        with open(file1, 'w') as f:
            f.write("RSA public key data")
        with open(file2, 'w') as f:
            f.write("Encrypted message")
        
        # Crear ZIP
        with zipfile.ZipFile(zip_path, 'w') as zip_ref:
            zip_ref.write(file1, file1.name)
            zip_ref.write(file2, file2.name)
        
        return zip_path
    
    def test_init(self, temp_dir):
        """Test inicialización de FileAnalyzer"""
        work_dir = temp_dir / "work"
        analyzer = FileAnalyzer(work_dir=str(work_dir))
        
        assert analyzer.work_dir == work_dir
        assert work_dir.exists()
        assert len(analyzer.supported_archives) > 0
    
    def test_generate_challenge_id(self, file_analyzer, sample_text_file):
        """Test generación de ID de desafío"""
        id1 = file_analyzer._generate_challenge_id(sample_text_file)
        id2 = file_analyzer._generate_challenge_id(sample_text_file)
        
        assert isinstance(id1, str)
        assert len(id1) == 12
        assert id1 != id2  # Deberían ser diferentes por timestamp
    
    def test_is_archive(self, file_analyzer, temp_dir):
        """Test detección de archivos comprimidos"""
        # Archivos comprimidos
        assert file_analyzer._is_archive(Path("test.zip"))
        assert file_analyzer._is_archive(Path("test.rar"))
        assert file_analyzer._is_archive(Path("test.tar.gz"))
        assert file_analyzer._is_archive(Path("test.7z"))
        
        # Archivos no comprimidos
        assert not file_analyzer._is_archive(Path("test.txt"))
        assert not file_analyzer._is_archive(Path("test.py"))
    
    @patch('magic.from_file')
    def test_analyze_single_file(self, mock_magic, file_analyzer, sample_text_file):
        """Test análisis de archivo individual"""
        mock_magic.return_value = "text/plain"
        
        file_info = file_analyzer._analyze_single_file(sample_text_file)
        
        assert isinstance(file_info, FileInfo)
        assert file_info.path == sample_text_file
        assert file_info.size > 0
        assert file_info.mime_type == "text/plain"
        assert file_info.hash_md5
        assert file_info.hash_sha256
    
    def test_calculate_hashes(self, file_analyzer, sample_text_file):
        """Test cálculo de hashes"""
        md5_hash, sha256_hash = file_analyzer._calculate_hashes(sample_text_file)
        
        assert len(md5_hash) == 32  # MD5 hex length
        assert len(sha256_hash) == 64  # SHA256 hex length
        assert md5_hash.isalnum()
        assert sha256_hash.isalnum()
    
    def test_detect_challenge_type_rsa(self, file_analyzer, temp_dir):
        """Test detección de tipo RSA"""
        # Crear archivo con contenido RSA
        rsa_file = temp_dir / "rsa_challenge.txt"
        with open(rsa_file, 'w') as f:
            f.write("RSA public key modulus exponent factorization")
        
        file_info = FileInfo(path=rsa_file, size=100, mime_type="text/plain")
        
        from src.models.data import ChallengeData
        challenge = ChallengeData(id="test", name="test", files=[file_info])
        
        challenge_type = file_analyzer._detect_challenge_type(challenge)
        assert challenge_type == ChallengeType.RSA
    
    def test_detect_challenge_type_basic_crypto(self, file_analyzer, temp_dir):
        """Test detección de tipo criptografía básica"""
        # Crear archivo con contenido de criptografía básica
        crypto_file = temp_dir / "caesar_cipher.txt"
        with open(crypto_file, 'w') as f:
            f.write("caesar cipher frequency analysis vigenere")
        
        file_info = FileInfo(path=crypto_file, size=100, mime_type="text/plain")
        
        from src.models.data import ChallengeData
        challenge = ChallengeData(id="test", name="test", files=[file_info])
        
        challenge_type = file_analyzer._detect_challenge_type(challenge)
        assert challenge_type == ChallengeType.BASIC_CRYPTO
    
    def test_is_text_file(self, file_analyzer):
        """Test detección de archivos de texto"""
        # Por MIME type
        text_file = FileInfo(path=Path("test.txt"), size=100, mime_type="text/plain")
        assert file_analyzer._is_text_file(text_file)
        
        # Por extensión
        py_file = FileInfo(path=Path("test.py"), size=100)
        assert file_analyzer._is_text_file(py_file)
        
        # Archivo binario
        bin_file = FileInfo(path=Path("test.bin"), size=100, mime_type="application/octet-stream")
        assert not file_analyzer._is_text_file(bin_file)
    
    def test_read_file_content(self, file_analyzer, sample_text_file):
        """Test lectura de contenido de archivo"""
        content = file_analyzer._read_file_content(sample_text_file)
        
        assert content is not None
        assert "RSA challenge" in content
        assert "public key" in content
    
    def test_read_file_content_large_file(self, file_analyzer, temp_dir):
        """Test lectura de archivo demasiado grande"""
        large_file = temp_dir / "large.txt"
        
        # Mock para simular archivo grande
        with patch.object(Path, 'stat') as mock_stat:
            mock_stat.return_value.st_size = 2 * 1024 * 1024  # 2MB
            
            content = file_analyzer._read_file_content(large_file)
            assert content is None
    
    @patch('magic.from_file')
    def test_analyze_file_single(self, mock_magic, file_analyzer, sample_text_file):
        """Test análisis de archivo individual (no comprimido)"""
        mock_magic.return_value = "text/plain"
        
        challenge = file_analyzer.analyze_file(sample_text_file)
        
        assert challenge.id
        assert challenge.name == sample_text_file.stem
        assert len(challenge.files) == 1
        assert challenge.challenge_type == ChallengeType.RSA  # Por contenido
        assert challenge.metadata['total_files'] == 1
    
    def test_analyze_file_nonexistent(self, file_analyzer):
        """Test análisis de archivo inexistente"""
        with pytest.raises(FileNotFoundError):
            file_analyzer.analyze_file("nonexistent.txt")
    
    def test_extract_zip(self, file_analyzer, sample_zip_file, temp_dir):
        """Test extracción de archivo ZIP"""
        extract_dir = temp_dir / "extract"
        extract_dir.mkdir()
        
        extracted_files = file_analyzer._extract_zip(sample_zip_file, extract_dir)
        
        assert len(extracted_files) == 2
        assert all(f.exists() for f in extracted_files)
        assert any("rsa_key.txt" in str(f) for f in extracted_files)
        assert any("cipher.txt" in str(f) for f in extracted_files)
    
    def test_validate_zip_safety_path_traversal(self, file_analyzer, temp_dir):
        """Test validación de seguridad ZIP - path traversal"""
        malicious_zip = temp_dir / "malicious.zip"
        
        with zipfile.ZipFile(malicious_zip, 'w') as zip_ref:
            # Crear entrada maliciosa con path traversal
            zip_info = zipfile.ZipInfo("../../../etc/passwd")
            zip_info.file_size = 100
            zip_ref.writestr(zip_info, "malicious content")
        
        with zipfile.ZipFile(malicious_zip, 'r') as zip_ref:
            with pytest.raises(FileExtractionError, match="Archivo peligroso detectado"):
                file_analyzer._validate_zip_safety(zip_ref)
    
    def test_validate_zip_safety_zip_bomb(self, file_analyzer, temp_dir):
        """Test validación de seguridad ZIP - zip bomb"""
        bomb_zip = temp_dir / "bomb.zip"
        
        with zipfile.ZipFile(bomb_zip, 'w') as zip_ref:
            # Crear entrada con tamaño excesivo
            zip_info = zipfile.ZipInfo("large_file.txt")
            zip_info.file_size = 2 * 1024 * 1024 * 1024  # 2GB
            zip_ref.writestr(zip_info, "small content")
        
        with zipfile.ZipFile(bomb_zip, 'r') as zip_ref:
            with pytest.raises(FileExtractionError, match="demasiado grande"):
                file_analyzer._validate_zip_safety(zip_ref)
    
    def test_extract_tar(self, file_analyzer, temp_dir):
        """Test extracción de archivo TAR"""
        # Crear archivo TAR
        tar_path = temp_dir / "test.tar"
        extract_dir = temp_dir / "extract"
        extract_dir.mkdir()
        
        # Crear archivos para el TAR
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        
        with open(file1, 'w') as f:
            f.write("content1")
        with open(file2, 'w') as f:
            f.write("content2")
        
        # Crear TAR
        with tarfile.open(tar_path, 'w') as tar_ref:
            tar_ref.add(file1, arcname=file1.name)
            tar_ref.add(file2, arcname=file2.name)
        
        # Extraer
        extracted_files = file_analyzer._extract_tar(tar_path, extract_dir)
        
        assert len(extracted_files) == 2
        assert all(f.exists() for f in extracted_files)
    
    def test_validate_tar_safety(self, file_analyzer, temp_dir):
        """Test validación de seguridad TAR"""
        malicious_tar = temp_dir / "malicious.tar"
        
        with tarfile.open(malicious_tar, 'w') as tar_ref:
            # Crear entrada maliciosa
            tar_info = tarfile.TarInfo("../../../etc/passwd")
            tar_info.size = 100
            tar_ref.addfile(tar_info, fileobj=None)
        
        with tarfile.open(malicious_tar, 'r') as tar_ref:
            with pytest.raises(FileExtractionError, match="Archivo peligroso detectado"):
                file_analyzer._validate_tar_safety(tar_ref)
    
    def test_extract_metadata(self, file_analyzer, temp_dir):
        """Test extracción de metadatos"""
        # Crear archivos de diferentes tipos
        files = [
            FileInfo(path=Path("test.txt"), size=100, mime_type="text/plain"),
            FileInfo(path=Path("test.jpg"), size=200, mime_type="image/jpeg"),
            FileInfo(path=Path("test.py"), size=150, mime_type="text/x-python"),
        ]
        
        from src.models.data import ChallengeData
        challenge = ChallengeData(id="test", name="test", files=files)
        
        metadata = file_analyzer._extract_metadata(challenge)
        
        assert metadata['total_files'] == 3
        assert metadata['total_size'] == 450
        assert 'text' in metadata['file_types']
        assert 'image' in metadata['file_types']
        assert '.txt' in metadata['extensions']
        assert '.jpg' in metadata['extensions']
        assert '.py' in metadata['extensions']
    
    def test_organize_files(self, file_analyzer):
        """Test organización de archivos"""
        files = [
            FileInfo(path=Path("test.txt"), size=100, mime_type="text/plain"),
            FileInfo(path=Path("test.jpg"), size=200, mime_type="image/jpeg"),
            FileInfo(path=Path("test.py"), size=150, mime_type="text/x-python"),
        ]
        
        from src.models.data import ChallengeData
        challenge = ChallengeData(id="test", name="test", files=files)
        
        file_analyzer._organize_files(challenge)
        
        assert 'images' in challenge.tags
        assert 'text' in challenge.tags
        assert 'python' in challenge.tags
    
    def test_cleanup_extracted_files(self, file_analyzer, temp_dir):
        """Test limpieza de archivos extraídos"""
        challenge_id = "test_challenge"
        extract_dir = file_analyzer.work_dir / challenge_id
        extract_dir.mkdir(parents=True)
        
        # Crear archivo de prueba
        test_file = extract_dir / "test.txt"
        test_file.write_text("test content")
        
        assert extract_dir.exists()
        assert test_file.exists()
        
        # Limpiar
        file_analyzer.cleanup_extracted_files(challenge_id)
        
        assert not extract_dir.exists()
    
    def test_get_supported_formats(self, file_analyzer):
        """Test obtener formatos soportados"""
        formats = file_analyzer.get_supported_formats()
        
        assert isinstance(formats, list)
        assert '.zip' in formats
        assert '.rar' in formats
        assert '.tar' in formats
        assert '.7z' in formats
    
    @patch('shutil.which')
    def test_find_unrar_tool_found(self, mock_which, temp_dir):
        """Test encontrar herramienta unrar"""
        mock_which.return_value = '/usr/bin/unrar'
        
        analyzer = FileAnalyzer(work_dir=str(temp_dir))
        result = analyzer._find_unrar_tool()
        
        assert result == '/usr/bin/unrar'
    
    @patch('shutil.which')
    def test_find_unrar_tool_not_found(self, mock_which, temp_dir):
        """Test no encontrar herramienta unrar"""
        mock_which.return_value = None
        
        analyzer = FileAnalyzer(work_dir=str(temp_dir))
        result = analyzer._find_unrar_tool()
        
        assert result is None
    
    def test_extract_archive_unsupported_format(self, file_analyzer, temp_dir):
        """Test extracción de formato no soportado"""
        unsupported_file = temp_dir / "test.unknown"
        unsupported_file.write_text("test content")
        
        with pytest.raises(FileExtractionError, match="Formato no soportado"):
            file_analyzer._extract_archive(unsupported_file, "test_id")


if __name__ == "__main__":
    pytest.main([__file__])