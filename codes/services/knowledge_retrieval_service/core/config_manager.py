"""
统一配置管理模块
负责管理RAG系统的所有配置，确保构建知识库模块和检索生成模块使用一致的配置
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """统一配置管理器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        current_dir = Path(__file__).parent
        return str(current_dir.parent / "api" / "config" / "rag_config.json")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"成功加载配置文件: {self.config_path}")
                return config
            else:
                logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "vector_service": {
                "device": "auto",
                "vector_dim": 768,
                "batch_size": 32,
                "text_model_path": "../../../codes/ai_models/llm_models/text2vec-base-chinese",
                "image_model_path": "clip-ViT-B-32",
                "use_knowledge_base_service": True
            },
            "retrieval_service": {
                "vector_dim": 768,
                "max_results": 20,
                "similarity_threshold": 0.7,
                "retrieval_strategy": "semantic",
                "vector_db_path": "../../../datas/vector_databases/multimodal",
                "collection_name": "medical_multimodal_vectors",
                "model_name": "shibing624/text2vec-base-chinese"
            },
            "llm_service": {
                "device": "auto",
                "model_path": "../../../ai_models/llm_models/Qwen2-0.5B-Medical-MLX",
                "max_length": 2048,
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 50,
                "repetition_penalty": 1.1,
                "timeout": 600,
                "model_config_path": "../../../ai_models/llm_models/model_config.json"
            },
            "knowledge_base": {
                "base_dir": "../../../datas/medical_knowledge",
                "text_data_dir": "text_data",
                "image_data_dir": "image_text_data",
                "voice_data_dir": "voice_data",
                "vector_db_dir": "vector_databases"
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "reload": True,
                "log_level": "info"
            }
        }
    
    def get_vector_service_config(self) -> Dict[str, Any]:
        """获取向量化服务配置"""
        return self.config.get("vector_service", {})
    
    def get_retrieval_service_config(self) -> Dict[str, Any]:
        """获取检索服务配置"""
        return self.config.get("retrieval_service", {})
    
    def get_llm_service_config(self) -> Dict[str, Any]:
        """获取LLM服务配置"""
        return self.config.get("llm_service", {})
    
    def get_knowledge_base_config(self) -> Dict[str, Any]:
        """获取知识库配置"""
        return self.config.get("knowledge_base", {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return self.config.get("api", {})
    
    def get_model_path(self, model_type: str) -> str:
        """
        获取模型路径
        
        Args:
            model_type: 模型类型 (text, image, llm)
            
        Returns:
            模型路径
        """
        if model_type == "text":
            return self.get_vector_service_config().get("text_model_path", "")
        elif model_type == "image":
            return self.get_vector_service_config().get("image_model_path", "")
        elif model_type == "llm":
            return self.get_llm_service_config().get("model_path", "")
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
    
    def get_vector_db_path(self) -> str:
        """获取向量数据库路径"""
        return self.get_retrieval_service_config().get("vector_db_path", "")
    
    def get_knowledge_base_path(self, data_type: str) -> str:
        """
        获取知识库数据路径
        
        Args:
            data_type: 数据类型 (text, image, voice, vector_db)
            
        Returns:
            数据路径
        """
        base_dir = self.get_knowledge_base_config().get("base_dir", "")
        
        if data_type == "text":
            return os.path.join(base_dir, self.get_knowledge_base_config().get("text_data_dir", "text_data"))
        elif data_type == "image":
            return os.path.join(base_dir, self.get_knowledge_base_config().get("image_data_dir", "image_text_data"))
        elif data_type == "voice":
            return os.path.join(base_dir, self.get_knowledge_base_config().get("voice_data_dir", "voice_data"))
        elif data_type == "vector_db":
            return os.path.join(base_dir, self.get_knowledge_base_config().get("vector_db_dir", "vector_databases"))
        else:
            raise ValueError(f"不支持的数据类型: {data_type}")
    
    def update_config(self, section: str, key: str, value: Any):
        """
        更新配置
        
        Args:
            section: 配置节
            key: 配置键
            value: 配置值
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        logger.info(f"更新配置: {section}.{key} = {value}")
    
    def save_config(self, config_path: str = None):
        """
        保存配置到文件
        
        Args:
            config_path: 保存路径
        """
        save_path = config_path or self.config_path
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"配置已保存到: {save_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise
    
    def validate_config(self) -> bool:
        """
        验证配置的有效性
        
        Returns:
            配置是否有效
        """
        try:
            # 检查必要的配置项
            required_sections = ["vector_service", "retrieval_service", "llm_service"]
            for section in required_sections:
                if section not in self.config:
                    logger.error(f"缺少必要的配置节: {section}")
                    return False
            
            # 检查向量化服务配置
            vector_config = self.get_vector_service_config()
            if not vector_config.get("text_model_path"):
                logger.error("缺少文本模型路径配置")
                return False
            
            # 检查LLM服务配置
            llm_config = self.get_llm_service_config()
            if not llm_config.get("model_path"):
                logger.error("缺少LLM模型路径配置")
                return False
            
            logger.info("配置验证通过")
            return True
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要
        
        Returns:
            配置摘要信息
        """
        return {
            "config_path": self.config_path,
            "vector_model": self.get_model_path("text"),
            "llm_model": self.get_model_path("llm"),
            "vector_db_path": self.get_vector_db_path(),
            "knowledge_base_path": self.get_knowledge_base_path("vector_db"),
            "is_valid": self.validate_config()
        }


# 全局配置管理器实例
config_manager = ConfigManager()


if __name__ == "__main__":
    # 测试配置管理器
    manager = ConfigManager()
    
    print("配置摘要:")
    summary = manager.get_config_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n向量化服务配置:")
    vector_config = manager.get_vector_service_config()
    for key, value in vector_config.items():
        print(f"  {key}: {value}")
    
    print("\n检索服务配置:")
    retrieval_config = manager.get_retrieval_service_config()
    for key, value in retrieval_config.items():
        print(f"  {key}: {value}")
    
    print("\nLLM服务配置:")
    llm_config = manager.get_llm_service_config()
    for key, value in llm_config.items():
        print(f"  {key}: {value}")
