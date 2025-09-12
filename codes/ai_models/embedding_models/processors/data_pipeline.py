"""
数据处理管道
统一处理各种数据格式和来源
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
import pandas as pd
import numpy as np
from PIL import Image
import cv2

from .text_preprocessing import OptimizedMedicalTextPreprocessor as TextPreprocessor
from .image_text_preprocessing import MedicalImageTextPreprocessor as ImageTextPreprocessor


class DataPipeline:
    """数据处理管道类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据处理管道
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化处理器
        raw_data_dir = self.config.get('raw_data_dir', 'data/raw')
        output_dir = self.config.get('output_dir', 'data/processed')
        
        self.text_processor = TextPreprocessor(raw_data_dir, output_dir)
        self.image_text_processor = ImageTextPreprocessor(raw_data_dir)
        
        # 数据统计
        self.stats = {
            'processed_texts': 0,
            'processed_images': 0,
            'errors': 0
        }
    
    def process_vqa_dataset(self, data_dir: str, output_dir: str) -> Dict[str, Any]:
        """
        处理VQA数据集
        
        Args:
            data_dir: 数据目录
            output_dir: 输出目录
            
        Returns:
            处理结果统计
        """
        self.logger.info(f"开始处理VQA数据集: {data_dir}")
        
        data_path = Path(data_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {
            'texts_processed': 0,
            'images_processed': 0,
            'errors': [],
            'output_files': []
        }
        
        try:
            # 处理文本数据
            text_files = list(data_path.glob("*.csv"))
            for text_file in text_files:
                try:
                    df = pd.read_csv(text_file)
                    processed_texts = self.text_processor.process_dataframe(df)
                    
                    output_file = output_path / f"processed_{text_file.name}"
                    processed_texts.to_csv(output_file, index=False)
                    results['texts_processed'] += len(processed_texts)
                    results['output_files'].append(str(output_file))
                    
                    self.logger.info(f"处理文本文件: {text_file.name} -> {output_file.name}")
                    
                except Exception as e:
                    error_msg = f"处理文本文件 {text_file.name} 失败: {e}"
                    self.logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            # 处理图像数据
            image_files = list(data_path.glob("*.npy"))
            for image_file in image_files:
                try:
                    images = np.load(image_file)
                    processed_images = self._process_image_array(images)
                    
                    output_file = output_path / f"processed_{image_file.name}"
                    np.save(output_file, processed_images)
                    results['images_processed'] += len(processed_images)
                    results['output_files'].append(str(output_file))
                    
                    self.logger.info(f"处理图像文件: {image_file.name} -> {output_file.name}")
                    
                except Exception as e:
                    error_msg = f"处理图像文件 {image_file.name} 失败: {e}"
                    self.logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            # 保存处理统计
            stats_file = output_path / "processing_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"VQA数据集处理完成，统计信息已保存到: {stats_file}")
            
        except Exception as e:
            self.logger.error(f"VQA数据集处理失败: {e}")
            raise
        
        return results
    
    def process_medical_reports(self, reports_file: str, output_dir: str) -> Dict[str, Any]:
        """
        处理医疗报告数据
        
        Args:
            reports_file: 报告文件路径
            output_dir: 输出目录
            
        Returns:
            处理结果统计
        """
        self.logger.info(f"开始处理医疗报告: {reports_file}")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {
            'reports_processed': 0,
            'texts_extracted': 0,
            'images_processed': 0,
            'errors': [],
            'output_files': []
        }
        
        try:
            # 读取报告数据
            df = pd.read_csv(reports_file)
            
            # 处理文本内容
            if 'text' in df.columns or 'content' in df.columns:
                text_column = 'text' if 'text' in df.columns else 'content'
                processed_texts = self.text_processor.process_series(df[text_column])
                
                text_output = output_path / "processed_texts.npy"
                np.save(text_output, processed_texts)
                results['texts_extracted'] = len(processed_texts)
                results['output_files'].append(str(text_output))
            
            # 处理图像路径
            if 'image_path' in df.columns:
                image_paths = df['image_path'].dropna().tolist()
                processed_images = self._process_image_paths(image_paths)
                
                image_output = output_path / "processed_images.npy"
                np.save(image_output, processed_images)
                results['images_processed'] = len(processed_images)
                results['output_files'].append(str(image_output))
            
            # 保存处理后的数据框
            processed_df = df.copy()
            if 'text' in processed_df.columns:
                processed_df['processed_text'] = processed_texts.tolist()
            
            output_file = output_path / "processed_reports.csv"
            processed_df.to_csv(output_file, index=False)
            results['reports_processed'] = len(processed_df)
            results['output_files'].append(str(output_file))
            
            # 保存统计信息
            stats_file = output_path / "processing_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"医疗报告处理完成，统计信息已保存到: {stats_file}")
            
        except Exception as e:
            self.logger.error(f"医疗报告处理失败: {e}")
            raise
        
        return results
    
    def _process_image_array(self, images: np.ndarray) -> np.ndarray:
        """
        处理图像数组
        
        Args:
            images: 图像数组
            
        Returns:
            处理后的图像数组
        """
        processed_images = []
        
        for image in images:
            try:
                # 确保图像是PIL Image格式
                if isinstance(image, np.ndarray):
                    if image.dtype != np.uint8:
                        image = (image * 255).astype(np.uint8)
                    image = Image.fromarray(image)
                
                # 调整大小
                image = image.resize((224, 224))
                
                # 转换为numpy数组
                processed_image = np.array(image)
                processed_images.append(processed_image)
                
            except Exception as e:
                self.logger.warning(f"处理图像失败: {e}")
                continue
        
        return np.array(processed_images)
    
    def _process_image_paths(self, image_paths: List[str]) -> np.ndarray:
        """
        处理图像路径列表
        
        Args:
            image_paths: 图像路径列表
            
        Returns:
            处理后的图像数组
        """
        processed_images = []
        
        for image_path in image_paths:
            try:
                # 加载图像
                image = Image.open(image_path)
                
                # 调整大小
                image = image.resize((224, 224))
                
                # 转换为numpy数组
                processed_image = np.array(image)
                processed_images.append(processed_image)
                
            except Exception as e:
                self.logger.warning(f"处理图像 {image_path} 失败: {e}")
                continue
        
        return np.array(processed_images)
    
    def validate_data(self, data_path: str) -> Dict[str, Any]:
        """
        验证数据质量
        
        Args:
            data_path: 数据路径
            
        Returns:
            验证结果
        """
        self.logger.info(f"开始验证数据: {data_path}")
        
        validation_result = {
            'valid': True,
            'issues': [],
            'statistics': {}
        }
        
        try:
            data_path = Path(data_path)
            
            # 检查文件存在性
            if not data_path.exists():
                validation_result['valid'] = False
                validation_result['issues'].append(f"数据路径不存在: {data_path}")
                return validation_result
            
            # 检查CSV文件
            csv_files = list(data_path.glob("*.csv"))
            for csv_file in csv_files:
                try:
                    df = pd.read_csv(csv_file)
                    validation_result['statistics'][csv_file.name] = {
                        'rows': len(df),
                        'columns': len(df.columns),
                        'null_values': df.isnull().sum().to_dict()
                    }
                except Exception as e:
                    validation_result['issues'].append(f"CSV文件 {csv_file.name} 读取失败: {e}")
            
            # 检查NPY文件
            npy_files = list(data_path.glob("*.npy"))
            for npy_file in npy_files:
                try:
                    data = np.load(npy_file)
                    validation_result['statistics'][npy_file.name] = {
                        'shape': data.shape,
                        'dtype': str(data.dtype),
                        'size': data.size
                    }
                except Exception as e:
                    validation_result['issues'].append(f"NPY文件 {npy_file.name} 读取失败: {e}")
            
            # 检查图像文件
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
            image_files = []
            for ext in image_extensions:
                image_files.extend(data_path.glob(f"*{ext}"))
            
            validation_result['statistics']['image_files'] = len(image_files)
            
            if validation_result['issues']:
                validation_result['valid'] = False
            
            self.logger.info(f"数据验证完成，发现 {len(validation_result['issues'])} 个问题")
            
        except Exception as e:
            self.logger.error(f"数据验证失败: {e}")
            validation_result['valid'] = False
            validation_result['issues'].append(f"验证过程失败: {e}")
        
        return validation_result
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        获取管道状态
        
        Returns:
            管道状态信息
        """
        return {
            'pipeline_name': 'DataPipeline',
            'version': '1.0.0',
            'statistics': self.stats,
            'processors': {
                'text_processor': self.text_processor is not None,
                'image_text_processor': self.image_text_processor is not None
            }
        }
