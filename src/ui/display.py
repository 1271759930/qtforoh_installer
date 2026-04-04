"""
Display module - Console output and formatting
"""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..config.schema import InstallConfig


class Display:
    """Console display handler - Only responsible for output"""

    def __init__(self):
        self.console = Console(force_terminal=True)

    def show_welcome(self) -> None:
        """Show welcome message"""
        welcome_text = """
[bold cyan]Qt for HarmonyOS Installation Tool[/bold cyan]

This tool will help you install Qt for HarmonyOS by:
  1. Collecting necessary paths and configurations
  2. Downloading required tools (make, perl)
  3. Configuring build environment
  4. Compiling and installing Qt

[yellow]Prerequisites:[/yellow]
  • Python >= 3.12
  • Git >= 2.39.3
  • HarmonyOS SDK (API >= 15, recommended API 17)
  • Qt source code (tqtc-qt5)

[green]Official Guide:[/green] https://wiki.qt.io/Building_Qt_for_HarmonyOS
        """
        self.console.print(Panel(welcome_text, border_style="cyan"))

    def show_step_title(self, step_number: int, title: str) -> None:
        """Show step title"""
        self.console.print(f"\n[bold cyan]Step {step_number}: {title}...[/bold cyan]")

    def show_success(self, message: str) -> None:
        """Show success message"""
        self.console.print(f"[green]✓[/green] {message}")

    def show_error(self, message: str) -> None:
        """Show error message"""
        self.console.print(f"[red]✗[/red] {message}")

    def show_warning(self, message: str) -> None:
        """Show warning message"""
        self.console.print(f"[yellow]⚠[/yellow] {message}")

    def show_info(self, message: str) -> None:
        """Show info message"""
        self.console.print(f"[cyan]{message}[/cyan]")

    def show_config_summary(self, config: InstallConfig) -> None:
        """Display configuration summary"""
        self.console.print("\n" + "=" * 60)
        self.console.print("[bold cyan]Configuration Summary[/bold cyan]\n")

        table = Table(show_header=False, box=None)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Qt Source Path", str(config.qt_source_path))
        table.add_row("HarmonyOS SDK Path", str(config.harmony_sdk_path))
        table.add_row("Install Path", str(config.install_path))
        table.add_row("Architecture", config.architecture)
        table.add_row("Qt Version", f"{config.qt_version} ({config.version_source})")
        table.add_row("Build Type", config.build_type)
        table.add_row("Parallel Jobs", str(config.parallel_jobs))

        # Show tool paths if configured
        if config.make_path:
            table.add_row("Make Path", str(config.make_path))
        if config.perl_path:
            table.add_row("Perl Path", str(config.perl_path))

        self.console.print(table)

    def show_completion_message(self, config: InstallConfig, workspace: Path) -> None:
        """Show completion message with next steps"""
        from ..utils import is_windows

        completion_text = f"""
[bold green]✓ Installation Completed Successfully![/bold green]

[bold cyan]Next Steps:[/bold cyan]

1. [yellow]Configure Qt Creator:[/yellow]
   • Add Qt version: {config.install_path}/bin/qmake
   • Add compiler: {config.harmony_sdk_path}/native/llvm/bin/clang
   • Create kit with ohos-clang mkspec

2. [yellow]Test your installation:[/yellow]
   • Create a simple Qt project
   • Build for HarmonyOS target
   • Deploy to device via DevEco Studio

3. [yellow]Environment setup for future builds:[/yellow]
   • Run: {workspace / ('setup_env.bat' if is_windows() else 'setup_env.sh')}

[bold cyan]Useful Resources:[/bold cyan]
  • Official Guide: https://wiki.qt.io/Building_Qt_for_HarmonyOS
  • Qt Documentation: https://doc.qt.io/
  • HarmonyOS Dev: https://developer.huawei.com/consumer/cn/

[bold cyan]Installed Qt Location:[/bold cyan]
  {config.install_path}
        """

        self.console.print(Panel(completion_text, border_style="green"))

    def print(self, message: str = "") -> None:
        """Print a message"""
        self.console.print(message)