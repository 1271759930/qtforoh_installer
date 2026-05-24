# Qt for HarmonyOS 交叉编译工具

在 Windows 平台上交叉编译 Qt 框架，生成面向 HarmonyOS 平台的 Qt SDK。

## 功能说明

本工具在 **Windows 平台**上运行，使用 HarmonyOS SDK 交叉编译 Qt 源码，生成可在 HarmonyOS 应用开发中使用的 Qt 库。编译产物安装在 Windows 本地，供 Qt Creator 等开发工具调用。

**支持平台**：Windows（其他平台暂未测试）

## 快速开始

```bash
python run.py
```

就这么简单。脚本会自动：
- ✓ 检查 Python 版本
- ✓ 安装缺失的依赖
- ✓ 启动交互式安装流程

## 其他命令

```bash
python run.py check      # 检查前置条件
python run.py config     # 查看当前配置
python run.py guide      # 显示安装指南
python run.py clean      # 清理构建产物
python run.py --help     # 显示所有命令
```

## 前置要求

| 工具 | 版本要求 | 说明 |
|------|---------|------|
| Python | >= 3.10 | 运行本工具 |
| Git | >= 2.39.3 | 克隆 Qt 源码（商业版本需要） |
| HarmonyOS SDK | API >= 15 | 推荐 API 17 |
| Qt 源码 | 5.12.12 或 5.15.16 | 见下方获取方法 |

### 获取 Qt 源码

有两种方式获取 Qt for HarmonyOS 源码：

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
- 下载地址：[Qt for HarmonyOS 5.12.12 源码包](https://download.qt.io/snapshots/qt/qt-for-harmonyos/5.12.12/qt-harmonyos-src-5.12.12-20260403.zip)
- 发布说明：[Qt 5.12.12 Open Source Release for HarmonyOS](https://wiki.qt.io/Qt5.12.12_Open_Source_Release_for_HarmonyOS)

### 安装 HarmonyOS SDK

1. 下载 [DevEco Studio](https://developer.huawei.com/consumer/cn/deveco-studio/)
2. 安装 HarmonyOS SDK（API Version 17）
3. SDK 路径示例：`C:\Users\<用户>\Library\OpenHarmony\Sdk\17`

## 详细文档

更多内容请查看：
- [安装指南](docs/GUIDE.md) - 详细步骤和配置说明
- [故障排除](docs/GUIDE.md#故障排除) - 常见问题解决

## 许可证

MIT License