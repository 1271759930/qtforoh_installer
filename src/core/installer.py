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
                    self.config_manager.save_config()
                    self.display.show_success("配置已保存 / Configuration saved")
                    return config
                else:
                    return None

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
        archives_dir = tools_dir / "archives"

        self.downloader = ToolDownloader(
            tools_dir,
            self.config_manager.tool_config
        )

        # Check if tools exist, if not, try to extract from archives
        make_ok, perl_ok, mingw_ok = self.downloader.check_existing_tools()

        if not (make_ok and perl_ok):
            self.display.print("\n[cyan]检查本地工具压缩包... / Checking local archives...[/cyan]")

            if archives_dir.exists():
                self.display.print(f"  压缩包目录 / Archives directory: {archives_dir}")

                llvm_archive = archives_dir / "llvm-mingw-20240917-ucrt-x86_64.zip"
                perl_archive = archives_dir / "strawberry-perl-5.42.2.1-64bit-portable.zip"

                if llvm_archive.exists() or perl_archive.exists():
                    self.display.print("[cyan]从本地压缩包解压工具... / Extracting from local archives...[/cyan]")

                    import zipfile

                    llvm_mingw_dir = tools_dir / "llvm-mingw"
                    perl_dir = tools_dir / "perl"

                    # Extract llvm-mingw
                    if llvm_archive.exists() and not llvm_mingw_dir.exists():
                        self._extract_archive(llvm_archive, llvm_mingw_dir, "llvm-mingw")

                    # Extract Perl
                    if perl_archive.exists() and not perl_dir.exists():
                        self._extract_archive(perl_archive, perl_dir, "Perl")

                    # Re-check after extraction
                    make_ok, perl_ok, mingw_ok = self.downloader.check_existing_tools()

        if make_ok and perl_ok:
            self.display.show_success("所有所需工具已就绪 / All required tools are ready")

            if not mingw_ok:
                self.display.show_warning(
                    "PATH中未检测到MinGW (gcc/g++) / MinGW (gcc/g++) not detected in PATH."
                )
                self.display.print(
                    "[yellow]  请确保 tools/archives/ 目录包含压缩包 "
                    "/ Ensure tools/archives/ contains the archives.[/yellow]"
                )

            return True
        else:
            self.display.show_error("某些所需工具缺失 / Some required tools are missing")
            self.display.print("  [yellow]请运行 python scripts/download_tools.py 准备工具[/yellow]")
            self.display.print("  [yellow]Run 'python scripts/download_tools.py' to setup tools[/yellow]")
            return False

    def _extract_archive(self, archive_path: Path, target_dir: Path, tool_name: str) -> bool:
        """Extract a zip archive"""
        import zipfile

        self.display.print(f"\n[cyan]解压 {tool_name} / Extracting {tool_name}[/cyan]")
        self.display.print(f"  源文件 / Source: {archive_path}")

        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                members = zf.namelist()

                root_folder = None
                for name in members[:10]:
                    if '/' in name:
                        potential_root = name.split('/')[0]
                        break

                target_dir.mkdir(parents=True, exist_ok=True)

                for member in members:
                    if root_folder:
                        if member == root_folder:
                            continue
                        if member.startswith(root_folder + '/'):
                            member = member[len(root_folder) + 1:]

                    if not member:
                        continue

                    target_path = target_dir / member

                    if member.endswith('/'):
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        actual_member = root_folder + '/' + member if root_folder else member
                        try:
                            with zf.open(actual_member) as src:
                                with open(target_path, 'wb') as dst:
                                    dst.write(src.read())
                        except KeyError:
                            with zf.open(member) as src:
                                with open(target_path, 'wb') as dst:
                                    dst.write(src.read())

            self.display.print(f"  [green]✓ {tool_name} 解压完成 / Extraction completed[/green]")
            return True

        except Exception as e:
            self.display.print(f"  [red]✗ 解压失败 / Extraction failed: {e}[/red]")
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