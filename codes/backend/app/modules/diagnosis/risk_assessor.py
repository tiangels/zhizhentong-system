"""
风险评估器
评估症状的严重程度和风险等级
"""

from typing import Dict, Any, List
import re


class RiskAssessor:
    """风险评估器"""
    
    def __init__(self):
        """初始化风险评估器"""
        # 高风险症状关键词
        self.high_risk_symptoms = [
            '胸痛', '呼吸困难', '意识丧失', '抽搐', '大出血', '休克',
            '急性腹痛', '剧烈头痛', '瘫痪', '失语', '视力丧失',
            '心跳骤停', '血压异常', '体温过高', '体温过低'
        ]
        
        # 中风险症状关键词
        self.medium_risk_symptoms = [
            '发热', '咳嗽', '腹痛', '恶心', '呕吐', '腹泻',
            '头痛', '头晕', '乏力', '食欲不振', '失眠',
            '关节痛', '肌肉痛', '皮疹', '瘙痒'
        ]
        
        # 紧急症状模式
        self.emergency_patterns = [
            r'突然.*疼痛',
            r'剧烈.*疼痛',
            r'无法.*呼吸',
            r'意识.*不清',
            r'失去.*知觉',
            r'大量.*出血',
            r'心跳.*停止',
            r'血压.*异常'
        ]
    
    def assess_risk(self, symptom_analysis: Dict[str, Any]) -> Dict[str, str]:
        """
        评估症状风险
        
        Args:
            symptom_analysis: 症状分析结果
            
        Returns:
            Dict[str, str]: 风险评估结果
        """
        symptoms = symptom_analysis.get('symptoms', [])
        symptom_text = symptom_analysis.get('original_text', '')
        
        # 分析症状严重程度
        severity = self._analyze_severity(symptoms, symptom_text)
        
        # 分析疾病风险
        disease_risk = self._analyze_disease_risk(symptoms, symptom_text)
        
        # 分析紧急程度
        urgency = self._analyze_urgency(symptoms, symptom_text)
        
        # 分析并发症风险
        complication_risk = self._analyze_complication_risk(symptoms, symptom_text)
        
        return {
            'severity': severity,
            'disease_risk': disease_risk,
            'urgency': urgency,
            'complication_risk': complication_risk,
            'overall_risk': self._calculate_overall_risk(severity, disease_risk, urgency, complication_risk)
        }
    
    def _analyze_severity(self, symptoms: List[str], symptom_text: str) -> str:
        """分析症状严重程度"""
        high_risk_count = sum(1 for symptom in symptoms if any(hr in symptom for hr in self.high_risk_symptoms))
        medium_risk_count = sum(1 for symptom in symptoms if any(mr in symptom for mr in self.medium_risk_symptoms))
        
        if high_risk_count > 0:
            return 'high'
        elif medium_risk_count > 2:
            return 'medium'
        else:
            return 'low'
    
    def _analyze_disease_risk(self, symptoms: List[str], symptom_text: str) -> str:
        """分析疾病风险"""
        # 基于症状数量和类型评估疾病风险
        if len(symptoms) > 5:
            return 'high'
        elif len(symptoms) > 2:
            return 'medium'
        else:
            return 'low'
    
    def _analyze_urgency(self, symptoms: List[str], symptom_text: str) -> str:
        """分析紧急程度"""
        # 检查紧急症状模式
        for pattern in self.emergency_patterns:
            if re.search(pattern, symptom_text):
                return 'urgent'
        
        # 检查高风险症状
        for symptom in symptoms:
            if any(hr in symptom for hr in self.high_risk_symptoms):
                return 'urgent'
        
        return 'normal'
    
    def _analyze_complication_risk(self, symptoms: List[str], symptom_text: str) -> str:
        """分析并发症风险"""
        # 基于症状组合评估并发症风险
        complication_indicators = [
            '发热', '咳嗽', '胸痛',  # 可能肺炎
            '腹痛', '恶心', '呕吐',  # 可能急腹症
            '头痛', '头晕', '意识',  # 可能神经系统问题
            '心悸', '胸痛', '呼吸困难'  # 可能心脏问题
        ]
        
        indicator_count = sum(1 for indicator in complication_indicators 
                             if any(indicator in symptom for symptom in symptoms))
        
        if indicator_count >= 3:
            return 'high'
        elif indicator_count >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_overall_risk(self, severity: str, disease_risk: str, urgency: str, complication_risk: str) -> str:
        """计算整体风险等级"""
        risk_scores = {
            'high': 3,
            'medium': 2,
            'low': 1,
            'urgent': 4
        }
        
        total_score = (
            risk_scores.get(severity, 1) +
            risk_scores.get(disease_risk, 1) +
            risk_scores.get(complication_risk, 1)
        )
        
        # 紧急情况直接判定为高风险
        if urgency == 'urgent':
            return 'critical'
        
        if total_score >= 8:
            return 'high'
        elif total_score >= 5:
            return 'medium'
        else:
            return 'low'
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取风险评估器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'high_risk_symptoms_count': len(self.high_risk_symptoms),
            'medium_risk_symptoms_count': len(self.medium_risk_symptoms),
            'emergency_patterns_count': len(self.emergency_patterns),
            'risk_levels': ['low', 'medium', 'high', 'critical'],
            'urgency_levels': ['normal', 'urgent']
        }
