# Qt for HarmonyOS 编译环境问题与解决方案经验总结

## 一、概述

本文档总结了在 Windows 平台上使用 llvm-mingw-ucrt 工具链交叉编译 Qt for HarmonyOS 时遇到的环境问题及其解决方案。核心原则：**问题根源永远是环境配置，而非源码本身**。

---

## 二、PATH 环境变量污染问题

### 2.1 问题现象

configure 阶段检测到错误的编译器：
- 检测到 MSVC `cl.exe` 而非 MinGW `gcc/g++`
- 检测到其他 MinGW 安装路径的编译器（如 `D:\Prog\winlibs64ucrt_stage\mingw64`）
- `where gcc.exe` 返回非预期的编译器路径

### 2.2 原因分析

Windows 系统中 PATH 环境变量通常包含多个工具链路径：
```
PATH=D:\Prog\winlibs64ucrt_stage\mingw64\bin;C:\Strawberry\c\bin;C:\tools\llvm-mingw\bin;...
```

Qt configure 检测编译器时使用 `where` 命令查找第一个匹配的编译器。PATH 中靠前的路径会被优先选择，导致错误的编译器被检测到。

### 2.3 解决方案

**方案一：构建脚本中重置 PATH**

在批处理脚本开头将 PATH 重置为最小必要路径：
```batch
REM Reset PATH to avoid MSVC pollution and other MinGW interference
set "PATH=C:\Windows\System32;C:\Windows"

REM Add llvm-mingw-ucrt FIRST - provides clang/clang++ and mingw32-make
set "MINGW_BIN=C:\tools\llvm-mingw-20251118-ucrt-x86_64\bin"
if exist "%MINGW_BIN%" set "PATH=%PATH%;%MINGW_BIN%"

REM Add Perl (only for perl, not for GCC)
set "PERL_BIN=C:\Strawberry\perl\bin"
if exist "%PERL_BIN%" set "PATH=%PATH%;%PERL_BIN%"
```

**关键原则**：
1. **llvm-mingw 必须在 PATH 最前面**：提供 `clang`、`clang++`、`mingw32-make`
2. **Strawberry Perl 只添加 perl 目录**：`C:\Strawberry\perl\bin`，**不添加** `C:\Strawberry\c\bin`（含 GCC）
3. **不依赖系统 PATH**：用户系统 PATH 可能包含各种干扰工具链

**方案二：Python subprocess 使用干净环境**

```python
# 使用最小干净环境，避免继承污染的 PATH
clean_env = {
    "PATH": "C:\\Windows\\System32;C:\\Windows",
    "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
    "TEMP": os.environ.get("TEMP", ""),
    "TMP": os.environ.get("TMP", ""),
    "COMSPEC": os.environ.get("COMSPEC", "C:\\Windows\\System32\\cmd.exe"),
}

result = subprocess.run(
    [str(script_path)],
    cwd=build_dir,
    shell=True,
    env=clean_env  # 不使用 os.environ.copy()
)
```

---

## 三、编译器类型与 mkspec 选择

### 3.1 llvm-mingw 编译器特性

llvm-mingw-ucrt 提供的编译器：
- `clang.exe` / `clang++.exe`：原生 Clang 编译器
- `gcc.exe` / `g++.exe`：**Clang 包装器**（不是真正的 GCC）

验证方法：
```batch
C:\tools\llvm-mingw\bin\g++.exe --version
# 输出: clang version 19.x.x (显示为 clang，不是 GCC)
```

### 3.2 mkspec 平台选择

| 工具链 | mkspec 平台 | 说明 |
|--------|-------------|------|
| llvm-mingw-ucrt | `win32-clang-g++` | Clang 编译器，支持 MinGW 目标 |
| MinGW-w64 GCC | `win32-g++` | 真正的 GCC 编译器 |
| MSVC | `win32-msvc` | Visual Studio 编译器 |

**错误案例**：
使用 `win32-g++` 但 PATH 中只有 llvm-mingw 的 clang 包装器：
```
ERROR: mkspecs/win32-g++/qmake.conf not found
或
ERROR: -fno-keep-inline-dllexport flag unsupported (clang 不支持此 GCC flag)
```

**正确方案**：
```batch
configure -platform win32-clang-g++ -xplatform ohos-clang ...
```

