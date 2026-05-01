# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Qt for HarmonyOS Installation CLI Tool - 自动化编译和安装鸿蒙版本 Qt 框架的命令行工具。

**关键前置条件**：
- Python >= 3.12 (硬性要求，代码中强制检查)
- Git >= 2.39.3
- HarmonyOS SDK (API >= 15，推荐 API 17)
- Qt 源代码 (tqtc-qt5，分支 `tqtc/harmonyos-5.15.16`)

## Entry Points

```bash
# Wrapper script (推荐) - 自动检查 Python 版本、安装依赖
python run.py              # 交互式菜单
python run.py install      # 直接安装
python run.py check        # 检查前置条件

# 模块方式运行 (需预先安装依赖)
python -m src.cli install

# 安装后命令行入口
pip install -e .
qtohos-installer install   # 已注册 CLI 命令
```

## Bundled Tools

工具打包在 `tools/` 目录，无需用户手动安装 make/perl：

```
tools/
├── llvm-mingw/bin/   # mingw32-make.exe, gcc.exe, g++.exe
├── perl/bin/         # perl.exe (Strawberry Perl portable)
└── archives/         # 工具压缩包 (~200MB)
```

**首次使用前下载工具**：
```bash
python scripts/download_tools.py
```

工具自动检测，无需在 `config.yaml` 配置路径。只有 Python 路径可配置（用于 QML 编译）。

## Common Commands

### 运行工具
```bash
python run.py install    # 交互式安装
python run.py check      # 检查前置条件
python run.py config     # 查看配置
python run.py guide      # 显示安装指南
python run.py clean      # 清理构建产物 (workspace/temp/)
```

### 开发环境
```bash
pip install -r requirements.txt    # 运行时依赖
pip install -e ".[dev]"            # 开发依赖 (pytest, black, flake8, mypy)
```

### 代码检查
```bash
black src/       # 格式化 (line-length 100)
flake8 src/      # Lint
mypy src/        # 类型检查
```

### 测试
```bash
# 测试是独立脚本，不使用 pytest 框架
python tests/test_ui.py
python tests/test_download.py
python tests/test_bundled_tools.py
```

## Architecture

```
src/
├── cli.py              # CLI 入口 (Click 命令)
├── core/
│   ├── installer.py    # 流程编排器
│   ├── steps.py        # 安装步骤定义 (可扩展)
│   └── executor.py     # 步骤执行器
├── config/
│   ├── schema.py       # 配置数据类
│   ├── loader.py       # 配置加载/保存
│   └ defaults.py       # 版本特定默认配置、跳过模块列表
├── ui/
│   ├── display.py      # 输出展示 (Rich Console)
│   ├── prompts.py      # 交互式输入
│   └ menu.py           # 主菜单循环
├── builder/
│   ├── qt_builder.py   # Qt 编译执行
│   ├── env_setup.py    # 环境变量设置
│   └ script_gen.py     # Windows 批处理脚本生成
├── tools/
│   └ downloader.py     # 工具下载
└ utils.py              # 工具函数
```

**扩展安装流程**：修改 `core/steps.py` 的 `DEFAULT_STEPS` 列表，或使用 `create_custom_steps(skip_steps=...)`。

## Key Build Details

### Windows 构建特殊性

使用生成的批处理脚本 `build_qt_ohos.bat` 而非直接 subprocess：
- 重置 PATH 避免 MSVC `cl.exe` 污染编译环境
- 确保 MinGW `gcc/g++` 被正确检测用于 host tools
- 避免 Python subprocess 环境变量继承问题

**禁止在 configure 前设置 QMAKESPEC** (`script_gen.py` 会显式 unset)。

### Configure 关键参数

`builder/qt_builder.py` 生成的 configure 命令：
- `-platform win32-g++`: MinGW 构建宿主工具
- `-xplatform ohos-clang`: 交叉编译到 HarmonyOS
- `-device-option OHOS_ARCH=<arch>`: 目标架构
- `-prefix` + `-extprefix`: 设备前缀和实际安装路径

### 环境变量

`builder/env_setup.py` 设置核心环境变量：
- `NATIVE_OHOS_SDK`, `OHOS_SDK_SYSROOT`, `LLVM_INSTALL_DIR`
- `OHOS_TARGET_ARCH`
- `MINGW_ROOT`, `PERL_ROOT` (bundled tools 路径)
- PATH 更新包含 llvm-mingw 和 perl

## Configuration

用户配置保存在 `config.yaml`，示例在 `config.example.yaml`。

## Skip Modules

默认跳过的 Qt 模块在 `config/defaults.py` 定义，按版本区分 (5.12 vs 5.15)。核心模块 `qtbase`, `qtdeclarative` 不应跳过。

## Logs

日志保存在 `logs/` 目录，格式 `install_<timestamp>.log`。

## Build Directory

构建临时文件在 `workspace/temp/`，`clean` 命令清理此目录。

## Reference

- 官方文档: https://wiki.qt.io/Building_Qt_for_HarmonyOS
- Qt 源码: https://codereview.qt-project.org/qt/tqtc-qt5