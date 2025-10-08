#!/usr/bin/env python
"""
医疗知识数据预处理执行脚本
用于将原始数据预处理为适合向量化的格式

使用方法:
python run_preprocessing.py [选项]

选项:ython3y'to从头kai
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
import logging
from datetime import datetime
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "processors"))

def setup_logging():
    """配置统一日志记录，输出到embedding_service.log"""
    import sys
    from pathlib import Path

    # 添加common模块到路径
    current_file = Path(__file__)
    common_dir = current_file.parent.parent.parent / "common"
    sys.path.insert(0, str(common_dir))

    from log_config import get_logger, get_project_root, get_log_dir
    
    # 使用统一的日志管理器
    logger = get_logger(__name__)
    logger.info("🔧 数据预处理系统启动")
    logger.info(f"📁 项目根目录: {get_project_root()}")
    logger.info(f"📁 日志目录: {get_log_dir()}")
    
    return logger

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
    
    # 检查语音原始数据
    voice_raw_dir = base_data_dir / "voice_data" / "raw"
    print(f"语音原始数据目录: {voice_raw_dir}")
    if voice_raw_dir.exists():
        # 支持的音频格式
        audio_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg', '.wma']
        voice_files = []
        for ext in audio_extensions:
            voice_files.extend(list(voice_raw_dir.rglob(f"*{ext}")))
        
        print(f"  ✅ 找到 {len(voice_files)} 个语音文件")
        if voice_files:
            print("  示例文件:")
            for file in voice_files[:3]:
                print(f"    - {file.relative_to(voice_raw_dir)}")
    else:
        print("  ❌ 语音原始数据目录不存在")
        # 语音数据不是必需的，所以不返回False
    
    # 检查原始报告文件
    raw_reports = base_data_dir / "image_text_data" / "raw" / "chestX-rays" / "indiana_reports.csv"
    print(f"\n原始数据检查:")
    print(f"  报告文件: {'✅ 存在' if raw_reports.exists() else '❌ 不存在'}")
    
    return True

def run_text_preprocessing():
    """运行文本数据预处理"""
    print("\n=== 开始文本数据预处理 ===")
    
    try:
        from processors.text_preprocessing import OptimizedMedicalTextPreprocessor
        
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
        from processors.image_text_preprocessing import MedicalImageTextPreprocessor
        
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

def run_voice_preprocessing():
    """运行语音数据预处理"""
    print("\n=== 开始语音数据预处理 ===")
    
    try:
        from processors.voice_preprocessing import VoicePreprocessor
        
        # 设置数据目录
        raw_data_dir = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/voice_data/raw"
        output_dir = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/voice_data/processed"
        
        # 创建预处理实例并运行
        preprocessor = VoicePreprocessor(raw_data_dir, output_dir)
        preprocessor.run(sample_size=10, process_all_files=True)
        
        print("✅ 语音数据预处理完成")
        return True
        
    except Exception as e:
        print(f"❌ 语音数据预处理失败: {e}")
        import traceback
        traceback.print_exc()
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
    
    # 检查语音预处理结果
    voice_processed_dir = base_data_dir / "voice_data" / "processed"
    print(f"语音预处理结果目录: {voice_processed_dir}")
    if voice_processed_dir.exists():
        voice_files = list(voice_processed_dir.rglob("*.csv")) + list(voice_processed_dir.rglob("*.json"))
        print(f"  ✅ 找到 {len(voice_files)} 个预处理文件")
        if voice_files:
            print("  示例文件:")
            for file in voice_files[:3]:
                print(f"    - {file.name}")
    else:
        print("  ❌ 语音预处理结果目录不存在")

def main():
    """主函数"""
    # 设置日志记录
    logger = setup_logging()
    
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
  
  # 只预处理语音数据
  python run_preprocessing.py --voice
  python run_preprocessing.py --mode voice
  
  # 预处理所有数据
  python run_preprocessing.py --all
  python run_preprocessing.py --mode all
  
  # 跳过检查，直接预处理
  python run_preprocessing.py --all --skip-check
        """
    )
    
    parser.add_argument("--mode", 
                       choices=["check", "text", "image", "voice", "all"], 
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
    parser.add_argument("--voice", 
                       action="store_true", 
                       help="只预处理语音数据")
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
    
    logger.info("🔧 医疗知识数据预处理系统")
    logger.info("=" * 50)
    
    # 处理便捷参数，确定执行模式
    mode = args.mode
    
    # 检查是否有便捷参数被使用
    convenience_args = [args.check_data, args.text, args.image, args.voice, args.all]
    if any(convenience_args):
        if args.check_data:
            mode = "check"
        elif args.text:
            mode = "text"
        elif args.image:
            mode = "image"
        elif args.voice:
            mode = "voice"
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
    
    elif mode == "voice":
        if not run_voice_preprocessing():
            success = False
    
    elif mode == "all":
        # 按顺序执行各种预处理
        if not run_text_preprocessing():
            success = False
        
        if not run_image_preprocessing():
            success = False
        
        if not run_voice_preprocessing():
            success = False
    
    if success:
        logger.info("\n🎉 数据预处理任务执行成功！")
        logger.info("\n📁 预处理结果位置:")
        base_data_dir = Path("/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge")
        logger.info(f"  文本预处理结果: {base_data_dir / 'text_data' / 'processed'}")
        logger.info(f"  图像预处理结果: {base_data_dir / 'image_text_data' / 'processed'}")
        logger.info(f"  语音预处理结果: {base_data_dir / 'voice_data' / 'processed'}")
        
        logger.info("\n🚀 现在可以运行向量化了！")
        logger.info("   python run_vectorization.py --multimodal")
        
        return 0
    else:
        print("\n❌ 部分预处理任务执行失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    exit(main())
