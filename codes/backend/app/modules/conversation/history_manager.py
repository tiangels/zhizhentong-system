"""
对话历史管理器
管理对话历史记录和消息存储
"""

import time
from typing import Dict, Any, List, Optional
from collections import defaultdict


class ConversationHistoryManager:
    """对话历史管理器"""
    
    def __init__(self):
        """初始化历史管理器"""
        self.stats = defaultdict(int)
        self.conversation_histories = {}  # 内存中的历史记录存储
        
        # 历史记录配置
        self.max_history_size = 100  # 每个对话最大历史记录数
        self.max_conversations = 1000  # 最大对话数量
    
    def add_message(self, conversation_id: str, user_id: str, message: str, response: str, state: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        添加消息到历史记录
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            message: 用户消息
            response: 系统回复
            state: 对话状态
            metadata: 元数据
        """
        # 获取对话历史
        history = self.get_history(conversation_id)
        
        # 创建消息记录
        message_record = {
            'id': f"msg_{int(time.time())}",
            'timestamp': time.time(),
            'user_id': user_id,
            'user_message': message,
            'system_response': response,
            'state': state,
            'metadata': metadata or {}
        }
        
        # 添加到历史记录
        history.append(message_record)
        
        # 限制历史记录大小
        if len(history) > self.max_history_size:
            history.pop(0)  # 移除最旧的消息
        
        # 保存历史记录
        self.conversation_histories[conversation_id] = history
        
        self.stats['messages_added'] += 1
        
        # 清理过期的对话
        self._cleanup_old_conversations()
    
    def get_history(self, conversation_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取对话历史
        
        Args:
            conversation_id: 对话ID
            limit: 返回消息数量限制
            
        Returns:
            List[Dict[str, Any]]: 对话历史
        """
        history = self.conversation_histories.get(conversation_id, [])
        
        if limit:
            history = history[-limit:]  # 返回最新的消息
        
        return history.copy()
    
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """
        获取对话摘要
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            Dict[str, Any]: 对话摘要
        """
        history = self.get_history(conversation_id)
        
        if not history:
            return {
                'conversation_id': conversation_id,
                'message_count': 0,
                'start_time': None,
                'end_time': None,
                'duration': 0,
                'states': []
            }
        
        # 计算摘要信息
        message_count = len(history)
        start_time = history[0]['timestamp']
        end_time = history[-1]['timestamp']
        duration = end_time - start_time
        
        # 统计状态
        states = [msg['state'] for msg in history]
        unique_states = list(set(states))
        
        # 统计用户消息长度
        user_message_lengths = [len(msg['user_message']) for msg in history]
        avg_message_length = sum(user_message_lengths) / len(user_message_lengths) if user_message_lengths else 0
        
        return {
            'conversation_id': conversation_id,
            'message_count': message_count,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'states': unique_states,
            'avg_message_length': avg_message_length
        }
    
    def search_history(self, conversation_id: str, query: str) -> List[Dict[str, Any]]:
        """
        搜索对话历史
        
        Args:
            conversation_id: 对话ID
            query: 搜索查询
            
        Returns:
            List[Dict[str, Any]]: 匹配的消息
        """
        history = self.get_history(conversation_id)
        matching_messages = []
        
        query_lower = query.lower()
        
        for message in history:
            user_message = message['user_message'].lower()
            system_response = message['system_response'].lower()
            
            if query_lower in user_message or query_lower in system_response:
                matching_messages.append(message)
        
        return matching_messages
    
    def get_user_conversations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取用户的对话列表
        
        Args:
            user_id: 用户ID
            limit: 返回对话数量限制
            
        Returns:
            List[Dict[str, Any]]: 用户对话列表
        """
        user_conversations = []
        
        for conversation_id, history in self.conversation_histories.items():
            if history and history[0]['user_id'] == user_id:
                summary = self.get_conversation_summary(conversation_id)
                user_conversations.append(summary)
        
        # 按开始时间排序（最新的在前）
        user_conversations.sort(key=lambda x: x['start_time'], reverse=True)
        
        return user_conversations[:limit]
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        删除对话
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            bool: 是否删除成功
        """
        if conversation_id in self.conversation_histories:
            del self.conversation_histories[conversation_id]
            self.stats['conversations_deleted'] += 1
            return True
        
        return False
    
    def clear_user_history(self, user_id: str) -> int:
        """
        清除用户的所有对话历史
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 删除的对话数量
        """
        deleted_count = 0
        
        conversation_ids_to_delete = []
        
        for conversation_id, history in self.conversation_histories.items():
            if history and history[0]['user_id'] == user_id:
                conversation_ids_to_delete.append(conversation_id)
        
        for conversation_id in conversation_ids_to_delete:
            if self.delete_conversation(conversation_id):
                deleted_count += 1
        
        return deleted_count
    
    def _cleanup_old_conversations(self) -> None:
        """
        清理过期的对话
        """
        if len(self.conversation_histories) <= self.max_conversations:
            return
        
        # 按最后活动时间排序
        conversation_times = []
        for conversation_id, history in self.conversation_histories.items():
            if history:
                last_time = history[-1]['timestamp']
                conversation_times.append((conversation_id, last_time))
        
        # 按时间排序（最旧的在前）
        conversation_times.sort(key=lambda x: x[1])
        
        # 删除最旧的对话
        to_delete = len(conversation_times) - self.max_conversations
        for i in range(to_delete):
            conversation_id = conversation_times[i][0]
            self.delete_conversation(conversation_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取历史管理统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_messages = sum(len(history) for history in self.conversation_histories.values())
        
        return {
            'total_conversations': len(self.conversation_histories),
            'total_messages': total_messages,
            'messages_added': self.stats['messages_added'],
            'conversations_deleted': self.stats['conversations_deleted'],
            'max_history_size': self.max_history_size,
            'max_conversations': self.max_conversations
        }
