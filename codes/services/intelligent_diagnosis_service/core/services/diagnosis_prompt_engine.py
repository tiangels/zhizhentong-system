"""
智能诊断提示词引擎模块
专门为智能诊断服务设计的提示词构建引擎
"""

from typing import List, Dict, Any, Optional


class DiagnosisPromptEngine:
    """智能诊断提示词引擎类"""
    
    def __init__(self, mode: str = "optimized"):
        """
        初始化智能诊断提示词引擎
        
        Args:
            mode: 提示词模式 ("standard", "optimized", "ultra_compact")
        """
        self.mode = mode
        self.mode_map = {
            "standard": self._build_standard_prompt,
            "optimized": self._build_optimized_prompt,
            "ultra_compact": self._build_ultra_compact_prompt
        }
    
    def build_diagnosis_prompt(self, question: str, context: str, response_type: str = "diagnosis") -> str:
        """
        构建诊断提示词
        
        Args:
            question: 用户问题
            context: 检索到的上下文
            response_type: 响应类型 (diagnosis, advice, explanation)
            
        Returns:
            构建的提示词
        """
        return self.mode_map[self.mode]("diagnosis", {
            "question": question,
            "context": context,
            "response_type": response_type
        })
    
    def build_summary_prompt(self, conversation_history: str, retrieval_content: str = "") -> str:
        """
        构建摘要提示词
        
        Args:
            conversation_history: 对话历史
            retrieval_content: 知识检索内容
            
        Returns:
            构建的提示词
        """
        return self.mode_map[self.mode]("summary", {
            "conversation_history": conversation_history,
            "retrieval_content": retrieval_content
        })
    
    def build_fallback_prompt(self, query: str, response_type: str = "diagnosis") -> str:
        """
        构建回退提示词
        
        Args:
            query: 用户查询
            response_type: 响应类型
            
        Returns:
            构建的提示词
        """
        return self.mode_map[self.mode]("fallback", {
            "query": query,
            "response_type": response_type
        })
    
    def _build_standard_prompt(self, prompt_type: str, data: Dict[str, Any]) -> str:
        """构建标准版提示词"""
        if prompt_type == "diagnosis":
            return self._build_standard_diagnosis_prompt(data)
        elif prompt_type == "summary":
            return self._build_standard_summary_prompt(data)
        elif prompt_type == "fallback":
            return self._build_standard_fallback_prompt(data)
        else:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    def _build_optimized_prompt(self, prompt_type: str, data: Dict[str, Any]) -> str:
        """构建优化版提示词"""
        if prompt_type == "diagnosis":
            return self._build_optimized_diagnosis_prompt(data)
        elif prompt_type == "summary":
            return self._build_optimized_summary_prompt(data)
        elif prompt_type == "fallback":
            return self._build_optimized_fallback_prompt(data)
        else:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    def _build_ultra_compact_prompt(self, prompt_type: str, data: Dict[str, Any]) -> str:
        """构建超精简版提示词"""
        if prompt_type == "diagnosis":
            return self._build_ultra_compact_diagnosis_prompt(data)
        elif prompt_type == "summary":
            return self._build_ultra_compact_summary_prompt(data)
        elif prompt_type == "fallback":
            return self._build_ultra_compact_fallback_prompt(data)
        else:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    # ==================== 标准版提示词构建方法 ====================
    
    def _build_standard_diagnosis_prompt(self, data: Dict[str, Any]) -> str:
        """构建标准版诊断提示词"""
        question = data["question"]
        context = data["context"]
        response_type = data["response_type"]
        
        if response_type == "diagnosis":
            prompt = f"""作为一位专业的医疗AI助手，请基于以下信息提供诊断建议：

患者问题：{question}

相关医学知识：
{context}

请按照以下格式提供诊断建议：

【症状分析】
- 分析患者描述的症状特点
- 识别可能的疾病模式
- 考虑症状的严重程度和紧急程度

【可能诊断】
- 列出最可能的诊断（使用"考虑...可能"表述）
- 按可能性从高到低排序
- 避免给出绝对化的诊断结论

【诊断依据】
- 基于症状和医学知识的分析依据
- 说明为什么考虑这些诊断
- 指出需要进一步确认的要点

【建议检查】
- 推荐相关的医学检查项目
- 说明检查的目的和意义
- 建议检查的优先级和时机

【注意事项】
- 提醒患者需要关注的重要症状
- 建议何时需要紧急就医
- 强调此建议仅供参考，需要专业医生面诊确认

【免责声明】
- 强调此回答仅供参考，不能替代专业医生的诊断
- 提醒患者及时咨询专业医生获取准确信息
- 如有紧急情况请立即就医

要求：
- 使用概率性表述，避免绝对化诊断
- 语言专业但易懂
- 保持医疗安全性和谨慎性
- 基于提供的医学知识进行分析"""
        elif response_type == "advice":
            prompt = f"""作为一位专业的医疗AI助手，请根据以下信息提供健康建议：

用户问题：{question}
相关医学知识：{context}

请提供：
1. 健康建议
2. 预防措施
3. 生活方式建议
4. 何时需要就医

注意：这仅供参考，不能替代专业医生的建议。"""
        elif response_type == "explanation":
            prompt = f"""作为一位专业的医疗AI助手，请解释以下医学概念：

用户问题：{question}
相关医学知识：{context}

请提供：
1. 详细解释
2. 相关机制
3. 临床表现
4. 治疗原则

注意：这仅供参考，不能替代专业医生的解释。"""
        else:
            prompt = f"""医疗AI助手，基于医学知识回答问题。

问题：{question}
医学知识：{context}

回答格式：
1. 问题回应
2. 医学分析
3. 就医建议
4. 免责声明

要求：概率性表述，不替代医生诊断。"""
        
        return prompt
    
    def _build_standard_summary_prompt(self, data: Dict[str, Any]) -> str:
        """构建标准版摘要提示词"""
        conversation_history = data["conversation_history"]
        retrieval_content = data.get("retrieval_content", "")
        
        prompt = f"""生成医疗摘要：

对话历史：
{conversation_history}

相关文献：
{retrieval_content if retrieval_content else "无"}

要求：
- 200-300字，突出关键信息
- 包含患者信息、症状描述、医学分析、诊断依据
- 使用标准医学术语
- 避免绝对化表述

摘要："""
        
        return prompt
    
    def _build_standard_fallback_prompt(self, data: Dict[str, Any]) -> str:
        """构建标准版回退提示词"""
        query = data["query"]
        response_type = data["response_type"]
        
        prompt = f"""你是一位专业的医疗AI助手。用户询问了以下问题，但我在医学知识库中没有找到足够相关的信息来提供准确的医疗建议。

用户问题：{query}

请按照以下格式回答：

【问题理解】
- 简要理解用户的问题和关注点

【一般性建议】
- 提供一般性的健康建议和注意事项
- 建议用户关注的相关症状或体征
- 给出基本的生活调理建议

【就医建议】
- 强烈建议用户咨询专业医生
- 建议合适的就诊科室
- 提醒及时就医的重要性

【重要提醒】
- 强调此回答仅供参考，不能替代专业诊断
- 提醒用户及时咨询专业医生获取准确信息
- 如有紧急情况请立即就医

要求：
- 语言温和、专业
- 避免给出具体的诊断或治疗建议
- 重点强调咨询专业医生的重要性
- 保持回答的谨慎性和安全性"""
        
        return prompt
    
    # ==================== 优化版提示词构建方法 ====================
    
    def _build_optimized_diagnosis_prompt(self, data: Dict[str, Any]) -> str:
        """构建优化版诊断提示词"""
        question = data["question"]
        context = data["context"]
        response_type = data["response_type"]
        
        if response_type == "diagnosis":
            if context and context.strip():
                prompt = f"""基于以下医学知识提供诊断建议：

医学知识：
{context}

患者症状：{question}

请分析可能的原因并提供建议："""
            else:
                prompt = f"""患者症状：{question}

请分析可能的原因并提供建议："""
        elif response_type == "advice":
            prompt = f"""医疗AI助手，提供健康建议：

问题：{question}
知识：{context}

请提供：
1. 健康建议
2. 预防措施
3. 生活方式建议
4. 何时就医

提醒：仅供参考，请咨询专业医生。"""
        elif response_type == "explanation":
            prompt = f"""医疗AI助手，解释医学概念：

问题：{question}
知识：{context}

请提供：
1. 概念解释
2. 相关症状
3. 治疗方法
4. 注意事项

提醒：仅供参考，请咨询专业医生。"""
        else:
            prompt = f"""医疗AI助手，回答问题：

问题：{question}
知识：{context}

请提供：
1. 问题回应
2. 医学分析
3. 就医建议
4. 免责声明

提醒：仅供参考，请咨询专业医生。"""
        
        return prompt
    
    def _build_optimized_summary_prompt(self, data: Dict[str, Any]) -> str:
        """构建优化版摘要提示词"""
        conversation_history = data["conversation_history"]
        retrieval_content = data.get("retrieval_content", "")
        
        prompt = f"""生成医疗摘要：

对话：{conversation_history}
文献：{retrieval_content if retrieval_content else "无"}

要求：
- 200-300字，突出关键信息
- 患者信息+症状+分析+依据
- 使用标准医学术语
- 避免绝对化表述

摘要："""
        
        return prompt
    
    def _build_optimized_fallback_prompt(self, data: Dict[str, Any]) -> str:
        """构建优化版回退提示词"""
        query = data["query"]
        
        prompt = f"""医疗AI助手。

问题：{query}

请提供：
1. 问题理解
2. 一般建议
3. 就医建议
4. 重要提醒

要求：温和专业，避免具体诊断，强调咨询医生。"""
        
        return prompt
    
    # ==================== 超精简版提示词构建方法 ====================
    
    def _build_ultra_compact_diagnosis_prompt(self, data: Dict[str, Any]) -> str:
        """构建超精简版诊断提示词"""
        question = data["question"]
        context = data["context"]
        response_type = data["response_type"]
        
        if response_type == "diagnosis":
            prompt = f"""症状：{question}

请分析并提供建议："""
        elif response_type == "advice":
            prompt = f"""医疗AI助手。

问题：{question}
知识：{context}

请提供：1.健康建议 2.预防措施 3.生活方式 4.就医时机
注意：仅供参考，不能替代专业医生。"""
        elif response_type == "explanation":
            prompt = f"""医疗AI助手。

问题：{question}
知识：{context}

请提供：1.详细解释 2.相关机制 3.临床表现 4.治疗原则
注意：仅供参考，不能替代专业医生。"""
        else:
            prompt = f"""医疗AI助手。

问题：{question}
知识：{context}

格式：1.问题回应 2.医学分析 3.就医建议 4.免责声明
要求：概率性表述，不替代医生诊断。"""
        
        return prompt
    
    def _build_ultra_compact_summary_prompt(self, data: Dict[str, Any]) -> str:
        """构建超精简版摘要提示词"""
        conversation_history = data["conversation_history"]
        retrieval_content = data.get("retrieval_content", "")
        
        prompt = f"""生成医疗摘要：

对话：{conversation_history}
文献：{retrieval_content if retrieval_content else "无"}

要求：200-300字，突出关键信息，使用标准医学术语，避免绝对化表述

摘要："""
        
        return prompt
    
    def _build_ultra_compact_fallback_prompt(self, data: Dict[str, Any]) -> str:
        """构建超精简版回退提示词"""
        query = data["query"]
        
        prompt = f"""医疗AI助手。

问题：{query}

请提供：1.问题理解 2.一般建议 3.就医建议 4.重要提醒
要求：温和专业，避免具体诊断，强调咨询医生。"""
        
        return prompt


