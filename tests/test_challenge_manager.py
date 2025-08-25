"""
Tests para Challenge Manager
"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import Future

from src.core.challenge_manager import ChallengeManager
from src.core.file_analyzer import FileAnalyzer
from src.core.plugin_manager import PluginManager
from src.models.data import ChallengeData, SolutionResult, ChallengeType, DifficultyLevel, FileInfo
from src.models.exceptions import (
    InsufficientDataError, ValidationError, ChallengeTimeoutError
)


class TestChallengeManager:
    """Tests para ChallengeManager"""
    
    @pytest.fixture
    def mock_file_analyzer(self):
        """Mock del FileAnalyzer"""
        analyzer = Mock(spec=FileAnalyzer)
        return analyzer
    
    @pytest.fixture
    def mock_plugin_manager(self):
        """Mock del PluginManager"""
        manager = Mock(spec=PluginManager)
        return manager
    
    @pytest.fixture
    def challenge_manager(self, mock_file_analyzer, mock_plugin_manager):
        """Instancia de ChallengeManager con mocks"""
        return ChallengeManager(
            file_analyzer=mock_file_analyzer,
            plugin_manager=mock_plugin_manager
        )
    
    @pytest.fixture
    def sample_challenge(self):
        """Desafío de muestra"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            file_info = FileInfo(path=Path(tmp.name), size=100)
            return ChallengeData(
                id="test-challenge",
                name="Test Challenge",
                files=[file_info],
                challenge_type=ChallengeType.RSA
            )
    
    @pytest.fixture
    def temp_file(self):
        """Archivo temporal para tests"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp:
            tmp.write(b"test content")
            tmp.flush()
            yield Path(tmp.name)
    
    def test_initialization(self, challenge_manager):
        """Test inicialización del ChallengeManager"""
        assert challenge_manager.file_analyzer is not None
        assert challenge_manager.plugin_manager is not None
        assert len(challenge_manager._active_challenges) == 0
        assert len(challenge_manager._solution_history) == 0
        assert challenge_manager._stats['total_challenges'] == 0
    
    def test_load_challenge_success(self, challenge_manager, mock_file_analyzer, temp_file):
        """Test carga exitosa de desafío"""
        # Configurar mock
        expected_challenge = ChallengeData(
            id="test-id",
            name="Test",
            challenge_type=ChallengeType.RSA
        )
        mock_file_analyzer.analyze_file.return_value = expected_challenge
        
        # Cargar desafío
        result = challenge_manager.load_challenge(temp_file)
        
        # Verificar
        assert result == expected_challenge
        assert result.id in challenge_manager._active_challenges
        assert challenge_manager._stats['total_challenges'] == 1
        mock_file_analyzer.analyze_file.assert_called_once_with(temp_file)
    
    def test_load_challenge_failure(self, challenge_manager, mock_file_analyzer, temp_file):
        """Test falla en carga de desafío"""
        # Configurar mock para fallar
        mock_file_analyzer.analyze_file.side_effect = Exception("Analysis failed")
        
        # Verificar que se lanza excepción
        with pytest.raises(ValidationError, match="Error cargando desafío"):
            challenge_manager.load_challenge(temp_file)
        
        # Verificar estado
        assert len(challenge_manager._active_challenges) == 0
        assert challenge_manager._stats['total_challenges'] == 0
    
    def test_validate_challenge_success(self, challenge_manager, sample_challenge):
        """Test validación exitosa de desafío"""
        # No debería lanzar excepción
        challenge_manager._validate_challenge(sample_challenge)
    
    def test_validate_challenge_no_data(self, challenge_manager):
        """Test validación falla sin datos"""
        empty_challenge = ChallengeData(id="empty", name="Empty")
        
        with pytest.raises(InsufficientDataError, match="debe tener archivos o información de red"):
            challenge_manager._validate_challenge(empty_challenge)
    
    def test_validate_challenge_missing_file(self, challenge_manager):
        """Test validación falla con archivo faltante"""
        challenge = ChallengeData(
            id="missing-file",
            name="Missing File",
            files=[FileInfo(path=Path("/nonexistent/file.txt"), size=100)]
        )
        
        with pytest.raises(InsufficientDataError, match="Archivo no encontrado"):
            challenge_manager._validate_challenge(challenge)
    
    def test_detect_challenge_type_already_set(self, challenge_manager, sample_challenge):
        """Test detección cuando el tipo ya está definido"""
        result = challenge_manager._detect_challenge_type(sample_challenge)
        assert result == ChallengeType.RSA
    
    def test_detect_challenge_type_from_plugins(self, challenge_manager, mock_plugin_manager):
        """Test detección de tipo usando plugins"""
        # Crear desafío sin tipo
        challenge = ChallengeData(
            id="unknown",
            name="Unknown",
            files=[FileInfo(path=Path("/tmp/test.txt"), size=100)],
            challenge_type=ChallengeType.UNKNOWN
        )
        
        # Configurar mocks
        mock_plugin = Mock()
        mock_plugin.can_handle.return_value = 0.8
        mock_plugin_info = Mock()
        mock_plugin_info.supported_types = [ChallengeType.BASIC_CRYPTO]
        mock_plugin.get_plugin_info.return_value = mock_plugin_info
        
        mock_plugin_manager.get_available_plugins.return_value = ["test_plugin"]
        mock_plugin_manager.get_plugin.return_value = mock_plugin
        
        # Detectar tipo
        result = challenge_manager._detect_challenge_type(challenge)
        
        assert result == ChallengeType.BASIC_CRYPTO
    
    def test_select_optimal_strategy_single(self, challenge_manager, mock_plugin_manager, sample_challenge):
        """Test selección de estrategia para un plugin"""
        mock_plugin_manager.select_best_plugins.return_value = [("plugin1", Mock(), 0.9)]
        
        strategy = challenge_manager._select_optimal_strategy(sample_challenge)
        assert strategy == "single"
    
    def test_select_optimal_strategy_sequential(self, challenge_manager, mock_plugin_manager, sample_challenge):
        """Test selección de estrategia secuencial"""
        mock_plugin_manager.select_best_plugins.return_value = [
            ("plugin1", Mock(), 0.9),
            ("plugin2", Mock(), 0.7),
            ("plugin3", Mock(), 0.5)
        ]
        
        strategy = challenge_manager._select_optimal_strategy(sample_challenge)
        assert strategy == "sequential"
    
    def test_select_optimal_strategy_parallel(self, challenge_manager, mock_plugin_manager, sample_challenge):
        """Test selección de estrategia paralela"""
        mock_plugin_manager.select_best_plugins.return_value = [
            ("plugin1", Mock(), 0.9),
            ("plugin2", Mock(), 0.8),
            ("plugin3", Mock(), 0.7),
            ("plugin4", Mock(), 0.6)
        ]
        
        strategy = challenge_manager._select_optimal_strategy(sample_challenge)
        assert strategy == "parallel"
    
    def test_select_optimal_strategy_no_plugins(self, challenge_manager, mock_plugin_manager, sample_challenge):
        """Test selección sin plugins disponibles"""
        mock_plugin_manager.select_best_plugins.return_value = []
        
        with pytest.raises(InsufficientDataError, match="No hay plugins disponibles"):
            challenge_manager._select_optimal_strategy(sample_challenge)
    
    def test_solve_single_plugin_success(self, challenge_manager, mock_plugin_manager, sample_challenge):
        """Test resolución con plugin único exitosa"""
        # Configurar mock
        success_result = SolutionResult(success=True, flag="CTF{test}")
        mock_plugin_manager.select_best_plugins.return_value = [("plugin1", Mock(), 0.9)]
        mock_plugin_manager.solve_with_plugin.return_value = success_result
        
        # Resolver
        result = challenge_manager._solve_single_plugin(sample_challenge)
        
        assert result.success is True
        assert result.flag == "CTF{test}"
        mock_plugin_manager.solve_with_plugin.assert_called_once_with("plugin1", sample_challenge)
    
    def test_solve_single_plugin_no_plugins(self, challenge_manager, mock_plugin_manager, sample_challenge):
        """Test resolución sin plugins disponibles"""
        mock_plugin_manager.select_best_plugins.return_value = []
        
        result = challenge_manager._solve_single_plugin(sample_challenge)
        
        assert result.success is False
        assert "No hay plugins disponibles" in result.error_message
    
    def test_solve_sequential_success(self, challenge_manager, mock_plugin_manager, sample_challenge):
        """Test resolución secuencial exitosa"""
        # Configurar mocks - primer plugin falla, segundo tiene éxito
        fail_result = SolutionResult(success=False, error_message="Failed")
        success_result = SolutionResult(success=True, flag="CTF{sequential}")
        
        mock_plugin_manager.select_best_plugins.return_value = [
            ("plugin1", Mock(), 0.9),
            ("plugin2", Mock(), 0.7)
        ]
        mock_plugin_manager.solve_with_plugin.side_effect = [fail_result, success_result]
        
        # Resolver
        result = challenge_manager._solve_sequential(sample_challenge)
        
        assert result.success is True
        assert result.flag == "CTF{sequential}"
        assert mock_plugin_manager.solve_with_plugin.call_count == 2
    
    def test_solve_sequential_all_fail(self, challenge_manager, mock_plugin_manager, sample_challenge):
        """Test resolución secuencial - todos fallan"""
        fail_result = SolutionResult(success=False, error_message="Failed")
        
        mock_plugin_manager.select_best_plugins.return_value = [
            ("plugin1", Mock(), 0.9),
            ("plugin2", Mock(), 0.7)
        ]
        mock_plugin_manager.solve_with_plugin.return_value = fail_result
        
        result = challenge_manager._solve_sequential(sample_challenge)
        
        assert result.success is False
        assert "Ningún plugin pudo resolver" in result.error_message
    
    def test_solve_parallel_success(self, challenge_manager, mock_plugin_manager, sample_challenge):
        """Test resolución paralela exitosa"""
        success_result = SolutionResult(success=True, flag="CTF{parallel}")
        
        mock_plugin_manager.select_best_plugins.return_value = [
            ("plugin1", Mock(), 0.9),
            ("plugin2", Mock(), 0.7)
        ]
        
        # Mock del executor
        mock_future = Mock()
        mock_future.result.return_value = success_result
        challenge_manager._executor.submit = Mock(return_value=mock_future)
        
        result = challenge_manager._solve_parallel(sample_challenge)
        
        assert result.success is True
        assert result.flag == "CTF{parallel}"
    
    def test_solve_challenge_auto_strategy(self, challenge_manager, mock_file_analyzer, 
                                         mock_plugin_manager, sample_challenge):
        """Test resolución completa con estrategia automática"""
        # Configurar mocks
        success_result = SolutionResult(success=True, flag="CTF{auto}")
        mock_plugin_manager.select_best_plugins.return_value = [("plugin1", Mock(), 0.9)]
        mock_plugin_manager.solve_with_plugin.return_value = success_result
        
        # Resolver
        result = challenge_manager.solve_challenge(sample_challenge, strategy="auto")
        
        assert result.success is True
        assert result.flag == "CTF{auto}"
        assert result.execution_time > 0
        assert len(challenge_manager._solution_history) == 1
        assert challenge_manager._stats['successful_solutions'] == 1
    
    def test_solve_challenge_validation_error(self, challenge_manager):
        """Test resolución con error de validación"""
        # Desafío inválido
        invalid_challenge = ChallengeData(id="invalid", name="Invalid")
        
        result = challenge_manager.solve_challenge(invalid_challenge)
        
        assert result.success is False
        assert "debe tener archivos o información de red" in result.error_message
        assert len(challenge_manager._solution_history) == 1
        assert challenge_manager._stats['failed_solutions'] == 1
    
    def test_register_solution_success(self, challenge_manager, sample_challenge):
        """Test registro de solución exitosa"""
        result = SolutionResult(
            success=True,
            flag="CTF{test}",
            execution_time=1.5,
            plugin_name="test_plugin"
        )
        
        challenge_manager._active_challenges[sample_challenge.id] = sample_challenge
        challenge_manager._register_solution(sample_challenge, result)
        
        assert len(challenge_manager._solution_history) == 1
        assert challenge_manager._stats['successful_solutions'] == 1
        assert challenge_manager._stats['average_solve_time'] == 1.5
        assert challenge_manager._stats['plugin_usage']['test_plugin'] == 1
        assert sample_challenge.id not in challenge_manager._active_challenges
    
    def test_register_solution_failure(self, challenge_manager, sample_challenge):
        """Test registro de solución fallida"""
        result = SolutionResult(
            success=False,
            error_message="Failed",
            execution_time=2.0
        )
        
        challenge_manager._register_solution(sample_challenge, result)
        
        assert len(challenge_manager._solution_history) == 1
        assert challenge_manager._stats['failed_solutions'] == 1
        assert challenge_manager._stats['average_solve_time'] == 2.0
    
    def test_get_active_challenges(self, challenge_manager, sample_challenge):
        """Test obtener desafíos activos"""
        challenge_manager._active_challenges[sample_challenge.id] = sample_challenge
        
        active = challenge_manager.get_active_challenges()
        
        assert sample_challenge.id in active
        assert active[sample_challenge.id] == sample_challenge
        # Verificar que es una copia
        assert active is not challenge_manager._active_challenges
    
    def test_get_solution_history(self, challenge_manager):
        """Test obtener historial de soluciones"""
        result1 = SolutionResult(success=True, flag="CTF{1}")
        result2 = SolutionResult(success=False, error_message="Failed")
        
        challenge_manager._solution_history = [result1, result2]
        
        history = challenge_manager.get_solution_history()
        
        assert len(history) == 2
        assert history[0] == result1
        assert history[1] == result2
        # Verificar que es una copia
        assert history is not challenge_manager._solution_history
    
    def test_get_statistics(self, challenge_manager, mock_plugin_manager):
        """Test obtener estadísticas"""
        # Configurar estado
        challenge_manager._stats = {
            'total_challenges': 10,
            'successful_solutions': 7,
            'failed_solutions': 3,
            'average_solve_time': 2.5,
            'plugin_usage': {'plugin1': 5, 'plugin2': 2}
        }
        challenge_manager._active_challenges = {'active1': Mock()}
        
        mock_plugin_manager.get_plugin_statistics.return_value = {'total_plugins': 5}
        
        stats = challenge_manager.get_statistics()
        
        assert stats['total_challenges'] == 10
        assert stats['successful_solutions'] == 7
        assert stats['active_challenges'] == 1
        assert stats['success_rate'] == 70.0
        assert 'plugin_manager_stats' in stats
    
    def test_clear_history(self, challenge_manager):
        """Test limpiar historial"""
        # Agregar datos
        challenge_manager._solution_history = [Mock(), Mock()]
        challenge_manager._stats['total_challenges'] = 5
        
        # Limpiar
        challenge_manager.clear_history()
        
        assert len(challenge_manager._solution_history) == 0
        assert challenge_manager._stats['total_challenges'] == 0
        assert challenge_manager._stats['successful_solutions'] == 0
    
    def test_cancel_challenge(self, challenge_manager, sample_challenge):
        """Test cancelar desafío"""
        # Agregar desafío activo
        challenge_manager._active_challenges[sample_challenge.id] = sample_challenge
        
        # Cancelar
        result = challenge_manager.cancel_challenge(sample_challenge.id)
        
        assert result is True
        assert sample_challenge.id not in challenge_manager._active_challenges
        
        # Cancelar inexistente
        result = challenge_manager.cancel_challenge("nonexistent")
        assert result is False
    
    def test_estimate_difficulty_beginner(self, challenge_manager, mock_plugin_manager, sample_challenge):
        """Test estimación de dificultad - principiante"""
        # Configurar plugins con alta confianza
        mock_plugin = Mock()
        mock_plugin.can_handle.return_value = 0.95
        
        mock_plugin_manager.get_available_plugins.return_value = ["plugin1"]
        mock_plugin_manager.get_plugin.return_value = mock_plugin
        
        difficulty = challenge_manager.estimate_difficulty(sample_challenge)
        assert difficulty == DifficultyLevel.BEGINNER
    
    def test_estimate_difficulty_expert(self, challenge_manager, mock_plugin_manager, sample_challenge):
        """Test estimación de dificultad - experto"""
        # Configurar plugins con baja confianza
        mock_plugin = Mock()
        mock_plugin.can_handle.return_value = 0.1
        
        mock_plugin_manager.get_available_plugins.return_value = ["plugin1"]
        mock_plugin_manager.get_plugin.return_value = mock_plugin
        
        difficulty = challenge_manager.estimate_difficulty(sample_challenge)
        assert difficulty == DifficultyLevel.EXPERT
    
    def test_estimate_difficulty_no_plugins(self, challenge_manager, mock_plugin_manager, sample_challenge):
        """Test estimación sin plugins disponibles"""
        mock_plugin_manager.get_available_plugins.return_value = []
        
        difficulty = challenge_manager.estimate_difficulty(sample_challenge)
        assert difficulty == DifficultyLevel.EXPERT
    
    @patch('asyncio.get_event_loop')
    def test_solve_challenge_async(self, mock_get_loop, challenge_manager, sample_challenge):
        """Test resolución asíncrona"""
        mock_loop = Mock()
        mock_future = Mock()
        mock_loop.run_in_executor.return_value = mock_future
        mock_get_loop.return_value = mock_loop
        
        result = challenge_manager.solve_challenge_async(sample_challenge, "auto")
        
        assert result == mock_future
        mock_loop.run_in_executor.assert_called_once()
    
    def test_execute_strategy_invalid(self, challenge_manager, sample_challenge):
        """Test ejecutar estrategia inválida"""
        with pytest.raises(ValidationError, match="Estrategia no soportada"):
            challenge_manager._execute_strategy(sample_challenge, "invalid_strategy")


if __name__ == "__main__":
    pytest.main([__file__])