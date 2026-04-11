"""
Installation flow controller - Orchestrates the installation process
安装流程控制器 - 协调安装过程
"""

import sys
from pathlib import Path
from typing import Optional, List
import logging

from .steps import InstallStep, DEFAULT_STEPS
from .executor import StepExecutor
from ..config import ConfigManager, InstallConfig
from ..config.defaults import get_qt_version_config
from ..ui.display import Display
from ..ui.prompts import ConfigCollector
from ..tools.downloader import ToolDownloader
from ..builder.env_setup import EnvironmentManager
from ..builder.qt_builder import QtBuilder
from ..utils import setup_logging, check_python_version, is_windows


class QtHarmonyInstaller:
    """Main installation controller - Orchestrates the installation flow
    主安装控制器 - 协调安装流程"""

    def __init__(
        self,
        workspace: Path,
        auto_confirm: bool = False,
        steps: Optional[List[InstallStep]] = None
    ):
        self.workspace = workspace
        self.auto_confirm = auto_confirm
        self.steps = steps or DEFAULT_STEPS

        # UI components
        self.display = Display()
        self.collector = ConfigCollector()

        # Core components
        self.executor = StepExecutor(self.display)
        self.config_manager = ConfigManager(workspace / "config.yaml")

        # Build components (initialized during execution)
        self.logger: Optional[logging.Logger] = None
        self.downloader: Optional[ToolDownloader] = None
        self.env_manager: Optional[EnvironmentManager] = None
        self.builder: Optional[QtBuilder] = None

    def run(self) -> bool:
        """
        Run complete installation process.
        运行完整安装过程。

        Returns:
            True if installation successful, False otherwise
        """
        try:
            # Execute all steps
            success = self.executor.run_all(self.steps, self)

            if success:
                config = self.config_manager.install_config
                if config:
                    self.display.show_completion_message(config, self.workspace)

                if self.logger:
                    self.logger.info("Installation completed successfully / 安装成功完成")

            return success

        except KeyboardInterrupt:
            self.display.print("\n[yellow]用户取消安装 / Installation cancelled by user[/yellow]")
            if self.logger:
                self.logger.info("Installation cancelled by user / 用户取消安装")
            return False

        except Exception as e:
            self.display.show_error(f"安装错误 / Installation error: {e}")
            if self.logger:
                self.logger.error(f"Installation error: {e}")
            return False

    # Step handler methods (called by steps)

    def initialize(self) -> bool:
        """Initialize installer - Step 1 / 初始化安装器 - 步骤1"""
        # Setup logging
        log_dir = self.workspace / "logs"
        self.logger = setup_logging(log_dir)
        self.executor.set_logger(self.logger)
        self.logger.info("Qt for HarmonyOS Installer initialized / 安装器已初始化")

        # Check Python version
        is_valid, version = check_python_version()
        if not is_valid:
            self.display.show_error(version)
            self.display.print("[red]需要Python版本 >= 3.12 / Python version >= 3.12 is required[/red]")
            return False

        self.display.show_success(f"Python版本 / Python version: {version}")

        # Check platform
        if not is_windows():
            self.display.show_warning("此工具主要设计用于Windows / This tool is primarily designed for Windows")
            self.display.show_warning("某些功能在其他平台上可能无法正常工作 / Some features may not work correctly on other platforms")

        return True

    def check_prerequisites(self) -> bool:
        """Check prerequisites - Step 2 / 检查前置条件 - 步骤2"""
        import shutil

        all_ok = True

        # Check Git
        if shutil.which("git"):
            self.display.show_success("Git可用 / Git is available")
        else:
            self.display.show_error("Git未安装 / Git is not installed")
            self.display.print("  请从以下地址安装Git / Please install Git from: https://git-scm.com/downloads")
            all_ok = False

        return all_ok

    def load_or_prompt_config(self) -> Optional[InstallConfig]:
        """Load or prompt for configuration - Step 3 / 加载或提示配置 - 步骤3"""
        # Try to load existing config
        if self.config_manager.load_config():
            self.display.print("\n[yellow]发现现有配置 / Found existing configuration[/yellow]")

            config = self.config_manager.install_config
            if config:
                if self.auto_confirm:
                    self.display.show_success("使用现有配置(自动确认) / Using existing configuration (auto-confirm)")
                    return config
                elif self.collector.confirm_configuration(config):
                    return config

        # Prompt for new configuration
        try:
            config = self.collector.collect_all()
            self.config_manager.install_config = config

            # Initialize skip_modules if needed
            if not config.skip_modules:
                version_config = get_qt_version_config(config.qt_version)
                config.skip_modules = version_config.get("skip_modules", []).copy()

            self.config_manager.save_config()
            self.display.show_success("配置已保存 / Configuration saved")
            return config

        except KeyboardInterrupt:
            self.display.print("\n[yellow]用户取消安装 / Installation cancelled by user[/yellow]")
            return None

    def setup_tools(self) -> bool:
        """Setup required tools - Step 4 / 设置所需工具 - 步骤4"""
        tools_dir = self.workspace / "tools"
        config = self.config_manager.install_config

        self.downloader = ToolDownloader(
            tools_dir,
            self.config_manager.tool_config,
            make_path=config.make_path if config else None,
            perl_path=config.perl_path if config else None
        )

        tools_ok, mingw_ok = self.downloader.ensure_tools_available()

        if tools_ok:
            self.display.show_success("所有所需工具已就绪 / All required tools are ready")

            if not mingw_ok:
                self.display.show_warning(
                    "PATH中未检测到MinGW (gcc/g++) / MinGW (gcc/g++) not detected in PATH. "
                    "Host工具可能使用MSVC / Host tools may use MSVC instead."
                )
                self.display.print(
                    "[yellow]  建议配置make路径到包含gcc/g++的MinGW目录 "
                    "/ Consider configuring make path to MinGW directory "
                    "which contains gcc/g++.[/yellow]"
                )

            return True
        else:
            self.display.show_error("某些所需工具缺失 / Some required tools are missing")
            self.display.print("  [yellow]构建Qt需要Make和Perl / Make and Perl are required for building Qt[/yellow]")
            return False

    def setup_environment(self) -> bool:
        """Setup environment variables - Step 5 / 设置环境变量 - 步骤5"""
        config = self.config_manager.install_config
        if not config:
            self.display.show_error("配置未加载 / Configuration not loaded")
            return False

        self.env_manager = EnvironmentManager(config)
        self.env_manager.setup_environment()

        if self.env_manager.validate_environment():
            self.display.show_success("环境设置完成 / Environment setup complete")

            # Save environment script
            env_script = (
                self.workspace / "setup_env.bat"
                if is_windows()
                else self.workspace / "setup_env.sh"
            )
            self.env_manager.save_environment_script(env_script)

            return True
        else:
            self.display.show_error("环境验证失败 / Environment validation failed")
            return False

    def build_qt(self) -> bool:
        """Build and install Qt - Step 6 / 构建并安装Qt - 步骤6"""
        config = self.config_manager.install_config
        if not config or not self.env_manager:
            self.display.show_error("配置或环境未设置 / Configuration or environment not setup")
            return False

        self.builder = QtBuilder(config, self.env_manager, self.logger)

        return self.builder.build_all()