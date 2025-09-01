"""
症状分析器
分析症状描述，提取症状特征和严重程度
"""

import re
import time
from typing import Dict, Any, List
from collections import defaultdict


class SymptomAnalyzer:
    """症状分析器"""
    
    def __init__(self):
        """初始化症状分析器"""
        self.stats = defaultdict(int)
        
        # 症状词典
        self.symptom_dict = {
            '发热': {'severity_levels': ['低热', '中热', '高热'], 'body_parts': ['全身']},
            '头痛': {'severity_levels': ['轻微', '中度', '剧烈'], 'body_parts': ['头部']},
            '腹痛': {'severity_levels': ['轻微', '中度', '剧烈'], 'body_parts': ['腹部']},
            '咳嗽': {'severity_levels': ['轻微', '中度', '剧烈'], 'body_parts': ['胸部', '喉咙']},
            '鼻塞': {'severity_levels': ['轻微', '中度', '严重'], 'body_parts': ['鼻子']},
            '咽痛': {'severity_levels': ['轻微', '中度', '剧烈'], 'body_parts': ['喉咙']},
            '胸痛': {'severity_levels': ['轻微', '中度', '剧烈'], 'body_parts': ['胸部']},
            '恶心': {'severity_levels': ['轻微', '中度', '严重'], 'body_parts': ['胃部']},
            '呕吐': {'severity_levels': ['轻微', '中度', '剧烈'], 'body_parts': ['胃部']},
            '腹泻': {'severity_levels': ['轻微', '中度', '严重'], 'body_parts': ['腹部']},
            '眩晕': {'severity_levels': ['轻微', '中度', '严重'], 'body_parts': ['头部']},
            '失眠': {'severity_levels': ['轻微', '中度', '严重'], 'body_parts': ['全身']},
            '焦虑': {'severity_levels': ['轻微', '中度', '严重'], 'body_parts': ['心理']},
            '抑郁': {'severity_levels': ['轻微', '中度', '严重'], 'body_parts': ['心理']},
            '乏力': {'severity_levels': ['轻微', '中度', '严重'], 'body_parts': ['全身']},
            '食欲不振': {'severity_levels': ['轻微', '中度', '严重'], 'body_parts': ['胃部']},
            '心悸': {'severity_levels': ['轻微', '中度', '剧烈'], 'body_parts': ['胸部']},
            '气短': {'severity_levels': ['轻微', '中度', '严重'], 'body_parts': ['胸部']},
            '水肿': {'severity_levels': ['轻微', '中度', '严重'], 'body_parts': ['四肢', '面部']}
        }
        
        # 时间表达词典
        self.time_patterns = {
            r'(\d+天前)': 'days_ago',
            r'(\d+周前)': 'weeks_ago',
            r'(\d+个月前)': 'months_ago',
            r'(\d+年前)': 'years_ago',
            r'(昨天)': 'yesterday',
            r'(今天)': 'today',
            r'(刚才)': 'just_now',
            r'(最近)': 'recently'
        }
    
    def analyze_symptoms(self, symptom_text: str) -> Dict[str, Any]:
        """
        分析症状描述
        
        Args:
            symptom_text: 症状描述文本
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        start_time = time.time()
        self.stats['total_analyzed'] += 1
        
        # 症状解析
        parsed_symptoms = self._parse_symptoms(symptom_text)
        
        # 症状标准化
        normalized_symptoms = self._normalize_symptoms(parsed_symptoms)
        
        # 严重程度评估
        severity_scores = self._assess_severity(normalized_symptoms)
        
        # 症状组合分析
        combinations = self._analyze_combinations(normalized_symptoms)
        
        # 时间线分析
        timeline = self._analyze_timeline(symptom_text)
        
        processing_time = time.time() - start_time
        self.stats['total_processing_time'] += processing_time
        
        return {
            'symptoms': [s['name'] for s in normalized_symptoms],  # 只返回症状名称列表
            'severity': severity_scores,
            'combinations': combinations,
            'timeline': timeline,
            'processing_time': processing_time,
            'original_text': symptom_text
        }
    
    def _parse_symptoms(self, text: str) -> List[Dict[str, Any]]:
        """
        解析症状
        
        Args:
            text: 症状文本
            
        Returns:
            List[Dict[str, Any]]: 解析的症状列表
        """
        symptoms = []
        
        for symptom, info in self.symptom_dict.items():
            if symptom in text:
                # 查找严重程度修饰词
                severity = self._find_severity(text, symptom, info['severity_levels'])
                
                # 查找身体部位
                body_parts = self._find_body_parts(text, symptom, info['body_parts'])
                
                symptoms.append({
                    'symptom': symptom,
                    'severity': severity,
                    'body_parts': body_parts,
                    'position': text.find(symptom)
                })
        
        # 按位置排序
        symptoms.sort(key=lambda x: x['position'])
        
        return symptoms
    
    def _find_severity(self, text: str, symptom: str, severity_levels: List[str]) -> str:
        """
        查找严重程度
        
        Args:
            text: 症状文本
            symptom: 症状名称
            severity_levels: 严重程度级别列表
            
        Returns:
            str: 严重程度
        """
        # 在症状前后查找严重程度修饰词
        symptom_pos = text.find(symptom)
        if symptom_pos == -1:
            return 'moderate'
        
        # 查找症状前的修饰词
        before_text = text[max(0, symptom_pos-10):symptom_pos]
        for level in severity_levels:
            if level in before_text:
                return level
        
        # 查找症状后的修饰词
        after_text = text[symptom_pos+len(symptom):symptom_pos+len(symptom)+10]
        for level in severity_levels:
            if level in after_text:
                return level
        
        return 'moderate'
    
    def _find_body_parts(self, text: str, symptom: str, default_parts: List[str]) -> List[str]:
        """
        查找身体部位
        
        Args:
            text: 症状文本
            symptom: 症状名称
            default_parts: 默认身体部位列表
            
        Returns:
            List[str]: 身体部位列表
        """
        # 这里可以实现更复杂的身体部位识别逻辑
        # 目前返回默认部位
        return default_parts
    
    def _normalize_symptoms(self, parsed_symptoms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        标准化症状
        
        Args:
            parsed_symptoms: 解析的症状列表
            
        Returns:
            List[Dict[str, Any]]: 标准化后的症状列表
        """
        normalized = []
        
        for symptom in parsed_symptoms:
            normalized_symptom = {
                'name': symptom['symptom'],
                'severity': symptom['severity'],
                'body_parts': symptom['body_parts'],
                'normalized_name': self._normalize_symptom_name(symptom['symptom'])
            }
            normalized.append(normalized_symptom)
        
        return normalized
    
    def _normalize_symptom_name(self, symptom_name: str) -> str:
        """
        标准化症状名称
        
        Args:
            symptom_name: 症状名称
            
        Returns:
            str: 标准化后的症状名称
        """
        # 症状名称标准化映射
        normalization_map = {
            '头疼': '头痛',
            '肚子疼': '腹痛',
            '拉肚子': '腹泻',
            '嗓子疼': '咽痛',
            '胸闷': '胸痛'
        }
        
        return normalization_map.get(symptom_name, symptom_name)
    
    def _assess_severity(self, symptoms: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        评估严重程度
        
        Args:
            symptoms: 症状列表
            
        Returns:
            Dict[str, float]: 严重程度评分
        """
        severity_scores = {}
        
        for symptom in symptoms:
            name = symptom['name']
            severity = symptom['severity']
            
            # 根据严重程度计算分数
            severity_score = self._calculate_severity_score(severity)
            severity_scores[name] = severity_score
        
        return severity_scores
    
    def _calculate_severity_score(self, severity: str) -> float:
        """
        计算严重程度分数
        
        Args:
            severity: 严重程度描述
            
        Returns:
            float: 严重程度分数
        """
        severity_map = {
            '轻微': 0.3,
            '低热': 0.3,
            '中度': 0.6,
            '中热': 0.6,
            '剧烈': 0.9,
            '高热': 0.9,
            '严重': 0.8
        }
        
        return severity_map.get(severity, 0.5)
    
    def _analyze_combinations(self, symptoms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        分析症状组合
        
        Args:
            symptoms: 症状列表
            
        Returns:
            List[Dict[str, Any]]: 症状组合分析结果
        """
        combinations = []
        
        if len(symptoms) >= 2:
            # 分析常见的症状组合
            symptom_names = [s['name'] for s in symptoms]
            
            # 呼吸道症状组合
            respiratory_symptoms = ['发热', '咳嗽', '鼻塞', '咽痛']
            if any(s in symptom_names for s in respiratory_symptoms):
                combinations.append({
                    'type': 'respiratory',
                    'symptoms': [s for s in symptom_names if s in respiratory_symptoms],
                    'suggested_diagnosis': '上呼吸道感染'
                })
            
            # 消化道症状组合
            digestive_symptoms = ['腹痛', '腹泻', '恶心', '呕吐']
            if any(s in symptom_names for s in digestive_symptoms):
                combinations.append({
                    'type': 'digestive',
                    'symptoms': [s for s in symptom_names if s in digestive_symptoms],
                    'suggested_diagnosis': '急性胃肠炎'
                })
            
            # 神经系统症状组合
            neurological_symptoms = ['头痛', '眩晕', '失眠', '焦虑']
            if any(s in symptom_names for s in neurological_symptoms):
                combinations.append({
                    'type': 'neurological',
                    'symptoms': [s for s in symptom_names if s in neurological_symptoms],
                    'suggested_diagnosis': '偏头痛或紧张性头痛'
                })
        
        return combinations
    
    def _analyze_timeline(self, text: str) -> Dict[str, Any]:
        """
        分析时间线
        
        Args:
            text: 症状文本
            
        Returns:
            Dict[str, Any]: 时间线分析结果
        """
        timeline = {
            'onset_time': None,
            'duration': None,
            'progression': 'stable'
        }
        
        # 查找时间表达
        for pattern, time_type in self.time_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                timeline['onset_time'] = time_type
                break
        
        # 分析症状进展
        if any(word in text for word in ['加重', '恶化', '越来越']):
            timeline['progression'] = 'worsening'
        elif any(word in text for word in ['好转', '减轻', '改善']):
            timeline['progression'] = 'improving'
        
        return timeline
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取分析统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'total_analyzed': self.stats['total_analyzed'],
            'total_processing_time': self.stats['total_processing_time'],
            'avg_processing_time': (
                self.stats['total_processing_time'] / self.stats['total_analyzed']
                if self.stats['total_analyzed'] > 0 else 0
            )
        }
