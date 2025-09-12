"""
通用文本数据预处理器
处理text_data/raw目录下的各种格式文件（PDF、TXT、CSV、JSON、Excel等）
"""

import os
import re
import pandas as pd
import json
import jieba
from tqdm import tqdm
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# PDF处理
try:
    import PyPDF2
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("警告: PDF处理库未安装，将跳过PDF文件处理")

# Excel处理
try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    print("警告: Excel处理库未安装，将跳过Excel文件处理")

logger = logging.getLogger(__name__)

class GeneralTextPreprocessor:
    """通用文本数据预处理器"""
    
    def __init__(self, raw_data_dir: str, output_dir: str):
        """
        初始化预处理器
        
        Args:
            raw_data_dir: 原始数据目录路径
            output_dir: 输出目录路径
        """
        self.raw_data_dir = Path(raw_data_dir)
        self.output_dir = Path(output_dir)
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "training_data").mkdir(exist_ok=True)
        (self.output_dir / "test_data").mkdir(exist_ok=True)
        
        # 存储处理后的数据
        self.processed_documents = []
        
        # 支持的文件格式
        self.supported_formats = {
            '.txt': self._process_txt_file,
            '.csv': self._process_csv_file,
            '.json': self._process_json_file,
            '.pdf': self._process_pdf_file,
            '.xlsx': self._process_excel_file,
            '.xls': self._process_excel_file,
        }
        
        logger.info(f"通用文本预处理器初始化完成")
        logger.info(f"原始数据目录: {self.raw_data_dir}")
        logger.info(f"输出目录: {self.output_dir}")
    
    def _process_txt_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """处理TXT文件"""
        documents = []
        
        try:
            # 尝试不同编码
            content = None
            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                logger.warning(f"无法读取文件: {file_path}")
                return documents
            
            # 按段落分割
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            
            for i, paragraph in enumerate(paragraphs):
                if len(paragraph) > 10:  # 过滤太短的段落
                    documents.append({
                        'id': f"{file_path.stem}_{i}",
                        'content': paragraph,
                        'source_file': str(file_path),
                        'file_type': 'txt',
                        'metadata': {
                            'paragraph_index': i,
                            'total_paragraphs': len(paragraphs),
                            'file_size': len(content)
                        }
                    })
            
            logger.info(f"处理TXT文件: {file_path.name}, 提取 {len(documents)} 个段落")
            
        except Exception as e:
            logger.error(f"处理TXT文件失败 {file_path}: {e}")
        
        return documents
    
    def _process_csv_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """处理CSV文件"""
        documents = []
        
        try:
            # 尝试读取CSV文件
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # 处理每一行
            for idx, row in df.iterrows():
                # 将行数据转换为文本
                text_parts = []
                for col, value in row.items():
                    if pd.notna(value) and str(value).strip():
                        text_parts.append(f"{col}: {value}")
                
                if text_parts:
                    content = " | ".join(text_parts)
                    documents.append({
                        'id': f"{file_path.stem}_{idx}",
                        'content': content,
                        'source_file': str(file_path),
                        'file_type': 'csv',
                        'metadata': {
                            'row_index': idx,
                            'total_rows': len(df),
                            'columns': list(df.columns)
                        }
                    })
            
            logger.info(f"处理CSV文件: {file_path.name}, 提取 {len(documents)} 行数据")
            
        except Exception as e:
            logger.error(f"处理CSV文件失败 {file_path}: {e}")
        
        return documents
    
    def _process_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """处理JSON文件"""
        documents = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 递归处理JSON数据
            def extract_text_from_json(obj, path=""):
                texts = []
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        texts.extend(extract_text_from_json(value, current_path))
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        current_path = f"{path}[{i}]" if path else f"[{i}]"
                        texts.extend(extract_text_from_json(item, current_path))
                elif isinstance(obj, str) and len(obj.strip()) > 5:
                    texts.append({
                        'path': path,
                        'content': obj.strip()
                    })
                return texts
            
            extracted_texts = extract_text_from_json(data)
            
            for i, text_info in enumerate(extracted_texts):
                documents.append({
                    'id': f"{file_path.stem}_{i}",
                    'content': text_info['content'],
                    'source_file': str(file_path),
                    'file_type': 'json',
                    'metadata': {
                        'json_path': text_info['path'],
                        'total_texts': len(extracted_texts)
                    }
                })
            
            logger.info(f"处理JSON文件: {file_path.name}, 提取 {len(documents)} 个文本片段")
            
        except Exception as e:
            logger.error(f"处理JSON文件失败 {file_path}: {e}")
        
        return documents
    
    def _process_pdf_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """处理PDF文件"""
        documents = []
        
        if not PDF_AVAILABLE:
            logger.warning(f"PDF处理库未安装，跳过文件: {file_path}")
            return documents
        
        try:
            # 使用pdfplumber提取文本
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text and len(text.strip()) > 10:
                        documents.append({
                            'id': f"{file_path.stem}_page_{page_num}",
                            'content': text.strip(),
                            'source_file': str(file_path),
                            'file_type': 'pdf',
                            'metadata': {
                                'page_number': page_num + 1,
                                'total_pages': len(pdf.pages)
                            }
                        })
            
            logger.info(f"处理PDF文件: {file_path.name}, 提取 {len(documents)} 页内容")
            
        except Exception as e:
            logger.error(f"处理PDF文件失败 {file_path}: {e}")
        
        return documents
    
    def _process_excel_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """处理Excel文件"""
        documents = []
        
        if not EXCEL_AVAILABLE:
            logger.warning(f"Excel处理库未安装，跳过文件: {file_path}")
            return documents
        
        try:
            # 读取Excel文件的所有工作表
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # 处理每一行
                for idx, row in df.iterrows():
                    text_parts = []
                    for col, value in row.items():
                        if pd.notna(value) and str(value).strip():
                            text_parts.append(f"{col}: {value}")
                    
                    if text_parts:
                        content = " | ".join(text_parts)
                        documents.append({
                            'id': f"{file_path.stem}_{sheet_name}_{idx}",
                            'content': content,
                            'source_file': str(file_path),
                            'file_type': 'excel',
                            'metadata': {
                                'sheet_name': sheet_name,
                                'row_index': idx,
                                'total_rows': len(df),
                                'columns': list(df.columns)
                            }
                        })
            
            logger.info(f"处理Excel文件: {file_path.name}, 提取 {len(documents)} 行数据")
            
        except Exception as e:
            logger.error(f"处理Excel文件失败 {file_path}: {e}")
        
        return documents
    
    def process_all_files(self) -> List[Dict[str, Any]]:
        """处理所有支持的文件"""
        logger.info("开始处理所有文件...")
        
        all_documents = []
        
        # 遍历原始数据目录
        for file_path in self.raw_data_dir.rglob("*"):
            if file_path.is_file():
                file_ext = file_path.suffix.lower()
                
                if file_ext in self.supported_formats:
                    logger.info(f"处理文件: {file_path.name}")
                    documents = self.supported_formats[file_ext](file_path)
                    all_documents.extend(documents)
                else:
                    logger.info(f"跳过不支持的文件格式: {file_path.name} ({file_ext})")
        
        self.processed_documents = all_documents
        logger.info(f"文件处理完成，共提取 {len(all_documents)} 个文档")
        
        return all_documents
    
    def clean_and_enhance_data(self):
        """清洗和增强数据"""
        logger.info("开始清洗和增强数据...")
        
        if not self.processed_documents:
            logger.warning("没有文档需要清洗")
            return
        
        # 去重
        initial_count = len(self.processed_documents)
        seen_contents = set()
        unique_documents = []
        
        for doc in self.processed_documents:
            content_hash = hash(doc['content'])
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_documents.append(doc)
        
        self.processed_documents = unique_documents
        logger.info(f"去重完成: {initial_count} -> {len(unique_documents)}")
        
        # 过滤太短的文档
        filtered_documents = [doc for doc in self.processed_documents if len(doc['content']) > 20]
        logger.info(f"过滤短文档: {len(self.processed_documents)} -> {len(filtered_documents)}")
        self.processed_documents = filtered_documents
        
        # 添加分词结果
        logger.info("进行中文分词处理...")
        for doc in tqdm(self.processed_documents, desc="分词处理"):
            doc['content_tokens'] = ' '.join(jieba.cut(doc['content']))
    
    def save_data(self):
        """保存处理后的数据"""
        logger.info("保存处理后的数据...")
        
        if not self.processed_documents:
            logger.warning("没有数据需要保存")
            return
        
        # 转换为DataFrame
        df = pd.DataFrame(self.processed_documents)
        
        # 分割训练集和测试集
        total_count = len(df)
        train_size = int(total_count * 0.8)
        
        train_df = df[:train_size]
        test_df = df[train_size:]
        
        # 保存训练集
        train_path = self.output_dir / "training_data" / "general_text_train.csv"
        train_df.to_csv(train_path, index=False, encoding='utf-8')
        logger.info(f"训练集已保存: {train_path} ({len(train_df)} 条)")
        
        # 保存测试集
        test_path = self.output_dir / "test_data" / "general_text_test.csv"
        test_df.to_csv(test_path, index=False, encoding='utf-8')
        logger.info(f"测试集已保存: {test_path} ({len(test_df)} 条)")
        
        # 创建数据摘要
        self.create_data_summary()
    
    def create_data_summary(self):
        """创建数据摘要"""
        summary = {
            "general_text_data": {
                "total_count": len(self.processed_documents),
                "file_types": {},
                "source_files": []
            }
        }
        
        # 统计文件类型
        for doc in self.processed_documents:
            file_type = doc.get('file_type', 'unknown')
            summary["general_text_data"]["file_types"][file_type] = \
                summary["general_text_data"]["file_types"].get(file_type, 0) + 1
        
        # 统计源文件
        source_files = set(doc['source_file'] for doc in self.processed_documents)
        summary["general_text_data"]["source_files"] = list(source_files)
        
        # 保存摘要
        summary_path = self.output_dir / "data_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据摘要已保存: {summary_path}")
    
    def run(self):
        """运行完整的预处理流程"""
        logger.info("开始通用文本数据预处理...")
        
        try:
            # 处理所有文件
            self.process_all_files()
            
            # 清洗和增强数据
            self.clean_and_enhance_data()
            
            # 保存数据
            self.save_data()
            
            logger.info("通用文本数据预处理完成！")
            return True
            
        except Exception as e:
            logger.error(f"预处理失败: {e}")
            return False

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 设置路径
    raw_data_dir = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/text_data/raw"
    output_dir = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/text_data/processed"
    
    # 创建预处理器并运行
    preprocessor = GeneralTextPreprocessor(raw_data_dir, output_dir)
    success = preprocessor.run()
    
    if success:
        print("✅ 通用文本数据预处理完成")
    else:
        print("❌ 通用文本数据预处理失败")
