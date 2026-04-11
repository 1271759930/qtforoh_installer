# Qt for HarmonyOS 交叉编译指南

本文档提供详细的交叉编译步骤、配置说明和故障排除方法。

**说明**：本工具在 Windows 平台上运行，使用 HarmonyOS SDK 的编译器交叉编译 Qt 源码，生成面向 HarmonyOS 平台的 Qt SDK。编译产物安装在 Windows 本地路径，供 Qt Creator 调用以开发 HarmonyOS 应用。

## 目录

- [安装流程详解](#安装流程详解)
- [配置说明](#配置说明)
- [编译选项](#编译选项)
- [环境变量](#环境变量)
- [安装后配置](#安装后配置)
- [故障排除](#故障排除)
- [项目结构](#项目结构)
- [开发指南](#开发指南)

---

## 安装流程详解

运行 `python run.py install` 后，工具会引导您完成以下步骤：

### Step 1: Qt 源码路径

输入 Qt for HarmonyOS 源代码目录的绝对路径。

```
请输入 Qt 源码路径:
> D:\code\qt-harmonyos-src-5.12.12
```

**获取 Qt 源码的两种方式：**

**方式一：商业 License（tqtc 仓库）**
适用于拥有 Qt 商业许可证的用户，支持两个版本：

1. 登录 [Qt Code Review](https://codereview.qt-project.org)
2. 点击右上角 **Settings** → **HTTP Credentials** → **GENERATE NEW PASSWORD**，生成并保存密码
3. 访问 [tqtc-qt5 仓库](https://codereview.qt-project.org/admin/repos/qt/tqtc-qt5)，复制 git 地址
4. 克隆仓库：
   ```bash
   git clone <复制的仓库地址>
   cd tqtc-qt5
   
   # 选择版本分支
   # Qt 5.12.12 版本
   git checkout tqtc/harmonyos-5.12.12
   
   # 或 Qt 5.15.16 版本
   git checkout tqtc/harmonyos-5.15.16
   
   # 初始化子模块
   git submodule update --init --recursive
   ```

**方式二：开源版本（免费下载）**
适用于开源项目或个人开发：
- 下载地址：[Qt for HarmonyOS 5.12.12 源码包](https://download.qt.io/snapshots/qt/qt-for-harmonyos/5.12.12/qt-harmonyos-src-5.12.12-20260403.zip)
- 发布说明：[Qt 5.12.12 Open Source Release for HarmonyOS](https://wiki.qt.io/Qt5.12.12_Open_Source_Release_for_HarmonyOS)

工具会验证：
- 目录是否存在
- 是否包含必要的子目录 (qtbase, qtbase/mkspecs)
- 对于 tqtc 仓库：Git 分支是否正确

### Step 2: HarmonyOS SDK 路径

输入 HarmonyOS SDK 目录路径。

```
请输入 HarmonyOS SDK 路径:
> D:\DevEco\sdk\default\openharmony
```

工具会验证：
- SDK 是否包含 `native` 子目录
- Native SDK 是否包含 `llvm`, `sysroot` 等必要组件

### Step 3: 安装路径

输入 Qt 安装目标路径。

```
请输入 Qt 安装路径:
> D:\code\qt_install
```

目录不存在时会自动创建。

### Step 4: 架构选择

选择目标架构：

```
请选择目标架构:
> arm64-v8a (推荐 - 适用于大多数 HarmonyOS 设备)
  x86_64     (适用于模拟器或 x86 设备)
```

### Step 5: 构建类型

选择构建类型：

```
请选择构建类型:
> release              (推荐 - 优化构建)
  debug                (包含调试符号)
  release-with-debug-info
```

### Step 6: 并行任务数

设置编译并行度，默认根据 CPU 核心数自动设置。

```
请设置并行任务数 (默认: 8):
> 8
```

建议值：
- 4 核 CPU: 4-8
- 8 核 CPU: 8-12
- 16 核 CPU: 16

### Step 7: 确认配置

工具会显示所有配置供您确认：

```
配置摘要:
  Qt 源码路径:     D:\code\qt-harmonyos-src-5.12.12
  SDK 路径:        D:\DevEco\sdk\default\openharmony
  安装路径:        D:\code\qt_install
  架构:            arm64-v8a
  构建类型:        release
  并行任务数:      8
  Qt 版本:         5.12.12 (自动检测)

是否继续? [Y/n]
```

### Step 8: 自动安装

确认后，工具会自动：
1. 下载缺失的编译工具 (make, perl)
2. 配置环境变量
3. 执行 configure
4. 编译 Qt 模块
5. 安装到指定目录

---

## 配置说明

配置文件保存在工作目录的 `config.yaml`：

```yaml
install:
  qt_source_path: /path/to/qt-harmonyos-src-5.12.12
  harmony_sdk_path: /path/to/harmony-sdk
  install_path: /path/to/qt-install
  architecture: arm64-v8a
  qt_version: 5.12.12  # 自动检测，5.12.12(开源) 或 5.15.16(商业)
  build_type: release
  parallel_jobs: 8
  
  # 可选工具路径
  make_path: null
  perl_path: null
  
  # 跳过的模块
  skip_modules:
    - qt3d
    - qtactiveqt
    - ...
```

### 工具路径配置

如果您已安装 make 和 perl，可在配置中指定路径避免重复下载：

```yaml
make_path: "C:/Program Files/GnuWin32/bin/make.exe"
perl_path: "C:/Strawberry/perl/bin/perl.exe"
```

详细说明见 [TOOL_PATH_CONFIG.md](TOOL_PATH_CONFIG.md)。

---

## 编译选项

### 架构选择

| 架构 | 适用场景 |
|------|---------|
| `arm64-v8a` | 大多数 HarmonyOS 设备（推荐） |
| `x86_64` | 模拟器或 x86 设备 |

### 构建类型

| 类型 | 说明 |
|------|------|
| `release` | 优化构建，适合生产环境 |
| `debug` | 包含调试符号，适合开发调试 |
| `release-with-debug-info` | 优化但保留调试信息 |

### 跳过的模块

默认跳过以下不必要的 Qt 模块：

```
qt3d, qtactiveqt, qtandroidextras, qtcanvas3d,
qtconnectivity, qtdatavis3d, qtdoc, qtdocgallery,
qtfeedback, qtgamepad, qtgraphicaleffects, qtlocation,
qtmacextras, qtnetworkauth, qtpim, qtpurchasing,
qtqa, qtremoteobjects, qtrepotools, qtscript,
qtscxml, qtsensors, qtserialbus, qtserialport,
qtspeech, qtsystems, qttools, qttranslations,
qtvirtualkeyboard, qtwayland, qtwebchannel, qtwebengine,
qtwebglplugin, qtwebsockets, qtwebview, qtwinextras,
qtx11extras, qtopcua, qtknx, doc
```

---

## 环境变量

工具自动配置以下环境变量：

| 变量 | 说明 |
|------|------|
| `NATIVE_OHOS_SDK` | HarmonyOS Native SDK 路径 |
| `OHOS_SDK_SYSROOT` | SDK sysroot 路径 |
| `LLVM_INSTALL_DIR` | LLVM 编译器路径 |
| `OHOS_SDK_ROOT` | HarmonyOS SDK 根路径 |
| `HOS_SDK_HOME` | HarmonyOS SDK 根路径 |
| `QT5_ROOT_DIR` | Qt 源码路径 |
| `MINGW_ROOT` | MinGW 工具路径 |
| `PERL_ROOT` | Perl 工具路径 |
| `PATH` | 更新包含编译器和工具路径 |

环境变量脚本会保存为：
- Windows: `setup_env.bat`
- Linux/macOS: `setup_env.sh`

---

## 安装后配置

### 在 Qt Creator 中配置

1. **添加 Qt 版本**：
   - 路径：`<安装路径>/bin/qmake`
   - 版本名称：Qt 5.12.12 HarmonyOS（或根据实际编译版本）

2. **添加编译器**：
   - C 编译器：`<SDK路径>/native/llvm/bin/clang`
   - C++ 编译器：`<SDK路径>/native/llvm/bin/clang++`
   - ABI：`arm-linux-generic-elf-64bit`

3. **创建构建套件**：
   - 选择上述 Qt 版本和编译器
   - mkspec：`ohos-clang`
   - 环境变量：设置 `NATIVE_OHOS_SDK`

### 在 DevEco Studio 中集成

1. 使用 Qt Creator 编译 Qt 项目生成 `.so` 库文件
2. 将 `.so` 文件复制到 DevEco 项目的 `entry/libs/arm64-v8a` 目录
3. 在 `QtAppConstants.ets` 中指定库名
4. 配置签名并运行到设备

---

## 故障排除

### Python 版本过低

```
错误: Python 版本过低
当前版本: Python 3.10.0
需要版本: Python >= 3.12
```

**解决方案**：
- 从 [python.org](https://python.org/downloads/) 下载 Python 3.12+
- 安装后重新运行 `python run.py`

### make 或 perl 未找到

```
[ERROR] make 未安装
```

**解决方案**：
- 工具会尝试自动下载
- Windows 用户可手动安装：
  - [GnuWin32 Make](https://sourceforge.net/projects/gnuwin32/files/make/)
  - [Strawberry Perl](https://strawberryperl.com/)
- 或使用 Chocolatey：`choco install make perl`

### HarmonyOS SDK 路径错误

```
[ERROR] HarmonyOS SDK native 目录不存在
```

**解决方案**：
- 确保 SDK 已通过 DevEco Studio 安装
- 检查路径是否包含 `native` 目录
- 正确路径示例：`C:\Users\<用户>\Library\OpenHarmony\Sdk\17`

### Qt 源码缺少文件

```
[ERROR] qtbase/mkspecs 目录不存在
```

**解决方案**：
- **商业版本 (tqtc)**：确保已运行 `git submodule update --init --recursive`，检查分支是否正确 (`tqtc/harmonyos-5.12.12` 或 `tqtc/harmonyos-5.15.16`)
- **开源版本**：确保下载的 zip 包已完整解压，检查目录结构是否完整

### 编译失败

**解决方案**：
- 查看日志：`logs/install_<时间戳>.log`
- 检查环境变量是否正确设置
- 尝试减少并行任务数（资源不足可能导致失败）
- 确保磁盘空间充足（编译需要约 10GB）

### 查看日志

```bash
# Windows
type logs\install_20260411_120000.log

# Linux/macOS
cat logs/install_20260411_120000.log
```

---

## 项目结构

```
qtohos-installer/
├── run.py                  # 主入口脚本
├── src/                    # 源代码
│   ├── cli.py             # CLI 命令定义
│   ├── core/              # 核心流程
│   │   ├── installer.py   # 流程编排
│   │   ├── steps.py       # 安装步骤
│   │   └── executor.py    # 步骤执行
│   ├── config/            # 配置管理
│   │   ├── schema.py      # 数据类
│   │   ├── loader.py      # 配置加载
│   │   └ defaults.py      # 默认配置
│   ├── ui/                # 用户界面
│   │   ├── display.py     # 输出展示
│   │   └ prompts.py       # 交互输入
│   ├── builder/           # 构建模块
│   │   ├── qt_builder.py  # Qt 编译
│   │   ├── env_setup.py   # 环境设置
│   │   └ script_gen.py    # 脚本生成
│   ├── tools/             # 工具管理
│   │   └ downloader.py    # 工具下载
│   └ utils.py             # 工具函数
├── docs/                   # 文档
├── tests/                  # 测试
├── pyproject.toml          # 项目配置
├── requirements.txt        # 依赖列表
├── README.md               # 快速开始
└── GUIDE.md               # 详细指南
```

---

## 开发指南

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black src/
flake8 src/
```

### 类型检查

```bash
mypy src/
```

---

## 参考资源

- [Qt for HarmonyOS 官方文档](https://wiki.qt.io/Building_Qt_for_HarmonyOS)
- [Qt 官方文档](https://doc.qt.io/)
- [HarmonyOS 开发者文档](https://developer.huawei.com/consumer/cn/)
- [DevEco Studio 下载](https://developer.huawei.com/consumer/cn/deveco-studio/)