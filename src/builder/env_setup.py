"""
Environment setup - Configure build environment variables
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional

from ..config.schema import InstallConfig
from ..utils import is_windows
from ..constants import (
    BUNDLED_LLVM_MINGW_BIN,
    BUNDLED_PERL_BIN,
    BUNDLED_PERL_BIN_ALT,
)


# ---------------------------------------------------------------------------
# Windows 8.3 short-path helpers
# ---------------------------------------------------------------------------

def _get_windows_short_path(path: str) -> str:
    """Return the 8.3 short path name for *path* (Windows only).

    Qt's ``qmake`` does not quote compiler paths when probing the compiler,
    so any path containing spaces (e.g. ``C:\\Program Files\\Huawei\\...``)
    gets split at the first space and execution fails with something like::

        Cannot run target compiler 'C:\\Program Files\\...clang++'

    Using the DOS-style short name (``C:\\PROGRA~1\\...``) avoids this.

    Returns the original *path* when short-path conversion fails or when
    the path does not contain spaces.
    """
    if " " not in path:
        return path
    try:
        import ctypes
        from ctypes import wintypes

        get_short = ctypes.windll.kernel32.GetShortPathNameW
        get_short.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        get_short.restype = wintypes.DWORD

        needed = get_short(path, None, 0)
        if needed > 0:
            buf = ctypes.create_unicode_buffer(needed)
            if get_short(path, buf, needed) > 0:
                return buf.value
    except Exception:
        pass
    return path


def _ensure_short_on_windows(path: str) -> str:
    """Convert *path* to its 8.3 short form on Windows when it contains spaces.

    On other platforms the path is returned unchanged.
    """
    if not is_windows():
        return path
    return _get_windows_short_path(path)


class EnvironmentManager:
    """Manage environment variables for Qt HarmonyOS build"""

    def __init__(self, config: InstallConfig):
        self.config = config
        self.env_vars: Dict[str, str] = {}

        # Bundled tools paths (from constants)
        self.bundled_mingw_bin = BUNDLED_LLVM_MINGW_BIN
        self.bundled_perl_bin = BUNDLED_PERL_BIN
        self.bundled_perl_bin_alt = BUNDLED_PERL_BIN_ALT

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
        # Get HarmonyOS SDK paths (long form - used for file-existence validation)
        sdk_native_path = self.config.harmony_sdk_path / "native"
        sdk_sysroot_path = sdk_native_path / "sysroot"
        llvm_path = sdk_native_path / "llvm"

        # Qt's qmake does not quote compiler paths when probing, so any path
        # containing a space (e.g. "C:\Program Files\Huawei\...") gets split
        # and clang++ fails with "Cannot run target compiler 'C:\Program' ...".
        # Using the Windows 8.3 short form avoids this.
        sdk_native_env = _ensure_short_on_windows(str(sdk_native_path))
        sdk_sysroot_env = _ensure_short_on_windows(str(sdk_sysroot_path))
        llvm_dir_env = _ensure_short_on_windows(str(llvm_path))
        harmony_sdk_env = _ensure_short_on_windows(str(self.config.harmony_sdk_path))

        # Set environment variables
        self.env_vars = {
            # HarmonyOS SDK paths (short form on Windows when they contain spaces)
            "NATIVE_OHOS_SDK": sdk_native_env,
            "OHOS_SDK_SYSROOT": sdk_sysroot_env,
            "LLVM_INSTALL_DIR": llvm_dir_env,
            "OHOS_SDK_ROOT": harmony_sdk_env,
            "HOS_SDK_HOME": harmony_sdk_env,

            # Qt paths
            "QT5_ROOT_DIR": str(self.config.qt_source_path),
            "QT_INSTALL_PATH": str(self.config.actual_install_path),

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
        """Setup Windows-specific environment - Bundled tools first"""
        # CRITICAL: Reset PATH first to avoid MSVC pollution
        self.reset_path_to_minimum()

        # Set tool roots from bundled tools
        self._set_windows_tool_roots()

        # Add bundled llvm-mingw to PATH if available
        if self.bundled_mingw_bin.exists():
            current_path = self.env_vars.get("PATH", "")
            self.env_vars["PATH"] = f"{self.bundled_mingw_bin};{current_path}"
            self.env_vars["MINGW_ROOT"] = str(self.bundled_mingw_bin)

        # Add bundled Perl to PATH if available
        if self.bundled_perl_bin.exists():
            current_path = self.env_vars.get("PATH", "")
            self.env_vars["PATH"] = f"{self.bundled_perl_bin};{current_path}"
            self.env_vars["PERL_ROOT"] = str(self.bundled_perl_bin.parent.parent)
        elif self.bundled_perl_bin_alt.exists():
            current_path = self.env_vars.get("PATH", "")
            self.env_vars["PATH"] = f"{self.bundled_perl_bin_alt};{current_path}"
            self.env_vars["PERL_ROOT"] = str(self.bundled_perl_bin_alt.parent)

        # Add Python to PATH if configured
        self._setup_python_environment()

        # Add LLVM bin to PATH
        llvm_bin = self.config.harmony_sdk_path / "native" / "llvm" / "bin"
        if llvm_bin.exists():
            current_path = self.env_vars.get("PATH", "")
            self.env_vars["PATH"] = f"{llvm_bin};{current_path}"

    def _set_windows_tool_roots(self) -> None:
        """Set MINGW_ROOT/PERL_ROOT/PYTHON_ROOT from bundled tools or user config."""
        # MinGW - bundled tools only
        if self.bundled_mingw_bin.exists():
            self.env_vars["MINGW_ROOT"] = str(self.bundled_mingw_bin)

        # Perl - bundled tools only
        if self.bundled_perl_bin.exists():
            self.env_vars["PERL_ROOT"] = str(self.bundled_perl_bin.parent.parent)
        elif self.bundled_perl_bin_alt.exists():
            self.env_vars["PERL_ROOT"] = str(self.bundled_perl_bin_alt.parent)

        # Python path - user config only (no bundled Python)
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
        """Save Windows batch script with persistent user environment variables.

        Uses ``setx`` so that variables survive across terminal sessions.
        The critical env vars (``NATIVE_OHOS_SDK``, ``OHOS_TARGET_ARCH``, …)
        are persisted to the user-level registry.  ``PATH`` is handled
        separately via PowerShell/registry append to avoid the 1024-char
        ``setx`` limit and to preserve existing user PATH entries.

        ``SET`` is also issued for each variable so that a CMD session
        running or ``call``-ing this script picks up the values immediately.
        """
        # Collect tool directories that must be on PATH for qmake / make / perl.
        # NOTE: The OHOS SDK ``native/llvm/bin`` (containing ARM/x86_64 OHOS
        # cross-compilers clang/clang++) is intentionally NOT added to PATH.
        # qmake resolves those compilers via the ``NATIVE_OHOS_SDK`` env var
        # in the ohos-clang mkspec. Putting OHOS cross-compilers in PATH
        # causes qmake to attempt to run them directly as host executables,
        # which fails on Windows (they target OHOS, not Windows).
        path_additions: list[str] = []
        if self.bundled_mingw_bin.exists():
            path_additions.append(str(self.bundled_mingw_bin))
        if self.bundled_perl_bin.exists():
            path_additions.append(str(self.bundled_perl_bin))
        elif self.bundled_perl_bin_alt.exists():
            path_additions.append(str(self.bundled_perl_bin_alt))

        lines: list[str] = []
        lines.append("@echo off")
        lines.append("REM Qt for HarmonyOS Environment Setup")
        lines.append(
            "REM Generated by qtforoh_installer – "
            "variables are persisted via setx (user-level registry)"
        )
        lines.append("")

        # ── Persistent user-level variables ──────────────────────────
        lines.append("REM === Persist environment variables (user-level) ===")
        for key, value in self.env_vars.items():
            if key == "PATH":
                continue
            escaped = value.replace('"', '""')
            lines.append(f'setx {key} "{escaped}" >nul 2>&1')

        # The env_vars["NATIVE_OHOS_SDK"] is now a short path on Windows when
        # the SDK lives in a path with spaces. Old installations however may
        # have left the long form in user PATH. Clean both variants so re-
        # running the script is idempotent across versions.
        sdk_native_short = str(self.config.harmony_sdk_path / "native")
        sdk_native_short = _ensure_short_on_windows(sdk_native_short)
        sdk_native_long = str(self.config.harmony_sdk_path / "native")

        # Use PowerShell to atomically: (1) remove any old OHOS SDK entries
        # (both long and short prefixes - these contain cross-compilers that
        # must NOT be in PATH), then (2) append the host-tool dirs if not
        # already present.
        lines.append("")
        lines.append(
            "REM Update user PATH: remove OHOS cross-compilers, keep host tools"
        )
        add_str = ";".join(path_additions) if path_additions else ""
        lines.append(
            f'powershell -NoProfile -Command "'
            f"$p=[Environment]::GetEnvironmentVariable('Path','User');"
            f"$nativeLong='{sdk_native_long}';"
            f"$nativeShort='{sdk_native_short}';"
            # Strip any entry whose normalized path lives under the OHOS SDK
            # ``native`` folder - whether it was stored as the long form or
            # the 8.3 short form. Also accept mixed forward/back slashes.
            f"$parts=if($p){{$p.Split(';')}}else{{@()}};"
            f"$kept=@();"
            f"$removedCount=0;"
            f"foreach($d in $parts){{"
            f"if(-not $d){{continue}};"
            f"$n=$d.Replace('/','\\');"
            f"if($n.StartsWith($nativeLong,[System.StringComparison]::OrdinalIgnoreCase)"
            f" -or $n.StartsWith($nativeShort,[System.StringComparison]::OrdinalIgnoreCase))"
            f"{{$removedCount++}}else{{$kept+=$d}}}};"
            # Append host-tool dirs (mingw, perl) if missing
            f"$add='{add_str}';"
            f"$addedCount=0;"
            f'if($add){{'
            f"foreach($nd in $add.Split(';')){{"
            f"if($nd -and $kept -notcontains $nd){{$kept=$kept+$nd;$addedCount++}}}}}};"
            f"if($removedCount -gt 0 -or $addedCount -gt 0){{"
            f"$newPath=$kept -join ';';"
            f"[Environment]::SetEnvironmentVariable('Path',$newPath,'User');"
            f'Write-Host "  [PATH] Removed $removedCount OHOS cross-compiler entries, added $addedCount host-tool entries"}}'
            f'else{{Write-Host "  [PATH] User PATH already clean"}}" '
        )
        # Build a session PATH that includes host tools for immediate use,
        # but excludes OHOS SDK LLVM bin (keep cross-compiler out of session too).
        session_parts: list[str] = list(path_additions)
        session_parts.append("%PATH%")
        session_path = ";".join(session_parts)
        lines.append(f"SET PATH={session_path}")

        lines.append("")

        # ── Immediate session variables (for CMD callers) ─────────────
        lines.append("REM === Current session variables ===")
        for key, value in self.env_vars.items():
            if key == "PATH":
                continue
            lines.append(f"SET {key}={value}")

        lines.append("")
        lines.append("echo.")
        lines.append("echo ============================================")
        lines.append("echo Environment variables set successfully.")
        lines.append("echo   [setx] Variables persisted to user-level registry.")
        lines.append("echo.")
        lines.append("echo NOTE: Open a NEW terminal for changes to take effect,")
        lines.append("echo       or use the SET values above in CMD immediately.")
        lines.append("echo ============================================")
        lines.append("")

        output_path.write_text("\n".join(lines), encoding="utf-8")

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