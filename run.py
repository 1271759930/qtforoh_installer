#!/usr/bin/env python3
"""
Qt for HarmonyOS Installer - 一键启动脚本

用法:
    python run.py              # 进入主菜单
    python run.py install      # 直接运行安装
    python run.py check        # 检查前置条件
    python run.py config       # 查看配置
    python run.py guide        # 显示安装指南
    python run.py clean        # 清理构建产物
    python run.py --help       # 显示帮助

此脚本会自动:
    1. 检查 Python 版本 (需要 >= 3.10)
    2. 检查并安装缺失的依赖
    3. 进入交互式菜单或执行指定命令
"""

import sys
import subprocess
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == "win32":
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")


def check_python_version():
    """检查 Python 版本是否 >= 3.10"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("=" * 50)
        print("错误: Python 版本过低")
        print(f"当前版本: Python {version.major}.{version.minor}.{version.micro}")
        print("需要版本: Python >= 3.10")
        print("=" * 50)
        print()
        print("请从以下地址下载并安装 Python 3.10 或更高版本:")
        print("  https://python.org/downloads/")
        sys.exit(1)

    print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")


def ensure_dependencies():
    """确保依赖已安装，缺失则自动安装"""
    required_packages = [
        ("click", "click>=8.1.0"),
        ("questionary", "questionary>=2.0.0"),
        ("rich", "rich>=13.0.0"),
        ("requests", "requests>=2.31.0"),
        ("tqdm", "tqdm>=4.66.0"),
        ("yaml", "pyyaml>=6.0"),  # yaml module name differs from package name
        ("colorama", "colorama>=0.4.6"),
    ]

    missing = []
    for module_name, package_spec in required_packages:
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_spec)

    if missing:
        print()
        print("=" * 50)
        print("检测到缺失依赖，正在自动安装...")
        print("=" * 50)
        print(f"缺失: {', '.join(missing)}")
        print()

        # 使用 pip 安装 requirements.txt
        project_root = Path(__file__).parent
        requirements_file = project_root / "requirements.txt"

        if requirements_file.exists():
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
            if not _is_verbose():
                cmd.append("-q")  # 安静模式

            result = subprocess.run(cmd)
            if result.returncode != 0:
                print()
                print("[错误] 依赖安装失败，请手动执行:")
                print(f"  {sys.executable} -m pip install -r requirements.txt")
                sys.exit(1)
        else:
            # 直接安装缺失的包
            cmd = [sys.executable, "-m", "pip", "install"] + missing
            if not _is_verbose():
                cmd.append("-q")

            result = subprocess.run(cmd)
            if result.returncode != 0:
                print()
                print("[错误] 依赖安装失败，请手动执行:")
                print(f"  {sys.executable} -m pip install { ' '.join(missing)}")
                sys.exit(1)

        print("[OK] 依赖已安装")


def _is_verbose():
    """检查是否开启详细模式"""
    return "--verbose" in sys.argv or "-v" in sys.argv


def check_git():
    """检查 Git 是否安装（可选，但建议安装）"""
    import shutil
    if shutil.which("git"):
        print("[OK] Git 已安装")
    else:
        print("[WARN] Git 未安装 (克隆 Qt 源码需要 Git)")
        print("       下载地址: https://git-scm.com/downloads")


def main():
    """主入口"""
    # Step 1: 检查 Python 版本
    check_python_version()

    # Step 2: 检查 Git
    check_git()

    # Step 3: 确保依赖已安装
    ensure_dependencies()

    # Step 4: 运行
    # 如果有命令行参数，直接执行 CLI 命令
    # 否则进入交互式菜单
    args = [a for a in sys.argv[1:] if not a.startswith('-')]

    if args:
        # 有子命令参数，直接调用 CLI
        from src.cli import cli
        cli()
    else:
        # 无参数，进入交互式菜单
        print()
        print("=" * 50)
        print("Qt for HarmonyOS 交叉编译工具")
        print("=" * 50)
        print()

        from src.ui.menu import run_menu_loop
        run_menu_loop()


if __name__ == "__main__":
    main()