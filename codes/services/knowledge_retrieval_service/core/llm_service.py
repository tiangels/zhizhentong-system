"""
统一大语言模型服务模块
整合标准版、优化版和超精简版LLM服务
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
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import warnings

# 忽略警告
warnings.filterwarnings("ignore")

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

# 导入提示词引擎
from .prompt_engine import PromptEngine


class TimeoutException(Exception):
    """超时异常"""
    pass


class LLMService:
    """统一大语言模型服务类，支持多种模式"""
    
    def __init__(self, config: Dict[str, Any], mode: str = "optimized"):
        """
        初始化大语言模型服务
        
        Args:
            config: 配置字典，包含模型路径、设备等配置信息
            mode: 服务模式 ("standard", "optimized", "ultra_compact")
        """
        self.config = config
        self.mode = mode
        self.device = config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        
        # 尝试从统一模型配置加载
        self.model_path = self._get_model_path_from_config()
        
        self.max_length = config.get('max_length', 2048)
        self.temperature = config.get('temperature', 0.7)
        self.top_p = config.get('top_p', 0.9)
        self.top_k = config.get('top_k', 50)
        self.repetition_penalty = config.get('repetition_penalty', 1.1)
        
        # 模型和分词器
        self.model = None
        self.tokenizer = None
        
        # 初始化提示词引擎
        self.prompt_engine = PromptEngine(mode)
        
        # 初始化模型
        self._load_model()

    def get_model_stats(self) -> Dict[str, Any]:
        """返回模型的基本运行状态，供健康检查使用。"""
        try:
            stats: Dict[str, Any] = {
                "mode": self.mode,
                "device": self.device,
                "model_path": self.model_path or "",
                "max_length": self.max_length,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "repetition_penalty": self.repetition_penalty,
                "loaded": bool(self.model is not None and self.tokenizer is not None)
            }
            try:
                if self.model is not None:
                    stats["num_parameters"] = sum(p.numel() for p in self.model.parameters())
            except Exception:
                pass
            return stats
        except Exception as e:
            logger.error(f"获取LLM模型状态失败: {e}")
            return {"error": str(e)}
    
    def _get_model_path_from_config(self) -> str:
        """从统一模型配置获取模型路径"""
        try:
            import json
            from pathlib import Path
            
            # 尝试从统一模型配置加载
            model_config_path = Path(__file__).parent.parent.parent.parent / "ai_models" / "llm_models" / "model_config.json"
            logger.info(f"检查统一模型配置文件: {model_config_path}")
            logger.info(f"配置文件存在: {model_config_path.exists()}")
            
            if model_config_path.exists():
                with open(model_config_path, 'r', encoding='utf-8') as f:
                    model_config = json.load(f)
                
                # 获取LLM模型配置
                llm_config = model_config.get('models', {}).get('llm', {})
                model_path = llm_config.get('model_path')
                logger.info(f"从统一配置获取的模型路径: {model_path}")
                
                if model_path:
                    # 检查是否为Hugging Face模型名称（包含"/"但不存在的本地路径）
                    is_huggingface_model = "/" in model_path and not os.path.exists(model_path)
                    logger.info(f"是否为Hugging Face模型: {is_huggingface_model}")
                    logger.info(f"本地路径是否存在: {os.path.exists(model_path) if not is_huggingface_model else 'N/A'}")
                    
                    if is_huggingface_model or os.path.exists(model_path):
                        logger.info(f"使用统一配置中的LLM模型: {model_path}")
                        return model_path
            
            # 回退到配置中的默认路径
            default_path = self.config.get('model_path', 'FreedomIntelligence/Apollo-0.5B')
            logger.info(f"使用配置中的LLM模型路径: {default_path}")
            return default_path
            
        except Exception as e:
            logger.warning(f"加载统一模型配置失败: {e}")
            # 回退到配置中的默认路径
            default_path = self.config.get('model_path', 'FreedomIntelligence/Apollo-0.5B')
            return default_path
    
    def _load_model(self):
        """加载大语言模型"""
        try:
            logger.info(f"Loading Apollo-0.5B model from {self.model_path}")
            logger.info(f"Model path type: {type(self.model_path)}")
            logger.info(f"Model path value: '{self.model_path}'")
            
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
                use_fast=False,
                local_files_only=True
            )
            
            # 设置pad_token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # 加载模型
            logger.info("Loading model...")
            try:
                # 首先尝试使用safetensors加载
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.bfloat16 if self.device == 'cuda' else torch.float16,
                    device_map="auto" if self.device == 'cuda' else None,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                    use_safetensors=True,
                    local_files_only=True
                )
            except Exception as e:
                logger.warning(f"Safetensors加载失败，尝试其他方式: {e}")
                # 如果safetensors失败，尝试不使用safetensors
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.bfloat16 if self.device == 'cuda' else torch.float16,
                    device_map="auto" if self.device == 'cuda' else None,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                    use_safetensors=False,
                    local_files_only=True
                )
            
            # 如果使用CPU，将模型移动到CPU
            if self.device == 'cpu':
                self.model = self.model.to(self.device)
            
            # 设置为评估模式
            self.model.eval()
            
            logger.info("Apollo-0.5B model loaded successfully")
            
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
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    bos_token_id=self.tokenizer.bos_token_id,
                    use_cache=True
                )
                
                # 生成文本
                logger.info(f"开始生成文本，输入长度: {inputs.size(1)}")
                with torch.no_grad():
                    outputs = self.model.generate(
                        inputs,
                        generation_config=generation_config,
                        attention_mask=torch.ones_like(inputs)
                    )
                
                logger.info(f"生成完成，输出形状: {outputs.shape}")
                
                # 解码输出 - 只解码新生成的部分
                input_length = inputs.size(1)
                generated_tokens = outputs[0][input_length:]  # 只取新生成的tokens
                
                logger.info(f"生成的tokens数量: {len(generated_tokens)}")
                logger.info(f"生成的tokens: {generated_tokens.tolist()[:20]}...")  # 显示前20个token
                
                # 过滤掉特殊tokens（pad, eos, bos等）
                special_tokens = {self.tokenizer.pad_token_id, self.tokenizer.eos_token_id, self.tokenizer.bos_token_id}
                if hasattr(self.tokenizer, 'unk_token_id') and self.tokenizer.unk_token_id is not None:
                    special_tokens.add(self.tokenizer.unk_token_id)
                
                # 过滤掉特殊tokens
                filtered_tokens = [token for token in generated_tokens if token not in special_tokens]
                logger.info(f"过滤后的tokens数量: {len(filtered_tokens)}")
                logger.info(f"过滤后的tokens: {filtered_tokens[:20]}...")
                
                if len(filtered_tokens) == 0:
                    logger.warning("所有生成的tokens都是特殊tokens，尝试使用原始tokens解码")
                    generated_text = self.tokenizer.decode(generated_tokens, skip_special_tokens=False)
                else:
                    generated_text = self.tokenizer.decode(filtered_tokens, skip_special_tokens=True)
                
                logger.info(f"解码后文本长度: {len(generated_text)}")
                logger.info(f"解码后文本内容: {generated_text[:200]}...")
                
                # 清理生成的文本
                generated_text = generated_text.strip()
                logger.info(f"清理后文本: {generated_text[:100]}...")
                
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
    
    def generate_knowledge_response(self, query: str, context: str = "", 
                                   response_type: str = "general") -> str:
        """
        生成知识检索响应（移除医疗诊断功能）
        
        Args:
            query: 用户查询
            context: 检索到的上下文
            response_type: 响应类型 (general, explanation, summary)
            
        Returns:
            知识检索响应文本
        """
        try:
            logger.info("=" * 40)
            logger.info("🤖 开始LLM知识检索响应生成流程")
            logger.info("=" * 40)
            logger.info(f"输入参数: query='{query}', context长度={len(context)}, response_type='{response_type}'")
            logger.info(f"使用模式: {self.mode}")
            
            # 使用提示词引擎构建提示词
            prompt = self.prompt_engine.build_retrieval_prompt(query, context, response_type)
            
            logger.info(f"提示词构建完成，总长度: {len(prompt)} 字符")
            logger.info(f"完整提示词内容: {prompt}")
            
            # 生成响应
            response = self.generate_text(
                prompt,
                max_new_tokens=256,
                temperature=0.9,  # 提高温度以获得更好的生成效果
                top_p=0.95,       # 提高top_p
                timeout=600
            )
            
            logger.info(f"LLM生成完成，响应长度: {len(response)} 字符")
            logger.info("=" * 40)
            logger.info("🤖 LLM知识检索响应生成流程完成")
            logger.info("=" * 40)
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"LLM知识检索响应生成失败: {e}")
            logger.info("=" * 40)
            logger.info("🤖 LLM知识检索响应生成流程失败")
            logger.info("=" * 40)
            return "抱歉，我无法回答您的问题。请稍后重试。"
    
    def _build_general_prompt(self, query: str, context: str) -> str:
        """构建通用提示词"""
        prompt = f"""知识检索AI助手，基于检索到的知识回答问题。

