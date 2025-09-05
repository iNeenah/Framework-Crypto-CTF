import os
import sys
import logging
import glob
import subprocess
import shlex

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.live import Live

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter, NestedCompleter

# --- Configuración de Path y Logging ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from src.main_agent import CryptoAgent

logging.basicConfig(filename='agent.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
console = Console()

class AgentTUI:
    def __init__(self):
        self.console = Console()
        self.agent = None
        self.history = FileHistory(os.path.join(PROJECT_ROOT, '.agent_history'))
        self.session = PromptSession(history=self.history, auto_suggest=AutoSuggestFromHistory())
        
        # State Management
        self.loaded_challenge_name = None
        self.loaded_challenge_path = None
        self.challenge_description = None
        self.challenge_port = None
        self.running_process = None

    def _get_commands_completer(self):
        """Crea un completer dinámico basado en los desafíos disponibles."""
        challenge_dirs = self._get_challenge_dirs()
        challenge_names = {name: None for name in challenge_dirs}

        return NestedCompleter.from_nested_dict({
            'challenges': None,
            'load': challenge_names,
            'run': None,
            'solve': None,
            'stop': None,
            'help': None,
            'exit': None,
        })

    def _initialize_agent(self):
        if self.agent is None:
            with self.console.status("[bold green]Inicializando el Agente Experto...[/bold green]"):
                try:
                    self.agent = CryptoAgent()
                    self.console.print(Panel("[bold green]¡Agente Experto listo y en línea![/bold green]", title="[cyan]Estado[/cyan]", expand=False))
                except Exception as e:
                    self.console.print(Panel(f"[bold red]Error fatal al inicializar el agente:[/bold red]\n{e}", title="[red]Error[/red]"))
                    return False
        return True

    def _get_challenge_dirs(self):
        live_challenges_path = os.path.join(PROJECT_ROOT, 'challenges', 'live', '*')
        return [os.path.basename(path) for path in glob.glob(live_challenges_path) if os.path.isdir(path)]

    def display_welcome(self):
        welcome_panel = Panel(
            "[bold blue]Bienvenido al Asistente Experto de Criptografía CTF[/bold blue]\n\n" 
            "Escribe `help` para ver los comandos disponibles.",
            title="Crypto Agent v3.0 - Live Hacking Edition",
            expand=False,
            border_style="cyan"
        )
        self.console.print(welcome_panel)

    def display_help(self):
        help_text = """
        [bold]Flujo de Trabajo:[/bold] `challenges` -> `load <nombre>` -> `run` -> `solve` -> `stop`

        [bold]Comandos Disponibles:[/bold]
        - `challenges`: Lista los desafíos disponibles en `challenges/live/`.
        - `load <nombre>`: Carga un desafío para trabajar en él.
        - `run`: Ejecuta el servidor del desafío cargado en segundo plano.
        - `solve`: Intenta resolver el desafío que está corriendo actualmente.
        - `stop`: Detiene el servidor del desafío que está corriendo.
        - `help`: Muestra este mensaje de ayuda.
        - `exit`: Sale del programa.
        """
        self.console.print(Panel(Markdown(help_text), title="Ayuda"))

    def handle_command(self, user_input):
        parts = shlex.split(user_input)
        if not parts:
            return
        command = parts[0].lower()

        if command == 'exit':
            self.console.print("[bold yellow]Saliendo del agente. ¡Hasta luego![/bold yellow]")
            if self.running_process:
                self.handle_command('stop')
            sys.exit(0)
        elif command == 'help':
            self.display_help()
        elif command == 'challenges':
            self.console.print(Panel("\n".join(self._get_challenge_dirs()), title="Desafíos Disponibles"))
        elif command == 'load':
            if len(parts) > 1:
                self._load_challenge(parts[1])
            else:
                self.console.print("[red]Uso: load <nombre_del_desafio>[/red]")
        elif command == 'run':
            self._run_challenge()
        elif command == 'stop':
            self._stop_challenge()
        elif command == 'solve':
            self._solve_challenge()
        else:
            self.console.print("[bold red]Comando no reconocido.[/bold red]")

    def _load_challenge(self, name):
        path = os.path.join(PROJECT_ROOT, 'challenges', 'live', name)
        if not os.path.isdir(path):
            self.console.print(f"[red]Error: No se encuentra el desafío '{name}'[/red]")
            return
        
        self.loaded_challenge_name = name
        self.loaded_challenge_path = path
        
        try:
            with open(os.path.join(path, 'README.md'), 'r') as f:
                self.challenge_description = f.read()
            with open(os.path.join(path, 'port.txt'), 'r') as f:
                self.challenge_port = int(f.read().strip())
            self.console.print(f"[green]Desafío '{name}' cargado.[/green]")
            self.console.print(Panel(self.challenge_description, title=f"Descripción de {name}"))
        except (FileNotFoundError, ValueError) as e:
            self.console.print(f"[red]Error: El paquete del desafío '{name}' es inválido. {e}[/red]")
            self.loaded_challenge_name = None # Reset state

    def _run_challenge(self):
        if not self.loaded_challenge_path:
            self.console.print("[red]Error: Ningún desafío cargado. Usa `load <nombre>` primero.[/red]")
            return
        if self.running_process:
            self.console.print(f"[yellow]El desafío '{self.loaded_challenge_name}' ya se está ejecutando (PID: {self.running_process.pid}). Usa `stop` primero.[/yellow]")
            return

        challenge_script = os.path.join(self.loaded_challenge_path, 'challenge.py')
        if not os.path.exists(challenge_script):
            self.console.print(f"[red]Error: No se encuentra el script `challenge.py` para '{self.loaded_challenge_name}'[/red]")
            return

        try:
            # Ejecutar en segundo plano
            self.running_process = subprocess.Popen([sys.executable, challenge_script], cwd=self.loaded_challenge_path)
            self.console.print(f"[green]Desafío '{self.loaded_challenge_name}' ejecutándose en segundo plano (PID: {self.running_process.pid}) en el puerto {self.challenge_port}.[/green]")
        except Exception as e:
            self.console.print(f"[red]Error al ejecutar el desafío: {e}[/red]")
            self.running_process = None

    def _stop_challenge(self):
        if not self.running_process:
            self.console.print("[yellow]Ningún desafío se está ejecutando.[/yellow]")
            return
        
        self.console.print(f"[yellow]Deteniendo el desafío '{self.loaded_challenge_name}' (PID: {self.running_process.pid})...")
        self.running_process.terminate() # Envía SIGTERM
        try:
            self.running_process.wait(timeout=5) # Espera a que termine
            self.console.print("[green]Proceso detenido exitosamente.[/green]")
        except subprocess.TimeoutExpired:
            self.console.print("[bold red]El proceso no terminó, forzando detención...[/bold red]")
            self.running_process.kill() # Envía SIGKILL
            self.console.print("[green]Proceso detenido.[/green]")
        
        self.running_process = None

    def _solve_challenge(self):
        if not self.running_process:
            self.console.print("[red]Error: Debes ejecutar un desafío con `run` antes de intentar resolverlo.[/red]")
            return
        if not self._initialize_agent():
            return

        solution_content = ""
        with Live(console=self.console, auto_refresh=True, vertical_overflow="visible") as live:
            for update in self.agent.solve(self.challenge_description, 'localhost', self.challenge_port):
                status = update.get("status")
                if status in ["embedding_query", "searching_kb", "retrieving_context", "generating_solution"]:
                    live.update(Panel(f"[bold cyan]>[/bold cyan] {update['message']}", title="Estado del Agente"))
                elif status == "found_results":
                    table = Table(title="Contexto Relevante Encontrado")
                    table.add_column("Similitud", style="cyan")
                    table.add_column("Fuente", style="magenta")
                    for res in update['data']:
                        table.add_row(f"{res['similarity']:.2f}%", os.path.basename(res['path']))
                    live.update(table)
                elif status == "solution_chunk":
                    solution_content += update['data']
                    live.update(Panel(Markdown(solution_content), title="[bold green]Respuesta del Agente (en progreso...)[/bold green]"))
                elif status == "done":
                    live.update(Panel(Markdown(solution_content), title="[bold green]Respuesta Final del Agente[/bold green]"))

    def run(self):
        self.display_welcome()
        while True:
            try:
                completer = self._get_commands_completer()
                user_input = self.session.prompt(
                    f"({self.loaded_challenge_name or 'No cargado'}) > ", 
                    auto_suggest=AutoSuggestFromHistory(),
                    completer=completer
                )
                self.handle_command(user_input)
            except KeyboardInterrupt:
                self.handle_command('exit')
            except Exception as e:
                logging.error(f"Error inesperado en el bucle principal: {e}")
                self.console.print(f"[bold red]Ha ocurrido un error inesperado: {e}[/bold red]")

if __name__ == "__main__":
    app = AgentTUI()
    app.run()
