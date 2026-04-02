"""
Qt builder module
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
import logging
from rich.console import Console
from rich.panel import Panel

from .config import InstallConfig
from .environment import EnvironmentManager
from .utils import run_command, ensure_directory, is_windows


class QtBuilder:
    """Build Qt for HarmonyOS"""
    
    def __init__(
        self,
        config: InstallConfig,
        env_manager: EnvironmentManager,
        logger: Optional[logging.Logger] = None
    ):
        self.config = config
        self.env_manager = env_manager
        self.logger = logger or logging.getLogger("qtohos-installer")
        self.console = Console()
        
        # Build directory (parallel to source dir, per Qt HarmonyOS wiki)
        self.build_dir = config.qt_source_path.parent / f"build_{config.architecture}"
        
        # Make command
        self.make_cmd = "mingw32-make" if is_windows() else "make"
    
    def prepare_build_directory(self) -> bool:
        """
        Prepare build directory
        
        Returns:
            True if successful, False otherwise
        """
        self.console.print("\n[bold cyan]Preparing build directory...[/bold cyan]")
        
        try:
            # Create build directory
            ensure_directory(self.build_dir)
            
            self.console.print(f"[green]✓ Build directory created: {self.build_dir}[/green]")
            return True
        
        except Exception as e:
            self.console.print(f"[red]✗ Failed to create build directory: {e}[/red]")
            self.logger.error(f"Failed to create build directory: {e}")
            return False
    
    def generate_configure_command(self) -> List[str]:
        """
        Generate configure command for Qt
        
        Returns:
            Configure command as list of strings
        """
        self.console.print("\n[bold cyan]Generating configure command...[/bold cyan]")
        
        # Base configure command
        # Prefer qtbase/configure.bat -top-level (same as Qt HarmonyOS wiki and
        # common manual workflows). Fallback to top-level configure script.
        if is_windows():
            qtbase_configure = self.config.qt_source_path / "qtbase" / "configure.bat"
            root_configure = self.config.qt_source_path / "configure.bat"
            if qtbase_configure.exists():
                configure_script = qtbase_configure
                cmd = [str(configure_script), "-top-level"]
            else:
                configure_script = root_configure
                cmd = [str(configure_script)]
        else:
            configure_script = self.config.qt_source_path / "configure"
            cmd = [str(configure_script)]
        
        # Add common options
        cmd.extend([
            "-v",  # Verbose output
            "-xplatform", "ohos-clang",  # Target platform
            "-opensource",
            "-confirm-license",
            "-no-use-gold-linker",
            "-no-gcc-sysroot",
            "-ohos-arch", self.config.architecture,
            "-c++std", "c++14",
            "-nomake", "examples",
            "-nomake", "tests",
        ])
        
        # Build type
        if self.config.build_type == "debug":
            cmd.append("-debug")
        elif self.config.build_type == "release":
            cmd.append("-release")
        else:  # release-with-debug-info
            cmd.extend(["-release", "-force-debug-info"])
        
        # Installation prefix
        # For HarmonyOS, we use two prefixes:
        # -prefix: location on device (e.g., /data/storage/el1/bundle/libs/arm64)
        # -extprefix: external prefix (actual installation location)
        
        device_prefix = f"/data/storage/el1/bundle/libs/{self.config.architecture.split('-')[0]}"
        cmd.extend([
            "-prefix", device_prefix,
            "-extprefix", str(self.config.install_path),
        ])
        
        # Windows-specific options
        if is_windows():
            llvm_dir = self.env_manager.env_vars.get("LLVM_INSTALL_DIR", "")
            if llvm_dir:
                cmd.extend(["-device-option", f"CROSS_COMPILE={llvm_dir}/bin"])
        
        # Skip modules
        for module in self.config.skip_modules:
            cmd.extend(["-skip", module])
        
        # No DBus (not available on HarmonyOS)
        cmd.append("-no-dbus")
        
        # Display command
        self.console.print("\n[bold]Configure command:[/bold]")
        cmd_str = " ".join(cmd)
        self.console.print(Panel(cmd_str, border_style="cyan"))
        
        return cmd
    
    def configure_qt(self) -> Tuple[int, str, str]:
        """
        Run Qt configure
        
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        self.console.print("\n[bold cyan]Configuring Qt...[/bold cyan]")
        self.logger.info("Starting Qt configuration")
        
        cmd = self.generate_configure_command()
        env = self.env_manager.get_build_environment()
        
        # Run configure
        exit_code, stdout, stderr = run_command(
            cmd,
            cwd=self.build_dir,
            env=env,
            capture_output=False,
            logger=self.logger
        )
        
        if exit_code == 0:
            self.console.print("\n[green]✓ Qt configuration completed successfully[/green]")
            self.logger.info("Qt configuration completed successfully")
        else:
            self.console.print(f"\n[red]✗ Qt configuration failed with code: {exit_code}[/red]")
            self.logger.error(f"Qt configuration failed with code: {exit_code}")
        
        return exit_code, stdout, stderr
    
    def build_qt(self) -> Tuple[int, str, str]:
        """
        Build Qt (make)
        
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        self.console.print("\n[bold cyan]Building Qt...[/bold cyan]")
        self.console.print(
            f"[yellow]This may take a long time (parallel jobs: {self.config.parallel_jobs})[/yellow]"
        )
        self.logger.info(f"Starting Qt build with {self.config.parallel_jobs} parallel jobs")
        
        env = self.env_manager.get_build_environment()
        
        # Make command
        cmd = [self.make_cmd, f"-j{self.config.parallel_jobs}"]
        
        # Run make
        exit_code, stdout, stderr = run_command(
            cmd,
            cwd=self.build_dir,
            env=env,
            capture_output=False,
            logger=self.logger
        )
        
        if exit_code == 0:
            self.console.print("\n[green]✓ Qt build completed successfully[/green]")
            self.logger.info("Qt build completed successfully")
        else:
            self.console.print(f"\n[red]✗ Qt build failed with code: {exit_code}[/red]")
            self.logger.error(f"Qt build failed with code: {exit_code}")
        
        return exit_code, stdout, stderr
    
    def install_qt(self) -> Tuple[int, str, str]:
        """
        Install Qt (make install)
        
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        self.console.print("\n[bold cyan]Installing Qt...[/bold cyan]")
        self.logger.info("Starting Qt installation")
        
        env = self.env_manager.get_build_environment()
        
        # Make install command
        cmd = [self.make_cmd, "install"]
        
        # Run make install
        exit_code, stdout, stderr = run_command(
            cmd,
            cwd=self.build_dir,
            env=env,
            capture_output=False,
            logger=self.logger
        )
        
        if exit_code == 0:
            self.console.print("\n[green]✓ Qt installation completed successfully[/green]")
            self.logger.info("Qt installation completed successfully")
            
            # Verify installation
            self._verify_installation()
        else:
            self.console.print(f"\n[red]✗ Qt installation failed with code: {exit_code}[/red]")
            self.logger.error(f"Qt installation failed with code: {exit_code}")
        
        return exit_code, stdout, stderr
    
    def _verify_installation(self) -> None:
        """Verify Qt installation"""
        self.console.print("\n[bold cyan]Verifying installation...[/bold cyan]")
        
        # Check for qmake
        qmake_path = self.config.install_path / "bin" / "qmake"
        if is_windows():
            qmake_path = qmake_path.with_suffix(".exe")
        
        if qmake_path.exists():
            self.console.print(f"[green]✓ qmake found: {qmake_path}[/green]")
            
            # Get Qt version
            try:
                result = run_command(
                    [str(qmake_path), "-query", "QT_VERSION"],
                    capture_output=True,
                    logger=self.logger
                )
                if result[0] == 0:
                    qt_version = result[1].strip()
                    self.console.print(f"[green]  Qt version: {qt_version}[/green]")
            except Exception:
                pass
        else:
            self.console.print(f"[yellow]⚠ qmake not found at expected location[/yellow]")
        
        # Check for libraries
        lib_dir = self.config.install_path / "lib"
        if lib_dir.exists():
            libs = list(lib_dir.glob("*.so")) if not is_windows() else list(lib_dir.glob("*.dll"))
            self.console.print(f"[green]✓ Found {len(libs)} libraries[/green]")
        else:
            self.console.print(f"[yellow]⚠ Library directory not found[/yellow]")
    
    def build_all(self) -> bool:
        """
        Run complete build process
        
        Returns:
            True if all steps successful, False otherwise
        """
        self.console.print("\n" + "=" * 60)
        self.console.print("[bold cyan]Starting Qt Build Process[/bold cyan]")
        self.console.print("=" * 60)
        
        # Step 1: Prepare build directory
        if not self.prepare_build_directory():
            return False
        
        # Step 2: Configure
        exit_code, _, _ = self.configure_qt()
        if exit_code != 0:
            return False
        
        # Step 3: Build
        exit_code, _, _ = self.build_qt()
        if exit_code != 0:
            return False
        
        # Step 4: Install
        exit_code, _, _ = self.install_qt()
        if exit_code != 0:
            return False
        
        self.console.print("\n" + "=" * 60)
        self.console.print("[bold green]✓ Qt Build Process Completed Successfully[/bold]")
        self.console.print("=" * 60)
        
        return True
