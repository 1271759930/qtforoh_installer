# Qt for HarmonyOS Installation CLI Tool

一个用于安装鸿蒙版本Qt框架的交互式CLI工具。

## 功能特性

- ✅ **交互式配置输入**：通过友好的交互界面收集Qt源码路径、鸿蒙SDK路径和安装路径
- ✅ **自动工具下载**：自动下载并配置所需的编译工具（make、perl）
- ✅ **环境变量配置**：自动设置所有必要的编译环境变量
- ✅ **自动化编译流程**：一键完成Qt的configure、build和install
- ✅ **进度显示**：实时显示编译进度和日志
- ✅ **错误处理**：完善的错误检测和日志记录
- ✅ **配置管理**：保存和加载安装配置，支持重复安装

## 前置要求

在运行此工具之前，请确保已安装以下软件：

- **Python** >= 3.12.0
- **Git** >= 2.39.3
- **HarmonyOS SDK** (API >= 15，推荐 API 17)
- **Qt源代码** (tqtc-qt5)

### 获取Qt源代码

```bash
# 克隆Qt仓库
git clone https://codereview.qt-project.org/qt/tqtc-qt5
cd tqtc-qt5

# 切换到HarmonyOS分支
git checkout tqtc/harmonyos-5.15.16

# 初始化子模块
git submodule update --init --recursive
```

### 安装HarmonyOS SDK