---

## 四、QMAKESPEC 环境变量问题

### 4.1 问题现象

configure 报错：
```
Please make sure to unset QMAKESPEC before running configure
```

### 4.2 原因分析

Qt configure 会自动检测编译器并设置 QMAKESPEC。如果环境中已设置 QMAKESPEC，会导致：
1. 编译器检测结果与预设 QMAKESPEC 不匹配
2. 缓存的编译器路径干扰后续编译

### 4.3 解决方案

在 configure 前清除所有 Qt 相关环境变量：
```batch
REM Unset all compiler and Qt environment variables before configure
set "QMAKESPEC="
set "XQMAKESPEC="
set "QMAKEPATH="
set "QMAKEFEATURES="
set "LD="
set "AR="
set "NM="
set "STRIP="
set "OBJCOPY="
set "OBJDUMP="
set "RC="
set "WINDRES="
set "CFLAGS="
set "CXXFLAGS="
set "LDFLAGS="
set "CPPFLAGS="
set "QMAKE_CC="
set "QMAKE_CXX="
set "QMAKE_LINK="
set "QMAKE_AR="
```

---

## 五、sh.exe 依赖问题（Git Bash 干扰）

### 5.1 问题现象

mingw32-make 执行时报错：
```
sh.exe: command not found
或
make: SHELL: sh: command not found
```

### 5.2 原因分析

mingw32-make 默认使用 `sh.exe` 作为 SHELL。Git Bash 安装后 `sh.exe` 在 PATH 中，但：
1. Git Bash 的 sh.exe 路径可能不稳定
2. sh.exe 与 cmd.exe 语法不兼容
3. MAKEFLAGS 环境变量可能包含 sh.exe 相关设置

### 5.3 解决方案

强制使用 cmd.exe 作为 SHELL：
```batch
REM Clear MAKEFLAGS to prevent sh.exe dependency
set "MAKEFLAGS="
set "MFLAGS="
set "SHELL=cmd.exe"

REM Build with explicit SHELL setting
mingw32-make SHELL=cmd.exe -j8
```

---

## 六、Configure 参数问题

### 6.1 -top-level 参数重复

**问题**：顶层 `configure.bat` 自动添加 `-top-level` 参数

查看 `C:\code\tqtc-qt5\configure.bat`：
```batch
echo + %configure% -top-level %*
call %configure% -top-level %*  # 第43行已添加 -top-level
```

如果生成的脚本再添加 `-top-level`，会导致参数重复：
```batch
call configure.bat -top-level -top-level ...  # 重复！
```

**解决**：构建脚本中不要手动添加 `-top-level`

### 6.2 架构参数选择

| Qt 版本 | 架构参数格式 |
|---------|-------------|
| Qt 5.12 | `-ohos-arch arm64-v8a` |
| Qt 5.15 | `-ohos-arch arm64-v8a` 或 `-device-option OHOS_ARCH=arm64-v8a` |

**推荐统一使用**：`-ohos-arch arm64-v8a`

### 6.3 CROSS_COMPILE 参数

指定 OHOS LLVM 编译器路径：
```batch
-device-option CROSS_COMPILE=%LLVM_INSTALL_DIR%\bin
```

注意：路径需要指向 bin 目录，且使用 `%LLVM_INSTALL_DIR%\bin` 而非硬编码路径。

---

## 七、构建目录缓存清理

### 7.1 问题现象

修改环境后重新 configure，仍然使用旧的编译器：
```
Checking for g++... D:\Prog\old_mingw\bin\g++.exe (错误的旧路径)
```

### 7.2 原因分析

Qt configure 缓存检测结果：
- `config.cache`：缓存配置检测结果
- `config.log`：详细的检测日志
- `.qmake.super`：qmake 超级构建缓存
- `qtbase/.qmake.stash`：源码树缓存
- `qmake/Makefile`：包含编译器路径

### 7.3 解决方案

