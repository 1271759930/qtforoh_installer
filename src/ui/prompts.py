"""
Interactive prompts - Modern CLI UI with selection lists and input boxes
"""

from pathlib import Path
from typing import Optional, Tuple, List
import questionary
from questionary import Style

from ..config.schema import InstallConfig
from ..config.defaults import get_qt_version_config
from ..utils import validate_path, detect_qt_version


# Custom style for questionary - similar to Claude CLI
CUSTOM_STYLE = Style([
    ("qmark", "fg:cyan bold"),
    ("question", "fg:white bold"),
    ("answer", "fg:green bold"),
    ("pointer", "fg:cyan bold"),
    ("highlighted", "fg:cyan bold"),
    ("selected", "fg:green"),
    ("separator", "fg:gray"),
    ("instruction", "fg:gray"),
    ("text", "fg:white"),
])


class ConfigCollector:
    """Interactive configuration collector with modern UI"""

    def __init__(self):
        pass

    def _print_header(self, title: str) -> None:
        """Print a section header"""
        print()
        print(f"\033[96m{'─' * 50}\033[0m")
        print(f"\033[1;96m  {title}\033[0m")
        print(f"\033[96m{'─' * 50}\033[0m")
        print()

    def collect_qt_source_path(self, default: Optional[str] = None) -> Path:
        """Collect Qt source path with interactive input"""
        self._print_header("Qt Source Code Path")

        print("Please specify the path to Qt source code (tqtc-qt5).")
        print("This should contain the Qt source files for HarmonyOS.")
        print()

        while True:
            response = questionary.path(
                "Qt source code path:",
                default=default or "",
                style=CUSTOM_STYLE,
                validate=lambda x: len(x.strip()) > 0 or "Path cannot be empty"
            ).ask()

            if response is None:
                raise KeyboardInterrupt("Installation cancelled by user")

            path = Path(response.strip())
            is_valid, message = validate_path(path, must_exist=True, create=False)

            if is_valid:
                # Validate Qt source
                if not (path / "qtbase").exists():
                    print(f"\033[93m  Warning: 'qtbase' not found in Qt source directory\033[0m")
                print(f"\033[92m  ✓ {message}\033[0m")
                return path
            else:
                print(f"\033[91m  ✗ {message}\033[0m")
                print()

    def collect_harmony_sdk_path(self, default: Optional[str] = None) -> Path:
        """Collect HarmonyOS SDK path with interactive input"""
        self._print_header("HarmonyOS SDK Path")

        print("Please specify the path to HarmonyOS SDK.")
        print("This should contain the 'native' directory with LLVM toolchain.")
        print("Example: C:\\Users\\<user>\\Library\\OpenHarmony\\Sdk\\12")
        print()

        while True:
            response = questionary.path(
                "HarmonyOS SDK path:",
                default=default or "",
                style=CUSTOM_STYLE,
            ).ask()

            if response is None:
                raise KeyboardInterrupt("Installation cancelled by user")

            path = Path(response.strip())
            is_valid, message = validate_path(path, must_exist=True, create=False)

            if is_valid:
                # Validate SDK structure
                native_path = path / "native"
                if not native_path.exists():
                    print(f"\033[91m  ✗ 'native' directory not found in SDK path\033[0m")
                    continue
                print(f"\033[92m  ✓ {message}\033[0m")
                return path
            else:
                print(f"\033[91m  ✗ {message}\033[0m")
                print()

    def collect_install_path(self, default: Optional[str] = None) -> Path:
        """Collect Qt installation path with interactive input"""
        self._print_header("Qt Installation Path")

        print("Please specify where to install Qt for HarmonyOS.")
        print("This directory will contain the compiled Qt libraries and headers.")
        print("Example: C:\\Qt\\Qt5.15.16-HarmonyOS")
        print()

        response = questionary.path(
            "Qt installation path:",
            default=default or "",
            style=CUSTOM_STYLE,
        ).ask()

        if response is None:
            raise KeyboardInterrupt("Installation cancelled by user")

        path = Path(response.strip())
        is_valid, message = validate_path(path, must_exist=False, create=True)
        print(f"\033[92m  ✓ {message}\033[0m")
        return path

    def collect_architecture(self, default: str = "arm64-v8a") -> str:
        """Collect target architecture with selection list"""
        self._print_header("Target Architecture")

        choices = [
            questionary.Choice(
                "arm64-v8a  (recommended for most HarmonyOS devices)",
                value="arm64-v8a"
            ),
            questionary.Choice(
                "x86_64     (for emulator or x86 devices)",
                value="x86_64"
            ),
        ]

        response = questionary.select(
            "Select target architecture:",
            choices=choices,
            default=default,
            style=CUSTOM_STYLE,
        ).ask()

        if response is None:
            raise KeyboardInterrupt("Installation cancelled by user")

        print(f"\033[92m  ✓ Selected: {response}\033[0m")
        return response

    def collect_build_type(self, default: str = "release") -> str:
        """Collect build type with selection list"""
        self._print_header("Build Type")

        choices = [
            questionary.Choice(
                "release                 (optimized, recommended for production)",
                value="release"
            ),
            questionary.Choice(
                "debug                   (with debug symbols, for development)",
                value="debug"
            ),
            questionary.Choice(
                "release-with-debug-info (optimized but with debug info)",
                value="release-with-debug-info"
            ),
        ]

        response = questionary.select(
            "Select build type:",
            choices=choices,
            default=default,
            style=CUSTOM_STYLE,
        ).ask()

        if response is None:
            raise KeyboardInterrupt("Installation cancelled by user")

        print(f"\033[92m  ✓ Selected: {response}\033[0m")
        return response

    def collect_parallel_jobs(self, default: int = 8) -> int:
        """Collect number of parallel jobs"""
        self._print_header("Parallel Build Jobs")

        print("Tip: Set to your CPU core count for optimal performance")
        print()

        while True:
            response = questionary.text(
                "Number of parallel jobs:",
                default=str(default),
                style=CUSTOM_STYLE,
            ).ask()

            if response is None:
                raise KeyboardInterrupt("Installation cancelled by user")

            try:
                jobs = int(response.strip())
                if jobs > 0:
                    print(f"\033[92m  ✓ Using {jobs} parallel jobs\033[0m")
                    return jobs
                else:
                    print("\033[91m  ✗ Must be a positive number\033[0m")
            except ValueError:
                print("\033[91m  ✗ Please enter a valid number\033[0m")

    def collect_tool_paths(
        self,
        current_make: Optional[Path] = None,
        current_perl: Optional[Path] = None
    ) -> Tuple[Optional[Path], Optional[Path]]:
        """Collect tool paths with selection and input"""
        self._print_header("Build Tools Configuration")

        print("MinGW (mingw32-make) and Perl are required for building Qt.")
        print("The make path should contain gcc/g++ compilers.")
        print()

        make_path = current_make
        perl_path = current_perl

        # MinGW configuration
        if current_make:
            print(f"Current MinGW: {current_make}")

        config_mingw = questionary.confirm(
            "Configure MinGW path?",
            default=current_make is None,
            style=CUSTOM_STYLE,
        ).ask()

        if config_mingw is None:
            raise KeyboardInterrupt("Installation cancelled by user")

        if config_mingw:
            make_path = self._collect_tool_path(
                "MinGW (mingw32-make)",
                current_make
            )

        # Perl configuration
        print()
        if current_perl:
            print(f"Current Perl: {current_perl}")

        config_perl = questionary.confirm(
            "Configure Perl path?",
            default=current_perl is None,
            style=CUSTOM_STYLE,
        ).ask()

        if config_perl is None:
            raise KeyboardInterrupt("Installation cancelled by user")

        if config_perl:
            perl_path = self._collect_tool_path(
                "Perl",
                current_perl
            )

        return make_path, perl_path

    def _collect_tool_path(
        self,
        tool_name: str,
        default: Optional[Path] = None
    ) -> Optional[Path]:
        """Collect a tool path with interactive input"""
        response = questionary.path(
            f"{tool_name} path (or press Enter to skip):",
            default=str(default) if default else "",
            style=CUSTOM_STYLE,
        ).ask()

        if response is None:
            return default

        if not response.strip():
            return default

        path = Path(response.strip())
        if path.exists():
            print(f"\033[92m  ✓ {tool_name} path set: {path}\033[0m")
            return path
        else:
            print(f"\033[91m  ✗ Path not found: {path}\033[0m")
            return default

    def confirm_configuration(self, config: InstallConfig) -> bool:
        """
        Display configuration and ask for confirmation with selection list.
        Returns True if user confirms, False if user cancels.
        """
        while True:
            self._show_config_summary(config)

            # Show version-specific notes
            version_config = get_qt_version_config(config.qt_version)
            if version_config.get("notes"):
                print(f"\n\033[93m  Note: {version_config['notes']}\033[0m")

            print()
            choices = [
                questionary.Choice("✓ Proceed with installation", value="proceed"),
                questionary.Choice("✎ Modify configuration", value="modify"),
                questionary.Choice("✗ Cancel installation", value="cancel"),
            ]

            response = questionary.select(
                "What would you like to do?",
                choices=choices,
                style=CUSTOM_STYLE,
            ).ask()

            if response is None or response == "cancel":
                return False
            elif response == "proceed":
                return True
            elif response == "modify":
                if not self._modify_config_menu(config):
                    return False

    def _show_config_summary(self, config: InstallConfig) -> None:
        """Display configuration summary"""
        print()
        print("\033[96m" + "═" * 50 + "\033[0m")
        print("\033[1;96m  Configuration Summary\033[0m")
        print("\033[96m" + "═" * 50 + "\033[0m")
        print()

        items = [
            ("Qt Source Path", str(config.qt_source_path)),
            ("HarmonyOS SDK Path", str(config.harmony_sdk_path)),
            ("Install Path", str(config.install_path)),
            ("Architecture", config.architecture),
            ("Qt Version", f"{config.qt_version} ({config.version_source})"),
            ("Build Type", config.build_type),
            ("Parallel Jobs", str(config.parallel_jobs)),
        ]

        if config.make_path:
            items.append(("Make Path", str(config.make_path)))
        if config.perl_path:
            items.append(("Perl Path", str(config.perl_path)))

        max_label_len = max(len(label) for label, _ in items)
        for label, value in items:
            print(f"  \033[96m{label:<{max_label_len}}\033[0m  {value}")

    def _modify_config_menu(self, config: InstallConfig) -> bool:
        """
        Show menu to modify specific configuration options.
        Returns True to continue, False to cancel.
        """
        while True:
            print()
            print("\033[96m" + "─" * 50 + "\033[0m")
            print("\033[1;96m  Modify Configuration\033[0m")
            print("\033[96m" + "─" * 50 + "\033[0m")
            print()

            choices = [
                questionary.Choice(f"Qt Source Path:      {config.qt_source_path}", value="1"),
                questionary.Choice(f"HarmonyOS SDK Path:  {config.harmony_sdk_path}", value="2"),
                questionary.Choice(f"Installation Path:   {config.install_path}", value="3"),
                questionary.Choice(f"Architecture:        {config.architecture}", value="4"),
                questionary.Choice(f"Qt Version:          {config.qt_version} ({config.version_source})", value="5"),
                questionary.Choice(f"Build Type:          {config.build_type}", value="6"),
                questionary.Choice(f"Parallel Jobs:       {config.parallel_jobs}", value="7"),
                questionary.Choice(f"Tool Paths (MinGW/Perl)", value="8"),
                questionary.Choice("─" * 40, value="separator", disabled=True),
                questionary.Choice("✓ Done - Return to confirmation", value="done"),
                questionary.Choice("✗ Cancel installation", value="cancel"),
            ]

            response = questionary.select(
                "Select option to modify:",
                choices=choices,
                style=CUSTOM_STYLE,
            ).ask()

            if response is None or response == "cancel":
                return False
            elif response == "done":
                return True
            elif response == "separator":
                continue
            elif response == "1":
                config.qt_source_path = self.collect_qt_source_path(
                    default=str(config.qt_source_path)
                )
                # Re-detect version
                qt_version, version_source = detect_qt_version(config.qt_source_path)
                config.qt_version = qt_version
                config.version_source = version_source
            elif response == "2":
                config.harmony_sdk_path = self.collect_harmony_sdk_path(
                    default=str(config.harmony_sdk_path)
                )
            elif response == "3":
                config.install_path = self.collect_install_path(
                    default=str(config.install_path)
                )
            elif response == "4":
                config.architecture = self.collect_architecture(
                    default=config.architecture
                )
            elif response == "5":
                config.qt_version, config.version_source = self.collect_qt_version(
                    detected_version=config.qt_version,
                    detected_source=config.version_source
                )
            elif response == "6":
                config.build_type = self.collect_build_type(
                    default=config.build_type
                )
            elif response == "7":
                config.parallel_jobs = self.collect_parallel_jobs(
                    default=config.parallel_jobs
                )
            elif response == "8":
                config.make_path, config.perl_path = self.collect_tool_paths(
                    current_make=config.make_path,
                    current_perl=config.perl_path
                )

    def show_welcome(self) -> None:
        """Show welcome message"""
        print()
        print("\033[96m" + "═" * 60 + "\033[0m")
        print("\033[1;96m" + "  Qt for HarmonyOS Installation Tool".center(60) + "\033[0m")
        print("\033[96m" + "═" * 60 + "\033[0m")
        print()
        print("This tool will help you install Qt for HarmonyOS by:")
        print("  1. Collecting necessary paths and configurations")
        print("  2. Downloading required tools (make, perl)")
        print("  3. Configuring build environment")
        print("  4. Compiling and installing Qt")
        print()
        print("\033[93mPrerequisites:\033[0m")
        print("  • Python >= 3.12")
        print("  • Git >= 2.39.3")
        print("  • HarmonyOS SDK (API >= 15, recommended API 17)")
        print("  • Qt source code (tqtc-qt5)")
        print()
        print("\033[92mOfficial Guide:\033[0m https://wiki.qt.io/Building_Qt_for_HarmonyOS")
        print()

    def collect_qt_version(self, detected_version: str, detected_source: str) -> Tuple[str, str]:
        """Collect Qt version with selection list"""
        self._print_header("Qt Version")

        # Get version-specific notes
        version_config = get_qt_version_config(detected_version)
        if version_config.get("notes"):
            print(f"\033[93m  Note: {version_config['notes']}\033[0m")
        print()

        # Build choices with detected version first
        choices = [
            questionary.Choice(
                f"{detected_version} (detected from {detected_source})",
                value=detected_version
            ),
        ]

        # Add other available versions
        available_versions = [
            ("5.15.16", "recommended LTS"),
            ("5.12.12", "LTS"),
        ]
        for ver, note in available_versions:
            if ver != detected_version:
                choices.append(questionary.Choice(
                    f"{ver} ({note})",
                    value=ver
                ))

        # Add custom version option
        choices.append(questionary.Choice(
            "Custom version...",
            value="custom"
        ))

        response = questionary.select(
            "Select Qt version:",
            choices=choices,
            style=CUSTOM_STYLE,
        ).ask()

        if response is None:
            raise KeyboardInterrupt("Installation cancelled by user")

        if response == "custom":
            custom_version = questionary.text(
                "Enter Qt version:",
                default=detected_version,
                style=CUSTOM_STYLE,
            ).ask()
            if custom_version is None:
                raise KeyboardInterrupt("Installation cancelled by user")
            print(f"\033[92m  ✓ Selected: {custom_version} (manual input)\033[0m")
            return custom_version, "manual input"

        if response == detected_version:
            print(f"\033[92m  ✓ Selected: {response} (auto-detected)\033[0m")
            return response, detected_source
        else:
            print(f"\033[92m  ✓ Selected: {response}\033[0m")
            return response, "manual selection"

    def collect_all(self) -> InstallConfig:
        """Collect all configuration from user with modern UI"""
        self.show_welcome()

        # Collect paths
        qt_source_path = self.collect_qt_source_path()
        harmony_sdk_path = self.collect_harmony_sdk_path()
        install_path = self.collect_install_path()

        # Auto-detect Qt version
        print()
        print("\033[96mDetecting Qt version...\033[0m")
        detected_version, detected_source = detect_qt_version(qt_source_path)
        print(f"\033[92m  ✓ Detected: {detected_version} (from {detected_source})\033[0m")

        # Collect Qt version (with selection list)
        qt_version, version_source = self.collect_qt_version(detected_version, detected_source)

        # Collect build options
        architecture = self.collect_architecture()
        build_type = self.collect_build_type()
        parallel_jobs = self.collect_parallel_jobs()

        # Collect tool paths
        make_path, perl_path = self.collect_tool_paths()

        # Create configuration
        config = InstallConfig(
            qt_source_path=qt_source_path,
            harmony_sdk_path=harmony_sdk_path,
            install_path=install_path,
            architecture=architecture,
            qt_version=qt_version,
            build_type=build_type,
            parallel_jobs=parallel_jobs,
            make_path=make_path,
            perl_path=perl_path,
            version_source=version_source
        )

        # Confirm configuration (allows modification via menu)
        if self.confirm_configuration(config):
            return config
        else:
            raise KeyboardInterrupt("Installation cancelled by user")

    def _collect_qt_version(self) -> str:
        """Collect Qt version manually with selection list"""
        self._print_header("Qt Version Selection")

        choices = [
            questionary.Choice("5.15.16 (recommended)", value="5.15.16"),
            questionary.Choice("5.12.12 (LTS)", value="5.12.12"),
            questionary.Choice("Custom version...", value="custom"),
        ]

        response = questionary.select(
            "Select Qt version:",
            choices=choices,
            style=CUSTOM_STYLE,
        ).ask()

        if response is None:
            raise KeyboardInterrupt("Installation cancelled by user")

        if response == "custom":
            response = questionary.text(
                "Enter Qt version:",
                default="5.15.16",
                style=CUSTOM_STYLE,
            ).ask()
            if response is None:
                raise KeyboardInterrupt("Installation cancelled by user")

        return response