"""
检索服务模块
负责从向量数据库中检索相关文档，为RAG生成提供上下文
"""

import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
# import faiss  # 暂时注释掉，使用numpy替代
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetrievalService:
    """检索服务类，负责文档检索和排序"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化检索服务
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.vector_db = None
        self.metadata_db = {}  # 存储文档元数据
        self.vector_dim = config.get('vector_dim', 384)
        self.max_results = config.get('max_results', 20)
        self.similarity_threshold = config.get('similarity_threshold', 0.8)
        
        # 检索策略配置
        self.retrieval_strategies = {
            'semantic': self._semantic_retrieval,
            'hybrid': self._hybrid_retrieval,
            'rerank': self._rerank_retrieval
        }
        
        self.current_strategy = config.get('retrieval_strategy', 'semantic')
        
        # 初始化向量数据库
        self._init_vector_db()
    
    def _init_vector_db(self):
        """初始化向量数据库"""
        try:
            from langchain_chroma import Chroma
            from langchain_community.embeddings import HuggingFaceEmbeddings
            
            # 创建嵌入函数
            self.embedding_function = HuggingFaceEmbeddings(
                model_name=self.config.get('model_name', 'sentence-transformers/all-MiniLM-L6-v2'),
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            
            # 创建ChromaDB向量数据库
            db_path = self.config.get('vector_db_path', './vector_db')
            collection_name = self.config.get('collection_name', 'medical_multimodal_vectors')
            self.vector_db = Chroma(
                persist_directory=db_path,
                embedding_function=self.embedding_function,
                collection_name=collection_name
            )
            
            # 保留numpy数组作为备用
            self.vectors = []  # 存储向量
            self.documents = []  # 存储文档
            logger.info("Retrieval service initialized with ChromaDB")
        except Exception as e:
            logger.error(f"Error initializing retrieval service: {e}")
            raise
    
    def add_documents(self, vectors: np.ndarray, documents: List[Dict[str, Any]]):
        """
        添加文档到检索系统
        
        Args:
            vectors: 文档向量矩阵
            documents: 文档元数据列表
        """
        try:
            if vectors.size == 0 or not documents:
                return
            
            # 确保向量是二维的
            if vectors.ndim == 1:
                vectors = vectors.reshape(1, -1)
            
            # 准备ChromaDB的文档和元数据
            chroma_documents = []
            chroma_metadatas = []
            
            for i, doc in enumerate(documents):
                # 提取文档内容
                content = doc.get('content', doc.get('text', ''))
                if not content:
                    content = f"Document {i}: {doc.get('title', 'Untitled')}"
                
                chroma_documents.append(content)
                
                # 准备元数据
                metadata = {
                    'id': doc.get('id', f'doc_{i}'),
                    'title': doc.get('title', ''),
                    'source': doc.get('source', ''),
                    'category': doc.get('category', ''),
                    'timestamp': doc.get('timestamp', datetime.now().isoformat()),
                    'metadata': doc.get('metadata', {})
                }
                chroma_metadatas.append(metadata)
            
            # 添加到ChromaDB
            self.vector_db.add_documents(
                documents=chroma_documents,
                metadatas=chroma_metadatas,
                embeddings=vectors.tolist()
            )
            
            # 同时保留numpy数组作为备用
            start_idx = len(self.vectors)
            self.vectors.extend(vectors.tolist())
            
            # 存储文档元数据到本地字典
            for i, doc in enumerate(documents):
                doc_id = start_idx + i
                self.metadata_db[doc_id] = {
                    'id': doc_id,
                    'content': doc.get('content', ''),
                    'title': doc.get('title', ''),
                    'source': doc.get('source', ''),
                    'category': doc.get('category', ''),
                    'timestamp': doc.get('timestamp', datetime.now().isoformat()),
                    'metadata': doc.get('metadata', {})
                }
            
            logger.info(f"Added {len(documents)} documents to ChromaDB and local storage")
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def retrieve_documents(self, query_vector: np.ndarray, top_k: int = 10, 
                          strategy: str = None, query_text: str = None) -> List[Dict[str, Any]]:
        """
        检索相关文档
        
        Args:
            query_vector: 查询向量
            top_k: 返回文档数量
            strategy: 检索策略
            
        Returns:
            检索到的文档列表
        """
        try:
            print("=" * 50)
            print("🔍 文档检索开始")
            print("=" * 50)
            logger.info("开始文档检索...")
            
            # 1. 获取用户输入
            print("==========")
            print("获取用户输入开始")
            print("==========")
            logger.info(f"获取用户输入细节日志：向量维度={len(query_vector) if query_vector is not None else 'None'}, top_k={top_k}, strategy='{strategy}'")
            logger.info("获取用户输入成功")
            print("获取用户输入结束")
            print("==========")
            
            # 2. 用户数据处理
            print("==========")
            print("用户数据处理开始")
            print("==========")
            logger.info("用户数据处理的细节日志：开始验证检索参数")
            
            if self.vector_db._collection.count() == 0:
                logger.warning("向量数据库为空，无法检索")
                return []
            
            # 使用指定的检索策略
            strategy = strategy or self.current_strategy
            if strategy not in self.retrieval_strategies:
                strategy = 'semantic'
                logger.info(f"使用默认检索策略: {strategy}")
            
            logger.info(f"检索策略: {strategy}")
            logger.info(f"相似度阈值: {self.similarity_threshold}")
            logger.info("用户数据处理完成")
            logger.info("用户数据处理成功")
            print("==========")
            
            # 3. 执行检索
            print("==========")
            print("执行检索开始")
            print("==========")
            logger.info("执行检索的细节日志：开始执行文档检索")
            
            # 执行检索
            results = self.retrieval_strategies[strategy](query_vector, top_k, query_text)
            logger.info(f"初步检索完成，找到 {len(results)} 个文档")
            
            # 过滤低相似度结果
            filtered_results = [
                result for result in results 
                if result.get('similarity', 0) >= self.similarity_threshold
            ]
            logger.info(f"相似度过滤完成，保留 {len(filtered_results)} 个文档（阈值: {self.similarity_threshold:.1%}）")
            
            # 记录相似度分布信息
            if results:
                similarities = [result.get('similarity', 0) for result in results]
                max_sim = max(similarities)
                min_sim = min(similarities)
                avg_sim = sum(similarities) / len(similarities)
                logger.info(f"相似度分布: 最高={max_sim:.3f}, 最低={min_sim:.3f}, 平均={avg_sim:.3f}")
            
            final_results = filtered_results[:top_k]
            logger.info(f"最终返回 {len(final_results)} 个文档")
            
            # 如果没有相关结果，记录警告
            if not final_results:
                logger.warning(f"⚠️ 没有找到相似度大于 {self.similarity_threshold:.1%} 的相关文档")
                if results:
                    logger.warning(f"最高相似度仅为: {max_sim:.3f}")
                else:
                    logger.warning("知识库中没有任何文档")
            logger.info("执行检索成功")
            print("执行检索结束")
            print("==========")
            
            # 4. 返回用户结果
            print("==========")
            print("返回用户结果开始")
            print("==========")
            logger.info("返回用户结果的细节日志：开始构建检索结果")
            logger.info(f"检索结果数量: {len(final_results)}")
            for i, result in enumerate(final_results):
                similarity = result.get('similarity', 0)
                title = result.get('title', '无标题')
                logger.info(f"结果 {i+1}: 相似度={similarity:.3f}, 标题='{title}'")
            logger.info("返回用户结果成功")
            print("返回用户结果结束")
            print("==========")
            
            print("=" * 50)
            print("🎉 文档检索完成")
            print("=" * 50)
            logger.info("文档检索成功完成")
            
            return final_results
            
        except Exception as e:
            print("=" * 50)
            print("❌ 文档检索失败")
            print("=" * 50)
            logger.error(f"文档检索失败: {e}")
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    def _semantic_retrieval(self, query_vector: np.ndarray, top_k: int, query_text: str = None) -> List[Dict[str, Any]]:
        """
        语义检索策略
        
        Args:
            query_vector: 查询向量
            top_k: 返回文档数量
            query_text: 查询文本（用于ChromaDB文本搜索）
            
        Returns:
            检索结果列表
        """
        try:
            # 检查ChromaDB是否有数据
            if self.vector_db._collection.count() == 0:
                logger.warning("ChromaDB中没有可检索的文档")
                return []
            
            # 使用用户的实际查询文本进行检索
            if not query_text:
                logger.warning("没有提供查询文本，无法进行语义检索")
                return []
            
            logger.info(f"使用查询文本进行语义检索: '{query_text}'")
            
            results = self.vector_db.similarity_search_with_score(
                query=query_text,
                k=top_k * 2,  # 获取更多候选结果用于后续过滤
                filter=None
            )
            
            # 转换结果格式
            formatted_results = []
            for doc, score in results:
                result = {
                    'content': doc.page_content,
                    'title': doc.metadata.get('title', ''),
                    'source': doc.metadata.get('source', ''),
                    'category': doc.metadata.get('category', ''),
                    'timestamp': doc.metadata.get('timestamp', ''),
                    'metadata': doc.metadata,
                    'similarity': float(score)
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in semantic retrieval: {e}")
            return []
    
    def _hybrid_retrieval(self, query_vector: np.ndarray, top_k: int, query_text: str = None) -> List[Dict[str, Any]]:
        """
        混合检索策略（语义 + 关键词）
        
        Args:
            query_vector: 查询向量
            top_k: 返回文档数量
            query_text: 查询文本
            
        Returns:
            检索结果列表
        """
        try:
            # 先进行语义检索
            semantic_results = self._semantic_retrieval(query_vector, top_k * 2, query_text)
            
            # 这里可以添加关键词检索逻辑
            # 目前简单返回语义检索结果
            return semantic_results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in hybrid retrieval: {e}")
            return []
    
    def _rerank_retrieval(self, query_vector: np.ndarray, top_k: int, query_text: str = None) -> List[Dict[str, Any]]:
        """
        重排序检索策略
        
        Args:
            query_vector: 查询向量
            top_k: 返回文档数量
            query_text: 查询文本
            
        Returns:
            检索结果列表
        """
        try:
            # 先获取更多候选文档
            candidates = self._semantic_retrieval(query_vector, top_k * 3, query_text)
            
            # 这里可以添加重排序逻辑
            # 目前简单返回前top_k个结果
            return candidates[:top_k]
            
        except Exception as e:
            logger.error(f"Error in rerank retrieval: {e}")
            return []
    
    def search_by_keywords(self, keywords: List[str], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        基于关键词搜索文档
        
        Args:
            keywords: 关键词列表
            top_k: 返回文档数量
            
        Returns:
            搜索结果列表
        """
        try:
            results = []
            keyword_set = set(keywords)
            
            for doc_id, doc in self.metadata_db.items():
                # 简单的关键词匹配
                content = doc.get('content', '').lower()
                title = doc.get('title', '').lower()
                
                # 计算匹配的关键词数量
                matches = sum(1 for keyword in keyword_set if keyword.lower() in content or keyword.lower() in title)
                
                if matches > 0:
                    doc_copy = doc.copy()
                    doc_copy['keyword_matches'] = matches
                    doc_copy['similarity'] = matches / len(keyword_set)
                    results.append(doc_copy)
            
            # 按匹配度排序
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            文档信息
        """
        return self.metadata_db.get(doc_id)
    
    def get_documents_by_category(self, category: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        根据类别获取文档
        
        Args:
            category: 文档类别
            top_k: 返回文档数量
            
        Returns:
            文档列表
        """
        try:
            results = []
            for doc in self.metadata_db.values():
                if doc.get('category', '').lower() == category.lower():
                    results.append(doc)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error getting documents by category: {e}")
            return []
    
    def get_documents_by_source(self, source: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        根据来源获取文档
        
        Args:
            source: 文档来源
            top_k: 返回文档数量
            
        Returns:
            文档列表
        """
        try:
            results = []
            for doc in self.metadata_db.values():
                if doc.get('source', '').lower() == source.lower():
                    results.append(doc)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error getting documents by source: {e}")
            return []
    
    def update_document(self, doc_id: int, updates: Dict[str, Any]):
        """
        更新文档信息
        
        Args:
            doc_id: 文档ID
            updates: 更新内容
        """
        try:
            if doc_id in self.metadata_db:
                self.metadata_db[doc_id].update(updates)
                logger.info(f"Updated document {doc_id}")
            else:
                logger.warning(f"Document {doc_id} not found")
                
        except Exception as e:
            logger.error(f"Error updating document: {e}")
    
    def delete_document(self, doc_id: int):
        """
        删除文档
        
        Args:
            doc_id: 文档ID
        """
        try:
            if doc_id in self.metadata_db:
                del self.metadata_db[doc_id]
                logger.info(f"Deleted document {doc_id}")
            else:
                logger.warning(f"Document {doc_id} not found")
                
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取检索系统统计信息
        
        Returns:
            统计信息
        """
        try:
            total_docs = len(self.metadata_db)
            categories = set(doc.get('category', '') for doc in self.metadata_db.values())
            sources = set(doc.get('source', '') for doc in self.metadata_db.values())
            
            return {
                'total_documents': total_docs,
                'vector_database_size': self.vector_db._collection.count(),
                'categories': list(categories),
                'sources': list(sources),
                'retrieval_strategy': self.current_strategy,
                'similarity_threshold': self.similarity_threshold
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def save_metadata(self, metadata_path: str):
        """
        保存元数据到文件
        
        Args:
            metadata_path: 元数据文件路径
        """
        try:
            os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata_db, f, ensure_ascii=False, indent=2)
            logger.info(f"Metadata saved to {metadata_path}")
            
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            raise
    
    def load_metadata(self, metadata_path: str):
        """
        从文件加载元数据
        
        Args:
            metadata_path: 元数据文件路径
        """
        try:
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata_db = json.load(f)
                logger.info(f"Metadata loaded from {metadata_path}")
            else:
                logger.warning(f"Metadata file not found: {metadata_path}")
                
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            raise
    
    def clear_all(self):
        """清空所有数据"""
        try:
            self.vector_db.reset()
            self.metadata_db.clear()
            logger.info("All data cleared")
        except Exception as e:
            logger.error(f"Error clearing data: {e}")
            raise


class RetrievalServiceFactory:
    """检索服务工厂类"""
    
    @staticmethod
    def create_retrieval_service(config_path: str = None) -> RetrievalService:
        """
        创建检索服务实例
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            检索服务实例
        """
        # 默认配置
        default_config = {
            'vector_dim': 384,
            'max_results': 20,
            'similarity_threshold': 0.7,
            'retrieval_strategy': 'semantic'
        }
        
        # 如果提供了配置文件，则加载配置
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Error loading config file: {e}, using default config")
        
        return RetrievalService(default_config)


if __name__ == "__main__":
    # 测试检索服务
    config = {
        'vector_dim': 384,
        'max_results': 10,
        'similarity_threshold': 0.5,
        'retrieval_strategy': 'semantic'
    }
    
    retrieval_service = RetrievalService(config)
    
    # 模拟添加文档
    test_documents = [
        {
            'content': '胸痛是心肌梗死的常见症状，通常表现为胸骨后压榨性疼痛',
            'title': '心肌梗死症状',
            'category': '心血管疾病',
            'source': '医学教科书'
        },
        {
            'content': '呼吸困难可能由多种原因引起，包括肺部疾病和心脏疾病',
            'title': '呼吸困难原因',
            'category': '呼吸系统疾病',
            'source': '临床指南'
        },
        {
            'content': '发热是感染性疾病的主要症状之一，需要及时治疗',
            'title': '发热症状',
            'category': '感染性疾病',
            'source': '医学期刊'
        }
    ]
    
    # 模拟向量（实际使用中应该通过向量化服务生成）
    test_vectors = np.random.rand(len(test_documents), 384).astype('float32')
    
    # 添加文档
    retrieval_service.add_documents(test_vectors, test_documents)
    
    # 测试检索
    query_vector = np.random.rand(384).astype('float32')
    results = retrieval_service.retrieve_documents(query_vector, top_k=2)
    
    print(f"Retrieved {len(results)} documents")
    for result in results:
        print(f"Title: {result['title']}, Similarity: {result['similarity']:.3f}")
    
    # 测试关键词搜索
    keyword_results = retrieval_service.search_by_keywords(['胸痛', '心肌梗死'], top_k=2)
    print(f"\nKeyword search results: {len(keyword_results)}")
    
    # 获取统计信息
    stats = retrieval_service.get_statistics()
    print(f"\nStatistics: {stats}")