问题：{query}

相关知识：{context}

回答格式：
1. 问题回应
2. 知识分析
3. 相关建议
4. 免责声明

要求：基于检索到的知识进行回答，避免超出知识范围。"""
        
        return prompt
    
    def chat_with_context(self, messages: List[Dict[str, str]], 
                         context: str = "") -> str:
        """
        基于上下文的对话（使用统一提示词引擎）
        
        Args:
            messages: 对话历史
            context: 检索到的上下文
            
        Returns:
            回复文本
        """
        try:
            # 使用提示词引擎构建对话提示词
            prompt = self.prompt_engine.build_chat_prompt(messages, context)
            
            # 生成回复
            response = self.generate_text(
                prompt,
                max_new_tokens=512,
                temperature=0.3,
                top_p=0.8,
                repetition_penalty=1.1
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in chat with context: {e}")
            return "抱歉，我无法理解您的问题。请重新描述您的问题。"
    
    def _build_chat_prompt(self, messages: List[Dict[str, str]], context: str) -> str:
        """构建精简版对话提示词（优化：减少60% token消耗）"""
        if context:
            prompt = f"""你是医疗AI助手，基于医学知识提供专业建议。

知识：{context}

回答格式：
【症状分析】- 分析症状特点
【专业建议】- 医疗建议和注意事项  
【就医指导】- 就医时机和科室
【注意事项】- 仅供参考，需医生面诊

