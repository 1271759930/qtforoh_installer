"""
Interactive menu module - Main menu for Qt for HarmonyOS Installer
"""

import sys
from pathlib import Path
import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .display import Display


console = Console(force_terminal=True)
display = Display()


def show_menu() -> str:
    """
    Display the main menu and return the selected action.

    Returns:
        str: Selected action key ('install', 'check', 'config', 'guide', 'clean', 'exit')
    """
    console.clear()

    # Display header
    console.print("=" * 50, style="cyan")
    console.print("Qt for HarmonyOS 交叉编译工具", style="bold cyan")
    console.print("=" * 50, style="cyan")
    console.print()

    choices = [
        questionary.Choice("安装 Qt          - 交互式安装 Qt for HarmonyOS", value="install"),
        questionary.Choice("检查环境         - 检查前置条件和依赖", value="check"),
        questionary.Choice("查看配置         - 显示当前配置信息", value="config"),
        questionary.Choice("安装指南         - 显示安装步骤说明", value="guide"),
        questionary.Choice("清理构建产物     - 删除构建目录和日志", value="clean"),
        questionary.Choice("退出", value="exit"),
    ]

    action = questionary.select(
        "请选择要执行的功能:",
        choices=choices,
        style=questionary.Style([
            ('qmark', 'fg:cyan bold'),
            ('question', 'fg:white bold'),
            ('answer', 'fg:green bold'),
            ('pointer', 'fg:cyan bold'),
            ('highlighted', 'fg:cyan bold'),
            ('selected', 'fg:green'),
        ])
    ).ask()

    if action is None:
        # User cancelled (Ctrl+C)
        return "exit"

    return action


def do_install():
    """执行安装流程"""
    from ..core import QtHarmonyInstaller

    workspace_path = Path(".").resolve()
    console.print("\n[bold cyan]Qt for HarmonyOS Installation Tool[/bold cyan]")
    console.print(f"Workspace: {workspace_path}\n")

    installer = QtHarmonyInstaller(workspace_path)

    if installer.run():
        console.print("\n[bold green]✓ Installation successful![/bold green]")
    else:
        console.print("\n[bold red]✗ Installation failed[/bold red]")


def do_check():
    """执行环境检查"""
    from ..config import ConfigManager
    from ..utils import check_python_version, check_llvm_mingw, check_perl
    import shutil

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


def do_config():
    """显示当前配置"""
    from ..config import ConfigManager

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
            table.add_row("Install Path", str(cfg.install_path))
            table.add_row("Architecture", cfg.architecture)
            table.add_row("Qt Version", cfg.qt_version)
            table.add_row("Build Type", cfg.build_type)
            table.add_row("Parallel Jobs", str(cfg.parallel_jobs))

            console.print(table)
    else:
        console.print("\n[yellow]No configuration found[/yellow]")
        console.print("Run '安装 Qt' to create configuration")


def do_guide():
    """显示安装指南"""
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
  • Run '检查环境' to verify prerequisites
    """

    console.print(Panel(guide_text, border_style="cyan"))


def do_clean():
    """清理构建产物"""
    from ..config import ConfigManager
    import shutil

    workspace_path = Path(".").resolve()
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


def run_menu_loop():
    """
    Run the menu in a loop. Execute selected action and return to menu
    until user chooses to exit.
    """
    while True:
        action = show_menu()

        if action == "exit":
            console.print("\n[yellow]再见！[/yellow]")
            sys.exit(0)

        # Execute the selected action
        try:
            if action == "install":
                do_install()
            elif action == "check":
                do_check()
            elif action == "config":
                do_config()
            elif action == "guide":
                do_guide()
            elif action == "clean":
                do_clean()

            console.print()
            console.print("[cyan]按 Enter 返回菜单...[/cyan]")
            input()

        except KeyboardInterrupt:
            console.print("\n[yellow]操作已取消[/yellow]")
            continue
        except Exception as e:
            console.print(f"\n[red]执行出错: {e}[/red]")
            console.print("[cyan]按 Enter 返回菜单...[/cyan]")
            input()