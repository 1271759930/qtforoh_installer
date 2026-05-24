#!/usr/bin/env python3
"""
Standalone Qt for HarmonyOS build script.

This script can be called independently by any tool, AI agent, or CI system.
It reads a config.yaml file and performs the complete Qt build process.

Usage:
    python build_qt_ohos.py config.yaml
    python build_qt_ohos.py config.yaml --build-dir /path/to/build
    python build_qt_ohos.py config.yaml --dry-run

Only Qt compilation environment variables are set:
    NATIVE_OHOS_SDK, OHOS_SDK_SYSROOT, LLVM_INSTALL_DIR, OHOS_SDK_ROOT,
    OHOS_TARGET_ARCH, PERL5LIB, PATH (MinGW+Perl+LLVM+System)

Cleared to prevent interference:
    QMAKESPEC, XQMAKESPEC, QMAKEPATH, QMAKEFEATURES, MAKEFLAGS, MFLAGS

NOT set (not needed by Qt's configure/make):
    QT5_ROOT_DIR, QT_INSTALL_PATH, QT_ARCH, QT_BUILD_TYPE,
    HOS_SDK_HOME, PYTHON_ROOT, PYTHON_PATH
"""

import argparse
import os
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def is_windows() -> bool:
    return platform.system() == "Windows"


@dataclass
class BuildConfig:
    qt_source_path: Path
    harmony_sdk_path: Path
    install_path: Path
    architecture: str = "arm64-v8a"
    qt_version: str = "5.15.16"
    build_type: str = "release"
    parallel_jobs: int = 8
    skip_modules: List[str] = field(default_factory=list)
    mingw_bin: str = ""
    perl_root: str = ""

    @property
    def actual_install_path(self) -> Path:
        return self.install_path / f"Qt{self.qt_version}-{self.architecture}"


QT_VERSION_CONFIGS = {
    "5.12": {
        "c++std": "c++14",
        "extra_options": ["-no-dbus"],
    },
    "5.15": {
        "c++std": "c++14",
        "extra_options": ["-no-dbus"],
    },
}

DEFAULT_VERSION_CONFIG = {
    "c++std": "c++14",
    "extra_options": ["-no-dbus"],
}


def get_version_config(qt_version: str) -> dict:
    parts = qt_version.split(".")
    if len(parts) >= 2:
        key = f"{parts[0]}.{parts[1]}"
        if key in QT_VERSION_CONFIGS:
            return QT_VERSION_CONFIGS[key]
    return DEFAULT_VERSION_CONFIG


def load_config(config_path: Path) -> dict:
    try:
        import yaml
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        pass

    return _minimal_yaml_load(config_path)


