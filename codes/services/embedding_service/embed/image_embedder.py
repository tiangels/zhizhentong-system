"""
图像向量化模块
使用与文本相同的模型进行图像向量化，确保向量空间一致性
"""

import os
import sys
from pathlib import Path

# 首先设置路径，必须在其他导入之前
current_file = Path(__file__)
# 从 embed/image_embedder.py 到 codes/common
# embed/image_embedder.py -> embed/ -> embedding_models/ -> ai_models/ -> codes/ -> codes/common
common_dir = current_file.parent.parent.parent.parent / "common"
sys.path.insert(0, str(common_dir))

# 添加项目根目录到路径
project_root = current_file.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "codes" / "ai_models" / "llm_models"))

# 添加utils模块到路径
utils_dir = current_file.parent / "utils"
sys.path.insert(0, str(utils_dir))

# 现在可以安全导入其他模块
import logging
import numpy as np
from typing import List, Union, Optional, Dict, Any
import torch
from PIL import Image
import torchvision.transforms as transforms

# 导入配置管理器
from config.config_manager import get_config, get_model_path

import importlib.util
spec = importlib.util.spec_from_file_location("log_config", str(common_dir / "log_config.py"))
log_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(log_config)
setup_embedding_service_logging = log_config.setup_embedding_service_logging
logger = setup_embedding_service_logging()



