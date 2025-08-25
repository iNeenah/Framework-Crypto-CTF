"""
Tests para el sistema de red (NetworkConnector y NetworkPlugin)
"""

import pytest
import asyncio
import socket
import threading
import time
from unittest.mock import Mock, patch, AsyncMock

from src.core.network_connector import NetworkConnector, NetworkResponse, NetworkSession
from src.plugins.network.plugin import NetworkPlugin
from src.models.data import ChallengeData, NetworkInfo, ChallengeType


class MockTCPServer:
    """Servidor TCP mock para tests"""
    
    def __init__(self, host='localhost', port=0):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.responses = []
        self.received_data = []
    
    def start(self):
        """Iniciar servidor mock"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.port = self.server_socket.getsockname()[1]  # Obtener puerto asignado
        self.server_socket.listen(1)
        self.running = True
        
        # Ejecutar en hilo separado
        self.thread = threading.Thread(target=self._run_server)
        self.thread.daemon = True
        self.thread.start()
        
        # Esperar un poco para que el servidor esté listo
        time.sleep(0.1)
    
    def _run_server(self):
        """Ejecutar servidor"""
        try:
            while self.running:
                self.server_socket.settimeout(1.0)
                try:
                    client_socket, addr = self.server_socket.accept()
                    self._handle_client(client_socket)
                except socket.timeout:
                    continue
                except Exception:
                    break
        except Exception:
            pass
    
    def _handle_client(self, client_socket):
        """Manejar cliente"""
        try:
            # Enviar respuestas predefinidas
            for response in self.responses:
                if isinstance(response, str):
                    client_socket.send(response.encode('utf-8'))
                else:
                    client_socket.send(response)
                
                # Recibir datos del cliente
                try:
                    data = client_socket.recv(1024)
                    if data:
                        self.received_data.append(data)
                except:
                    break
            
        except Exception:
            pass
        finally:
            client_socket.close()
    
    def stop(self):
        """Detener servidor"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1.0)
    
    def add_response(self, response):
        """Agregar respuesta del servidor"""
        self.responses.append(response)


