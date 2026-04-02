# Qt for HarmonyOS Installer 改进设计

## Context

当前Qt for HarmonyOS安装器在configure阶段存在编译器选择问题。用户报告即使配置了正确的环境变量，生成的makefile仍使用了MSVC编译器而不是clang编译器，导致编译失败。

**问题根因**：
1. 缺少 `-platform win32-g++` 参数，导致Qt configure默认使用系统MSVC编译器
2. PATH没有预先重置，系统中已安装的Visual Studio污染构建环境
3. MinGW工具链缺失，无法正确编译qmake等主机工具

**参考项目**：`C:\Users\Administrator\Downloads\Build-main\Build-main` (gitcode.com/qtforohos/Build)

## Problem Statement

用户环境：
- Qt源码路径：`D:\code\tqtc-qt5`
- HarmonyOS SDK：`D:\DevEco\sdk\default\openharmony`
- 安装路径：`D:\code\Qt5.12-HarmonyOS`

问题表现：
- configure阶段生成的makefile使用MSVC编译器（cl.exe）
- 应使用HarmonyOS SDK的clang编译器进行交叉编译
- 主机工具（qmake）应使用MinGW/GCC编译

## Design

采用方案1：增强现有架构，修复关键问题并改进用户体验。

### 改进模块

#### 1. builder.py - Configure命令改进

**文件路径**：`src/builder.py`

**改动内容**：

```python
def generate_configure_command(self) -> List[str]:
    # 在现有代码第86-97行区域添加
    # 添加platform参数指定MinGW编译主机工具
    if is_windows():
        cmd.extend(["-platform", "win32-g++"])

    # xplatform已在现有代码中，确保正确
    cmd.extend(["-xplatform", "ohos-clang"])
```

**新增方法**：

```python
def _print_compiler_detection(self, env: dict) -> None:
    """在configure前打印编译器检测信息"""
    # 检查PATH中是否有MSVC（应无）
    # 检查MinGW gcc是否可用
    # 检查OHOS clang是否可用

def _verify_generated_mkspec(self) -> None:
    """验证configure生成的mkspec是否正确"""
    # 检查qtbase/mkspecs/default是否指向ohos-clang
```

#### 2. environment.py - PATH管理改进

**文件路径**：`src/environment.py`

**改动内容**：

```python
def reset_path_to_minimum(self) -> None:
    """重置PATH到最小值，避免系统编译器污染"""
    if is_windows():
        minimum_path = [
            "C:\\Windows\\System32",
            "C:\\Windows",
            os.path.dirname(sys.executable)
        ]
        self.env_vars["PATH"] = os.pathsep.join(minimum_path)

def _setup_windows_environment(self) -> None:
    # 首先重置PATH（现有代码第78行区域修改）
    self.reset_path_to_minimum()

    # 然后按顺序添加工具路径
    self._add_mingw_to_path()
    self._add_perl_to_path()
    self._add_llvm_to_path()
```

#### 3. downloader.py - MinGW工具链下载

**文件路径**：`src/downloader.py`

**改动内容**：

```python
def download_mingw(self) -> bool:
    """下载MinGW工具链"""
    mingw_url = "https://gitcode.com/Li-Yaosong/prebuilt/releases/download/1.0.0/mingw64-x86_64-8.1.0-release-posix-seh-rt_v6-rev0.7z"
    # 下载并解压到tools/mingw目录

def validate_toolchain(self) -> bool:
    """验证工具链完整可用"""
    # 测试gcc --version
    # 测试mingw32-make --version
    # 测试perl -e "print $^V"
```

#### 4. config.py - 配置结构扩展

**文件路径**：`src/config.py`

**改动内容**：

```python
@dataclass
class InstallConfig:
    # 现有字段保持不变
    mingw_path: Optional[Path] = None  # 新增MinGW路径
```

#### 5. interactive.py - 交互引导改进

**文件路径**：`src/interactive.py`

**改动内容**：

```python
def prompt_tool_paths(self) -> Tuple[Optional[Path], Optional[Path], Optional[Path]]:
    """提示用户配置工具路径（make/perl/mingw）"""
    # 新增mingw路径提示选项
    # 添加实时验证和版本显示
```

### 修改文件清单

| 文件 | 改动类型 | 改动内容 |
|------|---------|---------|
| `src/builder.py` | 修改+新增 | 添加-platform参数，添加编译器检测方法 |
| `src/environment.py` | 修改+新增 | PATH重置功能，改进PATH构建顺序 |
| `src/downloader.py` | 新增 | MinGW下载功能，工具链验证 |
| `src/config.py` | 修改 | 添加mingw_path字段 |
| `src/interactive.py` | 修改 | 添加mingw路径配置提示 |

## Verification

### 前置条件验证

```bash
python -m src.cli check
# 验证输出：
# ✓ MinGW gcc: x.x.x
# ✓ MinGW g++: x.x.x
# ✓ mingw32-make: x.x.x
# ✓ Perl: x.x.x
# ✓ Clang (OHOS SDK): x.x.x
```

### Configure验证

```bash
python -m src.cli install
# 检查configure输出：
# - "Platform: win32-g++"
# - "Xplatform: ohos-clang"
# - 无MSVC/Visual Studio相关信息
```

### Makefile验证

```bash
# 检查生成的Makefile
cat build_arm64-v8a/Makefile | grep "CC"
# 应显示 clang，不是 cl.exe

cat build_arm64-v8a/qtbase/Makefile | grep "CXX"
# 应显示 clang++，不是 msvc
```

### 构建验证

```bash
python -m src.cli install
D:\code\Qt5.12-HarmonyOS\bin\qmake.exe -query
# 验证qmake能正确运行
```

## Implementation Notes

1. **优先级**：先修复builder.py的-platform参数，这是最关键的改动
2. **依赖关系**：MinGW下载依赖config.py的mingw_path字段
3. **测试顺序**：先测试configure输出，再测试makefile内容，最后测试完整构建

## References

- 参考项目：`C:\Users\Administrator\Downloads\Build-main\Build-main`
- 参考项目关键代码：
  - `build_qt/config.py:125-176` - PATH重置和工具验证
  - `build_qt/config.py:392-397` - `-platform win32-g++` 参数
  - `configure.json:65` - qt5-config中的platform配置