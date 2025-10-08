#!/usr/bin/env python3
"""
医疗文本数据预处理模块
专门处理文本文件（PDF、TXT、CSV、JSON、Excel等）

功能:
1. 支持多种文本格式 (PDF、TXT、CSV、JSON、Excel)
2. 医疗文本数据清洗和预处理
3. 批量处理文本文件
4. 生成结构化输出

作者: AI Assistant
创建时间: 2025-09-17
版本: 1.0.0
"""

import os
import re
import pandas as pd
import jieba
import json
from tqdm import tqdm
import numpy as np
import PyPDF2
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime

# 设置中文字体显示
import matplotlib.pyplot as plt

# 导入字体配置模块
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config'))
    from font_config import configure_chinese_font
    # 配置中文字体
    configure_chinese_font()
except ImportError:
    # 如果字体配置不可用，使用基本配置
    plt.rcParams["font.family"] = ["Heiti TC"]

# PDF处理
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("警告: pdfplumber未安装，将跳过PDF文件处理")


# Excel处理
try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    print("警告: openpyxl未安装，将跳过Excel文件处理")

try:
    from .base_processor import BaseDataProcessor
except ImportError:
    from base_processor import BaseDataProcessor

# 数据预处理只负责数据清洗和格式转换，不包含文档切分功能

