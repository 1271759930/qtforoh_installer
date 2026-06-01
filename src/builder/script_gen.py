"""
Build script generator - Generates Windows batch scripts for Qt build
"""

import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config.schema import InstallConfig
    from .env_setup import EnvironmentManager


def get_windows_short_path(long_path: str) -> str:
    """
    Get Windows short path name (8.3 format) to handle paths with spaces.
    
    Args:
        long_path: Full Windows path that may contain spaces
        
    Returns:
        Short path name without spaces, or original path if conversion fails
    """
    try:
        import ctypes
        from ctypes import wintypes
        
        GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
        GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        GetShortPathNameW.restype = wintypes.DWORD
        
        buffer_size = GetShortPathNameW(long_path, None, 0)
        if buffer_size > 0:
            buffer = ctypes.create_unicode_buffer(buffer_size)
            result = GetShortPathNameW(long_path, buffer, buffer_size)
            if result > 0:
                return buffer.value
    except Exception:
        pass
    return long_path


def generate_build_script(
    config: "InstallConfig",
    env_manager: "EnvironmentManager",
    build_dir: Path
) -> Path:
    """
    Generate Windows batch script for building Qt.
    This avoids environment variable inheritance issues with subprocess.

    Args:
        config: Installation configuration
        env_manager: Environment manager
        build_dir: Build directory path

    Returns:
        Path to generated batch script
    """
    import sys
    import os

    env = env_manager.get_build_environment()

    # Get paths - use short path names to handle spaces in Windows
    mingw_bin = env.get("MINGW_ROOT", "")
    perl_root = env.get("PERL_ROOT", "")
    python_bin = env.get("PYTHON_ROOT", "")
    
    # Perl bin is under PERL_ROOT/perl/bin or PERL_ROOT/bin
    if perl_root:
        perl_bin_path = Path(perl_root) / "perl" / "bin"
        if perl_bin_path.exists():
            perl_bin = str(perl_bin_path)
        else:
            perl_bin_alt = Path(perl_root) / "bin"
            if perl_bin_alt.exists():
                perl_bin = str(perl_bin_alt)
            else:
                perl_bin = perl_root
    else:
        perl_bin = ""
    
    # Convert tool paths to short path if contains spaces
    if mingw_bin and " " in mingw_bin:
        mingw_bin = get_windows_short_path(mingw_bin)
    if perl_root and " " in perl_root:
        perl_root = get_windows_short_path(perl_root)
    if perl_bin and " " in perl_bin:
        perl_bin = get_windows_short_path(perl_bin)
    if python_bin and " " in python_bin:
        python_bin = get_windows_short_path(python_bin)
    
    # SDK paths - convert to short path if contains spaces
    sdk_path_str = str(config.harmony_sdk_path)
    if " " in sdk_path_str:
        sdk_path_str = get_windows_short_path(sdk_path_str)
    llvm_bin = sdk_path_str + "\\native\\llvm\\bin"
    
    # Install path - convert to short path if contains spaces
    install_path_str = str(config.actual_install_path)
    if " " in install_path_str:
        install_path_str = get_windows_short_path(install_path_str)
    
    # Qt source path - convert to short path if contains spaces
    qt_source_str = str(config.qt_source_path)
    if " " in qt_source_str:
        qt_source_str = get_windows_short_path(qt_source_str)
    
    # Build directory - convert to short path if contains spaces
    build_dir_str = str(build_dir)
    if " " in build_dir_str:
        build_dir_str = get_windows_short_path(build_dir_str)

    # If python_bin not set, try multiple fallback sources
    if not python_bin:
        # First try from config
        if config.python_path:
            from pathlib import Path as PPath
            python_path = PPath(config.python_path)
            if python_path.is_file():
                python_bin = str(python_path.parent)
            elif python_path.name.lower() == "bin":
                python_bin = str(python_path)
            else:
                python_bin = str(python_path / "bin")

        # Second fallback: use current Python executable directory
        if not python_bin:
            python_bin = os.path.dirname(sys.executable)

    # Configure script path - use short path version
    configure_script = qt_source_str + "\\configure.bat"

    # Build configure arguments
    device_prefix = f"/data/storage/el1/bundle/libs/{config.architecture.split('-')[0]}"

    # Get version-specific configuration for skip_modules and nomake_targets
    from ..config.defaults import get_qt_version_config
    version_config = get_qt_version_config(config.qt_version)
    skip_modules_list = config.skip_modules if config.skip_modules else version_config.get("skip_modules", [])
    skip_modules = " ".join([f"-skip {m}" for m in skip_modules_list])

    # Get nomake targets from config or version default
    nomake_targets_list = config.nomake_targets if config.nomake_targets else version_config.get("nomake_targets", ["doc", "examples", "tests"])
    nomake_targets = " ".join([f"-nomake {t}" for t in nomake_targets_list])

    # Get extra configure options
    extra_options = version_config.get("extra_configure_options", [])
    extra_args = " ".join(extra_options)

    # OpenGL ES option
    opengl_args = ""
    if config.force_opengl_es:
        opengl_args = "-opengl es2 -opengles3"

    cxx_std = version_config.get("c++std", "c++14")

    # Build type option
    build_type_opt = "-debug" if config.build_type == "debug" else "-release"

    # Generate script content
    script_content = f'''@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================
echo Qt for HarmonyOS Build Script
echo Qt Version: {config.qt_version}
echo Force OpenGL ES: {'Yes (-opengl es2 -opengles3)' if config.force_opengl_es else 'No (auto-detect)'}
echo Generated by qtohos-installer
echo ============================================
echo.

REM Reset PATH to avoid MSVC pollution and other MinGW interference
set "PATH=C:\\Windows\\System32;C:\\Windows"

REM Clear MAKEFLAGS to prevent sh.exe dependency from other MinGW
set "MAKEFLAGS="
set "MFLAGS="
set "SHELL=cmd.exe"

REM Add llvm-mingw-ucrt FIRST
set "MINGW_BIN={mingw_bin}"
if exist "%MINGW_BIN%" set "PATH=%PATH%;%MINGW_BIN%"
if exist "%MINGW_BIN%" echo [OK] MinGW (llvm-mingw): %MINGW_BIN%
if not exist "%MINGW_BIN%" echo [ERROR] MinGW path not found: %MINGW_BIN%
if not exist "%MINGW_BIN%" exit /b 1

REM Add Perl
set "PERL_BIN={perl_bin}"
set "PERL_ROOT={perl_root}"
if exist "%PERL_BIN%" set "PATH=%PATH%;%PERL_BIN%"
if exist "%PERL_ROOT%" set "PERL5LIB=%PERL_ROOT%\\perl\\lib;%PERL_ROOT%\\perl\\vendor\\lib;%PERL_ROOT%\\perl\\site\\lib"
if exist "%PERL_BIN%" echo [OK] Perl: %PERL_BIN%
if exist "%PERL_ROOT%" echo [OK] Perl Root: %PERL_ROOT%
if not exist "%PERL_BIN%" echo [ERROR] Perl path not found: %PERL_BIN%
if not exist "%PERL_BIN%" exit /b 1

REM Add Python for QML compilation
set "PYTHON_BIN={python_bin}"
if exist "%PYTHON_BIN%" set "PATH=%PATH%;%PYTHON_BIN%"
if exist "%PYTHON_BIN%" echo [OK] Python: %PYTHON_BIN%"
if not exist "%PYTHON_BIN%" echo [WARN] Python path not configured - using system Python

REM Add LLVM for OHOS cross-compile
set "LLVM_BIN={llvm_bin}"
if exist "%LLVM_BIN%" set "PATH=%PATH%;%LLVM_BIN%"
if exist "%LLVM_BIN%" echo [OK] LLVM: %LLVM_BIN%
if not exist "%LLVM_BIN%" echo [WARN] LLVM path not found: %LLVM_BIN%

REM Set environment variables (use short paths to handle spaces)
set "NATIVE_OHOS_SDK={sdk_path_str}\\native"
set "OHOS_SDK_SYSROOT={sdk_path_str}\\native\\sysroot"
set "LLVM_INSTALL_DIR={llvm_bin}\\.."
set "OHOS_SDK_ROOT={sdk_path_str}"
set "OHOS_TARGET_ARCH={config.architecture}"

echo.
echo Environment:
echo   NATIVE_OHOS_SDK: %NATIVE_OHOS_SDK%
echo   OHOS_TARGET_ARCH: %OHOS_TARGET_ARCH%
echo.

REM Compiler check
where cl.exe >nul 2>&1
if %errorlevel% equ 0 echo [WARN] MSVC cl.exe found in PATH - may cause issues
if %errorlevel% neq 0 echo [OK] MSVC cl.exe not found

REM Unset compiler environment variables
set "QMAKESPEC="
set "XQMAKESPEC="
set "QMAKEPATH="
set "QMAKEFEATURES="

REM Clear MSVC/compiler env vars that could leak wrong Qt headers
set "INCLUDE="
set "LIB="
set "LIBPATH="
set "QTDIR="
set "QT_PLUGIN_PATH="
set "QML2_IMPORT_PATH="
set "C_INCLUDE_PATH="
set "CPLUS_INCLUDE_PATH="

echo.
echo ============================================

REM Create build directory
set "BUILD_DIR={build_dir_str}"
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

REM Run configure
echo.
echo [Configure] Starting...
echo.

pushd "%BUILD_DIR%"

call "{configure_script}" -v -platform win32-clang-g++ -xplatform ohos-clang -device-option CROSS_COMPILE="{llvm_bin}" -prefix "{device_prefix}" -extprefix "{install_path_str}" -opensource -confirm-license {build_type_opt} -no-use-gold-linker {skip_modules} {extra_args} {opengl_args} {nomake_targets} -no-gcc-sysroot -c++std {cxx_std} -ohos-arch {config.architecture}

if %errorlevel% neq 0 echo.
if %errorlevel% neq 0 echo [ERROR] Configure failed with code %errorlevel%
if %errorlevel% neq 0 popd
if %errorlevel% neq 0 exit /b 1

echo.
echo [OK] Configure completed successfully
echo.

REM Build
echo [Build] Starting with {config.parallel_jobs} parallel jobs...
echo.

set "SHELL=cmd.exe"
mingw32-make SHELL=cmd.exe -j{config.parallel_jobs}

if %errorlevel% neq 0 echo.
if %errorlevel% neq 0 echo [ERROR] Build failed with code %errorlevel%
if %errorlevel% neq 0 popd
if %errorlevel% neq 0 exit /b 1

echo.
echo [OK] Build completed successfully
echo.

REM Install
echo [Install] Starting...
echo.

mingw32-make install

if %errorlevel% neq 0 echo.
if %errorlevel% neq 0 echo [ERROR] Install failed with code %errorlevel%
if %errorlevel% neq 0 popd
if %errorlevel% neq 0 exit /b 1

popd

REM Copy runtime DLLs
echo.
echo [Copy] Copying runtime dependencies...
for %%d in (libstdc++-6.dll libgcc_s_seh-1.dll libwinpthread-1.dll) do if exist "%MINGW_BIN%\\%%d" copy /y "%MINGW_BIN%\\%%d" "{install_path_str}\\bin\\" >nul

echo.
echo ============================================
echo [SUCCESS] Build completed!
echo Install path: {install_path_str}
echo ============================================

if exist "{install_path_str}\\bin\\qmake.exe" echo.
if exist "{install_path_str}\\bin\\qmake.exe" echo Qt version:
if exist "{install_path_str}\\bin\\qmake.exe" "{install_path_str}\\bin\\qmake.exe" -query QT_VERSION

exit /b 0
'''

    # Write script to file
    script_path = build_dir.parent / "build_qt_ohos.bat"
    script_path.write_text(script_content, encoding="utf-8")

    return script_path