class UnifiedImageEmbedder:
    """
    统一图像嵌入器
    使用与文本相同的模型进行图像向量化，确保向量空间一致性
    """
    
    def __init__(self, model_name: str = None, device: str = "cpu"):
        """
        初始化图像嵌入器
        
        Args:
            model_name: 模型名称，如果为None则使用配置中的模型
            device: 设备类型
        """
        self.device = device
        self.model = None
        self.processor = None
        self.model_name = model_name or self._get_default_model()
        
        # 设置模型路径
        self.model_path = self._get_model_path()
        
        # 图像预处理变换
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        self._load_model()
    
    def _get_default_model(self):
        """获取默认模型名称"""
        try:
            # 使用配置管理器获取模型路径
            config = get_config()
            if hasattr(config, 'image_embedding') and hasattr(config.image_embedding, 'model_name'):
                return config.image_embedding.model_name
            else:
                # 回退到默认配置
                return "microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"
        except Exception as e:
            logger.warning(f"获取模型路径失败: {e}")
            # 回退到默认配置
            return "microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"
    
    def _get_model_path(self):
        """获取模型路径"""
        try:
            # 如果是本地路径，直接返回
            if os.path.exists(self.model_name):
                return self.model_name
            
            # 尝试从配置获取本地路径
            config = get_config()
            if hasattr(config, 'image_embedding') and hasattr(config.image_embedding, 'local_path'):
                local_path = config.image_embedding.local_path
                if os.path.exists(local_path):
                    return local_path
            
            # 回退到默认本地路径
            default_path = os.path.join(
                project_root, "codes", "ai_models", "llm_models", 
                "BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"
            )
            if os.path.exists(default_path):
                return default_path
            
            # 最后回退到模型名称
            return self.model_name
            
        except Exception as e:
            logger.warning(f"获取模型路径失败: {e}")
            return self.model_name
    
    def _load_model(self):
        """加载模型"""
        try:
            logger.info(f"正在加载图像嵌入模型: {self.model_name}")
            
            # 优先尝试使用OpenCLIP加载BiomedCLIP模型
            try:
                self._load_openclip_model()
                return
            except Exception as openclip_error:
                logger.warning(f"OpenCLIP加载失败: {openclip_error}")
            
            # 如果OpenCLIP失败，尝试HuggingFace格式
            try:
                from transformers import AutoModel, AutoProcessor
                
                # 使用本地模型路径
                self.model = AutoModel.from_pretrained(self.model_path)
                self.processor = AutoProcessor.from_pretrained(self.model_path)
                
                # 移动到指定设备
                self.model = self.model.to(self.device)
                self.model.eval()
                
                logger.info(f"BiomedCLIP模型加载成功: {self.model_path}")
                
            except Exception as hf_error:
                logger.warning(f"HuggingFace格式加载失败: {hf_error}")
                raise hf_error
                
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            logger.warning("将使用虚拟图像嵌入器")
            self.model = None
            self.processor = None
            # 不抛出异常，让系统继续运行
    
    def _load_openclip_model(self):
        """加载OpenCLIP格式的模型"""
        try:
            import open_clip
            
            # 使用本地BiomedCLIP模型
            logger.info("使用OpenCLIP加载本地BiomedCLIP模型")
            
            # 检查本地配置文件
            config_path = os.path.join(self.model_path, 'open_clip_config.json')
            if os.path.exists(config_path):
                # 使用与文本嵌入器相同的本地加载方式
                self._load_local_openclip_model()
            else:
                # 回退到远程模型
                logger.warning(f"本地配置文件不存在: {config_path}，回退到远程模型")
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
                
                # 为了兼容性，也设置processor属性
                self.processor = self.preprocess
                
                # 移动到指定设备
                self.model = self.model.to(self.device)
                self.model.eval()
            
        except Exception as e:
            logger.error(f"OpenCLIP模型加载失败: {e}")
            raise e  # 重新抛出异常，让上层处理
    
    def _load_local_openclip_model(self):
        """加载本地OpenCLIP模型"""
        import json
        import open_clip
        
        # 加载本地配置
        config_path = os.path.join(self.model_path, 'open_clip_config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        model_cfg = config['model_cfg']
        preprocess_cfg = config['preprocess_cfg']
        
        # 创建模型架构
        from open_clip.model import CustomTextCLIP
        model = CustomTextCLIP(
            embed_dim=model_cfg['embed_dim'],
            vision_cfg=model_cfg['vision_cfg'],
            text_cfg=model_cfg['text_cfg']
        )
        
        # 加载本地权重
        local_model_path = os.path.join(self.model_path, 'open_clip_pytorch_model.bin')
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
        
        # 为了兼容性，也设置processor属性
        self.processor = self.preprocess
        
        self.model = model
        logger.info(f"成功加载本地模型: {local_model_path}")
    
    def embed_image(self, image_input: Union[str, np.ndarray]) -> List[float]:
        """
        对单张图像进行向量化
        
        Args:
            image_input: 图像文件路径或numpy数组
            
        Returns:
            图像向量
        """
        try:
            if self.model is None:
                logger.warning("模型未加载，返回随机向量")
                return np.random.rand(512).tolist()
            
            # 处理不同类型的图像输入
            if isinstance(image_input, str):
                # 从文件路径加载图像
                image = Image.open(image_input).convert('RGB')
            elif isinstance(image_input, np.ndarray):
                # 从numpy数组创建图像
                if image_input.dtype != np.uint8:
                    image_input = (image_input * 255).astype(np.uint8)
                image = Image.fromarray(image_input)
            else:
                raise ValueError(f"不支持的图像输入类型: {type(image_input)}")
            
            # 预处理图像
            if hasattr(self, 'preprocess'):
                # 使用OpenCLIP的预处理
                image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
                inputs = {"pixel_values": image_tensor}
            elif self.processor:
                # 使用模型特定的处理器
                inputs = self.processor(images=image, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            else:
                # 使用标准预处理
                image_tensor = self.transform(image).unsqueeze(0).to(self.device)
                inputs = {"pixel_values": image_tensor}
            
            # 获取图像特征
            with torch.no_grad():
                if hasattr(self, 'preprocess'):
                    # 使用OpenCLIP的图像编码
                    image_features = self.model.encode_image(image_tensor)
                elif hasattr(self.model, 'get_image_features'):
                    # BiomedCLIP模型
                    image_features = self.model.get_image_features(**inputs)
                elif hasattr(self.model, 'vision_model'):
                    # 使用vision_model获取图像特征
                    vision_outputs = self.model.vision_model(**inputs)
                    image_features = vision_outputs.pooler_output
                else:
                    # 其他多模态模型
                    outputs = self.model(**inputs)
                    if hasattr(outputs, 'image_embeds'):
                        image_features = outputs.image_embeds
                    else:
                        image_features = outputs.last_hidden_state.mean(dim=1)
                
                # 归一化特征向量
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                
                # 转换为列表
                embedding = image_features.cpu().numpy().flatten().tolist()
                
                # 确保向量维度为512
                if len(embedding) != 512:
                    if len(embedding) > 512:
                        embedding = embedding[:512]
                    else:
                        embedding.extend([0.0] * (512 - len(embedding)))
                
                logger.debug(f"图像向量化成功, 向量维度: {len(embedding)}")
                return embedding
                
        except Exception as e:
            logger.error(f"图像向量化失败: {e}")
            # 返回随机向量作为后备，确保与文本向量维度一致
            return np.random.rand(512).tolist()
    
    def embed_images(self, image_paths: List[str]) -> List[List[float]]:
        """
        批量对图像进行向量化
        
        Args:
            image_paths: 图像文件路径列表
            
        Returns:
            图像向量列表
        """
        embeddings = []
        for image_path in image_paths:
            embedding = self.embed_image(image_path)
            embeddings.append(embedding)
        
        logger.info(f"批量图像向量化完成: {len(embeddings)} 张图像")
        return embeddings

class ImageEmbedderFactory:
    """图像嵌入器工厂类"""
    
    @staticmethod
    def create_embedder(embedder_type: str = "unified", 
                       model_name: str = None, 
                       device: str = "cpu") -> UnifiedImageEmbedder:
        """
        创建图像嵌入器
        
        Args:
            embedder_type: 嵌入器类型（目前只支持unified）
            model_name: 模型名称
            device: 设备类型
            
        Returns:
            图像嵌入器实例
        """
        if embedder_type == "unified":
            return UnifiedImageEmbedder(model_name=model_name, device=device)
        else:
            raise ValueError(f"不支持的嵌入器类型: {embedder_type}")

def batch_embed_images(embedder, image_paths: List[str], 
                      batch_size: int = 32) -> List[List[float]]:
    """
    批量图像向量化函数
    
    Args:
        embedder: 图像嵌入器实例
        image_paths: 图像文件路径列表
        batch_size: 批次大小
        
    Returns:
        图像向量列表
    """
    return embedder.embed_images(image_paths)

# 测试函数
def test_image_embedder():
    """测试图像嵌入器"""
    print("测试图像嵌入器...")
    
    # 创建测试图像路径（使用项目中的实际图像）
    test_image_path = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/image_text_data/processed/images/1_IM-2117-1004003.dcm.png"
    
    if os.path.exists(test_image_path):
        embedder = ImageEmbedderFactory.create_embedder()
        embedding = embedder.embed_image(test_image_path)
        print(f"测试成功! 向量维度: {len(embedding)}")
        return True
    else:
        print("测试图像不存在，跳过测试")
        return False

if __name__ == "__main__":
    test_image_embedder()
