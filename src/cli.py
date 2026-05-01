"""
CLI entry point - Command definitions and dispatch
"""

import sys
from pathlib import Path
import click
from rich.console import Console

# Fix encoding for Windows PowerShell
if sys.platform == "win32":
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")

# Import from new module structure
from .core import QtHarmonyInstaller
from .ui.display import Display
from .ui.commands import do_check, do_config, do_guide, do_clean


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
    do_config(workspace_path)


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
    do_check(workspace_path)


@cli.command()
def guide():
    """
    Show installation guide and documentation

    Displays helpful information about the installation process.
    """
    do_guide()


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
    do_clean(workspace_path)


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