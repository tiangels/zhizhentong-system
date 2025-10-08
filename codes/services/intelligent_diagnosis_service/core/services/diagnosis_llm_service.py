"""
智能诊断大语言模型服务模块
基于Apollo-0.5B模型的医疗诊断生成服务
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
setup_logging("diagnosis_service")
logger = get_logger(__name__)

# 导入提示词引擎
from .diagnosis_prompt_engine import DiagnosisPromptEngine


class TimeoutException(Exception):
    """超时异常"""
    pass


class DiagnosisLLMService:
    """智能诊断大语言模型服务类"""
    
    def __init__(self, config: Dict[str, Any], mode: str = "optimized"):
        """
        初始化智能诊断大语言模型服务
        
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
        
        # 初始化诊断提示词引擎
        self.prompt_engine = DiagnosisPromptEngine(mode)
        
        # 初始化模型
        self._load_model()
    
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
    
    def generate_diagnosis_response(self, query: str, context: str = "", 
                                   response_type: str = "diagnosis") -> str:
        """
        生成诊断响应（使用统一提示词引擎）
        
        Args:
            query: 用户查询
            context: 检索到的上下文
            response_type: 响应类型 (diagnosis, advice, explanation)
            
        Returns:
            诊断响应文本
        """
        try:
            logger.info("=" * 40)
            logger.info("🤖 开始智能诊断响应生成流程")
            logger.info("=" * 40)
            logger.info(f"输入参数: query='{query}', context长度={len(context)}, response_type='{response_type}'")
            logger.info(f"使用模式: {self.mode}")
            
            # 使用诊断提示词引擎构建提示词
            prompt = self.prompt_engine.build_diagnosis_prompt(query, context, response_type)
            
            logger.info(f"提示词构建完成，总长度: {len(prompt)} 字符")
            logger.info(f"完整提示词内容: {prompt}")
            
            # 生成响应
            response = self.generate_text(
                prompt,
                max_new_tokens=512,  # 增加最大token数
                temperature=0.9,    # 提高温度以获得更好的生成效果
                top_p=0.95,         # 提高top_p
                timeout=600
            )
            
            logger.info(f"智能诊断生成完成，响应长度: {len(response)} 字符")
            
            # 检查生成质量
            if not response or response.strip() in ["<|endoftext|>", "", "。", "，"]:
                logger.warning("模型生成质量不佳，使用备用响应")
                response = self._generate_fallback_response(query, response_type)
            
            logger.info("=" * 40)
            logger.info("🤖 智能诊断响应生成流程完成")
            logger.info("=" * 40)
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"智能诊断响应生成失败: {e}")
            logger.info("=" * 40)
            logger.info("🤖 智能诊断响应生成流程失败")
            logger.info("=" * 40)
            return self._generate_fallback_response(query, response_type)
    
    def _generate_fallback_response(self, query: str, response_type: str) -> str:
        """
        生成备用响应
        
        Args:
            query: 用户查询
            response_type: 响应类型
            
        Returns:
            备用响应文本
        """
        logger.info("生成备用诊断响应")
        
        # 基于症状关键词的简单诊断建议
        symptoms_keywords = {
            "头痛": {
                "causes": ["紧张性头痛", "偏头痛", "高血压", "睡眠不足"],
                "checks": ["血压测量", "神经系统检查", "头部CT/MRI"],
                "advice": ["保持充足睡眠", "减少压力", "避免长时间用眼"]
            },
            "咳嗽": {
                "causes": ["感冒", "支气管炎", "肺炎", "过敏"],
                "checks": ["胸部X光", "血常规", "痰培养"],
                "advice": ["多喝水", "保持室内湿度", "避免刺激性食物"]
            },
            "发热": {
                "causes": ["感染", "炎症", "免疫反应"],
                "checks": ["体温监测", "血常规", "C反应蛋白"],
                "advice": ["多休息", "补充水分", "物理降温"]
            },
            "腹痛": {
                "causes": ["消化不良", "胃炎", "阑尾炎", "肠炎"],
                "checks": ["腹部触诊", "血常规", "腹部B超"],
                "advice": ["清淡饮食", "避免辛辣食物", "观察症状变化"]
            }
        }
        
        # 查找匹配的症状
        matched_symptoms = []
        for symptom, info in symptoms_keywords.items():
            if symptom in query:
                matched_symptoms.append((symptom, info))
        
        if matched_symptoms:
            symptom, info = matched_symptoms[0]
            response = f"""基于您描述的"{symptom}"症状，可能的原因包括：

1. 可能原因：
{chr(10).join(f"- {cause}" for cause in info['causes'])}

2. 建议检查：
{chr(10).join(f"- {check}" for check in info['checks'])}

3. 注意事项：
{chr(10).join(f"- {advice}" for advice in info['advice'])}

⚠️ 重要提醒：
- 以上建议仅供参考，不能替代专业医生的诊断
- 如症状持续或加重，请及时就医
- 如有紧急情况，请立即前往医院急诊科"""
        else:
            response = f"""基于您描述的症状，建议您：

1. 可能原因：
- 需要进一步了解症状的详细情况
- 可能涉及多个系统的疾病

2. 建议检查：
- 详细病史询问
- 体格检查
- 必要的实验室检查

3. 注意事项：
- 记录症状的详细情况（时间、频率、严重程度）
- 观察症状的变化趋势
- 注意是否有其他伴随症状

⚠️ 重要提醒：
- 以上建议仅供参考，不能替代专业医生的诊断
- 建议您尽快咨询专业医生进行详细评估
- 如有紧急情况，请立即就医"""
        
        return response
    
    def generate_text(self, prompt: str, max_new_tokens: int = 256, 
                     temperature: float = None, top_p: float = None,
                     top_k: int = None, repetition_penalty: float = None,
                     timeout: int = 600) -> str:
        """
        生成文本（带超时处理）
        
        Args:
            prompt: 输入提示词
            max_new_tokens: 最大生成token数
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
                    use_cache=True,
                    num_beams=1,
                    no_repeat_ngram_size=2
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
                
                # 改进的token过滤逻辑
                # 首先尝试直接解码所有生成的tokens
                generated_text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
                
                # 如果解码结果为空或太短，尝试不跳过特殊tokens
                if not generated_text or len(generated_text.strip()) < 5:
                    logger.warning("跳过特殊tokens后解码结果为空，尝试包含特殊tokens解码")
                    generated_text = self.tokenizer.decode(generated_tokens, skip_special_tokens=False)
                
                # 如果还是为空，尝试只过滤pad token
                if not generated_text or len(generated_text.strip()) < 5:
                    logger.warning("包含特殊tokens解码仍为空，尝试只过滤pad token")
                    pad_token_id = self.tokenizer.pad_token_id
                    filtered_tokens = [token for token in generated_tokens if token != pad_token_id]
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
    
    def generate_diagnosis_response_stream(self, query: str, context: str = "",
                                         response_type: str = "diagnosis"):
        """
        流式生成诊断回答
        
        Args:
            query: 用户问题
            context: 检索到的上下文
            response_type: 响应类型
            
        Yields:
            生成的文本块
        """
        try:
            logger.info("=" * 40)
            logger.info("🌊 开始智能诊断流式响应生成流程")
            logger.info("=" * 40)
            logger.info(f"输入参数: query='{query}', context长度={len(context)}, response_type='{response_type}'")
            
            # 构建诊断回答提示词
            logger.info("步骤1: 开始构建流式诊断回答提示词")
            logger.info(f"用户查询: '{query}'")
            logger.info(f"上下文长度: {len(context)} 字符")
            logger.info(f"响应类型: {response_type}")
            
            if context:
                logger.info("使用带上下文的提示词模板")
                prompt = f"""基于以下医学知识提供诊断建议：

