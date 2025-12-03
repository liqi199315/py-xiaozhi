# EXE打包问题排查指南

## 问题：打包后运行显示空白窗口

### 原因

QML文件和src目录下的资源文件没有被正确打包。

### 解决方案

#### 步骤1：更新spec文件

确保 `build_exe.spec` 包含以下内容：

```python
datas = [
    ('config', 'config'),
    ('assets', 'assets'),
    ('web', 'web'),
    ('libs', 'libs'),
    # 重要！添加这两行
    ('src/display/*.qml', 'src/display'),
    ('src/views', 'src/views'),
]
```

#### 步骤2：重新打包

```bash
# 清理旧文件
rmdir /s /q build
rmdir /s /q dist

# 重新打包
pyinstaller build_exe.spec
```

#### 步骤3：验证资源

```bash
# 进入打包目录
cd dist\XiaozhiAI

# 运行资源检查脚本（复制check_resources.py到这里）
python check_resources.py
```

或手动检查：
```
dist\XiaozhiAI\_internal\
├── config\           ✓
├── assets\           ✓
├── web\              ✓
├──libs\             ✓
└── src\              ✓ 重要！
    ├── display\
    │   └── gui_display.qml  ✓ 重要！
    └── views\        ✓
```

## 其他常见问题

### 1. 启用控制台查看错误

编辑 `build_exe.spec`：

```python
exe = EXE(
    ...
    console=True,  # 改为True
    ...
)
```

重新打包后，双击exe会显示控制台窗口，可以看到错误信息。

### 2. QML加载错误

如果看到类似错误：
```
file:///C:/path/to/gui_display.qml: File not found
```

**解决**：
- 确保 `src/display/gui_display.qml` 在 datas 中
- 检查相对路径是否正确

### 3. 图标不显示

```python
# 在build_exe.spec中
icon=os.path.join(root_dir, 'assets', 'icon.ico')
```

先运行：
```bash
python convert_icon.py  # 转换PNG为ICO
```

### 4. 依赖库缺失

在 `hidden imports` 中添加缺失的模块：

```python
hiddenimports = [
    # 添加报错的模块
    'missing_module_name',
    ...
]
```

### 5. 打包体积过大

优化方法：
1. 启用UPX压缩（已启用）
2. 排除不需要的库
3. 使用虚拟环境打包

## 调试流程

### 开启调试模式

```python
# build_exe.spec
exe = EXE(
    ...
    debug=True,
    console=True,
    ...
)
```

### 查看打包内容

```bash
# 进入_internal目录
cd dist\XiaozhiAI\_internal

# 查看目录结构
tree /F
```

### 测试单个文件

在打包目录中创建测试脚本：

```python
# test_qml.py
import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQuickWidgets import QQuickWidget
from PyQt5.QtCore import QUrl

app = QApplication(sys.argv)

# 检查QML文件
qml_file = Path(sys._MEIPASS) / 'src' / 'display' / 'gui_display.qml'
print(f"QML path: {qml_file}")
print(f"Exists: {qml_file.exists()}")

if qml_file.exists():
    widget = QQuickWidget()
    widget.setSource(QUrl.fromLocalFile(str(qml_file)))
    widget.show()
    sys.exit(app.exec_())
else:
    print("QML file not found!")
```

## 完整的重新打包流程

```bash
# 1. 清理
rmdir /s /q build
rmdir /s /q dist

# 2. 转换图标（可选）
python convert_icon.py

# 3. 打包（启用调试）
# 临时编辑build_exe.spec，设置console=True
pyinstaller build_exe.spec

# 4. 测试
cd dist\XiaozhiAI
XiaozhiAI.exe

# 5. 查看控制台输出，找到错误
# 6. 根据错误修复spec文件
# 7. 重复2-6直到成功

# 8. 最后关闭调试
# 编辑build_exe.spec，设置console=False
pyinstaller build_exe.spec
```

## 已知问题和解决方案

### QML找不到

**症状**：空白窗口，控制台显示"file not found"

**解决**：
```python
# build_exe.spec
datas = [
    ...
    ('src/display/*.qml', 'src/display'),  # 添加这行
]
```

### PyQt5插件缺失

**症状**：无法加载Qt平台插件

**解决**：
```bash
pip uninstall PyQt5 PyQt5-Qt5 PyQt5-sip
pip install PyQt5
pyinstaller build_exe.spec
```

### Live2D模型不显示

**症状**：窗口显示但没有模型

**解决**：
```python
datas = [
    ('web/live2d', 'web/live2d'),  # 添加Live2D资源
]
```

## 验证清单

打包前检查：

- [ ] `build_exe.spec` 包含所有必要的 datas
- [ ] `assets/icon.ico` 存在（或icon.png）
- [ ] `requirements.txt` 安装完成
- [ ] PyInstaller 已安装

打包后检查：

- [ ] dist/XiaozhiAI/ 目录存在
- [ ] XiaozhiAI.exe 可以运行
- [ ] _internal/src/display/gui_display.qml 存在
- [ ] _internal/assets/ 目录存在
- [ ] _internal/config/ 目录存在

运行检查：

- [ ] 双击exe启动成功
- [ ] 窗口正常显示（不是空白）
- [ ] 可以看到GUI界面
- [ ] 激活窗口显示正常
- [ ] Web控制台可以访问

## 获取帮助

如果问题仍然存在：

1. 运行 `check_resources.py` 检查资源
2. 设置 `console=True` 查看错误
3. 复制完整错误信息
4. 提交Issue并附上错误信息

---

**最常见的解决方案：添加QML文件到datas后重新打包！**
