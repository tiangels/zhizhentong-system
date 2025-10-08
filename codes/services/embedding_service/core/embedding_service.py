"""
智诊通向量化服务核心模块
整合文本、图像、多模态向量化功能
提供统一的向量化服务接口
"""

import os
import sys
import logging
from typing import List, Union, Optional, Dict, Any, Tuple
from pathlib import Path
import numpy as np
import torch
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "codes" / "services" / "embedding_service"))

# 导入配置管理器
from config.config_manager import get_config

# 导入向量化器
from embed.text_embedder import BiomedCLIPTextEmbedder, TextEmbedderFactory
from embed.image_embedder import UnifiedImageEmbedder, ImageEmbedderFactory

# 导入跨模态检索
from core.cross_modal_retrieval import CrossModalRetrieval

# 使用统一日志配置
import sys
from pathlib import Path

# 添加common模块到路径
current_file = Path(__file__)
common_dir = current_file.parent.parent.parent.parent / "common"
sys.path.insert(0, str(common_dir))

from log_config import setup_embedding_service_logging
logger = setup_embedding_service_logging()

class EmbeddingService:
    """
    智诊通向量化服务核心类
    整合文本、图像、多模态向量化功能
    """
    
    def __init__(self, device: str = "cpu"):
        """
        初始化向量化服务
        
        Args:
            device: 设备类型
        """
        self.device = device
        self.config = get_config()
        
        # 初始化嵌入器
        self.text_embedder = None
        self.image_embedder = None
        
        # 初始化跨模态检索
        self.cross_modal_retrieval = None
        
        self._initialize_embedders()
        self._initialize_retrieval()
    
    def _initialize_embedders(self):
        """初始化嵌入器"""
        try:
            # 初始化文本嵌入器
            self.text_embedder = TextEmbedderFactory.create_embedder(
                model_name="biomedclip",
                device=self.device
            )
            logger.info("文本嵌入器初始化成功")
            
            # 初始化图像嵌入器
            self.image_embedder = ImageEmbedderFactory.create_embedder(
                model_name="biomedclip",
                device=self.device
            )
            logger.info("图像嵌入器初始化成功")
            
        except Exception as e:
            logger.error(f"嵌入器初始化失败: {e}")
            raise
    
    def _initialize_retrieval(self):
        """初始化跨模态检索"""
        try:
            # 传递已经初始化的嵌入器给跨模态检索系统
            self.cross_modal_retrieval = CrossModalRetrieval(
                text_embedder=self.text_embedder,
                image_embedder=self.image_embedder
            )
            logger.info("跨模态检索系统初始化成功")
        except Exception as e:
            logger.warning(f"跨模态检索系统初始化失败: {e}")
            self.cross_modal_retrieval = None
    
    def vectorize_text(self, 
                      texts: List[str], 
                      chunk_strategy: str = "medical_structured",
                      preprocessing: bool = True) -> Dict[str, Any]:
        """
        文本向量化
        
        Args:
            texts: 文本列表
            chunk_strategy: 分块策略
            preprocessing: 是否预处理
            
        Returns:
            向量化结果
        """
        start_time = datetime.now()
        process_id = f"vec_{start_time.strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            logger.info(f"🔤 [{process_id}] 开始文本向量化处理")
            logger.info(f"📊 [{process_id}] 输入参数: texts_count={len(texts)}, chunk_strategy={chunk_strategy}, preprocessing={preprocessing}")
            
            if not self.text_embedder:
                logger.error(f"❌ [{process_id}] 文本嵌入器未初始化")
                raise ValueError("文本嵌入器未初始化")
            
            logger.info(f"✅ [{process_id}] 文本嵌入器状态正常")
            
            # 预处理文本
            if preprocessing:
                logger.info(f"🔄 [{process_id}] 开始文本预处理")
                processed_texts = self._preprocess_texts(texts, chunk_strategy)
                logger.info(f"✅ [{process_id}] 文本预处理完成: 原始={len(texts)}, 处理后={len(processed_texts)}")
                
                # 记录预处理详情
                for i, (original, processed) in enumerate(zip(texts, processed_texts)):
                    if original != processed:
                        logger.info(f"📝 [{process_id}] 文本 {i+1} 预处理: '{original[:50]}...' -> '{processed[:50]}...'")
            else:
                processed_texts = texts
                logger.info(f"⏭️ [{process_id}] 跳过文本预处理")
            
            # 向量化
            logger.info(f"🚀 [{process_id}] 开始向量化处理")
            vectors = []
            
            for i, text in enumerate(processed_texts):
                logger.info(f"🔄 [{process_id}] 处理文本 {i+1}/{len(processed_texts)}: 长度={len(text)} 字符")
                
                vector_start = datetime.now()
                vector = self.text_embedder.embed_query(text)
                vector_time = (datetime.now() - vector_start).total_seconds()
                
                vectors.append(vector)
                
                logger.info(f"✅ [{process_id}] 文本 {i+1} 向量化完成: 维度={len(vector)}, 耗时={vector_time:.3f}s")
                
                # 记录向量统计信息
                if hasattr(vector, '__len__') and len(vector) > 0:
                    vector_stats = {
                        'min': min(vector),
                        'max': max(vector),
                        'mean': sum(vector) / len(vector),
                        'std': np.std(vector) if hasattr(np, 'std') else 0
                    }
                    logger.info(f"📊 [{process_id}] 文本 {i+1} 向量统计: min={vector_stats['min']:.4f}, max={vector_stats['max']:.4f}, mean={vector_stats['mean']:.4f}")
            
            total_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": True,
                "vectors": vectors,
                "texts": processed_texts,
                "model_name": "biomedclip",
                "dimension": len(vectors[0]) if vectors else 0,
                "count": len(vectors)
            }
            
            logger.info(f"🎉 [{process_id}] 文本向量化全部完成")
            logger.info(f"📈 [{process_id}] 最终结果: vectors_count={len(vectors)}, dimension={result['dimension']}, total_time={total_time:.3f}s")
            
            return result
            
        except Exception as e:
            total_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ [{process_id}] 文本向量化失败: {e}")
            logger.error(f"⏱️ [{process_id}] 失败时间: {total_time:.3f}s")
            return {
                "success": False,
                "error": str(e),
                "vectors": [],
                "texts": texts
            }
    
    def vectorize_image(self, 
                       image_path: str,
                       preprocessing: bool = True) -> Dict[str, Any]:
        """
        图像向量化
        
        Args:
            image_path: 图像路径
            preprocessing: 是否预处理
            
        Returns:
            向量化结果
        """
        start_time = datetime.now()
        process_id = f"img_{start_time.strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            logger.info(f"🖼️ [{process_id}] 开始图像向量化处理")
            logger.info(f"📊 [{process_id}] 输入参数: image_path='{image_path}', preprocessing={preprocessing}")
            
            if not self.image_embedder:
                logger.error(f"❌ [{process_id}] 图像嵌入器未初始化")
                raise ValueError("图像嵌入器未初始化")
            
            logger.info(f"✅ [{process_id}] 图像嵌入器状态正常")
            
            # 检查图像文件是否存在
            if not os.path.exists(image_path):
                logger.error(f"❌ [{process_id}] 图像文件不存在: {image_path}")
                raise FileNotFoundError(f"图像文件不存在: {image_path}")
            
            logger.info(f"✅ [{process_id}] 图像文件存在，开始向量化")
            
            # 获取图像文件信息
            file_size = os.path.getsize(image_path)
            logger.info(f"📁 [{process_id}] 图像文件信息: 大小={file_size} bytes")
            
            # 向量化
            vector_start = datetime.now()
            vector = self.image_embedder.embed_image(image_path)
            vector_time = (datetime.now() - vector_start).total_seconds()
            
            total_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": True,
                "vector": vector,
                "image_path": image_path,
                "model_name": "biomedclip",
                "dimension": len(vector)
            }
            
            logger.info(f"🎉 [{process_id}] 图像向量化完成")
            logger.info(f"📈 [{process_id}] 处理结果: dimension={len(vector)}, vector_time={vector_time:.3f}s, total_time={total_time:.3f}s")
            
            # 记录向量统计信息
            if hasattr(vector, '__len__') and len(vector) > 0:
                vector_stats = {
                    'min': min(vector),
                    'max': max(vector),
                    'mean': sum(vector) / len(vector),
                    'std': np.std(vector) if hasattr(np, 'std') else 0
                }
                logger.info(f"📊 [{process_id}] 向量统计: min={vector_stats['min']:.4f}, max={vector_stats['max']:.4f}, mean={vector_stats['mean']:.4f}")
            
            return result
            
        except Exception as e:
            total_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ [{process_id}] 图像向量化失败: {e}")
            logger.error(f"⏱️ [{process_id}] 失败时间: {total_time:.3f}s")
            return {
                "success": False,
                "error": str(e),
                "vector": None,
                "image_path": image_path
            }
    
    def vectorize_multimodal(self, 
                           texts: List[str] = None,
                           image_paths: List[str] = None,
                           chunk_strategy: str = "medical_structured",
                           preprocessing: bool = True) -> Dict[str, Any]:
        """
        多模态向量化
        
        Args:
            texts: 文本列表
            image_paths: 图像路径列表
            chunk_strategy: 分块策略
            preprocessing: 是否预处理
            
        Returns:
            多模态向量化结果
        """
        try:
            results = {
                "success": True,
                "text_vectors": [],
                "image_vectors": [],
                "combined_vectors": [],
                "texts": texts or [],
                "image_paths": image_paths or [],
                "model_name": "biomedclip",
                "dimension": 0,
                "count": 0
            }
            
            # 文本向量化
            if texts:
                text_result = self.vectorize_text(texts, chunk_strategy, preprocessing)
                if text_result["success"]:
                    results["text_vectors"] = text_result["vectors"]
                    results["texts"] = text_result["texts"]
                    results["dimension"] = text_result["dimension"]
                else:
                    results["success"] = False
                    results["error"] = f"文本向量化失败: {text_result.get('error', '未知错误')}"
                    return results
            
            # 图像向量化
            if image_paths:
                image_vectors = []
                for image_path in image_paths:
                    image_result = self.vectorize_image(image_path, preprocessing)
                    if image_result["success"]:
                        image_vectors.append(image_result["vector"])
                    else:
                        results["success"] = False
                        results["error"] = f"图像向量化失败: {image_result.get('error', '未知错误')}"
                        return results
                
                results["image_vectors"] = image_vectors
                if not results["dimension"]:
                    results["dimension"] = len(image_vectors[0]) if image_vectors else 0
            
            # 合并向量
            all_vectors = results["text_vectors"] + results["image_vectors"]
            results["combined_vectors"] = all_vectors
            results["count"] = len(all_vectors)
            
            return results
            
        except Exception as e:
            logger.error(f"多模态向量化失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "text_vectors": [],
                "image_vectors": [],
                "combined_vectors": [],
                "texts": texts or [],
                "image_paths": image_paths or []
            }
    
    def _preprocess_texts(self, texts: List[str], chunk_strategy: str) -> List[str]:
        """
        预处理文本
        
        Args:
            texts: 原始文本列表
            chunk_strategy: 分块策略
            
        Returns:
            预处理后的文本列表
        """
        try:
            # 这里可以添加文本预处理逻辑
            # 例如：分块、清洗、标准化等
            processed_texts = []
            
            for text in texts:
                # 基础预处理
                text = text.strip()
                if text:
                    processed_texts.append(text)
            
            return processed_texts
            
        except Exception as e:
            logger.error(f"文本预处理失败: {e}")
            return texts
    
    def get_available_models(self) -> Dict[str, Any]:
        """
        获取可用模型列表
        
        Returns:
            可用模型信息
        """
        try:
            models = {
                "text_models": [
                    {
                        "name": "biomedclip",
                        "description": "BiomedCLIP文本嵌入模型",
                        "dimension": 512,
                        "language": "multilingual"
                    }
                ],
                "image_models": [
                    {
                        "name": "biomedclip",
                        "description": "BiomedCLIP图像嵌入模型",
                        "dimension": 512,
                        "supported_formats": ["jpg", "jpeg", "png", "bmp", "tiff"]
                    }
                ],
                "multimodal_models": [
                    {
                        "name": "biomedclip",
                        "description": "BiomedCLIP多模态嵌入模型",
                        "dimension": 512,
                        "supports": ["text", "image"]
                    }
                ]
            }
            
            return {
                "success": True,
                "models": models,
                "total_models": len(models["text_models"]) + len(models["image_models"]) + len(models["multimodal_models"])
            }
            
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "models": {}
            }
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        获取服务信息
        
        Returns:
            服务信息
        """
        try:
            info = {
                "service_name": "智诊通向量化服务",
                "version": "1.0.0",
                "device": self.device,
                "status": "running",
                "text_embedder_available": self.text_embedder is not None,
                "image_embedder_available": self.image_embedder is not None,
                "timestamp": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "info": info
            }
            
        except Exception as e:
            logger.error(f"获取服务信息失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "info": {}
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态
        """
        try:
            # 检查嵌入器状态
            text_ok = self.text_embedder is not None
            image_ok = self.image_embedder is not None
            
            # 简单测试
            if text_ok:
                try:
                    test_vector = self.text_embedder.embed_documents(["测试"])[0]
                    text_ok = len(test_vector) > 0
                except:
                    text_ok = False
            
            if image_ok:
                # 图像嵌入器测试需要实际图像文件，这里只检查初始化状态
                pass
            
            status = "healthy" if (text_ok or image_ok) else "unhealthy"
            
            return {
                "success": True,
                "status": status,
                "text_embedder": "ok" if text_ok else "error",
                "image_embedder": "ok" if image_ok else "error",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "success": False,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def cleanup(self):
        """
        清理资源
        在服务关闭时调用，释放内存和资源
        """
        try:
            logger.info("🔄 开始清理向量化服务资源...")
            
            # 清理嵌入器
            if self.text_embedder:
                try:
                    # 如果嵌入器有清理方法，调用它
                    if hasattr(self.text_embedder, 'cleanup'):
                        await self.text_embedder.cleanup()
                    elif hasattr(self.text_embedder, 'close'):
                        self.text_embedder.close()
                    logger.info("✅ 文本嵌入器清理完成")
                except Exception as e:
                    logger.warning(f"⚠️ 文本嵌入器清理失败: {e}")
                
                self.text_embedder = None
            
            if self.image_embedder:
                try:
                    # 如果嵌入器有清理方法，调用它
                    if hasattr(self.image_embedder, 'cleanup'):
                        await self.image_embedder.cleanup()
                    elif hasattr(self.image_embedder, 'close'):
                        self.image_embedder.close()
                    logger.info("✅ 图像嵌入器清理完成")
                except Exception as e:
                    logger.warning(f"⚠️ 图像嵌入器清理失败: {e}")
                
                self.image_embedder = None
            
            # 清理GPU内存
            if torch.cuda.is_available():
                try:
                    torch.cuda.empty_cache()
                    logger.info("✅ GPU内存清理完成")
                except Exception as e:
                    logger.warning(f"⚠️ GPU内存清理失败: {e}")
            
            logger.info("✅ 向量化服务资源清理完成")
            
        except Exception as e:
            logger.error(f"❌ 向量化服务资源清理失败: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取向量化服务统计信息
        
        Returns:
            统计信息字典
        """
        try:
            stats = {
                "service_name": "EmbeddingService",
                "status": "running",
                "device": self.device,
                "models": {
                    "text_embedder": {
                        "name": "biomedclip",
                        "status": "loaded" if self.text_embedder else "not_loaded"
                    },
                    "image_embedder": {
                        "name": "biomedclip", 
                        "status": "loaded" if self.image_embedder else "not_loaded"
                    }
                },
                "capabilities": [
                    "text_vectorization",
                    "image_vectorization", 
                    "multimodal_vectorization",
                    "document_retrieval"
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ 向量化服务统计信息获取成功")
            return stats
            
        except Exception as e:
            logger.error(f"❌ 向量化服务统计信息获取失败: {e}")
            return {
                "service_name": "EmbeddingService",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def retrieve_documents(self, 
                          query: str, 
                          top_k: int = 5, 
                          retrieval_type: str = "text",
                          similarity_threshold: float = 0.3) -> Dict[str, Any]:
        """
        文档检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            retrieval_type: 检索类型 (text, image, multimodal)
            similarity_threshold: 相似度阈值
            
        Returns:
            检索结果
        """
        start_time = datetime.now()
        process_id = f"ret_{start_time.strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            logger.info(f"🔍 [{process_id}] 开始文档检索处理")
            logger.info(f"📊 [{process_id}] 检索参数: query='{query}', top_k={top_k}, retrieval_type={retrieval_type}, similarity_threshold={similarity_threshold}")
            
            if not self.cross_modal_retrieval:
                logger.error(f"❌ [{process_id}] 跨模态检索系统未初始化")
                raise ValueError("跨模态检索系统未初始化")
            
            logger.info(f"✅ [{process_id}] 跨模态检索系统状态正常")
            
            # 执行检索
            logger.info(f"🚀 [{process_id}] 开始执行检索")
            
            if retrieval_type == "text":
                logger.info(f"📝 [{process_id}] 执行文本检索")
                results = self.cross_modal_retrieval.search(query=query, top_k=top_k)
                logger.info(f"✅ [{process_id}] 文本检索完成: 原始结果数={len(results)}")
                
            elif retrieval_type == "image":
                logger.warning(f"⚠️ [{process_id}] 图像检索需要图像路径，暂不支持纯文本查询")
                results = []
                
            else:  # multimodal
                logger.info(f"🔄 [{process_id}] 执行多模态检索")
                results = self.cross_modal_retrieval.search(query=query, top_k=top_k)
                logger.info(f"✅ [{process_id}] 多模态检索完成: 原始结果数={len(results)}")
            
            # 过滤相似度阈值
            logger.info(f"🔍 [{process_id}] 开始相似度过滤: threshold={similarity_threshold}")
            filtered_results = []
            
            for i, result in enumerate(results):
                similarity_score = result.get('similarity_score', 0)
                logger.info(f"📊 [{process_id}] 结果 {i+1}: 相似度={similarity_score:.4f}")
                
                if similarity_score >= similarity_threshold:
                    filtered_results.append(result)
                    logger.info(f"✅ [{process_id}] 结果 {i+1} 通过阈值过滤")
                else:
                    logger.info(f"❌ [{process_id}] 结果 {i+1} 未通过阈值过滤")
            
            total_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"🎉 [{process_id}] 文档检索全部完成")
            logger.info(f"📈 [{process_id}] 最终结果: 原始结果={len(results)}, 过滤后结果={len(filtered_results)}, total_time={total_time:.3f}s")
            
            # 记录每个检索结果的详情
            if filtered_results:
                logger.info(f"🔍 [{process_id}] 检索结果详情:")
                for i, result in enumerate(filtered_results[:3]):  # 只记录前3个结果的详情
                    content_preview = result.get('content', '')[:50]
                    similarity = result.get('similarity_score', 0)
                    logger.info(f"   📄 [{process_id}] 结果 {i+1}: 相似度={similarity:.4f}, 内容='{content_preview}...'")
            
            return {
                "query": query,
                "results": filtered_results,
                "total_found": len(filtered_results),
                "retrieval_type": retrieval_type,
                "similarity_threshold": similarity_threshold
            }
            
        except Exception as e:
            total_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ [{process_id}] 文档检索失败: {e}")
            logger.error(f"⏱️ [{process_id}] 失败时间: {total_time:.3f}s")
            return {
                "query": query,
                "results": [],
                "total_found": 0,
                "retrieval_type": retrieval_type,
                "similarity_threshold": similarity_threshold,
                "error": str(e)
            }
