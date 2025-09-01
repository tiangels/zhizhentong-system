"""
对话状态管理器
管理对话状态转换和状态持久化
"""

import time
from typing import Dict, Any, Optional
from collections import defaultdict


class ConversationStateManager:
    """对话状态管理器"""
    
    def __init__(self):
        """初始化状态管理器"""
        self.stats = defaultdict(int)
        self.conversation_states = {}  # 内存中的状态存储
        
        # 状态定义
        self.states = {
            'greeting': '问候状态',
            'symptom_collection': '症状收集状态',
            'diagnosis': '诊断状态',
            'recommendation': '建议状态',
            'follow_up': '随访状态',
            'end': '结束状态'
        }
        
        # 状态转换规则
        self.transition_rules = {
            'greeting': {
                'triggers': ['symptom', 'problem', 'help'],
                'next_state': 'symptom_collection'
            },
            'symptom_collection': {
                'triggers': ['diagnosis', 'what', 'disease'],
                'next_state': 'diagnosis'
            },
            'diagnosis': {
                'triggers': ['treatment', 'medicine', 'cure'],
                'next_state': 'recommendation'
            },
            'recommendation': {
                'triggers': ['follow', 'monitor', 'check'],
                'next_state': 'follow_up'
            },
            'follow_up': {
                'triggers': ['end', 'finish', 'goodbye'],
                'next_state': 'end'
            }
        }
    
    def get_state(self, conversation_id: str) -> str:
        """
        获取对话状态
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            str: 当前状态
        """
        return self.conversation_states.get(conversation_id, 'greeting')
    
    def set_state(self, conversation_id: str, state: str) -> None:
        """
        设置对话状态
        
        Args:
            conversation_id: 对话ID
            state: 新状态
        """
        if state in self.states:
            self.conversation_states[conversation_id] = state
            self.stats['state_changes'] += 1
    
    def transition_state(self, current_state: str, message: str, context: Dict[str, Any]) -> str:
        """
        状态转换
        
        Args:
            current_state: 当前状态
            message: 用户消息
            context: 对话上下文
            
        Returns:
            str: 新状态
        """
        # 检查是否有转换规则
        if current_state in self.transition_rules:
            rule = self.transition_rules[current_state]
            triggers = rule.get('triggers', [])
            
            # 检查消息中是否包含触发词
            message_lower = message.lower()
            for trigger in triggers:
                if trigger in message_lower:
                    next_state = rule['next_state']
                    self.stats['state_transitions'] += 1
                    return next_state
        
        # 如果没有触发转换，保持当前状态
        return current_state
    
    def update_state(self, conversation_id: str, new_state: str) -> None:
        """
        更新状态
        
        Args:
            conversation_id: 对话ID
            new_state: 新状态
        """
        self.set_state(conversation_id, new_state)
    
    def reset_state(self, conversation_id: str) -> None:
        """
        重置状态
        
        Args:
            conversation_id: 对话ID
        """
        self.conversation_states[conversation_id] = 'greeting'
        self.stats['state_resets'] += 1
    
    def get_state_info(self, state: str) -> Dict[str, Any]:
        """
        获取状态信息
        
        Args:
            state: 状态名称
            
        Returns:
            Dict[str, Any]: 状态信息
        """
        if state in self.states:
            return {
                'name': state,
                'description': self.states[state],
                'transitions': self.transition_rules.get(state, {})
            }
        return {}
    
    def get_all_states(self) -> Dict[str, str]:
        """
        获取所有状态
        
        Returns:
            Dict[str, str]: 状态映射
        """
        return self.states.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取状态管理统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'total_conversations': len(self.conversation_states),
            'state_changes': self.stats['state_changes'],
            'state_transitions': self.stats['state_transitions'],
            'state_resets': self.stats['state_resets'],
            'total_states': len(self.states)
        }
