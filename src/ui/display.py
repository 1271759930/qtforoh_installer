"""
Display module - Console output and formatting
显示模块 - 控制台输出和格式化
"""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..config.schema import InstallConfig


class Display:
    """Console display handler - Only responsible for output
    控制台显示处理器 - 仅负责输出"""

    def __init__(self):
        self.console = Console(force_terminal=True)

    def show_welcome(self) -> None:
        """Show welcome message / 显示欢迎信息"""
        welcome_text = """
[bold cyan]Qt for HarmonyOS 安装工具 / Installation Tool[/bold cyan]

本工具将帮助您安装鸿蒙版Qt:
This tool will help you install Qt for HarmonyOS by:
  1. 收集必要的路径和配置 / Collecting necessary paths and configurations
  2. 下载所需工具 (make, perl) / Downloading required tools (make, perl)
  3. 配置构建环境 / Configuring build environment
  4. 编译并安装Qt / Compiling and installing Qt

[yellow]前置条件 / Prerequisites:[/yellow]
  • Python >= 3.12
  • Git >= 2.39.3
  • HarmonyOS SDK (API >= 15, 推荐API 17 / recommended API 17)
  • Qt源代码 / Qt source code (tqtc-qt5)

[green]官方指南 / Official Guide:[/green] https://wiki.qt.io/Building_Qt_for_HarmonyOS
        """
        self.console.print(Panel(welcome_text, border_style="cyan"))

    def show_step_title(self, step_number: int, title: str) -> None:
        """Show step title / 显示步骤标题"""
        self.console.print(f"\n[bold cyan]步骤 {step_number} / Step {step_number}: {title}...[/bold cyan]")

    def show_success(self, message: str) -> None:
        """Show success message / 显示成功消息"""
        self.console.print(f"[green]✓[/green] {message}")

    def show_error(self, message: str) -> None:
        """Show error message / 显示错误消息"""
        self.console.print(f"[red]✗[/red] {message}")

    def show_warning(self, message: str) -> None:
        """Show warning message / 显示警告消息"""
        self.console.print(f"[yellow]⚠[/yellow] {message}")

    def show_info(self, message: str) -> None:
        """Show info message / 显示信息消息"""
        self.console.print(f"[cyan]{message}[/cyan]")

    def show_config_summary(self, config: InstallConfig) -> None:
        """Display configuration summary / 显示配置摘要"""
        self.console.print("\n" + "=" * 60)
        self.console.print("[bold cyan]配置摘要 / Configuration Summary[/bold cyan]\n")

        table = Table(show_header=False, box=None)
        table.add_column("属性 / Property", style="cyan")
        table.add_column("值 / Value", style="green")

        table.add_row("Qt源码路径 / Qt Source Path", str(config.qt_source_path))
        table.add_row("HarmonyOS SDK路径 / SDK Path", str(config.harmony_sdk_path))
        table.add_row("安装路径 / Install Path", str(config.install_path))
        table.add_row("架构 / Architecture", config.architecture)
        table.add_row("Qt版本 / Qt Version", f"{config.qt_version} ({config.version_source})")
        table.add_row("构建类型 / Build Type", config.build_type)
        table.add_row("并行任务 / Parallel Jobs", str(config.parallel_jobs))

        # Show tool paths if configured
        if config.make_path:
            table.add_row("Make路径 / Make Path", str(config.make_path))
        if config.perl_path:
            table.add_row("Perl路径 / Perl Path", str(config.perl_path))
        if config.python_path:
            table.add_row("Python路径 / Python Path", str(config.python_path))

        self.console.print(table)

    def show_completion_message(self, config: InstallConfig, workspace: Path) -> None:
        """Show completion message with next steps / 显示完成消息和后续步骤"""
        from ..utils import is_windows

        completion_text = f"""
[bold green]✓ 安装成功完成! / Installation Completed Successfully![/bold green]

[bold cyan]后续步骤 / Next Steps:[/bold cyan]

1. [yellow]配置Qt Creator / Configure Qt Creator:[/yellow]
   • 添加Qt版本 / Add Qt version: {config.install_path}/bin/qmake
   • 添加编译器 / Add compiler: {config.harmony_sdk_path}/native/llvm/bin/clang
   • 创建使用ohos-clang mkspec的构建套件 / Create kit with ohos-clang mkspec

2. [yellow]测试安装 / Test your installation:[/yellow]
   • 创建简单的Qt项目 / Create a simple Qt project
   • 为HarmonyOS目标构建 / Build for HarmonyOS target
   • 通过DevEco Studio部署到设备 / Deploy to device via DevEco Studio

3. [yellow]未来构建的环境设置 / Environment setup for future builds:[/yellow]
   • 运行 / Run: {workspace / ('setup_env.bat' if is_windows() else 'setup_env.sh')}

[bold cyan]有用资源 / Useful Resources:[/bold cyan]
  • 官方指南 / Official Guide: https://wiki.qt.io/Building_Qt_for_HarmonyOS
  • Qt文档 / Qt Documentation: https://doc.qt.io/
  • HarmonyOS开发者 / HarmonyOS Dev: https://developer.huawei.com/consumer/cn/

[bold cyan]Qt安装位置 / Installed Qt Location:[/bold cyan]
  {config.install_path}
        """

        self.console.print(Panel(completion_text, border_style="green"))

    def print(self, message: str = "") -> None:
        """Print a message / 打印消息"""
        self.console.print(message)