# 交互式输入改进说明

## 问题

用户反馈在输入时没有回显，希望有更明显的输入框样式。

## 解决方案

使用 Rich Prompt 替代 questionary，提供更清晰的输入界面。

## 改进效果

### 1. 路径输入

**改进前**：
```
Step 1: Qt Source Code Path
Please specify the path to Qt source code (tqtc-qt5).
This should contain the Qt source files for HarmonyOS.
⠙ Qt source code path: _
```

**改进后**：
```
Step 1: Qt Source Code Path
Please specify the path to Qt source code (tqtc-qt5).
This should contain the Qt source files for HarmonyOS.

╭─────────────────────────────────────╮
│ Qt source code path:                │
╰─────────────────────────────────────╯

Enter path: D:\code\tqtc-qt5_
```

### 2. 架构选择

**改进前**：
```
Step 4: Target Architecture
⠙ Select target architecture: _
```

**改进后**：
```
Step 4: Target Architecture

Available options:
  1. arm64-v8a (recommended for most HarmonyOS devices)
  2. x86_64 (for emulator or x86 devices)

Select architecture [1/2] (1): 1_
✓ Selected: arm64-v8a
```

### 3. 构建类型选择

**改进前**：
```
Step 5: Build Type
⠙ Select build type: _
```

**改进后**：
```
Step 5: Build Type

Available options:
  1. release (optimized, recommended for production)
  2. debug (with debug symbols, for development)
  3. release-with-debug-info (optimized but with debug info)

Select build type [1/2/3] (1): 1_
✓ Selected: release
```

### 4. 并行任务数

**改进前**：
```
Step 6: Parallel Build Jobs
⠙ Number of parallel build jobs (default: 8): _
```

**改进后**：
```
Step 6: Parallel Build Jobs
Tip: Set to your CPU core count for optimal performance

Number of parallel jobs (8): 16_
✓ Using 16 parallel jobs
```

### 5. 配置确认

**改进前**：
```
Configuration Summary
...
⠙ Proceed with installation? [Y/n]: _
```

**改进后**：
```
============================================================
Configuration Summary

Qt Source Path        D:\code\tqtc-qt5
HarmonyOS SDK Path   C:\Users\Admin\Library\OpenHarmony\Sdk\12
Install Path         C:\Qt\Qt5.15.16-HarmonyOS
Architecture         arm64-v8a
Qt Version           5.15.16
Build Type           release
Parallel Jobs        16

Proceed with installation? [Y/n]: Y_
```

## 技术实现

### 使用的 Rich 组件

1. **Panel** - 用于创建输入框边框
2. **Prompt.ask()** - 用于文本输入
3. **Confirm.ask()** - 用于确认输入
4. **Console.print()** - 用于显示选项列表

### 代码示例

```python
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()

# 路径输入
console.print(Panel(
    "[bold cyan]Qt source code path:[/bold cyan]",
    border_style="cyan",
    expand=False
))
response = Prompt.ask("[bold green]Enter path[/bold green]")

# 选择输入
console.print("\n[bold]Available options:[/bold]")
console.print("  [cyan]1[/cyan]. Option A")
console.print("  [cyan]2[/cyan]. Option B")
choice = Prompt.ask(
    "\n[bold green]Select option[/bold green]",
    choices=["1", "2"],
    default="1"
)

# 确认输入
confirm = Confirm.ask(
    "\n[bold]Proceed?[/bold]",
    default=True
)
```

## 优势

1. **明显的输入框** - 使用 Panel 创建边框，输入区域更明显
2. **清晰的回显** - Rich Prompt 提供清晰的输入回显
3. **更好的提示** - 使用颜色和加粗字体突出重要信息
4. **选项列表** - 显示所有可用选项，用户无需猜测
5. **即时反馈** - 选择后立即显示结果（✓ Selected: ...）
6. **错误提示** - 清晰的错误消息和重试提示

## 测试

运行以下命令测试新的输入界面：

```bash
python -m src.cli install
```

## 注意事项

- 所有输入都支持 Ctrl+C 取消
- 路径输入会自动验证
- 选择输入会验证输入范围
- 数字输入会验证是否为有效数字