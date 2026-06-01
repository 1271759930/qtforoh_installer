# 使用指南

## 快速开始

### Windows用户

1. **安装依赖**
   ```cmd
   setup.bat
   ```
   或手动安装：
   ```cmd
   pip install -r requirements.txt
   pip install -e .
   ```

2. **运行安装工具**
   ```cmd
   qtohos-installer install
   ```
   
   或使用快速启动脚本：
   ```cmd
   python quick_start.py
   ```

### Linux/macOS用户

1. **安装依赖**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

2. **运行安装工具**
   ```bash
   qtohos-installer install
   ```

## 详细步骤

### 第一步：准备Qt源码

在运行安装工具之前，需要先获取Qt源码：

```bash
# 克隆Qt仓库
git clone https://codereview.qt-project.org/qt/tqtc-qt5
cd tqtc-qt5

# 切换到HarmonyOS分支（5.15.16版本）
git checkout tqtc/harmonyos-5.15.16

# 初始化所有子模块（重要！）
git submodule update --init --recursive

# 返回上级目录
cd ..
```

**注意事项：**
- 确保有足够的磁盘空间（源码约2-3GB）
- 子模块初始化是必需的，否则编译会失败
- 如果网络问题导致克隆失败，可以多次尝试

### 第二步：安装HarmonyOS SDK

1. **下载DevEco Studio**
   - 访问：https://developer.huawei.com/consumer/cn/deveco-studio/
   - 下载最新版本（推荐5.0或更高）

2. **安装SDK**
   - 打开DevEco Studio
   - 进入 Settings/Preferences > HarmonyOS SDK
   - 安装SDK（推荐API Version 17）
   - SDK路径通常在：`C:\Users\<用户名>\Library\OpenHarmony\Sdk\<版本号>`

3. **验证SDK路径**
   ```cmd
   # Windows
   dir C:\Users\<用户名>\Library\OpenHarmony\Sdk\12\native
   
   # 应该看到 llvm, sysroot 等目录
   ```

### 第三步：运行安装工具

```bash
qtohos-installer install
```

工具会依次询问：

#### 1. Qt源码路径
```
Qt source code path: D:\code\tqtc-qt5
```
- 输入第一步中克隆的Qt源码目录
- 工具会验证是否存在configure文件和qtbase目录

#### 2. HarmonyOS SDK路径
```
HarmonyOS SDK path: C:\Users\Administrator\Library\OpenHarmony\Sdk\12
```
- 输入第二步中安装的SDK路径
- 工具会验证native目录是否存在

#### 3. Qt安装路径
```
Qt installation path: C:\Qt\Qt5.15.16-HarmonyOS
```
- 输入希望安装Qt的目标路径
- 可以是任意路径，工具会自动创建

#### 4. 目标架构
```
Select target architecture:
  > arm64-v8a (recommended for most HarmonyOS devices)
    x86_64 (for emulator or x86 devices)
```
- 选择 `arm64-v8a` 用于真实设备
- 选择 `x86_64` 用于模拟器

#### 5. 构建类型
```
Select build type:
  > release (optimized, recommended for production)
    debug (with debug symbols, for development)
    release-with-debug-info (optimized but with debug info)
```
- 选择 `release` 用于生产环境
- 选择 `debug` 用于开发调试

#### 6. 并行任务数
```
Number of parallel build jobs (default: 8): 8
```
- 建议设置为CPU核心数
- 8核CPU建议8-12个任务
- 过多可能导致内存不足

#### 7. 确认配置
```
Configuration Summary:
  Qt Source Path: D:\code\tqtc-qt5
  HarmonyOS SDK Path: C:\Users\Administrator\Library\OpenHarmony\Sdk\12
  Install Path: C:\Qt\Qt5.15.16-HarmonyOS
  Architecture: arm64-v8a
  Qt Version: 5.15.16
  Build Type: release
  Parallel Jobs: 8

Proceed with installation? [Y/n]: Y
```

### 第四步：自动安装过程

工具会自动执行：

1. **检查并下载工具**（如果缺失）
   - make（Windows下可能需要安装）
   - perl（Windows下会下载Strawberry Perl）

2. **设置环境变量**
   ```
   NATIVE_OHOS_SDK: <SDK路径>/native
   LLVM_INSTALL_DIR: <SDK路径>/native/llvm
   OHOS_SDK_SYSROOT: <SDK路径>/native/sysroot
   ...
   ```

3. **创建构建目录**
   ```
   <项目目录>/temp/build_<Qt版本>_<架构>
   ```
   例如: `C:\code\qtforoh_installer\temp\build_5.12.12_arm64-v8a`

4. **运行configure**
   ```
   configure -xplatform ohos-clang -ohos-arch arm64-v8a ...
   ```

5. **编译Qt**（耗时最长）
   ```
   mingw32-make -j8
   ```
   - 根据硬件配置，可能需要1-3小时
   - 可以看到实时编译进度

6. **安装Qt**
   ```
   mingw32-make install
   ```
   - 将编译结果安装到指定路径

### 第五步：验证安装

安装完成后，验证：

```bash
# 检查qmake
C:\Qt\Qt5.15.16-HarmonyOS\bin\qmake.exe -query QT_VERSION

# 应该显示：5.15.16

# 检查库文件
dir C:\Qt\Qt5.15.16-HarmonyOS\lib
```

## 配置Qt Creator

### 1. 添加Qt版本

