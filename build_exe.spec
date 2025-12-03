# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller配置文件 - 小智AI客户端
用于打包Windows可执行文件
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
    # Web控制台文件
    ('web', 'web'),
    # 原生库
    ('libs', 'libs'),
    # 源代码中的资源文件（QML等）
    ('src/display/*.qml', 'src/display'),
    ('src/views', 'src/views'),
]

# 收集模型文件（如果存在）
models_dir = os.path.join(root_dir, 'models')
if os.path.exists(models_dir):
    datas.append(('models', 'models'))

# 收集Live2D相关数据
live2d_data = []
try:
    # PIXI和Live2D的数据文件
    live2d_data = collect_data_files('pixi_live2d_display')
except:
    pass

datas.extend(live2d_data)

# 隐藏导入（确保这些模块被包含）
hiddenimports = [
    # 核心模块
    'src.application',
    'src.display.gui_display',
    'src.display.cli_display',
    
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
    
    # 第三方库
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtQuick',
    'PyQt5.QtQuickWidgets',
    'qasync',
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
]

# 自动收集所有src下的子模块
try:
    src_modules = collect_submodules('src')
    hiddenimports.extend(src_modules)
except:
    pass

# PyQt5的二进制文件和插件
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
]

a = Analysis(
    ['main.py'],
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
    name='XiaozhiAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 设置为False隐藏控制台窗口
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
    name='XiaozhiAI',
)
