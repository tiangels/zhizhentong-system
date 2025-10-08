"""
知识检索管道模块
整合向量化服务、检索服务和大语言模型服务，实现完整的知识检索流程
"""

import os
import json
import logging
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, AsyncGenerator
from pathlib import Path
from datetime import datetime

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

# 导入核心服务
from .retrieval_service import RetrievalService, RetrievalServiceFactory
from .llm_service import LLMService, LLMServiceFactory
from .vector_service_client import VectorServiceClient
from .conversation_memory_service import ConversationMemoryService
from .config_manager import ConfigManager


class KnowledgeRetrievalPipeline:
    """知识检索管道，整合所有服务实现完整的RAG流程"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化知识检索管道
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.retrieval_service = None
        self.llm_service = None
        self.vectorization_client = None
        self.conversation_memory = None
        
        # 初始化各个服务
        self._init_services()
    
    def _init_services(self):
        """初始化各个服务组件"""
        try:
            logger.info("初始化知识检索管道服务...")
            
            # 初始化检索服务
            retrieval_config = self.config.get('retrieval', {})
            logger.info(f"检索服务配置: {retrieval_config}")
            self.retrieval_service = RetrievalServiceFactory.create_retrieval_service()
            logger.info("检索服务初始化完成")
            
            # 初始化LLM服务
            llm_config = self.config.get('llm', {})
            self.llm_service = LLMServiceFactory.create_llm_service(config_dict=llm_config)
            logger.info("LLM服务初始化完成")
            
            # 初始化向量化服务客户端
            vector_config = self.config.get('vectorization', {})
            self.vectorization_client = VectorServiceClient(vector_config)
            logger.info("向量化服务客户端初始化完成")
            
            # 初始化对话记忆服务
            memory_config = self.config.get('memory', {})
            self.conversation_memory = ConversationMemoryService(memory_config)
            logger.info("对话记忆服务初始化完成")
            
            logger.info("知识检索管道初始化完成")
            
        except Exception as e:
            logger.error(f"初始化知识检索管道失败: {e}")
            raise
    
    def query(self, question: str, top_k: int = 5, response_type: str = "general", 
              similarity_threshold: float = 0.5) -> Dict[str, Any]:
        """
        执行知识检索查询
        
        Args:
            question: 用户问题
            top_k: 检索文档数量
            response_type: 响应类型
            similarity_threshold: 相似度阈值
            
        Returns:
            查询结果
        """
        try:
            logger.info(f"开始执行知识检索查询: {question[:50]}...")
            
            # 1. 向量化查询文本
            logger.info("步骤1: 向量化查询文本")
            query_vector = self.vectorization_client.text_to_vector(question)
            if query_vector is None or len(query_vector) == 0:
                raise Exception("查询文本向量化失败")
            
            # 2. 检索相关文档
            logger.info("步骤2: 检索相关文档")
            retrieved_docs = self.retrieval_service.retrieve_documents(
                query_vector=query_vector,
                top_k=top_k,
                query_text=question
            )
            
            if not retrieved_docs:
                logger.warning("未找到相关文档")
                return {
                    "answer": "抱歉，我没有找到与您问题相关的信息。",
                    "retrieved_documents": [],
                    "confidence": 0.0,
                    "sources": []
                }
            
            # 3. 生成回答
            logger.info("步骤3: 生成回答")
            
            # 构建上下文文本
            context_text = " ".join([doc.get("content", "") for doc in retrieved_docs])
            
            answer = self.llm_service.generate_knowledge_response(
                query=question,
                context=context_text,
                response_type=response_type
            )
            
            # 4. 计算置信度
            confidence = self._calculate_confidence(retrieved_docs, answer)
            
            # 5. 提取来源信息
            sources = self._extract_sources(retrieved_docs)
            
            result = {
                "answer": answer,
                "retrieved_documents": retrieved_docs,
                "confidence": confidence,
                "sources": sources,
                "query": question,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"知识检索查询完成，置信度: {confidence:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"知识检索查询失败: {e}")
            return {
                "answer": f"查询处理失败: {str(e)}",
                "retrieved_documents": [],
                "confidence": 0.0,
                "sources": [],
                "error": str(e)
            }
    
    async def query_stream(self, question: str, top_k: int = 5, response_type: str = "general", 
                          similarity_threshold: float = 0.5):
        """
        流式执行知识检索查询
        
        Args:
            question: 用户问题
            top_k: 检索文档数量
            response_type: 响应类型
            similarity_threshold: 相似度阈值
            
        Yields:
            流式响应块
        """
        try:
            logger.info(f"开始流式知识检索查询: {question[:50]}...")
            
            # 发送开始信号
            yield {"type": "start", "message": "开始检索相关文档...", "timestamp": datetime.now().isoformat()}
            
            # 1. 向量化查询文本
            logger.info("步骤1: 向量化查询文本")
            query_vector = self.vectorization_client.text_to_vector(question)
            if query_vector is None or len(query_vector) == 0:
                yield {"type": "error", "message": "查询文本向量化失败"}
                return
            
            yield {"type": "progress", "message": "查询文本向量化完成", "step": 1}
            
            # 2. 检索相关文档
            logger.info("步骤2: 检索相关文档")
            retrieved_docs = self.retrieval_service.retrieve_documents(
                query_vector=query_vector,
                top_k=top_k,
                query_text=question
            )
            
            if not retrieved_docs:
                logger.warning("未找到相关文档")
                yield {"type": "warning", "message": "未找到相关文档"}
                yield {"type": "answer", "content": "抱歉，我没有找到与您问题相关的信息。"}
                yield {"type": "end", "timestamp": datetime.now().isoformat()}
                return
            
            yield {"type": "progress", "message": f"找到 {len(retrieved_docs)} 个相关文档", "step": 2}
            
            # 3. 流式生成回答
            logger.info("步骤3: 流式生成回答")
            yield {"type": "progress", "message": "开始生成回答...", "step": 3}
            
            # 构建上下文
            context_parts = []
            for doc in retrieved_docs:
                if "content" in doc:
                    context_parts.append(doc["content"])
                elif "text" in doc:
                    context_parts.append(doc["text"])
            
            context = "\n\n".join(context_parts)
            
            # 使用LLM服务的流式生成
            chunk_count = 0
            for chunk in self.llm_service.generate_knowledge_response_stream(
                query=question,
                context=context,
                response_type=response_type
            ):
                chunk_count += 1
                yield {"type": "text", "content": chunk}
            
            # 4. 计算置信度
            confidence = self._calculate_confidence(retrieved_docs, "")
            
            # 5. 提取来源信息
            sources = self._extract_sources(retrieved_docs)
            
            # 发送元数据
            yield {
                "type": "metadata",
                "confidence": confidence,
                "sources": sources,
                "retrieved_count": len(retrieved_docs),
                "timestamp": datetime.now().isoformat()
            }
            
            # 发送结束信号
            yield {"type": "end", "timestamp": datetime.now().isoformat()}
            
            logger.info(f"流式知识检索查询完成，置信度: {confidence:.3f}")
            
        except Exception as e:
            logger.error(f"流式知识检索查询失败: {e}")
            yield {"type": "error", "message": f"查询处理失败: {str(e)}"}
            yield {"type": "end", "timestamp": datetime.now().isoformat()}
    
    def chat(self, messages: List[Dict[str, str]], top_k: int = 5, 
             multimodal_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行对话式查询
        
        Args:
            messages: 对话历史
            top_k: 检索文档数量
            multimodal_data: 多模态数据
            
        Returns:
            对话结果
        """
        try:
            logger.info("开始执行对话式查询")
            
            # 获取最后一条用户消息
            user_message = None
            for message in reversed(messages):
                if message.get('role') == 'user':
                    user_message = message.get('content', '')
                    break
            
            if not user_message:
                return {
                    "answer": "请提供您的问题。",
                    "retrieved_documents": [],
                    "confidence": 0.0,
                    "sources": []
                }
            
            # 使用对话记忆服务处理上下文
            context = self.conversation_memory.process_conversation(messages)
            
            # 执行查询
            result = self.query(
                question=user_message,
                top_k=top_k,
                response_type="conversational"
            )
            
            # 更新对话记忆
            self.conversation_memory.add_interaction(user_message, result["answer"])
            
            return result
            
        except Exception as e:
            logger.error(f"对话式查询失败: {e}")
            return {
                "answer": f"对话处理失败: {str(e)}",
                "retrieved_documents": [],
                "confidence": 0.0,
                "sources": [],
                "error": str(e)
            }
    
    def search_documents(self, query: str, search_type: str = "hybrid", 
                        top_k: int = 3) -> List[Dict[str, Any]]:
        """
        搜索文档
        
        Args:
            query: 搜索查询
            search_type: 搜索类型
            top_k: 返回文档数量
            
        Returns:
            搜索结果
        """
        try:
            logger.info(f"开始搜索文档: {query[:50]}...")
            
            # 向量化查询文本
            query_vector = self.vectorization_client.text_to_vector(query)
            if query_vector is None or len(query_vector) == 0:
                return []
            
            # 执行检索
            results = self.retrieval_service.retrieve_documents(
                query_vector=query_vector,
                top_k=top_k,
                strategy=search_type,
                query_text=query
            )
            
            logger.info(f"搜索完成，找到 {len(results)} 个文档")
            return results
            
        except Exception as e:
            logger.error(f"文档搜索失败: {e}")
            return []
    
    def batch_query(self, questions: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        批量查询
        
        Args:
            questions: 问题列表
            top_k: 检索文档数量
            
        Returns:
            批量查询结果
        """
        try:
            logger.info(f"开始批量查询，共 {len(questions)} 个问题")
            
            results = []
            for i, question in enumerate(questions):
                logger.info(f"处理问题 {i+1}/{len(questions)}: {question[:50]}...")
                
                result = self.query(question=question, top_k=top_k)
                results.append({
                    "question": question,
                    "result": result
                })
            
            logger.info("批量查询完成")
            return results
            
        except Exception as e:
            logger.error(f"批量查询失败: {e}")
            return []
    
    def _calculate_confidence(self, retrieved_docs: List[Dict[str, Any]], 
                            answer: str) -> float:
        """
        计算回答置信度
        
        Args:
            retrieved_docs: 检索到的文档
            answer: 生成的回答
            
        Returns:
            置信度分数
        """
        try:
            if not retrieved_docs:
                return 0.0
            
            # 基于检索文档的相似度计算置信度
            similarities = [doc.get('similarity', 0) for doc in retrieved_docs]
            avg_similarity = sum(similarities) / len(similarities)
            
            # 基于文档数量调整置信度
            doc_count_factor = min(len(retrieved_docs) / 5, 1.0)
            
            # 综合置信度
            confidence = avg_similarity * doc_count_factor
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"计算置信度失败: {e}")
            return 0.0
    
    def _extract_sources(self, retrieved_docs: List[Dict[str, Any]]) -> List[str]:
        """
        提取来源信息
        
        Args:
            retrieved_docs: 检索到的文档
            
        Returns:
            来源列表
        """
        try:
            sources = []
            for doc in retrieved_docs:
                source = doc.get('source', '')
                if source and source not in sources:
                    sources.append(source)
            
            return sources
            
        except Exception as e:
            logger.error(f"提取来源信息失败: {e}")
            return []
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        获取系统统计信息
        
        Returns:
            系统统计信息
        """
        try:
            stats = {
                "pipeline_status": "running",
                "services": {
                    "retrieval_service": "active" if self.retrieval_service else "inactive",
                    "llm_service": "active" if self.llm_service else "inactive",
                    "vectorization_client": "active" if self.vectorization_client else "inactive",
                    "conversation_memory": "active" if self.conversation_memory else "inactive"
                },
                "retrieval_stats": self.retrieval_service.get_statistics() if self.retrieval_service else {},
                "llm_stats": self.llm_service.get_model_stats() if self.llm_service else {},
                "timestamp": datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取系统统计信息失败: {e}")
            return {"error": str(e)}
    
    def save_system(self, save_dir: str):
        """
        保存系统状态
        
        Args:
            save_dir: 保存目录
        """
        try:
            logger.info(f"保存系统状态到: {save_dir}")
            
            os.makedirs(save_dir, exist_ok=True)
            
            # 保存配置
            config_path = os.path.join(save_dir, "config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            # 保存检索服务状态
            if self.retrieval_service:
                retrieval_path = os.path.join(save_dir, "retrieval_service")
                self.retrieval_service.save_metadata(os.path.join(retrieval_path, "metadata.json"))
            
            # 保存对话记忆
            if self.conversation_memory:
                memory_path = os.path.join(save_dir, "conversation_memory")
                self.conversation_memory.save_memory(memory_path)
            
            logger.info("系统状态保存完成")
            
        except Exception as e:
            logger.error(f"保存系统状态失败: {e}")
            raise
    
    def load_system(self, save_dir: str):
        """
        加载系统状态
        
        Args:
            save_dir: 保存目录
        """
        try:
            logger.info(f"从 {save_dir} 加载系统状态")
            
            # 加载配置
            config_path = os.path.join(save_dir, "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                self.config.update(loaded_config)
            
            # 重新初始化服务
            self._init_services()
            
            # 加载检索服务状态
            if self.retrieval_service:
                retrieval_path = os.path.join(save_dir, "retrieval_service", "metadata.json")
                if os.path.exists(retrieval_path):
                    self.retrieval_service.load_metadata(retrieval_path)
            
            # 加载对话记忆
            if self.conversation_memory:
                memory_path = os.path.join(save_dir, "conversation_memory")
                if os.path.exists(memory_path):
                    self.conversation_memory.load_memory(memory_path)
            
            logger.info("系统状态加载完成")
            
        except Exception as e:
            logger.error(f"加载系统状态失败: {e}")
            raise
    
    def clear_system(self):
        """清空系统状态"""
        try:
            logger.info("清空系统状态")
            
            if self.retrieval_service:
                self.retrieval_service.clear_all()
            
            if self.conversation_memory:
                self.conversation_memory.clear_memory()
            
            logger.info("系统状态清空完成")
            
        except Exception as e:
            logger.error(f"清空系统状态失败: {e}")


class KnowledgeRetrievalPipelineFactory:
    """知识检索管道工厂类"""
    
    @staticmethod
    def create_pipeline(config_path: str = None) -> KnowledgeRetrievalPipeline:
        """
        创建知识检索管道实例
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            知识检索管道实例
        """
        try:
            # 默认配置
            default_config = {
                "retrieval": {
                    "vector_dim": 512,  # 修复向量维度
                    "max_results": 20,
                    "similarity_threshold": 0.1,  # 降低阈值
                    "retrieval_strategy": "hybrid",
                    "vectorization_service_url": "http://localhost:8001",
                    "vector_db_path": "../../../datas/chroma_db",  # 添加ChromaDB路径
                    "collection_name": "medical_multimodal_vectors"  # 添加集合名称
                },
                "llm": {
                    "model_name": "apollo",
                    "model_path": "FreedomIntelligence/Apollo-0.5B",
                    "max_length": 2048,
                    "temperature": 0.7,
                    "top_p": 0.9
                },
                "vectorization": {
                    "vectorization_service_url": "http://localhost:8001",
                    "timeout": 300,
                    "retry_attempts": 3,
                    "vector_dim": 768
                },
                "memory": {
                    "max_history": 10,
                    "memory_type": "conversation"
                }
            }
            
            # 如果提供了配置文件，则加载配置
            if config_path and os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        user_config = json.load(f)
                    default_config.update(user_config)
                except Exception as e:
                    logger.warning(f"加载配置文件失败: {e}, 使用默认配置")
            
            # 创建管道实例
            pipeline = KnowledgeRetrievalPipeline(default_config)
            logger.info("知识检索管道创建成功")
            
            return pipeline
            
        except Exception as e:
            logger.error(f"创建知识检索管道失败: {e}")
            raise


if __name__ == "__main__":
    # 测试知识检索管道
    try:
        logger.info("开始测试知识检索管道")
        
        # 创建管道
        pipeline = KnowledgeRetrievalPipelineFactory.create_pipeline()
        
        # 测试查询
        test_question = "什么是心肌梗死？"
        result = pipeline.query(test_question, top_k=3)
        
        print(f"测试问题: {test_question}")
        print(f"回答: {result['answer']}")
        print(f"置信度: {result['confidence']:.3f}")
        print(f"检索文档数量: {len(result['retrieved_documents'])}")
        
        # 测试系统统计
        stats = pipeline.get_system_stats()
        print(f"系统状态: {stats}")
        
        logger.info("知识检索管道测试完成")
        
    except Exception as e:
        logger.error(f"知识检索管道测试失败: {e}")
        print(f"测试失败: {e}")

