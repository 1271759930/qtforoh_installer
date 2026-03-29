# 工具路径配置功能使用说明

## 功能概述

如果您已经安装了make和perl工具，可以通过配置指定它们的路径，避免重复安装。

## 配置方式

### 方式1：交互式配置（推荐）

运行安装命令时，在Step 7会询问您是否已安装工具：

```bash
python -m src.cli install
```

**交互流程示例**：

```
Step 7: Build Tools Configuration
Note: make and perl are required for building Qt

Have you already installed make? [y/N]: y

Please specify make executable path
Example: C:\Program Files\GnuWin32\bin\make.exe

Make executable path: C:\Program Files\GnuWin32\bin\make.exe
✓ Make path set: C:\Program Files\GnuWin32\bin\make.exe

Have you already installed perl? [y/N]: y

Please specify perl executable path
Example: C:\Strawberry Perl\perl\bin\perl.exe

Perl executable path: C:\Strawberry Perl\perl\bin\perl.exe
✓ Perl path set: C:\Strawberry Perl\perl\bin\perl.exe
```

### 方式2：配置文件

在 `config.yaml` 中直接配置：

```yaml
install:
  # ... 其他配置 ...

  # Tool paths (optional)
  make_path: "C:/Program Files/GnuWin32/bin/make.exe"
  perl_path: "C:/Strawberry Perl/perl/bin/perl.exe"
```

或使用 `config.example.yaml` 作为模板：

```bash
# 复制配置模板
cp config.example.yaml config.yaml

# 编辑配置文件
notepad config.yaml
```

## 工具安装方法

### Make工具

#### Windows

```bash
# 方式1：使用winget
winget install GnuWin32.Make

# 方式2：使用chocolatey
choco install make

# 方式3：手动下载
# https://sourceforge.net/projects/gnuwin32/files/make/
```

安装后路径通常为：
- `C:\Program Files\GnuWin32\bin\make.exe`
- 或在PATH中可以直接使用 `make`

#### Linux/macOS

```bash
# Ubuntu/Debian
sudo apt-get install make

# macOS
xcode-select --install
```

### Perl

#### Windows

```bash
# 方式1：使用winget
winget install StrawberryPerl.StrawberryPerl

# 方式2：使用chocolatey
choco install strawberryperl

# 方式3：手动下载
# https://strawberryperl.com/
```

安装后路径通常为：
- `C:\Strawberry Perl\perl\bin\perl.exe`
- 或在PATH中可以直接使用 `perl`

#### Linux/macOS

```bash
# Ubuntu/Debian
sudo apt-get install perl

# macOS
brew install perl
```

## 验证工具安装

### 检查工具是否可用

```bash
# 检查make
make --version

# 检查perl
perl --version
```

### 使用check命令

```bash
python -m src.cli check
```

输出示例：

```
Checking Prerequisites...

✓ Python: Python 3.14.3
✓ Git is available
✓ Make is available
✓ Perl is available

Check Complete
```

## 配置优先级

工具查找顺序：

1. **配置的路径** - 优先使用 `make_path` 和 `perl_path`
2. **PATH环境变量** - 查找系统PATH中的工具
3. **tools目录** - 查找项目tools目录中的工具
4. **自动安装** - 如果都找不到，尝试自动安装

## 配置示例

### 示例1：使用系统安装的工具

```yaml
install:
  qt_source_path: "D:/code/tqtc-qt5"
  harmony_sdk_path: "C:/Users/Admin/Library/OpenHarmony/Sdk/12"
  install_path: "C:/Qt/Qt5.15.16-HarmonyOS"
  architecture: "arm64-v8a"
  qt_version: "5.15.16"
  build_type: "release"
  parallel_jobs: 8
  make_path: null  # 使用PATH中的make
  perl_path: null  # 使用PATH中的perl
```

### 示例2：指定工具路径

```yaml
install:
  qt_source_path: "D:/code/tqtc-qt5"
  harmony_sdk_path: "C:/Users/Admin/Library/OpenHarmony/Sdk/12"
  install_path: "C:/Qt/Qt5.15.16-HarmonyOS"
  architecture: "arm64-v8a"
  qt_version: "5.15.16"
  build_type: "release"
  parallel_jobs: 8
  make_path: "C:/Program Files/GnuWin32/bin/make.exe"
  perl_path: "C:/Strawberry Perl/perl/bin/perl.exe"
```

## 常见问题

### Q: 配置了工具路径但仍然提示找不到？

**A**: 请检查：
1. 路径是否正确（注意Windows路径分隔符）
2. 文件是否存在
3. 是否有执行权限

### Q: 工具在PATH中，是否还需要配置？

**A**: 不需要。工具会自动检测PATH中的工具，只有当工具不在PATH中时才需要配置。

### Q: 可以只配置其中一个工具吗？

**A**: 可以。您可以只配置make或只配置perl，另一个工具会自动处理。

### Q: 配置后如何修改？

**A**: 有两种方式：
1. 重新运行 `python -m src.cli install`，会提示是否使用现有配置
2. 直接编辑 `config.yaml` 文件

## 使用流程

### 完整流程

```bash
# 1. 安装工具（如果还没有）
winget install GnuWin32.Make
winget install StrawberryPerl.StrawberryPerl

# 2. 重启PowerShell（让PATH生效）

# 3. 验证安装
make --version
perl --version

# 4. 运行安装工具
python -m src.cli install

# 5. 在Step 7选择已安装工具，输入路径（或跳过让工具自动检测）
```

### 使用配置文件流程

```bash
# 1. 创建配置文件
cp config.example.yaml config.yaml

# 2. 编辑配置文件，设置工具路径
notepad config.yaml

# 3. 运行安装
python -m src.cli install
```

## 注意事项

1. **路径格式**：Windows路径可以使用 `/` 或 `\\`，推荐使用 `/`
2. **空格处理**：路径包含空格时，在配置文件中不需要引号
3. **可执行文件**：确保配置的是可执行文件路径（.exe），不是目录
4. **权限问题**：确保工具可执行权限正常
5. **版本兼容**：确保工具版本满足要求（make >= 3.82, perl >= 5.38）

## 相关文档

- [README.md](README.md) - 项目概述
- [USAGE.md](USAGE.md) - 详细使用指南
- [config.example.yaml](config.example.yaml) - 配置示例