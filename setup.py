#!/usr/bin/env python3
"""
Setup script para Crypto CTF Solver
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="crypto-ctf-solver",
    version="0.1.0",
    author="Crypto CTF Solver Team",
    description="Framework inteligente para resolver desafíos de criptografía y CTF",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security :: Cryptography",
        "Topic :: Security",
    ],
    python_requires=">=3.9",
    install_requires=[
        # Criptografía
        "pycryptodome>=3.18.0",
        "gmpy2>=2.1.5",
        "cryptography>=41.0.0",
        
        # Matemáticas avanzadas
        "sympy>=1.12",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        
        # Machine Learning
        "tensorflow>=2.13.0",
        "torch>=2.0.0",
        "scikit-learn>=1.3.0",
        "pandas>=2.0.0",
        
        # Redes y CTF
        "pwntools>=4.10.0",
        "asyncio-mqtt>=0.13.0",
        "aiohttp>=3.8.0",
        
        # Compresión de archivos
        "py7zr>=0.20.0",
        "rarfile>=4.0",
        "patool>=1.12",
        
        # Utilidades
        "click>=8.1.0",
        "colorama>=0.4.6",
        "tqdm>=4.65.0",
        "rich>=13.4.0",
        "pydantic>=2.0.0",
        "python-magic>=0.4.27",
        
        # Testing y desarrollo
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.1.0",
        "black>=23.7.0",
        "flake8>=6.0.0",
        "mypy>=1.5.0",
    ],
    extras_require={
        "sage": ["sage>=10.0"],  # Opcional para matemáticas muy avanzadas
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pre-commit>=3.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "crypto-ctf-solver=src.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)