每次 configure 前彻底清理缓存：
```batch
REM Clean build directory cache
if exist "%BUILD_DIR%\config.cache" del /f "%BUILD_DIR%\config.cache"
if exist "%BUILD_DIR%\config.log" del /f "%BUILD_DIR%\config.log"
if exist "%BUILD_DIR%\config.summary" del /f "%BUILD_DIR%\config.summary"
if exist "%BUILD_DIR%\.qmake.super" del /f "%BUILD_DIR%\.qmake.super"
if exist "%BUILD_DIR%\bin" rd /s /q "%BUILD_DIR%\bin"
if exist "%BUILD_DIR%\mkspecs" rd /s /q "%BUILD_DIR%\mkspecs"
if exist "%BUILD_DIR%\qtbase" rd /s /q "%BUILD_DIR%\qtbase"

REM Clean source tree cache
if exist "%QT_SOURCE%\qtbase\.qmake.stash" del /f "%QT_SOURCE%\qtbase\.qmake.stash"
if exist "%QT_SOURCE%\qtbase\qmake\Makefile" del /f "%QT_SOURCE%\qtbase\qmake\Makefile"
if exist "%QT_SOURCE%\qtbase\src\corelib\global\qconfig.cpp" del /f "%QT_SOURCE%\qtbase\src\corelib\global\qconfig.cpp"
```

---

## 八、模块编译警告问题

### 8.1 问题现象

部分模块编译失败：
```
qcoapqudpconnection.cpp:290:5: error: unused variable 'q' [-Werror,-Wunused-variable]
```

### 8.2 原因分析

Clang 编译器默认将某些警告视为错误（`-Werror`），而部分 Qt 模块代码存在：
- 未使用变量
- 废弃函数调用

### 8.3 解决方案

**方案一**：跳过有问题的模块

Qt 5.15 HarmonyOS 推荐跳过列表：
```batch
-skip doc -skip qtactiveqt -skip qtandroidextras -skip qtcanvas3d
-skip qtdoc -skip qtfeedback -skip qtgamepad -skip qtlocation
-skip qtmacextras -skip qtnetworkauth -skip qtpim -skip qtpurchasing
-skip qtqa -skip qtremoteobjects -skip qtrepotools -skip qtscript
-skip qtsystems -skip qttools -skip qtwayland -skip qtwebchannel
-skip qtwebengine -skip qtwebglplugin -skip qtwinextras -skip qtx11extras
-skip qtopcua -skip qtknx -skip qtconnectivity
```

**方案二**：修改源码（不推荐）

修改源码消除警告，但这违反"问题在环境不在源码"原则。

---

## 九、工具链依赖关系

### 9.1 编译阶段工具需求

| 编译阶段 | 所需工具 | 来源 |
|----------|----------|------|
| configure | perl, qmake | Strawberry Perl, qtbase |
| host tools (qmake, moc, rcc) | clang/clang++ | llvm-mingw-ucrt |
| target libraries (libQt5Core.so) | clang (交叉编译) | OHOS SDK LLVM |
| make | mingw32-make | llvm-mingw-ucrt |

### 9.2 工具路径配置原则

```
llvm-mingw-ucrt/bin/
├── clang.exe        → Host tools 编译器
├── clang++.exe      → Host tools 编译器
├── mingw32-make.exe → 构建工具
├── gcc.exe          → clang wrapper (备用)
├── g++.exe          → clang wrapper (备用)

OHOS SDK/native/llvm/bin/
├── clang.exe        → 交叉编译器
├── llvm-ar.exe      → 归档工具
├── llvm-nm.exe      → 符号工具

Strawberry Perl/perl/bin/
├── perl.exe         → configure 脚本执行
```

---

## 十、完整环境配置模板

### 10.1 批处理脚本模板

