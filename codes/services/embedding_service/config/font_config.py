#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
matplotlib中文字体配置模块
解决Mac系统上matplotlib中文字体显示问题
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform
import warnings

def configure_chinese_font():
    """
    配置matplotlib中文字体
    支持Mac、Windows、Linux系统
    """
    system = platform.system()
    
    if system == "Darwin":  # macOS
        # Mac系统推荐的中文字体优先级
        chinese_fonts = [
            'PingFang SC',      # 苹方-简
            'Heiti SC',         # 黑体-简
            'STHeiti',          # 华文黑体
            'Arial Unicode MS', # Arial Unicode MS
            'Songti SC',        # 宋体-简
            'Kaiti SC',         # 楷体-简
        ]
    elif system == "Windows":
        # Windows系统中文字体
        chinese_fonts = [
            'SimHei',           # 黑体
            'Microsoft YaHei',  # 微软雅黑
            'SimSun',           # 宋体
            'KaiTi',            # 楷体
            'FangSong',         # 仿宋
        ]
    else:  # Linux
        # Linux系统中文字体
        chinese_fonts = [
            'WenQuanYi Micro Hei',  # 文泉驿微米黑
            'WenQuanYi Zen Hei',    # 文泉驿正黑
            'Noto Sans CJK SC',     # Noto Sans 中文
            'Source Han Sans SC',   # 思源黑体
            'DejaVu Sans',          # DejaVu Sans
        ]
    
    # 检查可用字体
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    
    # 找到系统中可用的中文字体
    valid_fonts = []
    for font in chinese_fonts:
        if font in available_fonts:
            valid_fonts.append(font)
    
    if not valid_fonts:
        # 如果没有找到预设字体，尝试模糊匹配
        chinese_keywords = ['chinese', 'simhei', 'wenquanyi', 'arial unicode', 
                           'pingfang', 'heiti', 'songti', 'stheit', 'kaiti', 'noto']
        
        for font in available_fonts:
            if any(keyword in font.lower() for keyword in chinese_keywords):
                if font not in valid_fonts:
                    valid_fonts.append(font)
    
    if valid_fonts:
        # 配置matplotlib字体
        plt.rcParams['font.sans-serif'] = valid_fonts + ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 清除字体缓存
        try:
            import matplotlib
            matplotlib.font_manager._rebuild()
        except:
            pass
        
        print(f"✅ 已配置中文字体: {valid_fonts[0]}")
        return True
    else:
        warnings.warn("⚠️ 未找到可用的中文字体，图表中的中文可能显示为方块")
        return False

def get_available_chinese_fonts():
    """
    获取系统中可用的中文字体列表
    
    Returns:
        list: 可用的中文字体名称列表
    """
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    
    chinese_keywords = ['chinese', 'simhei', 'wenquanyi', 'arial unicode', 
                       'pingfang', 'heiti', 'songti', 'stheit', 'kaiti', 'noto']
    
    chinese_fonts = []
    for font in available_fonts:
        if any(keyword in font.lower() for keyword in chinese_keywords):
            chinese_fonts.append(font)
    
    return sorted(list(set(chinese_fonts)))

def test_chinese_display():
    """
    测试中文字体显示效果
    
    Returns:
        bool: 测试是否成功
    """
    try:
        import numpy as np
        
        # 配置字体
        configure_chinese_font()
        
        # 创建测试图表
        fig, ax = plt.subplots(figsize=(8, 6))
        
        x = np.linspace(0, 2*np.pi, 100)
        y = np.sin(x)
        
        ax.plot(x, y, label='正弦波')
        ax.set_title('中文字体测试')
        ax.set_xlabel('X轴')
        ax.set_ylabel('Y轴')
        ax.legend()
        ax.grid(True)
        
        plt.tight_layout()
        plt.close()  # 关闭图表，不显示
        
        print("✅ 中文字体测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 中文字体测试失败: {e}")
        return False

def install_chinese_fonts_mac():
    """
    在Mac系统上安装中文字体的建议
    """
    print("📝 Mac系统中文字体安装建议:")
    print("1. 系统自带字体:")
    print("   - PingFang SC (苹方-简)")
    print("   - Heiti SC (黑体-简)")
    print("   - STHeiti (华文黑体)")
    print("   - Arial Unicode MS")
    print()
    print("2. 如需更多字体，可通过Homebrew安装:")
    print("   brew install font-source-han-sans")
    print("   brew install font-source-han-serif")
    print()
    print("3. 或手动下载安装:")
    print("   - 思源黑体: https://github.com/adobe-fonts/source-han-sans")
    print("   - 文泉驿字体: http://wenq.org/wqy2/")

if __name__ == "__main__":
    print("🎨 matplotlib中文字体配置工具")
    print("=" * 50)
    
    # 显示可用字体
    fonts = get_available_chinese_fonts()
    print(f"🔍 找到 {len(fonts)} 个中文字体:")
    for font in fonts:
        print(f"  - {font}")
    
    print()
    
    # 配置字体
    success = configure_chinese_font()
    
    if success:
        # 测试显示
        test_chinese_display()
    else:
        # 提供安装建议
        if platform.system() == "Darwin":
            install_chinese_fonts_mac()
