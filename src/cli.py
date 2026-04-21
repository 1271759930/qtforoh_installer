"""
CLI entry point - Command definitions and dispatch
"""

import sys
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Fix encoding for Windows PowerShell
if sys.platform == "win32":
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")

# Import from new module structure
from .core import QtHarmonyInstaller
from .config import ConfigManager
from .ui.display import Display
from .utils import check_python_version, check_llvm_mingw, check_perl


console = Console(force_terminal=True)
display = Display()


@click.group()
@click.version_option(version="1.0.0", prog_name="qtohos-installer")
def cli():
    """
    Qt for HarmonyOS Cross-Compilation CLI Tool

    This tool cross-compiles Qt framework for HarmonyOS platform on Windows.
    It helps you by:
    - Collecting necessary paths and configurations
    - Downloading required tools (make, perl)
    - Configuring cross-compilation environment
    - Compiling Qt source with HarmonyOS SDK toolchain
    - Installing Qt SDK to local Windows path
    """
    pass


@cli.command()
@click.option(
    "--workspace", "-w",
    type=click.Path(exists=False),
    default=".",
    help="Workspace directory for installation"
)
@click.option(
    "--yes", "-y",
    is_flag=True,
    default=False,
    help="Skip confirmation prompts (use existing config)"
)
def install(workspace: str, yes: bool):
    """
    Run interactive installation process

    This command will:
    1. Prompt for Qt source path, HarmonyOS SDK path, and installation path
    2. Download required tools (make, perl)
    3. Setup environment variables
    4. Build and install Qt for HarmonyOS
    """
    workspace_path = Path(workspace).resolve()

    console.print("\n[bold cyan]Qt for HarmonyOS Installation Tool[/bold cyan]")
    console.print(f"Workspace: {workspace_path}\n")

    installer = QtHarmonyInstaller(workspace_path, auto_confirm=yes)

    if installer.run():
        console.print("\n[bold green]✓ Installation successful![/bold green]")
        sys.exit(0)
    else:
        console.print("\n[bold red]✗ Installation failed[/bold red]")
        sys.exit(1)


@cli.command()
@click.option(
    "--workspace", "-w",
    type=click.Path(exists=True),
    default=".",
    help="Workspace directory"
)
def config(workspace: str):
    """
    View or modify configuration

    Shows current configuration and allows modification.
    """
    workspace_path = Path(workspace).resolve()
    config_manager = ConfigManager(workspace_path / "config.yaml")

    if config_manager.load_config():
        console.print("\n[bold cyan]Current Configuration:[/bold cyan]\n")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        cfg = config_manager.install_config
        if cfg:
            table.add_row("Qt Source Path", str(cfg.qt_source_path))
            table.add_row("HarmonyOS SDK Path", str(cfg.harmony_sdk_path))
            table.add_row("Base Install Path", str(cfg.install_path))
            table.add_row("Actual Install Path", str(cfg.actual_install_path))
            table.add_row("Architecture", cfg.architecture)
            table.add_row("Qt Version", cfg.qt_version)
            table.add_row("Build Type", cfg.build_type)
            table.add_row("Parallel Jobs", str(cfg.parallel_jobs))

            console.print(table)
    else:
        console.print("\n[yellow]No configuration found[/yellow]")
        console.print("Run 'qtohos-installer install' to create configuration")


