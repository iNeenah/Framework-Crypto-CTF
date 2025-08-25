#!/usr/bin/env python3
"""
Interfaz web completa para el Crypto CTF Solver
"""
import os
import sys
import asyncio
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Agregar src al path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi import Request, Depends
    from pydantic import BaseModel
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    print("FastAPI not available. Install with: pip install fastapi uvicorn jinja2 python-multipart")

from main import CryptoCTFSolver
from ml.models.ultimate_classifier import UltimateClassifier
from utils.production_logging import get_production_logger
from utils.error_handling import handle_exceptions, create_error_response
from utils.production_config import get_config

logger = get_production_logger("web_api")

# Modelos Pydantic
class ChallengeAnalysisRequest(BaseModel):
    content: str
    challenge_type: Optional[str] = None

class ChallengeAnalysisResponse(BaseModel):
    success: bool
    predicted_type: Optional[str] = None
    confidence: Optional[float] = None
    execution_time: Optional[float] = None
    suggestions: Optional[List[str]] = None
    error: Optional[str] = None

class SolutionRequest(BaseModel):
    content: str
    challenge_type: Optional[str] = None
    timeout: Optional[int] = 60

class SolutionResponse(BaseModel):
    success: bool
    flag: Optional[str] = None
    method: Optional[str] = None
    confidence: Optional[float] = None
    execution_time: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class SystemStatusResponse(BaseModel):
    status: str
    version: str
    uptime: float
    plugins_loaded: int
    ml_model_loaded: bool
    cache_enabled: bool
    total_challenges_processed: int
    success_rate: float

