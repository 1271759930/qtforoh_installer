"""
Shared command implementations - Used by both CLI and interactive menu
共享命令实现 - CLI 和交互式菜单共用
"""

import sys
import shutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..config import ConfigManager
from ..utils import check_python_version, check_llvm_mingw, check_perl, is_windows

console = Console(force_terminal=True)


def do_check(workspace_path: Path = None) -> None:
    """执行环境检查 / Check prerequisites and environment"""
    if workspace_path is None:
        workspace_path = Path(".").resolve()

    config_manager = ConfigManager(workspace_path / "config.yaml")

    console.print("\n[bold cyan]Checking Prerequisites...[/bold cyan]\n")

    # Check Python version
    is_valid, version = check_python_version()
    if is_valid:
        console.print(f"[green]✓ Python: {version}[/green]")
    else:
        console.print(f"[red]✗ Python: {version}[/red]")

    # Check Git
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


def do_config(workspace_path: Path = None) -> None:
    """显示当前配置 / Display current configuration"""
    if workspace_path is None:
        workspace_path = Path(".").resolve()

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
        console.print("Run 'install' to create configuration")


def do_guide() -> None:
    """显示安装指南 / Show installation guide"""
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
   python run.py

4. [yellow]Configure Qt Creator[/yellow]
   Add Qt version: <install_path>/bin/qmake
   Add compiler: <sdk_path>/native/llvm/bin/clang
   Create kit with ohos-clang mkspec

[bold]Official Documentation:[/bold]
  https://wiki.qt.io/Building_Qt_for_HarmonyOS

[bold]Troubleshooting:[/bold]
  • If make/perl missing, tool will attempt to download
  • Check logs in workspace/logs/ directory
  • Run 'check' to verify prerequisites
    """

    console.print(Panel(guide_text, border_style="cyan"))


def do_clean(workspace_path: Path = None) -> None:
    """清理构建产物 / Clean build artifacts"""
    if workspace_path is None:
        workspace_path = Path(".").resolve()

    config_manager = ConfigManager(workspace_path / "config.yaml")

    if not config_manager.load_config():
        console.print("\n[yellow]No configuration found[/yellow]")
        return

    cfg = config_manager.install_config
    if not cfg:
        return

    console.print("\n[bold cyan]Cleaning build artifacts...[/bold cyan]")

    # Clean build directory from workspace/temp
    build_dir = workspace_path / "temp" / f"build_{cfg.qt_version}_{cfg.architecture}"
    if build_dir.exists():
        console.print(f"Removing: {build_dir}")
        try:
            shutil.rmtree(build_dir)
            console.print("[green]✓ Build directory removed[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to remove build directory: {e}[/red]")
            console.print("[yellow]Try closing any programs using these files[/yellow]")

    # Clean temp directory if empty
    temp_dir = workspace_path / "temp"
    if temp_dir.exists() and temp_dir.is_dir():
        try:
            remaining = list(temp_dir.iterdir())
            if not remaining:
                shutil.rmtree(temp_dir)
                console.print("[green]✓ Empty temp directory removed[/green]")
        except Exception:
            pass

    # Clean logs - close logging handlers first
    logs_dir = workspace_path / "logs"
    if logs_dir.exists():
        console.print(f"Removing: {logs_dir}")
        try:
            # Close all logging handlers to release file handles
            import logging
            logger = logging.getLogger("qtohos-installer")
            for handler in logger.handlers[:]:
                try:
                    handler.close()
                    logger.removeHandler(handler)
                except Exception:
                    pass

            # Also close root logger handlers
            for handler in logging.root.handlers[:]:
                try:
                    handler.close()
                    logging.root.removeHandler(handler)
                except Exception:
                    pass

            shutil.rmtree(logs_dir)
            console.print("[green]✓ Logs directory removed[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to remove logs directory: {e}[/red]")
            console.print("[yellow]Try closing any programs using these files[/yellow]")

    console.print("\n[bold green]✓ Clean complete[/bold green]")
    console.print("[yellow]Note: Configuration preserved[/yellow]")