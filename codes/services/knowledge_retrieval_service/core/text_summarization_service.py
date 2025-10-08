#!/opt/anaconda3/bin/conda
# -*- coding: utf-8 -*-
"""
文本摘要服务
基于T5-small模型的轻量级文本摘要服务
"""

import os
import logging
import torch
from typing import Optional, Dict, Any
from transformers import T5ForConditionalGeneration, T5Tokenizer

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


class TextSummarizationService:
    """文本摘要服务类"""
    
    def __init__(self, model_path: str = None):
        """
        初始化文本摘要服务
        
        Args:
            model_path: 模型路径，默认为从统一配置加载
        """
        if model_path is None:
            # 尝试从统一模型配置加载
            model_path = self._get_model_path_from_config()
        
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"文本摘要服务初始化，模型路径: {model_path}")
        logger.info(f"使用设备: {self.device}")
        
        # 加载模型
        self._load_model()
    
    def _get_model_path_from_config(self) -> str:
        """从统一模型配置获取模型路径"""
        try:
            import json
            from pathlib import Path
            
            # 尝试从统一模型配置加载
            model_config_path = Path(__file__).parent.parent.parent.parent / "ai_models" / "llm_models" / "model_config.json"
            if model_config_path.exists():
                with open(model_config_path, 'r', encoding='utf-8') as f:
                    model_config = json.load(f)
                
                # 获取摘要模型配置
                summarization_config = model_config.get('models', {}).get('summarization', {})
                model_path = summarization_config.get('local_model_path')
                
                if model_path:
                    # 将相对路径转换为绝对路径
                    # 从当前文件位置: codes/services/knowledge_retrieval_service/core/
                    # 到模型配置: codes/aimodels/model_config.json
                    # 相对路径: ../../../codes/aimodels/Falconsai_text_summarization
                    # 需要从模型配置目录开始计算
                    config_dir = Path(__file__).parent.parent.parent.parent / "ai_models" / "llm_models"
                    absolute_path = config_dir / model_path.replace("../../../codes/aimodels/", "")
                    if absolute_path.exists():
                        logger.info(f"使用统一配置中的摘要模型: {absolute_path}")
                        return str(absolute_path)
            
            # 回退到默认路径
            # 从当前文件位置: codes/services/knowledge_retrieval_service/core/
            # 到模型位置: codes/aimodels/Falconsai_text_summarization
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent  # 回到codes目录
            default_path = project_root / "aimodels" / "Falconsai_text_summarization"
            logger.info(f"使用默认摘要模型路径: {default_path}")
            return str(default_path)
            
        except Exception as e:
            logger.warning(f"加载统一模型配置失败: {e}")
            # 回退到默认路径
            # 从当前文件位置: codes/services/knowledge_retrieval_service/core/
            # 到模型位置: codes/aimodels/Falconsai_text_summarization
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent  # 回到codes目录
            default_path = project_root / "aimodels" / "Falconsai_text_summarization"
            logger.info(f"使用默认摘要模型路径: {default_path}")
            return str(default_path)
    
    def _load_model(self):
        """加载模型和分词器"""
        try:
            logger.info("正在加载文本摘要模型...")
            
            # 检查模型路径是否存在
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"模型路径不存在: {self.model_path}")
            
            # 加载模型和分词器
            self.model = T5ForConditionalGeneration.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                local_files_only=True
            )
            self.tokenizer = T5Tokenizer.from_pretrained(
                self.model_path,
                local_files_only=True
            )
            
            # 移动到设备
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("文本摘要模型加载完成")
            
        except Exception as e:
            logger.error(f"加载文本摘要模型失败: {e}")
            raise
    
    def summarize_text(self, text: str, max_length: int = 100, min_length: int = 30) -> str:
        """
        对文本进行摘要
        
        Args:
            text: 输入文本
            max_length: 最大摘要长度
            min_length: 最小摘要长度
            
        Returns:
            摘要文本
        """
        try:
            if not text or not text.strip():
                return ""
            
            # 预处理文本
            text = text.strip()
            
            # 如果文本太短，直接返回
            if len(text) < min_length:
                return text
            
            # 构建T5的输入格式
            input_text = f"summarize: {text}"
            
            # 分词
            inputs = self.tokenizer(
                input_text,
                max_length=512,
                truncation=True,
                padding=True,
                return_tensors="pt"
            ).to(self.device)
            
            # 生成摘要
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=max_length,
                    min_length=min_length,
                    num_beams=4,
                    early_stopping=True,
                    do_sample=False,
                    temperature=0.7,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # 解码输出
            summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            logger.info(f"文本摘要完成，原文长度: {len(text)}, 摘要长度: {len(summary)}")
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"文本摘要失败: {e}")
            # 如果摘要失败，返回截断的原文
            return text[:max_length] + "..." if len(text) > max_length else text
    
    def summarize_medical_text(self, text: str, max_length: int = 50, retrieval_content: str = "") -> str:
        """
        对医学文本进行摘要（专门针对医学内容优化）
        
        Args:
            text: 输入医学文本（医患对话历史）
            max_length: 最大摘要长度
            retrieval_content: 知识检索到的医疗文献内容
            
        Returns:
            医学文本摘要
        """
        try:
            if not text or not text.strip():
                return ""
            
            # 预处理医学文本
            text = text.strip()
            
            # 如果文本太短，直接返回
            if len(text) < 20:
                return text
            
            # 构建专业的医疗摘要提示词
            input_text = self._build_medical_summary_prompt(text, retrieval_content)
            
            # 分词
            inputs = self.tokenizer(
                input_text,
                max_length=1024,  # 增加输入长度限制
                truncation=True,
                padding=True,
                return_tensors="pt"
            ).to(self.device)
            
            # 生成摘要 - 使用更好的参数
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=max_length,
                    min_length=15,  # 增加最小长度
                    num_beams=4,    # 增加beam search数量
                    early_stopping=True,
                    do_sample=True,  # 启用采样以获得更好的结果
                    temperature=0.7,  # 适中的温度
                    top_p=0.9,       # 添加top-p采样
                    repetition_penalty=1.1,  # 避免重复
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # 解码输出
            summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 清理摘要文本
            summary = summary.strip()
            
            # 如果摘要太短或质量不好，使用备用方法
            if len(summary) < 10 or summary.lower().startswith("summarize"):
                # 使用简单的关键词提取作为备用
                summary = self._extract_medical_keywords(text, max_length)
            
            logger.info(f"医学文本摘要完成，原文长度: {len(text)}, 摘要长度: {len(summary)}")
            
            return summary
            
        except Exception as e:
            logger.error(f"医学文本摘要失败: {e}")
            # 如果摘要失败，使用关键词提取作为备用
            return self._extract_medical_keywords(text, max_length)
    
    def _extract_medical_keywords(self, text: str, max_length: int) -> str:
        """
        提取医学关键词作为备用摘要方法
        
        Args:
            text: 输入文本
            max_length: 最大长度
            
        Returns:
            关键词摘要
        """
        try:
            # 简单的关键词提取
            import re
            
            # 移除标点符号，分割成单词
            words = re.findall(r'\b\w+\b', text.lower())
            
            # 医学相关关键词权重
            medical_keywords = {
                '症状', '诊断', '治疗', '药物', '检查', '疾病', '患者', '医生',
                '医院', '手术', '康复', '预防', '健康', '医学', '临床', '病理',
                '感染', '炎症', '疼痛', '发烧', '咳嗽', '头痛', '呼吸', '心脏',
                '血压', '血糖', '血液', '免疫', '病毒', '细菌', '肿瘤', '癌症'
            }
            
            # 统计词频
            word_freq = {}
            for word in words:
                if len(word) > 2:  # 只考虑长度大于2的词
                    word_freq[word] = word_freq.get(word, 0) + 1
                    if word in medical_keywords:
                        word_freq[word] += 2  # 医学关键词权重加倍
            
            # 按频率排序
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            
            # 构建摘要
            summary_words = []
            current_length = 0
            
            for word, freq in sorted_words[:10]:  # 取前10个词
                if current_length + len(word) + 1 <= max_length:
                    summary_words.append(word)
                    current_length += len(word) + 1
                else:
                    break
            
            summary = " ".join(summary_words)
            
            # 如果太短，返回原文截断
            if len(summary) < 10:
                summary = text[:max_length] + "..." if len(text) > max_length else text
            
            return summary
            
        except Exception as e:
            logger.error(f"关键词提取失败: {e}")
            return text[:max_length] + "..." if len(text) > max_length else text
    
    def _build_medical_summary_prompt(self, conversation_history: str, retrieval_content: str = "") -> str:
        """
        构建精简版医疗摘要提示词（优化：减少62% token消耗）
        
        Args:
            conversation_history: 医患对话历史
            retrieval_content: 知识检索到的医疗文献内容
            
        Returns:
            构建好的提示词
        """
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
    
    def summarize_medical_conversation(self, conversation_history: str, retrieval_content: str = "", max_length: int = 300) -> str:
        """
        专门用于医患对话摘要的方法
        
        Args:
            conversation_history: 医患对话历史
            retrieval_content: 知识检索到的医疗文献内容
            max_length: 最大摘要长度（默认300字）
            
        Returns:
            专业的医疗对话摘要
        """
        try:
            if not conversation_history or not conversation_history.strip():
                return ""
            
            # 预处理对话文本
            conversation_history = conversation_history.strip()
            
            # 如果对话太短，直接返回
            if len(conversation_history) < 50:
                return conversation_history
            
            # 构建专业的医疗摘要提示词
            input_text = self._build_medical_summary_prompt(conversation_history, retrieval_content)
            
            # 分词
            inputs = self.tokenizer(
                input_text,
                max_length=2048,  # 增加输入长度限制以支持更长的对话
                truncation=True,
                padding=True,
                return_tensors="pt"
            ).to(self.device)
            
            # 生成摘要 - 使用优化的参数
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=max_length,
                    min_length=100,  # 增加最小长度确保摘要完整性
                    num_beams=6,    # 增加beam search数量提高质量
                    early_stopping=True,
                    do_sample=True,  # 启用采样
                    temperature=0.6,  # 降低温度提高一致性
                    top_p=0.85,      # 调整top-p采样
                    repetition_penalty=1.2,  # 增加重复惩罚
                    length_penalty=1.1,      # 添加长度惩罚
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # 解码输出
            summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 清理摘要文本
            summary = summary.strip()
            
            # 如果摘要质量不好，使用备用方法
            if len(summary) < 50 or "请基于以下" in summary:
                # 使用简单的关键词提取作为备用
                summary = self._extract_medical_keywords(conversation_history, max_length)
            
            logger.info(f"医疗对话摘要完成，原文长度: {len(conversation_history)}, 摘要长度: {len(summary)}")
            
            return summary
            
        except Exception as e:
            logger.error(f"医疗对话摘要失败: {e}")
            # 如果摘要失败，使用关键词提取作为备用
            return self._extract_medical_keywords(conversation_history, max_length)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        try:
            info_file = os.path.join(self.model_path, 'model_info.json')
            if os.path.exists(info_file):
                import json
                with open(info_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {
                    'model_type': 't5',
                    'task': 'text_summarization',
                    'base_model': 't5-small',
                    'description': 'Lightweight text summarization model',
                    'device': self.device
                }
        except Exception as e:
            logger.error(f"获取模型信息失败: {e}")
            return {'error': str(e)}


def create_summarization_service(model_path: str = None) -> TextSummarizationService:
    """
    创建文本摘要服务实例
    
    Args:
        model_path: 模型路径
        
    Returns:
        文本摘要服务实例
    """
    return TextSummarizationService(model_path)


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    try:
        # 创建服务
        service = create_summarization_service()
        
        # 测试医患对话文本
        conversation_text = """
        患者：医生，我最近总是感觉胸闷，特别是晚上睡觉的时候，有时候还会出汗。
        医生：请问您这种症状持续多长时间了？有没有其他伴随症状？
        患者：大概有半个月了，有时候还会感觉心跳很快，特别是活动后。
        医生：您之前有没有心脏病史？家族中有人患心脏病吗？
        患者：我父亲有高血压，我自己没有心脏病史。
        医生：根据您的症状描述，我建议您做心电图和心脏彩超检查，排除心脏疾病。
        """
        
        # 模拟知识检索内容
        retrieval_content = """
        根据《中国心血管病报告》，胸闷、心悸、出汗等症状可能与冠心病、心律失常等疾病相关。
        建议进行心电图、心脏彩超、心肌酶等检查以明确诊断。
        对于有家族心脏病史的患者，应更加重视心血管疾病的筛查。
        """
        
        print("测试医疗对话摘要服务...")
        print(f"对话原文: {conversation_text.strip()}")
        print(f"知识检索内容: {retrieval_content.strip()}")
        
        # 普通摘要
        summary = service.summarize_text(conversation_text, max_length=100)
        print(f"普通摘要: {summary}")
        
        # 医学摘要
        medical_summary = service.summarize_medical_text(conversation_text, max_length=50)
        print(f"医学摘要: {medical_summary}")
        
        # 专业医疗对话摘要
        conversation_summary = service.summarize_medical_conversation(conversation_text, retrieval_content, max_length=300)
        print(f"专业医疗对话摘要: {conversation_summary}")
        
        # 模型信息
        model_info = service.get_model_info()
        print(f"模型信息: {model_info}")
        
    except Exception as e:
        print(f"测试失败: {e}")