class TestNetworkConnector:
    """Tests para NetworkConnector"""
    
    @pytest.fixture
    def connector(self):
        return NetworkConnector()
    
    @pytest.fixture
    def mock_server(self):
        server = MockTCPServer()
        server.start()
        yield server
        server.stop()
    
    @pytest.fixture
    def network_info(self, mock_server):
        return NetworkInfo(
            host='localhost',
            port=mock_server.port,
            protocol='tcp',
            timeout=5
        )
    
    def test_connector_initialization(self, connector):
        """Test inicialización del conector"""
        assert connector._response_patterns is not None
        assert 'flag' in connector._response_patterns
        assert 'prompt' in connector._response_patterns
        assert len(connector._active_sessions) == 0
    
    @pytest.mark.asyncio
    async def test_tcp_connection(self, connector, network_info, mock_server):
        """Test conexión TCP"""
        mock_server.add_response("Welcome to the server!\n")
        
        connection_id = await connector.connect(network_info)
        
        assert connection_id is not None
        assert connection_id in connector._active_sessions
        
        session = connector._active_sessions[connection_id]
        assert session.connected is True
        assert session.network_info == network_info
        
        await connector.disconnect(connection_id)
    
    @pytest.mark.asyncio
    async def test_send_receive_data(self, connector, network_info, mock_server):
        """Test envío y recepción de datos"""
        mock_server.add_response("Hello from server\n")
        
        connection_id = await connector.connect(network_info)
        
        # Enviar datos
        response = await connector.send_data(connection_id, "test message")
        
        assert response.success is True
        assert b"Hello from server" in response.data
        
        await connector.disconnect(connection_id)
    
    @pytest.mark.asyncio
    async def test_connection_timeout(self, connector):
        """Test timeout de conexión"""
        # Intentar conectar a puerto cerrado
        network_info = NetworkInfo(
            host='localhost',
            port=99999,  # Puerto que no existe
            protocol='tcp',
            timeout=1
        )
        
        with pytest.raises(Exception):  # Debería fallar
            await connector.connect(network_info)
    
    @pytest.mark.asyncio
    async def test_udp_connection(self, connector):
        """Test conexión UDP"""
        network_info = NetworkInfo(
            host='localhost',
            port=12345,
            protocol='udp',
            timeout=5
        )
        
        connection_id = await connector.connect(network_info)
        
        assert connection_id is not None
        session = connector._active_sessions[connection_id]
        assert session.socket is not None
        
        await connector.disconnect(connection_id)
    
    def test_pattern_matching(self, connector):
        """Test patrones de respuesta"""
        # Test flag pattern
        flag_text = "Here is your flag: CTF{test_flag}"
        assert connector._contains_flag(flag_text.encode())
        
        extracted_flag = connector.extract_flag(flag_text.encode())
        assert extracted_flag == "CTF{test_flag}"
        
        # Test no flag
        no_flag_text = "No flag here"
        assert not connector._contains_flag(no_flag_text.encode())
    
    def test_analyze_and_respond(self, connector):
        """Test análisis y respuesta automática"""
        # Test menu
        menu_text = "1. Option 1\n2. Option 2\nSelect: "
        response = connector._analyze_and_respond(menu_text.encode())
        assert response == "1"
        
        # Test prompt
        prompt_text = "Enter your name: "
        response = connector._analyze_and_respond(prompt_text.encode())
        assert response == "admin"
        
        # Test password prompt
        password_text = "Password: "
        response = connector._analyze_and_respond(password_text.encode())
        assert response == "password"
    
    @pytest.mark.asyncio
    async def test_interactive_session(self, connector, network_info, mock_server):
        """Test sesión interactiva"""
        # Configurar respuestas del servidor
        mock_server.add_response("Welcome! Enter command: ")
        mock_server.add_response("CTF{interactive_flag}")
        
        connection_id = await connector.connect(network_info)
        
        responses = await connector.interactive_session(connection_id, max_interactions=5)
        
        assert len(responses) > 0
        # Verificar que se recibieron respuestas
        assert any(response.success for response in responses)
        
        await connector.disconnect(connection_id)
    
    @pytest.mark.asyncio
    async def test_disconnect_all(self, connector, network_info, mock_server):
        """Test desconexión de todas las sesiones"""
        mock_server.add_response("Hello\n")
        
        # Crear múltiples conexiones
        connection1 = await connector.connect(network_info)
        connection2 = await connector.connect(network_info)
        
        assert len(connector._active_sessions) == 2
        
        await connector.disconnect_all()
        
        assert len(connector._active_sessions) == 0
    
    def test_session_info(self, connector):
        """Test información de sesión"""
        # Sin sesiones
        info = connector.get_session_info("nonexistent")
        assert info is None
        
        # Con sesión mock
        network_info = NetworkInfo(host="test", port=1234, protocol="tcp")
        session = NetworkSession(
            connection_id="test_session",
            network_info=network_info,
            connected=True,
            last_activity=time.time()
        )
        connector._active_sessions["test_session"] = session
        
        info = connector.get_session_info("test_session")
        assert info is not None
        assert info['connection_id'] == "test_session"
        assert info['host'] == "test"
        assert info['port'] == 1234