class WebApplication:
    """Aplicación web principal"""
    
    def __init__(self):
        if not HAS_FASTAPI:
            raise ImportError("FastAPI is required for web interface")
        
        self.app = FastAPI(
            title="Crypto CTF Solver",
            description="Advanced cryptographic challenge solver with AI capabilities",
            version="1.0.0",
            docs_url="/api/docs",
            redoc_url="/api/redoc"
        )
        
        self.config = get_config()
        self.solver = CryptoCTFSolver()
        self.classifier = None
        self.start_time = datetime.now()
        self.stats = {
            'total_requests': 0,
            'successful_solutions': 0,
            'failed_solutions': 0,
            'analysis_requests': 0
        }
        
        # Configurar aplicación
        self._setup_middleware()
        self._setup_routes()
        self._setup_static_files()
        self._load_ml_model()
    
    def _setup_middleware(self):
        """Configurar middleware"""
        # CORS
        if self.config.api.cors_enabled:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=self.config.api.cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        
        # Middleware personalizado para logging
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = datetime.now()
            
            # Log request
            logger.info(f"Request: {request.method} {request.url.path}", {
                'method': request.method,
                'path': request.url.path,
                'client_ip': request.client.host,
                'user_agent': request.headers.get('user-agent', '')
            })
            
            response = await call_next(request)
            
            # Log response
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Response: {response.status_code} in {execution_time:.3f}s", {
                'status_code': response.status_code,
                'execution_time': execution_time
            })
            
            self.stats['total_requests'] += 1
            
            return response
    
    def _setup_static_files(self):
        """Configurar archivos estáticos"""
        static_dir = Path(__file__).parent / "static"
        templates_dir = Path(__file__).parent / "templates"
        
        # Crear directorios si no existen
        static_dir.mkdir(exist_ok=True)
        templates_dir.mkdir(exist_ok=True)
        
        # Crear archivos básicos si no existen
        self._create_default_static_files(static_dir, templates_dir)
        
        # Montar archivos estáticos
        self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
        self.templates = Jinja2Templates(directory=templates_dir)
    
    def _create_default_static_files(self, static_dir: Path, templates_dir: Path):
        """Crear archivos estáticos por defecto"""
        
        # CSS básico
        css_content = """
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #007bff;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        textarea, input, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        textarea {
            height: 200px;
            resize: vertical;
        }
        button {
            background-color: #007bff;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
        }
        button:hover {
            background-color: #0056b3;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #007bff;
            background-color: #f8f9fa;
        }
        .success {
            border-left-color: #28a745;
            background-color: #d4edda;
        }
        .error {
            border-left-color: #dc3545;
            background-color: #f8d7da;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #007bff;
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        """
        
        (static_dir / "style.css").write_text(css_content)
        
        # JavaScript básico
        js_content = """
        async function analyzeChallenge() {
            const content = document.getElementById('content').value;
            const resultDiv = document.getElementById('result');
            
            if (!content.trim()) {
                alert('Por favor ingresa el contenido del desafío');
                return;
            }
            
            resultDiv.innerHTML = '<p>Analizando...</p>';
            
            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ content: content })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    resultDiv.className = 'result success';
                    resultDiv.innerHTML = `
                        <h3>Análisis Completado</h3>
                        <p><strong>Tipo Predicho:</strong> ${data.predicted_type}</p>
                        <p><strong>Confianza:</strong> ${(data.confidence * 100).toFixed(1)}%</p>
                        <p><strong>Tiempo:</strong> ${data.execution_time.toFixed(3)}s</p>
                        ${data.suggestions ? '<p><strong>Sugerencias:</strong> ' + data.suggestions.join(', ') + '</p>' : ''}
                    `;
                } else {
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML = `<h3>Error</h3><p>${data.error}</p>`;
                }
            } catch (error) {
                resultDiv.className = 'result error';
                resultDiv.innerHTML = `<h3>Error</h3><p>Error de conexión: ${error.message}</p>`;
            }
        }
        
        async function solveChallenge() {
            const content = document.getElementById('content').value;
            const resultDiv = document.getElementById('result');
            
            if (!content.trim()) {
                alert('Por favor ingresa el contenido del desafío');
                return;
            }
            
            resultDiv.innerHTML = '<p>Resolviendo desafío...</p>';
            
            try {
                const response = await fetch('/api/solve', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ content: content })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    resultDiv.className = 'result success';
                    resultDiv.innerHTML = `
                        <h3>¡Desafío Resuelto!</h3>
                        <p><strong>Flag:</strong> <code>${data.flag}</code></p>
                        <p><strong>Método:</strong> ${data.method}</p>
                        <p><strong>Confianza:</strong> ${(data.confidence * 100).toFixed(1)}%</p>
                        <p><strong>Tiempo:</strong> ${data.execution_time.toFixed(3)}s</p>
                        ${data.details ? '<details><summary>Detalles</summary><pre>' + JSON.stringify(data.details, null, 2) + '</pre></details>' : ''}
                    `;
                } else {
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML = `<h3>No se pudo resolver</h3><p>${data.error}</p>`;
                }
            } catch (error) {
                resultDiv.className = 'result error';
                resultDiv.innerHTML = `<h3>Error</h3><p>Error de conexión: ${error.message}</p>`;
            }
        }
        
        async function loadStats() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                document.getElementById('total-challenges').textContent = data.total_challenges_processed;
                document.getElementById('success-rate').textContent = (data.success_rate * 100).toFixed(1) + '%';
                document.getElementById('plugins-loaded').textContent = data.plugins_loaded;
                document.getElementById('ml-status').textContent = data.ml_model_loaded ? 'Activo' : 'Inactivo';
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }
        
        // Cargar estadísticas al cargar la página
        document.addEventListener('DOMContentLoaded', loadStats);
        """
        
        (static_dir / "script.js").write_text(js_content)
        
        # Template HTML principal
        html_template = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Crypto CTF Solver</title>
            <link rel="stylesheet" href="/static/style.css">
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎮 Crypto CTF Solver</h1>
                    <p>Sistema avanzado de resolución de desafíos criptográficos con IA</p>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-value" id="total-challenges">0</div>
                        <div class="stat-label">Desafíos Procesados</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="success-rate">0%</div>
                        <div class="stat-label">Tasa de Éxito</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="plugins-loaded">0</div>
                        <div class="stat-label">Plugins Cargados</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="ml-status">-</div>
                        <div class="stat-label">Modelo ML</div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="content">Contenido del Desafío:</label>
                    <textarea id="content" placeholder="Pega aquí el contenido del desafío criptográfico..."></textarea>
                </div>
                
                <div class="form-group">
                    <button onclick="analyzeChallenge()">🔍 Analizar</button>
                    <button onclick="solveChallenge()">🚀 Resolver</button>
                </div>
                
                <div id="result"></div>
                
                <div style="margin-top: 40px; text-align: center; color: #666;">
                    <p>API Documentation: <a href="/api/docs">/api/docs</a> | Status: <a href="/api/status">/api/status</a></p>
                </div>
            </div>
            
            <script src="/static/script.js"></script>
        </body>
        </html>
        """
        
        (templates_dir / "index.html").write_text(html_template)
    
    def _load_ml_model(self):
        """Cargar modelo ML"""
        try:
            if self.config.ml.enabled:
                self.classifier = UltimateClassifier()
                model_path = self.config.ml.model_path
                
                if Path(model_path).exists():
                    self.classifier.load_model(model_path)
                    logger.info("ML model loaded successfully")
                else:
                    logger.warning(f"ML model not found at {model_path}")
            else:
                logger.info("ML disabled in configuration")
        except Exception as e:
            logger.error(f"Error loading ML model: {e}")
    
    def _setup_routes(self):
        """Configurar rutas"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            """Página principal"""
            return self.templates.TemplateResponse("index.html", {"request": request})
        
        @self.app.post("/api/analyze", response_model=ChallengeAnalysisResponse)
        @handle_exceptions(default_return=ChallengeAnalysisResponse(success=False, error="Internal error"))
        async def analyze_challenge(request: ChallengeAnalysisRequest):
            """Analizar desafío"""
            start_time = datetime.now()
            
            try:
                if self.classifier:
                    result = self.classifier.predict(request.content)
                    
                    if result['success']:
                        execution_time = (datetime.now() - start_time).total_seconds()
                        
                        # Log para análisis
                        content_hash = hashlib.md5(request.content.encode()).hexdigest()[:8]
                        logger.log_ml_prediction(
                            content_hash,
                            result['predicted_type'],
                            result['confidence'],
                            execution_time
                        )
                        
                        self.stats['analysis_requests'] += 1
                        
                        return ChallengeAnalysisResponse(
                            success=True,
                            predicted_type=result['predicted_type'],
                            confidence=result['confidence'],
                            execution_time=execution_time,
                            suggestions=self._get_suggestions(result['predicted_type'])
                        )
                    else:
                        return ChallengeAnalysisResponse(
                            success=False,
                            error=result.get('error', 'ML prediction failed')
                        )
                else:
                    return ChallengeAnalysisResponse(
                        success=False,
                        error="ML model not available"
                    )
                    
            except Exception as e:
                logger.error(f"Error in challenge analysis: {e}")
                return ChallengeAnalysisResponse(
                    success=False,
                    error=str(e)
                )
        
        @self.app.post("/api/solve", response_model=SolutionResponse)
        @handle_exceptions(default_return=SolutionResponse(success=False, error="Internal error"))
        async def solve_challenge(request: SolutionRequest):
            """Resolver desafío"""
            start_time = datetime.now()
            
            try:
                # Usar el solver principal
                result = self.solver.analyze_challenge_content(request.content)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                if result and result.get('success'):
                    self.stats['successful_solutions'] += 1
                    
                    return SolutionResponse(
                        success=True,
                        flag="Solution found",  # Placeholder
                        method=result.get('detected_type', 'unknown'),
                        confidence=result.get('confidence', 0.5),
                        execution_time=execution_time,
                        details=result
                    )
                else:
                    self.stats['failed_solutions'] += 1
                    
                    return SolutionResponse(
                        success=False,
                        error=result.get('error', 'Could not solve challenge'),
                        execution_time=execution_time
                    )
                    
            except Exception as e:
                logger.error(f"Error solving challenge: {e}")
                self.stats['failed_solutions'] += 1
                
                return SolutionResponse(
                    success=False,
                    error=str(e)
                )
        
        @self.app.get("/api/status", response_model=SystemStatusResponse)
        async def get_status():
            """Estado del sistema"""
            uptime = (datetime.now() - self.start_time).total_seconds()
            total_solutions = self.stats['successful_solutions'] + self.stats['failed_solutions']
            success_rate = (self.stats['successful_solutions'] / total_solutions) if total_solutions > 0 else 0
            
            return SystemStatusResponse(
                status="running",
                version=self.config.version,
                uptime=uptime,
                plugins_loaded=len(self.solver.plugin_manager.get_available_plugins()),
                ml_model_loaded=self.classifier is not None and self.classifier.is_trained,
                cache_enabled=self.config.cache.enabled,
                total_challenges_processed=total_solutions,
                success_rate=success_rate
            )
        
        @self.app.get("/api/health")
        async def health_check():
            """Health check para monitoreo"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.post("/api/upload")
        async def upload_file(file: UploadFile = File(...)):
            """Subir archivo de desafío"""
            try:
                # Validar tamaño
                content = await file.read()
                if len(content) > self.config.security.max_file_size:
                    raise HTTPException(400, "File too large")
                
                # Validar tipo
                if not any(file.filename.endswith(ext) for ext in self.config.security.allowed_file_types):
                    raise HTTPException(400, "File type not allowed")
                
                # Procesar contenido
                content_str = content.decode('utf-8', errors='ignore')
                
                # Analizar
                if self.classifier:
                    result = self.classifier.predict(content_str)
                    return {
                        "success": True,
                        "filename": file.filename,
                        "size": len(content),
                        "analysis": result
                    }
                else:
                    return {
                        "success": True,
                        "filename": file.filename,
                        "size": len(content),
                        "message": "File uploaded but ML analysis not available"
                    }
                    
            except Exception as e:
                logger.error(f"Error uploading file: {e}")
                raise HTTPException(500, str(e))
    
    def _get_suggestions(self, challenge_type: str) -> List[str]:
        """Obtener sugerencias basadas en el tipo de desafío"""
        suggestions_map = {
            'BASIC_CRYPTO': [
                'Probar análisis de frecuencia',
                'Verificar cifrados clásicos (Caesar, Vigenère)',
                'Intentar decodificación Base64',
                'Buscar patrones XOR'
            ],
            'RSA': [
                'Verificar factores pequeños',
                'Probar ataque de Wiener',
                'Buscar exponente público pequeño',
                'Intentar factorización'
            ],
            'ECC': [
                'Verificar curvas débiles',
                'Probar ataques de punto inválido',
                'Buscar reutilización de nonce',
                'Intentar Smart\'s attack'
            ],
            'HASH': [
                'Probar ataques de diccionario',
                'Buscar colisiones conocidas',
                'Verificar funciones hash débiles',
                'Intentar rainbow tables'
            ],
            'STREAM_CIPHER': [
                'Verificar reutilización de nonce',
                'Buscar texto plano conocido',
                'Probar ataques de keystream',
                'Analizar patrones de cifrado'
            ],
            'NETWORK': [
                'Analizar paquetes de red',
                'Buscar datos ocultos en headers',
                'Verificar protocolos débiles',
                'Examinar tráfico DNS'
            ]
        }
        
        return suggestions_map.get(challenge_type, ['Analizar contenido manualmente'])
    
    def run(self, host: str = None, port: int = None, debug: bool = None):
        """Ejecutar aplicación web"""
        host = host or self.config.api.host
        port = port or self.config.api.port
        debug = debug if debug is not None else self.config.api.debug
        
        logger.info(f"Starting web application on {host}:{port}")
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            debug=debug,
            access_log=True
        )

def create_app() -> FastAPI:
    """Factory para crear aplicación"""
    web_app = WebApplication()
    return web_app.app

def main():
    """Función principal"""
    if not HAS_FASTAPI:
        print("Error: FastAPI is required for web interface")
        print("Install with: pip install fastapi uvicorn jinja2 python-multipart")
        return 1
    
    try:
        web_app = WebApplication()
        web_app.run()
    except KeyboardInterrupt:
        logger.info("Web application stopped by user")
    except Exception as e:
        logger.error(f"Error running web application: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())