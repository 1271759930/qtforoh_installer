# 快速使用指南

## 安装步骤

### 1. 安装依赖

```bash
# 在项目目录下运行
python -m pip install -r requirements.txt
```

### 2. 安装工具（可选）

```bash
# 开发模式安装（推荐）
python -m pip install -e .
```

**注意**：如果安装后 `qtohos-installer` 命令无法识别，请使用下面的运行方式。

## 运行方式

### ✅ 方式1：使用Python模块运行（推荐）

```bash
# 查看帮助
python -m src.cli --help

# 运行安装
python -m src.cli install

# 查看配置
python -m src.cli config

# 检查环境
python -m src.cli check

# 显示指南
python -m src.cli guide

# 清理构建
python -m src.cli clean
```

### ✅ 方式2：使用快速启动脚本

```bash
# 查看帮助
python quick_start.py --help

# 运行安装
python quick_start.py install
```

### 方式3：如果qtohos-installer命令可用

```bash
# 查看帮助
qtohos-installer --help

# 运行安装
qtohos-installer install
```

## 常见问题

### Q: pip命令无法识别？

**解决方案**：使用 `python -m pip` 代替 `pip`

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

### Q: qtohos-installer命令无法识别？

**原因**：Scripts目录不在PATH中

**解决方案**：使用 `python -m src.cli` 运行

```bash
python -m src.cli install
```

### Q: 运行时提示ImportError？

**原因**：直接运行了src/cli.py文件

**解决方案**：使用模块方式运行

```bash
# 不要这样运行
python src/cli.py install  # ❌ 错误

# 应该这样运行
python -m src.cli install  # ✅ 正确
```

## 测试安装

运行以下命令测试工具是否正常：

```bash
# 查看版本
python -m src.cli --version

# 查看帮助
python -m src.cli --help

# 检查环境
python -m src.cli check
```

## 下一步

1. 准备Qt源码（tqtc-qt5）
2. 安装HarmonyOS SDK
3. 运行安装工具：
   ```bash
   python -m src.cli install
   ```

## 完整示例

```bash
# 1. 进入项目目录
cd d:\code\qtohos_installer

# 2. 安装依赖
python -m pip install -r requirements.txt

# 3. 测试工具
python -m src.cli --help

# 4. 检查环境
python -m src.cli check

# 5. 运行安装（准备好Qt源码和SDK后）
python -m src.cli install
```

## 更多帮助

- 详细文档：README.md
- 使用指南：USAGE.md
- 官方文档：https://wiki.qt.io/Building_Qt_for_HarmonyOS