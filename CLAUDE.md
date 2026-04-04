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
pytest tests/    # 运行测试
```

## Architecture

项目采用模块化架构，各模块职责分明：

```
src/
├── cli.py              # CLI 入口，Click 命令定义
├── core/               # 核心流程控制
│   ├── installer.py    # 流程编排器，协调各模块
│   ├── steps.py        # 安装步骤定义（可配置）
│   └── executor.py     # 步骤执行器
├── config/             # 配置管理
│   ├── schema.py       # 数据类（纯数据）
│   ├── loader.py       # 配置加载/保存
│   └── defaults.py     # 默认值和版本配置
├── ui/                 # 用户界面
│   ├── display.py      # 输出展示（Console 封装）
│   └── prompts.py      # 交互式输入收集
├── builder/            # 构建模块
│   ├── qt_builder.py   # Qt 编译执行
│   ├── env_setup.py    # 环境变量设置
│   └── script_gen.py   # 构建脚本生成
├── tools/              # 工具管理
│   └── downloader.py   # 工具下载（make/perl）
└── utils.py            # 工具函数
```

### 模块职责

| 模块 | 职责 |
|------|------|
| `cli.py` | CLI 入口，命令定义和路由 |
| `core/installer.py` | 流程编排，协调各模块完成安装 |
| `core/steps.py` | 安装步骤定义，支持自定义步骤列表 |
| `config/schema.py` | 配置数据类，纯数据容器 |
| `config/defaults.py` | 版本特定的默认配置 |
| `ui/prompts.py` | 交互式输入收集 |
| `ui/display.py` | 输出展示，状态显示 |
| `builder/qt_builder.py` | Qt 编译执行逻辑 |
| `builder/env_setup.py` | 环境变量设置 |
| `tools/downloader.py` | 工具下载和安装 |

### 扩展安装流程

要修改或扩展安装流程，只需修改 `core/steps.py` 中的步骤列表：

```python
# 自定义步骤
from src.core.steps import InstallStep, DEFAULT_STEPS, create_custom_steps

# 添加新步骤
my_steps = DEFAULT_STEPS + [
    InstallStep("custom", "自定义步骤", my_handler_function),
]

# 或跳过某些步骤
my_steps = create_custom_steps(skip_steps=["check"])
```

## Key Build Details

### Windows 构建特殊性

Windows 构建使用生成的批处理脚本 (`build_qt_ohos.bat`) 而非直接 subprocess 调用，原因：
- 避免 Python subprocess 环境变量继承问题
- 需要重置 PATH 防止 MSVC `cl.exe` 污染编译环境
- 确保 MinGW `gcc/g++` 被正确检测用于 host tools 构建

### Configure 关键参数

`builder/qt_builder.py` 生成的 configure 命令关键选项：
- `-platform win32-g++`: 使用 MinGW 构建宿主工具
- `-xplatform ohos-clang`: 交叉编译到 HarmonyOS
- `-device-option OHOS_ARCH=<arch>`: 目标架构
- `-prefix` + `-extprefix`: 设备前缀和实际安装路径
- **重要**: 不要在 configure 前设置 QMAKESPEC

### 环境变量

核心环境变量（由 `builder/env_setup.py` 设置）：
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

## Skipping Modules

默认跳过的 Qt 模块列表在 `config/defaults.py` 中定义，按 Qt 版本区分。

## Logs

日志保存在 `logs/` 目录，文件名格式 `install_<timestamp>.log`。

## Reference

- 官方文档: https://wiki.qt.io/Building_Qt_for_HarmonyOS
- Qt 源码: https://codereview.qt-project.org/qt/tqtc-qt5