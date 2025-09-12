#!/usr/bin/env conda run -n nlp python
"""
向量化服务主入口
提供统一的向量化服务接口
"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from codes.ai_models.embedding_models.core.vectorization_service import VectorizationService
from codes.ai_models.embedding_models.processors.data_pipeline import DataPipeline


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="向量化服务")
    parser.add_argument("--mode", choices=["image", "text", "multimodal", "analyze", "build_db", "pipeline", "status"], 
                       required=True, help="运行模式")
    parser.add_argument("--input", type=str, help="输入文件或目录")
    parser.add_argument("--output", type=str, help="输出目录")
    parser.add_argument("--config", type=str, default="config/unified_config.json", 
                       help="配置文件路径")
    parser.add_argument("--texts", type=str, nargs="+", help="文本列表（多模态模式）")
    parser.add_argument("--images", type=str, nargs="+", help="图像路径列表（多模态模式）")
    
    args = parser.parse_args()
    
    # 初始化服务
    try:
        service = VectorizationService(args.config)
        pipeline = DataPipeline()
    except Exception as e:
        print(f"服务初始化失败: {e}")
        return
    
    if args.mode == "image":
        print("启动图像向量化服务...")
        if args.input:
            vectors = service.process_images(args.input, args.output)
            print(f"图像向量化完成，向量形状: {vectors.shape}")
    
    elif args.mode == "text":
        print("启动文本向量化服务...")
        if args.input:
            vectors = service.process_texts(args.input, args.output)
            print(f"文本向量化完成，向量形状: {vectors.shape}")
    
    elif args.mode == "multimodal":
        print("启动多模态向量化服务...")
        if args.texts and args.images:
            result = service.process_multimodal(args.texts, args.images, args.output)
            print(f"多模态向量化完成，文本向量形状: {result['text_vectors'].shape}, 图像向量形状: {result['image_vectors'].shape}")
    
    elif args.mode == "analyze":
        print("启动数据分析服务...")
        if args.input:
            result = service.analyze_data(args.input)
            print(f"数据分析完成: {result}")
    
    elif args.mode == "pipeline":
        print("启动数据处理管道...")
        if args.input and args.output:
            result = pipeline.process_vqa_dataset(args.input, args.output)
            print(f"数据处理完成: {result}")
    
    elif args.mode == "build_db":
        print("构建向量数据库...")
        if args.input and args.output:
            success = service.build_vector_database(args.input, args.output)
            print(f"向量数据库构建{'成功' if success else '失败'}")
    
    elif args.mode == "status":
        print("获取服务状态...")
        status = service.get_service_status()
        pipeline_status = pipeline.get_pipeline_status()
        print(f"向量化服务状态: {status}")
        print(f"数据处理管道状态: {pipeline_status}")


if __name__ == "__main__":
    main()