医学知识：
{context}

问题：{query}

诊断建议："""
                logger.info(f"完整上下文内容: {context}")
            else:
                logger.info("使用无上下文的提示词模板")
                prompt = f"""请提供以下医学问题的诊断建议：

问题：{query}

诊断建议："""
            
            logger.info(f"提示词构建完成，总长度: {len(prompt)} 字符")
            logger.info(f"完整提示词内容: {prompt}")
            logger.info("步骤1: 构建流式诊断回答提示词完成")
            
            # 流式生成
            logger.info("步骤2: 开始流式生成诊断回答")
            logger.info("调用内部流式生成方法: _generate_stream")
            
            chunk_count = 0
            total_chars = 0
            
            for chunk in self._generate_stream(prompt):
                chunk_count += 1
                total_chars += len(chunk)
                logger.info(f"生成第{chunk_count}个文本块，长度: {len(chunk)} 字符，内容: '{chunk}'")
                yield chunk
            
            logger.info(f"流式生成完成，总共生成 {chunk_count} 个文本块，总长度: {total_chars} 字符")
            logger.info("步骤2: 流式生成诊断回答完成")
            logger.info("=" * 40)
            logger.info("🌊 智能诊断流式响应生成流程完成")
            logger.info("=" * 40)
                
        except Exception as e:
            logger.error(f"流式生成诊断回答出错：{e}")
            logger.error(f"错误详情: {str(e)}")
            logger.info("=" * 40)
            logger.info("🌊 智能诊断流式响应生成流程失败")
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
                'model_loaded': self.model is not None,
                'service_type': 'diagnosis_llm_service'
            }
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {}


class DiagnosisLLMServiceFactory:
    """智能诊断大语言模型服务工厂类"""
    
    @staticmethod
    def create_diagnosis_llm_service(config_path: str = None, mode: str = "optimized") -> DiagnosisLLMService:
        """
        创建智能诊断大语言模型服务实例
        
        Args:
            config_path: 配置文件路径
            mode: 服务模式 ("standard", "optimized", "ultra_compact")
            
        Returns:
            智能诊断大语言模型服务实例
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
        
        # 如果提供了配置文件，则加载配置
        if config_path and os.path.exists(config_path):
            try:
                logger.info(f"Loading config from: {config_path}")
                with open(config_path, 'r', encoding='utf-8') as f:
                    full_config = json.load(f)
                # 提取diagnosis_llm_service部分的配置
                if 'diagnosis_llm_service' in full_config:
                    user_config = full_config['diagnosis_llm_service']
                    logger.info(f"Found diagnosis_llm_service config: {user_config}")
                    default_config.update(user_config)
                    logger.info(f"Updated default_config: {default_config}")
                else:
                    logger.warning("No diagnosis_llm_service config found in file")
            except Exception as e:
                logger.warning(f"Error loading config file: {e}, using default config")
        else:
            logger.info(f"Config file not found or not provided: {config_path}")
        
        return DiagnosisLLMService(default_config, mode)


if __name__ == "__main__":
    # 测试智能诊断大语言模型服务
    config = {
        'device': 'cpu',  # 使用CPU进行测试
        'model_path': 'FreedomIntelligence/Apollo-0.5B',
        'max_length': 1024,
        'temperature': 0.7
    }
    
    try:
        llm_service = DiagnosisLLMService(config)
        
        # 测试诊断响应生成
        query = "我最近经常感到胸痛，这是什么原因？"
        context = "胸痛可能由多种原因引起，包括心血管疾病、肺部疾病等。"
        
        diagnosis_response = llm_service.generate_diagnosis_response(
            query, context, response_type="diagnosis"
        )
        print(f"\nDiagnosis response: {diagnosis_response}")
        
        # 获取模型信息
        model_info = llm_service.get_model_info()
        print(f"\nModel info: {model_info}")
        
    except Exception as e:
        print(f"Error in testing: {e}")
        print("Please ensure the model is properly downloaded and configured.")
