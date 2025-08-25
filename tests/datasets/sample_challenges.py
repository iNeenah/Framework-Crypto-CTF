"""
Sample challenges dataset for testing
"""

import tempfile
import zipfile
from pathlib import Path
from typing import List, Dict, Any

from src.models.data import ChallengeData, ChallengeType, FileInfo


class SampleChallengeGenerator:
    """Generador de desafíos de muestra para testing"""
    
    @staticmethod
    def create_caesar_cipher_challenge(tmp_dir: Path) -> Path:
        """Crear desafío de cifrado César"""
        challenge_dir = tmp_dir / "caesar_challenge"
        challenge_dir.mkdir(exist_ok=True)
        
        # Archivo con texto cifrado
        cipher_file = challenge_dir / "cipher.txt"
        cipher_file.write_text("WKLV LV D FDHVDU FLSKHU ZLWK VKLIW 3")
        
        # Pista
        hint_file = challenge_dir / "hint.txt"
        hint_file.write_text("Caesar cipher with shift 3")
        
        # Crear ZIP
        zip_path = tmp_dir / "caesar_challenge.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.write(cipher_file, cipher_file.name)
            zf.write(hint_file, hint_file.name)
        
        return zip_path
    
    @staticmethod
    def create_rsa_challenge(tmp_dir: Path) -> Path:
        """Crear desafío RSA básico"""
        challenge_dir = tmp_dir / "rsa_challenge"
        challenge_dir.mkdir(exist_ok=True)
        
        # Clave pública simulada
        public_key = challenge_dir / "public_key.pem"
        public_key.write_text("""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1234567890abcdef
-----END PUBLIC KEY-----""")
        
        # Mensaje cifrado
        cipher_file = challenge_dir / "cipher.txt"
        cipher_file.write_text("Encrypted: 1234567890abcdef...")
        
        # Descripción
        desc_file = challenge_dir / "description.txt"
        desc_file.write_text("RSA challenge: decrypt the message")
        
        # Crear ZIP
        zip_path = tmp_dir / "rsa_challenge.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file_path in challenge_dir.iterdir():
                zf.write(file_path, file_path.name)
        
        return zip_path   
 
    @staticmethod
    def create_xor_challenge(tmp_dir: Path) -> Path:
        """Crear desafío XOR"""
        challenge_dir = tmp_dir / "xor_challenge"
        challenge_dir.mkdir(exist_ok=True)
        
        # Datos XOR
        xor_file = challenge_dir / "xor_data.txt"
        xor_file.write_text("1a2b3c4d5e6f")
        
        # Clave
        key_file = challenge_dir / "key.txt"
        key_file.write_text("Key: 0x42")
        
        # Crear ZIP
        zip_path = tmp_dir / "xor_challenge.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.write(xor_file, xor_file.name)
            zf.write(key_file, key_file.name)
        
        return zip_path
    
    @staticmethod
    def create_network_challenge_info() -> Dict[str, Any]:
        """Crear información de desafío de red"""
        return {
            'host': 'example.com',
            'port': 1337,
            'protocol': 'tcp',
            'description': 'Connect and solve the network challenge'
        }
    
    @staticmethod
    def get_sample_dataset(tmp_dir: Path) -> List[Path]:
        """Obtener dataset completo de muestras"""
        generator = SampleChallengeGenerator()
        
        challenges = [
            generator.create_caesar_cipher_challenge(tmp_dir),
            generator.create_rsa_challenge(tmp_dir),
            generator.create_xor_challenge(tmp_dir)
        ]
        
        return challenges


# Datos de desafíos históricos conocidos (para referencia)
HISTORICAL_CHALLENGES = {
    'picoctf_2019_caesar': {
        'type': ChallengeType.BASIC_CRYPTO,
        'description': 'Caesar cipher with unknown shift',
        'expected_flag': 'picoCTF{crossingtherubiconzaqjsscr}',
        'difficulty': 1
    },
    'picoctf_2019_rsa_pop_quiz': {
        'type': ChallengeType.RSA,
        'description': 'RSA with small exponent',
        'expected_flag': 'picoCTF{wA8_th4t_3z_RSA?}',
        'difficulty': 3
    },
    'ctflearn_basic_android': {
        'type': ChallengeType.BASIC_CRYPTO,
        'description': 'Base64 encoded flag',
        'expected_flag': 'CTFlearn{4ndr01d_r3v3r51ng}',
        'difficulty': 1
    }
}