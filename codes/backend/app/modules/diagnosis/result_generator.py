"""
诊断结果生成器
生成格式化的诊断结果和建议
"""

import time
from typing import Dict, Any, List
from collections import defaultdict


class DiagnosisResultGenerator:
    """诊断结果生成器"""
    
    def __init__(self):
        """初始化诊断结果生成器"""
        self.stats = defaultdict(int)
        
        # 诊断结果模板
        self.diagnosis_templates = {
            '上呼吸道感染': {
                'description': '上呼吸道感染是一种常见的病毒感染，主要影响鼻子、喉咙和气管。',
                'common_symptoms': ['发热', '咳嗽', '鼻塞', '咽痛', '头痛'],
                'treatment_approach': '对症治疗，充分休息，多喝水',
                'recovery_time': '7-10天'
            },
            '急性胃肠炎': {
                'description': '急性胃肠炎是胃肠道黏膜的急性炎症，通常由病毒或细菌感染引起。',
                'common_symptoms': ['腹痛', '腹泻', '恶心', '呕吐', '发热'],
                'treatment_approach': '补充水分，清淡饮食，必要时使用止泻药',
                'recovery_time': '3-7天'
            },
            '偏头痛': {
                'description': '偏头痛是一种常见的原发性头痛，通常表现为单侧搏动性头痛。',
                'common_symptoms': ['头痛', '恶心', '呕吐', '光敏感', '声音敏感'],
                'treatment_approach': '避免触发因素，药物治疗，生活方式调整',
                'recovery_time': '4-72小时'
            }
        }
    
    def generate_result(self, diagnosis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成诊断结果
        
        Args:
            diagnosis_data: 诊断数据
            
        Returns:
            Dict[str, Any]: 格式化的诊断结果
        """
        start_time = time.time()
        self.stats['total_generated'] += 1
        
        # 格式化诊断结果
        formatted_results = self._format_diagnosis_results(diagnosis_data)
        
        # 生成建议
        recommendations = self._generate_recommendations(diagnosis_data)
        
        # 生成解释
        explanations = self._generate_explanations(diagnosis_data)
        
        # 生成随访计划
        follow_up_plan = self._generate_follow_up_plan(diagnosis_data)
        
        processing_time = time.time() - start_time
        self.stats['total_processing_time'] += processing_time
        
        return {
            'formatted_results': formatted_results,
            'recommendations': recommendations,
            'explanations': explanations,
            'follow_up_plan': follow_up_plan,
            'processing_time': processing_time
        }
    
    def _format_diagnosis_results(self, diagnosis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        格式化诊断结果
        
        Args:
            diagnosis_data: 诊断数据
            
        Returns:
            List[Dict[str, Any]]: 格式化的诊断结果
        """
        formatted_results = []
        results = diagnosis_data.get('results', [])
        
        for result in results:
            disease = result.get('disease', '')
            template = self.diagnosis_templates.get(disease, {})
            
            formatted_result = {
                'disease': disease,
                'confidence': result.get('confidence', 0.0),
                'severity': result.get('severity', 'moderate'),
                'risk_level': result.get('risk_level', 'medium'),
                'urgency': result.get('urgency', 'normal'),
                'description': template.get('description', ''),
                'common_symptoms': template.get('common_symptoms', []),
                'treatment_approach': template.get('treatment_approach', ''),
                'recovery_time': template.get('recovery_time', ''),
                'differential_diagnosis': result.get('differential_diagnosis', [])
            }
            
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def _generate_recommendations(self, diagnosis_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        生成建议
        
        Args:
            diagnosis_data: 诊断数据
            
        Returns:
            Dict[str, List[str]]: 建议分类
        """
        recommendations = {
            'immediate_actions': [],
            'lifestyle_changes': [],
            'medications': [],
            'preventive_measures': []
        }
        
        risk_assessment = diagnosis_data.get('risk_assessment', {})
        risk_level = risk_assessment.get('disease_risk', 'low')
        urgency_level = risk_assessment.get('urgency_level', 'normal')
        
        # 根据风险等级生成建议
        if risk_level == 'high' or urgency_level == 'emergency':
            recommendations['immediate_actions'].extend([
                '立即就医',
                '避免剧烈运动',
                '保持安静休息',
                '密切观察症状变化'
            ])
        elif risk_level == 'medium' or urgency_level == 'urgent':
            recommendations['immediate_actions'].extend([
                '尽快就医',
                '注意观察症状',
                '避免过度劳累',
                '保持充足休息'
            ])
        else:
            recommendations['immediate_actions'].extend([
                '适当休息',
                '多喝水',
                '注意饮食',
                '观察症状变化'
            ])
        
        # 生活方式建议
        recommendations['lifestyle_changes'].extend([
            '保持规律作息',
            '均衡饮食',
            '适量运动',
            '避免吸烟饮酒'
        ])
        
        # 药物建议（需要医生指导）
        recommendations['medications'].extend([
            '请在医生指导下用药',
            '不要自行购买处方药',
            '注意药物相互作用'
        ])
        
        # 预防措施
        recommendations['preventive_measures'].extend([
            '保持良好的个人卫生',
            '增强免疫力',
            '定期体检',
            '及时接种疫苗'
        ])
        
        return recommendations
    
    def _generate_explanations(self, diagnosis_data: Dict[str, Any]) -> Dict[str, str]:
        """
        生成解释
        
        Args:
            diagnosis_data: 诊断数据
            
        Returns:
            Dict[str, str]: 解释内容
        """
        explanations = {}
        
        # 诊断解释
        results = diagnosis_data.get('results', [])
        if results:
            primary_diagnosis = results[0]
            disease = primary_diagnosis.get('disease', '')
            confidence = primary_diagnosis.get('confidence', 0.0)
            
            explanations['diagnosis_explanation'] = (
                f"根据您的症状描述，最可能的诊断是{disease}，"
                f"诊断置信度为{confidence:.1%}。"
            )
        
        # 风险解释
        risk_assessment = diagnosis_data.get('risk_assessment', {})
        disease_risk = risk_assessment.get('disease_risk', 'low')
        urgency_level = risk_assessment.get('urgency_level', 'normal')
        
        explanations['risk_explanation'] = (
            f"当前疾病风险等级为{disease_risk}，"
            f"紧急程度为{urgency_level}。"
        )
        
        # 建议解释
        if urgency_level == 'emergency':
            explanations['recommendation_explanation'] = (
                "由于症状较为严重，建议立即就医以获得专业治疗。"
            )
        elif urgency_level == 'urgent':
            explanations['recommendation_explanation'] = (
                "建议尽快就医，同时注意观察症状变化。"
            )
        else:
            explanations['recommendation_explanation'] = (
                "建议适当休息，观察症状变化，必要时就医。"
            )
        
        return explanations
    
    def _generate_follow_up_plan(self, diagnosis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成随访计划
        
        Args:
            diagnosis_data: 诊断数据
            
        Returns:
            Dict[str, Any]: 随访计划
        """
        follow_up_plan = {
            'schedule': [],
            'monitoring': [],
            'red_flags': []
        }
        
        risk_assessment = diagnosis_data.get('risk_assessment', {})
        urgency_level = risk_assessment.get('urgency_level', 'normal')
        
        # 根据紧急程度制定随访计划
        if urgency_level == 'emergency':
            follow_up_plan['schedule'].extend([
                '立即就医',
                '24小时内复查',
                '根据医生建议安排后续随访'
            ])
        elif urgency_level == 'urgent':
            follow_up_plan['schedule'].extend([
                '尽快就医',
                '3-5天内复查',
                '症状加重时立即就医'
            ])
        else:
            follow_up_plan['schedule'].extend([
                '1周后复查',
                '症状持续或加重时就医',
                '根据恢复情况调整随访时间'
            ])
        
        # 监测项目
        follow_up_plan['monitoring'].extend([
            '症状变化',
            '体温（如有发热）',
            '精神状态',
            '饮食和睡眠'
        ])
        
        # 危险信号
        follow_up_plan['red_flags'].extend([
            '症状突然加重',
            '出现新的严重症状',
            '意识改变',
            '呼吸困难',
            '持续高热不退'
        ])
        
        return follow_up_plan
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取生成统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'total_generated': self.stats['total_generated'],
            'total_processing_time': self.stats['total_processing_time'],
            'avg_processing_time': (
                self.stats['total_processing_time'] / self.stats['total_generated']
                if self.stats['total_generated'] > 0 else 0
            )
        }
