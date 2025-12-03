"""
将PNG图标转换为ICO格式
用于Windows EXE打包
"""

try:
    from PIL import Image
    import os
    
    # 输入和输出路径
    input_png = 'assets/icon.png'
    output_ico = 'assets/icon.ico'
    
    print("正在转换图标...")
    print(f"输入: {input_png}")
    print(f"输出: {output_ico}")
    
    # 打开PNG图片
    img = Image.open(input_png)
    
    # 确保是RGBA模式
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # 创建多个尺寸的图标（Windows推荐）
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    
    # 保存为ICO
    img.save(output_ico, format='ICO', sizes=sizes)
    
    print(f"✅ 转换成功！图标已保存到: {output_ico}")
    print(f"文件大小: {os.path.getsize(output_ico) / 1024:.2f} KB")
    
except ImportError:
    print("❌ 需要安装Pillow库")
    print("请运行: pip install Pillow")
except FileNotFoundError:
    print(f"❌ 找不到文件: {input_png}")
    print("请确保assets/icon.png存在")
except Exception as e:
    print(f"❌ 转换失败: {e}")

input("按Enter键退出...")