def _minimal_yaml_load(config_path: Path) -> dict:
    result = {}
    current_section = None
    current_list_key = None

    with open(config_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n\r")
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                continue

            if not line.startswith(" ") and not line.startswith("\t") and stripped.endswith(":"):
                current_section = stripped[:-1]
                result[current_section] = {}
                current_list_key = None
                continue

            if current_section and (line.startswith("  ") or line.startswith("\t")):
                if stripped.startswith("- "):
                    if current_list_key and current_list_key in result[current_section]:
                        val = stripped[2:].strip().strip("'\"")
                        result[current_section][current_list_key].append(val)
                    continue

                if ":" in stripped:
                    key, _, value = stripped.partition(":")
                    key = key.strip()
                    value = value.strip().strip("'\"")

                    if not value:
                        result[current_section][key] = []
                        current_list_key = key
                    else:
                        if value.lower() == "null" or value.lower() == "none":
                            value = None
                        elif value.isdigit():
                            value = int(value)
                        result[current_section][key] = value
                        current_list_key = None

    return result


def config_from_dict(data: dict) -> BuildConfig:
    install = data.get("install", data)

    return BuildConfig(
        qt_source_path=Path(install["qt_source_path"]),
        harmony_sdk_path=Path(install["harmony_sdk_path"]),
        install_path=Path(install["install_path"]),
        architecture=install.get("architecture", "arm64-v8a"),
        qt_version=install.get("qt_version", "5.15.16"),
        build_type=install.get("build_type", "release"),
        parallel_jobs=int(install.get("parallel_jobs", 8)),
        skip_modules=install.get("skip_modules", []),
        mingw_bin=install.get("mingw_bin", ""),
        perl_root=install.get("perl_root", ""),
    )


def validate_config(config: BuildConfig) -> bool:
    ok = True

    if not config.qt_source_path.exists():
        print(f"[ERROR] Qt source path not found: {config.qt_source_path}")
        ok = False
    elif not (config.qt_source_path / "qtbase").exists() and \
         not (config.qt_source_path / "configure").exists() and \
         not (config.qt_source_path / "configure.bat").exists():
        print(f"[ERROR] Not a valid Qt source directory: {config.qt_source_path}")
        ok = False
    else:
        print(f"[OK] Qt source: {config.qt_source_path}")

    if not config.harmony_sdk_path.exists():
        print(f"[ERROR] HarmonyOS SDK path not found: {config.harmony_sdk_path}")
        ok = False
    else:
        print(f"[OK] HarmonyOS SDK: {config.harmony_sdk_path}")

    native = config.harmony_sdk_path / "native"
    if not native.exists():
        print(f"[ERROR] Native SDK not found: {native}")
        ok = False

    llvm = native / "llvm"
    if not llvm.exists():
        print(f"[ERROR] LLVM not found: {llvm}")
        ok = False

    if is_windows():
        mingw_make = Path(config.mingw_bin) / "mingw32-make.exe" if config.mingw_bin else None
        if config.mingw_bin and mingw_make and mingw_make.exists():
            print(f"[OK] MinGW: {config.mingw_bin}")
        elif config.mingw_bin:
            print(f"[ERROR] MinGW make not found at: {mingw_make}")
            ok = False
        else:
            print("[WARN] mingw_bin not set in config - build will fail on Windows")
            ok = False

        if config.perl_root:
            perl_exe = Path(config.perl_root) / "perl" / "bin" / "perl.exe"
            perl_alt = Path(config.perl_root) / "bin" / "perl.exe"
            if perl_exe.exists() or perl_alt.exists():
                print(f"[OK] Perl: {config.perl_root}")
            else:
                print(f"[ERROR] Perl not found under: {config.perl_root}")
                ok = False
        else:
            print("[WARN] perl_root not set in config - build will fail on Windows")
            ok = False

    print(f"[OK] Architecture: {config.architecture}")
    print(f"[OK] Qt version: {config.qt_version}")
    print(f"[OK] Build type: {config.build_type}")
    print(f"[OK] Install path: {config.actual_install_path}")

    return ok


def setup_windows_env(config: BuildConfig) -> Dict[str, str]:
    env = {}

    env["PATH"] = "C:\\Windows\\System32;C:\\Windows"
    env["MAKEFLAGS"] = ""
    env["MFLAGS"] = ""
    env["SHELL"] = "cmd.exe"
    env["QMAKESPEC"] = ""
    env["XQMAKESPEC"] = ""
    env["QMAKEPATH"] = ""
    env["QMAKEFEATURES"] = ""

    if config.mingw_bin:
        env["PATH"] += f";{config.mingw_bin}"

    if config.perl_root:
        perl_bin = _find_perl_bin(config.perl_root)
        if perl_bin:
            env["PATH"] += f";{perl_bin}"
        perl_root_path = Path(config.perl_root)
        env["PERL5LIB"] = ";".join([
            str(perl_root_path / "perl" / "lib"),
            str(perl_root_path / "perl" / "vendor" / "lib"),
            str(perl_root_path / "perl" / "site" / "lib"),
        ])

    sdk = str(config.harmony_sdk_path)
    llvm_bin = str(config.harmony_sdk_path / "native" / "llvm" / "bin")
    env["PATH"] += f";{llvm_bin}"

    env["NATIVE_OHOS_SDK"] = f"{sdk}\\native"
    env["OHOS_SDK_SYSROOT"] = f"{sdk}\\native\\sysroot"
    env["LLVM_INSTALL_DIR"] = f"{sdk}\\native\\llvm"
    env["OHOS_SDK_ROOT"] = sdk
    env["OHOS_TARGET_ARCH"] = config.architecture

    print("\nBuild environment (Qt compilation only):")
    for k in ["NATIVE_OHOS_SDK", "OHOS_SDK_SYSROOT", "LLVM_INSTALL_DIR",
              "OHOS_TARGET_ARCH", "PATH"]:
        print(f"  {k}={env.get(k, '')}")

    return env


def setup_unix_env(config: BuildConfig) -> Dict[str, str]:
    env = os.environ.copy()

    for k in ["MAKEFLAGS", "MFLAGS", "QMAKESPEC", "XQMAKESPEC",
              "QMAKEPATH", "QMAKEFEATURES"]:
        env[k] = ""

    sdk = str(config.harmony_sdk_path)
    llvm_bin = str(config.harmony_sdk_path / "native" / "llvm" / "bin")
    env["PATH"] = f"{llvm_bin}:{env.get('PATH', '')}"

    env["NATIVE_OHOS_SDK"] = f"{sdk}/native"
    env["OHOS_SDK_SYSROOT"] = f"{sdk}/native/sysroot"
    env["LLVM_INSTALL_DIR"] = f"{sdk}/native/llvm"
    env["OHOS_SDK_ROOT"] = sdk
    env["OHOS_TARGET_ARCH"] = config.architecture

    import shutil
    perl_path = shutil.which("perl")
    if perl_path:
        perl_dir = Path(perl_path).parent.parent
        env["PERL5LIB"] = ":".join([
            str(perl_dir / "lib"),
            str(perl_dir / "vendor" / "lib"),
            str(perl_dir / "site" / "lib"),
        ])
    else:
        print("[WARN] Perl not found in PATH")

    print("\nBuild environment (Qt compilation only):")
    for k in ["NATIVE_OHOS_SDK", "OHOS_SDK_SYSROOT", "LLVM_INSTALL_DIR",
              "OHOS_TARGET_ARCH"]:
        print(f"  {k}={env.get(k, '')}")

    return env


def _find_perl_bin(perl_root: str) -> Optional[str]:
    root = Path(perl_root)
    for candidate in [root / "perl" / "bin", root / "bin"]:
        if candidate.exists():
            return str(candidate)
    return None


def generate_configure_args(config: BuildConfig, win: bool) -> List[str]:
    vc = get_version_config(config.qt_version)

    if win:
        cfg = config.qt_source_path / "qtbase" / "configure.bat"
        if not cfg.exists():
            cfg = config.qt_source_path / "configure.bat"
    else:
        cfg = config.qt_source_path / "configure"

    args = [str(cfg), "-v"]

    if win:
        args.extend(["-platform", "win32-clang-g++"])

    args.extend(["-xplatform", "ohos-clang"])

    if win:
        llvm_bin = str(config.harmony_sdk_path / "native" / "llvm" / "bin")
        args.extend(["-device-option", f"CROSS_COMPILE={llvm_bin}"])

    device_prefix = f"/data/storage/el1/bundle/libs/{config.architecture.split('-')[0]}"
    args.extend([
        "-prefix", device_prefix,
        "-extprefix", str(config.actual_install_path),
        "-opensource", "-confirm-license",
        "-no-use-gold-linker", "-no-gcc-sysroot",
    ])

    if config.build_type == "debug":
        args.append("-debug")
    else:
        args.append("-release")

    args.extend(["-ohos-arch", config.architecture])
    args.extend(["-c++std", vc.get("c++std", "c++14")])
    args.extend(["-nomake", "tests", "-nomake", "examples"])

    for m in config.skip_modules:
        args.extend(["-skip", m])

    args.extend(vc.get("extra_options", []))

    return args


def run_subprocess(cmd: List[str], cwd: Path, env: Dict[str, str],
                   shell: bool = False) -> int:
    print(f"\n$ {' '.join(str(c) for c in cmd)}\n")

    try:
        proc = subprocess.Popen(
            cmd, cwd=str(cwd), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            bufsize=1, universal_newlines=False,
            shell=shell,
        )

        for raw_line in iter(proc.stdout.readline, b""):
            text = _decode(raw_line)
            print(text, end="", flush=True)

        proc.wait()
        return proc.returncode

    except FileNotFoundError:
        print(f"[ERROR] Command not found: {cmd[0]}")
        return 1
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1


def _decode(data: bytes) -> str:
    for enc in ["utf-8", "gbk", "cp936"]:
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def verify_installation(config: BuildConfig) -> bool:
    qmake = config.actual_install_path / "bin" / ("qmake.exe" if is_windows() else "qmake")

    if qmake.exists():
        print(f"\n[OK] qmake found: {qmake}")
        try:
            r = subprocess.run(
                [str(qmake), "-query", "QT_VERSION"],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode == 0:
                print(f"[OK] Qt version: {r.stdout.strip()}")
        except Exception:
            pass
        return True

    print(f"[WARN] qmake not found at: {qmake}")
    return False


def build(config: BuildConfig, build_dir: Path) -> bool:
    build_dir.mkdir(parents=True, exist_ok=True)
    win = is_windows()

    if win:
        return _build_windows(config, build_dir)

    return _build_unix(config, build_dir)


def _build_unix(config: BuildConfig, build_dir: Path) -> bool:
    env = setup_unix_env(config)
    make = "make"

    args = generate_configure_args(config, False)
    if run_subprocess(args, build_dir, env) != 0:
        print("[ERROR] Configure failed")
        return False

    if run_subprocess([make, f"-j{config.parallel_jobs}"], build_dir, env) != 0:
        print("[ERROR] Build failed")
        return False

    if run_subprocess([make, "install"], build_dir, env) != 0:
        print("[ERROR] Install failed")
        return False

    return verify_installation(config)


def _build_windows(config: BuildConfig, build_dir: Path) -> bool:
    script_path = _generate_bat(config, build_dir)
    print(f"\nBuild script generated: {script_path}")
    print("Running build script...\n")

    try:
        clean_env = {
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
            "TEMP": os.environ.get("TEMP", ""),
            "TMP": os.environ.get("TMP", ""),
            "COMSPEC": os.environ.get("COMSPEC", "C:\\Windows\\System32\\cmd.exe"),
            "PATHEXT": os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD"),
        }

        r = subprocess.run(
            [str(script_path)],
            cwd=str(build_dir.parent),
            shell=True,
            env=clean_env,
        )
        return r.returncode == 0

    except Exception as e:
        print(f"[ERROR] Failed to run build script: {e}")
        return False


def _generate_bat(config: BuildConfig, build_dir: Path) -> Path:
    mingw_bin = config.mingw_bin
    perl_root = config.perl_root

    perl_bin = ""
    if perl_root:
        pb = _find_perl_bin(perl_root)
        if pb:
            perl_bin = pb

    sdk = str(config.harmony_sdk_path)
    llvm_bin = f"{sdk}\\native\\llvm\\bin"
    install_path = str(config.actual_install_path)
    qt_source = str(config.qt_source_path)
    build_dir_str = str(build_dir)

    device_prefix = f"/data/storage/el1/bundle/libs/{config.architecture.split('-')[0]}"

    vc = get_version_config(config.qt_version)
    skip_args = " ".join(f"-skip {m}" for m in config.skip_modules)
    extra_args = " ".join(vc.get("extra_options", []))
    cxx_std = vc.get("c++std", "c++14")
    build_type_opt = "-debug" if config.build_type == "debug" else "-release"

    if (Path(qt_source) / "qtbase" / "configure.bat").exists():
        configure_script = f"{qt_source}\\qtbase\\configure.bat"
    else:
        configure_script = f"{qt_source}\\configure.bat"

    perl5lib = ""
    if perl_root:
        perl5lib = f"{perl_root}\\perl\\lib;{perl_root}\\perl\\vendor\\lib;{perl_root}\\perl\\site\\lib"

    lines = [
        "@echo off",
        "chcp 65001 >nul",
        "setlocal enabledelayedexpansion",
        "",
        "echo ============================================",
        "echo Qt for HarmonyOS Build Script",
        f"echo Qt Version: {config.qt_version}",
        "echo ============================================",
        "echo.",
        "",
        'REM === Qt compilation environment variables only ===',
        'set "PATH=C:\\Windows\\System32;C:\\Windows"',
        'set "MAKEFLAGS="',
        'set "MFLAGS="',
        'set "SHELL=cmd.exe"',
        'set "QMAKESPEC="',
        'set "XQMAKESPEC="',
        'set "QMAKEPATH="',
        'set "QMAKEFEATURES="',
        "",
        f'set "MINGW_BIN={mingw_bin}"',
        'if exist "%MINGW_BIN%" set "PATH=%PATH%;%MINGW_BIN%"',
        'if exist "%MINGW_BIN%" echo [OK] MinGW: %MINGW_BIN%',
        'if not exist "%MINGW_BIN%" echo [ERROR] MinGW not found: %MINGW_BIN%',
        'if not exist "%MINGW_BIN%" exit /b 1',
        "",
        f'set "PERL_BIN={perl_bin}"',
        f'set "PERL_ROOT={perl_root}"',
        f'set "PERL5LIB={perl5lib}"',
        'if exist "%PERL_BIN%" set "PATH=%PATH%;%PERL_BIN%"',
        'if exist "%PERL_BIN%" echo [OK] Perl: %PERL_BIN%',
        'if not exist "%PERL_BIN%" echo [ERROR] Perl not found: %PERL_BIN%',
        'if not exist "%PERL_BIN%" exit /b 1',
        "",
        f'set "LLVM_BIN={llvm_bin}"',
        'if exist "%LLVM_BIN%" set "PATH=%PATH%;%LLVM_BIN%"',
        'if exist "%LLVM_BIN%" echo [OK] LLVM: %LLVM_BIN%',
        "",
        f'set "NATIVE_OHOS_SDK={sdk}\\native"',
        f'set "OHOS_SDK_SYSROOT={sdk}\\native\\sysroot"',
        f'set "LLVM_INSTALL_DIR={sdk}\\native\\llvm"',
        f'set "OHOS_SDK_ROOT={sdk}"',
        f'set "OHOS_TARGET_ARCH={config.architecture}"',
        "",
        "echo.",
        "echo Environment:",
        "echo   NATIVE_OHOS_SDK: %NATIVE_OHOS_SDK%",
        "echo   OHOS_TARGET_ARCH: %OHOS_TARGET_ARCH%",
        "echo.",
        "",
        "where cl.exe >nul 2>&1",
        "if %errorlevel% equ 0 echo [WARN] MSVC cl.exe found in PATH",
        "if %errorlevel% neq 0 echo [OK] MSVC cl.exe not found",
        "",
        "echo.",
        "echo ============================================",
        "",
        f'set "BUILD_DIR={build_dir_str}"',
        'if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"',
        "",
        "echo [Configure] Starting...",
        'pushd "%BUILD_DIR%"',
        "",
        f'call "{configure_script}" -v -platform win32-clang-g++ -xplatform ohos-clang'
        f' -device-option CROSS_COMPILE="{llvm_bin}"'
        f' -prefix "{device_prefix}" -extprefix "{install_path}"'
        f" -opensource -confirm-license {build_type_opt}"
        f" -no-use-gold-linker -no-gcc-sysroot"
        f" -c++std {cxx_std} -ohos-arch {config.architecture}"
        f" {skip_args} {extra_args}"
        f" -nomake tests -nomake examples",
        "",
        "if %errorlevel% neq 0 echo [ERROR] Configure failed: %errorlevel%",
        "if %errorlevel% neq 0 popd",
        "if %errorlevel% neq 0 exit /b 1",
        "echo [OK] Configure completed",
        "",
        f"echo [Build] Starting ({config.parallel_jobs} jobs)...",
        'set "SHELL=cmd.exe"',
        f"mingw32-make SHELL=cmd.exe -j{config.parallel_jobs}",
        "",
        "if %errorlevel% neq 0 echo [ERROR] Build failed: %errorlevel%",
        "if %errorlevel% neq 0 popd",
        "if %errorlevel% neq 0 exit /b 1",
        "echo [OK] Build completed",
        "",
        "echo [Install] Starting...",
        "mingw32-make install",
        "",
        "if %errorlevel% neq 0 echo [ERROR] Install failed: %errorlevel%",
        "if %errorlevel% neq 0 popd",
        "if %errorlevel% neq 0 exit /b 1",
        "",
        "popd",
        "",
        "echo [Copy] Runtime DLLs...",
        f'for %%d in (libstdc++-6.dll libgcc_s_seh-1.dll libwinpthread-1.dll) do'
        f' if exist "{mingw_bin}\\%%d" copy /y "{mingw_bin}\\%%d"'
        f' "{install_path}\\bin\\" >nul',
        "",
        "echo.",
        "echo ============================================",
        "echo [SUCCESS] Build completed!",
        f"echo Install path: {install_path}",
        "echo ============================================",
        "",
        f'if exist "{install_path}\\bin\\qmake.exe" "{install_path}\\bin\\qmake.exe" -query QT_VERSION',
        "",
        "exit /b 0",
    ]

    script_path = build_dir.parent / "build_qt_ohos.bat"
    script_path.write_text("\r\n".join(lines), encoding="utf-8")
    return script_path


def main():
    parser = argparse.ArgumentParser(
        description="Build Qt for HarmonyOS (standalone script)",
    )
    parser.add_argument(
        "config", type=Path,
        help="Path to config.yaml",
    )
    parser.add_argument(
        "--build-dir", type=Path, default=None,
        help="Override build directory",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Validate config and show environment, do not build",
    )

    args = parser.parse_args()

    if not args.config.exists():
        print(f"[ERROR] Config file not found: {args.config}")
        sys.exit(1)

    data = load_config(args.config)
    if not data:
        print("[ERROR] Failed to load config")
        sys.exit(1)

    config = config_from_dict(data)

    print("=" * 50)
    print("Qt for HarmonyOS Build Script")
    print("=" * 50)

    if not validate_config(config):
        print("\n[ERROR] Configuration validation failed")
        sys.exit(1)

    if args.dry_run:
        if is_windows():
            setup_windows_env(config)
        else:
            setup_unix_env(config)

        args_list = generate_configure_args(config, is_windows())
        print("\nConfigure command:")
        print(" ".join(args_list))
        print("\n[OK] Dry run complete - no build performed")
        sys.exit(0)

    if args.build_dir:
        build_dir = args.build_dir
    else:
        build_dir = config.qt_source_path.parent / f"build_{config.architecture}"

    ok = build(config, build_dir)

    if ok:
        print("\n" + "=" * 50)
        print("[SUCCESS] Qt for HarmonyOS build completed!")
        print(f"Install path: {config.actual_install_path}")
        print("=" * 50)
        sys.exit(0)
    else:
        print("\n[ERROR] Build failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
