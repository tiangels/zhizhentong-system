"""
多轮对话记忆服务
实现对话历史摘要管理，支持多轮对话记忆功能
"""

import os
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
import threading

# 使用统一日志配置
import sys
from pathlib import Path

# 添加common模块到路径
current_file = Path(__file__)
common_dir = current_file.parent.parent.parent.parent / "common"
sys.path.insert(0, str(common_dir))

# 添加项目根目录到路径
import sys
from pathlib import Path
current_file = Path(__file__)
project_root = current_file.parent.parent.parent.parent  # 回到codes目录
sys.path.insert(0, str(project_root))

from common.log_config import setup_logging, get_logger
setup_logging("retrieval_service")
logger = get_logger(__name__)

# 导入文本摘要服务
from .text_summarization_service import TextSummarizationService


@dataclass
class ConversationTurn:
    """对话轮次数据结构"""
    turn_id: str
    user_question: str
    ai_response: str
    retrieved_context: str
    timestamp: str
    conversation_id: str
    turn_number: int


@dataclass
class ConversationMemory:
    """对话记忆数据结构"""
    conversation_id: str
    current_summary: str
    turn_count: int
    last_updated: str
    memory_length: int
    turns: List[ConversationTurn]


class ConversationMemoryService:
    """多轮对话记忆服务"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化对话记忆服务
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 记忆配置参数
        self.max_memory_length = self.config.get('max_memory_length', 400)  # 最大记忆长度
        self.summary_ratio = self.config.get('summary_ratio', 0.6)  # 摘要比例
        self.max_turns = self.config.get('max_turns', 10)  # 最大轮次
        self.memory_file = self.config.get('memory_file', 'conversation_memory.json')
        
        # 初始化文本摘要服务
        self.summarization_service = TextSummarizationService()
        
        # 对话记忆存储
        self.conversations: Dict[str, ConversationMemory] = {}
        self._lock = threading.Lock()
        
        # 加载现有记忆
        self._load_memories()
        
        logger.info("对话记忆服务初始化完成")
        logger.info(f"配置参数: max_memory_length={self.max_memory_length}, summary_ratio={self.summary_ratio}")
    
    def _load_memories(self):
        """加载现有对话记忆"""
        try:
            memory_path = Path(self.memory_file)
            if memory_path.exists():
                with open(memory_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 重建对话记忆对象
                for conv_id, conv_data in data.get('conversations', {}).items():
                    turns = [ConversationTurn(**turn) for turn in conv_data.get('turns', [])]
                    self.conversations[conv_id] = ConversationMemory(
                        conversation_id=conv_id,
                        current_summary=conv_data.get('current_summary', ''),
                        turn_count=conv_data.get('turn_count', 0),
                        last_updated=conv_data.get('last_updated', ''),
                        memory_length=conv_data.get('memory_length', 0),
                        turns=turns
                    )
                
                logger.info(f"成功加载 {len(self.conversations)} 个对话记忆")
            else:
                logger.info("未找到现有记忆文件，将创建新的记忆存储")
                
        except Exception as e:
            logger.error(f"加载对话记忆失败: {e}")
    
    def _save_memories(self):
        """保存对话记忆到文件"""
        try:
            with self._lock:
                # 准备保存数据
                save_data = {
                    'conversations': {},
                    'last_saved': datetime.now().isoformat()
                }
                
                for conv_id, memory in self.conversations.items():
                    save_data['conversations'][conv_id] = {
                        'conversation_id': memory.conversation_id,
                        'current_summary': memory.current_summary,
                        'turn_count': memory.turn_count,
                        'last_updated': memory.last_updated,
                        'memory_length': memory.memory_length,
                        'turns': [asdict(turn) for turn in memory.turns]
                    }
                
                # 保存到文件
                memory_path = Path(self.memory_file)
                memory_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(memory_path, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"对话记忆已保存到: {memory_path}")
                
        except Exception as e:
            logger.error(f"保存对话记忆失败: {e}")
    
    def create_conversation(self, conversation_id: str = None) -> str:
        """
        创建新的对话会话
        
        Args:
            conversation_id: 对话ID，如果为None则自动生成
            
        Returns:
            对话ID
        """
        if conversation_id is None:
            conversation_id = f"conv_{int(time.time())}_{id(self)}"
        
        if self._lock:
            with self._lock:
                self.conversations[conversation_id] = ConversationMemory(
                    conversation_id=conversation_id,
                    current_summary="",
                    turn_count=0,
                    last_updated=datetime.now().isoformat(),
                    memory_length=0,
                    turns=[]
                )
        else:
            self.conversations[conversation_id] = ConversationMemory(
                conversation_id=conversation_id,
                current_summary="",
                turn_count=0,
                last_updated=datetime.now().isoformat(),
                memory_length=0,
                turns=[]
            )
        
        logger.info(f"创建新对话会话: {conversation_id}")
        return conversation_id
    
    def add_turn(self, conversation_id: str, user_question: str, ai_response: str, 
                retrieved_context: str = "") -> ConversationTurn:
        """
        添加对话轮次
        
        Args:
            conversation_id: 对话ID
            user_question: 用户问题
            ai_response: AI回复
            retrieved_context: 检索到的上下文
            
        Returns:
            对话轮次对象
        """
        if self._lock:
            with self._lock:
                if conversation_id not in self.conversations:
                    self.create_conversation(conversation_id)
        else:
            if conversation_id not in self.conversations:
                self.create_conversation(conversation_id)
            
        memory = self.conversations[conversation_id]
        
        # 创建新的对话轮次
        turn = ConversationTurn(
            turn_id=f"{conversation_id}_turn_{memory.turn_count + 1}",
            user_question=user_question,
            ai_response=ai_response,
            retrieved_context=retrieved_context,
            timestamp=datetime.now().isoformat(),
            conversation_id=conversation_id,
            turn_number=memory.turn_count + 1
        )
        
        # 添加到记忆
        memory.turns.append(turn)
        memory.turn_count += 1
        memory.last_updated = datetime.now().isoformat()
        
        # 更新记忆摘要
        self._update_memory_summary(conversation_id)
        
        # 保存记忆
        self._save_memories()
        
        logger.info(f"添加对话轮次: {conversation_id}, 轮次: {turn.turn_number}")
        return turn
    
    def _update_memory_summary(self, conversation_id: str):
        """
        更新对话记忆摘要
        
        Args:
            conversation_id: 对话ID
        """
        try:
            memory = self.conversations[conversation_id]
            
            if memory.turn_count == 0:
                return
            
            # 获取当前轮次
            current_turn = memory.turns[-1]
            
            # 构建摘要输入
            if memory.turn_count == 1:
                # 第一轮：只有当前对话
                summary_input = f"问题：{current_turn.user_question}\n回答：{current_turn.ai_response}"
            else:
                # 后续轮次：历史摘要 + 当前对话
                previous_summary = memory.current_summary
                current_conversation = f"问题：{current_turn.user_question}\n回答：{current_turn.ai_response}"
                
                # 计算摘要长度
                total_length = len(previous_summary) + len(current_conversation)
                target_length = min(int(total_length * self.summary_ratio), self.max_memory_length)
                
                summary_input = f"历史摘要：{previous_summary}\n当前对话：{current_conversation}"
            
            # 生成新的摘要
            new_summary = self._generate_conversation_summary(summary_input, memory.current_summary)
            
            # 更新记忆
            memory.current_summary = new_summary
            memory.memory_length = len(new_summary)
            
            logger.info(f"更新对话摘要: {conversation_id}, 长度: {len(new_summary)}")
            
        except Exception as e:
            logger.error(f"更新记忆摘要失败: {e}")
    
    def _generate_conversation_summary(self, conversation_text: str, previous_summary: str = "") -> str:
        """
        生成对话摘要
        
        Args:
            conversation_text: 对话文本
            previous_summary: 之前的摘要
            
        Returns:
            生成的摘要
        """
        try:
            # 计算目标摘要长度
            total_length = len(conversation_text)
            target_length = min(int(total_length * self.summary_ratio), self.max_memory_length)
            
            # 如果文本太短，直接返回
            if total_length < 100:
                return conversation_text[:target_length]
            
            # 使用文本摘要服务生成摘要
            summary = self.summarization_service.summarize_medical_conversation(
                conversation_history=conversation_text,
                retrieval_content=previous_summary,
                max_length=target_length
            )
            
            # 如果摘要失败或太短，使用备用方法
            if len(summary) < 20:
                summary = self._create_fallback_summary(conversation_text, target_length)
            
            return summary
            
        except Exception as e:
            logger.error(f"生成对话摘要失败: {e}")
            return self._create_fallback_summary(conversation_text, self.max_memory_length)
    
    def _create_fallback_summary(self, text: str, max_length: int) -> str:
        """
        创建备用摘要（当AI摘要失败时）
        
        Args:
            text: 输入文本
            max_length: 最大长度
            
        Returns:
            备用摘要
        """
        try:
            # 简单的截断和关键词提取
            if len(text) <= max_length:
                return text
            
            # 按句子分割
            sentences = text.split('。')
            summary_sentences = []
            current_length = 0
            
            for sentence in sentences:
                if current_length + len(sentence) <= max_length:
                    summary_sentences.append(sentence)
                    current_length += len(sentence)
                else:
                    break
            
            summary = '。'.join(summary_sentences)
            if summary and not summary.endswith('。'):
                summary += '。'
            
            return summary[:max_length]
            
        except Exception as e:
            logger.error(f"创建备用摘要失败: {e}")
            return text[:max_length] + "..." if len(text) > max_length else text
    
    def get_conversation_memory(self, conversation_id: str) -> Optional[ConversationMemory]:
        """
        获取对话记忆
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            对话记忆对象
        """
        return self.conversations.get(conversation_id)
    
    def get_conversation_summary(self, conversation_id: str) -> str:
        """
        获取对话摘要
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            对话摘要
        """
        memory = self.conversations.get(conversation_id)
        return memory.current_summary if memory else ""
    
    def get_conversation_context(self, conversation_id: str, include_retrieval: bool = True) -> str:
        """
        获取对话上下文（用于知识检索）
        
        Args:
            conversation_id: 对话ID
            include_retrieval: 是否包含知识检索内容
            
        Returns:
            对话上下文
        """
        memory = self.conversations.get(conversation_id)
        if not memory:
            return ""
        
        context_parts = []
        
        # 添加历史摘要
        if memory.current_summary:
            context_parts.append(f"对话历史摘要：{memory.current_summary}")
        
        # 添加最近几轮对话（可选）
        if memory.turn_count > 0:
            recent_turns = memory.turns[-2:]  # 最近2轮
            for turn in recent_turns:
                if include_retrieval and turn.retrieved_context:
                    context_parts.append(f"检索知识：{turn.retrieved_context}")
                context_parts.append(f"问题：{turn.user_question}")
                context_parts.append(f"回答：{turn.ai_response}")
        
        return "\n".join(context_parts)
    
    def clear_conversation(self, conversation_id: str):
        """
        清空特定对话记忆
        
        Args:
            conversation_id: 对话ID
        """
        with self._lock:
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]
                self._save_memories()
                logger.info(f"清空对话记忆: {conversation_id}")
    
    def clear_all_conversations(self):
        """清空所有对话记忆"""
        with self._lock:
            self.conversations.clear()
            self._save_memories()
            logger.info("清空所有对话记忆")
    
    def clear_memory(self):
        """清空所有对话记忆（别名方法）"""
        self.clear_all_conversations()
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """
        获取对话统计信息
        
        Returns:
            统计信息字典
        """
        total_conversations = len(self.conversations)
        total_turns = sum(memory.turn_count for memory in self.conversations.values())
        avg_turns = total_turns / total_conversations if total_conversations > 0 else 0
        
        return {
            "total_conversations": total_conversations,
            "total_turns": total_turns,
            "average_turns_per_conversation": avg_turns,
            "max_memory_length": self.max_memory_length,
            "summary_ratio": self.summary_ratio,
            "last_updated": datetime.now().isoformat()
        }
    
    def export_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        导出对话数据
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            对话数据字典
        """
        memory = self.conversations.get(conversation_id)
        if not memory:
            return {}
        
        return {
            "conversation_id": memory.conversation_id,
            "current_summary": memory.current_summary,
            "turn_count": memory.turn_count,
            "last_updated": memory.last_updated,
            "memory_length": memory.memory_length,
            "turns": [asdict(turn) for turn in memory.turns]
        }


