"""
上下文跟踪器
跟踪和维护对话上下文信息
"""

import time
from typing import Dict, Any, List, Optional
from collections import defaultdict


class ContextTracker:
    """上下文跟踪器"""
    
    def __init__(self):
        """初始化上下文跟踪器"""
        self.stats = defaultdict(int)
        self.conversation_contexts = {}  # 内存中的上下文存储
        
        # 症状关键词
        self.symptom_keywords = [
            '发热', '头痛', '腹痛', '咳嗽', '鼻塞', '咽痛', '胸痛', 
            '恶心', '呕吐', '腹泻', '眩晕', '失眠', '焦虑', '抑郁'
        ]
        
        # 时间关键词
        self.time_keywords = [
            '天', '周', '月', '年', '小时', '分钟', '昨天', '今天', '刚才'
        ]
        
        # 严重程度关键词
        self.severity_keywords = {
            '轻微': 1,
            '轻度': 1,
            '中度': 2,
            '严重': 3,
            '剧烈': 3
        }
    
    def update_context(self, conversation_id: str, user_id: str, message: str, current_state: str) -> Dict[str, Any]:
        """
        更新上下文
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            message: 用户消息
            current_state: 当前状态
            
        Returns:
            Dict[str, Any]: 更新后的上下文
        """
        # 获取当前上下文
        context = self.get_context(conversation_id)
        
        # 提取信息
        extracted_info = self._extract_information(message)
        
        # 更新上下文
        updated_context = self._merge_context(context, extracted_info, current_state)
        
        # 保存上下文
        self.conversation_contexts[conversation_id] = updated_context
        
        self.stats['context_updates'] += 1
        
        return updated_context
    
    def get_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        获取上下文
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            Dict[str, Any]: 对话上下文
        """
        return self.conversation_contexts.get(conversation_id, {
            'user_id': None,
            'symptoms': [],
            'symptom_details': {},
            'time_info': {},
            'severity': 'moderate',
            'diagnosis': {},
            'recommendations': [],
            'conversation_history': [],
            'last_update': None
        })
    
    def _extract_information(self, message: str) -> Dict[str, Any]:
        """
        提取信息
        
        Args:
            message: 用户消息
            
        Returns:
            Dict[str, Any]: 提取的信息
        """
        extracted_info = {
            'symptoms': [],
            'symptom_details': {},
            'time_info': {},
            'severity': 'moderate'
        }
        
        # 提取症状
        for symptom in self.symptom_keywords:
            if symptom in message:
                extracted_info['symptoms'].append(symptom)
                
                # 提取症状详情
                symptom_detail = self._extract_symptom_detail(message, symptom)
                if symptom_detail:
                    extracted_info['symptom_details'][symptom] = symptom_detail
        
        # 提取时间信息
        time_info = self._extract_time_info(message)
        if time_info:
            extracted_info['time_info'] = time_info
        
        # 提取严重程度
        severity = self._extract_severity(message)
        if severity:
            extracted_info['severity'] = severity
        
        return extracted_info
    
    def _extract_symptom_detail(self, message: str, symptom: str) -> Dict[str, Any]:
        """
        提取症状详情
        
        Args:
            message: 用户消息
            symptom: 症状名称
            
        Returns:
            Dict[str, Any]: 症状详情
        """
        detail = {}
        
        # 查找症状在消息中的位置
        symptom_pos = message.find(symptom)
        if symptom_pos == -1:
            return detail
        
        # 提取症状前后的描述
        start_pos = max(0, symptom_pos - 20)
        end_pos = min(len(message), symptom_pos + len(symptom) + 20)
        context_text = message[start_pos:end_pos]
        
        # 提取严重程度
        for severity_word, level in self.severity_keywords.items():
            if severity_word in context_text:
                detail['severity'] = severity_word
                detail['severity_level'] = level
                break
        
        # 提取持续时间
        for time_word in self.time_keywords:
            if time_word in context_text:
                detail['duration'] = time_word
                break
        
        return detail
    
    def _extract_time_info(self, message: str) -> Dict[str, Any]:
        """
        提取时间信息
        
        Args:
            message: 用户消息
            
        Returns:
            Dict[str, Any]: 时间信息
        """
        time_info = {}
        
        # 提取时间表达
        for time_word in self.time_keywords:
            if time_word in message:
                time_info['time_expression'] = time_word
                break
        
        return time_info
    
    def _extract_severity(self, message: str) -> Optional[str]:
        """
        提取严重程度
        
        Args:
            message: 用户消息
            
        Returns:
            Optional[str]: 严重程度
        """
        for severity_word in self.severity_keywords:
            if severity_word in message:
                return severity_word
        
        return None
    
    def _merge_context(self, current_context: Dict[str, Any], new_info: Dict[str, Any], state: str) -> Dict[str, Any]:
        """
        合并上下文
        
        Args:
            current_context: 当前上下文
            new_info: 新信息
            state: 当前状态
            
        Returns:
            Dict[str, Any]: 合并后的上下文
        """
        merged_context = current_context.copy()
        
        # 合并症状
        if new_info['symptoms']:
            merged_context['symptoms'].extend(new_info['symptoms'])
            merged_context['symptoms'] = list(set(merged_context['symptoms']))  # 去重
        
        # 合并症状详情
        merged_context['symptom_details'].update(new_info['symptom_details'])
        
        # 合并时间信息
        if new_info['time_info']:
            merged_context['time_info'].update(new_info['time_info'])
        
        # 更新严重程度
        if new_info['severity'] != 'moderate':
            merged_context['severity'] = new_info['severity']
        
        # 根据状态更新上下文
        if state == 'diagnosis':
            # 在诊断状态下，可以添加诊断结果
            if 'diagnosis' not in merged_context:
                merged_context['diagnosis'] = {}
        
        elif state == 'recommendation':
            # 在建议状态下，可以添加建议
            if 'recommendations' not in merged_context:
                merged_context['recommendations'] = []
        
        # 更新时间戳
        merged_context['last_update'] = time.time()
        
        return merged_context
    
    def clear_context(self, conversation_id: str) -> None:
        """
        清除上下文
        
        Args:
            conversation_id: 对话ID
        """
        if conversation_id in self.conversation_contexts:
            del self.conversation_contexts[conversation_id]
            self.stats['context_clears'] += 1
    
    def get_context_summary(self, conversation_id: str) -> Dict[str, Any]:
        """
        获取上下文摘要
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            Dict[str, Any]: 上下文摘要
        """
        context = self.get_context(conversation_id)
        
        summary = {
            'total_symptoms': len(context.get('symptoms', [])),
            'symptoms': context.get('symptoms', []),
            'severity': context.get('severity', 'moderate'),
            'has_diagnosis': bool(context.get('diagnosis')),
            'has_recommendations': bool(context.get('recommendations')),
            'last_update': context.get('last_update')
        }
        
        return summary
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取上下文跟踪统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'total_conversations': len(self.conversation_contexts),
            'context_updates': self.stats['context_updates'],
            'context_clears': self.stats['context_clears']
        }
