#!/usr/bin/env python3
"""
医疗知识数据预处理执行脚本
用于将原始数据预处理为适合向量化的格式

使用方法:
python run_preprocessing.py [选项]

选项:
  --mode {text,image,all}    选择预处理模式
  --skip-check               跳过数据文件检查
  --config CONFIG_PATH       指定配置文件路径

数据流程:
raw/ → 预处理 → processed/ → 向量化 → 向量数据库
"""

import os
import sys
import json
import argparse
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "processors"))

def check_raw_data():
    """检查原始数据文件是否存在"""
    print("=== 检查原始数据文件 ===")
    
    # 数据目录路径
    base_data_dir = Path("/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge")
    
    # 检查文本原始数据
    text_raw_dir = base_data_dir / "text_data" / "raw"
    print(f"文本原始数据目录: {text_raw_dir}")
    if text_raw_dir.exists():
        text_files = list(text_raw_dir.glob("*"))
        print(f"  ✅ 找到 {len(text_files)} 个文本文件")
        if text_files:
            print("  示例文件:")
            for file in text_files[:3]:
                print(f"    - {file.name}")
    else:
        print("  ❌ 文本原始数据目录不存在")
        return False
    
    # 检查图像原始数据
    image_raw_dir = base_data_dir / "image_text_data" / "raw"
    print(f"图像原始数据目录: {image_raw_dir}")
    if image_raw_dir.exists():
        image_files = list(image_raw_dir.rglob("*.png")) + list(image_raw_dir.rglob("*.jpg")) + list(image_raw_dir.rglob("*.jpeg"))
        print(f"  ✅ 找到 {len(image_files)} 个图像文件")
        if image_files:
            print("  示例文件:")
            for file in image_files[:3]:
                print(f"    - {file.relative_to(image_raw_dir)}")
    else:
        print("  ❌ 图像原始数据目录不存在")
        return False
    
    # 检查原始报告文件
    raw_reports = base_data_dir / "image_text_data" / "raw" / "chestX-rays" / "indiana_reports.csv"
    print(f"\n原始数据检查:")
    print(f"  报告文件: {'✅ 存在' if raw_reports.exists() else '❌ 不存在'}")
    
    return True

def run_text_preprocessing():
    """运行文本数据预处理"""
    print("\n=== 开始文本数据预处理 ===")
    
    try:
        from text_preprocessing import OptimizedMedicalTextPreprocessor
        
        # 设置路径
        raw_data_dir = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/text_data/raw"
        output_dir = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/text_data/processed"
        
        # 创建预处理实例并运行
        preprocessor = OptimizedMedicalTextPreprocessor(raw_data_dir, output_dir)
        preprocessor.run(sample_size=100)  # 处理所有数据
        
        print("✅ 文本数据预处理完成")
        return True
        
    except Exception as e:
        print(f"❌ 文本数据预处理失败: {e}")
        return False

def run_image_preprocessing():
    """运行图像数据预处理"""
    print("\n=== 开始图像数据预处理 ===")
    
    try:
        from image_text_preprocessing import MedicalImageTextPreprocessor
        
        # 设置数据目录
        data_dir = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/image_text_data/raw"
        
        # 创建预处理实例并运行
        preprocessor = MedicalImageTextPreprocessor(data_dir)
        preprocessor.run()
        
        print("✅ 图像数据预处理完成")
        return True
        
    except Exception as e:
        print(f"❌ 图像数据预处理失败: {e}")
        return False

