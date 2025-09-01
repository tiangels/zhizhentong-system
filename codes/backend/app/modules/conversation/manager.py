"""
对话管理器主类
协调对话状态管理、上下文跟踪、历史记录等
"""

import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .state_manager import ConversationStateManager
from .context_tracker import ContextTracker
from .history_manager import ConversationHistoryManager


class ConversationInput(BaseModel):
    """对话输入数据模型"""
    conversation_id: Optional[str] = None
    user_id: str
    message: str
    message_type: str = "text"
    metadata: Optional[Dict[str, Any]] = None


class ConversationOutput(BaseModel):
    """对话输出数据模型"""
    conversation_id: str
    response: str
    state: str
    context: Dict[str, Any]
    processing_time: float


class ConversationManager:
    """对话管理器主类"""
    
    def __init__(self):
        """初始化对话管理器"""
        self.state_manager = ConversationStateManager()
        self.context_tracker = ContextTracker()
        self.history_manager = ConversationHistoryManager()
    
    def process_message(self, input_data: ConversationInput) -> ConversationOutput:
        """
        处理用户消息
        
        Args:
            input_data: 对话输入数据
            
        Returns:
            ConversationOutput: 对话输出结果
        """
        start_time = time.time()
        
        # 获取或创建对话ID
        conversation_id = input_data.conversation_id or self._generate_conversation_id()
        
        # 获取当前对话状态
        current_state = self.state_manager.get_state(conversation_id)
        
        # 更新上下文
        context = self.context_tracker.update_context(
            conversation_id=conversation_id,
            user_id=input_data.user_id,
            message=input_data.message,
            current_state=current_state
        )
        
        # 状态转换
        new_state = self.state_manager.transition_state(
            current_state=current_state,
            message=input_data.message,
            context=context
        )
        
        # 生成回复
        response = self._generate_response(input_data.message, context, new_state)
        
        # 更新历史记录
        self.history_manager.add_message(
            conversation_id=conversation_id,
            user_id=input_data.user_id,
            message=input_data.message,
            response=response,
            state=new_state,
            metadata=input_data.metadata
        )
        
        # 更新状态
        self.state_manager.update_state(conversation_id, new_state)
        
        processing_time = time.time() - start_time
        
        return ConversationOutput(
            conversation_id=conversation_id,
            response=response,
            state=new_state,
            context=context,
            processing_time=processing_time
        )
    
    def _generate_conversation_id(self) -> str:
        """
        生成对话ID
        
        Returns:
            str: 对话ID
        """
        return f"conv_{int(time.time())}"
    
    def _generate_response(self, message: str, context: Dict[str, Any], state: str) -> str:
        """
        生成回复
        
        Args:
            message: 用户消息
            context: 对话上下文
            state: 当前状态
            
        Returns:
            str: 生成的回复
        """
        # 模拟回复生成
        # 实际实现中会调用大语言模型
        
        # 根据状态生成不同回复
        if state == "greeting":
            return "您好！我是智诊通AI医生，很高兴为您服务。请描述您的症状或健康问题，我会尽力帮助您。"
        
        elif state == "symptom_collection":
            # 分析症状并生成回复
            symptoms = context.get('symptoms', [])
            if symptoms:
                return f"我了解到您有以下症状：{', '.join(symptoms)}。请继续详细描述您的症状，包括持续时间、严重程度等。"
            else:
                return "请详细描述您的症状，包括症状的性质、持续时间、严重程度等信息。"
        
        elif state == "diagnosis":
            # 生成诊断回复
            diagnosis = context.get('diagnosis', {})
            if diagnosis:
                disease = diagnosis.get('disease', '')
                confidence = diagnosis.get('confidence', 0.0)
                return f"根据您的症状描述，最可能的诊断是{disease}，诊断置信度为{confidence:.1%}。建议您及时就医以获得专业治疗。"
            else:
                return "我需要更多信息来进行准确的诊断。请提供更详细的症状描述。"
        
        elif state == "recommendation":
            # 生成建议回复
            recommendations = context.get('recommendations', [])
            if recommendations:
                return f"基于您的症状，我建议：{'; '.join(recommendations)}。如有疑问，请随时询问。"
            else:
                return "建议您及时就医，医生会根据您的具体情况提供专业的治疗建议。"
        
        else:
            # 默认回复
            return "我理解您的问题。请继续描述您的症状或健康问题，我会为您提供专业的建议。"
    
    def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取对话历史
        
        Args:
            conversation_id: 对话ID
            limit: 返回消息数量限制
            
        Returns:
            List[Dict[str, Any]]: 对话历史
        """
        return self.history_manager.get_history(conversation_id, limit)
    
    def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        获取对话上下文
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            Dict[str, Any]: 对话上下文
        """
        return self.context_tracker.get_context(conversation_id)
    
    def get_conversation_state(self, conversation_id: str) -> str:
        """
        获取对话状态
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            str: 对话状态
        """
        return self.state_manager.get_state(conversation_id)
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """
        获取对话统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'state_manager': self.state_manager.get_stats(),
            'context_tracker': self.context_tracker.get_stats(),
            'history_manager': self.history_manager.get_stats()
        }
