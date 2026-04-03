# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Qt for HarmonyOS Installation CLI Tool - 自动化编译和安装鸿蒙版本 Qt 框架的命令行工具。

**关键前置条件**：
- Python >= 3.12
- Git >= 2.39.3
- HarmonyOS SDK (API >= 15，推荐 API 17)
- Qt 源代码 (tqtc-qt5，分支 `tqtc/harmonyos-5.15.16`)

## Common Commands

### 运行工具
```bash
# 推荐：使用 Python 模块方式运行
python -m src.cli install    # 交互式安装
python -m src.cli check      # 检查前置条件
python -m src.cli config     # 查看配置
python -m src.cli guide      # 显示安装指南
python -m src.cli clean      # 清理构建产物

# 非交互模式（使用现有配置）
python -m src.cli install --yes

# 快速启动脚本
python quick_start.py install
```

### 开发环境设置
```bash
python -m pip install -r requirements.txt    # 安装依赖
python -m pip install -e .                   # 开发模式安装
```

### 代码格式化与检查
```bash
black src/       # 格式化
flake8 src/      # 代码检查
pytest tests/    # 运行测试（如有）
```

### 独立批处理脚本
```bash
configure-qt.bat   # Windows 交互式菜单构建脚本（可独立使用）
```

## Architecture

模块化架构，安装流程由 `installer.py` 协调各模块完成：

| 模块 | 职责 |
|------|------|
| `cli.py` | CLI 入口，Click 命令定义 (`install`, `check`, `config`, `guide`, `clean`) |
| `installer.py` | 流程控制器，按步骤协调：初始化 → 前置检查 → 配置收集 → 工具设置 → 环境设置 → 编译 |
| `interactive.py` | 用户交互输入收集（路径、架构、构建类型、并行任务数） |
| `config.py` | YAML 配置管理，`InstallConfig` 和 `ToolConfig` 数据类 |
| `environment.py` | 环境变量设置（NATIVE_OHOS_SDK, LLVM_INSTALL_DIR, PATH 等），Windows 下会重置 PATH 避免 MSVC 污染 |
| `builder.py` | Qt 编译执行，**Windows 下生成批处理脚本避免环境继承问题** |
| `downloader.py` | 工具下载（make/perl），支持 winget/chocolatey 自动安装 |

## Key Build Details

### Windows 构建特殊性

Windows 构建使用生成的批处理脚本 (`build_qt_ohos.bat`) 而非直接 subprocess 调用，原因：
- 避免 Python subprocess 环境变量继承问题
- 需要重置 PATH 防止 MSVC `cl.exe` 污染编译环境
- 确保 MinGW `gcc/g++` 被正确检测用于 host tools 构建

### Configure 关键参数

`builder.py` 生成的 configure 命令关键选项：
- `-platform win32-g++`: 使用 MinGW 构建宿主工具
- `-xplatform ohos-clang`: 交叉编译到 HarmonyOS
- `-device-option OHOS_ARCH=<arch>`: 目标架构
- `-prefix` + `-extprefix`: 设备前缀和实际安装路径
- **重要**: 不要在 configure 前设置 QMAKESPEC

### 环境变量

核心环境变量（由 `environment.py` 设置）：
- `NATIVE_OHOS_SDK`: HarmonyOS Native SDK 路径
- `OHOS_SDK_SYSROOT`: SDK sysroot
- `LLVM_INSTALL_DIR`: LLVM 编译器路径
- `OHOS_TARGET_ARCH`: 目标架构
- `MINGW_ROOT`, `PERL_ROOT`: 工具路径

## Configuration

用户配置保存在 `config.yaml`，包含：
- Qt 源码路径、SDK 路径、安装路径
- 架构 (arm64-v8a/x86_64)、构建类型 (release/debug)
- 并行任务数
- 可选的工具路径配置 (make_path, perl_path)

工具路径配置说明：`make_path` 应指向包含 `mingw32-make.exe` 的 MinGW 目录，MinGW 同时提供 `gcc/g++` 用于 host tools 构建。

## Skipping Modules

默认跳过的 Qt 模块列表在 `config.py` 的 `InstallConfig.skip_modules` 中定义，包括 qt3d、qtwebengine 等不需要的模块。

## Logs

日志保存在 `logs/` 目录，文件名格式 `install_<timestamp>.log`。

## Reference

- 官方文档: https://wiki.qt.io/Building_Qt_for_HarmonyOS
- Qt 源码: https://codereview.qt-project.org/qt/tqtc-qt5