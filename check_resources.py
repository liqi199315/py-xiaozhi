"""
快速测试打包后的资源路径
在exe所在目录运行此脚本，检查资源文件是否正确
"""

import sys
from pathlib import Path

print("="*50)
print("资源路径检查")
print("="*50)
print()

# 检查是否是打包版本
is_frozen = getattr(sys, 'frozen', False)
print(f"运行模式: {'打包版本 (frozen)' if is_frozen else '开发版本'}")
print(f"sys.executable: {sys.executable}")

if is_frozen:
    print(f"_MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")
    base_dir = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
else:
    base_dir = Path(__file__).parent

print(f"基础目录: {base_dir}")
print()

# 检查关键资源
resources_to_check = [
    'config',
    'config/config.json',
    'assets',
    'assets/icon.png',
    'assets/emojis',
    'web',
    'web/index.html',
    'libs',
    'src/display',
    'src/display/gui_display.qml',
    'src/views',
]

print("检查资源文件:")
print("-"*50)

missing = []
for resource in resources_to_check:
    path = base_dir / resource
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {resource}")
    if not exists:
        missing.append(resource)

print()

if missing:
    print("⚠️  缺少以下资源:")
    for m in missing:
        print(f"  - {m}")
    print()
    print("解决方案:")
    print("1. 检查 build_exe.spec 中的 datas 配置")
    print("2. 重新打包: pyinstaller build_exe.spec")
else:
    print("✅ 所有关键资源都已找到!")

print()
print("="*50)
input("按Enter键退出...")
