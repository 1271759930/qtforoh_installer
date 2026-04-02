"""
Environment configuration module
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional
from rich.console import Console

from .config import InstallConfig
from .utils import is_windows


class EnvironmentManager:
    """Manage environment variables for Qt HarmonyOS build"""
    
    def __init__(self, config: InstallConfig):
        self.config = config
        self.console = Console()
        self.env_vars: Dict[str, str] = {}

    def reset_path_to_minimum(self) -> None:
        """
        Reset PATH to minimum required paths.
        This prevents system compilers (MSVC) from polluting the build environment.
        """
        if is_windows():
            minimum_paths = [
                "C:\\Windows\\System32",
                "C:\\Windows",
                os.path.dirname(sys.executable)  # Python directory
            ]
            self.env_vars["PATH"] = os.pathsep.join(minimum_paths)
            self.console.print("[cyan]PATH reset to minimum to avoid MSVC pollution[/cyan]")

    def setup_environment(self) -> Dict[str, str]:
        """
        Setup all required environment variables
        
        Returns:
            Dictionary of environment variables
        """
        self.console.print("\n[bold cyan]Setting up environment variables...[/bold cyan]")
        
        # Get HarmonyOS SDK paths
        sdk_native_path = self.config.harmony_sdk_path / "native"
        sdk_sysroot_path = sdk_native_path / "sysroot"
        llvm_path = sdk_native_path / "llvm"
        
        # Validate paths
        if not sdk_native_path.exists():
            self.console.print(
                f"[red]Error: Native SDK path not found: {sdk_native_path}[/red]"
            )
            raise ValueError(f"Native SDK path not found: {sdk_native_path}")
        
        if not llvm_path.exists():
            self.console.print(
                f"[yellow]Warning: LLVM path not found: {llvm_path}[/yellow]"
            )
        
        # Set environment variables
        self.env_vars = {
            # HarmonyOS SDK paths
            "NATIVE_OHOS_SDK": str(sdk_native_path),
            "OHOS_SDK_SYSROOT": str(sdk_sysroot_path),
            "LLVM_INSTALL_DIR": str(llvm_path),
            "OHOS_SDK_ROOT": str(self.config.harmony_sdk_path),
            "HOS_SDK_HOME": str(self.config.harmony_sdk_path),

            # Qt paths
            "QT5_ROOT_DIR": str(self.config.qt_source_path),
            "QT_INSTALL_PATH": str(self.config.install_path),

            # Build configuration
            "QT_ARCH": self.config.architecture,
            "QT_BUILD_TYPE": self.config.build_type,

            # Required by ohos-clang mkspec (qmake.conf uses this)
            "OHOS_TARGET_ARCH": self.config.architecture,
        }
        
        # Platform-specific settings
        if is_windows():
            self._setup_windows_environment()
        else:
            self._setup_unix_environment()
        
        # Display environment variables
        self._display_environment()
        
        return self.env_vars
    
    def _setup_windows_environment(self) -> None:
        """Setup Windows-specific environment"""
        # CRITICAL: Reset PATH first to avoid MSVC pollution
        self.reset_path_to_minimum()

        self._set_windows_tool_roots()

        # Build tool paths configured by user (preferred on Windows)
        # make_path should point to mingw32-make which is part of MinGW toolchain
        custom_tool_path = self._build_windows_tool_path()
        if custom_tool_path:
            current_path = self.env_vars.get("PATH", "")
            self.env_vars["PATH"] = f"{custom_tool_path};{current_path}"

        # Add LLVM bin to PATH
        llvm_bin = self.config.harmony_sdk_path / "native" / "llvm" / "bin"
        if llvm_bin.exists():
            current_path = self.env_vars.get("PATH", "")
            self.env_vars["PATH"] = f"{llvm_bin};{current_path}"

        # Add Perl to PATH if in tools directory
        perl_bin = Path("tools") / "perl" / "perl" / "bin"
        if perl_bin.exists():
            current_path = self.env_vars.get("PATH", "")
            self.env_vars["PATH"] = f"{perl_bin};{current_path}"

    def _set_windows_tool_roots(self) -> None:
        """Set MINGW_ROOT/PERL_ROOT from user-configured tool paths."""
        make_path = self.config.make_path
        if make_path:
            make_path = Path(make_path)
            if make_path.is_file():
                mingw_bin = make_path.parent
            elif make_path.name.lower() == "bin":
                mingw_bin = make_path
            else:
                mingw_bin = make_path / "bin"
            self.env_vars["MINGW_ROOT"] = str(mingw_bin)

        perl_path = self.config.perl_path
        if perl_path:
            perl_path = Path(perl_path)
            if perl_path.is_file():
                perl_bin = perl_path.parent
            elif perl_path.name.lower() == "bin":
                perl_bin = perl_path
            else:
                perl_bin = perl_path / "bin"
            self.env_vars["PERL_ROOT"] = str(perl_bin)

    def _build_windows_tool_path(self) -> str:
        """
        Build custom PATH entries from user-provided make/perl paths.

        Expected order (based on Qt build requirements):
        1) <make_root>\\bin
        2) <make_root>
        3) <perl_root>\\bin
        4) <perl_root>\\site\\bin
        5) <strawberry_root>\\c\\bin
        """
        entries = []

        # make root path
        make_path = self.config.make_path
        if make_path:
            make_path = Path(make_path)
            # Support executable path, bin dir path, or root dir path
            if make_path.is_file():
                make_root = make_path.parent.parent if make_path.parent.name.lower() == "bin" else make_path.parent
            elif make_path.name.lower() == "bin":
                make_root = make_path.parent
            else:
                make_root = make_path

            entries.extend([
                str(make_root / "bin"),
                str(make_root),
            ])

        # perl bin path
        perl_path = self.config.perl_path
        if perl_path:
            perl_path = Path(perl_path)
            # Support executable path or perl bin directory path
            perl_bin = perl_path.parent if perl_path.is_file() else perl_path

            # If user passed perl root, normalize to perl/bin
            if perl_bin.name.lower() == "perl":
                perl_bin = perl_bin / "bin"

            entries.append(str(perl_bin))

            perl_root = perl_bin.parent if perl_bin.name.lower() == "bin" else perl_bin
            entries.append(str(perl_root / "site" / "bin"))

            strawberry_root = perl_root.parent
            entries.append(str(strawberry_root / "c" / "bin"))

        # Keep order and remove duplicates
        deduped = []
        seen = set()
        for item in entries:
            key = item.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(item)

        return ";".join(deduped)
    
    def _setup_unix_environment(self) -> None:
        """Setup Unix-specific environment (macOS/Linux)"""
        # Add LLVM bin to PATH
        llvm_bin = self.config.harmony_sdk_path / "native" / "llvm" / "bin"
        if llvm_bin.exists():
            current_path = os.environ.get("PATH", "")
            self.env_vars["PATH"] = f"{llvm_bin}:{current_path}"
    
    def _display_environment(self) -> None:
        """Display configured environment variables"""
        self.console.print("\n[bold]Environment Variables:[/bold]")
        
        for key, value in self.env_vars.items():
            if key == "PATH":
                # Don't display full PATH, just show what we added
                self.console.print(f"  [cyan]{key}[/cyan]: [green](updated)[/green]")
            else:
                self.console.print(f"  [cyan]{key}[/cyan]: [green]{value}[/green]")
    
    def get_build_environment(self) -> Dict[str, str]:
        """
        Get environment variables for build process

        Returns:
            Complete environment dictionary for subprocess
        """
        # Start with current environment
        env = os.environ.copy()

        # Update with our variables (this will override existing values)
        env.update(self.env_vars)

        # Debug: Print final PATH for verification
        if is_windows():
            self.console.print("\n[bold cyan]Final build environment PATH:[/bold cyan]")
            path_parts = env.get("PATH", "").split(os.pathsep)
            for i, part in enumerate(path_parts[:15]):  # Show first 15 entries
                marker = ""
                if "mingw" in part.lower():
                    marker = " [green](MinGW)[/green]"
                elif "perl" in part.lower():
                    marker = " [green](Perl)[/green]"
                elif "llvm" in part.lower() or "clang" in part.lower():
                    marker = " [green](LLVM)[/green]"
                elif "msvc" in part.lower() or "visual" in part.lower():
                    marker = " [red](MSVC - PROBLEM!)[/red]"
                self.console.print(f"  {i+1}. {part}{marker}")
            if len(path_parts) > 15:
                self.console.print(f"  ... and {len(path_parts) - 15} more entries")

        return env
    
    def validate_environment(self) -> bool:
        """
        Validate that all required environment variables are set correctly
        
        Returns:
            True if all validations pass, False otherwise
        """
        self.console.print("\n[bold cyan]Validating environment...[/bold cyan]")
        
        all_valid = True
        
        # Check NATIVE_OHOS_SDK
        native_sdk = Path(self.env_vars.get("NATIVE_OHOS_SDK", ""))
        if not native_sdk.exists():
            self.console.print(f"[red]✗ NATIVE_OHOS_SDK path does not exist[/red]")
            all_valid = False
        else:
            self.console.print(f"[green]✓ NATIVE_OHOS_SDK: {native_sdk}[/green]")
        
        # Check LLVM_INSTALL_DIR
        llvm_dir = Path(self.env_vars.get("LLVM_INSTALL_DIR", ""))
        if not llvm_dir.exists():
            self.console.print(f"[yellow]⚠ LLVM_INSTALL_DIR path does not exist[/yellow]")
            # This is a warning, not an error
        else:
            self.console.print(f"[green]✓ LLVM_INSTALL_DIR: {llvm_dir}[/green]")
        
        # Check compiler
        clang_path = llvm_dir / "bin" / "clang"
        clang_pp_path = llvm_dir / "bin" / "clang++"
        
        if is_windows():
            clang_path = clang_path.with_suffix(".exe")
            clang_pp_path = clang_pp_path.with_suffix(".exe")
        
        if clang_path.exists():
            self.console.print(f"[green]✓ Clang compiler found: {clang_path}[/green]")
        else:
            self.console.print(f"[red]✗ Clang compiler not found[/red]")
            all_valid = False
        
        if clang_pp_path.exists():
            self.console.print(f"[green]✓ Clang++ compiler found: {clang_pp_path}[/green]")
        else:
            self.console.print(f"[red]✗ Clang++ compiler not found[/red]")
            all_valid = False
        
        # Check Qt source
        qt_source = Path(self.env_vars.get("QT5_ROOT_DIR", ""))
        if not qt_source.exists():
            self.console.print(f"[red]✗ Qt source path does not exist[/red]")
            all_valid = False
        else:
            self.console.print(f"[green]✓ Qt source: {qt_source}[/green]")
        
        return all_valid
    
    def save_environment_script(self, output_path: Path) -> None:
        """
        Save environment setup script
        
        Args:
            output_path: Path to save the script
        """
        if is_windows():
            self._save_windows_script(output_path)
        else:
            self._save_unix_script(output_path)
    
    def _save_windows_script(self, output_path: Path) -> None:
        """Save Windows batch script"""
        script_content = "@echo off\n"
        script_content += "REM Qt for HarmonyOS Environment Setup\n\n"
        
        for key, value in self.env_vars.items():
            if key == "PATH":
                script_content += f"SET PATH={value}\n"
            else:
                script_content += f"SET {key}={value}\n"
        
        script_content += "\necho Environment variables set successfully.\n"
        script_content += "echo Run this script before building Qt.\n"
        
        output_path.write_text(script_content, encoding="utf-8")
        self.console.print(f"[green]✓ Environment script saved: {output_path}[/green]")
    
    def _save_unix_script(self, output_path: Path) -> None:
        """Save Unix shell script"""
        script_content = "#!/bin/bash\n"
        script_content += "# Qt for HarmonyOS Environment Setup\n\n"
        
        for key, value in self.env_vars.items():
            if key == "PATH":
                script_content += f"export PATH=\"{value}\"\n"
            else:
                script_content += f"export {key}=\"{value}\"\n"
        
        script_content += "\necho 'Environment variables set successfully.'\n"
        script_content += "echo 'Run this script before building Qt.'\n"
        
        output_path.write_text(script_content, encoding="utf-8")
        
        # Make executable
        output_path.chmod(0o755)
        
        self.console.print(f"[green]✓ Environment script saved: {output_path}[/green]")
