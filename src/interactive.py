"""
Interactive input module
"""

from pathlib import Path
from typing import Optional, Tuple, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text

from .config import InstallConfig
from .utils import validate_path, is_windows


class InteractivePrompt:
    """Interactive prompt for installation configuration"""
    
    def __init__(self):
        self.console = Console()
    
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
    
    def prompt_path(
        self,
        prompt_text: str,
        default: Optional[str] = None,
        must_exist: bool = True,
        create: bool = False,
        validate_func=None
    ) -> Path:
        """
        Prompt for a path input with clear input box
        
        Args:
            prompt_text: Prompt message
            default: Default value
            must_exist: Whether the path must exist
            create: Whether to create the path if it doesn't exist
            validate_func: Additional validation function
        
        Returns:
            Validated Path object
        """
        while True:
            # Show input box with Rich Prompt
            self.console.print()
            self.console.print(Panel(
                f"[bold cyan]{prompt_text}[/bold cyan]",
                border_style="cyan",
                expand=False
            ))
            
            # Get input with clear prompt
            if default:
                response = Prompt.ask(
                    "[bold green]Enter path[/bold green]",
                    default=default
                )
            else:
                response = Prompt.ask(
                    "[bold green]Enter path[/bold green]"
                )
            
            if not response or not response.strip():
                self.console.print("[red]✗ Path cannot be empty[/red]")
                continue
            
            # Validate the path
            path = Path(response.strip())
            is_valid, message = validate_path(path, must_exist, create)
            
            if is_valid:
                # Additional validation if provided
                if validate_func and not validate_func(path):
                    continue
                self.console.print(f"[green]✓[/green] {message}")
                return path
            else:
                self.console.print(f"[red]✗[/red] {message}")
                self.console.print("[yellow]Please try again or press Ctrl+C to cancel[/yellow]")
    
    def prompt_qt_source_path(self, default: Optional[str] = None) -> Path:
        """Prompt for Qt source path"""
        self.console.print("\n[bold cyan]Step 1: Qt Source Code Path[/bold cyan]")
        self.console.print(
            "Please specify the path to Qt source code (tqtc-qt5).\n"
            "This should contain the Qt source files for HarmonyOS."
        )
        
        return self.prompt_path(
            "Qt source code path:",
            default=default,
            must_exist=True,
            validate_func=self._validate_qt_source
        )
    
    def _validate_qt_source(self, path: Path) -> bool:
        """Validate Qt source directory"""
        # Check for key files/directories
        required_items = ["configure", "qtbase"]
        for item in required_items:
            if not (path / item).exists():
                self.console.print(
                    f"[yellow]Warning: '{item}' not found in Qt source directory[/yellow]"
                )
        return True
    
    def prompt_harmony_sdk_path(self, default: Optional[str] = None) -> Path:
        """Prompt for HarmonyOS SDK path"""
        self.console.print("\n[bold cyan]Step 2: HarmonyOS SDK Path[/bold cyan]")
        self.console.print(
            "Please specify the path to HarmonyOS SDK.\n"
            "This should contain the 'native' directory with LLVM toolchain.\n"
            "Example: C:\\Users\\<user>\\Library\\OpenHarmony\\Sdk\\12"
        )
        
        return self.prompt_path(
            "HarmonyOS SDK path:",
            default=default,
            must_exist=True,
            validate_func=self._validate_harmony_sdk
        )
    
    def _validate_harmony_sdk(self, path: Path) -> bool:
        """Validate HarmonyOS SDK directory"""
        # Check for native directory
        native_path = path / "native"
        if not native_path.exists():
            self.console.print(
                f"[red]Error: 'native' directory not found in SDK path[/red]"
            )
            return False
        
        # Check for LLVM
        llvm_path = native_path / "llvm"
        if not llvm_path.exists():
            self.console.print(
                f"[yellow]Warning: 'llvm' directory not found in native SDK[/yellow]"
            )
        
        return True
    
    def prompt_install_path(self, default: Optional[str] = None) -> Path:
        """Prompt for Qt installation path"""
        self.console.print("\n[bold cyan]Step 3: Qt Installation Path[/bold cyan]")
        self.console.print(
            "Please specify where to install Qt for HarmonyOS.\n"
            "This directory will contain the compiled Qt libraries and headers.\n"
            "Example: C:\\Qt\\Qt5.15.16-HarmonyOS"
        )
        
        return self.prompt_path(
            "Qt installation path:",
            default=default,
            must_exist=False,
            create=True
        )
    
    def prompt_architecture(self) -> str:
        """Prompt for target architecture"""
        self.console.print("\n[bold cyan]Step 4: Target Architecture[/bold cyan]")
        
        # Show options
        self.console.print("\n[bold]Available options:[/bold]")
        self.console.print("  [cyan]1[/cyan]. arm64-v8a (recommended for most HarmonyOS devices)")
        self.console.print("  [cyan]2[/cyan]. x86_64 (for emulator or x86 devices)")
        
        # Get user choice
        choice = Prompt.ask(
            "\n[bold green]Select architecture[/bold green]",
            choices=["1", "2"],
            default="1"
        )
        
        if choice == "1":
            self.console.print("[green]✓ Selected: arm64-v8a[/green]")
            return "arm64-v8a"
        else:
            self.console.print("[green]✓ Selected: x86_64[/green]")
            return "x86_64"
    
    def prompt_build_type(self) -> str:
        """Prompt for build type"""
        self.console.print("\n[bold cyan]Step 5: Build Type[/bold cyan]")
        
        # Show options
        self.console.print("\n[bold]Available options:[/bold]")
        self.console.print("  [cyan]1[/cyan]. release (optimized, recommended for production)")
        self.console.print("  [cyan]2[/cyan]. debug (with debug symbols, for development)")
        self.console.print("  [cyan]3[/cyan]. release-with-debug-info (optimized but with debug info)")
        
        # Get user choice
        choice = Prompt.ask(
            "\n[bold green]Select build type[/bold green]",
            choices=["1", "2", "3"],
            default="1"
        )
        
        if choice == "1":
            self.console.print("[green]✓ Selected: release[/green]")
            return "release"
        elif choice == "2":
            self.console.print("[green]✓ Selected: debug[/green]")
            return "debug"
        else:
            self.console.print("[green]✓ Selected: release-with-debug-info[/green]")
            return "release-with-debug-info"
    
    def prompt_parallel_jobs(self, default: int = 8) -> int:
        """Prompt for number of parallel jobs"""
        self.console.print("\n[bold cyan]Step 6: Parallel Build Jobs[/bold cyan]")
        self.console.print(
            "[yellow]Tip: Set to your CPU core count for optimal performance[/yellow]"
        )
        
        while True:
            response = Prompt.ask(
                "\n[bold green]Number of parallel jobs[/bold green]",
                default=str(default)
            )
            
            try:
                jobs = int(response)
                if jobs > 0:
                    self.console.print(f"[green]✓ Using {jobs} parallel jobs[/green]")
                    return jobs
                else:
                    self.console.print("[red]✗ Must be a positive number[/red]")
            except ValueError:
                self.console.print("[red]✗ Please enter a valid number[/red]")

    def prompt_tool_paths(self) -> Tuple[Optional[Path], Optional[Path]]:
        """Prompt for tool paths if already installed"""
        self.console.print("\n[bold cyan]Step 7: Build Tools Configuration[/bold cyan]")
        self.console.print(
            "[yellow]Note: make (MinGW) and perl are required for building Qt[/yellow]"
        )
        self.console.print(
            "[dim]提示: make路径应指向mingw32-make，它包含gcc/g++等编译工具[/dim]"
        )

        make_path = None
        perl_path = None

        # Ask about make (mingw32-make from MinGW toolchain)
        has_make = Confirm.ask(
            "\n[bold]Have you already installed MinGW (including mingw32-make)?[/bold]",
            default=False
        )

        if has_make:
            self.console.print("\n[bold]Please specify MinGW make path[/bold]")
            self.console.print("[yellow]You can provide mingw32-make executable or MinGW root directory[/yellow]")
            self.console.print("[yellow]Example 1: D:\\Tools\\llvm-mingw-xxxx\\bin\\mingw32-make.exe[/yellow]")
            self.console.print("[yellow]Example 2: D:\\Tools\\llvm-mingw-xxxx[/yellow]")

            while True:
                response = Prompt.ask(
                    "\n[bold green]mingw32-make path[/bold green] (or press Enter to skip)"
                )

                if not response.strip():
                    self.console.print("[yellow]Skipping make path configuration[/yellow]")
                    break

                path = Path(response.strip())
                if path.exists():
                    make_path = path
                    self.console.print(f"[green]✓ Make path set: {make_path}[/green]")
                    break
                else:
                    self.console.print(f"[red]✗ Path not found: {path}[/red]")
                    retry = Confirm.ask("[bold]Try again?[/bold]", default=True)
                    if not retry:
                        break

        # Ask about perl
        has_perl = Confirm.ask(
            "\n[bold]Have you already installed perl?[/bold]",
            default=False
        )

        if has_perl:
            self.console.print("\n[bold]Please specify perl path[/bold]")
            self.console.print("[yellow]You can provide either perl executable path or perl bin directory[/yellow]")
            self.console.print("[yellow]Example 1: C:\\Strawberry\\perl\\bin\\perl.exe[/yellow]")
            self.console.print("[yellow]Example 2: C:\\Strawberry\\perl\\bin[/yellow]")

            while True:
                response = Prompt.ask(
                    "\n[bold green]Perl executable path[/bold green] (or press Enter to skip)"
                )

                if not response.strip():
                    self.console.print("[yellow]Skipping perl path configuration[/yellow]")
                    break

                path = Path(response.strip())
                if path.exists():
                    perl_path = path
                    self.console.print(f"[green]✓ Perl path set: {perl_path}[/green]")
                    break
                else:
                    self.console.print(f"[red]✗ Path not found: {path}[/red]")
                    retry = Confirm.ask("[bold]Try again?[/bold]", default=True)
                    if not retry:
                        break

        return make_path, perl_path
    
    def confirm_configuration(self, config: InstallConfig) -> bool:
        """Display configuration and ask for confirmation"""
        self.console.print("\n" + "=" * 60)
        self.console.print("[bold cyan]Configuration Summary[/bold cyan]\n")
        
        table = Table(show_header=False, box=None)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Qt Source Path", str(config.qt_source_path))
        table.add_row("HarmonyOS SDK Path", str(config.harmony_sdk_path))
        table.add_row("Install Path", str(config.install_path))
        table.add_row("Architecture", config.architecture)
        table.add_row("Qt Version", config.qt_version)
        table.add_row("Build Type", config.build_type)
        table.add_row("Parallel Jobs", str(config.parallel_jobs))

        # Show tool paths if configured
        if config.make_path:
            table.add_row("Make Path", str(config.make_path))
        if config.perl_path:
            table.add_row("Perl Path", str(config.perl_path))

        self.console.print(table)
        
        # Use Rich Confirm
        confirm = Confirm.ask(
            "\n[bold]Proceed with installation?[/bold]",
            default=True
        )
        
        return confirm
    
    def collect_configuration(self) -> InstallConfig:
        """Collect all configuration from user"""
        self.show_welcome()
        
        # Prompt for paths
        qt_source_path = self.prompt_qt_source_path()
        harmony_sdk_path = self.prompt_harmony_sdk_path()
        install_path = self.prompt_install_path()
        
        # Prompt for build options
        architecture = self.prompt_architecture()
        build_type = self.prompt_build_type()
        parallel_jobs = self.prompt_parallel_jobs()
        
        # Prompt for tool paths
        make_path, perl_path = self.prompt_tool_paths()

        # Create configuration
        config = InstallConfig(
            qt_source_path=qt_source_path,
            harmony_sdk_path=harmony_sdk_path,
            install_path=install_path,
            architecture=architecture,
            build_type=build_type,
            parallel_jobs=parallel_jobs,
            make_path=make_path,
            perl_path=perl_path
        )

        # Confirm configuration
        if self.confirm_configuration(config):
            return config
        else:
            raise KeyboardInterrupt("Installation cancelled by user")
