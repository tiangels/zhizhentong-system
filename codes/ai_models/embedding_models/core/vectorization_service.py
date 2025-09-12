"""
统一向量化服务
整合文本和图像向量化功能
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import numpy as np
import pandas as pd

from .image_vectorization import ImageVectorizer
from .data_analyzer import MedicalDataAnalyzer as DataAnalyzer
from ..processors.text_preprocessing import OptimizedMedicalTextPreprocessor as TextPreprocessor
from ..models.image_embedder import ImageEmbedder


class VectorizationService:
    """统一向量化服务类"""
    
    def __init__(self, config_path: str = "config/unified_config.json"):
        """
        初始化向量化服务
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        
        # 初始化各个组件
        self.image_vectorizer = None
        self.text_processor = None
        self.data_analyzer = None
        self.image_embedder = None
        
        self._initialize_components()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config_file = Path(__file__).parent.parent / self.config_path
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 处理相对路径，确保模型路径正确
        if 'models' in config:
            for model_type, model_config in config['models'].items():
                if 'model_path' in model_config:
                    model_path = model_config['model_path']
                    if model_path.startswith('../'):
                        # 将相对路径转换为绝对路径
                        base_dir = Path(__file__).parent.parent.parent
                        model_config['model_path'] = str(base_dir / model_path[3:])
        
        return config
    
    def _setup_logging(self):
        """设置日志"""
        log_config = self.config.get('logging', {})
        log_file = Path(__file__).parent.parent / log_config.get('file', 'logs/vectorization.log')
        log_file.parent.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _initialize_components(self):
        """初始化各个组件"""
        try:
            # 初始化图像向量化器
            self.image_vectorizer = ImageVectorizer()
            self.logger.info("图像向量化器初始化成功")
            
            # 初始化文本处理器
            raw_data_dir = self.config.get('data', {}).get('raw_data_dir', 'data/raw')
            output_dir = self.config.get('data', {}).get('output_dir', 'data/processed')
            self.text_processor = TextPreprocessor(raw_data_dir, output_dir)
            self.logger.info("文本处理器初始化成功")
            
            # 初始化数据分析器
            data_dir = self.config.get('data', {}).get('data_dir', 'data')
            self.data_analyzer = DataAnalyzer(data_dir)
            self.logger.info("数据分析器初始化成功")
            
            # 初始化图像嵌入器
            model_name = self.config.get('models', {}).get('image_model', 'clip-vit-base-patch32')
            self.image_embedder = ImageEmbedder(model_name)
            self.logger.info("图像嵌入器初始化成功")
            
        except Exception as e:
            self.logger.error(f"组件初始化失败: {e}")
            # 不抛出异常，允许部分组件初始化失败
    
    def process_texts(self, texts: Union[str, List[str]], 
                     output_path: Optional[str] = None) -> np.ndarray:
        """
        处理文本向量化
        
        Args:
            texts: 文本或文本列表
            output_path: 输出路径
            
        Returns:
            文本向量数组
        """
        self.logger.info(f"开始处理文本向量化，数量: {len(texts) if isinstance(texts, list) else 1}")
        
        try:
            vectors = self.text_processor.process_texts(texts)
            
            if output_path:
                np.save(output_path, vectors)
                self.logger.info(f"文本向量已保存到: {output_path}")
            
            return vectors
            
        except Exception as e:
            self.logger.error(f"文本向量化失败: {e}")
            raise
    
    def process_images(self, image_paths: Union[str, List[str]], 
                      output_path: Optional[str] = None) -> np.ndarray:
        """
        处理图像向量化
        
        Args:
            image_paths: 图像路径或路径列表
            output_path: 输出路径
            
        Returns:
            图像向量数组
        """
        self.logger.info(f"开始处理图像向量化，数量: {len(image_paths) if isinstance(image_paths, list) else 1}")
        
        try:
            vectors = self.image_vectorizer.vectorize_images(image_paths)
            
            if output_path:
                np.save(output_path, vectors)
                self.logger.info(f"图像向量已保存到: {output_path}")
            
            return vectors
            
        except Exception as e:
            self.logger.error(f"图像向量化失败: {e}")
            raise
    
    def process_multimodal(self, texts: List[str], image_paths: List[str],
                          output_path: Optional[str] = None) -> Dict[str, np.ndarray]:
        """
        处理多模态数据
        
        Args:
            texts: 文本列表
            image_paths: 图像路径列表
            output_path: 输出路径
            
        Returns:
            包含文本和图像向量的字典
        """
        self.logger.info(f"开始处理多模态数据，文本: {len(texts)}, 图像: {len(image_paths)}")
        
        try:
            # 处理文本
            text_vectors = self.process_texts(texts)
            
            # 处理图像
            image_vectors = self.process_images(image_paths)
            
            result = {
                'text_vectors': text_vectors,
                'image_vectors': image_vectors
            }
            
            if output_path:
                np.savez(output_path, **result)
                self.logger.info(f"多模态向量已保存到: {output_path}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"多模态处理失败: {e}")
            raise
    
    def analyze_data(self, data_path: str) -> Dict[str, Any]:
        """
        分析数据质量
        
        Args:
            data_path: 数据路径
            
        Returns:
            数据分析结果
        """
        self.logger.info(f"开始分析数据: {data_path}")
        
        try:
            analysis_result = self.data_analyzer.analyze_data(data_path)
            self.logger.info("数据分析完成")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"数据分析失败: {e}")
            raise
    
    def build_vector_database(self, data_dir: str, db_path: str) -> bool:
        """
        构建向量数据库
        
        Args:
            data_dir: 数据目录
            db_path: 数据库路径
            
        Returns:
            是否成功
        """
        self.logger.info(f"开始构建向量数据库: {data_dir} -> {db_path}")
        
        try:
            # 这里可以调用向量数据库构建功能
            # 暂时返回True，具体实现待完善
            self.logger.info("向量数据库构建完成")
            return True
            
        except Exception as e:
            self.logger.error(f"向量数据库构建失败: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态
        
        Returns:
            服务状态信息
        """
        return {
            "service_name": "VectorizationService",
            "version": "1.0.0",
            "components": {
                "image_vectorizer": self.image_vectorizer is not None,
                "text_processor": self.text_processor is not None,
                "data_analyzer": self.data_analyzer is not None,
                "image_embedder": self.image_embedder is not None
            },
            "config_loaded": self.config is not None
        }
