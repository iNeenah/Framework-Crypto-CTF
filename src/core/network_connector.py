"""
Network Connector - Conector de red para desafíos CTF remotos
"""

import asyncio
import socket
import ssl
import time
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from ..models.data import NetworkInfo, SolutionResult
from ..models.exceptions import NetworkConnectionError, ChallengeTimeoutError
from ..utils.config import config
from ..utils.logging import get_logger


class ProtocolType(Enum):
    """Tipos de protocolo soportados"""
    TCP = "tcp"
    UDP = "udp"
    HTTP = "http"
    HTTPS = "https"
    TELNET = "telnet"
    SSH = "ssh"


@dataclass
class NetworkResponse:
    """Respuesta de red"""
    data: bytes
    timestamp: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class NetworkSession:
    """Sesión de red activa"""
    def __init__(self, session_id: str, network_info: NetworkInfo):
        self.session_id = session_id
        self.network_info = network_info
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        self.created_at = time.time()
        self.last_activity = time.time()
        self.data_received = b""
        self.data_sent = b""


class NetworkConnector:
    """Conector de red para interacciones CTF remotas"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._active_sessions: Dict[str, NetworkSession] = {}
        self._response_patterns: Dict[str, re.Pattern] = {}
        self._setup_common_patterns()
    
    def _setup_common_patterns(self) -> None:
        """Configurar patrones comunes de respuesta"""
        self._response_patterns = {
            'flag': re.compile(r'(CTF\{[^}]+\}|FLAG\{[^}]+\}|flag\{[^}]+\})', re.IGNORECASE),
            'prompt': re.compile(r'[>$#%]\s*$|Enter|Input|Choice|Select', re.IGNORECASE),
            'error': re.compile(r'error|invalid|wrong|fail|denied', re.IGNORECASE),
            'success': re.compile(r'correct|success|right|valid|accepted', re.IGNORECASE),
            'menu': re.compile(r'\d+\.\s+|[a-z]\)\s+|\[\d+\]', re.IGNORECASE),
            'base64': re.compile(r'[A-Za-z0-9+/]{20,}={0,2}'),
            'hex': re.compile(r'[0-9a-fA-F]{20,}'),
        }
    
    async def connect(self, network_info: NetworkInfo) -> str:
        """
        Establecer conexión con servicio remoto.
        
        Args:
            network_info: Información de conexión
            
        Returns:
            str: ID de la sesión creada
        """
        # Validar conexión con sistema de seguridad
        from .security_manager import security_manager
        validated_host, validated_port = security_manager.validate_network_connection(
            network_info.host, network_info.port
        )
        
        connection_id = f"{validated_host}:{validated_port}_{int(time.time())}"
        
        self.logger.info(f"Conectando a {validated_host}:{validated_port} ({network_info.protocol})")
        
        try:
            if network_info.protocol.lower() in ['tcp', 'telnet']:
                session = await self._connect_tcp(network_info, connection_id)
            elif network_info.protocol.lower() == 'udp':
                session = await self._connect_udp(network_info, connection_id)
            elif network_info.protocol.lower() in ['http', 'https']:
                session = await self._connect_http(network_info, connection_id)
            else:
                raise NetworkConnectionError(f"Protocolo no soportado: {network_info.protocol}")
            
            self._active_sessions[connection_id] = session
            self.logger.info(f"Conexión establecida: {connection_id}")
            
            return connection_id
            
        except Exception as e:
            self.logger.error(f"Error conectando a {network_info.host}:{network_info.port}: {e}")
            raise NetworkConnectionError(f"Error de conexión: {str(e)}", network_info.host, network_info.port)
    
    async def _connect_tcp(self, network_info: NetworkInfo, connection_id: str) -> NetworkSession:
        """Establecer conexión TCP"""
        try:
            if network_info.ssl:
                # Conexión SSL/TLS
                context = ssl.create_default_context()
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(
                        network_info.host, 
                        network_info.port,
                        ssl=context
                    ),
                    timeout=network_info.timeout
                )
            else:
                # Conexión TCP normal
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(network_info.host, network_info.port),
                    timeout=network_info.timeout
                )
            
            session = NetworkSession(
                connection_id=connection_id,
                network_info=network_info,
                reader=reader,
                writer=writer,
                connected=True,
                last_activity=time.time()
            )
            
            return session
            
        except asyncio.TimeoutError:
            raise NetworkConnectionError("Timeout en conexión TCP", network_info.host, network_info.port)
        except Exception as e:
            raise NetworkConnectionError(f"Error TCP: {str(e)}", network_info.host, network_info.port)
    
    async def _connect_udp(self, network_info: NetworkInfo, connection_id: str) -> NetworkSession:
        """Establecer conexión UDP"""
        try:
            # UDP es connectionless, pero creamos un socket para envío
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(network_info.timeout)
            
            session = NetworkSession(
                connection_id=connection_id,
                network_info=network_info,
                socket=sock,
                connected=True,
                last_activity=time.time()
            )
            
            return session
            
        except Exception as e:
            raise NetworkConnectionError(f"Error UDP: {str(e)}", network_info.host, network_info.port)
    
    async def _connect_http(self, network_info: NetworkInfo, connection_id: str) -> NetworkSession:
        """Establecer conexión HTTP/HTTPS"""
        # Para HTTP, no mantenemos conexión persistente
        # Solo guardamos la información para requests posteriores
        session = NetworkSession(
            connection_id=connection_id,
            network_info=network_info,
            connected=True,
            last_activity=time.time()
        )
        
        return session
    
    async def send_data(self, connection_id: str, data: Union[str, bytes]) -> NetworkResponse:
        """
        Enviar datos a través de la conexión.
        
        Args:
            connection_id: ID de la sesión
            data: Datos a enviar
            
        Returns:
            NetworkResponse: Respuesta del servidor
        """
        if connection_id not in self._active_sessions:
            raise NetworkConnectionError(f"Sesión no encontrada: {connection_id}")
        
        session = self._active_sessions[connection_id]
        
        if not session.connected:
            raise NetworkConnectionError(f"Sesión no conectada: {connection_id}")
        
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            self.logger.debug(f"Enviando datos a {connection_id}: {data[:100]}...")
            
            if session.writer:  # TCP
                return await self._send_tcp(session, data)
            elif session.socket:  # UDP
                return await self._send_udp(session, data)
            else:  # HTTP
                return await self._send_http(session, data)
                
        except Exception as e:
            self.logger.error(f"Error enviando datos a {connection_id}: {e}")
            return NetworkResponse(
                data=b"",
                timestamp=time.time(),
                success=False,
                error_message=str(e)
            )
    
    async def _send_tcp(self, session: NetworkSession, data: bytes) -> NetworkResponse:
        """Enviar datos TCP y recibir respuesta"""
        try:
            # Enviar datos
            session.writer.write(data)
            if not data.endswith(b'\n'):
                session.writer.write(b'\n')
            await session.writer.drain()
            
            # Recibir respuesta
            response_data = await asyncio.wait_for(
                session.reader.read(4096),
                timeout=session.network_info.timeout
            )
            
            session.last_activity = time.time()
            
            return NetworkResponse(
                data=response_data,
                timestamp=time.time(),
                success=True
            )
            
        except asyncio.TimeoutError:
            return NetworkResponse(
                data=b"",
                timestamp=time.time(),
                success=False,
                error_message="Timeout esperando respuesta TCP"
            )
        except Exception as e:
            return NetworkResponse(
                data=b"",
                timestamp=time.time(),
                success=False,
                error_message=f"Error TCP: {str(e)}"
            )
    
    async def _send_udp(self, session: NetworkSession, data: bytes) -> NetworkResponse:
        """Enviar datos UDP y recibir respuesta"""
        try:
            # Enviar datos
            session.socket.sendto(data, (session.network_info.host, session.network_info.port))
            
            # Recibir respuesta
            response_data, addr = session.socket.recvfrom(4096)
            
            session.last_activity = time.time()
            
            return NetworkResponse(
                data=response_data,
                timestamp=time.time(),
                success=True
            )
            
        except socket.timeout:
            return NetworkResponse(
                data=b"",
                timestamp=time.time(),
                success=False,
                error_message="Timeout esperando respuesta UDP"
            )
        except Exception as e:
            return NetworkResponse(
                data=b"",
                timestamp=time.time(),
                success=False,
                error_message=f"Error UDP: {str(e)}"
            )
    
    async def _send_http(self, session: NetworkSession, data: bytes) -> NetworkResponse:
        """Enviar datos HTTP"""
        try:
            import aiohttp
            
            url = f"{'https' if session.network_info.ssl else 'http'}://{session.network_info.host}:{session.network_info.port}"
            
            timeout = aiohttp.ClientTimeout(total=session.network_info.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as client_session:
                async with client_session.post(url, data=data) as response:
                    response_data = await response.read()
                    
                    session.last_activity = time.time()
                    
                    return NetworkResponse(
                        data=response_data,
                        timestamp=time.time(),
                        success=response.status == 200
                    )
                    
        except Exception as e:
            return NetworkResponse(
                data=b"",
                timestamp=time.time(),
                success=False,
                error_message=f"Error HTTP: {str(e)}"
            )
    
    async def receive_data(self, connection_id: str, timeout: Optional[int] = None) -> NetworkResponse:
        """
        Recibir datos de la conexión.
        
        Args:
            connection_id: ID de la sesión
            timeout: Timeout personalizado
            
        Returns:
            NetworkResponse: Datos recibidos
        """
        if connection_id not in self._active_sessions:
            raise NetworkConnectionError(f"Sesión no encontrada: {connection_id}")
        
        session = self._active_sessions[connection_id]
        timeout = timeout or session.network_info.timeout
        
        try:
            if session.reader:  # TCP
                data = await asyncio.wait_for(session.reader.read(4096), timeout=timeout)
                session.last_activity = time.time()
                
                return NetworkResponse(
                    data=data,
                    timestamp=time.time(),
                    success=True
                )
            else:
                return NetworkResponse(
                    data=b"",
                    timestamp=time.time(),
                    success=False,
                    error_message="Recepción no soportada para este tipo de conexión"
                )
                
        except asyncio.TimeoutError:
            return NetworkResponse(
                data=b"",
                timestamp=time.time(),
                success=False,
                error_message="Timeout recibiendo datos"
            )
        except Exception as e:
            return NetworkResponse(
                data=b"",
                timestamp=time.time(),
                success=False,
                error_message=f"Error recibiendo datos: {str(e)}"
            )
    
    async def interactive_session(self, connection_id: str, max_interactions: int = 50) -> List[NetworkResponse]:
        """
        Sesión interactiva automática.
        
        Args:
            connection_id: ID de la sesión
            max_interactions: Máximo número de interacciones
            
        Returns:
            List[NetworkResponse]: Lista de respuestas
        """
        if connection_id not in self._active_sessions:
            raise NetworkConnectionError(f"Sesión no encontrada: {connection_id}")
        
        responses = []
        session = self._active_sessions[connection_id]
        
        self.logger.info(f"Iniciando sesión interactiva con {connection_id}")
        
        try:
            # Recibir mensaje inicial
            initial_response = await self.receive_data(connection_id, timeout=5)
            if initial_response.success:
                responses.append(initial_response)
                self.logger.debug(f"Mensaje inicial: {initial_response.data[:200]}")
            
            for interaction in range(max_interactions):
                if not session.connected:
                    break
                
                # Analizar última respuesta
                if responses:
                    last_response = responses[-1]
                    next_input = self._analyze_and_respond(last_response.data)
                    
                    if next_input is None:
                        self.logger.info("No se pudo determinar próxima entrada")
                        break
                    
                    # Enviar respuesta
                    response = await self.send_data(connection_id, next_input)
                    responses.append(response)
                    
                    if not response.success:
                        self.logger.warning(f"Error en interacción {interaction}: {response.error_message}")
                        break
                    
                    # Verificar si encontramos una flag
                    if self._contains_flag(response.data):
                        self.logger.info("Flag encontrada en respuesta")
                        break
                    
                    self.logger.debug(f"Interacción {interaction}: {response.data[:200]}")
                
                # Pequeña pausa entre interacciones
                await asyncio.sleep(0.1)
            
            return responses
            
        except Exception as e:
            self.logger.error(f"Error en sesión interactiva: {e}")
            return responses
    
    def _analyze_and_respond(self, data: bytes) -> Optional[str]:
        """Analizar respuesta y determinar próxima entrada"""
        try:
            text = data.decode('utf-8', errors='ignore').strip()
            text_lower = text.lower()
            
            # Detectar diferentes tipos de prompts y responder apropiadamente
            
            # Menú numérico
            if self._response_patterns['menu'].search(text):
                # Buscar opciones y elegir la primera
                menu_options = re.findall(r'(\d+)\.', text)
                if menu_options:
                    return menu_options[0]
            
            # Prompt de entrada
            if self._response_patterns['prompt'].search(text):
                # Respuestas comunes para diferentes prompts
                if 'name' in text_lower:
                    return 'admin'
                elif 'password' in text_lower:
                    return 'password'
                elif 'choice' in text_lower or 'select' in text_lower:
                    return '1'
                elif 'enter' in text_lower:
                    return 'test'
                else:
                    return 'yes'
            
            # Desafío de criptografía
            if 'decrypt' in text_lower or 'cipher' in text_lower:
                # Buscar datos cifrados
                if self._response_patterns['base64'].search(text):
                    # Intentar decodificar base64
                    import base64
                    matches = self._response_patterns['base64'].findall(text)
                    if matches:
                        try:
                            decoded = base64.b64decode(matches[0]).decode('utf-8', errors='ignore')
                            return decoded
                        except:
                            pass
                
                if self._response_patterns['hex'].search(text):
                    # Intentar decodificar hex
                    matches = self._response_patterns['hex'].findall(text)
                    if matches:
                        try:
                            decoded = bytes.fromhex(matches[0]).decode('utf-8', errors='ignore')
                            return decoded
                        except:
                            pass
            
            # Desafío matemático
            if any(word in text_lower for word in ['calculate', 'solve', 'equation', 'result']):
                # Buscar expresiones matemáticas simples
                math_expr = re.search(r'(\d+)\s*[\+\-\*\/]\s*(\d+)', text)
                if math_expr:
                    try:
                        result = eval(math_expr.group(0))  # Cuidado: eval es peligroso
                        return str(result)
                    except:
                        pass
            
            # Respuestas por defecto para diferentes contextos
            if '?' in text:
                return 'yes'
            elif 'continue' in text_lower:
                return 'y'
            elif len(text.strip()) < 10:  # Prompt muy corto
                return '\n'  # Solo enter
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error analizando respuesta: {e}")
            return None
    
    def _contains_flag(self, data: bytes) -> bool:
        """Verificar si los datos contienen una flag"""
        try:
            text = data.decode('utf-8', errors='ignore')
            return bool(self._response_patterns['flag'].search(text))
        except:
            return False
    
    def extract_flag(self, data: bytes) -> Optional[str]:
        """Extraer flag de los datos"""
        try:
            text = data.decode('utf-8', errors='ignore')
            match = self._response_patterns['flag'].search(text)
            return match.group(1) if match else None
        except:
            return None
    
    async def disconnect(self, connection_id: str) -> None:
        """Cerrar conexión"""
        if connection_id not in self._active_sessions:
            return
        
        session = self._active_sessions[connection_id]
        
        try:
            if session.writer:
                session.writer.close()
                await session.writer.wait_closed()
            
            if session.socket:
                session.socket.close()
            
            session.connected = False
            
        except Exception as e:
            self.logger.warning(f"Error cerrando conexión {connection_id}: {e}")
        
        finally:
            del self._active_sessions[connection_id]
            self.logger.info(f"Conexión cerrada: {connection_id}")
    
    async def disconnect_all(self) -> None:
        """Cerrar todas las conexiones activas"""
        connection_ids = list(self._active_sessions.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id)
    
    def get_active_sessions(self) -> List[str]:
        """Obtener lista de sesiones activas"""
        return list(self._active_sessions.keys())
    
    def get_session_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Obtener información de una sesión"""
        if connection_id not in self._active_sessions:
            return None
        
        session = self._active_sessions[connection_id]
        
        return {
            'connection_id': connection_id,
            'host': session.network_info.host,
            'port': session.network_info.port,
            'protocol': session.network_info.protocol,
            'connected': session.connected,
            'last_activity': session.last_activity,
            'uptime': time.time() - session.last_activity if session.connected else 0
        }
    
    async def test_connection(self, network_info: NetworkInfo) -> bool:
        """Probar conexión sin mantenerla activa"""
        try:
            connection_id = await self.connect(network_info)
            await self.disconnect(connection_id)
            return True
        except Exception as e:
            self.logger.debug(f"Test de conexión falló: {e}")
            return False
    
    def __del__(self):
        """Cleanup al destruir el conector"""
        # Cerrar conexiones pendientes
        if hasattr(self, '_active_sessions'):
            for session in self._active_sessions.values():
                try:
                    if session.writer:
                        session.writer.close()
                    if session.socket:
                        session.socket.close()
                except:
                    pass