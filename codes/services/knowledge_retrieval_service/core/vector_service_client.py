"""
向量化服务客户端
负责通过HTTP API调用向量化服务，实现文本和图像的向量化处理
"""

import os
import sys
import json
import logging
import requests
import numpy as np
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path

# 添加common模块到路径
current_file = Path(__file__)
common_dir = current_file.parent.parent.parent.parent / "common"
sys.path.insert(0, str(common_dir))

from common.log_config import setup_logging, get_logger
setup_logging("retrieval_service")
logger = get_logger(__name__)


class VectorServiceClient:
    """向量化服务客户端，通过HTTP API调用向量化服务"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化向量化服务客户端
        
        Args:
            config: 配置字典，包含向量化服务URL、超时等配置信息
        """
        self.config = config
        self.base_url = config.get('vectorization_service_url', 'http://localhost:8001')
        self.timeout = config.get('timeout', 300)
        self.retry_attempts = config.get('retry_attempts', 3)
        self.vector_dim = config.get('vector_dim', 768)
        
        # 检查向量化服务是否可用
        self._check_service_health()
    
    def _check_service_health(self):
        """检查向量化服务是否可用"""
        try:
            health_url = f"{self.base_url}/health"
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"向量化服务健康检查通过: {health_url}")
                return True
            else:
                logger.warning(f"向量化服务健康检查失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"向量化服务健康检查失败: {e}")
            return False
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送HTTP请求到向量化服务
        
        Args:
            endpoint: API端点
            payload: 请求数据
            
        Returns:
            响应数据
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"向向量化服务发送请求 (尝试 {attempt + 1}/{self.retry_attempts}): {url}")
                logger.info(f"请求参数: {payload}")
                
                response = requests.post(
                    url, 
                    json=payload, 
                    timeout=self.timeout,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"向量化服务响应成功: {result.get('message', '')}")
                    return result
                else:
                    logger.warning(f"向量化服务响应错误: {response.status_code} - {response.text}")
                    if attempt == self.retry_attempts - 1:
                        raise Exception(f"向量化服务响应错误: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"向量化服务请求超时 (尝试 {attempt + 1}/{self.retry_attempts})")
                if attempt == self.retry_attempts - 1:
                    raise Exception("向量化服务请求超时")
                    
            except requests.exceptions.ConnectionError:
                logger.warning(f"向量化服务连接失败 (尝试 {attempt + 1}/{self.retry_attempts})")
                if attempt == self.retry_attempts - 1:
                    raise Exception("向量化服务连接失败")
                    
            except Exception as e:
                logger.error(f"向量化服务请求失败: {e}")
                if attempt == self.retry_attempts - 1:
                    raise
        
        raise Exception("向量化服务请求失败，已达到最大重试次数")
    
    def text_to_vector(self, text: str) -> np.ndarray:
        """
        将文本转换为向量
        
        Args:
            text: 输入文本
            
        Returns:
            文本向量
        """
        start_time = datetime.now()
        process_id = f"client_vec_{start_time.strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            print("=" * 50)
            print("🔤 文本向量化开始 (通过API)")
            print("=" * 50)
            logger.info(f"🔤 [{process_id}] 开始客户端文本向量化")
            logger.info(f"📊 [{process_id}] 输入参数: text_length={len(text)} 字符")
            logger.info(f"📝 [{process_id}] 输入文本: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            
            # 1. 获取用户输入
            print("==========")
            print("获取用户输入开始")
            print("==========")
            logger.info(f"📥 [{process_id}] 获取用户输入: 文本长度={len(text)} 字符")
            logger.info(f"📝 [{process_id}] 文本内容: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            logger.info(f"✅ [{process_id}] 获取用户输入成功")
            print("获取用户输入结束")
            print("==========")
            
            # 2. 用户数据处理
            print("==========")
            print("用户数据处理开始")
            print("==========")
            logger.info(f"🔄 [{process_id}] 开始预处理文本")
            
            if not text or not text.strip():
                logger.warning(f"⚠️ [{process_id}] 空文本输入")
                return np.zeros(self.vector_dim)
            
            logger.info(f"✅ [{process_id}] 文本预处理完成，有效长度: {len(text.strip())} 字符")
            logger.info(f"✅ [{process_id}] 用户数据处理成功")
            print("==========")
            
            # 3. 调用向量化服务API
            print("==========")
            print("文本向量化开始")
            print("==========")
            logger.info(f"🚀 [{process_id}] 开始调用向量化服务API")
            
            payload = {
                "texts": [text],
                "chunk_strategy": "medical_structured",
                "preprocessing": True,
                "model_name": self.config.get('model_name', 'bge-large-zh-v1.5')
            }
            
            logger.info(f"📤 [{process_id}] 发送请求到向量化服务: payload_size={len(str(payload))} 字符")
            
            result = self._make_request("/api/v1/vectorize/text", payload)
            
            logger.info(f"📥 [{process_id}] 收到向量化服务响应: success={result.get('success', False)}")
            
            # 检查响应结构，支持嵌套的data字段
            if result.get('success'):
                # 尝试从data字段获取向量
                data = result.get('data', {})
                vectors = data.get('vectors') if data else result.get('vectors')
                
                if vectors and len(vectors) > 0:
                    vector = np.array(vectors[0])
                    
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    logger.info(f"✅ [{process_id}] 向量化完成")
                    logger.info(f"📈 [{process_id}] 处理结果: vector_dim={len(vector)}, processing_time={processing_time:.3f}s")
                    
                    # 记录向量统计信息
                    if hasattr(vector, '__len__') and len(vector) > 0:
                        vector_stats = {
                            'min': float(np.min(vector)),
                            'max': float(np.max(vector)),
                            'mean': float(np.mean(vector)),
                            'std': float(np.std(vector))
                        }
                        logger.info(f"📊 [{process_id}] 向量统计: min={vector_stats['min']:.4f}, max={vector_stats['max']:.4f}, mean={vector_stats['mean']:.4f}")
                    
                    logger.info("文本向量化成功")
                    print("文本向量化结束")
                    print("==========")
                    
                    # 4. 返回用户结果
                    print("==========")
                    print("返回用户结果开始")
                    print("==========")
                    logger.info(f"🎯 [{process_id}] 开始构建向量化结果")
                    logger.info(f"✅ [{process_id}] 向量化结果: 成功")
                    logger.info(f"🎉 [{process_id}] 返回用户结果成功")
                    print("返回用户结果结束")
                    print("==========")
                    
                    print("=" * 50)
                    print("🎉 文本向量化完成")
                    print("=" * 50)
                    logger.info(f"🏁 [{process_id}] 文本向量化成功完成")
                    
                    return vector
                else:
                    logger.error(f"❌ [{process_id}] 向量化服务返回的向量数据为空: {result}")
                    return np.zeros(self.vector_dim)
            else:
                error_msg = result.get('error', '未知错误')
                logger.error(f"❌ [{process_id}] 向量化服务返回错误: {error_msg}")
                return np.zeros(self.vector_dim)
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            print("=" * 50)
            print("❌ 文本向量化失败")
            print("=" * 50)
            logger.error(f"❌ [{process_id}] 客户端文本向量化失败: {e}")
            logger.error(f"⏱️ [{process_id}] 失败时间: {processing_time:.3f}s")
            return np.zeros(self.vector_dim)
    
    def image_to_vector(self, image_path: str) -> np.ndarray:
        """
        将图像转换为向量
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            图像向量
        """
        try:
            if not os.path.exists(image_path):
                logger.warning(f"Image file not found: {image_path}")
                return np.zeros(self.vector_dim)
            
            payload = {
                "image_paths": [image_path],
                "extract_text": True,
                "model_name": self.config.get('image_model_name', 'clip-vit-base-patch32')
            }
            
            result = self._make_request("/api/v1/vectorize/image", payload)
            
            if result.get('success') and result.get('vectors'):
                vector = np.array(result['vectors'][0])
                return vector
            else:
                logger.error(f"图像向量化服务返回错误: {result}")
                return np.zeros(self.vector_dim)
                
        except Exception as e:
            logger.error(f"Error converting image to vector: {e}")
            return np.zeros(self.vector_dim)
    
    def batch_text_to_vectors(self, texts: List[str]) -> np.ndarray:
        """
        批量将文本转换为向量
        
        Args:
            texts: 文本列表
            
        Returns:
            文本向量矩阵
        """
        try:
            if not texts:
                return np.array([])
            
            # 过滤空文本
            valid_texts = [text for text in texts if text and text.strip()]
            if not valid_texts:
                return np.zeros((len(texts), self.vector_dim))
            
            payload = {
                "texts": valid_texts,
                "chunk_strategy": "medical_structured",
                "preprocessing": True,
                "model_name": self.config.get('model_name', 'bge-large-zh-v1.5')
            }
            
            result = self._make_request("/api/v1/vectorize/text", payload)
            
            if result.get('success') and result.get('vectors'):
                vectors = np.array(result['vectors'])
                
                # 如果原始列表中有空文本，需要补齐
                if len(valid_texts) < len(texts):
                    full_vectors = np.zeros((len(texts), self.vector_dim))
                    valid_idx = 0
                    for i, text in enumerate(texts):
                        if text and text.strip():
                            full_vectors[i] = vectors[valid_idx]
                            valid_idx += 1
                    vectors = full_vectors
                
                return vectors
            else:
                logger.error(f"批量文本向量化服务返回错误: {result}")
                return np.zeros((len(texts), self.vector_dim))
                
        except Exception as e:
            logger.error(f"Error in batch text vectorization: {e}")
            return np.zeros((len(texts), self.vector_dim))
    
    def batch_image_to_vectors(self, image_paths: List[str]) -> np.ndarray:
        """
        批量将图像转换为向量
        
        Args:
            image_paths: 图像路径列表
            
        Returns:
            图像向量矩阵
        """
        try:
            if not image_paths:
                return np.array([])
            
            # 过滤有效图像路径
            valid_paths = [path for path in image_paths if os.path.exists(path)]
            if not valid_paths:
                return np.zeros((len(image_paths), self.vector_dim))
            
            payload = {
                "image_paths": valid_paths,
                "extract_text": True,
                "model_name": self.config.get('image_model_name', 'clip-vit-base-patch32')
            }
            
            result = self._make_request("/api/v1/vectorize/image", payload)
            
            if result.get('success') and result.get('vectors'):
                vectors = np.array(result['vectors'])
                
                # 补齐缺失的向量
                if len(valid_paths) < len(image_paths):
                    full_vectors = np.zeros((len(image_paths), self.vector_dim))
                    valid_idx = 0
                    for i, path in enumerate(image_paths):
                        if os.path.exists(path):
                            full_vectors[i] = vectors[valid_idx]
                            valid_idx += 1
                    vectors = full_vectors
                
                return vectors
            else:
                logger.error(f"批量图像向量化服务返回错误: {result}")
                return np.zeros((len(image_paths), self.vector_dim))
                
        except Exception as e:
            logger.error(f"Error in batch image vectorization: {e}")
            return np.zeros((len(image_paths), self.vector_dim))
    
    def multimodal_vectorize(self, texts: List[str] = None, image_paths: List[str] = None) -> np.ndarray:
        """
        多模态向量化
        
        Args:
            texts: 文本列表
            image_paths: 图像路径列表
            
        Returns:
            多模态向量
        """
        try:
            payload = {
                "texts": texts or [],
                "image_paths": image_paths or [],
                "fusion_method": "concat",
                "model_name": self.config.get('multimodal_model_name', 'multimodal-model')
            }
            
            result = self._make_request("/api/v1/vectorize/multimodal", payload)
            
            if result.get('success') and result.get('vectors'):
                vectors = np.array(result['vectors'])
                return vectors
            else:
                logger.error(f"多模态向量化服务返回错误: {result}")
                return np.zeros((1, self.vector_dim))
                
        except Exception as e:
            logger.error(f"Error in multimodal vectorization: {e}")
            return np.zeros((1, self.vector_dim))
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        获取向量化服务信息
        
        Returns:
            服务信息
        """
        try:
            result = self._make_request("/api/v1/info", {})
            return result
        except Exception as e:
            logger.error(f"Error getting service info: {e}")
            return {}
    
    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表
        
        Returns:
            模型列表
        """
        try:
            result = self._make_request("/api/v1/models", {})
            if result.get('success') and result.get('models'):
                return result['models']
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []


class VectorServiceClientFactory:
    """向量化服务客户端工厂类"""
    
    @staticmethod
    def create_vector_service_client(config_path: str = None) -> VectorServiceClient:
        """
        创建向量化服务客户端实例
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            向量化服务客户端实例
        """
        # 默认配置
        default_config = {
            'vectorization_service_url': 'http://localhost:8001',
            'timeout': 300,
            'retry_attempts': 3,
            'vector_dim': 768,
            'model_name': 'bge-large-zh-v1.5',
            'image_model_name': 'clip-vit-base-patch32',
            'multimodal_model_name': 'multimodal-model'
        }
        
        # 如果提供了配置文件，则加载配置
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Error loading config file: {e}, using default config")
        
        return VectorServiceClient(default_config)


if __name__ == "__main__":
    # 测试向量化服务客户端
    config = {
        'vectorization_service_url': 'http://localhost:8001',
        'timeout': 300,
        'retry_attempts': 3,
        'vector_dim': 768
    }
    
    client = VectorServiceClient(config)
    
    # 测试文本向量化
    test_text = "患者出现胸痛症状，持续3小时，伴有呼吸困难"
    vector = client.text_to_vector(test_text)
    print(f"Text vector shape: {vector.shape}")
    
    # 测试批量文本向量化
    test_texts = [
        "患者出现胸痛症状",
        "患者出现呼吸困难",
        "患者出现发热症状"
    ]
    vectors = client.batch_text_to_vectors(test_texts)
    print(f"Batch text vectors shape: {vectors.shape}")
    
    # 测试服务信息
    info = client.get_service_info()
    print(f"Service info: {info}")
    
    # 测试可用模型
    models = client.get_available_models()
    print(f"Available models: {models}")
