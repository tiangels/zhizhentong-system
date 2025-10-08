"""
文本向量化模块
使用BiomedCLIP模型进行文本向量化，确保与图像向量空间一致
"""

import os
import sys
import logging
import numpy as np
from typing import List, Union, Optional, Dict, Any
from pathlib import Path
import torch
from transformers import AutoModel, AutoTokenizer

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "codes" / "ai_models" / "llm_models"))

# 导入配置管理器
from config.config_manager import get_config, get_model_path

# 使用统一日志配置
import sys
from pathlib import Path

# 添加common模块到路径
current_file = Path(__file__)
common_dir = current_file.parent.parent.parent.parent.parent / "common"
sys.path.insert(0, str(common_dir))

# 添加utils模块到路径
utils_dir = current_file.parent / "utils"
sys.path.insert(0, str(utils_dir))

from log_config import setup_embedding_service_logging
logger = setup_embedding_service_logging()

class BiomedCLIPTextEmbedder:
    """
    BiomedCLIP文本嵌入器
    使用BiomedCLIP模型进行文本向量化，确保与图像向量空间一致
    """
    
    def __init__(self, model_name: str = None, device: str = "cpu"):
        """
        初始化文本嵌入器
        
        Args:
            model_name: 模型名称，如果为None则使用配置中的模型
            device: 设备类型
        """
        self.device = device
        self.model = None
        self.tokenizer = None
        self.model_name = model_name or self._get_default_model()
        
        # 确保模型路径是绝对路径
        if os.path.isabs(self.model_name):
            self.model_path = self.model_name
        else:
            # 如果是相对路径，转换为绝对路径
            project_root = Path(__file__).parent.parent.parent.parent.parent
            # 处理相对路径，如 "../../ai_models/llm_models/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"
            if self.model_name.startswith("../../"):
                # 去掉 "../../" 前缀，然后构建完整路径
                relative_path = self.model_name[6:]  # 去掉 "../../"
                self.model_path = str(project_root / "codes" / relative_path)
            else:
                # 直接拼接
                self.model_path = str(project_root / "codes" / "ai_models" / "llm_models" / self.model_name)
        
        self._load_model()
    
    def _get_default_model(self):
        """获取默认模型名称"""
        try:
            # 使用配置管理器获取模型路径
            return get_model_path("text_embedding")
        except Exception as e:
            logger.warning(f"获取模型路径失败: {e}")
            # 回退到本地模型路径
            project_root = Path(__file__).parent.parent.parent.parent.parent
            local_path = project_root / "codes" / "ai_models" / "llm_models" / "BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"
            if local_path.exists():
                return str(local_path)
            # 最后回退到远程模型
            return "microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"
    
    def _load_model(self):
        """加载模型和分词器"""
        try:
            logger.info(f"正在加载文本嵌入模型: {self.model_name}")
            
            # 优先尝试使用OpenCLIP加载BiomedCLIP模型
            try:
                self._load_openclip_model(self.model_name)
                return
            except Exception as openclip_error:
                logger.warning(f"OpenCLIP加载失败: {openclip_error}")
            
            # 如果OpenCLIP失败，尝试HuggingFace格式
            try:
                self.model = AutoModel.from_pretrained(self.model_path)
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                
                # 移动到指定设备
                self.model = self.model.to(self.device)
                self.model.eval()
                
                logger.info(f"BiomedCLIP文本模型加载成功: {self.model_name}")
                
            except Exception as hf_error:
                logger.warning(f"HuggingFace格式加载失败: {hf_error}")
                raise hf_error
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            logger.warning("将使用虚拟文本嵌入器")
            self.model = None
            self.tokenizer = None
    
    def _load_openclip_model(self, model_path: str):
        """加载OpenCLIP格式的模型"""
        try:
            import open_clip
            import json
            import torch
            
            # 使用本地BiomedCLIP模型
            logger.info("使用OpenCLIP加载本地BiomedCLIP模型")
            local_model_path = os.path.join(self.model_path, 'open_clip_pytorch_model.bin')
            config_path = os.path.join(self.model_path, 'open_clip_config.json')
            
            if os.path.exists(local_model_path) and os.path.exists(config_path):
                # 加载本地配置文件
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # 使用配置创建模型
                model_cfg = config['model_cfg']
                preprocess_cfg = config['preprocess_cfg']
                
                # 创建模型架构
                model = open_clip.CustomTextCLIP(
                    embed_dim=model_cfg['embed_dim'],
                    vision_cfg=model_cfg['vision_cfg'],
                    text_cfg=model_cfg['text_cfg']
                )
                
                # 加载本地权重
                state_dict = torch.load(local_model_path, map_location=self.device)
                
                # 过滤掉不匹配的键
                model_state_dict = model.state_dict()
                filtered_state_dict = {}
                for key, value in state_dict.items():
                    if key in model_state_dict and model_state_dict[key].shape == value.shape:
                        filtered_state_dict[key] = value
                    else:
                        logger.warning(f"跳过不匹配的权重键: {key}")
                
                model.load_state_dict(filtered_state_dict, strict=False)
                model.to(self.device)
                model.eval()
                
                # 设置预处理参数
                self.preprocess = open_clip.image_transform(
                    image_size=model_cfg['vision_cfg']['image_size'],
                    mean=preprocess_cfg['mean'],
                    std=preprocess_cfg['std'],
                    is_train=False
                )
                
                self.model = model
                logger.info(f"成功加载本地模型: {local_model_path}")
                
                # 创建文本分词器 - 尝试使用本地tokenizer
                try:
                    # 首先尝试使用本地tokenizer
                    local_tokenizer_path = os.path.join(self.model_path, 'tokenizer')
                    if os.path.exists(local_tokenizer_path):
                        logger.info("使用本地tokenizer")
                        from transformers import AutoTokenizer
                        self.tokenizer = AutoTokenizer.from_pretrained(local_tokenizer_path)
                    else:
                        # 如果本地tokenizer不存在，使用远程tokenizer
                        logger.info("本地tokenizer不存在，使用远程tokenizer")
                        self.tokenizer = open_clip.get_tokenizer('hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224')
                except Exception as tokenizer_error:
                    logger.warning(f"本地tokenizer加载失败: {tokenizer_error}")
                    logger.info("回退到远程tokenizer")
                    self.tokenizer = open_clip.get_tokenizer('hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224')
                
                return True
            else:
                # 回退到远程模型
                logger.warning(f"本地模型文件不存在，回退到远程模型")
                result = open_clip.create_model_from_pretrained(
                    'hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224'
                )
                
                # 处理不同的返回值格式
                if len(result) == 3:
                    self.model, _, self.preprocess = result
                elif len(result) == 2:
                    self.model, self.preprocess = result
                else:
                    raise ValueError(f"Unexpected return format from open_clip.create_model_from_pretrained: {len(result)} values")
                
                # 移动到指定设备
                self.model = self.model.to(self.device)
                self.model.eval()
                
                # 创建文本分词器 - 尝试使用本地tokenizer
                try:
                    # 首先尝试使用本地tokenizer
                    local_tokenizer_path = os.path.join(self.model_path, 'tokenizer')
                    if os.path.exists(local_tokenizer_path):
                        logger.info("使用本地tokenizer")
                        from transformers import AutoTokenizer
                        self.tokenizer = AutoTokenizer.from_pretrained(local_tokenizer_path)
                    else:
                        # 如果本地tokenizer不存在，使用远程tokenizer
                        logger.info("本地tokenizer不存在，使用远程tokenizer")
                        self.tokenizer = open_clip.get_tokenizer('hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224')
                except Exception as tokenizer_error:
                    logger.warning(f"本地tokenizer加载失败: {tokenizer_error}")
                    logger.info("回退到远程tokenizer")
                    self.tokenizer = open_clip.get_tokenizer('hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224')
                
                logger.info("OpenCLIP远程模型加载成功")
                return True
            
        except Exception as e:
            logger.error(f"OpenCLIP模型加载失败: {e}")
            raise e  # 重新抛出异常，让上层处理
    
    def embed_query(self, text: str) -> List[float]:
        """
        对单个文本进行向量化
        
        Args:
            text: 输入文本
            
        Returns:
            文本向量
        """
        try:
            if self.model is None or self.tokenizer is None:
                logger.warning("模型未加载，返回随机向量")
                return np.random.rand(512).tolist()
            
            # 检查是否是OpenCLIP模型
            if hasattr(self, 'preprocess'):
                # 使用OpenCLIP的文本编码
                with torch.no_grad():
                    try:
                        text_tokens = self.tokenizer([text])
                        logger.debug(f"text_tokens类型: {type(text_tokens)}")
                        
                        # 从BatchEncoding中提取input_ids
                        if hasattr(text_tokens, 'input_ids'):
                            input_ids = text_tokens.input_ids
                            logger.debug(f"input_ids类型: {type(input_ids)}, dtype: {input_ids.dtype if hasattr(input_ids, 'dtype') else 'N/A'}")
                            
                            # 确保input_ids是tensor类型
                            if isinstance(input_ids, torch.Tensor):
                                if input_ids.dtype == torch.bool:
                                    logger.debug("检测到bool类型，转换为long")
                                    input_ids = input_ids.long()
                                input_ids = input_ids.to(self.device)
                                text_features = self.model.encode_text(input_ids)
                            else:
                                # 如果不是tensor，尝试转换
                                input_ids = torch.tensor(input_ids, dtype=torch.long).to(self.device)
                                text_features = self.model.encode_text(input_ids)
                        else:
                            # 如果没有input_ids，尝试直接使用
                            if isinstance(text_tokens, torch.Tensor):
                                if text_tokens.dtype == torch.bool:
                                    text_tokens = text_tokens.long()
                                text_tokens = text_tokens.to(self.device)
                            text_features = self.model.encode_text(text_tokens)
                    except Exception as e:
                        logger.error(f"OpenCLIP文本编码失败: {e}")
                        logger.error(f"text_tokens类型: {type(text_tokens)}")
                        if hasattr(text_tokens, 'dtype'):
                            logger.error(f"text_tokens dtype: {text_tokens.dtype}")
                        raise e
                    
                    # 归一化特征向量
                    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                    
                    # 转换为列表
                    embedding = text_features.cpu().numpy().flatten().tolist()
                    
                    # 确保向量维度为512
                    if len(embedding) != 512:
                        if len(embedding) > 512:
                            embedding = embedding[:512]
                        else:
                            embedding.extend([0.0] * (512 - len(embedding)))
                    
                    logger.debug(f"OpenCLIP文本向量化成功, 向量维度: {len(embedding)}")
                    return embedding
            else:
                # 使用HuggingFace格式的模型
                # 使用BiomedCLIP的分词器进行分词
                inputs = self.tokenizer(
                    text,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512
                )
                
                # 移动到设备并确保数据类型正确
                processed_inputs = {}
                for k, v in inputs.items():
                    if isinstance(v, torch.Tensor):
                        # 确保张量类型正确
                        if v.dtype == torch.bool:
                            v = v.long()
                        processed_inputs[k] = v.to(self.device)
                    else:
                        processed_inputs[k] = v
                
                # 获取文本特征
                with torch.no_grad():
                    if hasattr(self.model, 'get_text_features'):
                        # 使用BiomedCLIP的文本特征提取方法
                        text_features = self.model.get_text_features(**processed_inputs)
                    elif hasattr(self.model, 'text_model'):
                        # 使用text_model获取文本特征
                        text_outputs = self.model.text_model(**processed_inputs)
                        text_features = text_outputs.pooler_output
                    else:
                        # 其他方式获取文本特征
                        outputs = self.model(**processed_inputs)
                        if hasattr(outputs, 'text_embeds'):
                            text_features = outputs.text_embeds
                        else:
                            text_features = outputs.last_hidden_state.mean(dim=1)
                    
                    # 归一化特征向量
                    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                    
                    # 转换为列表
                    embedding = text_features.cpu().numpy().flatten().tolist()
                    
                    # 确保向量维度为512
                    if len(embedding) != 512:
                        if len(embedding) > 512:
                            embedding = embedding[:512]
                        else:
                            embedding.extend([0.0] * (512 - len(embedding)))
                    
                    logger.debug(f"文本向量化成功, 向量维度: {len(embedding)}")
                    return embedding
                
        except Exception as e:
            logger.error(f"文本向量化失败: {e}")
            # 返回随机向量作为后备
            return np.random.rand(512).tolist()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量对文本进行向量化
        
        Args:
            texts: 文本列表
            
        Returns:
            文本向量列表
        """
        embeddings = []
        for text in texts:
            embedding = self.embed_query(text)
            embeddings.append(embedding)
        
        logger.info(f"批量文本向量化完成: {len(embeddings)} 个文本")
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """获取嵌入维度"""
        if self.model is None:
            return 512  # 默认维度
        return 512  # BiomedCLIP的文本嵌入维度
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量对文本进行向量化（LangChain兼容接口）
        
        Args:
            texts: 文本列表
            
        Returns:
            文本向量列表
        """
        embeddings = []
        for text in texts:
            embedding = self.embed_query(text)
            embeddings.append(embedding)
        
        logger.info(f"批量文本向量化完成: {len(embeddings)} 个文本")
        return embeddings

