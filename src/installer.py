"""
Installation flow controller
"""

import sys
from pathlib import Path
from typing import Optional
import logging
from rich.console import Console
from rich.panel import Panel

from .config import ConfigManager, InstallConfig
from .interactive import InteractivePrompt
from .downloader import ToolDownloader
from .environment import EnvironmentManager
from .builder import QtBuilder
from .utils import setup_logging, check_python_version, is_windows


class QtHarmonyInstaller:
    """Main installation controller"""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.console = Console()
        self.logger: Optional[logging.Logger] = None
        
        # Components
        self.config_manager = ConfigManager(workspace / "config.yaml")
        self.interactive = InteractivePrompt()
        self.downloader: Optional[ToolDownloader] = None
        self.env_manager: Optional[EnvironmentManager] = None
        self.builder: Optional[QtBuilder] = None
    
    def initialize(self) -> bool:
        """
        Initialize installer
        
        Returns:
            True if initialization successful, False otherwise
        """
        # Setup logging
        log_dir = self.workspace / "logs"
        self.logger = setup_logging(log_dir)
        self.logger.info("Qt for HarmonyOS Installer initialized")
        
        # Check Python version
        is_valid, version = check_python_version()
        if not is_valid:
            self.console.print(f"[red]Error: {version}[/red]")
            self.console.print("[red]Python version >= 3.12 is required[/red]")
            return False
        
        self.console.print(f"[green]✓ Python version: {version}[/green]")
        
        # Check platform
        if not is_windows():
            self.console.print(
                "[yellow]Warning: This tool is primarily designed for Windows[/yellow]"
            )
            self.console.print(
                "[yellow]Some features may not work correctly on other platforms[/yellow]"
            )
        
        return True
    
    def check_prerequisites(self) -> bool:
        """
        Check all prerequisites before installation
        
        Returns:
            True if all prerequisites met, False otherwise
        """
        self.console.print("\n[bold cyan]Checking prerequisites...[/bold cyan]")
        
        all_ok = True
        
        # Check Git
        import shutil
        if shutil.which("git"):
            self.console.print("[green]✓ Git is available[/green]")
        else:
            self.console.print("[red]✗ Git is not installed[/red]")
            self.console.print("  Please install Git from: https://git-scm.com/downloads")
            all_ok = False
        
        # Check Python (already checked in initialize)
        
        # Check if Qt source exists (will be prompted later)
        # Check if HarmonyOS SDK exists (will be prompted later)
        
        return all_ok
    
    def load_or_prompt_config(self) -> Optional[InstallConfig]:
        """
        Load existing config or prompt user for new config
        
        Returns:
            InstallConfig if successful, None otherwise
        """
        # Try to load existing config
        if self.config_manager.load_config():
            self.console.print("\n[yellow]Found existing configuration[/yellow]")
            
            # Display existing config
            config = self.config_manager.install_config
            if config and self.interactive.confirm_configuration(config):
                return config
        
        # Prompt for new configuration
        try:
            config = self.interactive.collect_configuration()
            self.config_manager.install_config = config
            self.config_manager.save_config()
            
            self.console.print("\n[green]✓ Configuration saved[/green]")
            return config
        
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Installation cancelled by user[/yellow]")
            return None
    
    def setup_tools(self) -> bool:
        """
        Setup required tools (make, perl, mingw)

        Returns:
            True if tools setup successful, False otherwise
        """
        self.console.print("\n[bold cyan]Setting up build tools...[/bold cyan]")

        tools_dir = self.workspace / "tools"
        config = self.config_manager.install_config

        # Pass configured tool paths to downloader
        self.downloader = ToolDownloader(
            tools_dir,
            self.config_manager.tool_config,
            make_path=config.make_path if config else None,
            perl_path=config.perl_path if config else None,
            mingw_path=config.mingw_path if config else None
        )

        tools_ok, mingw_ok = self.downloader.ensure_tools_available()

        if tools_ok:
            self.console.print("[green]✓ All required tools are ready[/green]")

            if not mingw_ok:
                self.console.print(
                    "[yellow]⚠ Warning: MinGW is not available. "
                    "Some build configurations may not work.[/yellow]"
                )
                self.console.print(
                    "[yellow]  You can configure MinGW path in config.yaml or let the "
                    "installer download it.[/yellow]"
                )

            return True
        else:
            self.console.print("[red]✗ Some required tools are missing[/red]")
            self.console.print("  [yellow]Make and Perl are required for building Qt[/yellow]")

            return False
    
    def setup_environment(self) -> bool:
        """
        Setup environment variables
        
        Returns:
            True if environment setup successful, False otherwise
        """
        self.console.print("\n[bold cyan]Setting up environment...[/bold cyan]")
        
        config = self.config_manager.install_config
        if not config:
            self.console.print("[red]Error: Configuration not loaded[/red]")
            return False
        
        self.env_manager = EnvironmentManager(config)
        self.env_manager.setup_environment()
        
        if self.env_manager.validate_environment():
            self.console.print("[green]✓ Environment setup complete[/green]")
            
            # Save environment script
            env_script = self.workspace / "setup_env.bat" if is_windows() else self.workspace / "setup_env.sh"
            self.env_manager.save_environment_script(env_script)
            
            return True
        else:
            self.console.print("[red]✗ Environment validation failed[/red]")
            return False
    
    def build_qt(self) -> bool:
        """
        Build and install Qt
        
        Returns:
            True if build successful, False otherwise
        """
        config = self.config_manager.install_config
        if not config or not self.env_manager:
            self.console.print("[red]Error: Configuration or environment not setup[/red]")
            return False
        
        self.builder = QtBuilder(config, self.env_manager, self.logger)
        
        return self.builder.build_all()
    
    def show_completion_message(self) -> None:
        """Show completion message with next steps"""
        config = self.config_manager.install_config
        
        completion_text = """
[bold green]✓ Installation Completed Successfully![/bold green]

[bold cyan]Next Steps:[/bold cyan]

1. [yellow]Configure Qt Creator:[/yellow]
   • Add Qt version: {install_path}/bin/qmake
   • Add compiler: {sdk_path}/native/llvm/bin/clang
   • Create kit with ohos-clang mkspec

2. [yellow]Test your installation:[/yellow]
   • Create a simple Qt project
   • Build for HarmonyOS target
   • Deploy to device via DevEco Studio

3. [yellow]Environment setup for future builds:[/yellow]
   • Run: {env_script}
   • Or source the script in your shell

[bold cyan]Useful Resources:[/bold cyan]
  • Official Guide: https://wiki.qt.io/Building_Qt_for_HarmonyOS
  • Qt Documentation: https://doc.qt.io/
  • HarmonyOS Dev: https://developer.huawei.com/consumer/cn/

[bold cyan]Installed Qt Location:[/bold cyan]
  {install_path}
        """.format(
            install_path=config.install_path if config else "N/A",
            sdk_path=config.harmony_sdk_path if config else "N/A",
            env_script=self.workspace / "setup_env.bat" if is_windows() else self.workspace / "setup_env.sh"
        )
        
        self.console.print(Panel(completion_text, border_style="green"))
    
    def run(self) -> bool:
        """
        Run complete installation process
        
        Returns:
            True if installation successful, False otherwise
        """
        try:
            # Step 1: Initialize
            self.console.print("\n[bold cyan]Step 1: Initializing...[/bold cyan]")
            if not self.initialize():
                return False
            
            # Step 2: Check prerequisites
            self.console.print("\n[bold cyan]Step 2: Checking prerequisites...[/bold cyan]")
            if not self.check_prerequisites():
                self.console.print(
                    "\n[yellow]Please install missing prerequisites and try again[/yellow]"
                )
                return False
            
            # Step 3: Get configuration
            self.console.print("\n[bold cyan]Step 3: Collecting configuration...[/bold cyan]")
            config = self.load_or_prompt_config()
            if not config:
                return False
            
            # Step 4: Setup tools
            self.console.print("\n[bold cyan]Step 4: Setting up tools...[/bold cyan]")
            if not self.setup_tools():
                return False
            
            # Step 5: Setup environment
            self.console.print("\n[bold cyan]Step 5: Setting up environment...[/bold cyan]")
            if not self.setup_environment():
                return False
            
            # Step 6: Build Qt
            self.console.print("\n[bold cyan]Step 6: Building Qt...[/bold cyan]")
            if not self.build_qt():
                return False
            
            # Show completion message
            self.show_completion_message()
            
            self.logger.info("Installation completed successfully")
            return True
        
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Installation cancelled by user[/yellow]")
            self.logger.info("Installation cancelled by user")
            return False
        
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")
            self.logger.error(f"Installation error: {e}")
            return False