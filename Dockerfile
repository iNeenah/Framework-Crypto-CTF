# Dockerfile para Crypto CTF Framework
FROM python:3.9-slim

LABEL maintainer="iNeenah"
LABEL description="Advanced ML-Powered CTF Crypto Solver Framework"
LABEL version="1.0.0"

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libgmp-dev \
    libmpfr-dev \
    libmpc-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorios necesarios
RUN mkdir -p data/sekai_writeups models/expert challenges/uploaded challenges/solved

# Exponer puerto (si se implementa interfaz web)
EXPOSE 8000

# Comando por defecto
CMD ["python", "main.py"]