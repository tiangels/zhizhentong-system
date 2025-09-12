"""
文档切分模块
实现多种文档切分策略，将长文档切分为适合向量化的小片段
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChunkStrategy(Enum):
    """切分策略枚举"""
    FIXED_SIZE = "fixed_size"           # 固定大小切分
    SENTENCE_BASED = "sentence_based"   # 基于句子切分
    PARAGRAPH_BASED = "paragraph_based" # 基于段落切分
    SEMANTIC_BASED = "semantic_based"   # 基于语义切分
    MEDICAL_STRUCTURED = "medical_structured"  # 医疗结构化切分


@dataclass
class ChunkConfig:
    """切分配置类"""
    strategy: ChunkStrategy = ChunkStrategy.FIXED_SIZE
    chunk_size: int = 512              # 每个chunk的最大字符数
    chunk_overlap: int = 50            # chunk之间的重叠字符数
    min_chunk_size: int = 100          # 最小chunk大小
    max_chunk_size: int = 1024         # 最大chunk大小
    preserve_sentences: bool = True    # 是否保持句子完整性
    preserve_paragraphs: bool = True   # 是否保持段落完整性
    medical_sections: List[str] = None # 医疗文档章节


class DocumentChunker:
    """文档切分类"""
    
    def __init__(self, config: ChunkConfig = None):
        """
        初始化文档切分器
        
        Args:
            config: 切分配置
        """
        self.config = config or ChunkConfig()
        self.logger = logging.getLogger(__name__)
        
        # 医疗文档章节标识
        self.medical_sections = self.config.medical_sections or [
            "主诉", "现病史", "既往史", "个人史", "家族史",
            "体格检查", "辅助检查", "诊断", "治疗", "预后",
            "症状", "体征", "检查结果", "诊断意见", "治疗建议"
        ]
        
        # 句子结束标点
        self.sentence_endings = r'[。！？；]'
        
        # 段落分隔符
        self.paragraph_separators = r'\n\s*\n'
    
    def chunk_document(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        切分文档
        
        Args:
            text: 输入文本
            metadata: 文档元数据
            
        Returns:
            切分后的文档片段列表
        """
        if not text or not text.strip():
            return []
        
        # 预处理文本
        processed_text = self._preprocess_text(text)
        
        # 根据策略切分
        self.logger.info(f"开始切分文档，策略: {self.config.strategy.value}, 文本长度: {len(processed_text)}")
        
        if self.config.strategy == ChunkStrategy.FIXED_SIZE:
            chunks = self._fixed_size_chunking(processed_text)
        elif self.config.strategy == ChunkStrategy.SENTENCE_BASED:
            chunks = self._sentence_based_chunking(processed_text)
        elif self.config.strategy == ChunkStrategy.PARAGRAPH_BASED:
            chunks = self._paragraph_based_chunking(processed_text)
        elif self.config.strategy == ChunkStrategy.SEMANTIC_BASED:
            chunks = self._semantic_based_chunking(processed_text)
        elif self.config.strategy == ChunkStrategy.MEDICAL_STRUCTURED:
            chunks = self._medical_structured_chunking(processed_text)
        else:
            chunks = self._fixed_size_chunking(processed_text)
        
        self.logger.info(f"切分完成，生成 {len(chunks)} 个片段")
        
        # 后处理chunks
        processed_chunks = self._postprocess_chunks(chunks, metadata)
        
        self.logger.info(f"文档切分完成，共生成 {len(processed_chunks)} 个片段")
        return processed_chunks
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 清理多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        # 清理特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fa5。！？；，、：""''（）【】]', '', text)
        return text.strip()
    
    def _fixed_size_chunking(self, text: str) -> List[str]:
        """固定大小切分"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.config.chunk_size
            
            if end >= len(text):
                chunk = text[start:]
            else:
                # 尝试在句子边界切分
                if self.config.preserve_sentences:
                    chunk_end = self._find_sentence_boundary(text, start, end)
                    if chunk_end > start:
                        end = chunk_end
                
                chunk = text[start:end]
            
            if len(chunk.strip()) >= self.config.min_chunk_size:
                chunks.append(chunk.strip())
            
            # 计算下一个chunk的起始位置（考虑重叠）
            start = end - self.config.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _sentence_based_chunking(self, text: str) -> List[str]:
        """基于句子切分"""
        # 按句子分割
        sentences = re.split(self.sentence_endings, text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # 如果添加当前句子会超过大小限制
            if len(current_chunk) + len(sentence) > self.config.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += "。" + sentence
                else:
                    current_chunk = sentence
        
        # 添加最后一个chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _paragraph_based_chunking(self, text: str) -> List[str]:
        """基于段落切分"""
        # 按段落分割
        paragraphs = re.split(self.paragraph_separators, text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # 如果段落本身超过大小限制，需要进一步切分
            if len(paragraph) > self.config.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # 对长段落进行固定大小切分
                sub_chunks = self._fixed_size_chunking(paragraph)
                chunks.extend(sub_chunks)
            else:
                # 如果添加当前段落会超过大小限制
                if len(current_chunk) + len(paragraph) > self.config.chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
        
        # 添加最后一个chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _semantic_based_chunking(self, text: str) -> List[str]:
        """基于语义切分（简化版本）"""
        # 这里可以实现更复杂的语义切分逻辑
        # 目前使用段落切分作为基础
        return self._paragraph_based_chunking(text)
    
    def _medical_structured_chunking(self, text: str) -> List[str]:
        """医疗结构化切分"""
        chunks = []
        
        # 识别医疗文档结构
        sections = self._identify_medical_sections(text)
        
        for section_name, section_content in sections.items():
            if len(section_content) <= self.config.chunk_size:
                # 如果章节内容不超过大小限制，直接作为一个chunk
                chunks.append(section_content)
            else:
                # 如果章节内容过长，进一步切分
                sub_chunks = self._sentence_based_chunking(section_content)
                for i, sub_chunk in enumerate(sub_chunks):
                    # 为子chunk添加章节信息
                    chunk_with_section = f"[{section_name}] {sub_chunk}"
                    chunks.append(chunk_with_section)
        
        return chunks
    
    def _identify_medical_sections(self, text: str) -> Dict[str, str]:
        """识别医疗文档章节"""
        sections = {}
        current_section = "未知章节"
        current_content = ""
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否是章节标题
            is_section_header = False
            for section in self.medical_sections:
                if section in line and len(line) < 50:  # 章节标题通常较短
                    # 保存前一个章节
                    if current_content.strip():
                        sections[current_section] = current_content.strip()
                    
                    # 开始新章节
                    current_section = section
                    current_content = ""
                    is_section_header = True
                    break
            
            if not is_section_header:
                current_content += line + "\n"
        
        # 保存最后一个章节
        if current_content.strip():
            sections[current_section] = current_content.strip()
        
        return sections
    
    def _find_sentence_boundary(self, text: str, start: int, end: int) -> int:
        """查找句子边界"""
        # 从end向前查找最近的句子结束符
        for i in range(end - 1, start, -1):
            if text[i] in '。！？；':
                return i + 1
        
        return end
    
    def _postprocess_chunks(self, chunks: List[str], metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """后处理chunks"""
        processed_chunks = []
        
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < self.config.min_chunk_size:
                continue
            
            chunk_data = {
                'id': f"chunk_{i}",
                'content': chunk,
                'length': len(chunk),
                'chunk_index': i,
                'total_chunks': len(chunks),
                'metadata': metadata or {}
            }
            
            # 添加章节信息（如果是医疗结构化切分）
            if self.config.strategy == ChunkStrategy.MEDICAL_STRUCTURED:
                section_match = re.match(r'\[([^\]]+)\]', chunk)
                if section_match:
                    chunk_data['section'] = section_match.group(1)
            
            processed_chunks.append(chunk_data)
        
        return processed_chunks
    
    def chunk_file(self, file_path: str, output_dir: str = None) -> List[Dict[str, Any]]:
        """
        切分文件
        
        Args:
            file_path: 文件路径
            output_dir: 输出目录
            
        Returns:
            切分后的文档片段列表
        """
        try:
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 获取文件元数据
            file_metadata = {
                'file_path': file_path,
                'file_name': Path(file_path).name,
                'file_size': len(content),
                'chunk_strategy': self.config.strategy.value
            }
            
            # 切分文档
            chunks = self.chunk_document(content, file_metadata)
            
            # 保存结果
            if output_dir:
                self._save_chunks(chunks, file_path, output_dir)
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"切分文件失败 {file_path}: {e}")
            return []
    
    def _save_chunks(self, chunks: List[Dict[str, Any]], file_path: str, output_dir: str):
        """保存切分结果"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成输出文件名
            file_name = Path(file_path).stem
            output_file = os.path.join(output_dir, f"{file_name}_chunks.json")
            
            # 保存为JSON格式
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"切分结果已保存到: {output_file}")
            
        except Exception as e:
            self.logger.error(f"保存切分结果失败: {e}")
    
    def batch_chunk_files(self, input_dir: str, output_dir: str, 
                         file_extensions: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        批量切分文件
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            file_extensions: 支持的文件扩展名
            
        Returns:
            文件路径到切分结果的映射
        """
        if file_extensions is None:
            file_extensions = ['.txt', '.md', '.json']
        
        results = {}
        
        for file_path in Path(input_dir).rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in file_extensions:
                chunks = self.chunk_file(str(file_path), output_dir)
                results[str(file_path)] = chunks
        
        self.logger.info(f"批量切分完成，共处理 {len(results)} 个文件")
        return results


def create_medical_chunker() -> DocumentChunker:
    """创建医疗文档切分器"""
    config = ChunkConfig(
        strategy=ChunkStrategy.MEDICAL_STRUCTURED,
        chunk_size=512,
        chunk_overlap=50,
        min_chunk_size=20,  # 降低最小片段大小，保留更多医疗信息
        max_chunk_size=1024,
        preserve_sentences=True,
        preserve_paragraphs=True,
        medical_sections=[
            "主诉", "现病史", "既往史", "个人史", "家族史",
            "体格检查", "辅助检查", "诊断", "治疗", "预后",
            "症状", "体征", "检查结果", "诊断意见", "治疗建议"
        ]
    )
    return DocumentChunker(config)


def create_general_chunker() -> DocumentChunker:
    """创建通用文档切分器"""
    config = ChunkConfig(
        strategy=ChunkStrategy.SENTENCE_BASED,
        chunk_size=512,
        chunk_overlap=50,
        min_chunk_size=20,  # 降低最小片段大小，保留更多有用信息
        max_chunk_size=1024,
        preserve_sentences=True,
        preserve_paragraphs=True
    )
    return DocumentChunker(config)


if __name__ == "__main__":
    # 测试文档切分功能
    test_text = """
    主诉：患者男性，45岁，因胸痛3天入院。
    
    现病史：患者3天前无明显诱因出现胸痛，呈持续性钝痛，伴胸闷、气短，活动后加重，休息后稍缓解。
    
    既往史：患者有高血压病史5年，规律服药，血压控制良好。无糖尿病、冠心病等病史。
    
    体格检查：体温36.5℃，脉搏80次/分，呼吸20次/分，血压140/90mmHg。神志清楚，精神可。
    
    辅助检查：心电图示ST段压低，T波倒置。胸部X线片示心影增大。
    
    诊断：1. 冠心病 不稳定性心绞痛 2. 高血压病2级
    
    治疗建议：1. 抗血小板聚集治疗 2. 调脂稳定斑块 3. 控制血压 4. 必要时行冠脉造影
    """
    
    # 测试医疗结构化切分
    medical_chunker = create_medical_chunker()
    chunks = medical_chunker.chunk_document(test_text)
    
    print("医疗结构化切分结果:")
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i+1} ---")
        print(f"内容: {chunk['content'][:100]}...")
        print(f"长度: {chunk['length']}")
        if 'section' in chunk:
            print(f"章节: {chunk['section']}")
    
    # 测试通用切分
    general_chunker = create_general_chunker()
    chunks = general_chunker.chunk_document(test_text)
    
    print(f"\n通用切分结果: 共 {len(chunks)} 个片段")
