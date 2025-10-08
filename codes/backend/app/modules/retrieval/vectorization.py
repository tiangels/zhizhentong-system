"""
向量化处理器
处理文档和查询的向量化
"""

import time
import numpy as np
from typing import Dict, Any, List
from collections import defaultdict


class VectorizationProcessor:
    """向量化处理器"""
    
    def __init__(self):
        """初始化向量化处理器"""
        self.stats = defaultdict(int)
        self.vector_dimension = 768  # 向量维度
        
        # 模拟词向量
        self.word_vectors = {
            '发热': np.random.randn(self.vector_dimension),
            '头痛': np.random.randn(self.vector_dimension),
            '腹痛': np.random.randn(self.vector_dimension),
            '咳嗽': np.random.randn(self.vector_dimension),
            '感冒': np.random.randn(self.vector_dimension),
            '治疗': np.random.randn(self.vector_dimension),
            '症状': np.random.randn(self.vector_dimension),
            '药物': np.random.randn(self.vector_dimension),
            '休息': np.random.randn(self.vector_dimension),
            '多喝水': np.random.randn(self.vector_dimension)
        }
    
    def process_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理文档向量化
        
        Args:
            documents: 文档列表
            
        Returns:
            Dict[str, Any]: 向量化结果
        """
        start_time = time.time()
        self.stats['total_documents_processed'] += len(documents)
        
        document_vectors = []
        vector_ids = []
        
        for doc in documents:
            # 文档向量化
            doc_vector = self._encode_document(doc)
            document_vectors.append(doc_vector)
            
            # 生成向量ID
            vector_id = f"doc_{doc.get('id', len(vector_ids))}"
            vector_ids.append(vector_id)
        
        # 向量优化
        optimized_vectors = self._optimize_vectors(document_vectors)
        
        # 构建索引
        index = self._build_index(optimized_vectors, vector_ids)
        
        processing_time = time.time() - start_time
        self.stats['total_processing_time'] += processing_time
        
        return {
            'vectors': optimized_vectors,
            'vector_ids': vector_ids,
            'index': index,
            'processing_time': processing_time
        }
    
    def process_query(self, query: str) -> np.ndarray:
        """
        处理查询向量化
        
        Args:
            query: 查询文本
            
        Returns:
            np.ndarray: 查询向量
        """
        start_time = time.time()
        self.stats['total_queries_processed'] += 1
        
        # 查询向量化
        query_vector = self._encode_query(query)
        
        # 向量优化
        optimized_vector = self._optimize_vector(query_vector)
        
        processing_time = time.time() - start_time
        self.stats['total_processing_time'] += processing_time
        
        return optimized_vector
    
    def _encode_document(self, document: Dict[str, Any]) -> np.ndarray:
        """
        编码文档
        
        Args:
            document: 文档数据
            
        Returns:
            np.ndarray: 文档向量
        """
        # 提取文档文本
        title = document.get('title', '')
        content = document.get('content', '')
        tags = document.get('tags', [])
        
        # 合并文本
        text = f"{title} {' '.join(tags)} {content}"
        
        # 分词并计算向量
        words = text.split()
        word_vectors = []
        
        for word in words:
            if word in self.word_vectors:
                word_vectors.append(self.word_vectors[word])
        
        if word_vectors:
            # 平均池化
            doc_vector = np.mean(word_vectors, axis=0)
        else:
            # 如果没有匹配的词，使用随机向量
            doc_vector = np.random.randn(self.vector_dimension)
        
        # 归一化
        doc_vector = doc_vector / (np.linalg.norm(doc_vector) + 1e-8)
        
        return doc_vector
    
    def _encode_query(self, query: str) -> np.ndarray:
        """
        编码查询
        
        Args:
            query: 查询文本
            
        Returns:
            np.ndarray: 查询向量
        """
        # 分词并计算向量
        words = query.split()
        word_vectors = []
        
        for word in words:
            if word in self.word_vectors:
                word_vectors.append(self.word_vectors[word])
        
        if word_vectors:
            # 平均池化
            query_vector = np.mean(word_vectors, axis=0)
        else:
            # 如果没有匹配的词，使用随机向量
            query_vector = np.random.randn(self.vector_dimension)
        
        # 归一化
        query_vector = query_vector / (np.linalg.norm(query_vector) + 1e-8)
        
        return query_vector
    
    def _optimize_vectors(self, vectors: List[np.ndarray]) -> List[np.ndarray]:
        """
        优化向量
        
        Args:
            vectors: 向量列表
            
        Returns:
            List[np.ndarray]: 优化后的向量列表
        """
        optimized_vectors = []
        
        for vector in vectors:
            # 向量质量检查
            if np.any(np.isnan(vector)) or np.any(np.isinf(vector)):
                # 如果向量包含无效值，使用零向量
                optimized_vector = np.zeros(self.vector_dimension)
            else:
                optimized_vector = vector
            
            optimized_vectors.append(optimized_vector)
        
        return optimized_vectors
    
    def _optimize_vector(self, vector: np.ndarray) -> np.ndarray:
        """
        优化单个向量
        
        Args:
            vector: 输入向量
            
        Returns:
            np.ndarray: 优化后的向量
        """
        # 向量质量检查
        if np.any(np.isnan(vector)) or np.any(np.isinf(vector)):
            # 如果向量包含无效值，使用零向量
            optimized_vector = np.zeros(self.vector_dimension)
        else:
            optimized_vector = vector
        
        return optimized_vector
    
    def _build_index(self, vectors: List[np.ndarray], vector_ids: List[str]) -> Dict[str, Any]:
        """
        构建向量索引
        
        Args:
            vectors: 向量列表
            vector_ids: 向量ID列表
            
        Returns:
            Dict[str, Any]: 索引结构
        """
        # 构建简单的向量索引
        index = {
            'vectors': vectors,
            'vector_ids': vector_ids,
            'dimension': self.vector_dimension,
            'total_vectors': len(vectors)
        }
        
        return index
    
    def calculate_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """
        计算向量相似度
        
        Args:
            vector1: 向量1
            vector2: 向量2
            
        Returns:
            float: 相似度分数
        """
        # 计算余弦相似度
        dot_product = np.dot(vector1, vector2)
        norm1 = np.linalg.norm(vector1)
        norm2 = np.linalg.norm(vector2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取向量化统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'total_documents_processed': self.stats['total_documents_processed'],
            'total_queries_processed': self.stats['total_queries_processed'],
            'total_processing_time': self.stats['total_processing_time'],
            'avg_processing_time': (
                self.stats['total_processing_time'] / 
                (self.stats['total_documents_processed'] + self.stats['total_queries_processed'])
                if (self.stats['total_documents_processed'] + self.stats['total_queries_processed']) > 0 else 0
            ),
            'vector_dimension': self.vector_dimension
        }