```batch
@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo Qt for HarmonyOS Build Script
echo ============================================

REM === Step 1: Reset PATH ===
set "PATH=C:\Windows\System32;C:\Windows"

REM === Step 2: Clear shell/make variables ===
set "MAKEFLAGS="
set "MFLAGS="
set "SHELL=cmd.exe"

REM === Step 3: Add llvm-mingw FIRST ===
set "MINGW_BIN=C:\tools\llvm-mingw-20251118-ucrt-x86_64\bin"
set "PATH=%PATH%;%MINGW_BIN%"

REM === Step 4: Add Perl (only perl directory) ===
set "PERL_BIN=C:\Strawberry\perl\bin"
set "PATH=%PATH%;%PERL_BIN%"

REM === Step 5: Add OHOS LLVM ===
set "LLVM_BIN=C:\DevEco\sdk\default\openharmony\native\llvm\bin"
set "PATH=%PATH%;%LLVM_BIN%"

REM === Step 6: Set environment variables ===
set "NATIVE_OHOS_SDK=C:\DevEco\sdk\default\openharmony\native"
set "OHOS_SDK_SYSROOT=C:\DevEco\sdk\default\openharmony\native\sysroot"
set "LLVM_INSTALL_DIR=C:\DevEco\sdk\default\openharmony\native\llvm"
set "OHOS_TARGET_ARCH=arm64-v8a"

REM === Step 7: Clear Qt/compiler variables ===
set "QMAKESPEC="
set "XQMAKESPEC="
set "QMAKEPATH="
set "QMAKEFEATURES="
set "LD="
set "AR="
set "NM="
set "CFLAGS="
set "CXXFLAGS="
set "LDFLAGS="
set "CPPFLAGS="
set "MINGW_HOME="
set "MSYSTEM="
set "MSYSTEM_PREFIX="

REM === Step 8: Verify compiler ===
where clang.exe
echo Expected: %MINGW_BIN%\clang.exe

REM === Step 9: Clean caches ===
if exist "%BUILD_DIR%\config.cache" del /f "%BUILD_DIR%\config.cache"
if exist "%BUILD_DIR%\qtbase" rd /s /q "%BUILD_DIR%\qtbase"

REM === Step 10: Configure ===
pushd "%BUILD_DIR%"
call "%QT_SOURCE%\configure.bat" -v -platform win32-clang-g++ -xplatform ohos-clang -device-option CROSS_COMPILE=%LLVM_INSTALL_DIR%\bin -ohos-arch arm64-v8a ...

REM === Step 11: Build ===
mingw32-make SHELL=cmd.exe -j8

popd
```

---

## 十一、调试技巧

### 11.1 编译器检测调试

```batch
REM 显示所有 clang.exe 路径
where clang.exe

REM 检测 MSVC 是否污染
where cl.exe >nul 2>&1
if %errorlevel% equ 0 echo [WARN] MSVC found!

REM 检测编译器版本
%MINGW_BIN%\clang++.exe --version
```

### 11.2 Configure 日志分析

查看 `config.log` 中的关键检测：
```
Checking for g++... <路径>
Checking for clang... <路径>
```

如果路径错误，检查 PATH 配置。

### 11.3 环境变量导出

```batch
REM 导出当前环境用于调试
set > env_debug.txt
```

---

## 十二、总结

### 核心原则

1. **问题在环境，不在源码**：源码经过验证，问题永远是环境配置错误
2. **PATH 是问题根源**：重置 PATH，按正确顺序添加工具路径
3. **llvm-mingw 提供 clang**：不是 GCC，使用 `win32-clang-g++` mkspec
4. **清理缓存**：每次 configure 前清理所有缓存文件
5. **显式设置 SHELL**：使用 `cmd.exe` 避免 sh.exe 依赖

### 检查清单

| 检查项 | 预期结果 |
|--------|----------|
| `where clang.exe` | 返回 llvm-mingw 路径 |
| `where cl.exe` | 未找到或报错 |
| `clang++ --version` | 显示 clang version |
| `QMAKESPEC` | 未设置（空） |
| `SHELL` | cmd.exe |
| `config.cache` | 已删除 |

---

## 附录：常见错误速查表

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `nmake not found` | 未指定 -platform | 添加 `-platform win32-clang-g++` |
| `sh.exe not found` | Git Bash 在 PATH | 设置 `SHELL=cmd.exe` |
| `QMAKESPEC already set` | 环境变量已设置 | 清除 QMAKESPEC |
| `wrong compiler detected` | PATH 顺序错误 | 重置 PATH，llvm-mingw 优先 |
| `-top-level repeated` | 脚本重复添加 | 脚本中不添加 -top-level |
| `win32-g++ not found` | 无真正 GCC | 使用 `win32-clang-g++` |
| `unused variable error` | 模块警告问题 | 跳过该模块 |

---

*文档生成时间：2026-04-03*
*适用版本：Qt 5.12/5.15 for HarmonyOS*
*工具链：llvm-mingw-ucrt + OHOS SDK LLVM*