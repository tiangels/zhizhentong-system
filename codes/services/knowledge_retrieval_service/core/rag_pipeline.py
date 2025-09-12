"""
RAG完整流程模块
整合向量化服务、检索服务和大语言模型服务，实现完整的RAG流程
"""

import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

from .vector_service import VectorService, VectorServiceFactory
from .retrieval_service import RetrievalService, RetrievalServiceFactory
from .llm_service import LLMService, LLMServiceFactory
from .config_manager import ConfigManager

# 导入文本摘要服务
from .text_summarization_service import TextSummarizationService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGPipeline:
    """RAG完整流程类，整合所有服务组件"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化RAG流程
        
        Args:
            config: 配置字典，如果为None则使用默认配置
        """
        # 使用统一配置管理器
        self.config_manager = ConfigManager()
        self.config = config or self.config_manager.config
        
        self.vector_service = None
        self.retrieval_service = None
        self.llm_service = None
        self.summarization_service = None
        
        # 初始化各个服务
        self._initialize_services()
        
        # 线程池用于并发处理
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info("RAG Pipeline initialized successfully")
    
    def _initialize_services(self):
        """初始化各个服务组件"""
        try:
            # 初始化向量化服务
            vector_config = self.config_manager.get_vector_service_config()
            self.vector_service = VectorServiceFactory.create_vector_service()
            logger.info("Vector service initialized")
            
            # 初始化检索服务
            retrieval_config = self.config_manager.get_retrieval_service_config()
            self.retrieval_service = RetrievalService(retrieval_config)
            logger.info("Retrieval service initialized")
            
            # 初始化大语言模型服务
            llm_config = self.config_manager.get_llm_service_config()
            config_path = self.config_manager.config_path
            self.llm_service = LLMServiceFactory.create_llm_service(config_path)
            logger.info("LLM service initialized")
            
            # 初始化文本摘要服务
            summarization_config = self.config.get('summarization_service', {})
            if summarization_config:
                model_path = summarization_config.get('model_path')
                self.summarization_service = TextSummarizationService(model_path)
                logger.info("Text summarization service initialized")
            else:
                logger.warning("No summarization service configuration found")
            
        except Exception as e:
            logger.error(f"Error initializing services: {e}")
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]], 
                     vectorize_images: bool = False) -> bool:
        """
        添加文档到RAG系统
        
        Args:
            documents: 文档列表
            vectorize_images: 是否向量化图像
            
        Returns:
            是否添加成功
        """
        try:
            print("=" * 50)
            print("📄 RAG文档添加流程开始")
            print("=" * 50)
            logger.info("开始RAG文档添加流程...")
            
            # 1. 获取用户输入
            print("==========")
            print("获取用户输入开始")
            print("==========")
            logger.info(f"获取用户输入细节日志：文档数量={len(documents)}, 向量化图像={vectorize_images}")
            if not documents:
                logger.warning("No documents provided")
                return False
            
            for i, doc in enumerate(documents):
                doc_type = doc.get('type', 'text')
                doc_title = doc.get('title', '无标题')
                logger.info(f"文档 {i+1}: 类型={doc_type}, 标题='{doc_title}'")
            
            logger.info("获取用户输入成功")
            print("获取用户输入结束")
            print("==========")
            
            # 2. 用户数据处理
            print("==========")
            print("用户数据处理开始")
            print("==========")
            logger.info("用户数据处理的细节日志：开始分类文档")
            
            # 分离文本和图像文档
            text_docs = []
            image_docs = []
            
            for doc in documents:
                if doc.get('type') == 'image' and vectorize_images:
                    image_docs.append(doc)
                else:
                    text_docs.append(doc)
            
            logger.info(f"文本文档数量: {len(text_docs)}")
            logger.info(f"图像文档数量: {len(image_docs)}")
            logger.info("用户数据处理完成")
            logger.info("用户数据处理成功")
            print("==========")
            
            # 3. 处理文本文档
            if text_docs:
                print("==========")
                print("处理文本文档开始")
                print("==========")
                logger.info("处理文本文档的细节日志：开始处理文本文档")
                self._process_text_documents(text_docs)
                logger.info("处理文本文档成功")
                print("处理文本文档结束")
                print("==========")
            
            # 4. 处理图像文档
            if image_docs:
                print("==========")
                print("处理图像文档开始")
                print("==========")
                logger.info("处理图像文档的细节日志：开始处理图像文档")
                self._process_image_documents(image_docs)
                logger.info("处理图像文档成功")
                print("处理图像文档结束")
                print("==========")
            
            # 5. 返回用户结果
            print("==========")
            print("返回用户结果开始")
            print("==========")
            logger.info("返回用户结果的细节日志：开始构建添加结果")
            logger.info(f"Successfully added {len(documents)} documents to RAG system")
            logger.info("返回用户结果成功")
            print("返回用户结果结束")
            print("==========")
            
            print("=" * 50)
            print("🎉 RAG文档添加流程完成")
            print("=" * 50)
            logger.info("RAG文档添加流程成功完成")
            
            return True
            
        except Exception as e:
            print("=" * 50)
            print("❌ RAG文档添加流程失败")
            print("=" * 50)
            logger.error(f"RAG文档添加流程失败: {e}")
            logger.error(f"Error adding documents: {e}")
            return False
    
    def _process_text_documents(self, documents: List[Dict[str, Any]]):
        """处理文本文档"""
        try:
            # 提取文本内容
            texts = []
            for doc in documents:
                content = doc.get('content', '')
                if content:
                    texts.append(content)
            
            if not texts:
                return
            
            # 向量化文本
            vectors = self.vector_service.batch_text_to_vectors(texts)
            
            # 添加到检索系统
            self.retrieval_service.add_documents(vectors, documents)
            
            logger.info(f"Processed {len(texts)} text documents")
            
        except Exception as e:
            logger.error(f"Error processing text documents: {e}")
            raise
    
    def _process_image_documents(self, documents: List[Dict[str, Any]]):
        """处理图像文档"""
        try:
            # 提取图像路径
            image_paths = []
            valid_docs = []
            
            for doc in documents:
                image_path = doc.get('image_path', '')
                if image_path and os.path.exists(image_path):
                    image_paths.append(image_path)
                    valid_docs.append(doc)
            
            if not image_paths:
                return
            
            # 向量化图像
            vectors = self.vector_service.batch_image_to_vectors(image_paths)
            
            # 添加到检索系统
            self.retrieval_service.add_documents(vectors, valid_docs)
            
            logger.info(f"Processed {len(image_paths)} image documents")
            
        except Exception as e:
            logger.error(f"Error processing image documents: {e}")
            raise
    
    def query(self, question: str, top_k: int = 5, 
              response_type: str = "general", similarity_threshold: float = None) -> Dict[str, Any]:
        """
        查询RAG系统
        
        Args:
            question: 用户问题
            top_k: 检索文档数量
            response_type: 响应类型
            similarity_threshold: 相似度阈值（可选，默认使用配置值）
            
        Returns:
            查询结果
        """
        try:
            print("=" * 50)
            print("🔍 RAG查询流程开始")
            print("=" * 50)
            logger.info("开始RAG查询流程...")
            
            # 1. 获取用户输入
            print("==========")
            print("获取用户输入开始")
            print("==========")
            logger.info(f"获取用户输入细节日志：问题='{question}', top_k={top_k}, response_type='{response_type}'")
            logger.info("获取用户输入成功")
            print("获取用户输入结束")
            print("==========")
            
            # 2. 用户数据处理
            print("==========")
            print("用户数据处理开始")
            print("==========")
            logger.info("用户数据处理的细节日志：开始预处理用户问题")
            logger.info(f"问题长度: {len(question)} 字符")
            logger.info(f"问题类型: {response_type}")
            logger.info("用户数据处理完成")
            logger.info("用户数据处理成功")
            print("==========")
            
            # 3. 用户数据向量化
            print("==========")
            print("用户数据向量化开始")
            print("==========")
            logger.info("用户数据向量化的细节日志：开始将用户问题转换为向量")
            query_vector = self.vector_service.text_to_vector(question)
            logger.info(f"向量化完成，向量维度: {len(query_vector) if query_vector is not None else 'None'}")
            logger.info("用户数据向量化成功")
            print("用户数据向量化结束")
            print("==========")
            
            # 4. 用户数据检索
            print("==========")
            print("用户数据检索开始")
            print("==========")
            logger.info("用户数据检索的细节日志：开始检索相关文档")
            logger.info(f"检索参数: top_k={top_k}")
            retrieved_docs = self.retrieval_service.retrieve_documents(
                query_vector, top_k=top_k, query_text=question
            )
            logger.info(f"检索完成，找到 {len(retrieved_docs)} 个相关文档")
            logger.info("用户数据检索成功")
            print("用户数据检索结束")
            print("==========")
            
            # 5. 文档摘要生成
            print("==========")
            print("文档摘要生成开始")
            print("==========")
            logger.info("文档摘要生成的细节日志：开始对检索到的文档进行摘要")
            logger.info(f"待摘要文档数量: {len(retrieved_docs)}")
            
            # 打印原始文档内容
            for i, doc in enumerate(retrieved_docs, 1):
                title = doc.get('title', f'文档{i}')
                content = doc.get('content', '')
                similarity = doc.get('similarity', 0)
                logger.info(f"原始文档{i}: 标题='{title}', 相似度={similarity:.3f}, 内容长度={len(content)}字符")
                logger.info(f"原始文档{i}内容预览: {content[:100]}...")
            
            summary = self._summarize_documents(retrieved_docs, question)
            logger.info(f"摘要生成完成，摘要长度: {len(summary)} 字符")
            logger.info(f"生成的摘要内容: {summary}")
            logger.info("文档摘要生成成功")
            print("文档摘要生成结束")
            print("==========")
            
            # 6. 构建上下文
            print("==========")
            print("构建上下文开始")
            print("==========")
            logger.info("构建上下文的细节日志：开始基于摘要构建上下文")
            context = self._build_context(summary)
            logger.info(f"上下文构建完成，上下文长度: {len(context)} 字符")
            logger.info(f"构建的上下文内容: {context}")
            logger.info("构建上下文成功")
            print("构建上下文结束")
            print("==========")
            
            # 7. 调用大模型生成回答
            print("==========")
            print("调用大模型生成回答开始")
            print("==========")
            logger.info("调用大模型生成回答的细节日志：开始调用LLM生成回答")
            logger.info(f"LLM参数: response_type='{response_type}'")
            
            # 检查是否有相关文档，决定生成策略
            if retrieved_docs:
                logger.info("✅ 基于检索到的医学知识生成回答")
                answer = self.llm_service.generate_medical_response(
                    question, context, response_type
                )
            else:
                logger.warning("⚠️ 没有找到相关医学知识，使用通用回答模式")
                answer = self.llm_service.generate_general_response(
                    question, response_type
                )
            logger.info(f"LLM生成完成，回答长度: {len(answer)} 字符")
            logger.info("调用大模型生成回答成功")
            print("调用大模型生成回答结束")
            print("==========")
            
            # 8. 返回用户结果
            print("==========")
            print("返回用户结果开始")
            print("==========")
            logger.info("返回用户结果的细节日志：开始构建最终结果")
            result = {
                'question': question,
                'answer': answer,
                'context': context,
                'retrieved_documents': retrieved_docs,
                'response_type': response_type,
                'timestamp': datetime.now().isoformat()
            }
            logger.info("结果构建完成")
            logger.info("返回用户结果成功")
            print("返回用户结果结束")
            print("==========")
            
            print("=" * 50)
            print("🎉 RAG查询流程完成")
            print("=" * 50)
            logger.info("RAG查询流程成功完成")
            
            return result
            
        except Exception as e:
            print("=" * 50)
            print("❌ RAG查询流程失败")
            print("=" * 50)
            logger.error(f"RAG查询流程失败: {e}")
            logger.error(f"Error in RAG query: {e}")
            return {
                'question': question,
                'answer': '抱歉，我无法处理您的问题。请稍后重试。',
                'context': '',
                'retrieved_documents': [],
                'response_type': response_type,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    
    def _build_context(self, summary: str, max_length: int = 800) -> str:
        """
        基于摘要构建上下文
        
        Args:
            summary: 统一摘要文本
            max_length: 最大上下文长度
            
        Returns:
            上下文字符串
        """
        try:
            if not summary:
                return ""
            
            # 构建上下文提示词
            context = f"""基于以下医学知识摘要，请回答用户的问题：

医学知识摘要：
{summary}

请基于以上医学知识，结合您的专业知识，为用户提供准确、专业的回答。"""
            
            # 如果上下文太长，截断到最大长度
            if len(context) > max_length:
                context = context[:max_length] + "..."
            
            return context.strip()
            
        except Exception as e:
            logger.error(f"构建上下文出错：{e}")
            return ""
    
    def chat(self, messages: List[Dict[str, str]], 
             top_k: int = 5) -> Dict[str, Any]:
        """
        对话功能
        
        Args:
            messages: 对话历史
            top_k: 检索文档数量
            
        Returns:
            对话结果
        """
        try:
            print("=" * 50)
            print("💬 RAG对话流程开始")
            print("=" * 50)
            logger.info("开始RAG对话流程...")
            
            # 1. 获取用户输入
            print("==========")
            print("获取用户输入开始")
            print("==========")
            logger.info(f"获取用户输入细节日志：对话历史长度={len(messages)}, top_k={top_k}")
            
            if not messages:
                logger.warning("对话历史为空")
                return {
                    'answer': '请告诉我您的问题。',
                    'context': '',
                    'retrieved_documents': [],
                    'timestamp': datetime.now().isoformat()
                }
            
            # 获取最后一个用户消息
            last_message = messages[-1]
            if last_message.get('role') != 'user':
                logger.warning("最后一条消息不是用户消息")
                return {
                    'answer': '请告诉我您的问题。',
                    'context': '',
                    'retrieved_documents': [],
                    'timestamp': datetime.now().isoformat()
                }
            
            question = last_message.get('content', '')
            logger.info(f"提取用户问题: '{question}'")
            
            # 不再进行关键词判断，让生成模型根据检索结果判断
            
            logger.info("获取用户输入成功")
            print("获取用户输入结束")
            print("==========")
            
            # 2. 用户数据处理
            print("==========")
            print("用户数据处理开始")
            print("==========")
            logger.info("用户数据处理的细节日志：开始处理对话历史")
            logger.info(f"对话轮数: {len(messages)}")
            logger.info(f"当前问题长度: {len(question)} 字符")
            logger.info("用户数据处理完成")
            logger.info("用户数据处理成功")
            print("==========")
            
            # 3. 用户数据向量化
            print("==========")
            print("用户数据向量化开始")
            print("==========")
            logger.info("用户数据向量化的细节日志：开始将用户问题转换为向量")
            query_vector = self.vector_service.text_to_vector(question)
            logger.info(f"向量化完成，向量维度: {len(query_vector) if query_vector is not None else 'None'}")
            logger.info("用户数据向量化成功")
            print("用户数据向量化结束")
            print("==========")
            
            # 4. 用户数据检索
            print("==========")
            print("用户数据检索开始")
            print("==========")
            logger.info("用户数据检索的细节日志：开始检索相关文档")
            logger.info(f"检索参数: top_k={top_k}")
            retrieved_docs = self.retrieval_service.retrieve_documents(
                query_vector, top_k=top_k, query_text=question
            )
            logger.info(f"检索完成，找到 {len(retrieved_docs)} 个相关文档")
            logger.info("用户数据检索成功")
            print("用户数据检索结束")
            print("==========")
            
            # 5. 构建上下文
            print("==========")
            print("构建上下文开始")
            print("==========")
            logger.info("构建上下文的细节日志：开始构建检索文档的上下文")
            context = self._build_context(retrieved_docs)
            logger.info(f"上下文构建完成，上下文长度: {len(context)} 字符")
            logger.info("构建上下文成功")
            print("构建上下文结束")
            print("==========")
            
            # 6. 调用大模型生成回答
            print("==========")
            print("调用大模型生成回答开始")
            print("==========")
            logger.info("调用大模型生成回答的细节日志：开始调用LLM生成对话回答")
            logger.info(f"对话历史长度: {len(messages)}")
            answer = self.llm_service.chat_with_context(messages, context)
            logger.info(f"LLM生成完成，回答长度: {len(answer)} 字符")
            logger.info("调用大模型生成回答成功")
            print("调用大模型生成回答结束")
            print("==========")
            
            # 7. 返回用户结果
            print("==========")
            print("返回用户结果开始")
            print("==========")
            logger.info("返回用户结果的细节日志：开始构建最终对话结果")
            result = {
                'answer': answer,
                'context': context,
                'retrieved_documents': retrieved_docs,
                'timestamp': datetime.now().isoformat()
            }
            logger.info("结果构建完成")
            logger.info("返回用户结果成功")
            print("返回用户结果结束")
            print("==========")
            
            print("=" * 50)
            print("🎉 RAG对话流程完成")
            print("=" * 50)
            logger.info("RAG对话流程成功完成")
            
            return result
            
        except Exception as e:
            print("=" * 50)
            print("❌ RAG对话流程失败")
            print("=" * 50)
            logger.error(f"RAG对话流程失败: {e}")
            logger.error(f"Error in chat: {e}")
            return {
                'answer': '抱歉，我无法理解您的问题。请重新描述您的问题。',
                'context': '',
                'retrieved_documents': [],
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def batch_query(self, questions: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        批量查询
        
        Args:
            questions: 问题列表
            top_k: 检索文档数量
            
        Returns:
            查询结果列表
        """
        try:
            print("=" * 50)
            print("📦 RAG批量查询流程开始")
            print("=" * 50)
            logger.info("开始RAG批量查询流程...")
            
            # 1. 获取用户输入
            print("==========")
            print("获取用户输入开始")
            print("==========")
            logger.info(f"获取用户输入细节日志：问题数量={len(questions)}, top_k={top_k}")
            for i, question in enumerate(questions):
                logger.info(f"问题 {i+1}: '{question[:50]}{'...' if len(question) > 50 else ''}'")
            logger.info("获取用户输入成功")
            print("获取用户输入结束")
            print("==========")
            
            # 2. 用户数据处理
            print("==========")
            print("用户数据处理开始")
            print("==========")
            logger.info("用户数据处理的细节日志：开始预处理批量问题")
            logger.info(f"总问题数: {len(questions)}")
            logger.info(f"平均问题长度: {sum(len(q) for q in questions) / len(questions):.1f} 字符")
            logger.info("用户数据处理完成")
            logger.info("用户数据处理成功")
            print("==========")
            
            # 3. 批量处理
            print("==========")
            print("批量处理开始")
            print("==========")
            logger.info("批量处理的细节日志：开始逐个处理问题")
            results = []
            
            for i, question in enumerate(questions):
                logger.info(f"处理问题 {i+1}/{len(questions)}: '{question[:30]}{'...' if len(question) > 30 else ''}'")
                result = self.query(question, top_k)
                results.append(result)
                logger.info(f"问题 {i+1} 处理完成")
            
            logger.info(f"批量处理完成，成功处理 {len(results)} 个问题")
            logger.info("批量处理成功")
            print("批量处理结束")
            print("==========")
            
            # 4. 返回用户结果
            print("==========")
            print("返回用户结果开始")
            print("==========")
            logger.info("返回用户结果的细节日志：开始构建批量查询结果")
            logger.info(f"结果数量: {len(results)}")
            success_count = sum(1 for r in results if 'error' not in r)
            logger.info(f"成功处理: {success_count}/{len(results)} 个问题")
            logger.info("返回用户结果成功")
            print("返回用户结果结束")
            print("==========")
            
            print("=" * 50)
            print("🎉 RAG批量查询流程完成")
            print("=" * 50)
            logger.info("RAG批量查询流程成功完成")
            
            return results
            
        except Exception as e:
            print("=" * 50)
            print("❌ RAG批量查询流程失败")
            print("=" * 50)
            logger.error(f"RAG批量查询流程失败: {e}")
            logger.error(f"Error in batch query: {e}")
            return []
    
    def search_documents(self, query: str, search_type: str = "semantic", 
                        top_k: int = 10) -> List[Dict[str, Any]]:
        """
        搜索文档
        
        Args:
            query: 查询字符串
            search_type: 搜索类型 (semantic, keyword, hybrid)
            top_k: 返回文档数量
            
        Returns:
            搜索结果
        """
        try:
            print("=" * 50)
            print("🔍 RAG文档搜索流程开始")
            print("=" * 50)
            logger.info("开始RAG文档搜索流程...")
            
            # 1. 获取用户输入
            print("==========")
            print("获取用户输入开始")
            print("==========")
            logger.info(f"获取用户输入细节日志：查询='{query}', 搜索类型='{search_type}', top_k={top_k}")
            logger.info("获取用户输入成功")
            print("获取用户输入结束")
            print("==========")
            
            # 2. 用户数据处理
            print("==========")
            print("用户数据处理开始")
            print("==========")
            logger.info("用户数据处理的细节日志：开始预处理搜索查询")
            logger.info(f"查询长度: {len(query)} 字符")
            logger.info(f"搜索类型: {search_type}")
            logger.info("用户数据处理完成")
            logger.info("用户数据处理成功")
            print("==========")
            
            # 3. 执行搜索
            print("==========")
            print("执行搜索开始")
            print("==========")
            logger.info("执行搜索的细节日志：开始执行文档搜索")
            
            if search_type == "keyword":
                # 关键词搜索
                logger.info("使用关键词搜索模式")
                keywords = query.split()
                logger.info(f"提取关键词: {keywords}")
                results = self.retrieval_service.search_by_keywords(keywords, top_k)
            else:
                # 语义搜索
                logger.info("使用语义搜索模式")
                logger.info("开始向量化查询")
                query_vector = self.vector_service.text_to_vector(query)
                logger.info(f"向量化完成，向量维度: {len(query_vector) if query_vector is not None else 'None'}")
                results = self.retrieval_service.retrieve_documents(
                    query_vector, top_k=top_k, strategy=search_type, query_text=query
                )
            
            logger.info(f"搜索完成，找到 {len(results)} 个相关文档")
            logger.info("执行搜索成功")
            print("执行搜索结束")
            print("==========")
            
            # 4. 返回用户结果
            print("==========")
            print("返回用户结果开始")
            print("==========")
            logger.info("返回用户结果的细节日志：开始构建搜索结果")
            logger.info(f"搜索结果数量: {len(results)}")
            logger.info("返回用户结果成功")
            print("返回用户结果结束")
            print("==========")
            
            print("=" * 50)
            print("🎉 RAG文档搜索流程完成")
            print("=" * 50)
            logger.info("RAG文档搜索流程成功完成")
            
            return results
            
        except Exception as e:
            print("=" * 50)
            print("❌ RAG文档搜索流程失败")
            print("=" * 50)
            logger.error(f"RAG文档搜索流程失败: {e}")
            logger.error(f"Error searching documents: {e}")
            return []
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        获取系统统计信息
        
        Returns:
            系统统计信息
        """
        try:
            vector_stats = self.vector_service.get_db_stats()
            retrieval_stats = self.retrieval_service.get_statistics()
            llm_info = self.llm_service.get_model_info()
            
            return {
                'vector_database': vector_stats,
                'retrieval_system': retrieval_stats,
                'llm_model': llm_info,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}
    
    def save_system(self, save_dir: str):
        """
        保存系统状态
        
        Args:
            save_dir: 保存目录
        """
        try:
            os.makedirs(save_dir, exist_ok=True)
            
            # 保存向量数据库
            vector_db_path = os.path.join(save_dir, "vector_db.index")
            self.vector_service.save_vector_db(vector_db_path)
            
            # 保存元数据
            metadata_path = os.path.join(save_dir, "metadata.json")
            self.retrieval_service.save_metadata(metadata_path)
            
            # 保存配置
            config_path = os.path.join(save_dir, "config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"System saved to {save_dir}")
            
        except Exception as e:
            logger.error(f"Error saving system: {e}")
            raise
    
    def load_system(self, save_dir: str):
        """
        加载系统状态
        
        Args:
            save_dir: 保存目录
        """
        try:
            # 加载向量数据库
            vector_db_path = os.path.join(save_dir, "vector_db.index")
            if os.path.exists(vector_db_path):
                self.vector_service.load_vector_db(vector_db_path)
            
            # 加载元数据
            metadata_path = os.path.join(save_dir, "metadata.json")
            if os.path.exists(metadata_path):
                self.retrieval_service.load_metadata(metadata_path)
            
            logger.info(f"System loaded from {save_dir}")
            
        except Exception as e:
            logger.error(f"Error loading system: {e}")
            raise
    
    def clear_system(self):
        """清空系统数据"""
        try:
            self.vector_service.clear_db()
            self.retrieval_service.clear_all()
            logger.info("System cleared")
        except Exception as e:
            logger.error(f"Error clearing system: {e}")
            raise
    
    def __del__(self):
        """析构函数"""
        try:
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=True)
        except Exception as e:
            logger.error(f"Error in destructor: {e}")
    
    def _summarize_documents(self, documents: List[Dict[str, Any]], question: str) -> str:
        """
        将所有检索到的文档整合后统一生成摘要
        
        Args:
            documents: 检索到的文档列表
            question: 用户问题
            
        Returns:
            整合后的摘要文本
        """
        try:
            logger.info("=" * 30)
            logger.info("📝 开始文档摘要生成流程")
            logger.info("=" * 30)
            logger.info(f"输入参数: 文档数量={len(documents)}, 问题='{question}'")
            
            if not documents:
                logger.warning("没有文档需要摘要，返回空字符串")
                return ""
            
            # 整合所有文档内容
            logger.info("步骤1: 开始整合文档内容")
            combined_content = ""
            for i, doc in enumerate(documents, 1):
                title = doc.get('title', f'文档{i}')
                content = doc.get('content', '')
                similarity = doc.get('similarity', 0)
                source = doc.get('source', '未知来源')
                
                logger.info(f"处理文档{i}: 标题='{title}', 相似度={similarity:.3f}, 来源='{source}'")
                logger.info(f"文档{i}原始内容长度: {len(content)} 字符")
                logger.info(f"文档{i}内容预览: {content[:150]}...")
                
                if content:
                    # 只添加纯内容，不包含格式信息
                    combined_content += f"\n{content}\n"
                    logger.info(f"文档{i}已添加到合并内容中")
                else:
                    logger.warning(f"文档{i}内容为空，跳过")
            
            logger.info(f"文档整合完成，合并内容总长度: {len(combined_content)} 字符")
            logger.info(f"合并内容预览: {combined_content[:300]}...")
            
            if not combined_content.strip():
                logger.warning("合并内容为空，返回空字符串")
                return ""
            
            # 构建简化摘要提示词
            logger.info("步骤2: 开始构建摘要提示词")
            # 限制输入内容长度，避免提示词过长
            max_input_length = 1000
            truncated_content = combined_content[:max_input_length]
            if len(combined_content) > max_input_length:
                logger.info(f"内容过长，截断到 {max_input_length} 字符")
            
            summary_prompt = f"""基于以下医学知识，生成不超过30字的简洁摘要，重点回答"{question}"：

{truncated_content}

要求：摘要必须控制在30字以内，简洁明了。
摘要："""
            
            logger.info(f"摘要提示词构建完成")
            logger.info(f"提示词总长度: {len(summary_prompt)} 字符")
            logger.info(f"提示词内容: {summary_prompt}")
            logger.info("步骤2: 摘要提示词构建完成")
            
            try:
                # 优先使用文本摘要服务
                if self.summarization_service:
                    logger.info("步骤3: 开始使用文本摘要服务进行文档摘要")
                    summarization_config = self.config.get('summarization_service', {})
                    use_medical = summarization_config.get('use_medical_summarization', True)
                    medical_max_length = summarization_config.get('medical_max_length', 50)
                    
                    if use_medical:
                        summary = self.summarization_service.summarize_medical_text(
                            combined_content, 
                            max_length=medical_max_length
                        )
                        logger.info("使用医学文本摘要服务完成摘要")
                    else:
                        max_length = summarization_config.get('max_length', 100)
                        summary = self.summarization_service.summarize_text(
                            combined_content, 
                            max_length=max_length
                        )
                        logger.info("使用通用文本摘要服务完成摘要")
                else:
                    # 备用方案：调用LLM进行统一摘要
                    logger.info("步骤3: 开始调用LLM进行文档摘要（备用方案）")
                    logger.info(f"LLM调用参数: max_new_tokens=100, temperature=0.3, timeout=600")
                    logger.info(f"发送给LLM的完整提示词: {summary_prompt}")
                    
                    summary = self.llm_service.generate_text(
                        prompt=summary_prompt,
                        max_new_tokens=100,
                        temperature=0.3,
                        timeout=600  # 设置超时时间为600秒
                    )
                
                logger.info(f"摘要生成完成")
                logger.info(f"原始摘要长度: {len(summary)} 字符")
                logger.info(f"生成的原始摘要: {summary}")
                
                # 清理摘要内容并控制长度
                cleaned_summary = summary.strip()
                
                # 强制控制摘要长度在30字以内
                if len(cleaned_summary) > 30:
                    logger.warning(f"摘要长度超过30字限制，当前长度: {len(cleaned_summary)} 字符")
                    # 截取前30个字符
                    cleaned_summary = cleaned_summary[:30]
                    logger.info(f"已截取到30字: {cleaned_summary}")
                
                logger.info(f"清理后摘要长度: {len(cleaned_summary)} 字符")
                logger.info(f"清理后摘要内容: {cleaned_summary}")
                
                logger.info(f"文档统一摘要完成：成功整合了{len(documents)}个文档")
                logger.info("=" * 30)
                logger.info("📝 文档摘要生成流程完成")
                logger.info("=" * 30)
                
                return cleaned_summary
                
            except Exception as e:
                logger.error(f"LLM摘要生成失败: {e}")
                logger.warning("使用备用摘要方案")
                
                # 如果摘要失败，返回前几个文档的简要信息
                fallback_summary = ""
                for i, doc in enumerate(documents[:3], 1):
                    title = doc.get('title', f'文档{i}')
                    content = doc.get('content', '')[:100]
                    if content:
                        fallback_summary += f"【{title}】{content}...\n"
                        logger.info(f"备用摘要添加文档{i}: {title}")
                
                fallback_summary = fallback_summary.strip()
                logger.info(f"备用摘要生成完成，长度: {len(fallback_summary)} 字符")
                logger.info(f"备用摘要内容: {fallback_summary}")
                
                logger.info("=" * 30)
                logger.info("📝 文档摘要生成流程完成（备用方案）")
                logger.info("=" * 30)
                
                return fallback_summary
            
        except Exception as e:
            logger.error(f"文档摘要过程出错：{e}")
            logger.error(f"错误详情: {str(e)}")
            logger.info("=" * 30)
            logger.info("📝 文档摘要生成流程失败")
            logger.info("=" * 30)
            return ""
    
    async def query_stream(self, question: str, top_k: int = 5, 
                    response_type: str = "general", similarity_threshold: float = None):
        """
        流式查询RAG系统，逐步生成回答
        
        Args:
            question: 用户问题
            top_k: 检索文档数量
            response_type: 响应类型
            similarity_threshold: 相似度阈值（可选，默认使用配置值）
            
        Yields:
            流式响应数据
        """
        try:
            logger.info("=" * 50)
            logger.info("🔍 RAG流式查询流程开始")
            logger.info("=" * 50)
            logger.info("开始RAG流式查询流程...")
            logger.info(f"查询参数: question='{question}', top_k={top_k}, response_type='{response_type}'")
            
            # 1. 获取用户输入
            yield {"type": "status", "message": "正在处理您的问题..."}
            logger.info("步骤1: 获取用户输入完成")
            
            # 2. 用户数据向量化
            yield {"type": "status", "message": "正在分析问题..."}
            logger.info("步骤2: 开始用户数据向量化")
            logger.info(f"问题内容: '{question}'")
            logger.info(f"问题长度: {len(question)} 字符")
            
            query_vector = self.vector_service.text_to_vector(question)
            logger.info(f"向量化完成，向量维度: {len(query_vector) if query_vector is not None else 'None'}")
            logger.info("步骤2: 用户数据向量化完成")
            
            # 3. 用户数据检索
            yield {"type": "status", "message": "正在检索相关知识..."}
            logger.info("步骤3: 开始用户数据检索")
            logger.info(f"检索参数: top_k={top_k}, query_text='{question}'")
            
            retrieved_docs = self.retrieval_service.retrieve_documents(
                query_vector, top_k=top_k, query_text=question
            )
            
            logger.info(f"检索完成，找到 {len(retrieved_docs)} 个相关文档")
            # 详细记录检索结果
            for i, doc in enumerate(retrieved_docs, 1):
                title = doc.get('title', f'文档{i}')
                content = doc.get('content', '')
                similarity = doc.get('similarity', 0)
                source = doc.get('source', '未知来源')
                logger.info(f"检索结果{i}: 标题='{title}', 相似度={similarity:.3f}, 来源='{source}'")
                logger.info(f"检索结果{i}内容长度: {len(content)} 字符")
                logger.info(f"检索结果{i}内容预览: {content[:200]}...")
            
            logger.info("步骤3: 用户数据检索完成")
            
            # 4. 内容摘要
            yield {"type": "status", "message": "正在整理检索到的内容..."}
            logger.info("步骤4: 开始内容摘要生成")
            logger.info(f"待摘要文档数量: {len(retrieved_docs)}")
            
            summary = self._summarize_documents(retrieved_docs, question)
            logger.info(f"摘要生成完成，摘要长度: {len(summary)} 字符")
            logger.info(f"生成的摘要内容: {summary}")
            logger.info("步骤4: 内容摘要生成完成")
            
            # 5. 构建上下文
            logger.info("步骤5: 开始构建上下文")
            context = self._build_context(summary)
            logger.info(f"上下文构建完成，上下文长度: {len(context)} 字符")
            logger.info(f"构建的上下文内容: {context}")
            logger.info("步骤5: 构建上下文完成")
            
            # 6. 流式生成回答
            yield {"type": "status", "message": "正在生成回答..."}
            logger.info("步骤6: 开始流式生成回答")
            logger.info(f"LLM参数: response_type='{response_type}'")
            logger.info(f"发送给LLM的完整上下文: {context}")
            
            # 检查是否有相关文档，决定生成策略
            if retrieved_docs:
                logger.info("✅ 基于检索到的医学知识生成回答")
                logger.info("调用LLM服务: generate_medical_response_stream")
                
                answer_chunks = []
                for chunk in self.llm_service.generate_medical_response_stream(
                    question, context, response_type
                ):
                    answer_chunks.append(chunk)
                    yield {"type": "content", "content": chunk}
                
                full_answer = ''.join(answer_chunks)
                logger.info(f"LLM流式生成完成，总回答长度: {len(full_answer)} 字符")
                logger.info(f"LLM生成的完整回答: {full_answer}")
            else:
                logger.warning("⚠️ 没有找到相关医学知识，使用通用回答模式")
                logger.info("调用LLM服务: generate_general_response_stream")
                
                answer_chunks = []
                for chunk in self.llm_service.generate_general_response_stream(
                    question, response_type
                ):
                    answer_chunks.append(chunk)
                    yield {"type": "content", "content": chunk}
                
                full_answer = ''.join(answer_chunks)
                logger.info(f"LLM流式生成完成，总回答长度: {len(full_answer)} 字符")
                logger.info(f"LLM生成的完整回答: {full_answer}")
            
            logger.info("步骤6: 流式生成回答完成")
            
            # 7. 返回检索到的文档信息
            logger.info("步骤7: 开始返回检索到的文档信息")
            documents_info = [
                {
                    "title": doc.get('title', ''),
                    "content": doc.get('content', ''),
                    "similarity": doc.get('similarity', 0),
                    "source": doc.get('source', '')
                }
                for doc in retrieved_docs
            ]
            
            logger.info(f"返回文档信息数量: {len(documents_info)}")
            for i, doc_info in enumerate(documents_info, 1):
                logger.info(f"返回文档{i}: 标题='{doc_info['title']}', 相似度={doc_info['similarity']:.3f}")
            
            yield {
                "type": "documents", 
                "documents": documents_info
            }
            
            logger.info("步骤7: 返回检索到的文档信息完成")
            
            yield {"type": "complete", "message": "回答生成完成"}
            logger.info("🎉 RAG流式查询流程完成")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"流式查询出错：{e}")
            logger.error(f"错误详情: {str(e)}")
            yield {"type": "error", "message": f"查询出错：{str(e)}"}


class RAGPipelineFactory:
    """RAG流程工厂类"""
    
    @staticmethod
    def create_rag_pipeline(config_path: str = None) -> RAGPipeline:
        """
        创建RAG流程实例
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            RAG流程实例
        """
        # 默认配置
        default_config = {
            'vector_service': {
                'device': 'cuda',
                'vector_dim': 384,
                'batch_size': 32
            },
            'retrieval_service': {
                'vector_dim': 384,
                'max_results': 20,
                'similarity_threshold': 0.7,
                'retrieval_strategy': 'semantic'
            },
            'llm_service': {
                'device': 'cuda',
                'model_path': 'ai_models/llm_models/Qwen2-0.5B-Medical-MLX',
                'max_length': 2048,
                'temperature': 0.7
            }
        }
        
        # 如果提供了配置文件，则加载配置
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Error loading config file: {e}, using default config")
        
        return RAGPipeline(default_config)


if __name__ == "__main__":
    # 测试RAG流程
    config = {
        'vector_service': {
            'device': 'cpu',
            'vector_dim': 384,
            'batch_size': 16
        },
        'retrieval_service': {
            'vector_dim': 384,
            'max_results': 10,
            'similarity_threshold': 0.5,
            'retrieval_strategy': 'semantic'
        },
        'llm_service': {
            'device': 'cpu',
            'model_path': 'ai_models/llm_models/Qwen2-0.5B-Medical-MLX',
            'max_length': 1024,
            'temperature': 0.7
        }
    }
    
    try:
        # 创建RAG流程
        rag_pipeline = RAGPipeline(config)
        
        # 测试文档
        test_documents = [
            {
                'content': '心肌梗死是由于冠状动脉急性闭塞导致心肌缺血坏死的心血管疾病。',
                'title': '心肌梗死定义',
                'category': '心血管疾病',
                'source': '医学教科书'
            },
            {
                'content': '胸痛是心肌梗死最常见的症状，通常表现为胸骨后压榨性疼痛。',
                'title': '心肌梗死症状',
                'category': '心血管疾病',
                'source': '临床指南'
            },
            {
                'content': '心电图检查是诊断心肌梗死的重要方法，可显示ST段抬高或压低。',
                'title': '心肌梗死诊断',
                'category': '心血管疾病',
                'source': '诊断手册'
            }
        ]
        
        # 添加文档
        success = rag_pipeline.add_documents(test_documents)
        print(f"Documents added: {success}")
        
        # 测试查询
        question = "什么是心肌梗死？"
        result = rag_pipeline.query(question, top_k=2)
        print(f"\nQuestion: {question}")
        print(f"Answer: {result['answer']}")
        print(f"Retrieved documents: {len(result['retrieved_documents'])}")
        
        # 测试对话
        messages = [
            {"role": "user", "content": "心肌梗死有什么症状？"}
        ]
        chat_result = rag_pipeline.chat(messages)
        print(f"\nChat answer: {chat_result['answer']}")
        
        # 获取系统统计信息
        stats = rag_pipeline.get_system_stats()
        print(f"\nSystem stats: {stats}")
        
    except Exception as e:
        print(f"Error in testing: {e}")
        print("Please ensure all services are properly configured.")