# 便捷函数
def build_diagnosis_prompt(question: str, context: str, response_type: str = "diagnosis", mode: str = "optimized") -> str:
    """构建诊断提示词的便捷函数"""
    engine = DiagnosisPromptEngine(mode)
    return engine.build_diagnosis_prompt(question, context, response_type)


def build_summary_prompt(conversation_history: str, retrieval_content: str = "", mode: str = "optimized") -> str:
    """构建摘要提示词的便捷函数"""
    engine = DiagnosisPromptEngine(mode)
    return engine.build_summary_prompt(conversation_history, retrieval_content)


def build_fallback_prompt(query: str, response_type: str = "diagnosis", mode: str = "optimized") -> str:
    """构建回退提示词的便捷函数"""
    engine = DiagnosisPromptEngine(mode)
    return engine.build_fallback_prompt(query, response_type)


# 提示词长度统计
PROMPT_LENGTH_STATS = {
    "standard": {
        "diagnosis_prompt": 800,
        "summary_prompt": 400,
        "fallback_prompt": 600
    },
    "optimized": {
        "diagnosis_prompt": 200,
        "summary_prompt": 150,
        "fallback_prompt": 100
    },
    "ultra_compact": {
        "diagnosis_prompt": 100,
        "summary_prompt": 80,
        "fallback_prompt": 60
    }
}

# Token节省统计
TOKEN_SAVINGS = {
    "optimized_vs_standard": "平均节省75% token",
    "ultra_compact_vs_standard": "平均节省87% token",
    "ultra_compact_vs_optimized": "平均节省50% token"
}
