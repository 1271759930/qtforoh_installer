"""
Qt Builder - Build Qt for HarmonyOS via standalone build script
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional

from ..config.schema import InstallConfig
from ..utils import run_command, is_windows


class QtBuilder:
    """Build Qt for HarmonyOS by calling the standalone build script"""

    def __init__(
        self,
        config: InstallConfig,
        logger: Optional[logging.Logger] = None,
        workspace: Optional[Path] = None,
    ):
        self.config = config
        self.logger = logger or logging.getLogger("qtohos-installer")

        if workspace:
            self.build_dir = workspace / "temp" / f"build_{config.architecture}"
        else:
            self.build_dir = config.qt_source_path.parent / f"build_{config.architecture}"

        self.workspace = workspace

    def build_all(self) -> bool:
        """
        Run complete build process via standalone build script.

        Returns:
            True if all steps successful, False otherwise
        """
        print("\n" + "=" * 60)
        print("[bold cyan]Starting Qt Build Process[/bold cyan]")
        print("=" * 60)

        script_path = self._find_build_script()
        if not script_path:
            print("[red]Build script not found: scripts/build_qt_ohos.py[/red]")
            self.logger.error("Build script not found")
            return False

        config_path = self._write_build_config()
        print(f"[cyan]Build config: {config_path}[/cyan]")
        print(f"[cyan]Build script: {script_path}[/cyan]")

        return self._run_build_script(script_path, config_path)

    def _find_build_script(self) -> Optional[Path]:
        """Locate the standalone build script"""
        if self.workspace:
            script = self.workspace / "scripts" / "build_qt_ohos.py"
            if script.exists():
                return script

        script = Path(__file__).parent.parent.parent / "scripts" / "build_qt_ohos.py"
        if script.exists():
            return script

        return None

    def _write_build_config(self) -> Path:
        """Write config.yaml with tool paths for the build script"""
        import yaml

        config_dir = self.build_dir.parent
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "build_config.yaml"

        from ..constants import BUNDLED_LLVM_MINGW_BIN, BUNDLED_PERL_DIR

        data = self.config.to_dict()
        data["mingw_bin"] = str(BUNDLED_LLVM_MINGW_BIN)
        data["perl_root"] = str(BUNDLED_PERL_DIR)

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump({"install": data}, f, default_flow_style=False, allow_unicode=True)

        return config_path

    def _run_build_script(self, script_path: Path, config_path: Path) -> bool:
        """Execute the standalone build script as subprocess"""
        print(f"\n[yellow]Running build script...[/yellow]")
        print("[yellow]This may take a long time...[/yellow]")
        self.logger.info(f"Executing build script: {script_path}")

        try:
            if is_windows():
                return self._run_windows(script_path, config_path)
            else:
                return self._run_unix(script_path, config_path)

        except Exception as e:
            print(f"\n[red]Failed to run build script: {e}[/red]")
            self.logger.error(f"Failed to run build script: {e}")
            return False

    def _run_windows(self, script_path: Path, config_path: Path) -> bool:
        """Run build script on Windows with minimal parent environment"""
        python_dir = os.path.dirname(os.sys.executable)
        base_path = f"{python_dir};C:\\Windows\\System32;C:\\Windows"

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

        result = subprocess.run(
            [os.sys.executable, str(script_path), str(config_path)],
            cwd=str(self.build_dir.parent),
            env=clean_env,
        )

        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("[bold green]Qt Build Process Completed Successfully[/bold green]")
            print("=" * 60)
            self._verify_installation()
            return True
        else:
            print(f"\n[red]Build failed with code: {result.returncode}[/red]")
            self.logger.error(f"Build script failed with code: {result.returncode}")
            return False

    def _run_unix(self, script_path: Path, config_path: Path) -> bool:
        """Run build script on Unix (macOS/Linux)"""
        result = subprocess.run(
            [os.sys.executable, str(script_path), str(config_path)],
            cwd=str(self.build_dir.parent),
        )

        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("[bold green]Qt Build Process Completed Successfully[/bold green]")
            print("=" * 60)
            self._verify_installation()
            return True
        else:
            print(f"\n[red]Build failed with code: {result.returncode}[/red]")
            self.logger.error(f"Build script failed with code: {result.returncode}")
            return False

    def _verify_installation(self) -> None:
        """Verify Qt installation"""
        print("\n[bold cyan]Verifying installation...[/bold cyan]")

        qmake_path = self.config.actual_install_path / "bin" / "qmake"
        if is_windows():
            qmake_path = qmake_path.with_suffix(".exe")

        if qmake_path.exists():
            print(f"[green]qmake found: {qmake_path}[/green]")

            try:
                result = run_command(
                    [str(qmake_path), "-query", "QT_VERSION"],
                    capture_output=True,
                    logger=self.logger,
                )
                if result[0] == 0:
                    qt_version = result[1].strip()
                    print(f"[green]  Qt version: {qt_version}[/green]")
            except Exception:
                pass
        else:
            print(f"[yellow]qmake not found at expected location[/yellow]")

        lib_dir = self.config.actual_install_path / "lib"
        if lib_dir.exists():
            libs = list(lib_dir.glob("*.so")) if not is_windows() else list(lib_dir.glob("*.dll"))
            print(f"[green]Found {len(libs)} libraries[/green]")
        else:
            print(f"[yellow]Library directory not found[/yellow]")
