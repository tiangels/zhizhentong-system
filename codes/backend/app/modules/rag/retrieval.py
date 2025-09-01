"""
RAG检索模块
基于检索增强生成的医疗知识检索
"""

import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .search_engine import RetrievalEngine
from .query_understanding import QueryUnderstanding
from .vectorization import VectorizationProcessor


class RetrievalInput(BaseModel):
    """检索输入数据模型"""
    query: str
    context: Optional[Dict[str, Any]] = None
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None


class RetrievalOutput(BaseModel):
    """检索输出数据模型"""
    query: str
    retrieved_knowledge: List[Dict[str, Any]]
    relevance_scores: List[float]
    processing_time: float
    total_found: int


class RAGRetrieval:
    """RAG检索器"""
    
    def __init__(self):
        """初始化RAG检索器"""
        self.query_understanding = QueryUnderstanding()
        self.vectorization = VectorizationProcessor()
        self.retrieval_engine = RetrievalEngine()
    
    def retrieve(self, input_data: RetrievalInput) -> RetrievalOutput:
        """
        执行RAG检索
        
        Args:
            input_data: 检索输入数据
            
        Returns:
            RetrievalOutput: 检索结果
        """
        start_time = time.time()
        
        # 查询理解
        query_understanding_result = self.query_understanding.understand_query(input_data.query)
        enhanced_query = query_understanding_result.get('processed_query', input_data.query)
        
        # 向量化
        query_vector = self.vectorization.process_query(enhanced_query)
        
        # 执行检索
        retrieval_result = self.retrieval_engine.retrieve(
            query_vector=query_vector,
            query_text=enhanced_query,
            top_k=input_data.top_k,
            filters=input_data.filters
        )
        
        processing_time = time.time() - start_time
        
        return RetrievalOutput(
            query=input_data.query,
            retrieved_knowledge=retrieval_result['results'],
            relevance_scores=[item.get('score', 0.0) for item in retrieval_result['results']],
            processing_time=processing_time,
            total_found=retrieval_result['total_found']
        )
