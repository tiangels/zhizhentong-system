"""
文本处理器
处理文本分析、情感分析、实体识别等
"""

import time
import re
from typing import Dict, Any, List
from collections import defaultdict


class TextProcessor:
    """文本处理器"""
    
    def __init__(self):
        """初始化文本处理器"""
        # 医疗相关实体词典
        self.medical_entities = {
            'symptoms': ['发热', '头痛', '腹痛', '咳嗽', '恶心', '呕吐', '腹泻', '乏力', '食欲不振'],
            'diseases': ['感冒', '流感', '肺炎', '胃炎', '高血压', '糖尿病', '心脏病'],
            'medications': ['阿司匹林', '布洛芬', '感冒药', '退烧药', '消炎药'],
            'body_parts': ['头部', '胸部', '腹部', '四肢', '心脏', '肺部', '胃部']
        }
        
        # 情感词典
        self.sentiment_words = {
            'positive': ['好', '舒服', '改善', '缓解', '有效', '满意'],
            'negative': ['痛', '难受', '严重', '恶化', '担心', '焦虑'],
            'neutral': ['一般', '正常', '稳定', '持续', '反复']
        }
    
    def process_text(self, text: str) -> Dict[str, Any]:
        """
        处理文本
        
        Args:
            text: 输入文本
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        start_time = time.time()
        
        # 文本预处理
        cleaned_text = self._preprocess_text(text)
        
        # 实体识别
        entities = self._extract_entities(cleaned_text)
        
        # 情感分析
        sentiment = self._analyze_sentiment(cleaned_text)
        
        # 关键词提取
        keywords = self._extract_keywords(cleaned_text)
        
        # 文本分类
        text_category = self._classify_text(cleaned_text)
        
        processing_time = time.time() - start_time
        
        return {
            'original_text': text,
            'cleaned_text': cleaned_text,
            'entities': entities,
            'sentiment': sentiment,
            'keywords': keywords,
            'category': text_category,
            'confidence': self._calculate_confidence(entities, sentiment),
            'processing_time': processing_time
        }
    
    def _preprocess_text(self, text: str) -> str:
        """文本预处理"""
        # 去除多余空格
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 去除特殊字符（保留中文、英文、数字）
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', text)
        
        return text
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """提取实体"""
        entities = []
        
        for entity_type, entity_list in self.medical_entities.items():
            for entity in entity_list:
                if entity in text:
                    entities.append({
                        'text': entity,
                        'type': entity_type,
                        'start': text.find(entity),
                        'end': text.find(entity) + len(entity)
                    })
        
        return entities
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """情感分析"""
        sentiment_scores = {
            'positive': 0,
            'negative': 0,
            'neutral': 0
        }
        
        for sentiment_type, words in self.sentiment_words.items():
            for word in words:
                if word in text:
                    sentiment_scores[sentiment_type] += 1
        
        # 确定主要情感
        max_score = max(sentiment_scores.values())
        if max_score == 0:
            primary_sentiment = 'neutral'
        else:
            primary_sentiment = max(sentiment_scores, key=sentiment_scores.get)
        
        return {
            'primary': primary_sentiment,
            'scores': sentiment_scores,
            'confidence': max_score / (sum(sentiment_scores.values()) + 1)
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取（基于词频）
        words = text.split()
        word_freq = defaultdict(int)
        
        for word in words:
            if len(word) > 1:  # 过滤单字符
                word_freq[word] += 1
        
        # 返回频率最高的前5个词
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        return [word for word, freq in keywords]
    
    def _classify_text(self, text: str) -> str:
        """文本分类"""
        # 基于关键词的简单分类
        if any(word in text for word in ['症状', '疼痛', '不适']):
            return 'symptom_description'
        elif any(word in text for word in ['治疗', '药物', '用药']):
            return 'treatment_inquiry'
        elif any(word in text for word in ['检查', '诊断', '结果']):
            return 'diagnosis_inquiry'
        else:
            return 'general_inquiry'
    
    def _calculate_confidence(self, entities: List[Dict[str, Any]], sentiment: Dict[str, Any]) -> float:
        """计算置信度"""
        # 基于实体数量和情感分析的置信度
        entity_confidence = min(len(entities) / 10.0, 1.0)  # 最多10个实体
        sentiment_confidence = sentiment.get('confidence', 0.0)
        
        return (entity_confidence + sentiment_confidence) / 2.0