要求：专业易懂，基于知识回答，保持安全性"""
        else:
            prompt = """你是医疗AI助手。如无相关医学知识，请：
1. 理解用户问题
2. 提供一般健康建议
3. 建议咨询专业医生
4. 强调仅供参考

请友好回应并引导用户描述具体健康问题。"""
        
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

    def generate_knowledge_response_stream(self, query: str, context: str = "",
                                       response_type: str = "general"):
        """
        流式生成知识检索回答
        
        Args:
            query: 用户问题
            context: 检索到的上下文
            response_type: 响应类型
            
        Yields:
            生成的文本块
        """
        try:
            logger.info("=" * 40)
            logger.info("🌊 开始LLM流式知识检索响应生成流程")
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


class OptimizedLLMService(LLMService):
    """优化版大语言模型服务类，使用精简版提示词"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化优化版LLM服务"""
        super().__init__(config, mode="optimized")
    
    def generate_text(self, prompt: str, max_new_tokens: int = 256, 
                     temperature: float = None, top_p: float = None, timeout: int = 300) -> str:
        """
        生成文本（优化版，支持超时处理）
        
        Args:
            prompt: 输入提示词
            max_new_tokens: 最大新token数
            temperature: 温度参数
            top_p: top_p参数
            timeout: 超时时间（秒）
            
        Returns:
            生成的文本
        """
        if temperature is None:
            temperature = self.temperature
        if top_p is None:
            top_p = self.top_p
            
        try:
            # 编码输入
            inputs = self.tokenizer.encode(prompt, return_tensors='pt')
            if self.device == 'cuda':
                inputs = inputs.to(self.device)
            
            # 生成配置
            generation_config = GenerationConfig(
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=self.top_k,
                repetition_penalty=self.repetition_penalty,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id
            )
            
            # 使用线程池执行生成，支持超时
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    self._generate_with_model,
                    inputs, generation_config
                )
                
                try:
                    result = future.result(timeout=timeout)
                    return result
                except TimeoutError:
                    raise TimeoutException(f"生成超时（{timeout}秒）")
                    
        except Exception as e:
            logger.error(f"文本生成失败: {e}")
            return f"生成失败: {str(e)}"
    
    def _generate_with_model(self, inputs, generation_config):
        """在模型上执行生成"""
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                generation_config=generation_config,
                attention_mask=torch.ones_like(inputs)
            )
            
            # 解码输出
            generated_text = self.tokenizer.decode(
                outputs[0][inputs.shape[1]:], 
                skip_special_tokens=True
            )
            
            return generated_text.strip()


