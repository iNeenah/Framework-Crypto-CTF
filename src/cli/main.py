"""
CLI Principal - Interfaz de línea de comandos para Crypto CTF Solver
"""

import argparse
import sys
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

from ..core.challenge_manager import ChallengeManager
from ..core.file_analyzer import FileAnalyzer
from ..core.plugin_manager import plugin_manager
from ..ml.training.training_manager import TrainingManager
from ..models.data import ChallengeType, NetworkInfo
from ..utils.logging import setup_logging, get_logger
from ..utils.config import config


class CryptoCTFSolverCLI:
    """Interfaz de línea de comandos principal"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.challenge_manager = ChallengeManager()
        self.file_analyzer = FileAnalyzer()
        self.training_manager = TrainingManager()
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Crear parser de argumentos"""
        parser = argparse.ArgumentParser(
            prog='crypto-ctf-solver',
            description='Solucionador automático de desafíos CTF de criptografía',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Ejemplos de uso:
  crypto-ctf-solver solve challenge.zip
  crypto-ctf-solver solve --strategy parallel challenge.tar.gz
  crypto-ctf-solver network --host example.com --port 1337 --protocol tcp
  crypto-ctf-solver analyze challenge_file.txt
  crypto-ctf-solver plugins --list
  crypto-ctf-solver train --export training_data.json
            """
        )
        
        # Argumentos globales
        parser.add_argument(
            '--verbose', '-v',
            action='count',
            default=0,
            help='Aumentar verbosidad (usar -v, -vv, -vvv)'
        )
        
        parser.add_argument(
            '--config',
            type=str,
            help='Archivo de configuración personalizado'
        )
        
        parser.add_argument(
            '--output', '-o',
            type=str,
            help='Archivo de salida para resultados'
        )
        
        # Subcomandos
        subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
        
        # Comando solve
        solve_parser = subparsers.add_parser('solve', help='Resolver desafío desde archivo')
        solve_parser.add_argument('file', help='Archivo del desafío')
        solve_parser.add_argument(
            '--strategy',
            choices=['auto', 'single', 'sequential', 'parallel'],
            default='auto',
            help='Estrategia de resolución'
        )
        solve_parser.add_argument(
            '--timeout',
            type=int,
            default=300,
            help='Timeout en segundos'
        )
        solve_parser.add_argument(
            '--plugins',
            nargs='+',
            help='Plugins específicos a usar'
        )
        
        # Comando network
        network_parser = subparsers.add_parser('network', help='Resolver desafío de red')
        network_parser.add_argument('--host', required=True, help='Host del servidor')
        network_parser.add_argument('--port', type=int, required=True, help='Puerto del servidor')
        network_parser.add_argument(
            '--protocol',
            choices=['tcp', 'udp', 'http', 'https'],
            default='tcp',
            help='Protocolo de conexión'
        )
        network_parser.add_argument('--ssl', action='store_true', help='Usar SSL/TLS')
        network_parser.add_argument(
            '--timeout',
            type=int,
            default=30,
            help='Timeout de conexión'
        )
        
        # Comando analyze
        analyze_parser = subparsers.add_parser('analyze', help='Analizar archivo sin resolver')
        analyze_parser.add_argument('file', help='Archivo a analizar')
        analyze_parser.add_argument(
            '--detailed',
            action='store_true',
            help='Análisis detallado'
        )
        
        # Comando plugins
        plugins_parser = subparsers.add_parser('plugins', help='Gestión de plugins')
        plugins_group = plugins_parser.add_mutually_exclusive_group(required=True)
        plugins_group.add_argument('--list', action='store_true', help='Listar plugins')
        plugins_group.add_argument('--info', help='Información de plugin específico')
        plugins_group.add_argument('--reload', help='Recargar plugin específico')
        plugins_group.add_argument('--stats', action='store_true', help='Estadísticas de plugins')
        
        # Comando train
        train_parser = subparsers.add_parser('train', help='Entrenamiento de ML')
        train_group = train_parser.add_mutually_exclusive_group(required=True)
        train_group.add_argument('--train', action='store_true', help='Entrenar clasificador')
        train_group.add_argument('--export', help='Exportar datos de entrenamiento')
        train_group.add_argument('--stats', action='store_true', help='Estadísticas de ML')
        train_group.add_argument('--predict', help='Predecir tipo de desafío')
        
        # Comando config
        config_parser = subparsers.add_parser('config', help='Configuración')
        config_group = config_parser.add_mutually_exclusive_group(required=True)
        config_group.add_argument('--show', action='store_true', help='Mostrar configuración')
        config_group.add_argument('--set', nargs=2, metavar=('KEY', 'VALUE'), help='Establecer valor')
        config_group.add_argument('--reset', action='store_true', help='Resetear configuración')
        
        return parser
    
    def setup_logging_level(self, verbose: int) -> None:
        """Configurar nivel de logging basado en verbosidad"""
        if verbose == 0:
            level = 'WARNING'
        elif verbose == 1:
            level = 'INFO'
        elif verbose == 2:
            level = 'DEBUG'
        else:
            level = 'DEBUG'
        
        setup_logging(level=level)
    
    def solve_file_challenge(self, args) -> Dict[str, Any]:
        """Resolver desafío desde archivo"""
        file_path = Path(args.file)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        self.logger.info(f"Resolviendo desafío: {file_path}")
        
        # Cargar desafío
        challenge_data = self.challenge_manager.load_challenge(file_path)
        
        # Configurar timeout si se especifica
        if args.timeout:
            config.plugins.plugin_timeout = args.timeout
        
        # Resolver desafío
        start_time = time.time()
        result = self.challenge_manager.solve_challenge(challenge_data, strategy=args.strategy)
        total_time = time.time() - start_time
        
        # Almacenar para ML si fue exitoso
        if result.success:
            self.training_manager.store_challenge(challenge_data, challenge_data.challenge_type)
            self.training_manager.store_solution(challenge_data.id, result)
        
        return {
            'challenge_id': challenge_data.id,
            'challenge_name': challenge_data.name,
            'challenge_type': challenge_data.challenge_type.value,
            'strategy_used': args.strategy,
            'success': result.success,
            'flag': result.flag,
            'method_used': result.method_used,
            'confidence': result.confidence,
            'execution_time': result.execution_time,
            'total_time': total_time,
            'error_message': result.error_message,
            'plugin_name': result.plugin_name
        }
    
    def solve_network_challenge(self, args) -> Dict[str, Any]:
        """Resolver desafío de red"""
        self.logger.info(f"Conectando a {args.host}:{args.port} ({args.protocol})")
        
        # Crear información de red
        network_info = NetworkInfo(
            host=args.host,
            port=args.port,
            protocol=args.protocol,
            ssl=args.ssl,
            timeout=args.timeout
        )
        
        # Crear desafío de red
        from ..models.data import ChallengeData
        challenge_data = ChallengeData(
            id=f"network_{args.host}_{args.port}",
            name=f"Network Challenge {args.host}:{args.port}",
            description=f"Remote challenge at {args.host}:{args.port}",
            challenge_type=ChallengeType.NETWORK,
            network_info=network_info
        )
        
        # Resolver
        start_time = time.time()
        result = self.challenge_manager.solve_challenge(challenge_data)
        total_time = time.time() - start_time
        
        return {
            'host': args.host,
            'port': args.port,
            'protocol': args.protocol,
            'success': result.success,
            'flag': result.flag,
            'method_used': result.method_used,
            'confidence': result.confidence,
            'execution_time': result.execution_time,
            'total_time': total_time,
            'error_message': result.error_message
        }
    
    def analyze_file(self, args) -> Dict[str, Any]:
        """Analizar archivo sin resolver"""
        file_path = Path(args.file)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        self.logger.info(f"Analizando archivo: {file_path}")
        
        # Analizar archivo
        challenge_data = self.file_analyzer.analyze_file(file_path)
        
        # Predicción ML si está disponible
        ml_prediction = None
        try:
            predicted_type, confidence, explanation = self.training_manager.predict_challenge_type(challenge_data)
            ml_prediction = {
                'predicted_type': predicted_type.value,
                'confidence': confidence,
                'explanation': explanation
            }
        except Exception as e:
            self.logger.debug(f"Error en predicción ML: {e}")
        
        # Estimación de dificultad
        difficulty = self.challenge_manager.estimate_difficulty(challenge_data)
        
        result = {
            'file_path': str(file_path),
            'challenge_id': challenge_data.id,
            'challenge_name': challenge_data.name,
            'detected_type': challenge_data.challenge_type.value,
            'difficulty': difficulty.value,
            'file_count': len(challenge_data.files),
            'total_size': sum(f.size for f in challenge_data.files),
            'tags': challenge_data.tags,
            'metadata': challenge_data.metadata
        }
        
        if ml_prediction:
            result['ml_prediction'] = ml_prediction
        
        if args.detailed:
            result['files'] = [
                {
                    'path': str(f.path),
                    'size': f.size,
                    'mime_type': f.mime_type,
                    'hash_md5': f.hash_md5,
                    'hash_sha256': f.hash_sha256
                }
                for f in challenge_data.files
            ]
        
        return result
    
    def manage_plugins(self, args) -> Dict[str, Any]:
        """Gestión de plugins"""
        if args.list:
            plugins = plugin_manager.get_available_plugins()
            plugin_info = {}
            
            for plugin_name in plugins:
                info = plugin_manager.get_plugin_info(plugin_name)
                if info:
                    plugin_info[plugin_name] = {
                        'version': info.version,
                        'description': info.description,
                        'supported_types': [t.value for t in info.supported_types],
                        'techniques': info.techniques,
                        'priority': info.priority,
                        'enabled': info.enabled
                    }
            
            return {'plugins': plugin_info}
        
        elif args.info:
            info = plugin_manager.get_plugin_info(args.info)
            if not info:
                raise ValueError(f"Plugin no encontrado: {args.info}")
            
            return {
                'plugin_name': args.info,
                'version': info.version,
                'description': info.description,
                'supported_types': [t.value for t in info.supported_types],
                'techniques': info.techniques,
                'priority': info.priority,
                'enabled': info.enabled
            }
        
        elif args.reload:
            success = plugin_manager.reload_plugin(args.reload)
            return {
                'plugin_name': args.reload,
                'reloaded': success
            }
        
        elif args.stats:
            return plugin_manager.get_plugin_statistics()
    
    def manage_training(self, args) -> Dict[str, Any]:
        """Gestión de entrenamiento ML"""
        if args.train:
            try:
                metrics = self.training_manager.train_classifier()
                return {
                    'training_completed': True,
                    'metrics': metrics
                }
            except ValueError as e:
                return {
                    'training_completed': False,
                    'error': str(e)
                }
        
        elif args.export:
            self.training_manager.export_training_data(args.export)
            return {
                'exported_to': args.export,
                'total_examples': len(self.training_manager.get_training_data())
            }
        
        elif args.stats:
            return self.training_manager.get_statistics()
        
        elif args.predict:
            file_path = Path(args.predict)
            if not file_path.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
            
            challenge_data = self.file_analyzer.analyze_file(file_path)
            predicted_type, confidence, explanation = self.training_manager.predict_challenge_type(challenge_data)
            
            return {
                'file_path': str(file_path),
                'predicted_type': predicted_type.value,
                'confidence': confidence,
                'explanation': explanation
            }
    
    def manage_config(self, args) -> Dict[str, Any]:
        """Gestión de configuración"""
        if args.show:
            return {
                'plugins': {
                    'enabled_plugins': config.plugins.enabled_plugins,
                    'max_concurrent_plugins': config.plugins.max_concurrent_plugins,
                    'plugin_timeout': config.plugins.plugin_timeout
                },
                'logging': {
                    'level': config.logging.level,
                    'format': config.logging.format
                }
            }
        
        elif args.set:
            key, value = args.set
            # Implementar lógica de configuración
            return {
                'key': key,
                'value': value,
                'updated': True
            }
        
        elif args.reset:
            # Implementar reset de configuración
            return {'reset': True}
    
    def format_output(self, result: Dict[str, Any], format_type: str = 'json') -> str:
        """Formatear salida"""
        if format_type == 'json':
            return json.dumps(result, indent=2, ensure_ascii=False)
        else:
            # Formato legible para humanos
            output = []
            
            if 'success' in result:
                status = "✅ ÉXITO" if result['success'] else "❌ FALLO"
                output.append(f"Estado: {status}")
                
                if result.get('flag'):
                    output.append(f"Flag: {result['flag']}")
                
                if result.get('method_used'):
                    output.append(f"Método: {result['method_used']}")
                
                if result.get('execution_time'):
                    output.append(f"Tiempo: {result['execution_time']:.2f}s")
                
                if result.get('error_message'):
                    output.append(f"Error: {result['error_message']}")
            
            return '\n'.join(output)
    
    def run(self, args=None) -> int:
        """Ejecutar CLI"""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        # Configurar logging
        self.setup_logging_level(parsed_args.verbose)
        
        # Verificar comando
        if not parsed_args.command:
            parser.print_help()
            return 1
        
        try:
            # Ejecutar comando
            if parsed_args.command == 'solve':
                result = self.solve_file_challenge(parsed_args)
            elif parsed_args.command == 'network':
                result = self.solve_network_challenge(parsed_args)
            elif parsed_args.command == 'analyze':
                result = self.analyze_file(parsed_args)
            elif parsed_args.command == 'plugins':
                result = self.manage_plugins(parsed_args)
            elif parsed_args.command == 'train':
                result = self.manage_training(parsed_args)
            elif parsed_args.command == 'config':
                result = self.manage_config(parsed_args)
            else:
                parser.print_help()
                return 1
            
            # Formatear y mostrar resultado
            if parsed_args.verbose > 0:
                output = self.format_output(result, 'json')
            else:
                output = self.format_output(result, 'human')
            
            # Guardar en archivo si se especifica
            if parsed_args.output:
                with open(parsed_args.output, 'w', encoding='utf-8') as f:
                    f.write(self.format_output(result, 'json'))
                print(f"Resultado guardado en: {parsed_args.output}")
            
            print(output)
            return 0
            
        except Exception as e:
            self.logger.error(f"Error ejecutando comando: {e}")
            if parsed_args.verbose > 1:
                import traceback
                traceback.print_exc()
            
            error_result = {
                'error': str(e),
                'command': parsed_args.command
            }
            print(self.format_output(error_result, 'json'))
            return 1


def main():
    """Punto de entrada principal"""
    cli = CryptoCTFSolverCLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())