- 打开Qt Creator
- 工具 > 选项 > Kits > Qt Versions
- 添加：`C:\Qt\Qt5.15.16-HarmonyOS\bin\qmake.exe`
- 名称：Qt 5.15.16 HarmonyOS

### 2. 添加编译器

- 工具 > 选项 > Kits > Compilers
- 添加C编译器：
  - 路径：`C:\Users\<用户>\Library\OpenHarmony\Sdk\12\native\llvm\bin\clang.exe`
  - 名称：OHOS Clang
- 添加C++编译器：
  - 路径：`C:\Users\<用户>\Library\OpenHarmony\Sdk\12\native\llvm\bin\clang++.exe`
  - 名称：OHOS Clang++
- ABI：`arm-linux-generic-elf-64bit`

### 3. 创建构建套件

- 工具 > 选项 > Kits > Kits
- 添加新Kit：
  - 名称：Qt 5.15.16 HarmonyOS arm64
  - Qt版本：Qt 5.15.16 HarmonyOS
  - 编译器：OHOS Clang / OHOS Clang++
  - mkspec：ohos-clang
  - 环境变量：`NATIVE_OHOS_SDK=<SDK路径>/native`

## 在DevEco Studio中集成

### 1. 编译Qt项目

- 在Qt Creator中使用HarmonyOS Kit编译项目
- 生成的 `.so` 文件在项目构建目录

### 2. 创建DevEco项目

- 打开DevEco Studio
- 创建新的HarmonyOS项目（Empty Ability）

### 3. 复制Qt库文件

```bash
# 将Qt项目的.so文件复制到DevEco项目
copy <Qt项目构建目录>\lib*.so <DevEco项目>\entry\libs\arm64-v8a
```

### 4. 配置Qt应用

修改 `entry/src/main/ets/common/QtAppConstants.ets`：

```typescript
export class QtAppConstants {
  // Qt库文件名（不带lib前缀和.so后缀）
  static readonly QT_LIB_NAME: string = 'your_qt_app';
  
  // 其他配置...
}
```

### 5. 运行到设备

- 在DevEco Studio中配置签名
- 连接HarmonyOS设备
- 运行项目

## 常用命令参考

```bash
# 查看当前配置
qtohos-installer config

# 检查环境
qtohos-installer check

# 显示帮助
qtohos-installer --help

# 显示安装指南
qtohos-installer guide

# 清理构建产物（保留配置）
qtohos-installer clean

# 手动设置环境变量（Windows）
setup_env.bat

# 手动设置环境变量（Linux/macOS）
source setup_env.sh
```

## 故障排除

### 问题：make未找到

**解决方案：**

```bash
# 使用Chocolatey（推荐）
choco install make

# 或使用winget
winget install GnuWin32.Make

# 或手动下载
# https://sourceforge.net/projects/gnuwin32/files/make/
```

### 问题：perl未找到

**解决方案：**

```bash
# 使用Chocolatey
choco install strawberryperl

# 或手动下载安装
# https://strawberryperl.com/
```

### 问题：编译失败

**检查步骤：**

1. 查看日志文件
   ```bash
   type logs\install_*.log
   ```

2. 检查环境变量
   ```bash
   qtohos-installer check
   ```

3. 尝试减少并行任务数
   - 修改 `config.yaml` 中的 `parallel_jobs`
   - 从8改为4或更少

4. 检查内存
   - 编译需要大量内存
   - 8GB以下建议减少并行任务

### 问题：Qt源码缺少文件

**解决方案：**

```bash
cd <Qt源码目录>
git submodule update --init --recursive
```

### 问题：SDK路径错误

**验证：**

```bash
# 检查native目录
dir <SDK路径>\native

# 应该包含：
# - llvm
# - sysroot
# - build-tools
```

## 性能优化建议

### 1. 使用SSD
- Qt源码和构建目录放在SSD上
- 可显著提升编译速度

### 2. 增加内存
- 16GB或更多内存可支持更多并行任务
- 减少编译时间

### 3. 调整并行任务数
- CPU核心数 × 1.5 是较好的平衡点
- 例如：8核CPU使用12个任务

### 4. 跳过更多模块
如果不需要某些Qt模块，可以在 `config.yaml` 中添加：
```yaml
skip_modules:
  - qtmultimedia  # 如果不需要多媒体
  - qtwebengine   # 如果不需要Web引擎
```

## 进阶使用

### 使用预设配置

```bash
# 复制示例配置
copy config.example.yaml config.yaml

# 编辑配置文件（修改路径）
notepad config.yaml

# 运行安装（会使用配置文件）
qtohos-installer install
```

### 多架构编译

```bash
# 编译arm64-v8a
qtohos-installer install
# 选择 arm64-v8a

# 编译x86_64（模拟器）
# 清理后重新安装
qtohos-installer clean
qtohos-installer install
# 选择 x86_64
```

### 自定义configure选项

修改 `src/builder.py` 中的 `generate_configure_command()` 方法，添加额外选项：

```python
# 例如添加OpenSSL支持
cmd.extend([
    "-openssl-runtime",
    "-I", "<openssl头文件路径>",
    "-ssl"
])
```

## 参考链接

- [Qt for HarmonyOS官方文档](https://wiki.qt.io/Building_Qt_for_HarmonyOS)
- [Qt编译系统文档](https://doc.qt.io/qt-5/configure-options.html)
- [HarmonyOS应用开发](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides-V5/application-dev-guide-V5)
- [DevEco Studio使用指南](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides-V5/deveco-studio-user-guide-V5)