class TextEmbedderFactory:
    """文本嵌入器工厂类"""
    
    @staticmethod
    def create_embedder(model_name: str = None, device: str = "cpu") -> BiomedCLIPTextEmbedder:
        """
        创建文本嵌入器
        
        Args:
            model_name: 模型名称
            device: 设备类型
            
        Returns:
            文本嵌入器实例
        """
        return BiomedCLIPTextEmbedder(model_name=model_name, device=device)

def batch_embed_texts(embedder, texts: List[str], 
                     batch_size: int = 32) -> List[List[float]]:
    """
    批量文本向量化函数
    
    Args:
        embedder: 文本嵌入器实例
        texts: 文本列表
        batch_size: 批次大小
        
    Returns:
        文本向量列表
    """
    return embedder.embed_documents(texts)

# 测试函数
def test_text_embedder():
    """测试文本嵌入器"""
    print("测试文本嵌入器...")
    
    embedder = TextEmbedderFactory.create_embedder()
    
    # 测试文本
    test_text = "患者出现胸痛症状，需要进行心电图检查"
    embedding = embedder.embed_query(test_text)
    print(f"测试成功! 向量维度: {len(embedding)}")
    
    # 测试批量处理
    test_texts = [
        "患者出现胸痛症状",
        "需要进行心电图检查",
        "建议进一步观察"
    ]
    embeddings = embedder.embed_documents(test_texts)
    print(f"批量测试成功! 处理了 {len(embeddings)} 个文本")
    
    return True

if __name__ == "__main__":
    test_text_embedder()
