# Windows EXE打包指南

本文档介绍如何将py-xiaozhi项目打包为Windows可执行文件（.exe）

## 📋 准备工作

### 系统要求

- ✅ Windows 10/11 (64位)
- ✅ Python 3.9-3.12
- ✅ 至少5GB可用磁盘空间

### 安装依赖

```bash
# 1. 安装项目依赖
pip install -r requirements.txt

# 2. 安装打包工具
pip install pyinstaller
```

## 🚀 一键打包（推荐）

### 方法1：使用批处理脚本

```bash
# 双击运行或在CMD中执行
build_exe.bat
```

脚本会自动完成：
1. ✅ 检查Python和依赖
2. ✅ 清理旧的构建文件
3. ✅ 执行打包
4. ✅ 创建必要的目录
5. ✅ 生成使用说明

### 方法2：手动打包

```bash
# 清理旧文件（可选）
rmdir /s /q build
rmdir /s /q dist

# 执行打包
pyinstaller build_exe.spec

# 输出在 dist/XiaozhiAI/ 目录
```

## 📦 打包输出

### 目录结构

```
dist/XiaozhiAI/
├── XiaozhiAI.exe          # 主程序（约30MB）
├── _internal/              # 依赖库和资源
│   ├── config/            # 配置文件
│   ├── assets/            # 资源文件
│   ├── web/               # Web控制台
│   ├── libs/              # 原生库
│   ├── models/            # 模型文件（如果有）
│   └── ...                # PyQt5、Python库等
├── logs/                   # 日志目录
├── cache/                  # 缓存目录
└── 使用说明.txt            # 自动生成的说明文件
```

### 文件大小

- **单个exe**：30-50 MB
- **整个文件夹**：200-300 MB（包含所有依赖）
- **压缩后**：100-150 MB

## 🎯 使用打包后的程序

### 基础使用

1. **双击启动**
   ```
   双击 XiaozhiAI.exe
   ```

2. **首次激活**
   - 程序会弹出激活窗口
   - 显示6位验证码
   - 访问 xiaozhi.me 输入验证码

3. **正常使用**
   - GUI界面自动启动
   - Web控制台默认运行在 http://127.0.0.1:8080

### 命令行参数

```bash
# 跳过激活（已激活设备）
XiaozhiAI.exe --skip-activation

# 使用CLI模式
XiaozhiAI.exe --mode cli

# 使用MQTT协议
XiaozhiAI.exe --protocol mqtt

# 自定义Web端口
set XIAOZHI_WEB_PORT=9090
XiaozhiAI.exe
```

## 🔧 自定义配置

### 修改图标

编辑 `build_exe.spec` 文件：

```python
exe = EXE(
    ...
    icon='assets/your_icon.ico',  # 修改为你的图标路径
    ...
)
```

### 修改程序名称

```python
exe = EXE(
    ...
    name='YourAppName',  # 修改程序名称
    ...
)
```

### 是否显示控制台窗口

```python
exe = EXE(
    ...
    console=False,  # False=隐藏控制台，True=显示控制台（用于调试）
    ...
)
```

### 添加额外的资源文件

在 `build_exe.spec` 中添加：

```python
datas = [
    ('config', 'config'),
    ('assets', 'assets'),
    ('web', 'web'),
    ('libs', 'libs'),
    ('your_folder', 'your_folder'),  # 添加你的文件夹
]
```

## 📚 高级选项

### 单文件模式

如果想打包成单个EXE文件（启动会慢，但方便分发）：

修改 `build_exe.spec`：

```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,      # 添加这行
    a.zipfiles,      # 添加这行
    a.datas,         # 添加这行
    [],
    name='XiaozhiAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='assets/icon.png',
)

# 注释掉COLLECT部分
# coll = COLLECT(...)
```

然后打包：
```bash
pyinstaller build_exe.spec
```

### 优化体积

1. **使用UPX压缩**（已启用）
   - 下载UPX：https://github.com/upx/upx/releases
   - 解压到系统PATH中
   - PyInstaller会自动使用

2. **排除不需要的模块**
   
   在 `build_exe.spec` 的 `excludes` 中添加：
   ```python
   excludes = [
       'matplotlib',
       'pandas',
       'scipy',
       # 添加其他不需要的库
   ]
   ```

3. **清理Python缓存**
   ```bash
   # 删除__pycache__
   for /d /r . %d in (__pycache__) do @if exist "%d" rd /s /q "%d"
   ```

## 🐛 常见问题

### Q1: 打包失败，提示缺少模块

**解决**：
```bash
# 重新安装依赖
pip install -r requirements.txt --force-reinstall

# 或在spec文件的hiddenimports中添加缺失模块
hiddenimports = [
    'your_missing_module',
    ...
]
```

### Q2: exe运行时提示DLL错误

**解决**：
```bash
# 重装PyQt5
pip uninstall PyQt5 PyQt5-Qt5 PyQt5-sip
pip install PyQt5
```

### Q3: 打包后体积很大

**解决**：
- 使用UPX压缩（已启用）
- 排除不需要的模块（见高级选项）
- 使用虚拟环境打包（减少无关依赖）

### Q4: 双击exe无反应

**解决**：
1. 临时启用控制台查看错误：
   ```python
   # build_exe.spec
   console=True,  # 改为True
   ```

2. 重新打包并查看错误信息

### Q5: 缺少配置文件或资源文件

**解决**：
确保 `build_exe.spec` 中包含了所有必要的资源：
```python
datas = [
    ('config', 'config'),
    ('assets', 'assets'),
    # 确保都在这里
]
```

## 📦 分发给用户

### 方法1：压缩整个文件夹

```bash
# 压缩 dist/XiaozhiAI/ 为 ZIP
# 用户解压后直接运行 XiaozhiAI.exe
```

### 方法2：创建安装程序

使用 **Inno Setup**（可选）：

1. 下载：https://jrsoftware.org/isdl.php
2. 创建安装脚本
3. 生成 setup.exe 安装程序

### 系统要求说明

告知用户需要：
- ✅ Windows 10/11 (64位)
- ✅ 麦克风和扬声器
- ✅ 稳定的网络连接
- ❌ 不需要安装Python

## 🎉 完成

现在您可以：
1. ✅ 双击 `build_exe.bat` 开始打包
2. ✅ 等待3-10分钟完成打包
3. ✅ 在 `dist/XiaozhiAI/` 找到可执行文件
4. ✅ 压缩后分发给用户

**完整打包后的程序包含**：
- 完整的GUI界面
- Live2D数字人
- 音频输入输出
- Web控制台
- 所有插件和功能

用户无需安装Python，直接双击即可使用！

## 📞 技术支持

遇到问题？
- 📖 查看项目文档：https://huangjunsen0406.github.io/py-xiaozhi/
- 💬 提交Issue：https://github.com/huangjunsen0406/py-xiaozhi/issues
- 📹 视频教程：https://www.bilibili.com/video/BV1dWQhYEEmq/
