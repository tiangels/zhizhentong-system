#!/usr/bin/env python
"""
医疗知识向量化执行脚本
用于将医疗文本和图像数据转换为向量并存储到向量数据库中

使用方法:
python run_vectorization.py [选项]

选项:
  --mode {check,text,image,multimodal,all,test}  选择执行模式
  --skip-check                                   跳过数据文件检查
  --config CONFIG_PATH                           指定配置文件路径

数据目录结构:
datas/medical_knowledge/
├── text_data/raw/          # 放置文本数据文件
├── image_text_data/raw/    # 放置图像数据文件
└── vector_databases/       # 向量数据库存储位置
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "core"))

# 导入配置管理器
from config.config_manager import get_config, get_data_path, get_file_path, get_vector_db_path, get_collection_name

def setup_logging():
    """设置统一日志配置，输出到embedding_service.log"""
    import sys
    from pathlib import Path

    # 添加common模块到路径
    current_file = Path(__file__)
    common_dir = current_file.parent.parent.parent / "common"
    sys.path.insert(0, str(common_dir))

    from log_config import get_logger, get_project_root, get_log_file
        
    # 使用统一的日志管理器
    logger = get_logger(__name__)
    logger.info("🚀 向量化系统启动")
    logger.info(f"📁 项目根目录: {get_project_root()}")
    logger.info(f"📁 日志文件: {get_log_file()}")
    
    return logger

# 初始化日志
logger = setup_logging()

def check_data_files(mode="all"):
    """检查数据文件是否存在"""
    logger.info("=== 检查数据文件 ===")
    logger.info(f"检查模式: {mode}")
    
    # 使用配置管理器获取路径
    config = get_config()
    base_data_dir = config.get_base_data_dir()
    
    # 根据模式选择性检查数据
    if mode in ["text", "all"]:
        # 检查文本数据
        text_raw_dir = get_data_path("text_data", "raw_dir")
        logger.info(f"文本数据目录: {text_raw_dir}")
        if text_raw_dir.exists():
            text_files = list(text_raw_dir.glob("*"))
            logger.info(f"  ✅ 找到 {len(text_files)} 个文本文件")
            if text_files:
                logger.info("  示例文件:")
                for file in text_files[:3]:
                    logger.info(f"    - {file.name}")
        else:
            logger.warning("  ❌ 文本数据目录不存在")
            if mode == "text":
                return False
    
    if mode in ["image", "multimodal", "all"]:
        # 检查图像数据
        image_raw_dir = get_data_path("image_text_data", "raw_dir")
        logger.info(f"图像数据目录: {image_raw_dir}")
        if image_raw_dir.exists():
            image_files = list(image_raw_dir.rglob("*.png")) + list(image_raw_dir.rglob("*.jpg")) + list(image_raw_dir.rglob("*.jpeg"))
            logger.info(f"  ✅ 找到 {len(image_files)} 个图像文件")
            if image_files:
                logger.info("  示例文件:")
                for file in image_files[:3]:
                    logger.info(f"    - {file.relative_to(image_raw_dir)}")
        else:
            logger.warning("  ❌ 图像数据目录不存在")
            if mode in ["image", "multimodal"]:
                return False
    
    if mode in ["voice", "all"]:
        # 检查语音数据
        voice_raw_dir = get_data_path("voice_data", "raw_dir")
        logger.info(f"语音数据目录: {voice_raw_dir}")
        if voice_raw_dir.exists():
            # 支持的音频格式
            audio_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg', '.wma']
            voice_files = []
            for ext in audio_extensions:
                voice_files.extend(list(voice_raw_dir.rglob(f"*{ext}")))
            
            logger.info(f"  ✅ 找到 {len(voice_files)} 个语音文件")
            if voice_files:
                logger.info("  示例文件:")
                for file in voice_files[:3]:
                    logger.info(f"    - {file.relative_to(voice_raw_dir)}")
        else:
            logger.warning("  ❌ 语音数据目录不存在")
            # 语音数据不是必需的，所以不返回False
    
    # 检查原始报告文件（仅对图像相关模式）
    if mode in ["image", "multimodal", "all"]:
        image_raw_dir = get_data_path("image_text_data", "raw_dir")
        raw_reports = image_raw_dir / "chestX-rays" / "indiana_reports.csv"
        logger.info(f"\n原始数据检查:")
        logger.info(f"  报告文件: {'✅ 存在' if raw_reports.exists() else '❌ 不存在'}")
    
    # 检查处理后的数据
    processed_reports = get_file_path("processed_reports")
    processed_images = get_file_path("processed_images")
    
    # 检查文本处理后的数据（仅对文本相关模式）
    if mode in ["text", "all"]:
        # 检查文本文档数据（不是训练数据，而是处理后的文档数据）
        text_documents = get_data_path("text_data", "processed_dir") / "text_documents.json"
        logger.info(f"  文本文档数据: {'✅ 存在' if text_documents.exists() else '⚠️  不存在，需要预处理'}")
    
    # 检查语音处理后的数据（仅对语音相关模式）
    if mode in ["voice", "all"]:
        voice_processed_dir = get_data_path("voice_data", "processed_dir")
        voice_transcriptions = voice_processed_dir / "voice_transcriptions.csv" if voice_processed_dir.exists() else None
        logger.info(f"  语音转录数据: {'✅ 存在' if voice_transcriptions and voice_transcriptions.exists() else '⚠️  不存在，需要预处理'}")
    
    # 检查图像相关数据（仅对图像相关模式）
    if mode in ["image", "multimodal", "all"]:
        logger.info(f"\n处理后数据检查:")
        logger.info(f"  报告文件: {'✅ 存在' if processed_reports.exists() else '⚠️  不存在，需要预处理'}")
        logger.info(f"  图像文件: {'✅ 存在' if processed_images.exists() else '⚠️  不存在，需要预处理'}")
    
    # 检查processed目录中的JSON数据文件
    logger.info(f"\nprocessed数据文件检查:")
    processed_files = {}
    
    if mode in ["text", "all"]:
        processed_files['text'] = get_data_path("text_data", "processed_dir") / "text_documents.json"
    
    if mode in ["image", "multimodal", "all"]:
        processed_files['image_text'] = get_data_path("image_text_data", "processed_dir") / "image_text_documents.json"
    
    if mode in ["voice", "all"]:
        processed_files['voice'] = get_data_path("voice_data", "processed_dir") / "voice_documents.json"
    
    all_processed_ok = True
    for data_type, processed_file in processed_files.items():
        exists = processed_file.exists()
        status = '✅ 存在' if exists else '⚠️  不存在，需要预处理'
        logger.info(f"  {data_type}: {status}")
        if not exists:
            all_processed_ok = False
    
    if not all_processed_ok:
        logger.warning("⚠️  部分processed数据文件不存在，建议先运行预处理")
        logger.info("  运行命令: python run_vectorization.py --mode preprocess")
    
    return True

def run_data_preprocessing(sample_size=None):
    """运行数据预处理"""
    if sample_size is None:
        print(f"\n=== 开始数据预处理 (处理所有数据) ===")
    else:
        print(f"\n=== 开始数据预处理 (样本限制: {sample_size}) ===")
    print("数据流程: raw数据 → 预处理 → processed数据")
    
    try:
        # 导入预处理模块
        processors_dir = current_dir / "processors"
        sys.path.append(str(processors_dir))
        
        from text_preprocessing import OptimizedMedicalTextPreprocessor, setup_logging as setup_text_logging
        from image_text_preprocessing import MedicalImageTextPreprocessor
        
        # 设置统一的日志配置
        logger = setup_text_logging()
        if sample_size is None:
            logger.info(f"=== 开始数据预处理 (处理所有数据) ===")
        else:
            logger.info(f"=== 开始数据预处理 (样本限制: {sample_size}) ===")
        logger.info("数据流程: raw数据 → 预处理 → processed数据")
        
        success = True
        
        # 文本数据预处理
        print("\n--- 文本数据预处理 ---")
        logger.info("--- 文本数据预处理 ---")
        try:
            # 处理通用文本数据（PDF、TXT、CSV等）
            raw_data_dir = get_data_path("text_data", "raw_dir")
            output_dir = get_data_path("text_data", "processed_dir")
            
            # 使用已经导入的模块
            general_text_preprocessor = OptimizedMedicalTextPreprocessor(str(raw_data_dir), str(output_dir))
            general_text_preprocessor.run(sample_size=sample_size)
            print("✅ 通用文本数据预处理完成")
            logger.info("✅ 通用文本数据预处理完成")
            
            # 跳过对话数据处理（数据质量较低，不需要）
            print("⚠️  跳过对话数据处理（数据质量较低）")
            logger.info("⚠️  跳过对话数据处理（数据质量较低）")
                
        except Exception as e:
            print(f"❌ 文本数据预处理失败: {e}")
            logger.error(f"❌ 文本数据预处理失败: {e}")
            success = False
        
        # 图像数据预处理
        print("\n--- 图像数据预处理 ---")
        logger.info("--- 图像数据预处理 ---")
        try:
            data_dir = get_data_path("image_text_data", "raw_dir")
            
            image_preprocessor = MedicalImageTextPreprocessor(str(data_dir))
            image_preprocessor.run()
            print("✅ 图像数据预处理完成")
            logger.info("✅ 图像数据预处理完成")
        except Exception as e:
            print(f"❌ 图像数据预处理失败: {e}")
            logger.error(f"❌ 图像数据预处理失败: {e}")
            success = False
        
        if success:
            print("\n✅ 数据预处理完成")
            print("现在可以继续进行向量化...")
            logger.info("✅ 数据预处理完成")
            logger.info("现在可以继续进行向量化...")
        
        return success
        
    except Exception as e:
        print(f"❌ 数据预处理失败: {e}")
        return False

def run_text_vectorization():
    """运行文本向量化"""
    print("\n=== 开始文本向量化 ===")
    
    try:
        from core.build_multimodal_database import UnifiedMultimodalVectorDatabaseBuilder
        
        # 初始化构建器
        builder = UnifiedMultimodalVectorDatabaseBuilder()
        
        # 只构建文本向量数据库（已注释 - 现在只构建多模态数据库）
        # builder.build_database(
        #     build_text=True,
        #     build_image=False,
        #     build_multimodal=False
        # )
        print("⚠️  文本向量化模式已禁用，现在统一使用多模态数据库")
        return False
        
        print("✅ 文本向量化完成")
        return True
        
    except Exception as e:
        print(f"❌ 文本向量化失败: {e}")
        return False

def run_image_vectorization():
    """运行图像向量化"""
    print("\n=== 开始图像向量化 ===")
    
    try:
        from core.build_multimodal_database import UnifiedMultimodalVectorDatabaseBuilder
        
        # 初始化构建器
        builder = UnifiedMultimodalVectorDatabaseBuilder()
        
        # 只构建图像向量数据库（已注释 - 现在只构建多模态数据库）
        # builder.build_database(
        #     build_text=False,
        #     build_image=True,
        #     build_multimodal=False
        # )
        print("⚠️  图像向量化模式已禁用，现在统一使用多模态数据库")
        return False
        
        print("✅ 图像向量化完成")
        return True
        
    except Exception as e:
        print(f"❌ 图像向量化失败: {e}")
        return False

def run_multimodal_vectorization(sample_size=None):
    """运行多模态向量化（核心功能）"""
    if sample_size is None:
        print(f"\n=== 开始多模态向量化 (处理所有数据) ===")
    else:
        print(f"\n=== 开始多模态向量化 (样本限制: {sample_size}) ===")
    print("这是多模态向量化的核心功能，将构建:")
    print("1. 多模态向量数据库（统一处理文本和图像）")
    print("2. 图像-文本映射关系")
    print("3. 优化说明: 已移除冗余的单独数据库，提高构建效率")
    
    try:
        from core.build_multimodal_database import UnifiedMultimodalVectorDatabaseBuilder
        
        # 初始化构建器
        builder = UnifiedMultimodalVectorDatabaseBuilder()
        
        # 构建多模态向量数据库（优化版本 - 只构建多模态数据库）
        builder.build_database(
            build_multimodal=True,  # 只构建多模态向量数据库
            sample_size=sample_size  # 传递样本限制
        )
        
        print("✅ 多模态向量化完成")
        print("\n📊 构建结果:")
        print("  - 多模态向量数据库: 统一处理文本和图像检索")
        print("  - 图像-文本映射: 支持图文配对检索")
        print("  - 优化说明: 已移除冗余的单独数据库，提高效率")
        
        return True
        
    except Exception as e:
        print(f"❌ 多模态向量化失败: {e}")
        print("\n🔧 故障排除建议:")
        print("1. 检查数据文件是否存在")
        print("2. 检查模型依赖是否正确安装")
        print("3. 检查内存是否充足")
        print("4. 查看详细错误日志")
        return False

def run_unified_multimodal_retrieval_test():
    """运行统一多模态检索测试"""
    print("\n=== 测试统一多模态检索系统 ===")
    
    try:
        from core.cross_modal_retrieval import CrossModalRetrieval
        
        # 初始化统一检索系统
        retrieval_system = CrossModalRetrieval()
        
        # 测试文本检索
        print("测试文本检索...")
        query = "右眼流眼泪"
        results = retrieval_system.search(query=query, top_k=3)
        
        print(f"查询: {query}")
        print(f"找到 {len(results)} 个相关结果")
        for i, result in enumerate(results, 1):
            print(f"结果 {i}: 相似度={result['similarity_score']:.4f}")
            print(f"  内容: {result['content'][:100]}...")
            print(f"  UID: {result['uid']}")
            print(f"  类型: {result['content_type']}")
        
        # 测试图像检索（如果有测试图像）
        print("\n测试图像检索...")
        test_image_path = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/image_text_data/raw/chestX-rays/images"
        if os.path.exists(test_image_path):
            image_files = [f for f in os.listdir(test_image_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
            if image_files:
                test_image = os.path.join(test_image_path, image_files[0])
                print(f"使用测试图像: {test_image}")
                image_results = retrieval_system.search(image_path=test_image, top_k=3)
                
                print(f"图像检索找到 {len(image_results)} 个相关结果")
                for i, result in enumerate(image_results, 1):
                    print(f"结果 {i}: 相似度={result['similarity_score']:.4f}")
                    print(f"  内容: {result['content'][:100]}...")
                    print(f"  UID: {result['uid']}")
                    print(f"  类型: {result['content_type']}")
            else:
                print("未找到测试图像文件")
        else:
            print("测试图像目录不存在")
        
        print("✅ 统一多模态检索系统测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 统一多模态检索测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="医疗知识向量化执行脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 检查数据文件
  python run_vectorization.py --check-data
  python run_vectorization.py --mode check
  
  # 只进行数据预处理
  python run_vectorization.py --preprocess
  python run_vectorization.py --mode preprocess
  
  # 只构建文本向量数据库
  python run_vectorization.py --text
  python run_vectorization.py --mode text
  
  # 只构建图像向量数据库
  python run_vectorization.py --image
  python run_vectorization.py --mode image
  
  # 只构建多模态向量数据库（推荐用于生产）
  python run_vectorization.py --multimodal
  python run_vectorization.py --mode multimodal
  
  # 完整流程：预处理 + 构建所有类型的向量数据库（推荐）
  python run_vectorization.py --all
  python run_vectorization.py --mode all
  
  # 测试跨模态检索系统
  python run_vectorization.py --test
  python run_vectorization.py --mode test
  
  # 跳过检查，直接构建（线上环境推荐）
  python run_vectorization.py --multimodal --skip-check
        """
    )
    
    parser.add_argument("--mode", 
                       choices=["check", "preprocess", "text", "image", "multimodal", "all", "test"], 
                       default="all", 
                       help="执行模式 (默认: all)")
    
    # 添加便捷参数
    parser.add_argument("--check-data", 
                       action="store_true", 
                       help="检查数据文件")
    parser.add_argument("--preprocess", 
                       action="store_true", 
                       help="只进行数据预处理")
    parser.add_argument("--text", 
                       action="store_true", 
                       help="只构建文本向量数据库")
    parser.add_argument("--image", 
                       action="store_true", 
                       help="只构建图像向量数据库")
    parser.add_argument("--multimodal", 
                       action="store_true", 
                       help="只构建多模态向量数据库")
    parser.add_argument("--test", 
                       action="store_true", 
                       help="测试跨模态检索系统")
    parser.add_argument("--all", 
                       action="store_true", 
                       help="构建所有类型的向量数据库")
    
    parser.add_argument("--skip-check", 
                       action="store_true", 
                       help="跳过数据文件检查")
    parser.add_argument("--config", 
                       type=str, 
                       help="指定配置文件路径")
    parser.add_argument("--sample_size", 
                       type=lambda x: None if x.lower() == 'none' else int(x),
                       default=None,
                       help="处理样本数量限制 (默认: None，处理所有数据)")
    
    args = parser.parse_args()
    
    print("🏥 医疗知识向量化系统")
    print("=" * 50)
    
    # 处理便捷参数，确定执行模式
    mode = args.mode
    
    # 检查是否有便捷参数被使用
    convenience_args = [args.check_data, args.preprocess, args.text, args.image, args.multimodal, args.test, args.all]
    if any(convenience_args):
        if args.check_data:
            mode = "check"
        elif args.preprocess:
            mode = "preprocess"
        elif args.text:
            mode = "text"
        elif args.image:
            mode = "image"
        elif args.multimodal:
            mode = "multimodal"
        elif args.test:
            mode = "test"
        elif args.all:
            mode = "all"
    
    # 检查数据文件
    if not args.skip_check and mode != "check":
        if not check_data_files(mode):
            print("❌ 数据文件检查失败，请检查数据目录")
            return 1
    
    success = True
    
    if mode == "check":
        if not check_data_files(mode):
            success = False
        if success:
            print("\n✅ 数据文件检查完成")
        return 0 if success else 1
    
    elif mode == "preprocess":
        if not run_data_preprocessing(args.sample_size):
            success = False
    
    elif mode == "text":
        if not run_text_vectorization():
            success = False
    
    elif mode == "image":
        if not run_image_vectorization():
            success = False
    
    elif mode == "multimodal":
        if not run_multimodal_vectorization(args.sample_size):
            success = False
    
    elif mode == "all":
        # 完整的处理流程：预处理 → 向量化
        print("\n🔄 执行完整处理流程：预处理 → 向量化")
        
        # 首先检查是否需要预处理
        base_data_dir = Path("/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge")
        processed_reports = base_data_dir / "image_text_data" / "processed" / "processed_reports.csv"
        processed_images = base_data_dir / "image_text_data" / "processed" / "processed_images.npy"
        text_documents = base_data_dir / "text_data" / "processed" / "text_documents.json"
        voice_documents = base_data_dir / "voice_data" / "processed" / "voice_documents.json"
        
        # 检查所有类型的预处理数据
        needs_preprocessing = (
            not processed_reports.exists() or 
            not processed_images.exists() or
            not text_documents.exists() or
            not voice_documents.exists()
        )
        
        if needs_preprocessing:
            print("⚠️  检测到缺少预处理数据，自动执行数据预处理...")
            print("🔄 调用: python run_preprocessing.py --all")
            
            # 自动调用run_preprocessing.py --all
            import subprocess
            try:
                # 构建命令
                preprocessing_cmd = [sys.executable, "run_preprocessing.py", "--all"]
                
                # 执行预处理脚本
                result = subprocess.run(
                    preprocessing_cmd,
                    cwd=current_dir,
                    capture_output=True,
                    text=True,
                    timeout=3600  # 1小时超时
                )
                
                if result.returncode == 0:
                    print("✅ 数据预处理完成")
                    print("📋 预处理输出:")
                    print(result.stdout)
                    logger.info("✅ 数据预处理完成")
                    logger.info(f"预处理输出: {result.stdout}")
                else:
                    print("❌ 数据预处理失败")
                    print("📋 错误信息:")
                    print(result.stderr)
                    logger.error("❌ 数据预处理失败")
                    logger.error(f"预处理错误: {result.stderr}")
                    success = False
                    
            except subprocess.TimeoutExpired:
                print("❌ 数据预处理超时（1小时）")
                logger.error("❌ 数据预处理超时")
                success = False
            except Exception as e:
                print(f"❌ 执行数据预处理时发生错误: {e}")
                logger.error(f"❌ 执行数据预处理时发生错误: {e}")
                success = False
                
            if not success:
                print("❌ 数据预处理失败，无法继续向量化")
                return 1
            else:
                print("✅ 数据预处理完成，开始向量化...")
        else:
            print("✅ 预处理数据已存在，直接进行向量化...")
        
        # 如果预处理成功或不需要预处理，继续向量化
        if success:
            # 只执行多模态向量化（优化版本）
            print("\n💡 优化说明: 已移除冗余的单独数据库构建，现在只构建多模态数据库")
            if not run_multimodal_vectorization(args.sample_size):
                success = False
    
    elif mode == "test":
        if not run_unified_multimodal_retrieval_test():
            success = False
    
    if success:
        print("\n🎉 向量化任务执行成功！")
        print("\n📁 向量数据库位置:")
        base_data_dir = Path("/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge")
        print(f"  多模态向量数据库: {Path('/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas') / 'chroma_db'}")
        print(f"  图像-文本映射: {Path('/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas') / 'chroma_db' / 'image_text_mapping.json'}")
        print("\n💡 优化说明:")
        print("   - 已移除冗余的单独文本和图像向量数据库")
        print("   - 现在统一使用多模态向量数据库，提高效率")
        print("   - 支持文本和图像的跨模态检索")
        
        print("\n🚀 现在您可以使用跨模态检索系统了！")
        print("   - 通过文本查询相关图像")
        print("   - 通过图像查询相关文本")
        print("   - 支持图文配对检索")
        
        return 0
    else:
        print("\n❌ 部分任务执行失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    exit(main())
