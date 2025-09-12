"""
大语言模型服务模块
负责调用Qwen2-0.5B-Medical-MLX模型进行文本生成
"""

import os
import json
import logging
import torch
import threading
import time
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
import warnings

# 忽略警告
warnings.filterwarnings("ignore")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    """超时异常"""
    pass


class LLMService:
    """大语言模型服务类，负责文本生成"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化大语言模型服务
        
        Args:
            config: 配置字典，包含模型路径、设备等配置信息
        """
        self.config = config
        self.device = config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        self.model_path = config.get('model_path', '/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/codes/ai_models/llm_models/Qwen3-1.7b-Medical-R1-sft')
        self.max_length = config.get('max_length', 2048)
        self.temperature = config.get('temperature', 0.7)
        self.top_p = config.get('top_p', 0.9)
        self.top_k = config.get('top_k', 50)
        self.repetition_penalty = config.get('repetition_penalty', 1.1)
        
        # 模型和分词器
        self.model = None
        self.tokenizer = None
        
        # 初始化模型
        self._load_model()
    
    def _load_model(self):
        """加载大语言模型"""
        try:
            logger.info(f"Loading Qwen2 Medical model from {self.model_path}")
            
            # 检查模型路径是否存在（支持本地路径和Hugging Face模型名称）
            is_huggingface_model = "/" in self.model_path and not os.path.exists(self.model_path)
            if not is_huggingface_model and not os.path.exists(self.model_path):
                logger.error(f"Model path does not exist: {self.model_path}")
                raise FileNotFoundError(f"Model path does not exist: {self.model_path}")
            
            # 加载分词器
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                use_fast=False
            )
            
            # 设置pad_token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # 加载模型
            logger.info("Loading model...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.bfloat16 if self.device == 'cuda' else torch.float32,
                device_map="auto" if self.device == 'cuda' else None,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                use_safetensors=True
            )
            
            # 如果使用CPU，将模型移动到CPU
            if self.device == 'cpu':
                self.model = self.model.to(self.device)
            
            # 设置为评估模式
            self.model.eval()
            
            logger.info("Qwen2 Medical model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def generate_text(self, prompt: str, max_new_tokens: int = 128, 
                     temperature: float = None, top_p: float = None,
                     top_k: int = None, repetition_penalty: float = None,
                     timeout: int = 600) -> str:
        """
        生成文本（带超时处理）
        
        Args:
            prompt: 输入提示词
            max_new_tokens: 最大生成token数（减少到256）
            temperature: 温度参数
            top_p: top_p参数
            top_k: top_k参数
            repetition_penalty: 重复惩罚参数
            timeout: 超时时间（秒）
            
        Returns:
            生成的文本
        """
        result = [None]
        exception = [None]
        
        def generate_worker():
            """在单独线程中执行生成任务"""
            try:
                # 使用传入参数或默认参数
                gen_temperature = temperature or self.temperature
                gen_top_p = top_p or self.top_p
                gen_top_k = top_k or self.top_k
                gen_repetition_penalty = repetition_penalty or self.repetition_penalty
                
                # 编码输入
                inputs = self.tokenizer.encode(prompt, return_tensors="pt")
                if inputs.size(1) > self.max_length:
                    inputs = inputs[:, -self.max_length:]
                
                # 移动到设备
                inputs = inputs.to(self.device)
                
                # 生成配置（优化参数）
                generation_config = GenerationConfig(
                    max_new_tokens=max_new_tokens,
                    temperature=gen_temperature,
                    top_p=gen_top_p,
                    top_k=gen_top_k,
                    repetition_penalty=gen_repetition_penalty,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    bos_token_id=self.tokenizer.bos_token_id,
                    use_cache=True
                )
                
                # 生成文本
                with torch.no_grad():
                    outputs = self.model.generate(
                        inputs,
                        generation_config=generation_config,
                        attention_mask=torch.ones_like(inputs)
                    )
                
                # 解码输出
                generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # 移除输入部分，只返回生成的部分
                if generated_text.startswith(prompt):
                    generated_text = generated_text[len(prompt):].strip()
                
                result[0] = generated_text
                
            except Exception as e:
                exception[0] = e
        
        try:
            # 启动生成线程
            thread = threading.Thread(target=generate_worker)
            thread.daemon = True
            thread.start()
            
            # 等待完成或超时
            thread.join(timeout=timeout)
            
            if thread.is_alive():
                # 超时
                logger.warning(f"LLM generation timeout after {timeout} seconds")
                return "抱歉，生成回答超时，请稍后重试。"
            
            if exception[0]:
                # 有异常
                raise exception[0]
            
            if result[0] is None:
                return "抱歉，生成回答时出现错误。"
            
            return result[0]
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return "抱歉，生成回答时出现错误。"
    
    def generate_general_response(self, query: str, response_type: str = "general") -> str:
        """
        生成通用响应（当没有找到相关医学知识时）
        
        Args:
            query: 用户查询
            response_type: 响应类型
            
        Returns:
            通用响应文本
        """
        try:
            logger.info("开始LLM通用响应生成...")
            
            # 构建通用提示词
            prompt = self._build_general_fallback_prompt(query, response_type)
            logger.info(f"通用提示词长度: {len(prompt)} 字符")
            
            # 生成响应
            response = self.generate_text(
                prompt,
                max_new_tokens=512,
                temperature=0.3,  # 使用较低温度确保回答更准确
                timeout=600  # 增加超时时间到120秒
            )
            
            logger.info(f"LLM通用响应生成完成，响应长度: {len(response)} 字符")
            
            return response
            
        except Exception as e:
            logger.error(f"LLM通用响应生成失败: {e}")
            return "抱歉，我无法回答您的问题。建议您咨询专业医生获取准确信息。"
    
    def generate_medical_response(self, query: str, context: str = "", 
                                response_type: str = "diagnosis") -> str:
        """
        生成医疗响应
        
        Args:
            query: 用户查询
            context: 检索到的上下文
            response_type: 响应类型 (diagnosis, advice, explanation)
            
        Returns:
            医疗响应文本
        """
        try:
            logger.info("=" * 40)
            logger.info("🤖 开始LLM医疗响应生成流程")
            logger.info("=" * 40)
            logger.info(f"输入参数: query='{query}', context长度={len(context)}, response_type='{response_type}'")
            
            # 1. 获取用户输入
            logger.info("步骤1: 获取用户输入")
            logger.info(f"用户查询: '{query}'")
            logger.info(f"查询长度: {len(query)} 字符")
            logger.info(f"上下文长度: {len(context)} 字符")
            logger.info(f"响应类型: {response_type}")
            logger.info(f"完整上下文内容: {context}")
            logger.info("步骤1: 获取用户输入完成")
            
            # 2. 用户数据处理
            logger.info("步骤2: 开始构建医疗提示词")
            logger.info(f"查询长度: {len(query)} 字符")
            logger.info(f"上下文长度: {len(context)} 字符")
            logger.info(f"响应类型: {response_type}")
            
            # 构建医疗提示词
            if response_type == "diagnosis":
                prompt = self._build_diagnosis_prompt(query, context)
                logger.info("构建诊断提示词")
            elif response_type == "advice":
                prompt = self._build_advice_prompt(query, context)
                logger.info("构建建议提示词")
            elif response_type == "explanation":
                prompt = self._build_explanation_prompt(query, context)
                logger.info("构建解释提示词")
            else:
                prompt = self._build_general_prompt(query, context)
                logger.info("构建通用提示词")
            
            logger.info(f"提示词构建完成，总长度: {len(prompt)} 字符")
            logger.info(f"完整提示词内容: {prompt}")
            logger.info("步骤2: 构建医疗提示词完成")
            
            # 3. 调用大模型生成回答
            logger.info("步骤3: 开始调用LLM生成医疗响应")
            logger.info(f"LLM调用参数: max_new_tokens=128, temperature=0.7, timeout=600")
            logger.info(f"发送给LLM的完整提示词: {prompt}")
            
            # 生成响应
            response = self.generate_text(
                prompt,
                max_new_tokens=128,  # 减少token数量
                temperature=0.7,
                timeout=600  # 增加超时时间到600秒
            )
            
            logger.info(f"LLM生成完成")
            logger.info(f"原始响应长度: {len(response)} 字符")
            logger.info(f"LLM生成的原始响应: {response}")
            
            # 清理响应内容
            cleaned_response = response.strip()
            logger.info(f"清理后响应长度: {len(cleaned_response)} 字符")
            logger.info(f"清理后响应内容: {cleaned_response}")
            
            logger.info("步骤3: 调用LLM生成医疗响应完成")
            logger.info("=" * 40)
            logger.info("🤖 LLM医疗响应生成流程完成")
            logger.info("=" * 40)
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"LLM医疗响应生成失败: {e}")
            logger.error(f"错误详情: {str(e)}")
            logger.info("=" * 40)
            logger.info("🤖 LLM医疗响应生成流程失败")
            logger.info("=" * 40)
            return "抱歉，我无法生成医疗建议。请咨询专业医生。"
    
    def _build_diagnosis_prompt(self, query: str, context: str) -> str:
        """构建诊断提示词"""
        prompt = f"""作为一位专业的医疗AI助手，请根据以下信息提供诊断建议：
        用户症状描述：{query}

        相关医学知识：
        {context}

        请提供：
        1. 可能的疾病诊断
        2. 诊断依据
        3. 建议的检查项目
        4. 注意事项

        注意：这仅供参考，不能替代专业医生的诊断。"""
        
        return prompt
    
    def _build_advice_prompt(self, query: str, context: str) -> str:
        """构建建议提示词"""
        prompt = f"""作为一位专业的医疗AI助手，请根据以下信息提供健康建议：

        用户问题：{query}

        相关医学知识：
        {context}

        请提供：
        1. 健康建议
        2. 预防措施
        3. 生活方式建议
        4. 何时需要就医

        注意：这仅供参考，不能替代专业医生的建议。"""
        
        return prompt
    
    def _build_explanation_prompt(self, query: str, context: str) -> str:
        """构建解释提示词"""
        prompt = f"""作为一位专业的医疗AI助手，请解释以下医学概念：

        用户问题：{query}

        相关医学知识：
        {context}

        请提供：
        1. 详细解释
        2. 相关机制
        3. 临床表现
        4. 治疗原则

        注意：这仅供参考，不能替代专业医生的解释。"""
        
        return prompt
    
    def _build_general_prompt(self, query: str, context: str) -> str:
        """构建通用提示词"""
        prompt = f"""你是一位专业的医疗AI助手，具有丰富的医学知识和临床经验。请根据用户的问题和提供的医学知识，给出专业、准确、实用的医疗建议。

        用户问题：{query}

        相关医学知识：
        {context}

        请按照以下专业格式回答：

        【症状分析】
        - 根据用户描述，分析可能的症状特点
        - 结合医学知识，说明症状的可能原因

        【专业建议】
        - 提供具体的医疗建议和注意事项
        - 建议必要的检查或观察要点
        - 给出生活调理建议

        【就医指导】
        - 明确什么情况下需要及时就医
        - 建议就诊科室和检查项目
        - 提醒紧急情况的处理方式

        【注意事项】
        - 强调此回答仅供参考，不能替代专业诊断
        - 提醒用户及时咨询专业医生

        要求：
        - 语言专业但易懂，避免过于复杂的医学术语
        - 回答要具体实用，不要泛泛而谈
        - 基于提供的医学知识进行回答，不要编造信息
        - 保持医疗建议的准确性和安全性"""
        
        return prompt
    
    def chat_with_context(self, messages: List[Dict[str, str]], 
                         context: str = "") -> str:
        """
        基于上下文的对话
        
        Args:
            messages: 对话历史
            context: 检索到的上下文
            
        Returns:
            回复文本
        """
        try:
            # 构建对话提示词
            prompt = self._build_chat_prompt(messages, context)
            
            # 生成回复
            response = self.generate_text(
                prompt,
                max_new_tokens=1024,  # 增加生成长度，支持更详细的回答
                temperature=0.3,      # 降低温度，提高回答的准确性和一致性
                top_p=0.8,           # 调整top_p，提高回答质量
                repetition_penalty=1.1  # 避免重复
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in chat with context: {e}")
            return "抱歉，我无法理解您的问题。请重新描述您的问题。"
    
    def _build_chat_prompt(self, messages: List[Dict[str, str]], context: str) -> str:
        """构建对话提示词"""
        prompt = """你是一位专业的医疗AI助手，具有丰富的医学知识和临床经验。

        """
        
        # 添加医学知识上下文
        if context:
            prompt += f"相关医学知识：\n{context}\n\n"
            prompt += """请根据用户的问题和提供的医学知识，给出专业、准确、实用的医疗建议。

            请按照以下专业格式回答：

            【症状分析】
            - 根据用户描述，分析可能的症状特点
            - 结合医学知识，说明症状的可能原因

            【专业建议】
            - 提供具体的医疗建议和注意事项
            - 建议必要的检查或观察要点
            - 给出生活调理建议

            【就医指导】
            - 明确什么情况下需要及时就医
            - 建议就诊科室和检查项目
            - 提醒紧急情况的处理方式

            【注意事项】
            - 强调此回答仅供参考，不能替代专业诊断
            - 提醒用户及时咨询专业医生

            要求：
            - 语言专业但易懂，避免过于复杂的医学术语
            - 回答要具体实用，不要泛泛而谈
            - 基于提供的医学知识进行回答，不要编造信息
            - 保持医疗建议的准确性和安全性"""
        else:
            prompt += """请注意：我没有找到与用户问题相关的医学知识。

            请根据以下情况判断用户输入的性质：

            1. 如果用户只是简单的问候（如"你好"、"您好"等），请友好地回应并引导用户描述具体的健康问题。

            2. 如果用户询问的是医疗相关问题，但没有找到相关医学知识，请：
            - 理解用户的问题和关注点
            - 提供一般性的健康建议
            - 强烈建议用户咨询专业医生
            - 强调此回答仅供参考，不能替代专业诊断

            3. 如果用户的问题不明确，请询问更多细节以便提供更好的帮助。

            要求：
            - 语言温和、专业
            - 避免给出具体的诊断或治疗建议
            - 重点强调咨询专业医生的重要性
            - 保持回答的谨慎性和安全性"""
        
        # 添加对话历史
        prompt += "\n\n对话历史：\n"
        for message in messages[-6:]:  # 只保留最近6轮对话
            role = "用户" if message["role"] == "user" else "助手"
            prompt += f"{role}：{message['content']}\n"
        
        return prompt
    
    def _build_general_fallback_prompt(self, query: str, response_type: str) -> str:
        """构建通用回退提示词（当没有找到相关医学知识时）"""
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
    
    def summarize_text(self, text: str, max_length: int = 200) -> str:
        """
        文本摘要
        
        Args:
            text: 输入文本
            max_length: 最大长度
            
        Returns:
            摘要文本
        """
        try:
            prompt = f"请为以下医学文本提供简洁的摘要（不超过{max_length}字）：\n\n{text}"
            
            summary = self.generate_text(
                prompt,
                max_new_tokens=max_length,
                temperature=0.3
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            return text[:max_length] + "..." if len(text) > max_length else text
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词
        
        Args:
            text: 输入文本
            
        Returns:
            关键词列表
        """
        try:
            prompt = f"请从以下医学文本中提取关键词（用逗号分隔）：\n\n{text}"
            
            keywords_text = self.generate_text(
                prompt,
                max_new_tokens=100,
                temperature=0.3
            )
            
            # 解析关键词
            keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
            
            return keywords[:10]  # 最多返回10个关键词
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        try:
            return {
                'model_path': self.model_path,
                'device': self.device,
                'max_length': self.max_length,
                'temperature': self.temperature,
                'top_p': self.top_p,
                'top_k': self.top_k,
                'repetition_penalty': self.repetition_penalty,
                'vocab_size': len(self.tokenizer) if self.tokenizer else 0,
                'model_loaded': self.model is not None
            }
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {}

    def generate_medical_response_stream(self, query: str, context: str = "",
                                       response_type: str = "general"):
        """
        流式生成医学回答
        
        Args:
            query: 用户问题
            context: 检索到的上下文
            response_type: 响应类型
            
        Yields:
            生成的文本块
        """
        try:
            logger.info("=" * 40)
            logger.info("🌊 开始LLM流式医疗响应生成流程")
            logger.info("=" * 40)
            logger.info(f"输入参数: query='{query}', context长度={len(context)}, response_type='{response_type}'")
            
            # 构建医学回答提示词
            logger.info("步骤1: 开始构建流式医学回答提示词")
            logger.info(f"用户查询: '{query}'")
            logger.info(f"上下文长度: {len(context)} 字符")
            logger.info(f"响应类型: {response_type}")
            
            if context:
                logger.info("使用带上下文的提示词模板")
                prompt = f"""基于以下医学知识回答问题：

医学知识：
{context}

问题：{query}

回答："""
                logger.info(f"完整上下文内容: {context}")
            else:
                logger.info("使用无上下文的提示词模板")
                prompt = f"""请回答以下医学问题：

问题：{query}

回答："""
            
            logger.info(f"提示词构建完成，总长度: {len(prompt)} 字符")
            logger.info(f"完整提示词内容: {prompt}")
            logger.info("步骤1: 构建流式医学回答提示词完成")
            
            # 流式生成
            logger.info("步骤2: 开始流式生成医学回答")
            logger.info("调用内部流式生成方法: _generate_stream")
            
            chunk_count = 0
            total_chars = 0
            
            for chunk in self._generate_stream(prompt):
                chunk_count += 1
                total_chars += len(chunk)
                logger.info(f"生成第{chunk_count}个文本块，长度: {len(chunk)} 字符，内容: '{chunk}'")
                yield chunk
            
            logger.info(f"流式生成完成，总共生成 {chunk_count} 个文本块，总长度: {total_chars} 字符")
            logger.info("步骤2: 流式生成医学回答完成")
            logger.info("=" * 40)
            logger.info("🌊 LLM流式医疗响应生成流程完成")
            logger.info("=" * 40)
                
        except Exception as e:
            logger.error(f"流式生成医学回答出错：{e}")
            logger.error(f"错误详情: {str(e)}")
            logger.info("=" * 40)
            logger.info("🌊 LLM流式医疗响应生成流程失败")
            logger.info("=" * 40)
            yield f"生成回答时出错：{str(e)}"

    
    def _generate_stream(self, prompt: str, max_new_tokens: int = 256):
        """
        流式生成文本
        
        Args:
            prompt: 输入提示词
            max_new_tokens: 最大生成token数
            
        Yields:
            生成的文本块
        """
        try:
            if not self.tokenizer or not self.model:
                yield "模型未初始化，请检查配置"
                return
            
            # 编码输入
            inputs = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
            
            # 生成参数
            generation_config = {
                'max_new_tokens': max_new_tokens,
                'temperature': self.temperature,
                'top_p': self.top_p,
                'top_k': self.top_k,
                'repetition_penalty': self.repetition_penalty,
                'do_sample': True,
                'pad_token_id': self.tokenizer.eos_token_id
            }
            
            # 流式生成
            with torch.no_grad():
                for output in self.model.generate(
                    inputs,
                    **generation_config,
                    return_dict_in_generate=True,
                    output_scores=True
                ):
                    # 检查output类型并解码新生成的token
                    if hasattr(output, 'sequences') and output.sequences is not None:
                        new_tokens = output.sequences[0][inputs.shape[1]:]
                        if len(new_tokens) > 0:
                            new_text = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
                            if new_text:
                                yield new_text
                    else:
                        # 如果output不是预期的格式，跳过
                        continue
                            
        except Exception as e:
            logger.error(f"流式生成文本出错：{e}")
            yield f"生成文本时出错：{str(e)}"


class LLMServiceFactory:
    """大语言模型服务工厂类"""
    
    @staticmethod
    def create_llm_service(config_path: str = None) -> LLMService:
        """
        创建大语言模型服务实例
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            大语言模型服务实例
        """
        # 默认配置
        default_config = {
            'device': 'cuda' if torch.cuda.is_available() else 'cpu',
            'model_path': '/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/codes/ai_models/llm_models/Qwen2-0.5B-Medical-MLX',
            'max_length': 2048,
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 50,
            'repetition_penalty': 1.1,
            'timeout': 600
        }
        
        # 如果提供了配置文件，则加载配置
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    full_config = json.load(f)
                # 提取llm_service部分的配置
                if 'llm_service' in full_config:
                    user_config = full_config['llm_service']
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Error loading config file: {e}, using default config")
        
        return LLMService(default_config)


if __name__ == "__main__":
    # 测试大语言模型服务
    config = {
        'device': 'cpu',  # 使用CPU进行测试
        'model_path': 'ai_models/llm_models/Qwen2-0.5B-Medical-MLX',
        'max_length': 1024,
        'temperature': 0.7
    }
    
    try:
        llm_service = LLMService(config)
        
        # 测试文本生成
        test_prompt = "请解释什么是心肌梗死？"
        response = llm_service.generate_text(test_prompt, max_new_tokens=200)
        print(f"Generated response: {response}")
        
        # 测试医疗响应生成
        query = "我最近经常感到胸痛，这是什么原因？"
        context = "胸痛可能由多种原因引起，包括心血管疾病、肺部疾病等。"
        
        medical_response = llm_service.generate_medical_response(
            query, context, response_type="diagnosis"
        )
        print(f"\nMedical response: {medical_response}")
        
        # 获取模型信息
        model_info = llm_service.get_model_info()
        print(f"\nModel info: {model_info}")
        
    except Exception as e:
        print(f"Error in testing: {e}")
        print("Please ensure the model is properly downloaded and configured.")
