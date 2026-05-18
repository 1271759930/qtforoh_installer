"""
Interactive prompts - Modern CLI UI with selection lists and input boxes
"""

from pathlib import Path
from typing import Optional, Tuple, List
import questionary
from questionary import Style

from ..config.schema import InstallConfig
from ..config.defaults import (
    get_qt_version_config,
    get_module_description,
    get_module_status,
    is_module_essential,
    get_available_modules,
    get_default_skip_modules,
)
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

    def show_license_agreement(self) -> bool:
        """
        Show Qt open source license agreement page.
        显示 Qt 开源协议同意页面。

        Returns:
            True if user agrees and continues, False if user cancels
        """
        print()
        print("\033[96m" + "═" * 60 + "\033[0m")
        print("\033[1;96m" + "  Qt 开源协议 / Qt Open Source License".center(60) + "\033[0m")
        print("\033[96m" + "═" * 60 + "\033[0m")
        print()

        print("Qt 使用 GNU Lesser General Public License (LGPL) 开源协议。")
        print()
        print("使用本工具构建 Qt 即表示您同意遵守 LGPL 协议条款。")
        print("主要条款包括：")
        print("  • 可以自由使用、修改和分发 Qt")
        print("  • 如果修改 Qt 本身，需要开源您的修改")
        print("  • 使用 Qt 开发的应用程序可以保持闭源")
        print("  • 需要提供 Qt 的源代码或获取方式")
        print()
        print("完整协议文本请参阅：")
        print("  \033[92mhttps://www.gnu.org/licenses/lgpl-3.0.html\033[0m")
        print()
        print("\033[90m" + "-" * 60 + "\033[0m")
        print()
        print("Qt is licensed under the GNU Lesser General Public License (LGPL).")
        print()
        print("By using this tool to build Qt, you agree to comply with the LGPL terms.")
        print("Key provisions include:")
        print("  • Freedom to use, modify, and distribute Qt")
        print("  • Modifications to Qt itself must be open-sourced")
        print("  • Applications using Qt may remain proprietary")
        print("  • Qt source code or access method must be provided")
        print()
        print("For full license text, see:")
        print("  \033[92mhttps://www.gnu.org/licenses/lgpl-3.0.html\033[0m")
        print()

        # Select for agreement
        choices = [
            questionary.Choice(
                "✓ 我同意开源协议并继续 / I agree to the open source license and continue",
                value="agree"
            ),
            questionary.Choice(
                "✗ 我不同意，退出安装 / I disagree and exit installation",
                value="disagree"
            ),
        ]

        response = questionary.select(
            "请选择 / Please select:",
            choices=choices,
            style=CUSTOM_STYLE,
        ).ask()

        if response is None or response == "disagree":
            print()
            print("\033[93m  安装已取消 / Installation cancelled\033[0m")
            return False

        # User agreed
        print()
        print("\033[92m  ✓ 您已同意 Qt 开源协议 / You have agreed to the Qt open source license\033[0m")
        return True

    def collect_qt_source_path(self, default: Optional[str] = None) -> Path:
        """Collect Qt source path with interactive input / 收集Qt源码路径"""
        self._print_header("Qt源码路径 / Qt Source Code Path")

        print("请指定Qt源码路径 (tqtc-qt5)。")
        print("该路径应包含用于HarmonyOS的Qt源文件。")
        print()
        print("Please specify the path to Qt source code (tqtc-qt5).")
        print("This should contain the Qt source files for HarmonyOS.")
        print()

        while True:
            response = questionary.path(
                "Qt源码路径 / Qt source code path:",
                default=default or "",
                style=CUSTOM_STYLE,
                validate=lambda x: len(x.strip()) > 0 or "路径不能为空 / Path cannot be empty"
            ).ask()

            if response is None:
                raise KeyboardInterrupt("用户取消安装 / Installation cancelled by user")

            path = Path(response.strip())
            is_valid, message = validate_path(path, must_exist=True, create=False)

            if is_valid:
                # Validate Qt source
                if not (path / "qtbase").exists():
                    print(f"\033[93m  警告: Qt源码目录中未找到 'qtbase' / Warning: 'qtbase' not found\033[0m")
                print(f"\033[92m  ✓ {message}\033[0m")
                return path
            else:
                print(f"\033[91m  ✗ {message}\033[0m")
                print()

    def collect_harmony_sdk_path(self, default: Optional[str] = None) -> Path:
        """Collect HarmonyOS SDK path with interactive input / 收集HarmonyOS SDK路径"""
        self._print_header("HarmonyOS SDK路径 / HarmonyOS SDK Path")

        print("请指定HarmonyOS SDK路径。")
        print("该路径应包含带有LLVM工具链的 'native' 目录。")
        print("示例: C:\\Users\\<user>\\Library\\OpenHarmony\\Sdk\\12")
        print()
        print("Please specify the path to HarmonyOS SDK.")
        print("This should contain the 'native' directory with LLVM toolchain.")
        print("Example: C:\\Users\\<user>\\Library\\OpenHarmony\\Sdk\\12")
        print()

        while True:
            response = questionary.path(
                "HarmonyOS SDK路径 / HarmonyOS SDK path:",
                default=default or "",
                style=CUSTOM_STYLE,
            ).ask()

            if response is None:
                raise KeyboardInterrupt("用户取消安装 / Installation cancelled by user")

            path = Path(response.strip())
            is_valid, message = validate_path(path, must_exist=True, create=False)

            if is_valid:
                # Validate SDK structure
                native_path = path / "native"
                if not native_path.exists():
                    print(f"\033[91m  ✗ SDK路径中未找到 'native' 目录 / 'native' directory not found\033[0m")
                    continue
                print(f"\033[92m  ✓ {message}\033[0m")
                return path
            else:
                print(f"\033[91m  ✗ {message}\033[0m")
                print()

    def collect_install_path(self, default: Optional[str] = None) -> Path:
        """Collect Qt installation path with interactive input / 收集Qt安装路径"""
        self._print_header("Qt安装路径 / Qt Installation Path")

        print("请指定Qt for HarmonyOS的安装基础路径。")
        print("实际安装目录将在此路径下自动创建，格式为: Qt{版本}-{架构}")
        print("示例: 输入 C:\\Qt，将安装到 C:\\Qt\\Qt5.15.16-arm64-v8a")
        print()
        print("Please specify the base installation path for Qt for HarmonyOS.")
        print("The actual installation directory will be created automatically under this path as: Qt{version}-{arch}")
        print("Example: Enter C:\\Qt, will install to C:\\Qt\\Qt5.15.16-arm64-v8a")
        print()

        response = questionary.path(
            "Qt安装路径 / Qt installation path:",
            default=default or "",
            style=CUSTOM_STYLE,
        ).ask()

        if response is None:
            raise KeyboardInterrupt("用户取消安装 / Installation cancelled by user")

        path = Path(response.strip())
        is_valid, message = validate_path(path, must_exist=False, create=True)
        print(f"\033[92m  ✓ {message}\033[0m")
        return path

    def collect_architecture(self, default: str = "arm64-v8a") -> str:
        """Collect target architecture with selection list / 收集目标架构"""
        self._print_header("目标架构 / Target Architecture")

        choices = [
            questionary.Choice(
                "arm64-v8a  (推荐用于大多数HarmonyOS设备 / recommended for most HarmonyOS devices)",
                value="arm64-v8a"
            ),
            questionary.Choice(
                "x86_64     (用于模拟器或x86设备 / for emulator or x86 devices)",
                value="x86_64"
            ),
        ]

        response = questionary.select(
            "选择目标架构 / Select target architecture:",
            choices=choices,
            default=default,
            style=CUSTOM_STYLE,
        ).ask()

        if response is None:
            raise KeyboardInterrupt("用户取消安装 / Installation cancelled by user")

        print(f"\033[92m  ✓ 已选择 / Selected: {response}\033[0m")
        return response

    def collect_build_type(self, default: str = "release") -> str:
        """Collect build type with selection list / 收集构建类型"""
        self._print_header("构建类型 / Build Type")

        choices = [
            questionary.Choice(
                "release                 (优化版本，推荐用于生产环境 / optimized, recommended for production)",
                value="release"
            ),
            questionary.Choice(
                "debug                   (调试版本，包含调试符号 / with debug symbols, for development)",
                value="debug"
            ),
            questionary.Choice(
                "release-with-debug-info (优化版本但包含调试信息 / optimized but with debug info)",
                value="release-with-debug-info"
            ),
        ]

        response = questionary.select(
            "选择构建类型 / Select build type:",
            choices=choices,
            default=default,
            style=CUSTOM_STYLE,
        ).ask()

        if response is None:
            raise KeyboardInterrupt("用户取消安装 / Installation cancelled by user")

        print(f"\033[92m  ✓ 已选择 / Selected: {response}\033[0m")
        return response

    def collect_force_opengl_es(self, default: bool = False) -> bool:
        """Collect Force OpenGL ES option / 收集强制OpenGL ES选项
        
        When enabled, configure will use -opengl es2 -opengles3 flags.
        This ensures OpenGL ES is used instead of Desktop OpenGL.
        """
        self._print_header("OpenGL 配置 / OpenGL Configuration")

        print("Qt for HarmonyOS 支持 Desktop OpenGL 和 OpenGL ES。")
        print("默认情况下，Qt 会自动检测使用哪种 OpenGL。")
        print()
        print("强制使用 OpenGL ES (-opengl es2 -opengles3) 可确保兼容性，")
        print("特别是在某些设备或SDK版本不支持 Desktop OpenGL 时。")
        print()
        print("Qt for HarmonyOS supports both Desktop OpenGL and OpenGL ES.")
        print("By default, Qt auto-detects which OpenGL to use.")
        print()
        print("Force OpenGL ES (-opengl es2 -opengles3) ensures compatibility,")
        print("especially when some devices or SDK versions don't support Desktop OpenGL.")
        print()
        print("\033[93m参考文档 / Reference:\033[0m https://wiki.qt.io/Building_Qt_for_HarmonyOS")
        print()

        response = questionary.confirm(
            "强制使用 OpenGL ES? (不勾选则自动检测) / Force OpenGL ES? (Leave unchecked for auto-detect)",
            default=default,
            style=CUSTOM_STYLE,
        ).ask()

        if response is None:
            raise KeyboardInterrupt("用户取消安装 / Installation cancelled by user")

        if response:
            print(f"\033[92m  ✓ 已启用强制 OpenGL ES / Force OpenGL ES enabled\033[0m")
            print(f"\033[92m  ✓ 将使用配置参数: -opengl es2 -opengles3\033[0m")
        else:
            print(f"\033[92m  ✓ 将使用自动检测 OpenGL / Auto-detect OpenGL\033[0m")

        return response

    def collect_parallel_jobs(self, default: int = 8) -> int:
        """Collect number of parallel jobs / 收集并行任务数"""
        self._print_header("并行构建任务数 / Parallel Build Jobs")

        print("提示: 设置为CPU核心数可获得最佳性能 / Tip: Set to your CPU core count for optimal performance")
        print()

        while True:
            response = questionary.text(
                "并行任务数 / Number of parallel jobs:",
                default=str(default),
                style=CUSTOM_STYLE,
            ).ask()

            if response is None:
                raise KeyboardInterrupt("用户取消安装 / Installation cancelled by user")

            try:
                jobs = int(response.strip())
                if jobs > 0:
                    print(f"\033[92m  ✓ 使用 / Using {jobs} 并行任务 / parallel jobs\033[0m")
                    return jobs
                else:
                    print("\033[91m  ✗ 必须为正数 / Must be a positive number\033[0m")
            except ValueError:
                print("\033[91m  ✗ 请输入有效数字 / Please enter a valid number\033[0m")

    def collect_skip_modules(
        self,
        current_skip_modules: List[str],
        qt_version: str = "5.15.16",
        qt_source_path: Optional[Path] = None
    ) -> List[str]:
        """Collect skip modules with checkbox selection / 收集跳过模块配置.

        Args:
            current_skip_modules: Currently selected modules to skip
            qt_version: Qt version to determine available modules
            qt_source_path: Qt source path to filter existing modules

        Returns:
            List of modules to skip
        """
        self._print_header("跳过模块配置 / Skip Modules Configuration")

        print("选择构建时要跳过的Qt模块。")
        print("使用空格键切换选择，回车键确认。")
        print()
        print("Select Qt modules to skip during build.")
        print("Use SPACE to toggle selection, ENTER to confirm.")
        print()
        print("\033[93m注意事项 / Note:\033[0m")
        print("  • 核心模块(qtbase/qtdeclarative)不建议跳过")
        print("  • Core modules (qtbase/qtdeclarative) should not be skipped")
        print("  • 已废弃/忽略模块建议跳过")
        print("  • Deprecated/ignored modules should be skipped")
        print()

        # Get available modules for this version
        available_modules = get_available_modules(qt_version, qt_source_path)

        if not available_modules:
            print("\033[91m  ✗ 源码路径中未找到模块 / No modules found in source path\033[0m")
            return current_skip_modules

        # Sort modules: essential first, then by status
        def module_sort_key(m):
            status = get_module_status(m)
            status_order = {"essential": 0, "addon": 1, "preview": 2, "deprecated": 3, "ignore": 4}
            return (is_module_essential(m), status_order.get(status, 5), m)

        available_modules.sort(key=module_sort_key)

        # Get version-specific default skip modules from documentation
        version_default_skip = get_default_skip_modules(qt_version)

        # Build choices with descriptions and status indicators
        choices = []
        for module in available_modules:
            description = get_module_description(module)
            status = get_module_status(module)

            # Determine if module should be checked (selected to skip)
            # Priority: Essential modules -> Version-specific defaults (highest priority)
            # Version-specific defaults from wiki.qt.io are authoritative
            if is_module_essential(module):
                is_checked = False  # Core modules never skip by default
                status_indicator = "\033[92m[核心/Essential]\033[0m"
            elif module in version_default_skip:
                # Use version-specific default from documentation (wiki.qt.io)
                # This is the authoritative source for HarmonyOS builds
                is_checked = True
                status_indicator = "\033[93m[推荐跳过/Recommended]\033[0m"
            else:
                # Module NOT in version-specific skip list -> NOT checked by default
                # User can manually select if needed
                is_checked = module in current_skip_modules
                status_indicator = ""

            # Build display title
            if status_indicator:
                title = f"{module} - {description} {status_indicator}"
            else:
                title = f"{module} - {description}"

            choices.append(questionary.Choice(
                title,
                value=module,
                checked=is_checked
            ))

        response = questionary.checkbox(
            f"选择要跳过的模块 / Select modules to skip ({len(available_modules)} 可用/available):",
            choices=choices,
            style=CUSTOM_STYLE,
        ).ask()

        if response is None:
            raise KeyboardInterrupt("用户取消安装 / Installation cancelled by user")

        # Always ensure essential modules are NOT skipped (even if user selected)
        final_skip = [m for m in response if not is_module_essential(m)]

        # Show result
        essential_warn = [m for m in response if is_module_essential(m)]
        if essential_warn:
            print(f"\033[93m  ⚠ 核心模块 {essential_warn} 已自动取消跳过 / Core modules auto-unselected\033[0m")

        print(f"\033[92m  ✓ 已选择 {len(final_skip)} 个模块跳过 / Selected {len(final_skip)} modules to skip\033[0m")
        return final_skip

    def collect_python_path(
        self,
        current_python: Optional[Path] = None
    ) -> Optional[Path]:
        """Collect Python path with selection and input / 收集 Python 路径"""
        self._print_header("Python 配置 / Python Configuration")

        print("Python用于QML编译，默认使用系统Python。")
        print("Python is required for QML compilation, system Python is used by default.")
        print()

        python_path = current_python

        if current_python:
            print(f"当前Python / Current Python: {current_python}")
        else:
            print("Python将默认从系统环境变量读取 / Python will be read from system environment variables by default.")

        config_python = questionary.confirm(
            "配置自定义Python路径? (不勾选则使用系统Python) / Configure custom Python path? (Leave unchecked to use system Python)",
            default=False,
            style=CUSTOM_STYLE,
        ).ask()

        if config_python is None:
            raise KeyboardInterrupt("用户取消安装 / Installation cancelled by user")

        if config_python:
            python_path = self._collect_tool_path(
                "Python",
                current_python
            )

        return python_path

    def _collect_tool_path(
        self,
        tool_name: str,
        default: Optional[Path] = None
    ) -> Optional[Path]:
        """Collect a tool path with interactive input / 收集工具路径"""
        response = questionary.path(
            f"{tool_name}路径 (回车跳过) / {tool_name} path (or press Enter to skip):",
            default=str(default) if default else "",
            style=CUSTOM_STYLE,
        ).ask()

        if response is None:
            return default

        if not response.strip():
            return default

        path = Path(response.strip())
        if path.exists():
            print(f"\033[92m  ✓ {tool_name}路径已设置 / {tool_name} path set: {path}\033[0m")
            return path
        else:
            print(f"\033[91m  ✗ 路径未找到 / Path not found: {path}\033[0m")
            return default

    def confirm_configuration(self, config: InstallConfig) -> bool:
        """
        Display configuration and ask for confirmation with selection list.
        显示配置并请求确认。
        Returns True if user confirms, False if user cancels.
        """
        while True:
            self._show_config_summary(config)

            # Show version-specific notes
            version_config = get_qt_version_config(config.qt_version)
            if version_config.get("notes"):
                print(f"\n\033[93m  注意 / Note: {version_config['notes']}\033[0m")

            print()
            choices = [
                questionary.Choice("✓ 开始安装 / Proceed with installation", value="proceed"),
                questionary.Choice("✎ 修改配置 / Modify configuration", value="modify"),
                questionary.Choice("✗ 取消安装 / Cancel installation", value="cancel"),
            ]

            response = questionary.select(
                "请选择 / What would you like to do?",
                choices=choices,
                style=CUSTOM_STYLE,
            ).ask()

            if response is None or response == "cancel":
                return False
            elif response == "proceed":
                return self._verify_and_update_config(config)
            elif response == "modify":
                if not self._modify_config_menu(config):
                    return False

    def _verify_and_update_config(self, config: InstallConfig) -> bool:
        """
        Verify and update configuration before installation.
        检测git版本并更新配置，确保模块匹配。
        """
        print()
        print("\033[96m检测源码Git版本... / Detecting Git version from source...\033[0m")

        detected_version, detected_source = detect_qt_version(config.qt_source_path)
        print(f"\033[92m  ✓ 检测到 / Detected: {detected_version} (来自 / from {detected_source})\033[0m")

        version_changed = False
        if detected_version != config.qt_version:
            print()
            print(f"\033[93m  ⚠ 配置版本({config.qt_version})与Git版本({detected_version})不同\033[0m")
            print(f"\033[93m  Warning: Config version ({config.qt_version}) differs from Git version ({detected_version})\033[0m")

            update = questionary.confirm(
                f"是否更新版本号为 {detected_version}? / Update version to {detected_version}?",
                default=True,
                style=CUSTOM_STYLE,
            ).ask()

            if update is None:
                return False
            elif update:
                config.qt_version = detected_version
                config.version_source = detected_source
                version_changed = True
                print(f"\033[92m  ✓ 已更新Qt版本 / Qt version updated: {config.qt_version}\033[0m")

        if version_changed:
            print()
            print("\033[96m更新跳过模块列表... / Updating skip modules list...\033[0m")

            available_modules = get_available_modules(config.qt_version, config.qt_source_path)
            default_skip = get_default_skip_modules(config.qt_version)

            new_skip = [m for m in default_skip if m in available_modules]

            old_skip_count = len(config.skip_modules)
            config.skip_modules = new_skip
            print(f"\033[92m  ✓ 已更新跳过模块 / Skip modules updated: {old_skip_count} → {len(config.skip_modules)} 个\033[0m")

        return True

    def _show_config_summary(self, config: InstallConfig) -> None:
        """Display configuration summary / 显示配置摘要"""
        print()
        print("\033[96m" + "═" * 50 + "\033[0m")
        print("\033[1;96m  配置摘要 / Configuration Summary\033[0m")
        print("\033[96m" + "═" * 50 + "\033[0m")
        print()

        items = [
            ("Qt源码路径 / Qt Source Path", str(config.qt_source_path)),
            ("HarmonyOS SDK路径 / SDK Path", str(config.harmony_sdk_path)),
            ("安装基础路径 / Base Install Path", str(config.install_path)),
            ("实际安装路径 / Actual Install Path", str(config.actual_install_path)),
            ("架构 / Architecture", config.architecture),
            ("Qt版本 / Qt Version", f"{config.qt_version} ({config.version_source})"),
            ("构建类型 / Build Type", config.build_type),
            ("并行任务 / Parallel Jobs", str(config.parallel_jobs)),
            ("强制OpenGL ES / Force OpenGL ES", "是 / Yes" if config.force_opengl_es else "否 / No (自动检测 / auto-detect)"),
        ]

        if config.python_path:
            items.append(("Python路径 / Python Path", str(config.python_path)))

        # Show skip modules count
        skip_count = len(config.skip_modules)
        items.append(("跳过模块 / Skip Modules", f"{skip_count} 个模块 / modules selected"))

        max_label_len = max(len(label) for label, _ in items)
        for label, value in items:
            print(f"  \033[96m{label:<{max_label_len}}\033[0m  {value}")

    def _modify_config_menu(self, config: InstallConfig) -> bool:
        """
        Show menu to modify specific configuration options.
        显示修改配置菜单。
        Returns True to continue, False to cancel.
        """
        while True:
            print()
            print("\033[96m" + "─" * 50 + "\033[0m")
            print("\033[1;96m  修改配置 / Modify Configuration\033[0m")
            print("\033[96m" + "─" * 50 + "\033[0m")
            print()

            choices = [
                questionary.Choice(f"Qt源码路径 / Qt Source Path:      {config.qt_source_path}", value="1"),
                questionary.Choice(f"HarmonyOS SDK路径 / SDK Path:  {config.harmony_sdk_path}", value="2"),
                questionary.Choice(f"安装基础路径 / Base Install Path:   {config.install_path}", value="3"),
                questionary.Choice(f"架构 / Architecture:        {config.architecture}", value="4"),
                questionary.Choice(f"Qt版本 / Qt Version:          {config.qt_version} ({config.version_source})", value="5"),
                questionary.Choice(f"构建类型 / Build Type:          {config.build_type}", value="6"),
                questionary.Choice(f"并行任务 / Parallel Jobs:       {config.parallel_jobs}", value="7"),
                questionary.Choice(f"Python路径 / Python Path:       {config.python_path or '系统Python / System Python'}", value="8"),
                questionary.Choice(f"跳过模块 / Skip Modules:        {len(config.skip_modules)} 个模块 / modules", value="9"),
                questionary.Choice(f"强制OpenGL ES / Force OpenGL ES: {'是 / Yes' if config.force_opengl_es else '否 / No'}", value="10"),
                questionary.Choice("─" * 40, value="separator", disabled=True),
                questionary.Choice("✓ 完成 - 返回确认 / Done - Return to confirmation", value="done"),
                questionary.Choice("✗ 取消安装 / Cancel installation", value="cancel"),
            ]

            response = questionary.select(
                "选择要修改的选项 / Select option to modify:",
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
                config.python_path = self.collect_python_path(
                    current_python=config.python_path
                )
            elif response == "9":
                config.skip_modules = self.collect_skip_modules(
                    current_skip_modules=config.skip_modules,
                    qt_version=config.qt_version,
                    qt_source_path=config.qt_source_path
                )
            elif response == "10":
                config.force_opengl_es = self.collect_force_opengl_es(
                    default=config.force_opengl_es
                )

    def show_welcome(self) -> None:
        """Show welcome message / 显示欢迎信息"""
        print()
        print("\033[96m" + "═" * 60 + "\033[0m")
        print("\033[1;96m" + "  Qt for HarmonyOS 安装工具 / Installation Tool".center(60) + "\033[0m")
        print("\033[96m" + "═" * 60 + "\033[0m")
        print()
        print("本工具将帮助您安装鸿蒙版Qt:")
        print("  1. 收集必要的路径和配置")
        print("  2. 配置构建环境 (内置make和perl工具)")
        print("  3. 编译并安装Qt")
        print()
        print("This tool will help you install Qt for HarmonyOS by:")
        print("  1. Collecting necessary paths and configurations")
        print("  2. Configuring build environment (bundled make and perl)")
        print("  3. Compiling and installing Qt")
        print()
        print("\033[93m前置条件 / Prerequisites:\033[0m")
        print("  • Python >= 3.10")
        print("  • Git >= 2.39.3")
        print("  • HarmonyOS SDK (API >= 15, 推荐API 17 / recommended API 17)")
        print("  • Qt源代码 / Qt source code (tqtc-qt5)")
        print()
        print("\033[92m官方指南 / Official Guide:\033[0m https://wiki.qt.io/Building_Qt_for_HarmonyOS")
        print()

    def collect_qt_version(self, detected_version: str, detected_source: str) -> Tuple[str, str]:
        """Collect Qt version with selection list / 收集Qt版本"""
        self._print_header("Qt版本 / Qt Version")

        # Get version-specific notes
        version_config = get_qt_version_config(detected_version)
        if version_config.get("notes"):
            print(f"\033[93m  注意 / Note: {version_config['notes']}\033[0m")
        print()

        # Build choices with detected version first
        choices = [
            questionary.Choice(
                f"{detected_version} (从{detected_source}检测 / detected from {detected_source})",
                value=detected_version
            ),
        ]

        # Add other available versions
        available_versions = [
            ("5.15.16", "推荐LTS / recommended LTS"),
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
            "自定义版本... / Custom version...",
            value="custom"
        ))

        response = questionary.select(
            "选择Qt版本 / Select Qt version:",
            choices=choices,
            style=CUSTOM_STYLE,
        ).ask()

        if response is None:
            raise KeyboardInterrupt("用户取消安装 / Installation cancelled by user")

        if response == "custom":
            custom_version = questionary.text(
                "输入Qt版本 / Enter Qt version:",
                default=detected_version,
                style=CUSTOM_STYLE,
            ).ask()
            if custom_version is None:
                raise KeyboardInterrupt("用户取消安装 / Installation cancelled by user")
            print(f"\033[92m  ✓ 已选择 / Selected: {custom_version} (手动输入 / manual input)\033[0m")
            return custom_version, "manual input"

        if response == detected_version:
            print(f"\033[92m  ✓ 已选择 / Selected: {response} (自动检测 / auto-detected)\033[0m")
            return response, detected_source
        else:
            print(f"\033[92m  ✓ 已选择 / Selected: {response}\033[0m")
            return response, "manual selection"

    def collect_all(self) -> InstallConfig:
        """Collect all configuration from user with modern UI / 收集所有用户配置"""
        self.show_welcome()

        # Show license agreement
        if not self.show_license_agreement():
            raise KeyboardInterrupt("用户取消安装 / Installation cancelled by user")

        # Collect paths
        qt_source_path = self.collect_qt_source_path()
        harmony_sdk_path = self.collect_harmony_sdk_path()
        install_path = self.collect_install_path()

        # Auto-detect Qt version
        print()
        print("\033[96m检测Qt版本... / Detecting Qt version...\033[0m")
        detected_version, detected_source = detect_qt_version(qt_source_path)
        print(f"\033[92m  ✓ 检测到 / Detected: {detected_version} (来自 / from {detected_source})\033[0m")

        # Collect Qt version (with selection list)
        qt_version, version_source = self.collect_qt_version(detected_version, detected_source)

        # Collect build options
        architecture = self.collect_architecture()
        build_type = self.collect_build_type()
        parallel_jobs = self.collect_parallel_jobs()

        # Collect OpenGL ES option
        force_opengl_es = self.collect_force_opengl_es()

        # Collect Python path (optional)
        python_path = self.collect_python_path()

        # Get default skip modules for selected version
        skip_modules = get_default_skip_modules(qt_version)

        # Ask if user wants to modify skip modules before creating config
        print()
        print(f"\033[96m跳过模块配置 / Skip Modules:\033[0m")
        print(f"  默认将跳过 {len(skip_modules)} 个模块 / Default: {len(skip_modules)} modules will be skipped")

        modify_skip = questionary.confirm(
            "是否要修改跳过的模块列表? / Do you want to modify the skip modules list?",
            default=False,
            style=CUSTOM_STYLE,
        ).ask()

        if modify_skip is None:
            raise KeyboardInterrupt("用户取消安装 / Installation cancelled by user")

        if modify_skip:
            skip_modules = self.collect_skip_modules(
                current_skip_modules=skip_modules,
                qt_version=qt_version,
                qt_source_path=qt_source_path
            )

        # Create configuration
        config = InstallConfig(
            qt_source_path=qt_source_path,
            harmony_sdk_path=harmony_sdk_path,
            install_path=install_path,
            architecture=architecture,
            qt_version=qt_version,
            build_type=build_type,
            parallel_jobs=parallel_jobs,
            skip_modules=skip_modules,
            python_path=python_path,
            version_source=version_source,
            force_opengl_es=force_opengl_es,
        )

        # Confirm configuration (allows modification via menu)
        if self.confirm_configuration(config):
            return config
        else:
            raise KeyboardInterrupt("用户取消安装 / Installation cancelled by user")

    def _collect_qt_version(self) -> str:
        """Collect Qt version manually with selection list / 手动收集Qt版本"""
        self._print_header("Qt版本选择 / Qt Version Selection")

        choices = [
            questionary.Choice("5.15.16 (推荐 / recommended)", value="5.15.16"),
            questionary.Choice("5.12.12 (LTS)", value="5.12.12"),
            questionary.Choice("自定义版本... / Custom version...", value="custom"),
        ]

        response = questionary.select(
            "选择Qt版本 / Select Qt version:",
            choices=choices,
            style=CUSTOM_STYLE,
        ).ask()

        if response is None:
            raise KeyboardInterrupt("用户取消安装 / Installation cancelled by user")

        if response == "custom":
            response = questionary.text(
                "输入Qt版本 / Enter Qt version:",
                default="5.15.16",
                style=CUSTOM_STYLE,
            ).ask()
            if response is None:
                raise KeyboardInterrupt("用户取消安装 / Installation cancelled by user")

        return response