@cli.command()
@click.option(
    "--workspace", "-w",
    type=click.Path(exists=True),
    default=".",
    help="Workspace directory"
)
def check(workspace: str):
    """
    Check prerequisites and environment

    Validates that all required tools and paths are available.
    """
    workspace_path = Path(workspace).resolve()
    config_manager = ConfigManager(workspace_path / "config.yaml")

    console.print("\n[bold cyan]Checking Prerequisites...[/bold cyan]\n")

    # Check Python version
    is_valid, version = check_python_version()
    if is_valid:
        console.print(f"[green]✓ Python: {version}[/green]")
    else:
        console.print(f"[red]✗ Python: {version}[/red]")

    # Check Git
    import shutil
    if shutil.which("git"):
        console.print("[green]✓ Git is available[/green]")
    else:
        console.print("[red]✗ Git is not installed[/red]")

    # Check llvm-mingw make
    is_valid, message, hint = check_llvm_mingw()
    if is_valid:
        console.print(f"[green]✓ {message}[/green]")
    else:
        console.print(f"[yellow]⚠ {message}[/yellow]")
        if hint:
            console.print(f"[cyan]    {hint}[/cyan]")

    # Check Perl
    is_valid, message, hint = check_perl()
    if is_valid:
        console.print(f"[green]✓ {message}[/green]")
    else:
        console.print(f"[yellow]⚠ {message}[/yellow]")
        if hint:
            console.print(f"[cyan]    {hint}[/cyan]")

    # Check configuration
    if config_manager.load_config():
        console.print("\n[bold cyan]Checking Configuration...[/bold cyan]\n")

        cfg = config_manager.install_config
        if cfg:
            # Check Qt source
            if cfg.qt_source_path.exists():
                console.print(f"[green]✓ Qt source: {cfg.qt_source_path}[/green]")
            else:
                console.print(f"[red]✗ Qt source not found: {cfg.qt_source_path}[/red]")

            # Check HarmonyOS SDK
            if cfg.harmony_sdk_path.exists():
                console.print(f"[green]✓ HarmonyOS SDK: {cfg.harmony_sdk_path}[/green]")
                native_path = cfg.harmony_sdk_path / "native"
                if native_path.exists():
                    console.print(f"[green]  ✓ Native SDK: {native_path}[/green]")
                else:
                    console.print(f"[red]  ✗ Native SDK not found[/red]")
            else:
                console.print(f"[red]✗ HarmonyOS SDK not found: {cfg.harmony_sdk_path}[/red]")
    else:
        console.print("\n[yellow]No configuration found[/yellow]")

    console.print("\n[bold cyan]Check Complete[/bold cyan]")


@cli.command()
def guide():
    """
    Show installation guide and documentation

    Displays helpful information about the installation process.
    """
    guide_text = """
[bold cyan]Qt for HarmonyOS Installation Guide[/bold cyan]

[bold]Prerequisites:[/bold]
  • Python >= 3.12
  • Git >= 2.39.3
  • HarmonyOS SDK (API >= 15, recommended API 17)
  • Qt source code (tqtc-qt5)

[bold]Step-by-Step Process:[/bold]

1. [yellow]Prepare Qt Source Code[/yellow]
   git clone https://codereview.qt-project.org/qt/tqtc-qt5
   cd tqtc-qt5
   git checkout tqtc/harmonyos-5.15.16
   git submodule update --init --recursive

2. [yellow]Install HarmonyOS SDK[/yellow]
   Download from: https://developer.huawei.com/consumer/cn/deveco-studio/
   Install DevEco Studio and SDK (API 17 recommended)

3. [yellow]Run Installation Tool[/yellow]
   qtohos-installer install

4. [yellow]Configure Qt Creator[/yellow]
   Add Qt version: <install_path>/bin/qmake
   Add compiler: <sdk_path>/native/llvm/bin/clang
   Create kit with ohos-clang mkspec

[bold]Official Documentation:[/bold]
  https://wiki.qt.io/Building_Qt_for_HarmonyOS

[bold]Troubleshooting:[/bold]
  • If make/perl missing, tool will attempt to download
  • Check logs in workspace/logs/ directory
  • Run 'qtohos-installer check' to verify prerequisites
    """

    console.print(Panel(guide_text, border_style="cyan"))


@cli.command()
@click.option(
    "--workspace", "-w",
    type=click.Path(exists=True),
    default=".",
    help="Workspace directory"
)
def clean(workspace: str):
    """
    Clean build artifacts and temporary files

    Removes build directory and temporary files, but keeps configuration.
    """
    workspace_path = Path(workspace).resolve()
    config_manager = ConfigManager(workspace_path / "config.yaml")

    if not config_manager.load_config():
        console.print("\n[yellow]No configuration found[/yellow]")
        return

    cfg = config_manager.install_config
    if not cfg:
        return

    console.print("\n[bold cyan]Cleaning build artifacts...[/bold cyan]")

    # Clean build directory
    build_dir = cfg.qt_source_path / f"build_{cfg.architecture}"
    if build_dir.exists():
        console.print(f"Removing: {build_dir}")
        import shutil
        try:
            shutil.rmtree(build_dir)
            console.print("[green]✓ Build directory removed[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to remove build directory: {e}[/red]")

    # Clean logs
    logs_dir = workspace_path / "logs"
    if logs_dir.exists():
        console.print(f"Removing: {logs_dir}")
        try:
            shutil.rmtree(logs_dir)
            console.print("[green]✓ Logs directory removed[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to remove logs directory: {e}[/red]")

    console.print("\n[bold green]✓ Clean complete[/bold green]")
    console.print("[yellow]Note: Configuration preserved[/yellow]")


def main():
    """Main entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()