1. 下载并安装 [DevEco Studio](https://developer.huawei.com/consumer/cn/deveco-studio/)
2. 在DevEco Studio中安装HarmonyOS SDK（推荐API Version 17）
3. SDK路径通常位于：`C:\Users\<用户名>\Library\OpenHarmony\Sdk\<API版本号>`

## 安装

### 方式1：使用pip安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/yourusername/qtohos-installer.git
cd qtohos-installer

# 安装依赖（如果pip命令无法识别，使用 python -m pip）
pip install -r requirements.txt
# 或
python -m pip install -r requirements.txt

# 安装工具（开发模式）
pip install -e .
# 或
python -m pip install -e .
```

**注意**：如果安装后 `qtohos-installer` 命令无法识别，是因为Scripts目录不在PATH中。您可以使用以下方式运行：

### 方式2：使用Python模块运行（推荐）

```bash
# 安装依赖后，直接运行
python -m src.cli install

# 或使用快速启动脚本
python quick_start.py install
```

### 方式3：使用完整路径

```bash
# Windows
C:\Users\<用户名>\AppData\Local\Python\pythoncore-3.14-64\Scripts\qtohos-installer.exe install

# Linux/macOS
~/.local/bin/qtohos-installer install
```

## 使用方法

### 基本安装流程

```bash
# 方式1：使用Python模块运行（最简单）
python -m src.cli install

# 方式2：使用快速启动脚本
python quick_start.py install

# 方式3：如果qtohos-installer命令可用
qtohos-installer install
```

工具将引导您完成以下步骤：

1. **输入Qt源码路径**：指定tqtc-qt5源代码目录
2. **输入鸿蒙SDK路径**：指定HarmonyOS SDK目录
3. **输入安装路径**：指定Qt安装目标目录
4. **选择架构**：选择目标架构（arm64-v8a 或 x86_64）
5. **选择构建类型**：选择release或debug
6. **配置并行任务数**：设置编译并行度
7. **确认配置**：查看并确认所有配置
8. **自动安装**：工具将自动完成下载、配置和编译

### 其他命令

```bash
# 查看当前配置
python -m src.cli config

# 检查前置条件和环境
python -m src.cli check

# 显示安装指南
python -m src.cli guide

# 清理构建产物
python -m src.cli clean

# 显示帮助
python -m src.cli --help
```

## 配置说明

工具会自动生成并保存配置文件 `config.yaml`，包含以下信息：

```yaml
install:
  qt_source_path: /path/to/tqtc-qt5
  harmony_sdk_path: /path/to/harmony-sdk
  install_path: /path/to/qt-install
  architecture: arm64-v8a
  qt_version: 5.15.16
  build_type: release
  parallel_jobs: 8
  # 工具路径配置（可选）
  make_path: null  # 如果已安装make，可指定路径
  perl_path: null  # 如果已安装perl，可指定路径
  skip_modules:
    - qt3d
    - qtactiveqt
    - ...
```

### 工具路径配置

如果您已经安装了make和perl，可以配置它们的路径避免重复安装：

**方式1：交互式配置**

运行 `python -m src.cli install` 时，在Step 7会询问是否已安装工具。

**方式2：配置文件**

在 `config.yaml` 中设置：
```yaml
make_path: "C:/Program Files/GnuWin32/bin/make.exe"
perl_path: "C:/Strawberry Perl/perl/bin/perl.exe"
```

详细说明请参考 [TOOL_PATH_CONFIG.md](TOOL_PATH_CONFIG.md)。

## 环境变量

工具会自动配置以下环境变量：

- `NATIVE_OHOS_SDK`: HarmonyOS Native SDK路径
- `OHOS_SDK_SYSROOT`: SDK sysroot路径
- `LLVM_INSTALL_DIR`: LLVM编译器路径
- `OHOS_SDK_ROOT`: HarmonyOS SDK根路径
- `QT5_ROOT_DIR`: Qt源码路径
- `PATH`: 更新包含编译器和工具路径

环境变量脚本会保存为：
- Windows: `setup_env.bat`
- Linux/macOS: `setup_env.sh`

## 编译选项

工具支持以下编译选项：

### 架构选择
- `arm64-v8a`: 适用于大多数HarmonyOS设备（推荐）
- `x86_64`: 适用于模拟器或x86设备

### 构建类型
- `release`: 优化构建，适用于生产环境
- `debug`: 包含调试符号，适用于开发
- `release-with-debug-info`: 优化但保留调试信息

### 跳过的模块
工具默认跳过以下不必要的Qt模块：
- qt3d, qtactiveqt, qtandroidextras, qtcanvas3d
- qtconnectivity, qtdatavis3d, qtdoc, qtdocgallery
- qtfeedback, qtgamepad, qtgraphicaleffects, qtlocation
- qtmacextras, qtnetworkauth, qtpim, qtpurchasing
- qtqa, qtremoteobjects, qtrepotools, qtscript
- qtscxml, qtsensors, qtserialbus, qtserialport
- qtspeech, qtsystems, qttools, qttranslations
- qtvirtualkeyboard, qtwayland, qtwebchannel, qtwebengine
- qtwebglplugin, qtwebsockets, qtwebview, qtwinextras
- qtx11extras, doc

## 编译时间估算

编译时间取决于您的硬件配置和并行任务数：

| CPU核心数 | 并行任务数 | 预估时间 |
|---------|----------|---------|
| 4核     | 4-8      | 2-3小时  |
| 8核     | 8-12     | 1-2小时  |
| 16核    | 16       | 30-60分钟 |

## 安装后配置

### 在Qt Creator中配置

1. **添加Qt版本**：
   - 路径：`<安装路径>/bin/qmake`
   - 版本名称：Qt 5.15.16 HarmonyOS

2. **添加编译器**：
   - C编译器：`<SDK路径>/native/llvm/bin/clang`
   - C++编译器：`<SDK路径>/native/llvm/bin/clang++`
   - ABI：`arm-linux-generic-elf-64bit`

3. **创建构建套件**：
   - 选择上述Qt版本和编译器
   - mkspec：`ohos-clang`
   - 环境变量：设置 `NATIVE_OHOS_SDK`

### 在DevEco Studio中集成

1. 使用Qt Creator编译Qt项目生成 `.so` 库文件
2. 将 `.so` 文件复制到DevEco项目的 `entry/libs/arm64-v8a` 目录
3. 在 `QtAppConstants.ets` 中指定库名
4. 配置签名并运行到设备

## 故障排除

### 常见问题

**问题1：make或perl未找到**

解决方案：
- 工具会尝试自动下载
- Windows用户可以使用：`choco install make perl`
- 或手动安装：[GnuWin32 Make](https://sourceforge.net/projects/gnuwin32/files/make/) 和 [Strawberry Perl](https://strawberryperl.com/)

**问题2：HarmonyOS SDK路径错误**

解决方案：
- 确保SDK已通过DevEco Studio安装
- 检查路径是否包含 `native` 目录
- 正确路径示例：`C:\Users\<用户>\Library\OpenHarmony\Sdk\12`

**问题3：Qt源码缺少文件**

解决方案：
- 确保已运行 `git submodule update --init --recursive`
- 检查是否在正确的分支（tqtc/harmonyos-5.15.16）

**问题4：编译失败**

解决方案：
- 查看日志文件：`logs/install_<时间戳>.log`
- 检查环境变量是否正确设置
- 尝试减少并行任务数（可能因资源不足导致失败）

### 日志查看

所有操作日志保存在 `logs/` 目录：
```bash
# Windows
type logs\install_20260329_205200.log

# Linux/macOS
cat logs/install_20260329_205200.log
```

## 项目结构

```
qtohos-installer/
├── src/                    # 源代码
│   ├── __init__.py        # 包初始化
│   ├── cli.py             # CLI入口
│   ├── interactive.py     # 交互式输入
│   ├── downloader.py      # 工具下载
│   ├── environment.py     # 环境配置
│   ├── builder.py         # Qt编译
│   ├── installer.py       # 安装流程
│   ├── config.py          # 配置管理
│   └ utils.py             # 工具函数
├── tools/                  # 下载的工具
├── logs/                   # 日志文件
├── pyproject.toml          # 项目配置
├── requirements.txt        # 依赖列表
├── README.md               # 本文档
└── .gitignore              # Git忽略配置
```

## 开发指南

### 依赖安装

```bash
pip install -r requirements.txt
```

### 开发模式运行

```bash
python src/cli.py install
```

### 测试

```bash
pytest tests/
```

### 代码格式化

```bash
black src/
flake8 src/
```

## 参考资源

- [Qt for HarmonyOS官方文档](https://wiki.qt.io/Building_Qt_for_HarmonyOS)
- [Qt官方文档](https://doc.qt.io/)
- [HarmonyOS开发者文档](https://developer.huawei.com/consumer/cn/)
- [DevEco Studio下载](https://developer.huawei.com/consumer/cn/deveco-studio/)

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交Issue和Pull Request！

## 作者

Qt HarmonyOS Installer Team

## 更新日志

### v1.0.0 (2026-03-29)
- ✨ 初始版本发布
- ✅ 完整的交互式安装流程
- ✅ 自动工具下载和配置
- ✅ 环境变量自动设置
- ✅ 编译进度实时显示
- ✅ 完善的错误处理和日志