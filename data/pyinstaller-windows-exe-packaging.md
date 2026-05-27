# PyInstaller 打包 Python 为 Windows EXE 完整指南

**标签**：#python #tools #experience #cross-platform
**来源**：实践总结 - 2026-03-05
**收录日期**：2026-03-05
**来源日期**：2026-03-05
**更新日期**：2026-05-27
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：PyInstaller 6.0+

### 概要
在 Linux 环境下为 Windows 打包 Python 程序的踩坑记录，包含 bat 脚本生成、资源文件打包、路径兼容等关键问题。

### 内容

#### 问题 1：Windows bat 脚本换行符

**现象**：在 Linux 写的 bat 文件在 Windows 运行报错，显示乱码命令

**原因**：Linux 用 LF 换行，Windows bat 必须 CRLF

**解决方案**：用 Python 生成 bat 文件
```python
content = '''@echo off
echo Hello World
pause
'''
with open('build_win.bat', 'w', newline='\r\n', encoding='utf-8') as f:
    f.write(content)
```

**补充验证（2026-05-27）**：

Windows 双击 `.bat` 启动 PowerShell 工具时，若 `.bat` 文件使用 LF 换行并包含中文 UTF-8 文案，在部分 `cmd.exe` 环境中可能被拆成半截命令执行，例如出现 `"sitory.ps1"`、`"-NoExit"` 不是内部或外部命令等异常。

更稳的处理方式：
- `.bat` 启动器保持纯 ASCII 内容，避免中文和复杂提示文案。
- `.bat` 使用 CRLF 换行。
- `.bat` 内避免容易被路径特殊字符干扰的括号块，使用 `goto` 标签分支更稳。
- 中文用户界面放到 PowerShell `.ps1` 中，`.ps1` 使用 UTF-8 BOM 保存，保证 Windows PowerShell 5.1 能正确读取中文。
- 启动 PowerShell 时使用 `-NoExit -STA -NoProfile -ExecutionPolicy Bypass -File "<script.ps1>"`，其中 `-NoExit` 用于避免双击后窗口闪退，`-STA` 便于使用 Windows Forms 文件夹选择框。

#### 问题 2：资源文件未打包

**现象**：运行 EXE 报错「故事文件不存在」

**原因**：PyInstaller 默认只打包 Python 代码，不包含 JSON/图片等资源

**解决方案**：使用 `--add-data` 参数
```bash
pyinstaller --onefile --console --name "myapp" --add-data "data;data" main.py
```

#### 问题 3：打包后资源路径错误

**现象**：`Path(__file__).parent / "data" / "file.json"` 找不到文件

**原因**：PyInstaller 打包后程序在临时目录运行，`__file__` 指向临时目录

**解决方案**：兼容打包和源码运行的路径获取函数
```python
import sys
from pathlib import Path

def get_base_path() -> Path:
    """获取基础路径，兼容 PyInstaller 打包"""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)  # 打包后的临时目录
    return Path(__file__).parent  # 源码运行
```

#### 问题 4：存档目录消失

**现象**：程序退出后存档丢失

**原因**：`sys._MEIPASS` 是临时目录，程序退出后会被删除

**解决方案**：存档等需要持久化的文件用 `Path.cwd()`（当前工作目录）
```python
save_dir = Path.cwd() / "saves"  # 不用临时目录
```

#### 问题 5：给 Windows 用户发文件格式

**现象**：tar.gz 在 Windows 解压后出现嵌套目录或乱码

**原因**：Windows 处理 tar.gz 的方式不同，可能需要多次解压

**解决方案**：用 ZIP 格式，Windows 原生支持
```python
import zipfile
with zipfile.ZipFile('myapp.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.write('main.py', 'main.py')
```

### 关键代码

完整的打包 bat 脚本模板：
```batch
@echo off
echo ========================================
echo   My App - Windows Build Script
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo [1/3] Installing PyInstaller...
pip install pyinstaller -q

echo [2/3] Building...
pyinstaller --onefile --console --name "myapp" --add-data "data;data" --clean main.py

echo [3/3] Done!
echo.
echo Executable: dist\myapp.exe
echo.
pause
```

Python 路径兼容代码：
```python
def get_base_path() -> Path:
    """获取基础路径，兼容 PyInstaller 打包"""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

# 资源文件路径（只读，可放临时目录）
resource_path = get_base_path() / "data" / "config.json"

# 存档路径（需要持久化，放当前目录）
save_path = Path.cwd() / "saves" / "game.sav"
```

### 参考链接

- [PyInstaller 官方文档](https://pyinstaller.org/en/stable/)
- [PyInstaller --add-data 参数说明](https://pyinstaller.org/en/stable/spec-files.html#adding-data-files)
- [sys._MEIPASS 说明](https://pyinstaller.org/en/stable/runtime-information.html)

### 验证记录
- [2026-03-05] 初次记录，来源：璃的故事游戏打包实践
- [2026-03-05] KT 确认 EXE 可正常运行
- [2026-05-27] 项目修复工具启动器实战验证：LF + 中文 UTF-8 `.bat` 在同事 Windows 机器上被 `cmd.exe` 解析成半截命令；改为 ASCII + CRLF 的 `.bat` 启动器，并将中文界面放入 UTF-8 BOM 的 `.ps1` 后，双击启动正常。

---
