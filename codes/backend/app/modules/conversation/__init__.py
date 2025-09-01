"""
对话管理模块
管理用户对话状态、上下文和历史记录
"""

from .manager import ConversationManager, ConversationInput, ConversationOutput
from .state_manager import ConversationStateManager
from .context_tracker import ContextTracker
from .history_manager import ConversationHistoryManager

__all__ = [
    "ConversationManager",
    "ConversationInput",
    "ConversationOutput",
    "ConversationStateManager",
    "ContextTracker",
    "ConversationHistoryManager"
]
