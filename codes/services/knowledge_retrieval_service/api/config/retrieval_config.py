"""
检索服务配置加载模块
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """
    加载检索服务配置
    
    Returns:
        配置字典
    """
    # 获取配置文件路径
    config_dir = Path(__file__).parent
    config_file = config_dir / "retrieval_config.json"
    
    # 默认配置
    default_config = {
        "vector_service": {
            "device": "cpu",
            "vector_dim": 512,
            "batch_size": 32,
            "text_model_path": "sentence-transformers/all-MiniLM-L6-v2",
            "image_model_path": "clip-ViT-B-32",
            "use_knowledge_base_service": True
        },
        "retrieval_service": {
            "vector_dim": 512,
            "max_results": 20,
            "similarity_threshold": 0.5,
            "retrieval_strategy": "semantic",
            "vector_db_path": "../../../datas/chroma_db",
            "collection_name": "medical_multimodal_vectors",
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "es_weight": 0.6,
            "vector_weight": 0.4,
            "rrf_k": 60,
            "max_es_results": 3,
            "max_vector_results": 3
        },
        "llm_service": {
            "device": "cpu",
            "model_path": "FreedomIntelligence/Apollo-0.5B",
            "max_length": 2048,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 50,
            "repetition_penalty": 1.1,
            "timeout": 600
        },
        "use_optimized_llm": True,
        "summarization_service": {
            "device": "cpu",
            "model_path": "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/codes/aimodels/Falconsai_text_summarization",
            "max_length": 100,
            "min_length": 30,
            "num_beams": 4,
            "temperature": 0.7,
            "early_stopping": True,
            "use_medical_summarization": True,
            "medical_max_length": 50,
            "timeout": 300
        },
        "vectorization_service": {
            "url": "http://localhost:8001",
            "timeout": 300,
            "retry_attempts": 3
        },
        "es_retrieval_service": {
            "url": "http://localhost:8004",
            "timeout": 300,
            "retry_attempts": 3,
            "enabled": True
        },
        "hybrid_retrieval_service": {
            "url": "http://localhost:8005",
            "timeout": 300,
            "retry_attempts": 3,
            "enabled": True
        },
        "api": {
            "host": "0.0.0.0",
            "port": 8002,
            "reload": True,
            "log_level": "info"
        }
    }
    
    # 如果配置文件存在，则加载
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            # 合并配置
            default_config.update(file_config)
            print(f"成功加载配置文件: {config_file}")
        except Exception as e:
            print(f"配置文件加载失败: {e}，使用默认配置")
    else:
        print(f"配置文件不存在: {config_file}，使用默认配置")
    
    return default_config
