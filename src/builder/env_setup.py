"""
Environment setup - Configure build environment variables
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional

from ..config.schema import InstallConfig
from ..utils import is_windows


class EnvironmentManager:
    """Manage environment variables for Qt HarmonyOS build"""

    def __init__(self, config: InstallConfig):
        self.config = config
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

    def setup_environment(self) -> Dict[str, str]:
        """
        Setup all required environment variables.

        Returns:
            Dictionary of environment variables
        """
        # Get HarmonyOS SDK paths
        sdk_native_path = self.config.harmony_sdk_path / "native"
        sdk_sysroot_path = sdk_native_path / "sysroot"
        llvm_path = sdk_native_path / "llvm"

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

            # Required by ohos-clang mkspec
            "OHOS_TARGET_ARCH": self.config.architecture,
        }

        # Platform-specific settings
        if is_windows():
            self._setup_windows_environment()
        else:
            self._setup_unix_environment()

        return self.env_vars

    def _setup_windows_environment(self) -> None:
        """Setup Windows-specific environment"""
        # CRITICAL: Reset PATH first to avoid MSVC pollution
        self.reset_path_to_minimum()

        self._set_windows_tool_roots()

        # Build tool paths configured by user
        custom_tool_path = self._build_windows_tool_path()
        if custom_tool_path:
            current_path = self.env_vars.get("PATH", "")
            self.env_vars["PATH"] = f"{custom_tool_path};{current_path}"

        # Add Python to PATH if configured
        self._setup_python_environment()

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
        """Set MINGW_ROOT/PERL_ROOT/PYTHON_ROOT from user-configured tool paths."""
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

        python_path = self.config.python_path
        if python_path:
            python_path = Path(python_path)
            if python_path.is_file():
                python_bin = python_path.parent
            elif python_path.name.lower() == "bin":
                python_bin = python_path
            else:
                python_bin = python_path / "bin"
            self.env_vars["PYTHON_ROOT"] = str(python_bin)

    def _setup_python_environment(self) -> None:
        """Setup Python environment variables for QML compilation."""
        python_path = self.config.python_path

        if python_path:
            # User configured Python path
            python_path = Path(python_path)
            if python_path.is_file():
                python_bin = python_path.parent
            elif python_path.name.lower() == "bin":
                python_bin = python_path
            else:
                python_bin = python_path / "bin"

            # Add Python to PATH
            current_path = self.env_vars.get("PATH", "")
            self.env_vars["PATH"] = f"{python_bin};{current_path}"

            # Set PYTHON_ROOT for reference
            self.env_vars["PYTHON_ROOT"] = str(python_bin)
            self.env_vars["PYTHON_PATH"] = str(python_path)
        else:
            # No user-configured Python path - use current Python executable
            # This ensures PYTHON_ROOT is always set for script generation
            current_python_dir = Path(sys.executable).parent

            # Always set PYTHON_ROOT to current Python directory
            self.env_vars["PYTHON_ROOT"] = str(current_python_dir)

            # Check if Python is already in PATH from reset_path_to_minimum
            current_path = self.env_vars.get("PATH", "")
            if str(current_python_dir) not in current_path:
                # Add Python to PATH if not already there
                self.env_vars["PATH"] = f"{current_python_dir};{current_path}"

    def _build_windows_tool_path(self) -> str:
        """Build custom PATH entries from user-provided make/perl paths."""
        entries = []

        # Make root path
        make_path = self.config.make_path
        if make_path:
            make_path = Path(make_path)
            if make_path.is_file():
                make_root = (
                    make_path.parent.parent
                    if make_path.parent.name.lower() == "bin"
                    else make_path.parent
                )
            elif make_path.name.lower() == "bin":
                make_root = make_path.parent
            else:
                make_root = make_path

            entries.extend([
                str(make_root / "bin"),
                str(make_root),
            ])

        # Perl bin path
        perl_path = self.config.perl_path
        if perl_path:
            perl_path = Path(perl_path)
            perl_bin = perl_path.parent if perl_path.is_file() else perl_path

            if perl_bin.name.lower() == "perl":
                perl_bin = perl_bin / "bin"

            entries.append(str(perl_bin))

            perl_root = perl_bin.parent if perl_bin.name.lower() == "bin" else perl_bin
            entries.append(str(perl_root / "site" / "bin"))

            strawberry_root = perl_root.parent
            entries.append(str(strawberry_root / "c" / "bin"))

        # Deduplicate
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
        llvm_bin = self.config.harmony_sdk_path / "native" / "llvm" / "bin"
        if llvm_bin.exists():
            current_path = os.environ.get("PATH", "")
            self.env_vars["PATH"] = f"{llvm_bin}:{current_path}"

    def get_build_environment(self) -> Dict[str, str]:
        """
        Get environment variables for build process.

        Returns:
            Complete environment dictionary for subprocess
        """
        # Start with current environment
        env = os.environ.copy()

        # Update with our variables
        env.update(self.env_vars)

        return env

    def validate_environment(self) -> bool:
        """
        Validate that all required environment variables are set correctly.

        Returns:
            True if all validations pass, False otherwise
        """
        all_valid = True

        # Check NATIVE_OHOS_SDK
        native_sdk = Path(self.env_vars.get("NATIVE_OHOS_SDK", ""))
        if not native_sdk.exists():
            all_valid = False

        # Check LLVM_INSTALL_DIR
        llvm_dir = Path(self.env_vars.get("LLVM_INSTALL_DIR", ""))

        # Check compiler
        clang_path = llvm_dir / "bin" / "clang"
        clang_pp_path = llvm_dir / "bin" / "clang++"

        if is_windows():
            clang_path = clang_path.with_suffix(".exe")
            clang_pp_path = clang_pp_path.with_suffix(".exe")

        if not clang_path.exists():
            all_valid = False

        if not clang_pp_path.exists():
            all_valid = False

        # Check Qt source
        qt_source = Path(self.env_vars.get("QT5_ROOT_DIR", ""))
        if not qt_source.exists():
            all_valid = False

        return all_valid

    def save_environment_script(self, output_path: Path) -> None:
        """
        Save environment setup script.

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

    def _save_unix_script(self, output_path: Path) -> None:
        """Save Unix shell script"""
        script_content = "#!/bin/bash\n"
        script_content += "# Qt for HarmonyOS Environment Setup\n\n"

        for key, value in self.env_vars.items():
            if key == "PATH":
                script_content += f'export PATH="{value}"\n'
            else:
                script_content += f'export {key}="{value}"\n'

        script_content += "\necho 'Environment variables set successfully.'\n"
        script_content += "echo 'Run this script before building Qt.'\n"

        output_path.write_text(script_content, encoding="utf-8")
        output_path.chmod(0o755)