class OptimizedMedicalTextPreprocessor(BaseDataProcessor):
    """医疗文本数据预处理器
    功能：
    1. 数据清洗和预处理
    2. 格式转换（PDF、TXT、CSV、JSON、Excel等）
    3. 生成供文档切分使用的JSON格式数据
    
    注意：不包含文档切分和分词功能，只负责数据预处理
    """
    
    def __init__(self, raw_data_dir: str, output_dir: str):
        """
        初始化医疗文本预处理器
        
        Args:
            raw_data_dir: 原始数据目录
            output_dir: 输出目录
        """
        super().__init__(raw_data_dir, output_dir)
        
        # 支持的文件格式
        self.supported_formats = {
            '.txt': self._process_txt_file,
            '.csv': self._process_csv_file,
            '.json': self._process_json_file,
            '.pdf': self._process_pdf_file,
            '.xlsx': self._process_excel_file,
            '.xls': self._process_excel_file,
        }
        
        # 处理统计
        self.processed_documents = []
        self.failed_files = []
        
        self.logger.info(f"📄 医疗文本预处理器初始化完成")
        self.logger.info(f"支持的文件格式: {list(self.supported_formats.keys())}")
    
    def _detect_data_type_from_filename(self, filename: str) -> str:
        """根据文件名判断数据类型"""
        filename_lower = filename.lower()
        
        # 医疗对话数据
        if any(keyword in filename_lower for keyword in ['dialogue', '对话', 'chat', 'conversation']):
            return 'dialogue'
        
        # VQA数据
        elif any(keyword in filename_lower for keyword in ['vqa', 'question', 'answer', '问答']):
            return 'vqa'
        
        # 医疗文档
        elif any(keyword in filename_lower for keyword in ['medical', '医疗', 'health', 'healthcare', 'diagnosis', '诊断']):
            return 'medical_document'
        
        # 默认为通用文档
        else:
            return 'general_document'
    
    def _process_txt_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """处理TXT文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
            
            # 按段落分割
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            
            documents = []
            for i, paragraph in enumerate(paragraphs):
                if len(paragraph) > 10:  # 过滤太短的段落
                    # 1. 调用基类的文本清洗功能，保留医学符号
                    cleaned_result = self.clean_text(paragraph)
                    
                    # 2. 调用数据脱敏功能
                    desensitized_result = self.desensitize_text(cleaned_result['cleaned_text'])
                    
                    # 3. 创建结构化输出
                    metadata = {
                        'file_name': file_path.name,
                        'file_path': str(file_path),
                        'data_type': self._detect_data_type_from_filename(file_path.name),
                        'paragraph_index': i,
                        'quality_score': cleaned_result['quality_score'],
                        'medical_terms_count': cleaned_result['medical_terms_count'],
                        'sensitive_info': desensitized_result['sensitive_info'],
                        'has_sensitive_data': desensitized_result['has_sensitive_data']
                    }
                    
                    structured_doc = self.create_structured_output(
                        desensitized_result['desensitized_text'], 
                        metadata
                    )
                    
                    documents.append(structured_doc)
            
            self.logger.info(f"✅ TXT文件处理完成: {file_path.name}, 段落数: {len(documents)}")
            return documents
            
        except Exception as e:
            self.logger.error(f"处理TXT文件失败 {file_path}: {e}")
            return []
    
    def _process_csv_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """处理CSV文件"""
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            
            documents = []
            for index, row in df.iterrows():
                # 将行数据转换为文本
                text_parts = []
                for col, value in row.items():
                    if pd.notna(value) and str(value).strip():
                        text_parts.append(f"{col}: {str(value).strip()}")
                
                if text_parts:
                    text_content = " | ".join(text_parts)
                    # 1. 调用基类的文本清洗功能，保留医学符号
                    cleaned_result = self.clean_text(text_content)
                    
                    # 2. 调用数据脱敏功能
                    desensitized_result = self.desensitize_text(cleaned_result['cleaned_text'])
                    
                    # 3. 创建结构化输出
                    metadata = {
                        'file_name': file_path.name,
                        'file_path': str(file_path),
                        'data_type': self._detect_data_type_from_filename(file_path.name),
                        'row_index': index,
                        'quality_score': cleaned_result['quality_score'],
                        'medical_terms_count': cleaned_result['medical_terms_count'],
                        'sensitive_info': desensitized_result['sensitive_info'],
                        'has_sensitive_data': desensitized_result['has_sensitive_data']
                    }
                    
                    structured_doc = self.create_structured_output(
                        desensitized_result['desensitized_text'], 
                        metadata
                    )
                    
                    documents.append(structured_doc)
            
            self.logger.info(f"✅ CSV文件处理完成: {file_path.name}, 行数: {len(documents)}")
            return documents
            
        except Exception as e:
            self.logger.error(f"处理CSV文件失败 {file_path}: {e}")
            return []
    
    def _process_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """处理JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            documents = []
            
            def extract_text_recursive(obj, path=""):
                """递归提取文本内容"""
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        extract_text_recursive(value, current_path)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        current_path = f"{path}[{i}]" if path else f"[{i}]"
                        extract_text_recursive(item, current_path)
                elif isinstance(obj, str) and obj.strip():
                    # 1. 调用基类的文本清洗功能，保留医学符号
                    cleaned_result = self.clean_text(obj.strip())
                    
                    # 2. 调用数据脱敏功能
                    desensitized_result = self.desensitize_text(cleaned_result['cleaned_text'])
                    
                    # 3. 创建结构化输出
                    metadata = {
                        'file_name': file_path.name,
                        'file_path': str(file_path),
                        'data_type': self._detect_data_type_from_filename(file_path.name),
                        'json_path': path,
                        'quality_score': cleaned_result['quality_score'],
                        'medical_terms_count': cleaned_result['medical_terms_count'],
                        'sensitive_info': desensitized_result['sensitive_info'],
                        'has_sensitive_data': desensitized_result['has_sensitive_data']
                    }
                    
                    structured_doc = self.create_structured_output(
                        desensitized_result['desensitized_text'], 
                        metadata
                    )
                    
                    documents.append(structured_doc)
            
            extract_text_recursive(data)
            
            self.logger.info(f"✅ JSON文件处理完成: {file_path.name}, 文本项数: {len(documents)}")
            return documents
            
        except Exception as e:
            self.logger.error(f"处理JSON文件失败 {file_path}: {e}")
            return []
    
    def _process_pdf_file(self, file_path) -> List[Dict[str, Any]]:
        """处理PDF文件"""
        if not PDF_AVAILABLE:
            self.logger.warning(f"PDF处理库未安装，跳过文件: {file_path}")
            return []
        
        # 确保file_path是Path对象
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        try:
            documents = []
            
            # 使用pdfplumber提取文本
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        # 1. 调用基类的文本清洗功能，保留医学符号
                        cleaned_result = self.clean_text(text.strip())
                        
                        # 2. 调用数据脱敏功能
                        desensitized_result = self.desensitize_text(cleaned_result['cleaned_text'])
                        
                        # 3. 创建结构化输出
                        metadata = {
                            'file_name': file_path.name,
                            'file_path': str(file_path),
                            'data_type': self._detect_data_type_from_filename(file_path.name),
                            'page_number': page_num + 1,
                            'quality_score': cleaned_result['quality_score'],
                            'medical_terms_count': cleaned_result['medical_terms_count'],
                            'sensitive_info': desensitized_result['sensitive_info'],
                            'has_sensitive_data': desensitized_result['has_sensitive_data']
                        }
                        
                        structured_doc = self.create_structured_output(
                            desensitized_result['desensitized_text'], 
                            metadata
                        )
                        
                        documents.append(structured_doc)
            
            self.logger.info(f"✅ PDF文件处理完成: {file_path.name}, 页数: {len(documents)}")
            return documents
            
        except Exception as e:
            self.logger.error(f"处理PDF文件失败 {file_path}: {e}")
            return []
    
    
    def _process_excel_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """处理Excel文件"""
        if not EXCEL_AVAILABLE:
            self.logger.warning(f"Excel处理库未安装，跳过文件: {file_path}")
            return []
        
        try:
            documents = []
            
            # 读取Excel文件
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                for index, row in df.iterrows():
                    # 将行数据转换为文本
                    text_parts = []
                    for col, value in row.items():
                        if pd.notna(value) and str(value).strip():
                            text_parts.append(f"{col}: {str(value).strip()}")
                    
                    if text_parts:
                        text_content = " | ".join(text_parts)
                        # 1. 调用基类的文本清洗功能，保留医学符号
                        cleaned_result = self.clean_text(text_content)
                        
                        # 2. 调用数据脱敏功能
                        desensitized_result = self.desensitize_text(cleaned_result['cleaned_text'])
                        
                        # 3. 创建结构化输出
                        metadata = {
                            'file_name': file_path.name,
                            'file_path': str(file_path),
                            'data_type': self._detect_data_type_from_filename(file_path.name),
                            'sheet_name': sheet_name,
                            'row_index': index,
                            'quality_score': cleaned_result['quality_score'],
                            'medical_terms_count': cleaned_result['medical_terms_count'],
                            'sensitive_info': desensitized_result['sensitive_info'],
                            'has_sensitive_data': desensitized_result['has_sensitive_data']
                        }
                        
                        structured_doc = self.create_structured_output(
                            desensitized_result['desensitized_text'], 
                            metadata
                        )
                        
                        documents.append(structured_doc)
            
            self.logger.info(f"✅ Excel文件处理完成: {file_path.name}, 工作表数: {len(excel_file.sheet_names)}")
            return documents
            
        except Exception as e:
            self.logger.error(f"处理Excel文件失败 {file_path}: {e}")
            return []
    
    def scan_text_files(self) -> List[Path]:
        """扫描文本文件"""
        text_files = []
        
        if self.raw_data_dir.exists():
            for file_path in self.raw_data_dir.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                    text_files.append(file_path)
        
        self.logger.info(f"🔍 发现 {len(text_files)} 个文本文件")
        return text_files
    
    def process_all_files(self, sample_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """处理所有文件"""
        all_documents = []
        
        # 扫描文件
        text_files = self.scan_text_files()
        
        if not text_files:
            self.logger.warning("⚠️ 未发现文本文件")
            return []
        
        # 限制处理数量
        if sample_size and sample_size > 0:
            text_files = text_files[:sample_size]
            self.logger.info(f"📊 限制处理数量: {len(text_files)} 个文件")
        
        # 处理文件
        for file_path in tqdm(text_files, desc="处理文本文件"):
            try:
                file_ext = file_path.suffix.lower()
                if file_ext in self.supported_formats:
                    self.logger.info(f"📄 处理文件: {file_path.name}")
                    documents = self.supported_formats[file_ext](file_path)
                    all_documents.extend(documents)
                else:
                    self.logger.debug(f"跳过不支持的文件格式: {file_path.name} ({file_ext})")
            except Exception as e:
                self.logger.error(f"处理文件失败 {file_path}: {e}")
                self.failed_files.append({
                    'file_name': file_path.name,
                    'file_path': str(file_path),
                    'error': str(e),
                    'processed_time': datetime.now().isoformat()
                })
        
        self.processed_documents = all_documents
        self.logger.info(f"🎉 文本处理完成! 成功处理 {len(all_documents)} 个文档")
        
        return all_documents
    
    def save_results(self, documents: List[Dict[str, Any]]):
        """保存处理结果 - 只保存JSON格式和统计信息"""
        if not documents:
            self.logger.warning("没有结果需要保存")
            return
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存为JSON格式（供文档切分使用）
        json_path = self.output_dir / 'text_documents.json'
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(documents, f, ensure_ascii=False, indent=2)
            self.logger.info(f"✅ JSON结果已保存: {json_path}")
        except Exception as e:
            self.logger.error(f"❌ JSON保存失败: {e}")
        
        # 保存处理统计
        stats_path = self.output_dir / 'text_processing_stats.json'
        try:
            stats = {
                'total_documents': len(documents),
                'failed_files': len(self.failed_files),
                'data_types': self._get_data_type_stats(documents),
                'file_formats': self._get_file_format_stats(documents),
                'processed_time': datetime.now().isoformat(),
                'description': '数据预处理结果，供文档切分模块使用'
            }
            
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            self.logger.info(f"✅ 处理统计已保存: {stats_path}")
            
        except Exception as e:
            self.logger.error(f"❌ 统计保存失败: {e}")
    
    # 移除向量化数据生成功能 - 数据预处理只负责数据清洗和格式转换
    
    def _get_data_type_stats(self, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        """获取数据类型统计"""
        stats = {}
        for doc in documents:
            data_type = doc.get('data_type', 'unknown')
            stats[data_type] = stats.get(data_type, 0) + 1
        return stats
    
    def _get_file_format_stats(self, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        """获取文件格式统计"""
        stats = {}
        for doc in documents:
            file_name = doc.get('file_name', '')
            file_ext = Path(file_name).suffix.lower()
            stats[file_ext] = stats.get(file_ext, 0) + 1
        return stats
    
    def run(self, sample_size: Optional[int] = None, process_all_files: bool = True):
        """运行文本处理"""
        self.logger.info("🚀 开始文本处理")
        
        if process_all_files:
            # 处理所有文件
            documents = self.process_all_files(sample_size)
            self.logger.info(f"处理完成后的documents: {documents}")
            if documents:
                # 保存结果
                self.save_results(documents)
                
                # 输出统计信息
                self.logger.info(f"📊 数据预处理完成统计:")
                self.logger.info(f"  - 成功处理文档: {len(documents)}")
                self.logger.info(f"  - 失败文件: {len(self.failed_files)}")
                
                # 数据类型统计
                data_type_stats = self._get_data_type_stats(documents)
                self.logger.info(f"  - 数据类型分布: {data_type_stats}")
                
                # 文件格式统计
                file_format_stats = self._get_file_format_stats(documents)
                self.logger.info(f"  - 文件格式分布: {file_format_stats}")
                
                self.logger.info("📄 数据预处理完成，JSON文件已保存供文档切分使用")
            else:
                self.logger.warning("⚠️ 没有成功处理任何文档")
        else:
            self.logger.info("跳过文件处理")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return {
            'total_documents': len(self.processed_documents),
            'failed_files': len(self.failed_files),
            'data_types': self._get_data_type_stats(self.processed_documents),
            'file_formats': self._get_file_format_stats(self.processed_documents),
            'supported_formats': list(self.supported_formats.keys())
        }


def setup_logging():
    """设置统一日志配置"""
    import sys
    from pathlib import Path
    current_dir = Path(__file__).parent
    sys.path.append(str(current_dir.parent / "core"))
    
    try:
        from log_manager import get_logger
        # 使用统一的日志管理器
        logger = get_logger(__name__)
    except ImportError:
        # 如果log_manager不可用，使用标准logging
        logger = logging.getLogger(__name__)
    logger.info("📝 开始文本预处理运行")
    logger.info("🎯 智诊通文本预处理系统启动")
    
    return logger

def main():
    """主函数"""
    # 设置统一日志配置
    logger = setup_logging()
    
    # 创建文本预处理器
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
    raw_data_dir = os.path.join(project_root, "datas", "medical_knowledge", "text_data", "raw")
    output_dir = os.path.join(project_root, "datas", "medical_knowledge", "text_data", "processed")
    
    processor = OptimizedMedicalTextPreprocessor(raw_data_dir, output_dir)
    
    # 运行处理
    processor.run(sample_size=5, process_all_files=True)
    
    # 输出统计信息
    stats = processor.get_processing_stats()
    logger.info("\n📊 数据预处理统计:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("\n🎯 数据预处理完成！")
    logger.info("📄 生成的JSON文件可供文档切分模块使用")


if __name__ == "__main__":
    main()
