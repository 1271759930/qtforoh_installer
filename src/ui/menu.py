"""
Interactive menu module - Main menu for Qt for HarmonyOS Installer
"""

import sys
from pathlib import Path
import questionary
from rich.console import Console

from .display import Display
from .commands import do_check, do_config, do_guide, do_clean


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