class TestNetworkPlugin:
    """Tests para NetworkPlugin"""
    
    @pytest.fixture
    def plugin(self):
        return NetworkPlugin()
    
    @pytest.fixture
    def network_challenge(self):
        network_info = NetworkInfo(
            host="example.com",
            port=1337,
            protocol="tcp"
        )
        return ChallengeData(
            id="network_test",
            name="Network Challenge",
            network_info=network_info,
            challenge_type=ChallengeType.NETWORK
        )
    
    def test_plugin_info(self, plugin):
        """Test información del plugin"""
        info = plugin.get_plugin_info()
        assert info.name == "network_ctf"
        assert ChallengeType.NETWORK in info.supported_types
        assert "interactive_session" in info.techniques
    
    def test_can_handle_network_challenge(self, plugin, network_challenge):
        """Test evaluación de desafío de red"""
        confidence = plugin.can_handle(network_challenge)
        assert confidence >= 0.8  # Debería tener alta confianza
    
    def test_can_handle_no_network_info(self, plugin):
        """Test evaluación sin información de red"""
        challenge = ChallengeData(
            id="no_network",
            name="No Network",
            challenge_type=ChallengeType.BASIC_CRYPTO
        )
        
        confidence = plugin.can_handle(challenge)
        assert confidence < 0.5  # Baja confianza sin info de red
    
    def test_analyze_network_content(self, plugin):
        """Test análisis de contenido de red"""
        network_content = "Connect to server using netcat: nc example.com 1337"
        confidence = plugin._analyze_network_content(network_content)
        assert confidence > 0.3
        
        non_network_content = "This is just regular text"
        confidence = plugin._analyze_network_content(non_network_content)
        assert confidence < 0.2
    
    def test_caesar_decrypt(self, plugin):
        """Test descifrado César"""
        # "HELLO" con shift 3 es "KHOOR"
        encrypted = "KHOOR"
        decrypted = plugin._caesar_decrypt(encrypted, 3)
        assert decrypted == "HELLO"
    
    @patch('src.plugins.network.plugin.NetworkConnector')
    def test_solve_no_network_info(self, mock_connector_class, plugin):
        """Test resolución sin información de red"""
        challenge = ChallengeData(id="test", name="Test")
        
        result = plugin.solve(challenge)
        
        assert result.success is False
        assert "No hay información de red" in result.error_message
    
    @patch('src.plugins.network.plugin.NetworkConnector')
    @pytest.mark.asyncio
    async def test_strategy_menu_navigation(self, mock_connector_class, plugin):
        """Test estrategia de navegación por menús"""
        # Mock del connector
        mock_connector = Mock()
        mock_responses = [
            Mock(success=True, data=b"1. Option 1\n2. Option 2\nSelect: "),
            Mock(success=True, data=b"CTF{menu_flag}")
        ]
        mock_connector.interactive_session = AsyncMock(return_value=mock_responses)
        mock_connector.extract_flag = Mock(return_value="CTF{menu_flag}")
        
        plugin.network_connector = mock_connector
        
        challenge = ChallengeData(id="test", name="Test")
        result = await plugin._strategy_menu_navigation("test_connection", challenge)
        
        assert result.success is True
        assert result.flag == "CTF{menu_flag}"
        assert "menu_navigation" in result.method_used
    
    @patch('src.plugins.network.plugin.NetworkConnector')
    @pytest.mark.asyncio
    async def test_strategy_crypto_challenge(self, mock_connector_class, plugin):
        """Test estrategia de desafío criptográfico"""
        # Mock del connector
        mock_connector = Mock()
        
        # Respuesta con Base64
        base64_response = Mock(success=True, data=b"Decode this: SGVsbG8gV29ybGQ=")
        success_response = Mock(success=True, data=b"CTF{crypto_solved}")
        
        mock_connector.receive_data = AsyncMock(return_value=base64_response)
        mock_connector.send_data = AsyncMock(return_value=success_response)
        mock_connector.extract_flag = Mock(return_value="CTF{crypto_solved}")
        
        plugin.network_connector = mock_connector
        
        challenge = ChallengeData(id="test", name="Test")
        result = await plugin._strategy_crypto_challenge("test_connection", challenge)
        
        assert result.success is True
        assert result.flag == "CTF{crypto_solved}"
    
    @patch('src.plugins.network.plugin.NetworkConnector')
    @pytest.mark.asyncio
    async def test_strategy_auth_bypass(self, mock_connector_class, plugin):
        """Test estrategia de bypass de autenticación"""
        mock_connector = Mock()
        
        # Primera respuesta (username prompt)
        username_response = Mock(success=True, data=b"Username: ")
        # Segunda respuesta (password prompt)
        password_response = Mock(success=True, data=b"Password: ")
        # Tercera respuesta (éxito)
        success_response = Mock(success=True, data=b"Welcome! CTF{auth_bypassed}")
        
        mock_connector.receive_data = AsyncMock(return_value=username_response)
        mock_connector.send_data = AsyncMock(side_effect=[password_response, success_response])
        mock_connector.extract_flag = Mock(return_value="CTF{auth_bypassed}")
        
        plugin.network_connector = mock_connector
        
        challenge = ChallengeData(id="test", name="Test")
        result = await plugin._strategy_auth_bypass("test_connection", challenge)
        
        assert result.success is True
        assert result.flag == "CTF{auth_bypassed}"
    
    @patch('src.plugins.network.plugin.NetworkConnector')
    @pytest.mark.asyncio
    async def test_strategy_command_injection(self, mock_connector_class, plugin):
        """Test estrategia de inyección de comandos"""
        mock_connector = Mock()
        
        # Respuesta exitosa con flag
        success_response = Mock(success=True, data=b"CTF{command_injected}")
        mock_connector.send_data = AsyncMock(return_value=success_response)
        mock_connector.extract_flag = Mock(return_value="CTF{command_injected}")
        
        plugin.network_connector = mock_connector
        
        challenge = ChallengeData(id="test", name="Test")
        result = await plugin._strategy_command_injection("test_connection", challenge)
        
        assert result.success is True
        assert result.flag == "CTF{command_injected}"
    
    @patch('src.plugins.network.plugin.NetworkConnector')
    @pytest.mark.asyncio
    async def test_strategy_simple_interaction(self, mock_connector_class, plugin):
        """Test estrategia de interacción simple"""
        mock_connector = Mock()
        
        # Respuesta exitosa
        success_response = Mock(success=True, data=b"CTF{simple_flag}")
        mock_connector.send_data = AsyncMock(return_value=success_response)
        mock_connector.extract_flag = Mock(return_value="CTF{simple_flag}")
        
        plugin.network_connector = mock_connector
        
        challenge = ChallengeData(id="test", name="Test")
        result = await plugin._strategy_simple_interaction("test_connection", challenge)
        
        assert result.success is True
        assert result.flag == "CTF{simple_flag}"
    
    @patch('src.plugins.network.plugin.NetworkConnector')
    @pytest.mark.asyncio
    async def test_all_strategies_fail(self, mock_connector_class, plugin):
        """Test cuando todas las estrategias fallan"""
        mock_connector = Mock()
        
        # Todas las respuestas fallan
        fail_response = Mock(success=False, error_message="Connection failed")
        mock_connector.test_connection = AsyncMock(return_value=True)
        mock_connector.connect = AsyncMock(return_value="test_connection")
        mock_connector.disconnect = AsyncMock()
        mock_connector.interactive_session = AsyncMock(return_value=[fail_response])
        mock_connector.receive_data = AsyncMock(return_value=fail_response)
        mock_connector.send_data = AsyncMock(return_value=fail_response)
        mock_connector.extract_flag = Mock(return_value=None)
        
        plugin.network_connector = mock_connector
        
        network_info = NetworkInfo(host="test", port=1234, protocol="tcp")
        challenge = ChallengeData(
            id="test",
            name="Test",
            network_info=network_info
        )
        
        result = await plugin._solve_async(challenge)
        
        assert result.success is False
        assert "Ninguna estrategia fue exitosa" in result.error_message


if __name__ == "__main__":
    pytest.main([__file__])