class ConversationMemoryServiceFactory:
    """对话记忆服务工厂类"""
    
    @staticmethod
    def create_memory_service(config: Dict[str, Any] = None) -> ConversationMemoryService:
        """
        创建对话记忆服务实例
        
        Args:
            config: 配置字典
            
        Returns:
            对话记忆服务实例
        """
        return ConversationMemoryService(config)


def create_conversation_memory_service(config: Dict[str, Any] = None) -> ConversationMemoryService:
    """
    创建对话记忆服务实例
    
    Args:
        config: 配置字典
        
    Returns:
        对话记忆服务实例
    """
    return ConversationMemoryServiceFactory.create_memory_service(config)


if __name__ == "__main__":
    # 测试对话记忆服务
    logging.basicConfig(level=logging.INFO)
    
    try:
        # 创建服务
        config = {
            'max_memory_length': 300,
            'summary_ratio': 0.6,
            'max_turns': 10
        }
        memory_service = create_conversation_memory_service(config)
        
        # 创建对话
        conv_id = memory_service.create_conversation()
        print(f"创建对话: {conv_id}")
        
        # 模拟多轮对话
        conversations = [
            ("我最近头痛，可能是什么原因？", "头痛可能由多种原因引起，建议您详细描述症状。"),
            ("头痛持续了3天，主要是太阳穴附近，有时候会恶心。", "根据您的描述，可能是偏头痛，建议避免强光和噪音刺激。"),
            ("那我应该怎么治疗呢？", "偏头痛的治疗包括药物治疗和生活方式调整，建议咨询专业医生。")
        ]
        
        for i, (question, response) in enumerate(conversations, 1):
            print(f"\n=== 第{i}轮对话 ===")
            print(f"问题: {question}")
            print(f"回答: {response}")
            
            # 添加对话轮次
            turn = memory_service.add_turn(
                conversation_id=conv_id,
                user_question=question,
                ai_response=response,
                retrieved_context=f"相关医学知识{i}"
            )
            
            # 获取当前摘要
            summary = memory_service.get_conversation_summary(conv_id)
            print(f"当前摘要: {summary}")
        
        # 获取完整上下文
        context = memory_service.get_conversation_context(conv_id)
        print(f"\n完整上下文:\n{context}")
        
        # 获取统计信息
        stats = memory_service.get_conversation_stats()
        print(f"\n统计信息: {stats}")
        
    except Exception as e:
        print(f"测试失败: {e}")
