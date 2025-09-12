#!/usr/bin/env python3
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
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "core"))

def check_data_files():
    """检查数据文件是否存在"""
    print("=== 检查数据文件 ===")
    
    # 数据目录路径
    base_data_dir = Path("/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge")
    
    # 检查文本数据
    text_raw_dir = base_data_dir / "text_data" / "raw"
    print(f"文本数据目录: {text_raw_dir}")
    if text_raw_dir.exists():
        text_files = list(text_raw_dir.glob("*"))
        print(f"  ✅ 找到 {len(text_files)} 个文本文件")
        if text_files:
            print("  示例文件:")
            for file in text_files[:3]:
                print(f"    - {file.name}")
    else:
        print("  ❌ 文本数据目录不存在")
        return False
    
    # 检查图像数据
    image_raw_dir = base_data_dir / "image_text_data" / "raw"
    print(f"图像数据目录: {image_raw_dir}")
    if image_raw_dir.exists():
        image_files = list(image_raw_dir.rglob("*.png")) + list(image_raw_dir.rglob("*.jpg")) + list(image_raw_dir.rglob("*.jpeg"))
        print(f"  ✅ 找到 {len(image_files)} 个图像文件")
        if image_files:
            print("  示例文件:")
            for file in image_files[:3]:
                print(f"    - {file.relative_to(image_raw_dir)}")
    else:
        print("  ❌ 图像数据目录不存在")
        return False
    
    # 检查原始报告文件
    raw_reports = base_data_dir / "image_text_data" / "raw" / "chestX-rays" / "indiana_reports.csv"
    print(f"\n原始数据检查:")
    print(f"  报告文件: {'✅ 存在' if raw_reports.exists() else '❌ 不存在'}")
    
    # 检查处理后的数据
    processed_reports = base_data_dir / "image_text_data" / "processed" / "processed_reports.csv"
    processed_images = base_data_dir / "image_text_data" / "processed" / "processed_images.npy"
    
    # 检查纯文本处理后的数据
    general_text_train = base_data_dir / "text_data" / "processed" / "training_data" / "general_text_train.csv"
    general_text_test = base_data_dir / "text_data" / "processed" / "test_data" / "general_text_test.csv"
    
    print(f"\n处理后数据检查:")
    print(f"  报告文件: {'✅ 存在' if processed_reports.exists() else '⚠️  不存在，需要预处理'}")
    print(f"  图像文件: {'✅ 存在' if processed_images.exists() else '⚠️  不存在，需要预处理'}")
    print(f"  纯文本训练数据: {'✅ 存在' if general_text_train.exists() else '⚠️  不存在，需要预处理'}")
    print(f"  纯文本测试数据: {'✅ 存在' if general_text_test.exists() else '⚠️  不存在，需要预处理'}")
    
    return True

def run_data_preprocessing():
    """运行数据预处理"""
    print("\n=== 开始数据预处理 ===")
    print("数据流程: raw数据 → 预处理 → processed数据")
    
    try:
        # 导入预处理模块
        sys.path.append(str(current_dir / "processors"))
        from text_preprocessing import OptimizedMedicalTextPreprocessor
        from image_text_preprocessing import MedicalImageTextPreprocessor
        
        success = True
        
        # 文本数据预处理
        print("\n--- 文本数据预处理 ---")
        try:
            # 处理通用文本数据（PDF、TXT、CSV等）
            raw_data_dir = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/text_data/raw"
            output_dir = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/text_data/processed"
            
            from general_text_preprocessing import GeneralTextPreprocessor
            general_text_preprocessor = GeneralTextPreprocessor(raw_data_dir, output_dir)
            general_text_preprocessor.run()
            print("✅ 通用文本数据预处理完成")
            
            # 处理特定格式的医疗对话数据（如果存在）
            try:
                text_preprocessor = OptimizedMedicalTextPreprocessor(raw_data_dir, output_dir)
                text_preprocessor.run(sample_size=100)  # 处理所有数据
                print("✅ 医疗对话数据预处理完成")
            except Exception as e:
                print(f"⚠️  医疗对话数据预处理跳过: {e}")
                
        except Exception as e:
            print(f"❌ 文本数据预处理失败: {e}")
            success = False
        
        # 图像数据预处理
        print("\n--- 图像数据预处理 ---")
        try:
            data_dir = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/image_text_data/raw"
            
            image_preprocessor = MedicalImageTextPreprocessor(data_dir)
            image_preprocessor.run()
            print("✅ 图像数据预处理完成")
        except Exception as e:
            print(f"❌ 图像数据预处理失败: {e}")
            success = False
        
        if success:
            print("\n✅ 数据预处理完成")
            print("现在可以继续进行向量化...")
        
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

def run_multimodal_vectorization():
    """运行多模态向量化（核心功能）"""
    print("\n=== 开始多模态向量化 ===")
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
            build_multimodal=True  # 只构建多模态向量数据库
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
        from core.build_multimodal_database import UnifiedMultimodalRetrieval
        
        # 初始化统一检索系统
        retrieval_system = UnifiedMultimodalRetrieval()
        
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
        if not check_data_files():
            print("❌ 数据文件检查失败，请检查数据目录")
            return 1
    
    success = True
    
    if mode == "check":
        if not check_data_files():
            success = False
        if success:
            print("\n✅ 数据文件检查完成")
        return 0 if success else 1
    
    elif mode == "preprocess":
        if not run_data_preprocessing():
            success = False
    
    elif mode == "text":
        if not run_text_vectorization():
            success = False
    
    elif mode == "image":
        if not run_image_vectorization():
            success = False
    
    elif mode == "multimodal":
        if not run_multimodal_vectorization():
            success = False
    
    elif mode == "all":
        # 完整的处理流程：预处理 → 向量化
        print("\n🔄 执行完整处理流程：预处理 → 向量化")
        
        # 首先检查是否需要预处理
        base_data_dir = Path("/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge")
        processed_reports = base_data_dir / "image_text_data" / "processed" / "processed_reports.csv"
        processed_images = base_data_dir / "image_text_data" / "processed" / "processed_images.npy"
        general_text_train = base_data_dir / "text_data" / "processed" / "training_data" / "general_text_train.csv"
        general_text_test = base_data_dir / "text_data" / "processed" / "test_data" / "general_text_test.csv"
        
        # 检查所有类型的预处理数据
        needs_preprocessing = (
            not processed_reports.exists() or 
            not processed_images.exists() or
            not general_text_train.exists() or
            not general_text_test.exists()
        )
        
        if needs_preprocessing:
            print("⚠️  检测到缺少预处理数据，先进行数据预处理...")
            if not run_data_preprocessing():
                success = False
                print("❌ 数据预处理失败，无法继续向量化")
            else:
                print("✅ 数据预处理完成，开始向量化...")
        else:
            print("✅ 预处理数据已存在，直接进行向量化...")
        
        # 如果预处理成功或不需要预处理，继续向量化
        if success:
            # 只执行多模态向量化（优化版本）
            print("\n💡 优化说明: 已移除冗余的单独数据库构建，现在只构建多模态数据库")
            if not run_multimodal_vectorization():
                success = False
    
    elif mode == "test":
        if not run_unified_multimodal_retrieval_test():
            success = False
    
    if success:
        print("\n🎉 向量化任务执行成功！")
        print("\n📁 向量数据库位置:")
        base_data_dir = Path("/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge")
        print(f"  多模态向量数据库: {Path('/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas') / 'vector_databases' / 'multimodal'}")
        print(f"  图像-文本映射: {Path('/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas') / 'vector_databases' / 'multimodal' / 'image_text_mapping.json'}")
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
