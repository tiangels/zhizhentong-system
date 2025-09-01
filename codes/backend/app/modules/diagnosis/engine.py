"""
智能诊断引擎
协调症状分析、诊断推理、风险评估等流程
"""

import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .symptom_analyzer import SymptomAnalyzer
from .risk_assessor import RiskAssessor
from .result_generator import DiagnosisResultGenerator


class DiagnosisInput(BaseModel):
    """诊断输入数据模型"""
    symptoms: str
    user_context: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    multimodal_data: Optional[Dict[str, Any]] = None


class DiagnosisOutput(BaseModel):
    """诊断输出数据模型"""
    diagnosis_id: str
    results: List[Dict[str, Any]]
    overall_confidence: float
    risk_assessment: Dict[str, str]
    recommendations: Dict[str, List[str]]
    processing_time: float


class DiagnosisEngine:
    """智能诊断引擎"""
    
    def __init__(self):
        """初始化诊断引擎"""
        self.symptom_analyzer = SymptomAnalyzer()
        self.risk_assessor = RiskAssessor()
        self.result_generator = DiagnosisResultGenerator()
    
    def diagnose(self, input_data: DiagnosisInput) -> DiagnosisOutput:
        """
        执行诊断
        
        Args:
            input_data: 诊断输入数据
            
        Returns:
            DiagnosisOutput: 诊断结果
        """
        start_time = time.time()
        
        # 症状分析
        symptom_analysis = self.symptom_analyzer.analyze_symptoms(input_data.symptoms)
        
        # 风险评估
        risk_assessment = self.risk_assessor.assess_risk(symptom_analysis)
        
        # 生成诊断结果
        diagnosis_results = self._generate_diagnosis_results(symptom_analysis, input_data)
        
        # 生成建议
        recommendations = self._generate_recommendations(diagnosis_results, risk_assessment)
        
        # 计算整体置信度
        overall_confidence = self._calculate_overall_confidence(diagnosis_results)
        
        processing_time = time.time() - start_time
        
        return DiagnosisOutput(
            diagnosis_id=f"diag_{int(time.time())}",
            results=diagnosis_results,
            overall_confidence=overall_confidence,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            processing_time=processing_time
        )
    
    def _generate_diagnosis_results(self, symptom_analysis: Dict[str, Any], input_data: DiagnosisInput) -> List[Dict[str, Any]]:
        """
        生成诊断结果
        
        Args:
            symptom_analysis: 症状分析结果
            input_data: 诊断输入数据
            
        Returns:
            List[Dict[str, Any]]: 诊断结果列表
        """
        # 模拟诊断结果
        mock_diagnoses = [
            {
                "disease": "上呼吸道感染",
                "confidence": 0.85,
                "severity": "moderate",
                "risk_level": "medium",
                "urgency": "normal",
                "symptoms": ["发热", "咳嗽", "鼻塞"],
                "differential_diagnosis": ["流感", "支气管炎"]
            },
            {
                "disease": "急性胃肠炎",
                "confidence": 0.72,
                "severity": "mild",
                "risk_level": "low",
                "urgency": "normal",
                "symptoms": ["腹痛", "腹泻", "恶心"],
                "differential_diagnosis": ["食物中毒", "肠易激综合征"]
            },
            {
                "disease": "偏头痛",
                "confidence": 0.68,
                "severity": "moderate",
                "risk_level": "low",
                "urgency": "normal",
                "symptoms": ["头痛", "恶心", "光敏感"],
                "differential_diagnosis": ["紧张性头痛", "丛集性头痛"]
            }
        ]
        
        # 根据症状分析结果选择相关诊断
        relevant_diagnoses = []
        analyzed_symptoms = symptom_analysis.get('symptoms', [])
        
        for diagnosis in mock_diagnoses:
            # 计算症状匹配度
            matching_symptoms = set(diagnosis['symptoms']) & set(analyzed_symptoms)
            if matching_symptoms:
                # 调整置信度基于匹配症状数量
                match_ratio = len(matching_symptoms) / len(diagnosis['symptoms'])
                diagnosis_copy = diagnosis.copy()  # 创建副本避免修改原始数据
                diagnosis_copy['confidence'] = min(0.95, diagnosis_copy['confidence'] * match_ratio)
                relevant_diagnoses.append(diagnosis_copy)
        
        # 如果没有匹配的诊断，返回通用诊断
        if not relevant_diagnoses:
            relevant_diagnoses = [mock_diagnoses[0]]
        
        return relevant_diagnoses[:3]  # 最多返回3个诊断
    
    def _generate_recommendations(self, diagnosis_results: List[Dict[str, Any]], risk_assessment: Dict[str, str]) -> Dict[str, List[str]]:
        """
        生成建议
        
        Args:
            diagnosis_results: 诊断结果
            risk_assessment: 风险评估
            
        Returns:
            Dict[str, List[str]]: 建议分类
        """
        recommendations = {
            "immediate_actions": [],
            "follow_up": [],
            "preventive_measures": []
        }
        
        # 根据风险等级生成建议
        risk_level = risk_assessment.get('disease_risk', 'low')
        
        if risk_level == 'high':
            recommendations["immediate_actions"].extend([
                "建议立即就医",
                "避免剧烈运动",
                "保持充足休息"
            ])
        elif risk_level == 'medium':
            recommendations["immediate_actions"].extend([
                "建议尽快就医",
                "注意观察症状变化",
                "避免过度劳累"
            ])
        else:
            recommendations["immediate_actions"].extend([
                "建议适当休息",
                "多喝水",
                "注意饮食"
            ])
        
        # 根据诊断结果生成随访建议
        for diagnosis in diagnosis_results:
            disease = diagnosis.get('disease', '')
            if '感染' in disease:
                recommendations["follow_up"].append("3-5天后复查")
            elif '炎' in disease:
                recommendations["follow_up"].append("1周后复查")
            else:
                recommendations["follow_up"].append("根据症状变化决定复查时间")
        
        # 预防措施
        recommendations["preventive_measures"].extend([
            "保持良好的个人卫生",
            "均衡饮食，增强免疫力",
            "适量运动，保持健康生活方式"
        ])
        
        return recommendations
    
    def _calculate_overall_confidence(self, diagnosis_results: List[Dict[str, Any]]) -> float:
        """
        计算整体置信度
        
        Args:
            diagnosis_results: 诊断结果
            
        Returns:
            float: 整体置信度
        """
        if not diagnosis_results:
            return 0.0
        
        # 计算加权平均置信度
        total_confidence = 0.0
        total_weight = 0.0
        
        for i, diagnosis in enumerate(diagnosis_results):
            weight = 1.0 / (i + 1)  # 第一个诊断权重最高
            confidence = diagnosis.get('confidence', 0.0)
            total_confidence += weight * confidence
            total_weight += weight
        
        return total_confidence / total_weight if total_weight > 0 else 0.0
    
    def get_diagnosis_stats(self) -> Dict[str, Any]:
        """
        获取诊断统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'symptom_analyzer': self.symptom_analyzer.get_stats(),
            'risk_assessor': self.risk_assessor.get_stats(),
            'result_generator': self.result_generator.get_stats()
        }
