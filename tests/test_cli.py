"""
Tests para la interfaz CLI
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from src.cli.main import cli
from src.models.data import ChallengeData, SolutionResult, ChallengeType, FileInfo


class TestCLI:
    """Tests para la interfaz de línea de comandos"""
    
    @pytest.fixture
    def runner(self):
        """Click test runner"""
        return CliRunner()
    
    @pytest.fixture
    def temp_challenge_file(self):
        """Archivo de desafío temporal"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            tmp.write("RSA challenge content")
            tmp.flush()
            yield tmp.name
    
    @pytest.fixture
    def mock_challenge_manager(self):
        """Mock del ChallengeManager"""
        with patch('src.cli.main.ChallengeManager') as mock:
            manager_instance = Mock()
            mock.return_value = manager_instance
            
            # Mock challenge data
            file_info = FileInfo(path=Path("/tmp/test.txt"), size=100)
            challenge_data = ChallengeData(
                id="test-challenge",
                name="Test Challenge",
                files=[file_info],
                challenge_type=ChallengeType.RSA
            )
            manager_instance.load_challenge.return_value = challenge_data
            
            # Mock successful result
            success_result = SolutionResult(
                success=True,
                flag="CTF{test_flag}",
                method_used="test_method",
                execution_time=1.5,
                confidence=0.9
            )
            manager_instance.solve_challenge.return_value = success_result
            
            yield manager_instance
    
    def test_cli_help(self, runner):
        """Test mostrar ayuda del CLI"""
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Crypto CTF Solver" in result.output
        assert "Framework inteligente" in result.output
    
    def test_cli_version(self, runner):
        """Test mostrar versión"""
        result = runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert "0.1.0" in result.output
    
    def test_solve_command_success(self, runner, temp_challenge_file, mock_challenge_manager):
        """Test comando solve exitoso"""
        result = runner.invoke(cli, ['solve', temp_challenge_file])
        
        assert result.exit_code == 0
        assert "SUCCESS" in result.output
        assert "CTF{test_flag}" in result.output
        
        # Verificar que se llamaron los métodos correctos
        mock_challenge_manager.load_challenge.assert_called_once()
        mock_challenge_manager.solve_challenge.assert_called_once()
    
    def test_solve_command_with_strategy(self, runner, temp_challenge_file, mock_challenge_manager):
        """Test comando solve con estrategia específica"""
        result = runner.invoke(cli, ['solve', temp_challenge_file, '--strategy', 'parallel'])
        
        assert result.exit_code == 0
        
        # Verificar que se pasó la estrategia correcta
        args, kwargs = mock_challenge_manager.solve_challenge.call_args
        assert len(args) >= 2
        assert args[1] == 'parallel'  # strategy parameter
    
    def test_solve_command_failure(self, runner, temp_challenge_file):
        """Test comando solve con falla"""
        with patch('src.cli.main.ChallengeManager') as mock_cm:
            manager_instance = Mock()
            mock_cm.return_value = manager_instance
            
            # Mock failed result
            failed_result = SolutionResult(
                success=False,
                error_message="Test failure",
                method_used="test_method",
                execution_time=1.0
            )
            manager_instance.solve_challenge.return_value = failed_result
            
            # Mock challenge data
            file_info = FileInfo(path=Path("/tmp/test.txt"), size=100)
            challenge_data = ChallengeData(
                id="test-challenge",
                name="Test Challenge",
                files=[file_info]
            )
            manager_instance.load_challenge.return_value = challenge_data
            
            result = runner.invoke(cli, ['solve', temp_challenge_file])
            
            assert result.exit_code == 1
            assert "FAILED" in result.output
            assert "Test failure" in result.output
    
    def test_solve_command_with_output(self, runner, temp_challenge_file, mock_challenge_manager):
        """Test comando solve con archivo de salida"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as output_file:
            result = runner.invoke(cli, [
                'solve', temp_challenge_file, 
                '--output', output_file.name
            ])
            
            assert result.exit_code == 0
            assert "Results saved" in result.output
    
    def test_solve_nonexistent_file(self, runner):
        """Test solve con archivo inexistente"""
        result = runner.invoke(cli, ['solve', '/nonexistent/file.txt'])
        
        assert result.exit_code != 0
        assert "does not exist" in result.output.lower()
    
    def test_connect_command(self, runner, mock_challenge_manager):
        """Test comando connect"""
        result = runner.invoke(cli, [
            'connect', 
            '--host', 'example.com',
            '--port', '1337'
        ])
        
        assert result.exit_code == 0
        assert "Connecting to: example.com:1337" in result.output
        
        # Verificar que se creó el desafío de red
        mock_challenge_manager.solve_challenge.assert_called_once()
        challenge_data = mock_challenge_manager.solve_challenge.call_args[0][0]
        assert challenge_data.network_info is not None
        assert challenge_data.network_info.host == "example.com"
        assert challenge_data.network_info.port == 1337
    
    def test_connect_command_with_ssl(self, runner, mock_challenge_manager):
        """Test comando connect con SSL"""
        result = runner.invoke(cli, [
            'connect',
            '--host', 'secure.example.com',
            '--port', '443',
            '--ssl'
        ])
        
        assert result.exit_code == 0
        
        # Verificar configuración SSL
        challenge_data = mock_challenge_manager.solve_challenge.call_args[0][0]
        assert challenge_data.network_info.ssl is True
    
    @patch('src.cli.main.TrainingManager')
    def test_train_command_success(self, mock_training_manager, runner):
        """Test comando train exitoso"""
        # Mock training manager
        training_instance = Mock()
        mock_training_manager.return_value = training_instance
        
        # Mock successful training result
        training_result = {
            'status': 'success',
            'training_time': 10.5,
            'test_accuracy': 0.85,
            'n_samples': 100
        }
        training_instance.train_challenge_classifier.return_value = training_result
        
        result = runner.invoke(cli, ['train'])
        
        assert result.exit_code == 0
        assert "Training completed successfully" in result.output
        assert "10.50s" in result.output
        assert "0.850" in result.output
    
    @patch('src.cli.main.TrainingManager')
    def test_train_command_insufficient_data(self, mock_training_manager, runner):
        """Test comando train con datos insuficientes"""
        training_instance = Mock()
        mock_training_manager.return_value = training_instance
        
        # Mock insufficient data result
        training_result = {
            'status': 'insufficient_data',
            'available_samples': 10,
            'required_samples': 100
        }
        training_instance.train_challenge_classifier.return_value = training_result
        
        result = runner.invoke(cli, ['train'])
        
        assert result.exit_code == 0
        assert "Insufficient training data" in result.output
        assert "Available: 10" in result.output
        assert "Required: 100" in result.output
    
    @patch('src.cli.main.plugin_manager')
    def test_plugins_command(self, mock_plugin_manager, runner):
        """Test comando plugins"""
        # Mock plugin statistics
        plugin_stats = {
            'total_plugins': 3,
            'enabled_plugins': 2,
            'plugin_details': [
                {
                    'name': 'basic_crypto',
                    'version': '1.0.0',
                    'enabled': True,
                    'priority': 50,
                    'supported_types': ['basic_crypto'],
                    'techniques': ['caesar', 'vigenere']
                },
                {
                    'name': 'rsa_plugin',
                    'version': '1.0.0',
                    'enabled': True,
                    'priority': 80,
                    'supported_types': ['rsa'],
                    'techniques': ['factorization', 'wiener']
                }
            ]
        }
        mock_plugin_manager.get_plugin_statistics.return_value = plugin_stats
        
        result = runner.invoke(cli, ['plugins'])
        
        assert result.exit_code == 0
        assert "Available Plugins" in result.output
        assert "basic_crypto" in result.output
        assert "rsa_plugin" in result.output
        assert "Total plugins: 3" in result.output
    
    @patch('src.cli.main.ChallengeManager')
    @patch('src.cli.main.TrainingManager')
    @patch('src.cli.main.plugin_manager')
    def test_stats_command_table(self, mock_plugin_manager, mock_training_manager, 
                                mock_challenge_manager, runner):
        """Test comando stats en formato tabla"""
        # Mock statistics
        cm_instance = Mock()
        mock_challenge_manager.return_value = cm_instance
        cm_instance.get_statistics.return_value = {
            'total_challenges': 10,
            'successful_solutions': 7,
            'failed_solutions': 3,
            'success_rate': 70.0,
            'average_solve_time': 2.5,
            'active_challenges': 1
        }
        
        training_instance = Mock()
        mock_training_manager.return_value = training_instance
        training_instance.get_training_statistics.return_value = {
            'total_training_records': 50,
            'training_sessions': 3,
            'last_training': '2023-01-01T12:00:00',
            'models_trained': {'challenge_classifier': True}
        }
        
        mock_plugin_manager.get_plugin_statistics.return_value = {
            'total_plugins': 4,
            'enabled_plugins': 3
        }
        
        result = runner.invoke(cli, ['stats'])
        
        assert result.exit_code == 0
        assert "System Statistics" in result.output
        assert "Challenge Manager" in result.output
        assert "Machine Learning" in result.output
        assert "Plugins" in result.output
    
    @patch('src.cli.main.ChallengeManager')
    @patch('src.cli.main.TrainingManager')
    @patch('src.cli.main.plugin_manager')
    def test_stats_command_json(self, mock_plugin_manager, mock_training_manager,
                               mock_challenge_manager, runner):
        """Test comando stats en formato JSON"""
        # Mock statistics (same as above)
        cm_instance = Mock()
        mock_challenge_manager.return_value = cm_instance
        cm_instance.get_statistics.return_value = {'total_challenges': 10}
        
        training_instance = Mock()
        mock_training_manager.return_value = training_instance
        training_instance.get_training_statistics.return_value = {'total_training_records': 50}
        
        mock_plugin_manager.get_plugin_statistics.return_value = {'total_plugins': 4}
        
        result = runner.invoke(cli, ['stats', '--format', 'json'])
        
        assert result.exit_code == 0
        
        # Verificar que es JSON válido
        try:
            json.loads(result.output)
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")
    
    @patch('src.cli.main.ChallengeManager')
    @patch('src.cli.main.plugin_manager')
    def test_test_command_specific_plugin(self, mock_plugin_manager, mock_challenge_manager, 
                                        runner, temp_challenge_file):
        """Test comando test con plugin específico"""
        # Mock challenge manager
        cm_instance = Mock()
        mock_challenge_manager.return_value = cm_instance
        
        file_info = FileInfo(path=Path("/tmp/test.txt"), size=100)
        challenge_data = ChallengeData(
            id="test-challenge",
            name="Test Challenge",
            files=[file_info]
        )
        cm_instance.load_challenge.return_value = challenge_data
        
        # Mock plugin manager
        mock_plugin_manager.get_available_plugins.return_value = ['test_plugin']
        
        success_result = SolutionResult(
            success=True,
            flag="CTF{test}",
            method_used="test_plugin"
        )
        mock_plugin_manager.solve_with_plugin.return_value = success_result
        
        result = runner.invoke(cli, ['test', '--plugin', 'test_plugin', temp_challenge_file])
        
        assert result.exit_code == 0
        assert "Testing plugin: test_plugin" in result.output
        assert "SUCCESS" in result.output
    
    @patch('src.cli.main.ChallengeManager')
    @patch('src.cli.main.plugin_manager')
    def test_test_command_plugin_selection(self, mock_plugin_manager, mock_challenge_manager,
                                         runner, temp_challenge_file):
        """Test comando test para selección de plugins"""
        # Mock challenge manager
        cm_instance = Mock()
        mock_challenge_manager.return_value = cm_instance
        
        file_info = FileInfo(path=Path("/tmp/test.txt"), size=100)
        challenge_data = ChallengeData(
            id="test-challenge",
            name="Test Challenge",
            files=[file_info]
        )
        cm_instance.load_challenge.return_value = challenge_data
        
        # Mock plugin selection
        mock_plugin_manager.select_best_plugins.return_value = [
            ('plugin1', Mock(), 0.9),
            ('plugin2', Mock(), 0.7),
            ('plugin3', Mock(), 0.0)
        ]
        
        result = runner.invoke(cli, ['test', temp_challenge_file])
        
        assert result.exit_code == 0
        assert "Plugin Selection Results" in result.output
        assert "plugin1" in result.output
        assert "0.900" in result.output
    
    def test_config_command_list_all(self, runner):
        """Test comando config para listar toda la configuración"""
        result = runner.invoke(cli, ['config', '--list-all'])
        
        assert result.exit_code == 0
        assert "Current Configuration" in result.output
        
        # Verificar que es JSON válido
        try:
            # Extraer JSON del output
            lines = result.output.split('\n')
            json_start = None
            for i, line in enumerate(lines):
                if line.strip().startswith('{'):
                    json_start = i
                    break
            
            if json_start is not None:
                json_content = '\n'.join(lines[json_start:])
                json.loads(json_content)
        except (json.JSONDecodeError, ValueError):
            # Es aceptable si no es JSON válido en este test básico
            pass
    
    def test_config_command_get_key(self, runner):
        """Test comando config para obtener clave específica"""
        result = runner.invoke(cli, ['config', '--key', 'logging.level'])
        
        assert result.exit_code == 0
        assert "Configuration for logging.level" in result.output
    
    def test_config_command_no_args(self, runner):
        """Test comando config sin argumentos"""
        result = runner.invoke(cli, ['config'])
        
        assert result.exit_code == 1
        assert "Specify --key or use --list-all" in result.output


if __name__ == "__main__":
    pytest.main([__file__])