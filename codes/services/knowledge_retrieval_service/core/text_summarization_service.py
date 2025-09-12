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

logger = logging.getLogger(__name__)


class TextSummarizationService:
    """文本摘要服务类"""
    
    def __init__(self, model_path: str = None):
        """
        初始化文本摘要服务
        
        Args:
            model_path: 模型路径，默认为当前目录下的Falconsai_text_summarization
        """
        if model_path is None:
            # 获取当前脚本所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, 'Falconsai_text_summarization')
        
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"文本摘要服务初始化，模型路径: {model_path}")
        logger.info(f"使用设备: {self.device}")
        
        # 加载模型
        self._load_model()
    
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
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            self.tokenizer = T5Tokenizer.from_pretrained(self.model_path)
            
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
    
    def summarize_medical_text(self, text: str, max_length: int = 50) -> str:
        """
        对医学文本进行摘要（专门针对医学内容优化）
        
        Args:
            text: 输入医学文本
            max_length: 最大摘要长度
            
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
            
            # 构建医学摘要的输入格式
            input_text = f"summarize medical text: {text}"
            
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
                    min_length=10,
                    num_beams=3,
                    early_stopping=True,
                    do_sample=False,
                    temperature=0.5,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # 解码输出
            summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            logger.info(f"医学文本摘要完成，原文长度: {len(text)}, 摘要长度: {len(summary)}")
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"医学文本摘要失败: {e}")
            # 如果摘要失败，返回截断的原文
            return text[:max_length] + "..." if len(text) > max_length else text
    
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
        
        # 测试文本
        test_text = """
        心肌梗死是一种严重的心血管疾病，通常由冠状动脉阻塞引起。
        患者可能出现胸痛、呼吸困难、恶心、出汗等症状。
        及时诊断和治疗对于患者的预后至关重要。
        治疗方法包括药物治疗、介入治疗和手术治疗。
        """
        
        print("测试文本摘要服务...")
        print(f"原文: {test_text.strip()}")
        
        # 普通摘要
        summary = service.summarize_text(test_text, max_length=50)
        print(f"普通摘要: {summary}")
        
        # 医学摘要
        medical_summary = service.summarize_medical_text(test_text, max_length=30)
        print(f"医学摘要: {medical_summary}")
        
        # 模型信息
        model_info = service.get_model_info()
        print(f"模型信息: {model_info}")
        
    except Exception as e:
        print(f"测试失败: {e}")
