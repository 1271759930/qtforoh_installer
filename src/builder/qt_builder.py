"""
Qt Builder - Build Qt for HarmonyOS
"""

import os
import sys
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple

from ..config.schema import InstallConfig
from ..config.defaults import get_qt_version_config
from ..utils import run_command, ensure_directory, is_windows
from .env_setup import EnvironmentManager
from .script_gen import generate_build_script


class QtBuilder:
    """Build Qt for HarmonyOS"""

    def __init__(
        self,
        config: InstallConfig,
        env_manager: EnvironmentManager,
        logger: Optional[logging.Logger] = None,
        workspace: Optional[Path] = None
    ):
        self.config = config
        self.env_manager = env_manager
        self.logger = logger or logging.getLogger("qtohos-installer")

        # Build directory - use workspace/temp if provided, otherwise parallel to source
        if workspace:
            self.build_dir = workspace / "temp" / f"build_{config.architecture}"
        else:
            self.build_dir = config.qt_source_path.parent / f"build_{config.architecture}"

        self.workspace = workspace

        # Make command
        self.make_cmd = "mingw32-make" if is_windows() else "make"

        # Script path for Windows batch script
        self.build_script_path: Optional[Path] = None

    def build_all(self) -> bool:
        """
        Run complete build process.

        Returns:
            True if all steps successful, False otherwise
        """
        print("\n" + "=" * 60)
        print("[bold cyan]Starting Qt Build Process[/bold cyan]")
        print("=" * 60)

        # Step 1: Prepare build directory
        if not self.prepare_build_directory():
            return False

        # On Windows, use batch script
        if is_windows():
            return self._build_with_script()

        # On Unix, use direct subprocess calls
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

        print("\n" + "=" * 60)
        print("[bold green]✓ Qt Build Process Completed Successfully[/bold]")
        print("=" * 60)

        return True

    def prepare_build_directory(self) -> bool:
        """Prepare build directory"""
        print("\n[bold cyan]Preparing build directory...[/bold cyan]")

        try:
            ensure_directory(self.build_dir)
            print(f"[green]✓ Build directory created: {self.build_dir}[/green]")
            return True

        except Exception as e:
            print(f"[red]✗ Failed to create build directory: {e}[/red]")
            self.logger.error(f"Failed to create build directory: {e}")
            return False

    def configure_qt(self) -> Tuple[int, str, str]:
        """Run Qt configure"""
        print("\n[bold cyan]Configuring Qt...[/bold cyan]")
        self.logger.info("Starting Qt configuration")

        cmd = self._generate_configure_command()
        env = self.env_manager.get_build_environment()

        exit_code, stdout, stderr = run_command(
            cmd,
            cwd=self.build_dir,
            env=env,
            capture_output=False,
            logger=self.logger
        )

        if exit_code == 0:
            print("\n[green]✓ Qt configuration completed successfully[/green]")
            self.logger.info("Qt configuration completed successfully")
        else:
            print(f"\n[red]✗ Qt configuration failed with code: {exit_code}[/red]")
            self.logger.error(f"Qt configuration failed with code: {exit_code}")

        return exit_code, stdout, stderr

    def build_qt(self) -> Tuple[int, str, str]:
        """Build Qt (make)"""
        print("\n[bold cyan]Building Qt...[/bold cyan]")
        print(f"[yellow]This may take a long time (parallel jobs: {self.config.parallel_jobs})[/yellow]")
        self.logger.info(f"Starting Qt build with {self.config.parallel_jobs} parallel jobs")

        env = self.env_manager.get_build_environment()
        cmd = [self.make_cmd, f"-j{self.config.parallel_jobs}"]

        exit_code, stdout, stderr = run_command(
            cmd,
            cwd=self.build_dir,
            env=env,
            capture_output=False,
            logger=self.logger
        )

        if exit_code == 0:
            print("\n[green]✓ Qt build completed successfully[/green]")
            self.logger.info("Qt build completed successfully")
        else:
            print(f"\n[red]✗ Qt build failed with code: {exit_code}[/red]")
            self.logger.error(f"Qt build failed with code: {exit_code}")

        return exit_code, stdout, stderr

    def install_qt(self) -> Tuple[int, str, str]:
        """Install Qt (make install)"""
        print("\n[bold cyan]Installing Qt...[/bold cyan]")
        self.logger.info("Starting Qt installation")

        env = self.env_manager.get_build_environment()
        cmd = [self.make_cmd, "install"]

        exit_code, stdout, stderr = run_command(
            cmd,
            cwd=self.build_dir,
            env=env,
            capture_output=False,
            logger=self.logger
        )

        if exit_code == 0:
            print("\n[green]✓ Qt installation completed successfully[/green]")
            self.logger.info("Qt installation completed successfully")
            self._verify_installation()
        else:
            print(f"\n[red]✗ Qt installation failed with code: {exit_code}[/red]")
            self.logger.error(f"Qt installation failed with code: {exit_code}")

        return exit_code, stdout, stderr

    def _build_with_script(self) -> bool:
        """Build Qt using generated batch script (Windows only)."""
        print("\n[bold cyan]Building Qt with batch script (Windows)...[/bold cyan]")

        # Generate the build script
        script_path = generate_build_script(
            self.config,
            self.env_manager,
            self.build_dir
        )
        self.build_script_path = script_path

        print(f"\n[yellow]Running build script: {script_path}[/yellow]")
        print("[yellow]This may take a long time...[/yellow]")
        self.logger.info(f"Executing build script: {script_path}")

        try:
            # Get Python path for clean_env - try multiple sources
            python_path = self.env_manager.env_vars.get("PYTHON_ROOT", "")

            # Fallback 1: from config
            if not python_path and self.config.python_path:
                from pathlib import Path as PPath
                p = PPath(self.config.python_path)
                if p.is_file():
                    python_path = str(p.parent)
                elif p.name.lower() == "bin":
                    python_path = str(p)
                else:
                    python_path = str(p / "bin")

            # Fallback 2: use current Python executable directory
            if not python_path:
                python_path = os.path.dirname(sys.executable)

            # Build PATH with Python
            base_path = "C:\\Windows\\System32;C:\\Windows"
            if python_path:
                base_path = f"{python_path};{base_path}"

            # Use minimal environment with Python
            clean_env = {
                "PATH": base_path,
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
                "TEMP": os.environ.get("TEMP", ""),
                "TMP": os.environ.get("TMP", ""),
                "USERPROFILE": os.environ.get("USERPROFILE", ""),
                "HOMEDRIVE": os.environ.get("HOMEDRIVE", ""),
                "HOMEPATH": os.environ.get("HOMEPATH", ""),
                "COMSPEC": os.environ.get("COMSPEC", "C:\\Windows\\System32\\cmd.exe"),
                "PATHEXT": os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD"),
            }

            # Add Python environment variable
            if python_path:
                clean_env["PYTHON_ROOT"] = python_path

            print(f"[cyan]Python path in clean_env: {python_path}[/cyan]")

            result = subprocess.run(
                [str(script_path)],
                cwd=self.build_dir.parent,
                shell=True,
                env=clean_env
            )

            if result.returncode == 0:
                print("\n" + "=" * 60)
                print("[bold green]✓ Qt Build Process Completed Successfully[/bold]")
                print("=" * 60)
                self._verify_installation()
                return True
            else:
                print(f"\n[red]✗ Build failed with code: {result.returncode}[/red]")
                self.logger.error(f"Build script failed with code: {result.returncode}")
                return False

        except Exception as e:
            print(f"\n[red]✗ Failed to run build script: {e}[/red]")
            self.logger.error(f"Failed to run build script: {e}")
            return False

    def _generate_configure_command(self) -> list:
        """Generate configure command for Qt"""
        version_config = get_qt_version_config(self.config.qt_version)

        # Configure script
        if is_windows():
            configure_script = self.config.qt_source_path / "qtbase" / "configure.bat"
            if not configure_script.exists():
                configure_script = self.config.qt_source_path / "configure.bat"
        else:
            configure_script = self.config.qt_source_path / "configure"

        cmd = [str(configure_script), "-v"]

        # Platform settings
        if is_windows():
            cmd.extend(["-platform", "win32-g++"])

        cmd.extend(["-xplatform", "ohos-clang"])

        # Common options
        cmd.extend([
            "-opensource",
            "-confirm-license",
            "-no-use-gold-linker",
            "-no-gcc-sysroot",
        ])

        # Architecture
        cmd.extend(["-ohos-arch", self.config.architecture])

        # Cross-compile option
        if is_windows():
            llvm_dir = self.env_manager.env_vars.get("LLVM_INSTALL_DIR", "")
            if llvm_dir:
                cmd.extend(["-device-option", f"CROSS_COMPILE={llvm_dir}/bin"])

        # C++ standard
        cxx_std = version_config.get("c++std", "c++14")
        cmd.extend(["-c++std", cxx_std])

        cmd.extend(["-nomake", "examples", "-nomake", "tests"])

        # Build type
        if self.config.build_type == "debug":
            cmd.append("-debug")
        elif self.config.build_type == "release":
            cmd.append("-release")
        else:
            cmd.extend(["-release", "-force-debug-info"])

        # Prefix
        device_prefix = f"/data/storage/el1/bundle/libs/{self.config.architecture.split('-')[0]}"
        cmd.extend([
            "-prefix", device_prefix,
            "-extprefix", str(self.config.actual_install_path),
        ])

        # Skip modules - use version default if not specified
        skip_modules_list = self.config.skip_modules if self.config.skip_modules else version_config.get("skip_modules", [])
        for module in skip_modules_list:
            cmd.extend(["-skip", module])

        # Extra options
        extra_options = version_config.get("extra_configure_options", [])
        cmd.extend(extra_options)

        # OpenGL ES option
        if self.config.force_opengl_es:
            cmd.extend(["-opengl", "es2", "-opengles3"])

        return cmd

    def _verify_installation(self) -> None:
        """Verify Qt installation"""
        print("\n[bold cyan]Verifying installation...[/bold cyan]")

        # Check for qmake
        qmake_path = self.config.actual_install_path / "bin" / "qmake"
        if is_windows():
            qmake_path = qmake_path.with_suffix(".exe")

        if qmake_path.exists():
            print(f"[green]✓ qmake found: {qmake_path}[/green]")

            # Get Qt version
            try:
                result = run_command(
                    [str(qmake_path), "-query", "QT_VERSION"],
                    capture_output=True,
                    logger=self.logger
                )
                if result[0] == 0:
                    qt_version = result[1].strip()
                    print(f"[green]  Qt version: {qt_version}[/green]")
            except Exception:
                pass
        else:
            print(f"[yellow]⚠ qmake not found at expected location[/yellow]")

        # Check for libraries
        lib_dir = self.config.actual_install_path / "lib"
        if lib_dir.exists():
            libs = list(lib_dir.glob("*.so")) if not is_windows() else list(lib_dir.glob("*.dll"))
            print(f"[green]✓ Found {len(libs)} libraries[/green]")
        else:
            print(f"[yellow]⚠ Library directory not found[/yellow]")