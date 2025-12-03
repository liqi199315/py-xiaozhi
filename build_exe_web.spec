# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller配置文件 - 小智AI客户端 (Web版)
用于打包使用Web界面的Windows可执行文件
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 项目根目录
root_dir = os.path.abspath(SPECPATH)

# 收集所有需要的数据文件
datas = [
    # 配置文件
    ('config', 'config'),
    # 资源文件（图标、表情等）
    ('assets', 'assets'),
    # Web控制台文件（重要！）
    ('web', 'web'),
    # 原生库
    ('libs', 'libs'),
    # 源代码中的资源文件（用于CLI激活界面）
    ('src/views', 'src/views'),
]

# 收集模型文件（如果存在）
models_dir = os.path.join(root_dir, 'models')
if os.path.exists(models_dir):
    datas.append(('models', 'models'))

# 收集 colorlog 的所有子模块和数据文件
try:
    colorlog_imports = collect_submodules('colorlog')
    colorlog_datas = collect_data_files('colorlog')
except:
    colorlog_imports = []
    colorlog_datas = []

# 隐藏导入（确保这些模块被包含）
hiddenimports = [
    # 核心模块
    'src.application',
    'src.display.webview_display',  # WebView内嵌显示
    'src.display.web_display',  # Web显示
    'src.display.cli_display',   # CLI显示（激活用）
    
    # 插件系统
    'src.plugins.audio',
    'src.plugins.base',
    'src.plugins.calendar',
    'src.plugins.iot',
    'src.plugins.manager',
    'src.plugins.mcp',
    'src.plugins.shortcuts',
    'src.plugins.ui',
    'src.plugins.wake_word',
    'src.plugins.web_server',
    
    # 协议
    'src.protocols.mqtt_protocol',
    'src.protocols.websocket_protocol',
    
    # 音频处理
    'src.audio_codecs.aec_processor',
    'src.audio_codecs.audio_codec',
    'src.audio_codecs.music_decoder',
    'src.audio_processing.wake_word_detect',
    
    # IoT和MCP
    'src.iot.thing',
    'src.iot.thing_manager',
    'src.mcp.mcp_server',
    
    # 工具类
    'src.utils.audio_utils',
    'src.utils.common_utils',
    'src.utils.config_manager',
    'src.utils.device_activator',
    'src.utils.device_fingerprint',
    'src.utils.logging_config',
    'src.utils.opus_loader',
    'src.utils.resource_finder',
    'src.utils.volume_controller',
    
    # 第三方库（Web版需要）
    'aiohttp',
    'aiohttp.web',
    'websockets',
    'paho.mqtt.client',
    'sounddevice',
    'numpy',
    'opuslib',
    'asyncio',
    'json',
    'pathlib',
    'webbrowser',  # 打开浏览器
    'colorlog',    # 彩色日志
    'logging',
    'logging.handlers',
    'webview',     # 内嵌浏览器
    'threading',
]

# 自动收集所有src下的子模块
try:
    src_modules = collect_submodules('src')
    hiddenimports.extend(src_modules)
except:
    pass

# 添加 colorlog 模块
if colorlog_imports:
    hiddenimports.extend(colorlog_imports)

# 添加 colorlog 数据文件
if colorlog_datas:
    datas.extend(colorlog_datas)

# 二进制文件
binaries = []

# 排除不需要的模块（减小体积）
excludes = [
    'matplotlib',
    'pandas',
    'scipy',
    'IPython',
    'jupyter',
    'notebook',
    'tkinter',
    'test',
    'tests',
    'setuptools',
    'pip',
    'wheel',
    # Web版不需要PyQt5
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtQuick',
    'PyQt5.QtQuickWidgets',
    'qasync',
]

a = Analysis(
    ['main_web.py'],  # 使用Web版启动脚本
    pathex=[root_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='XiaozhiAI-Web',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(root_dir, 'assets', 'icon.ico') if os.path.exists(os.path.join(root_dir, 'assets', 'icon.ico')) else os.path.join(root_dir, 'assets', 'icon.png'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='XiaozhiAI-Web',
)