def check_processed_data():
    """检查预处理后的数据"""
    print("\n=== 检查预处理后的数据 ===")
    
    base_data_dir = Path("/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge")
    
    # 检查文本预处理结果
    text_processed_dir = base_data_dir / "text_data" / "processed"
    print(f"文本预处理结果目录: {text_processed_dir}")
    if text_processed_dir.exists():
        text_files = list(text_processed_dir.rglob("*.csv")) + list(text_processed_dir.rglob("*.json"))
        print(f"  ✅ 找到 {len(text_files)} 个预处理文件")
        if text_files:
            print("  示例文件:")
            for file in text_files[:3]:
                print(f"    - {file.name}")
    else:
        print("  ❌ 文本预处理结果目录不存在")
    
    # 检查图像预处理结果
    image_processed_dir = base_data_dir / "image_text_data" / "processed"
    print(f"图像预处理结果目录: {image_processed_dir}")
    if image_processed_dir.exists():
        image_files = list(image_processed_dir.rglob("*.csv")) + list(image_processed_dir.rglob("*.npy"))
        print(f"  ✅ 找到 {len(image_files)} 个预处理文件")
        if image_files:
            print("  示例文件:")
            for file in image_files[:3]:
                print(f"    - {file.name}")
    else:
        print("  ❌ 图像预处理结果目录不存在")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="医疗知识数据预处理执行脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 检查原始数据文件
  python run_preprocessing.py --check-data
  python run_preprocessing.py --mode check
  
  # 只预处理文本数据
  python run_preprocessing.py --text
  python run_preprocessing.py --mode text
  
  # 只预处理图像数据
  python run_preprocessing.py --image
  python run_preprocessing.py --mode image
  
  # 预处理所有数据
  python run_preprocessing.py --all
  python run_preprocessing.py --mode all
  
  # 跳过检查，直接预处理
  python run_preprocessing.py --all --skip-check
        """
    )
    
    parser.add_argument("--mode", 
                       choices=["check", "text", "image", "all"], 
                       default="all", 
                       help="执行模式 (默认: all)")
    
    # 添加便捷参数
    parser.add_argument("--check-data", 
                       action="store_true", 
                       help="检查原始数据文件")
    parser.add_argument("--text", 
                       action="store_true", 
                       help="只预处理文本数据")
    parser.add_argument("--image", 
                       action="store_true", 
                       help="只预处理图像数据")
    parser.add_argument("--all", 
                       action="store_true", 
                       help="预处理所有数据")
    
    parser.add_argument("--skip-check", 
                       action="store_true", 
                       help="跳过数据文件检查")
    parser.add_argument("--config", 
                       type=str, 
                       help="指定配置文件路径")
    
    args = parser.parse_args()
    
    print("🔧 医疗知识数据预处理系统")
    print("=" * 50)
    
    # 处理便捷参数，确定执行模式
    mode = args.mode
    
    # 检查是否有便捷参数被使用
    convenience_args = [args.check_data, args.text, args.image, args.all]
    if any(convenience_args):
        if args.check_data:
            mode = "check"
        elif args.text:
            mode = "text"
        elif args.image:
            mode = "image"
        elif args.all:
            mode = "all"
    
    # 检查原始数据文件
    if not args.skip_check and mode != "check":
        if not check_raw_data():
            print("❌ 原始数据文件检查失败，请检查数据目录")
            return 1
    
    success = True
    
    if mode == "check":
        if not check_raw_data():
            success = False
        check_processed_data()
        if success:
            print("\n✅ 数据文件检查完成")
        return 0 if success else 1
    
    elif mode == "text":
        if not run_text_preprocessing():
            success = False
    
    elif mode == "image":
        if not run_image_preprocessing():
            success = False
    
    elif mode == "all":
        # 按顺序执行各种预处理
        if not run_text_preprocessing():
            success = False
        
        if not run_image_preprocessing():
            success = False
    
    if success:
        print("\n🎉 数据预处理任务执行成功！")
        print("\n📁 预处理结果位置:")
        base_data_dir = Path("/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge")
        print(f"  文本预处理结果: {base_data_dir / 'text_data' / 'processed'}")
        print(f"  图像预处理结果: {base_data_dir / 'image_text_data' / 'processed'}")
        
        print("\n🚀 现在可以运行向量化了！")
        print("   python run_vectorization.py --multimodal")
        
        return 0
    else:
        print("\n❌ 部分预处理任务执行失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    exit(main())