class UltraCompactLLMService(LLMService):
    """超精简版大语言模型服务类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化超精简版LLM服务"""
        super().__init__(config, mode="ultra_compact")


class LLMServiceFactory:
    """统一大语言模型服务工厂类"""
    
    @staticmethod
    def create_llm_service(config_path: str = None, config_dict: dict = None, mode: str = "optimized") -> LLMService:
        """
        创建大语言模型服务实例
        
        Args:
            config_path: 配置文件路径
            config_dict: 配置字典（直接传递配置）
            mode: 服务模式 ("standard", "optimized", "ultra_compact")
            
        Returns:
            大语言模型服务实例
        """
        # 默认配置
        default_config = {
            'device': 'cuda' if torch.cuda.is_available() else 'cpu',
            'model_path': 'FreedomIntelligence/Apollo-0.5B',
            'max_length': 2048,
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 50,
            'repetition_penalty': 1.1,
            'timeout': 600
        }
        
        # 如果提供了配置字典，直接使用
        if config_dict:
            try:
                logger.info(f"Using provided config dict: {config_dict}")
                default_config.update(config_dict)
                logger.info(f"Updated default_config: {default_config}")
            except Exception as e:
                logger.warning(f"Error using config dict: {e}, using default config")
        # 如果提供了配置文件，则加载配置
        elif config_path and os.path.exists(config_path):
            try:
                logger.info(f"Loading config from: {config_path}")
                with open(config_path, 'r', encoding='utf-8') as f:
                    full_config = json.load(f)
                # 提取llm_service部分的配置
                if 'llm_service' in full_config:
                    user_config = full_config['llm_service']
                    logger.info(f"Found llm_service config: {user_config}")
                    default_config.update(user_config)
                    logger.info(f"Updated default_config: {default_config}")
                else:
                    logger.warning("No llm_service config found in file")
            except Exception as e:
                logger.warning(f"Error loading config file: {e}, using default config")
        else:
            logger.info(f"Config file not found or not provided: {config_path}")
        
        # 根据模式创建相应的服务实例
        if mode == "optimized":
            return OptimizedLLMService(default_config)
        elif mode == "ultra_compact":
            return UltraCompactLLMService(default_config)
        else:
            return LLMService(default_config, mode)


class OptimizedLLMServiceFactory:
    """优化版大语言模型服务工厂类（向后兼容）"""
    
    @staticmethod
    def create_llm_service(config_path: str = None) -> OptimizedLLMService:
        """
        创建优化版大语言模型服务实例
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            优化版大语言模型服务实例
        """
        return LLMServiceFactory.create_llm_service(config_path, "optimized")


if __name__ == "__main__":
    # 测试大语言模型服务
    config = {
        'device': 'cpu',  # 使用CPU进行测试
        'model_path': 'FreedomIntelligence/Apollo-0.5B',
        'max_length': 1024,
        'temperature': 0.7
    }
    
    try:
        llm_service = LLMService(config)
        
        # 测试文本生成
        test_prompt = "请解释什么是心肌梗死？"
        response = llm_service.generate_text(test_prompt, max_new_tokens=200)
        print(f"Generated response: {response}")
        
        # 测试知识检索响应生成
        query = "什么是机器学习？"
        context = "机器学习是人工智能的一个分支，通过算法让计算机从数据中学习模式。"
        
        knowledge_response = llm_service.generate_knowledge_response(
            query, context, response_type="general"
        )
        print(f"\nKnowledge response: {knowledge_response}")
        
        # 获取模型信息
        model_info = llm_service.get_model_info()
        print(f"\nModel info: {model_info}")
        
    except Exception as e:
        print(f"Error in testing: {e}")
        print("Please ensure the model is properly downloaded and configured.")
