"""
查询理解器
理解用户查询意图，提取关键词，扩展查询
"""

import re
import time
from typing import Dict, Any, List
from collections import defaultdict


class QueryUnderstanding:
    """查询理解器"""
    
    def __init__(self):
        """初始化查询理解器"""
        self.stats = defaultdict(int)
        
        # 医疗意图词典
        self.intent_patterns = {
            'diagnosis': [
                r'诊断', r'什么病', r'得了什么', r'可能是什么', r'怀疑',
                r'症状', r'表现', r'征兆', r'迹象'
            ],
            'treatment': [
                r'治疗', r'怎么治', r'怎么办', r'如何治疗', r'用药',
                r'药物', r'吃什么药', r'治疗方法', r'护理'
            ],
            'symptom': [
                r'症状', r'表现', r'感觉', r'不适', r'疼痛',
                r'难受', r'不舒服', r'异常'
            ],
            'prevention': [
                r'预防', r'避免', r'防止', r'预防措施', r'保健',
                r'养生', r'健康', r'生活方式'
            ],
            'medicine': [
                r'药物', r'药品', r'药', r'副作用', r'禁忌',
                r'用法', r'用量', r'注意事项'
            ]
        }
        
        # 医疗关键词词典
        self.medical_keywords = {
            'symptoms': ['发热', '头痛', '腹痛', '咳嗽', '鼻塞', '咽痛', '胸痛', '恶心', '呕吐', '腹泻'],
            'diseases': ['感冒', '流感', '肺炎', '胃炎', '肠炎', '高血压', '糖尿病', '心脏病'],
            'body_parts': ['头', '胸', '腹', '胃', '肺', '心', '肝', '肾', '喉咙', '鼻子'],
            'treatments': ['休息', '多喝水', '吃药', '打针', '手术', '理疗', '针灸'],
            'medicines': ['感冒药', '退烧药', '消炎药', '止痛药', '维生素']
        }
    
    def understand_query(self, user_query: str) -> Dict[str, Any]:
        """
        理解用户查询
        
        Args:
            user_query: 用户查询
            
        Returns:
            Dict[str, Any]: 理解结果
        """
        start_time = time.time()
        self.stats['total_understood'] += 1
        
        # 意图分类
        intent = self._classify_intent(user_query)
        
        # 关键词提取
        keywords = self._extract_keywords(user_query)
        
        # 查询扩展
        expanded_query = self._expand_query(user_query, keywords)
        
        # 语言处理
        processed_query = self._process_language(expanded_query)
        
        processing_time = time.time() - start_time
        self.stats['total_processing_time'] += processing_time
        
        return {
            'original_query': user_query,
            'intent': intent,
            'keywords': keywords,
            'expanded_query': expanded_query,
            'processed_query': processed_query,
            'processing_time': processing_time
        }
    
    def _classify_intent(self, query: str) -> str:
        """
        分类查询意图
        
        Args:
            query: 用户查询
            
        Returns:
            str: 查询意图
        """
        intent_scores = defaultdict(int)
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    intent_scores[intent] += 1
        
        if intent_scores:
            # 返回得分最高的意图
            return max(intent_scores.items(), key=lambda x: x[1])[0]
        
        return 'general'
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        提取关键词
        
        Args:
            query: 用户查询
            
        Returns:
            List[str]: 关键词列表
        """
        keywords = []
        
        # 从各个类别中提取关键词
        for category, word_list in self.medical_keywords.items():
            for word in word_list:
                if word in query:
                    keywords.append(word)
        
        # 提取数字和时间表达
        number_patterns = [
            r'\d+度',  # 温度
            r'\d+天',  # 天数
            r'\d+小时',  # 小时
            r'\d+分钟'   # 分钟
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, query)
            keywords.extend(matches)
        
        return list(set(keywords))  # 去重
    
    def _expand_query(self, query: str, keywords: List[str]) -> str:
        """
        扩展查询
        
        Args:
            query: 原始查询
            keywords: 关键词列表
            
        Returns:
            str: 扩展后的查询
        """
        expanded_terms = []
        
        # 根据关键词扩展相关术语
        for keyword in keywords:
            if keyword in self.medical_keywords['symptoms']:
                # 症状相关扩展
                if keyword == '发热':
                    expanded_terms.extend(['发烧', '体温高', '低热', '高热'])
                elif keyword == '头痛':
                    expanded_terms.extend(['头疼', '头部疼痛'])
                elif keyword == '腹痛':
                    expanded_terms.extend(['肚子疼', '腹部疼痛'])
            
            elif keyword in self.medical_keywords['diseases']:
                # 疾病相关扩展
                if keyword == '感冒':
                    expanded_terms.extend(['上呼吸道感染', '普通感冒'])
                elif keyword == '肺炎':
                    expanded_terms.extend(['肺部感染', '支气管肺炎'])
        
        # 构建扩展查询
        expanded_query = query
        if expanded_terms:
            expanded_query += ' ' + ' '.join(expanded_terms)
        
        return expanded_query
    
    def _process_language(self, query: str) -> str:
        """
        语言处理
        
        Args:
            query: 查询文本
            
        Returns:
            str: 处理后的查询
        """
        # 标准化处理
        processed_query = query
        
        # 替换同义词
        synonyms = {
            '发烧': '发热',
            '头疼': '头痛',
            '肚子疼': '腹痛',
            '嗓子疼': '咽痛',
            '拉肚子': '腹泻'
        }
        
        for synonym, standard in synonyms.items():
            processed_query = processed_query.replace(synonym, standard)
        
        # 移除停用词
        stop_words = ['的', '了', '是', '在', '有', '和', '与', '或', '但', '而']
        for stop_word in stop_words:
            processed_query = processed_query.replace(stop_word, ' ')
        
        # 清理多余空格
        processed_query = re.sub(r'\s+', ' ', processed_query.strip())
        
        return processed_query
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取理解统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'total_understood': self.stats['total_understood'],
            'total_processing_time': self.stats['total_processing_time'],
            'avg_processing_time': (
                self.stats['total_processing_time'] / self.stats['total_understood']
                if self.stats['total_understood'] > 0 else 0
            )
        }
