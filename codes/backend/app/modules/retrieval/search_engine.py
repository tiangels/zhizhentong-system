"""
检索引擎
执行向量相似度检索和结果排序
"""

import time
import numpy as np
from typing import Dict, Any, List, Optional
from collections import defaultdict


class RetrievalEngine:
    """检索引擎"""
    
    def __init__(self):
        """初始化检索引擎"""
        self.stats = defaultdict(int)
        
        # 模拟知识库
        self.knowledge_base = [
            {
                'id': '1',
                'title': '感冒症状与治疗',
                'content': '感冒是一种常见的上呼吸道感染疾病，主要症状包括鼻塞、流涕、咳嗽、发热等。治疗方法包括休息、多喝水、对症治疗等。',
                'category': 'disease',
                'tags': ['感冒', '上呼吸道感染', '症状'],
                'source': '医学百科',
                'vector': np.random.randn(768)
            },
            {
                'id': '2',
                'title': '发热的处理方法',
                'content': '发热是身体对感染或炎症的正常反应。轻度发热可以通过多喝水、休息来缓解。高热需要及时就医。',
                'category': 'treatment',
                'tags': ['发热', '治疗', '护理'],
                'source': '临床指南',
                'vector': np.random.randn(768)
            },
            {
                'id': '3',
                'title': '咳嗽的分类与治疗',
                'content': '咳嗽分为干咳和湿咳。干咳多见于病毒感染，湿咳多见于细菌感染。治疗需要根据病因进行。',
                'category': 'symptom',
                'tags': ['咳嗽', '分类', '治疗'],
                'source': '呼吸科指南',
                'vector': np.random.randn(768)
            },
            {
                'id': '4',
                'title': '高血压预防',
                'content': '高血压是一种常见的慢性疾病，预防措施包括低盐饮食、适量运动、戒烟限酒、定期体检等。',
                'category': 'disease',
                'tags': ['高血压', '慢性病', '预防'],
                'source': '心血管指南',
                'vector': np.random.randn(768)
            },
            {
                'id': '5',
                'title': '糖尿病饮食指导',
                'content': '糖尿病患者需要控制饮食，建议低糖、低脂、高纤维饮食，定时定量，避免暴饮暴食。',
                'category': 'treatment',
                'tags': ['糖尿病', '饮食', '治疗'],
                'source': '内分泌指南',
                'vector': np.random.randn(768)
            }
        ]
    
    def retrieve(self, query_vector: np.ndarray, query_text: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行检索
        
        Args:
            query_vector: 查询向量
            query_text: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件
            
        Returns:
            Dict[str, Any]: 检索结果
        """
        start_time = time.time()
        self.stats['total_retrieved'] += 1
        
        # 向量检索
        vector_results = self._vector_retrieve(query_vector, top_k)
        
        # 混合检索
        hybrid_results = self._hybrid_retrieve(query_text, vector_results, filters)
        
        # 结果优化
        optimized_results = self._optimize_results(hybrid_results, top_k)
        
        processing_time = time.time() - start_time
        self.stats['total_processing_time'] += processing_time
        
        return {
            'results': optimized_results,
            'query': query_text,
            'processing_time': processing_time,
            'total_found': len(optimized_results)
        }
    
    def _vector_retrieve(self, query_vector: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        """
        向量检索
        
        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 检索结果
        """
        results = []
        
        for item in self.knowledge_base:
            # 计算相似度
            similarity = self._calculate_similarity(query_vector, item['vector'])
            
            results.append({
                'item': item,
                'similarity': similarity,
                'score': similarity
            })
        
        # 按相似度排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results[:top_k]
    
    def _hybrid_retrieve(self, query_text: str, vector_results: List[Dict[str, Any]], filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        混合检索
        
        Args:
            query_text: 查询文本
            vector_results: 向量检索结果
            filters: 过滤条件
            
        Returns:
            List[Dict[str, Any]]: 混合检索结果
        """
        hybrid_results = []
        
        for result in vector_results:
            item = result['item']
            base_score = result['score']
            
            # 文本匹配加分
            text_score = self._calculate_text_score(query_text, item)
            
            # 过滤条件检查
            if filters and not self._check_filters(item, filters):
                continue
            
            # 综合评分
            final_score = 0.7 * base_score + 0.3 * text_score
            
            hybrid_results.append({
                'item': item,
                'vector_score': base_score,
                'text_score': text_score,
                'final_score': final_score
            })
        
        return hybrid_results
    
    def _calculate_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
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
    
    def _calculate_text_score(self, query_text: str, item: Dict[str, Any]) -> float:
        """
        计算文本匹配分数
        
        Args:
            query_text: 查询文本
            item: 知识项
            
        Returns:
            float: 文本匹配分数
        """
        # 简单的关键词匹配
        query_words = set(query_text.split())
        title_words = set(item['title'].split())
        content_words = set(item['content'].split())
        tag_words = set(item['tags'])
        
        # 标题匹配权重最高
        title_matches = len(query_words & title_words)
        title_score = title_matches / len(title_words) if title_words else 0
        
        # 内容匹配
        content_matches = len(query_words & content_words)
        content_score = content_matches / len(content_words) if content_words else 0
        
        # 标签匹配
        tag_matches = len(query_words & tag_words)
        tag_score = tag_matches / len(tag_words) if tag_words else 0
        
        # 综合分数
        final_score = 0.5 * title_score + 0.3 * content_score + 0.2 * tag_score
        
        return min(final_score, 1.0)
    
    def _check_filters(self, item: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        检查过滤条件
        
        Args:
            item: 知识项
            filters: 过滤条件
            
        Returns:
            bool: 是否通过过滤
        """
        for key, value in filters.items():
            if key == 'category' and item.get('category') != value:
                return False
            elif key == 'source' and item.get('source') != value:
                return False
            elif key == 'tags' and not any(tag in item.get('tags', []) for tag in value):
                return False
        
        return True
    
    def _optimize_results(self, results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """
        优化检索结果
        
        Args:
            results: 检索结果
            top_k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 优化后的结果
        """
        # 按最终分数排序
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # 去重（基于ID）
        seen_ids = set()
        unique_results = []
        
        for result in results:
            item_id = result['item']['id']
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                unique_results.append(result)
        
        return unique_results[:top_k]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取检索统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'total_retrieved': self.stats['total_retrieved'],
            'total_processing_time': self.stats['total_processing_time'],
            'avg_processing_time': (
                self.stats['total_processing_time'] / self.stats['total_retrieved']
                if self.stats['total_retrieved'] > 0 else 0
            ),
            'knowledge_base_size': len(self.knowledge_base)
        }
