# 安装失败问题修复总结

## 问题分析

用户在运行安装时遇到两个错误：

### 1. UnicodeDecodeError
```
UnicodeDecodeError: 'gbk' codec can't decode byte 0xb0 in position 7630: illegal multibyte sequence
```

**原因**：
- subprocess.run() 使用 `text=True` 时，默认用系统编码（GBK）解码输出
- winget命令输出包含GBK无法解码的字符

### 2. Perl下载404错误
```
✗ Download failed: 404 Client Error: Not Found for url:
https://strawberryperl.com/download/5.38.2.2/strawberry-perl-5.38.2.2-64bit.msi
```

**原因**：
- Perl下载URL不可用，返回404错误

## 修复方案

### 修复1：解决编码问题

在 `src/downloader.py` 中，为所有 subprocess.run() 调用添加编码参数：

```python
result = subprocess.run(
    ["winget", "install", "..."],
    capture_output=True,
    text=True,
    encoding='utf-8',      # 使用UTF-8编码
    errors='ignore'        # 忽略无法解码的字符
)
```

**修改位置**：
- `_download_make_windows()` 方法中的 winget 和 choco 命令
- `_download_perl_windows()` 方法中的相关命令

### 修复2：改用winget安装Perl

不再依赖下载MSI文件，改用更可靠的winget安装：

```python
def _download_perl_windows(self) -> bool:
    # Try winget first (more reliable)
    if shutil.which("winget"):
        result = subprocess.run(
            ["winget", "install", "StrawberryPerl.StrawberryPerl", "--accept-source-agreements"],
            ...
        )
```

**优势**：
- winget会自动处理下载和安装
- 不需要手动管理下载URL
- 自动处理PATH配置

## 测试结果

运行 `test_download.py` 测试：

```
✓ Winget is available for Perl installation
✓ All tests passed!
```

**测试验证**：
- ✅ 编码问题已解决，无UnicodeDecodeError
- ✅ Perl安装逻辑正确
- ✅ 提供手动安装选项作为备选

## 手动安装选项

如果winget安装失败，工具会提示手动安装：

### Make工具
```bash
# 方式1：使用chocolatey
choco install make

# 方式2：使用winget
winget install GnuWin32.Make

# 方式3：手动下载
# https://sourceforge.net/projects/gnuwin32/files/make/
```

### Perl
```bash
# 方式1：使用winget
winget install StrawberryPerl.StrawberryPerl

# 方式2：使用chocolatey
choco install strawberryperl

# 方式3：手动下载
# https://strawberryperl.com/
```

## 下一步操作

### 方式1：手动安装工具后继续

```bash
# 1. 安装make
winget install GnuWin32.Make

# 2. 安装Perl
winget install StrawberryPerl.StrawberryPerl

# 3. 重启PowerShell（让PATH生效）

# 4. 验证安装
make --version
perl --version

# 5. 继续Qt安装
python -m src.cli install
```

### 方式2：使用配置文件跳过工具检查

如果您已经安装了make和perl，可以：

```bash
# 1. 检查工具是否可用
python -m src.cli check

# 2. 如果工具已安装，直接运行
python -m src.cli install
```

## 注意事项

1. **管理员权限**：winget安装可能需要管理员权限
2. **PATH配置**：安装后需要重启终端让PATH生效
3. **网络问题**：如果网络受限，建议手动下载安装包

## 修复文件

- `src/downloader.py` - 修复编码问题，改用winget安装
- `src/config.py` - 更新Perl版本信息
- `test_download.py` - 添加测试脚本

## 验证修复

```bash
# 运行测试
python test_download.py

# 检查环境
python -m src.cli check

# 继续安装
python -m src.cli install
```