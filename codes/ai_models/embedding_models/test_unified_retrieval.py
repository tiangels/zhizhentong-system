#!/usr/bin/env python3
"""
统一多模态检索系统测试脚本
测试新的统一检索接口
"""

import os
import sys
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_unified_retrieval():
    """测试统一多模态检索系统"""
    print("=" * 60)
    print("🧪 统一多模态检索系统测试")
    print("=" * 60)
    
    try:
        # 导入统一检索系统
        from core.build_multimodal_database import UnifiedMultimodalRetrieval
        
        print("✅ 成功导入统一多模态检索系统")
        
        # 初始化检索系统
        print("\n🔄 初始化检索系统...")
        retrieval_system = UnifiedMultimodalRetrieval()
        print("✅ 检索系统初始化成功")
        
        # 测试文本检索
        print("\n📝 测试文本检索...")
        text_queries = [
            "心脏增大",
            "肺部感染",
            "右眼流眼泪",
            "胸部X光片检查结果"
        ]
        
        for query in text_queries:
            print(f"\n查询: '{query}'")
            results = retrieval_system.search(query=query, top_k=3)
            
            print(f"找到 {len(results)} 个相关结果:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. 相似度: {result['similarity_score']:.4f}")
                print(f"     内容: {result['content'][:80]}...")
                print(f"     UID: {result['uid']}")
                print(f"     类型: {result['content_type']}")
                print(f"     来源: {result['source']}")
        
        # 测试图像检索
        print("\n🖼️  测试图像检索...")
        test_image_path = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/image_text_data/raw/chestX-rays/images"
        
        if os.path.exists(test_image_path):
            image_files = [f for f in os.listdir(test_image_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
            if image_files:
                test_image = os.path.join(test_image_path, image_files[0])
                print(f"使用测试图像: {os.path.basename(test_image)}")
                
                image_results = retrieval_system.search(image_path=test_image, top_k=3)
                
                print(f"图像检索找到 {len(image_results)} 个相关结果:")
                for i, result in enumerate(image_results, 1):
                    print(f"  {i}. 相似度: {result['similarity_score']:.4f}")
                    print(f"     内容: {result['content'][:80]}...")
                    print(f"     UID: {result['uid']}")
                    print(f"     类型: {result['content_type']}")
                    print(f"     来源: {result['source']}")
            else:
                print("❌ 未找到测试图像文件")
        else:
            print("❌ 测试图像目录不存在")
        
        # 测试混合检索
        print("\n🔄 测试混合检索（文本+图像）...")
        if os.path.exists(test_image_path):
            image_files = [f for f in os.listdir(test_image_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
            if image_files:
                test_image = os.path.join(test_image_path, image_files[0])
                mixed_results = retrieval_system.search(
                    query="胸部检查",
                    image_path=test_image,
                    top_k=5
                )
                
                print(f"混合检索找到 {len(mixed_results)} 个相关结果:")
                for i, result in enumerate(mixed_results, 1):
                    print(f"  {i}. 相似度: {result['similarity_score']:.4f}")
                    print(f"     内容: {result['content'][:60]}...")
                    print(f"     UID: {result['uid']}")
                    print(f"     类型: {result['content_type']}")
        
        print("\n🎉 统一多模态检索系统测试完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("智诊通系统 - 统一多模态检索测试")
    print("=" * 60)
    
    # 检查多模态数据库是否存在
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, "..", "..", "..")
    multimodal_db_path = os.path.join(project_root, "datas", "vector_databases", "multimodal")
    if not os.path.exists(multimodal_db_path):
        print("❌ 多模态向量数据库不存在，请先运行向量化脚本")
        print("   运行命令: python run_vectorization.py --multimodal")
        return 1
    
    # 运行测试
    success = test_unified_retrieval()
    
    if success:
        print("\n✅ 所有测试通过！")
        print("\n📋 系统优势:")
        print("  • 统一的检索接口，支持文本和图像查询")
        print("  • 自动去重和结果排序")
        print("  • 基于多模态向量数据库的高效检索")
        print("  • 支持跨模态检索（图像→文本）")
        return 0
    else:
        print("\n❌ 测试失败，请检查系统配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())
