#!/usr/bin/env python3
"""
DownUnderCTF Specialized Writeups Downloader
Descarga writeups específicos de DownUnderCTF
"""

import requests
import time
from pathlib import Path

def download_downunderctf_writeups():
    """Descarga writeups específicos de DownUnderCTF usando URLs directas"""
    
    writeups_dir = Path("data/expert_writeups")
    writeups_dir.mkdir(parents=True, exist_ok=True)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # URLs directas a archivos de writeup conocidos de DownUnderCTF
    direct_urls = [
        # 2024 Challenges
        "https://raw.githubusercontent.com/DownUnderCTF/Challenges_2024_Public/main/crypto/baby-rsa/solve.py",
        "https://raw.githubusercontent.com/DownUnderCTF/Challenges_2024_Public/main/crypto/baby-rsa/README.md",
        "https://raw.githubusercontent.com/DownUnderCTF/Challenges_2024_Public/main/crypto/apbq-rsa/solve.py",
        "https://raw.githubusercontent.com/DownUnderCTF/Challenges_2024_Public/main/crypto/apbq-rsa/README.md",
        "https://raw.githubusercontent.com/DownUnderCTF/Challenges_2024_Public/main/crypto/three-s/solve.py",
        "https://raw.githubusercontent.com/DownUnderCTF/Challenges_2024_Public/main/crypto/three-s/README.md",
        
        # 2023 Challenges  
        "https://raw.githubusercontent.com/DownUnderCTF/Challenges_2023_Public/main/crypto/baby-arx/solve.py",
        "https://raw.githubusercontent.com/DownUnderCTF/Challenges_2023_Public/main/crypto/baby-arx/README.md",
        "https://raw.githubusercontent.com/DownUnderCTF/Challenges_2023_Public/main/crypto/decrypt-me/solve.py",
        "https://raw.githubusercontent.com/DownUnderCTF/Challenges_2023_Public/main/crypto/decrypt-me/README.md",
        "https://raw.githubusercontent.com/DownUnderCTF/Challenges_2023_Public/main/crypto/rsa-interval-oracle/solve.py",
        "https://raw.githubusercontent.com/DownUnderCTF/Challenges_2023_Public/main/crypto/rsa-interval-oracle/README.md",
        
        # 2022 Challenges
        "https://raw.githubusercontent.com/DownUnderCTF/Challenges_2022_Public/main/crypto/babyARX/solve.py",
        "https://raw.githubusercontent.com/DownUnderCTF/Challenges_2022_Public/main/crypto/babyARX/README.md",
        "https://raw.githubusercontent.com/DownUnderCTF/Challenges_2022_Public/main/crypto/Substitution-Cipher-1/solve.py",
        "https://raw.githubusercontent.com/DownUnderCTF/Challenges_2022_Public/main/crypto/Substitution-Cipher-1/README.md",
        "https://raw.githubusercontent.com/DownUnderCTF/Challenges_2022_Public/main/crypto/Substitution-Cipher-2/solve.py",
        "https://raw.githubusercontent.com/DownUnderCTF/Challenges_2022_Public/main/crypto/Substitution-Cipher-2/README.md",
    ]
    
    print("🚀 Descargando writeups específicos de DownUnderCTF...")
    print("=" * 60)
    
    downloaded = 0
    for url in direct_urls:
        try:
            response = session.get(url)
            if response.status_code == 200:
                # Extraer información del URL
                parts = url.split('/')
                year = parts[5].replace('Challenges_', '').replace('_Public', '')
                challenge_name = parts[8] if len(parts) > 8 else 'unknown'
                filename = parts[-1]
                
                local_filename = f"downunderctf_{year}_{challenge_name}_{filename}"
                filepath = writeups_dir / local_filename
                
                with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(response.text)
                
                print(f"✅ {local_filename}")
                downloaded += 1
                time.sleep(0.5)  # Rate limiting
            else:
                print(f"⚠️  No encontrado: {url.split('/')[-1]}")
        except Exception as e:
            print(f"❌ Error: {url} - {e}")
    
    print(f"\n🏆 Descargados {downloaded} writeups de DownUnderCTF")
    return downloaded

if __name__ == "__main__":
    download_downunderctf_writeups()