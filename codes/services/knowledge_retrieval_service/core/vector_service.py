"""
向量服务模块
负责通过HTTP API调用向量化服务，为知识检索提供向量表示
注意：此模块不包含向量化构建功能，只负责调用向量化服务API
"""

import os
import sys
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

# 使用统一日志配置
import sys
from pathlib import Path

# 添加common模块到路径
current_file = Path(__file__)
common_dir = current_file.parent.parent.parent.parent / "common"
sys.path.insert(0, str(common_dir))

# 添加项目根目录到路径
import sys
from pathlib import Path
current_file = Path(__file__)
project_root = current_file.parent.parent.parent.parent  # 回到codes目录
sys.path.insert(0, str(project_root))

from common.log_config import setup_logging, get_logger
setup_logging("retrieval_service")
logger = get_logger(__name__)

# 导入向量化服务客户端
from .vector_service_client import VectorServiceClient, VectorServiceClientFactory


class VectorService:
    """向量服务类，负责通过HTTP API调用向量化服务"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化向量服务
        
        Args:
            config: 配置字典，包含向量化服务URL、超时等配置信息
        """
        self.config = config
        self.vectorization_client = None
        self._init_vectorization_client()
    
    def _init_vectorization_client(self):
        """初始化向量化服务客户端"""
        try:
            # 创建向量化服务客户端
            self.vectorization_client = VectorServiceClientFactory.create_client(self.config)
            logger.info("向量化服务客户端初始化成功")
        except Exception as e:
            logger.error(f"向量化服务客户端初始化失败: {e}")
            self.vectorization_client = None
    
    def text_to_vectors(self, texts: List[str]) -> np.ndarray:
        """
        将文本转换为向量
        
        Args:
            texts: 文本列表
            
        Returns:
            np.ndarray: 向量矩阵
        """
        try:
            if not self.vectorization_client:
                logger.error("向量化服务客户端未初始化")
                return np.array([])
            
            # 调用向量化服务API
            vectors = self.vectorization_client.batch_text_to_vectors(texts)
            logger.info(f"成功向量化 {len(texts)} 个文本")
            return vectors
            
        except Exception as e:
            logger.error(f"文本向量化失败: {e}")
            return np.array([])
    
    def image_to_vectors(self, image_paths: List[str]) -> np.ndarray:
        """
        将图像转换为向量
        
        Args:
            image_paths: 图像路径列表
            
        Returns:
            np.ndarray: 向量矩阵
        """
        try:
            if not self.vectorization_client:
                logger.error("向量化服务客户端未初始化")
                return np.array([])
            
            # 调用向量化服务API
            vectors = self.vectorization_client.batch_image_to_vectors(image_paths)
            logger.info(f"成功向量化 {len(image_paths)} 个图像")
            return vectors
            
        except Exception as e:
            logger.error(f"图像向量化失败: {e}")
            return np.array([])
    
    def multimodal_to_vectors(self, texts: List[str] = None, image_paths: List[str] = None) -> np.ndarray:
        """
        多模态向量化
        
        Args:
            texts: 文本列表
            image_paths: 图像路径列表
            
        Returns:
            np.ndarray: 向量矩阵
        """
        try:
            if not self.vectorization_client:
                logger.error("向量化服务客户端未初始化")
                return np.array([])
            
            # 调用向量化服务API
            vectors = self.vectorization_client.multimodal_vectorize(texts, image_paths)
            logger.info(f"成功多模态向量化")
            return vectors
            
        except Exception as e:
            logger.error(f"多模态向量化失败: {e}")
            return np.array([])
    
    def search_similar_vectors(self, query_vector: np.ndarray, top_k: int = 10) -> tuple:
        """
        在向量数据库中搜索相似向量
        
        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            
        Returns:
            tuple: (相似向量, 相似度分数)
        """
        try:
            if not self.vectorization_client:
                logger.error("向量化服务客户端未初始化")
                return np.array([]), np.array([])
            
            # 调用向量化服务API进行搜索
            results = self.vectorization_client.search_similar_vectors(query_vector, top_k)
            logger.info(f"成功搜索到 {len(results[0])} 个相似向量")
            return results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return np.array([]), np.array([])
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态
        
        Returns:
            Dict: 服务状态信息
        """
        try:
            if not self.vectorization_client:
                return {
                    'status': 'error',
                    'message': '向量化服务客户端未初始化',
                    'vectorization_service_available': False
                }
            
            # 调用向量化服务API获取状态
            status = self.vectorization_client.get_service_status()
            return {
                'status': 'healthy',
                'vectorization_service_available': True,
                'vectorization_service_status': status
            }
            
        except Exception as e:
            logger.error(f"获取服务状态失败: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'vectorization_service_available': False
            }


class VectorServiceFactory:
    """向量服务工厂类"""
    
    @staticmethod
    def create_vector_service(config_path: str = None) -> VectorService:
        """
        创建向量服务实例
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            VectorService: 向量服务实例
        """
        try:
            # 加载配置
            if config_path and os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                # 使用默认配置
                config = {
                    'vectorization_service': {
                        'url': 'http://localhost:8001',
                        'timeout': 30
                    }
                }
            
            # 创建向量服务实例
            vector_service = VectorService(config)
            logger.info("向量服务创建成功")
            return vector_service
            
        except Exception as e:
            logger.error(f"创建向量服务失败: {e}")
            raise


# 全局向量服务实例
_vector_service_instance = None

def get_vector_service(config_path: str = None) -> VectorService:
    """
    获取全局向量服务实例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        VectorService: 向量服务实例
    """
    global _vector_service_instance
    
    if _vector_service_instance is None:
        _vector_service_instance = VectorServiceFactory.create_vector_service(config_path)
    
    return _vector_service_instance


def clear_vector_service():
    """清除全局向量服务实例"""
    global _vector_service_instance
    _vector_service_instance = None