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

# 导入配置管理器
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config"))
try:
    from config_manager import get_config, get_model_path
except ImportError:
    # 如果配置管理器不可用，使用默认值
    def get_config():
        return {}
    def get_model_path(model_type):
        return ""

# LangChain imports
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.embeddings import HuggingFaceEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("Warning: LangChain not available. Install with: pip install langchain langchain-community")

# HuggingFace imports for ernie model
try:
    from sentence_transformers import SentenceTransformer
    import torch
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Warning: sentence-transformers not available. Install with: pip install sentence-transformers")

# 设置统一的日志文件
def setup_unified_logging():
    """设置统一的日志配置"""
    import sys
    from pathlib import Path
    current_dir = Path(__file__).parent
    sys.path.append(str(current_dir.parent / "core"))
    
    import sys
    from pathlib import Path

    # 添加common模块到路径
    current_file = Path(__file__)
    common_dir = current_file.parent.parent.parent.parent.parent / "common"
    sys.path.insert(0, str(common_dir))

    from log_config import get_logger
    
    # 使用统一的日志管理器
    logger = get_logger(__name__)
    logger.info("📄 开始文档分块运行")
    logger.info("🎯 智诊通文档分块系统启动")
    
    return logger

# 初始化日志
logger = setup_unified_logging()


class ChunkStrategy(Enum):
    """切分策略枚举"""
    FIXED_SIZE = "fixed_size"           # 固定大小切分
    SENTENCE_BASED = "sentence_based"   # 基于句子切分
    PARAGRAPH_BASED = "paragraph_based" # 基于段落切分
    SEMANTIC_BASED = "semantic_based"   # 基于语义切分
    MEDICAL_STRUCTURED = "medical_structured"  # 医疗结构化切分
    LANGCHAIN_RECURSIVE = "langchain_recursive"  # LangChain递归切分
    ERNIE_SEMANTIC = "ernie_semantic"   # ERNIE语义切分
    HYBRID_SMART = "hybrid_smart"       # 混合智能切分


@dataclass
class ChunkConfig:
    """切分配置类"""
    strategy: ChunkStrategy = ChunkStrategy.ERNIE_SEMANTIC
    chunk_size: int = 256              # 每个chunk的最大字符数（降低以匹配Token限制）
    chunk_overlap: int = 25            # chunk之间的重叠字符数
    min_chunk_size: int = 50           # 最小chunk大小
    max_chunk_size: int = 512          # 最大chunk大小
    preserve_sentences: bool = True    # 是否保持句子完整性
    preserve_paragraphs: bool = True   # 是否保持段落完整性
    medical_sections: List[str] = None # 医疗文档章节
    
    # 语义切分相关配置
    semantic_similarity_threshold: float = 0.7  # 语义相似度阈值
    ernie_model_name: str = "nghuyong/ernie-3.0-base-zh"  # ERNIE模型名称
    use_gpu: bool = True               # 是否使用GPU
    batch_size: int = 32              # 批处理大小
    
    # LangChain配置
    separators: List[str] = None       # 自定义分隔符
    length_function: str = "len"       # 长度计算函数


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
        
        # 测试相关属性
        self.test_results = {}
        self.test_logger = logging.getLogger('chunking_test')
        
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
        
        # 初始化ERNIE模型（延迟加载）
        self.ernie_model = None
        self._init_ernie_model()
        
        # 初始化LangChain分割器
        self.langchain_splitter = None
        self._init_langchain_splitter()
    
    def _init_ernie_model(self):
        """初始化ERNIE模型"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            self.logger.warning("sentence-transformers not available, ERNIE semantic chunking disabled")
            return
        
        try:
            device = "cuda" if self.config.use_gpu and torch.cuda.is_available() else "cpu"
            self.ernie_model = SentenceTransformer(
                self.config.ernie_model_name,
                device=device
            )
            self.logger.info(f"ERNIE model loaded on {device}")
        except Exception as e:
            self.logger.warning(f"Failed to load ERNIE model: {e}")
            self.logger.info("ERNIE semantic chunking will be disabled, falling back to other strategies")
            self.ernie_model = None
    
    def _init_langchain_splitter(self):
        """初始化LangChain分割器"""
        if not LANGCHAIN_AVAILABLE:
            self.logger.warning("LangChain not available, recursive chunking disabled")
            return
        
        try:
            # 默认分隔符，针对中文优化
            separators = self.config.separators or [
                "\n\n",  # 段落分隔符
                "\n",    # 行分隔符
                "。",    # 句号
                "！",    # 感叹号
                "？",    # 问号
                "；",    # 分号
                "，",    # 逗号
                " ",     # 空格
                ""       # 字符级别
            ]
            
            self.langchain_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                length_function=len,
                separators=separators,
                is_separator_regex=False
            )
            self.logger.info("LangChain RecursiveCharacterTextSplitter initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize LangChain splitter: {e}")
            self.langchain_splitter = None
    
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
            self.logger.warning("输入文本为空，跳过切分")
            return []
        
        # 预处理文本
        processed_text = self._preprocess_text(text)
        self.logger.info(f"文本预处理完成，原始长度: {len(text)}, 处理后长度: {len(processed_text)}")
        
        # 根据策略切分
        self.logger.info(f"开始切分文档，策略: {self.config.strategy.value}")
        self.logger.info(f"切分配置: chunk_size={self.config.chunk_size}, chunk_overlap={self.config.chunk_overlap}, min_chunk_size={self.config.min_chunk_size}")
        
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
        elif self.config.strategy == ChunkStrategy.LANGCHAIN_RECURSIVE:
            chunks = self._langchain_recursive_chunking(processed_text)
        elif self.config.strategy == ChunkStrategy.ERNIE_SEMANTIC:
            chunks = self._ernie_semantic_chunking(processed_text)
        elif self.config.strategy == ChunkStrategy.HYBRID_SMART:
            chunks = self._hybrid_smart_chunking(processed_text)
        else:
            chunks = self._fixed_size_chunking(processed_text)
        
        self.logger.info(f"切分完成，生成 {len(chunks)} 个原始片段")
        
        # 后处理chunks
        processed_chunks = self._postprocess_chunks(chunks, metadata)
        
        # 详细统计信息
        if processed_chunks:
            chunk_lengths = [chunk['length'] for chunk in processed_chunks]
            avg_length = sum(chunk_lengths) / len(chunk_lengths)
            min_length = min(chunk_lengths)
            max_length = max(chunk_lengths)
            
            self.logger.info(f"文档切分完成，共生成 {len(processed_chunks)} 个片段")
            self.logger.info(f"片段长度统计: 平均={avg_length:.1f}, 最小={min_length}, 最大={max_length}")
            
            # 显示前几个片段的详细信息
            for i, chunk in enumerate(processed_chunks[:2]):
                self.logger.info(f"片段 {i+1}: {chunk['content'][:80]}... (长度: {chunk['length']})")
        else:
            self.logger.warning("切分后没有生成任何有效片段")
        
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
        self.logger.info(f"使用固定大小切分策略，目标大小: {self.config.chunk_size}, 重叠: {self.config.chunk_overlap}")
        chunks = []
        start = 0
        chunk_count = 0
        
        while start < len(text):
            end = start + self.config.chunk_size
            
            if end >= len(text):
                chunk = text[start:]
                self.logger.debug(f"最后片段: 位置 {start}-{len(text)}")
            else:
                # 尝试在句子边界切分
                if self.config.preserve_sentences:
                    chunk_end = self._find_sentence_boundary(text, start, end)
                    if chunk_end > start:
                        end = chunk_end
                        self.logger.debug(f"在句子边界切分: 位置 {start}-{end}")
                
                chunk = text[start:end]
            
            if len(chunk.strip()) >= self.config.min_chunk_size:
                chunks.append(chunk.strip())
                chunk_count += 1
                self.logger.debug(f"片段 {chunk_count}: 长度 {len(chunk.strip())}")
            else:
                self.logger.debug(f"跳过过短片段: 长度 {len(chunk.strip())} < {self.config.min_chunk_size}")
            
            # 计算下一个chunk的起始位置（考虑重叠）
            start = end - self.config.chunk_overlap
            if start >= len(text):
                break
        
        self.logger.info(f"固定大小切分完成，生成 {len(chunks)} 个片段")
        return chunks
    
    def _sentence_based_chunking(self, text: str) -> List[str]:
        """基于句子切分"""
        self.logger.info(f"使用基于句子切分策略，目标大小: {self.config.chunk_size}")
        
        # 按句子分割
        sentences = re.split(self.sentence_endings, text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        self.logger.info(f"识别到 {len(sentences)} 个句子")
        
        chunks = []
        current_chunk = ""
        chunk_count = 0
        
        for i, sentence in enumerate(sentences):
            # 如果添加当前句子会超过大小限制
            if len(current_chunk) + len(sentence) > self.config.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    chunk_count += 1
                    self.logger.debug(f"完成片段 {chunk_count}: 长度 {len(current_chunk.strip())}")
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += "。" + sentence
                else:
                    current_chunk = sentence
        
        # 添加最后一个chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
            chunk_count += 1
            self.logger.debug(f"完成最后片段 {chunk_count}: 长度 {len(current_chunk.strip())}")
        
        self.logger.info(f"基于句子切分完成，生成 {len(chunks)} 个片段")
        return chunks
    
    def _paragraph_based_chunking(self, text: str) -> List[str]:
        """基于段落切分"""
        self.logger.info(f"使用基于段落切分策略，目标大小: {self.config.chunk_size}")
        
        # 按段落分割
        paragraphs = re.split(self.paragraph_separators, text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        self.logger.info(f"识别到 {len(paragraphs)} 个段落")
        
        chunks = []
        current_chunk = ""
        chunk_count = 0
        
        for i, paragraph in enumerate(paragraphs):
            # 如果段落本身超过大小限制，需要进一步切分
            if len(paragraph) > self.config.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    chunk_count += 1
                    self.logger.debug(f"完成片段 {chunk_count}: 长度 {len(current_chunk.strip())}")
                    current_chunk = ""
                
                # 对长段落进行固定大小切分
                self.logger.debug(f"段落 {i+1} 过长 ({len(paragraph)} 字符)，进行子切分")
                sub_chunks = self._fixed_size_chunking(paragraph)
                chunks.extend(sub_chunks)
                chunk_count += len(sub_chunks)
                self.logger.debug(f"段落 {i+1} 切分为 {len(sub_chunks)} 个子片段")
            else:
                # 如果添加当前段落会超过大小限制
                if len(current_chunk) + len(paragraph) > self.config.chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        chunk_count += 1
                        self.logger.debug(f"完成片段 {chunk_count}: 长度 {len(current_chunk.strip())}")
                    current_chunk = paragraph
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
        
        # 添加最后一个chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
            chunk_count += 1
            self.logger.debug(f"完成最后片段 {chunk_count}: 长度 {len(current_chunk.strip())}")
        
        self.logger.info(f"基于段落切分完成，生成 {len(chunks)} 个片段")
        return chunks
    
    def _semantic_based_chunking(self, text: str) -> List[str]:
        """基于语义切分（简化版本）"""
        # 这里可以实现更复杂的语义切分逻辑
        # 目前使用段落切分作为基础
        return self._paragraph_based_chunking(text)
    
    def _langchain_recursive_chunking(self, text: str) -> List[str]:
        """使用LangChain递归切分"""
        if not self.langchain_splitter:
            self.logger.warning("LangChain splitter not available, falling back to fixed size chunking")
            return self._fixed_size_chunking(text)
        
        try:
            chunks = self.langchain_splitter.split_text(text)
            return [chunk.strip() for chunk in chunks if chunk.strip()]
        except Exception as e:
            self.logger.error(f"LangChain recursive chunking failed: {e}")
            return self._fixed_size_chunking(text)
    
    def _ernie_semantic_chunking(self, text: str) -> List[str]:
        """使用ERNIE模型进行语义切分"""
        if not self.ernie_model:
            self.logger.warning("ERNIE model not available, falling back to paragraph chunking")
            return self._paragraph_based_chunking(text)
        
        try:
            # 首先按段落进行初步切分
            paragraphs = re.split(self.paragraph_separators, text)
            paragraphs = [p.strip() for p in paragraphs if p.strip()]
            
            if len(paragraphs) <= 1:
                return paragraphs
            
            # 计算段落间的语义相似度
            similarities = self._calculate_paragraph_similarities(paragraphs)
            
            # 基于相似度进行切分
            chunks = self._merge_paragraphs_by_similarity(paragraphs, similarities)
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"ERNIE semantic chunking failed: {e}")
            return self._paragraph_based_chunking(text)
    
    def _hybrid_smart_chunking(self, text: str) -> List[str]:
        """混合智能切分：结合LangChain和ERNIE"""
        try:
            # 第一步：使用LangChain进行初步切分
            if self.langchain_splitter:
                initial_chunks = self.langchain_splitter.split_text(text)
            else:
                initial_chunks = self._paragraph_based_chunking(text)
            
            # 第二步：使用ERNIE进行语义优化
            if self.ernie_model and len(initial_chunks) > 1:
                optimized_chunks = self._optimize_chunks_with_ernie(initial_chunks)
                return optimized_chunks
            else:
                return initial_chunks
                
        except Exception as e:
            self.logger.error(f"Hybrid smart chunking failed: {e}")
            return self._paragraph_based_chunking(text)
    
    def _calculate_paragraph_similarities(self, paragraphs: List[str]) -> List[float]:
        """计算段落间的语义相似度"""
        if len(paragraphs) < 2:
            return []
        
        try:
            # 使用ERNIE模型计算嵌入
            embeddings = self.ernie_model.encode(paragraphs, batch_size=self.config.batch_size)
            
            # 计算相邻段落的余弦相似度
            similarities = []
            for i in range(len(embeddings) - 1):
                similarity = np.dot(embeddings[i], embeddings[i + 1]) / (
                    np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[i + 1])
                )
                similarities.append(float(similarity))
            
            return similarities
            
        except Exception as e:
            self.logger.error(f"Failed to calculate paragraph similarities: {e}")
            return [0.5] * (len(paragraphs) - 1)  # 默认相似度
    
    def _merge_paragraphs_by_similarity(self, paragraphs: List[str], similarities: List[float]) -> List[str]:
        """根据相似度合并段落"""
        if not similarities:
            return paragraphs
        
        chunks = []
        current_chunk = paragraphs[0]
        
        for i, similarity in enumerate(similarities):
            if similarity >= self.config.semantic_similarity_threshold:
                # 相似度高，合并段落
                current_chunk += "\n\n" + paragraphs[i + 1]
            else:
                # 相似度低，开始新的chunk
                if len(current_chunk.strip()) >= self.config.min_chunk_size:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraphs[i + 1]
        
        # 添加最后一个chunk
        if len(current_chunk.strip()) >= self.config.min_chunk_size:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _optimize_chunks_with_ernie(self, chunks: List[str]) -> List[str]:
        """使用ERNIE优化chunks"""
        if len(chunks) <= 1:
            return chunks
        
        try:
            # 计算chunks间的相似度
            similarities = []
            for i in range(len(chunks) - 1):
                emb1 = self.ernie_model.encode([chunks[i]])
                emb2 = self.ernie_model.encode([chunks[i + 1]])
                similarity = np.dot(emb1[0], emb2[0]) / (
                    np.linalg.norm(emb1[0]) * np.linalg.norm(emb2[0])
                )
                similarities.append(float(similarity))
            
            # 合并相似度高的chunks
            optimized_chunks = []
            current_chunk = chunks[0]
            
            for i, similarity in enumerate(similarities):
                if (similarity >= self.config.semantic_similarity_threshold and 
                    len(current_chunk) + len(chunks[i + 1]) <= self.config.max_chunk_size):
                    # 合并chunks
                    current_chunk += "\n\n" + chunks[i + 1]
                else:
                    # 保存当前chunk，开始新的chunk
                    optimized_chunks.append(current_chunk.strip())
                    current_chunk = chunks[i + 1]
            
            # 添加最后一个chunk
            optimized_chunks.append(current_chunk.strip())
            
            return optimized_chunks
            
        except Exception as e:
            self.logger.error(f"Failed to optimize chunks with ERNIE: {e}")
            return chunks
    
    def _medical_structured_chunking(self, text: str) -> List[str]:
        """医疗结构化切分"""
        self.logger.info(f"使用医疗结构化切分策略，目标大小: {self.config.chunk_size}")
        
        chunks = []
        
        # 识别医疗文档结构
        sections = self._identify_medical_sections(text)
        self.logger.info(f"识别到 {len(sections)} 个医疗章节: {list(sections.keys())}")
        
        for section_name, section_content in sections.items():
            self.logger.debug(f"处理章节 '{section_name}': 长度 {len(section_content)} 字符")
            
            if len(section_content) <= self.config.chunk_size:
                # 如果章节内容不超过大小限制，直接作为一个chunk
                chunks.append(section_content)
                self.logger.debug(f"章节 '{section_name}' 直接作为片段: 长度 {len(section_content)}")
            else:
                # 如果章节内容过长，进一步切分
                self.logger.debug(f"章节 '{section_name}' 过长，进行子切分")
                sub_chunks = self._sentence_based_chunking(section_content)
                for i, sub_chunk in enumerate(sub_chunks):
                    # 为子chunk添加章节信息
                    chunk_with_section = f"[{section_name}] {sub_chunk}"
                    chunks.append(chunk_with_section)
                self.logger.debug(f"章节 '{section_name}' 切分为 {len(sub_chunks)} 个子片段")
        
        self.logger.info(f"医疗结构化切分完成，生成 {len(chunks)} 个片段")
        return chunks
    
    def _identify_medical_sections(self, text: str) -> Dict[str, str]:
        """识别医疗文档章节"""
        self.logger.debug("开始识别医疗文档章节")
        sections = {}
        current_section = "未知章节"
        current_content = ""
        section_count = 0
        
        lines = text.split('\n')
        self.logger.debug(f"分析 {len(lines)} 行文本")
        
        for line_num, line in enumerate(lines):
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
                        section_count += 1
                        self.logger.debug(f"完成章节 '{current_section}': 长度 {len(current_content.strip())}")
                    
                    # 开始新章节
                    current_section = section
                    current_content = ""
                    is_section_header = True
                    self.logger.debug(f"发现章节标题 '{section}' 在第 {line_num+1} 行")
                    break
            
            if not is_section_header:
                current_content += line + "\n"
        
        # 保存最后一个章节
        if current_content.strip():
            sections[current_section] = current_content.strip()
            section_count += 1
            self.logger.debug(f"完成最后章节 '{current_section}': 长度 {len(current_content.strip())}")
        
        self.logger.debug(f"医疗章节识别完成，共识别 {section_count} 个章节")
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
            # 避免在 embedding_service 下自动创建目录，仅当目录存在时才保存
            if not os.path.exists(output_dir):
                self.logger.warning(f"输出目录不存在，跳过保存: {output_dir}")
                return
            
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
    
    def load_vectorization_data(self, data_root_dir: str) -> List[Dict[str, Any]]:
        """
        从processed目录加载所有预处理数据（JSON格式）
        
        Args:
            data_root_dir: 数据根目录，包含text_data、image_text_data、voice_data
            
        Returns:
            统一格式的数据列表
        """
        all_data = []
        
        # 定义各数据类型的数据目录和文件
        data_configs = {
            'text': {
                'dir': os.path.join(data_root_dir, 'text_data', 'processed'),
                'file': 'text_documents.json'
            },
            'image_text': {
                'dir': os.path.join(data_root_dir, 'image_text_data', 'processed'),
                'file': 'image_text_documents.json'
            },
            'voice': {
                'dir': os.path.join(data_root_dir, 'voice_data', 'processed'),
                'file': 'voice_documents.json'
            }
        }
        
        for data_type, config in data_configs.items():
            data_dir = config['dir']
            json_file = config['file']
            json_path = os.path.join(data_dir, json_file)
            
            if os.path.exists(json_path):
                self.logger.info(f"📁 加载 {data_type} 数据: {json_path}")
                
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    self.logger.info(f"  ✅ 加载 {json_file}: {len(data)} 条记录")
                    
                    # 转换为统一格式
                    for item in data:
                        data_item = {
                            'id': item.get('id', 'unknown'),
                            'content': item.get('content', ''),
                            'type': data_type,
                            'metadata': {
                                'file_name': item.get('metadata', {}).get('file_name', ''),
                                'data_type': data_type,
                                'quality_score': item.get('metadata', {}).get('quality_score', 0.0),
                                'original_metadata': item.get('metadata', {})
                            }
                        }
                        
                        # 添加特定类型的元数据
                        if data_type == 'voice':
                            data_item['metadata']['voice_type'] = item.get('metadata', {}).get('voice_type', '')
                        elif data_type == 'image_text':
                            data_item['metadata']['image_type'] = item.get('metadata', {}).get('image_type', '')
                        
                        all_data.append(data_item)
                        
                except Exception as e:
                    self.logger.error(f"  ❌ 加载 {json_file} 失败: {e}")
            else:
                self.logger.warning(f"⚠️ 数据文件不存在: {json_path}")
        
        self.logger.info(f"🎉 数据加载完成，共加载 {len(all_data)} 条记录")
        return all_data
    
    def chunk_vectorization_data(self, data_root_dir: str, output_dir: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        切分processed目录中的所有数据
        
        Args:
            data_root_dir: 数据根目录
            output_dir: 输出目录
            
        Returns:
            切分结果
        """
        # 加载所有数据
        all_data = self.load_vectorization_data(data_root_dir)
        
        if not all_data:
            self.logger.warning("⚠️ 没有找到可切分的数据")
            return {}
        
        # 按数据类型分组切分
        results = {}
        data_by_type = {}
        
        # 按类型分组
        for item in all_data:
            data_type = item['type']
            if data_type not in data_by_type:
                data_by_type[data_type] = []
            data_by_type[data_type].append(item)
        
        # 分别切分每种类型的数据
        for data_type, items in data_by_type.items():
            self.logger.info(f"🔧 开始切分 {data_type} 数据，共 {len(items)} 条")
            
            type_chunks = []
            for item in items:
                chunks = self.chunk_document(item['content'], item['metadata'])
                type_chunks.extend(chunks)
            
            results[data_type] = type_chunks
            self.logger.info(f"✅ {data_type} 数据切分完成，生成 {len(type_chunks)} 个片段")
        
        # 保存切分结果
        self._save_vectorization_chunks(results, output_dir)
        
        return results
    
    def _save_vectorization_chunks(self, results: Dict[str, List[Dict[str, Any]]], output_dir: str):
        """保存vectorization数据的切分结果"""
        try:
            # 避免在 embedding_service 下自动创建目录，仅当目录存在时才保存
            if not os.path.exists(output_dir):
                self.logger.warning(f"输出目录不存在，跳过保存: {output_dir}")
                return
            
            # 保存每种类型的数据
            for data_type, chunks in results.items():
                output_file = os.path.join(output_dir, f"{data_type}_chunks.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(chunks, f, ensure_ascii=False, indent=2)
                self.logger.info(f"✅ {data_type} 切分结果已保存: {output_file}")
            
            # 保存合并的结果
            all_chunks = []
            for chunks in results.values():
                all_chunks.extend(chunks)
            
            merged_file = os.path.join(output_dir, "all_chunks.json")
            with open(merged_file, 'w', encoding='utf-8') as f:
                json.dump(all_chunks, f, ensure_ascii=False, indent=2)
            self.logger.info(f"✅ 合并切分结果已保存: {merged_file}")
            
        except Exception as e:
            self.logger.error(f"❌ 保存切分结果失败: {e}")


def create_medical_chunker() -> DocumentChunker:
    """创建医疗文档切分器"""
    config = ChunkConfig(
        strategy=ChunkStrategy.MEDICAL_STRUCTURED,
        chunk_size=256,  # 降低chunk大小以匹配Token限制
        chunk_overlap=25,
        min_chunk_size=20,  # 降低最小片段大小，保留更多医疗信息
        max_chunk_size=512,  # 降低最大chunk大小
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
        strategy=ChunkStrategy.LANGCHAIN_RECURSIVE,  # 使用LangChain递归切分，更适合长文本
        chunk_size=512,  # 增加chunk大小以处理长文本
        chunk_overlap=50,  # 增加重叠以保持上下文
        min_chunk_size=50,  # 增加最小片段大小
        max_chunk_size=1024,  # 增加最大chunk大小
        preserve_sentences=True,
        preserve_paragraphs=True
    )
    return DocumentChunker(config)


def create_langchain_chunker() -> DocumentChunker:
    """创建LangChain递归切分器"""
    config = ChunkConfig(
        strategy=ChunkStrategy.LANGCHAIN_RECURSIVE,
        chunk_size=512,
        chunk_overlap=50,
        min_chunk_size=20,
        max_chunk_size=1024,
        preserve_sentences=True,
        preserve_paragraphs=True
    )
    return DocumentChunker(config)


def create_ernie_semantic_chunker() -> DocumentChunker:
    """创建ERNIE语义切分器"""
    config = ChunkConfig(
        strategy=ChunkStrategy.ERNIE_SEMANTIC,
        chunk_size=512,
        chunk_overlap=50,
        min_chunk_size=20,
        max_chunk_size=1024,
        preserve_sentences=True,
        preserve_paragraphs=True,
        semantic_similarity_threshold=0.7,
        ernie_model_name="nghuyong/ernie-3.0-base-zh",
        use_gpu=True,
        batch_size=32
    )
    return DocumentChunker(config)


def create_hybrid_smart_chunker() -> DocumentChunker:
    """创建混合智能切分器"""
    config = ChunkConfig(
        strategy=ChunkStrategy.HYBRID_SMART,
        chunk_size=512,
        chunk_overlap=50,
        min_chunk_size=20,
        max_chunk_size=1024,
        preserve_sentences=True,
        preserve_paragraphs=True,
        semantic_similarity_threshold=0.7,
        ernie_model_name="nghuyong/ernie-3.0-base-zh",
        use_gpu=True,
        batch_size=32
    )
    return DocumentChunker(config)


class ChunkingTester:
    """文档切分测试器"""
    
    def __init__(self):
        self.test_logger = logging.getLogger('chunking_test')
        self.results = {}
    
    def run_comprehensive_test(self, test_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        运行综合切分测试
        
        Args:
            test_data: 测试数据，如果为None则使用默认测试数据
            
        Returns:
            测试结果字典
        """
        if test_data is None:
            test_data = self._load_default_test_data()
        
        self.test_logger.info("=" * 80)
        self.test_logger.info("🧪 开始新的文档切分测试运行")
        self.test_logger.info("=" * 80)
        self.test_logger.info("🎯 智诊通文档切分测试系统启动")
        self.test_logger.info(f"📁 项目根目录: {Path(__file__).parent.parent.parent.parent}")
        self.test_logger.info(f"📁 数据目录: {Path(__file__).parent.parent.parent.parent / 'datas' / 'medical_knowledge'}")
        self.test_logger.info("🚀 开始完整的文档切分测试...")
        
        # 测试所有策略
        strategies = [
            ("固定大小切分", ChunkStrategy.FIXED_SIZE),
            ("医疗结构化切分", ChunkStrategy.MEDICAL_STRUCTURED),
            ("LangChain递归切分", ChunkStrategy.LANGCHAIN_RECURSIVE),
            ("ERNIE语义切分", ChunkStrategy.ERNIE_SEMANTIC),
            ("混合智能切分", ChunkStrategy.HYBRID_SMART)
        ]
        
        results = {}
        
        for strategy_name, strategy in strategies:
            self.test_logger.info("")
            self.test_logger.info("=" * 60)
            self.test_logger.info(f"🧪 测试策略: {strategy_name}")
            self.test_logger.info("=" * 60)
            
            # 创建切分器
            config = ChunkConfig(strategy=strategy)
            chunker = DocumentChunker(config)
            
            # 测试切分
            result = self._test_strategy(test_data, strategy_name, chunker)
            results[strategy_name] = result
        
        # 生成报告
        self._generate_test_report(results)
        
        return results
    
    def _load_default_test_data(self) -> List[Dict[str, Any]]:
        """加载默认测试数据"""
        # 这里可以加载实际的医疗数据
        # 暂时使用模拟数据
        return [
            {
                "id": "test_1",
                "content": "患者男性，45岁，因胸痛3天入院。现病史：患者3天前无明显诱因出现胸痛，呈持续性钝痛，伴胸闷、气短。",
                "type": "text",
                "metadata": {"source": "test"}
            }
        ]
    
    def _test_strategy(self, test_data: List[Dict[str, Any]], 
                      strategy_name: str, chunker: DocumentChunker) -> Dict[str, Any]:
        """测试单个策略"""
        import time
        
        self.test_logger.info(f"🔧 测试 {strategy_name} 切分策略...")
        
        start_time = time.time()
        total_chunks = 0
        chunks_by_type = {}
        sample_chunks = []
        
        for item in test_data:
            content = item.get('content', '')
            data_type = item.get('type', 'text')
            
            self.test_logger.info(f"  📝 处理 {data_type} 数据: {item.get('id', 'unknown')}")
            
            # 切分文档
            chunks = chunker.chunk_document(content, item.get('metadata', {}))
            
            # 统计
            chunk_count = len(chunks)
            total_chunks += chunk_count
            chunks_by_type[data_type] = chunks_by_type.get(data_type, 0) + chunk_count
            
            # 保存样本
            for chunk in chunks[:2]:  # 只保存前2个样本
                sample_chunks.append({
                    'type': data_type,
                    'content': chunk.get('content', '')[:100] + '...' if len(chunk.get('content', '')) > 100 else chunk.get('content', ''),
                    'length': chunk.get('length', 0)
                })
            
            self.test_logger.info(f"    ✅ 生成 {chunk_count} 个chunks")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 计算平均大小
        avg_chunk_size = sum(chunk.get('length', 0) for chunk in sample_chunks) / len(sample_chunks) if sample_chunks else 0
        
        result = {
            'total_chunks': total_chunks,
            'avg_chunk_size': avg_chunk_size,
            'processing_time': processing_time,
            'chunks_by_type': chunks_by_type,
            'sample_chunks': sample_chunks
        }
        
        self.test_logger.info(f"  ✅ {strategy_name} 完成: {total_chunks} 个chunks, 平均大小 {avg_chunk_size:.1f} 字符, 耗时 {processing_time:.2f}s")
        
        return result
    
    def _generate_test_report(self, results: Dict[str, Any]):
        """生成测试报告"""
        self.test_logger.info("")
        self.test_logger.info("=" * 80)
        self.test_logger.info("📋 切分测试报告")
        self.test_logger.info("=" * 80)
        
        # 按总chunks数排序
        sorted_results = sorted(results.items(), key=lambda x: x[1]['total_chunks'], reverse=True)
        
        # 表头
        self.test_logger.info(f"{'策略名称':<20} {'总Chunks':<10} {'平均大小':<10} {'处理时间':<10} {'各类型分布'}")
        self.test_logger.info("-" * 80)
        
        # 结果行
        for strategy_name, result in sorted_results:
            chunks_by_type_str = ', '.join([f"{k}:{v}" for k, v in result['chunks_by_type'].items()])
            self.test_logger.info(f"{strategy_name:<20} {result['total_chunks']:<10} {result['avg_chunk_size']:.1f}      {result['processing_time']:.2f}      s {chunks_by_type_str}")
        
        # 详细分析
        self.test_logger.info(f"\n📊 详细分析:")
        for strategy_name, result in sorted_results:
            self.test_logger.info(f"\n🔍 {strategy_name}:")
            self.test_logger.info(f"  - 总chunks: {result['total_chunks']}")
            self.test_logger.info(f"  - 平均chunk大小: {result['avg_chunk_size']:.1f} 字符")
            self.test_logger.info(f"  - 处理时间: {result['processing_time']:.2f} 秒")
            self.test_logger.info(f"  - 各类型分布: {result['chunks_by_type']}")
            
            if result['sample_chunks']:
                self.test_logger.info(f"  - 样本chunks:")
                for i, chunk in enumerate(result['sample_chunks'][:2]):
                    self.test_logger.info(f"    {i+1}. [{chunk['type']}] {chunk['content']}")
        
        # 保存结果
        self._save_test_results(results)
        self.test_logger.info("🎉 测试完成!")
    
    def _save_test_results(self, results: Dict[str, Any]):
        """保存测试结果"""
        import json
        
        results_file = Path(__file__).parent.parent.parent.parent / "codes" / "logs" / "chunking_test_results.json"
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            self.test_logger.info(f"💾 测试结果已保存到: {results_file}")
        except Exception as e:
            self.test_logger.error(f"❌ 保存结果失败: {str(e)}")


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
    
    logger.info("=" * 60)
    logger.info("文档切分功能测试")
    logger.info("=" * 60)
    
    # 测试医疗结构化切分
    logger.info("\n1. 医疗结构化切分:")
    medical_chunker = create_medical_chunker()
    chunks = medical_chunker.chunk_document(test_text)
    for i, chunk in enumerate(chunks):
        logger.info(f"  Chunk {i+1}: {chunk['content'][:50]}... (长度: {chunk['length']})")
        if 'section' in chunk:
            logger.info(f"    章节: {chunk['section']}")
    
    # 测试通用切分
    logger.info(f"\n2. 通用切分: 共 {len(chunks)} 个片段")
    
    # 测试LangChain递归切分
    logger.info("\n3. LangChain递归切分:")
    try:
        langchain_chunker = create_langchain_chunker()
        chunks = langchain_chunker.chunk_document(test_text)
        for i, chunk in enumerate(chunks):
            logger.info(f"  Chunk {i+1}: {chunk[:50]}... (长度: {len(chunk)})")
    except Exception as e:
        logger.error(f"  LangChain切分失败: {e}")
    
    # 测试ERNIE语义切分
    logger.info("\n4. ERNIE语义切分:")
    try:
        ernie_chunker = create_ernie_semantic_chunker()
        chunks = ernie_chunker.chunk_document(test_text)
        for i, chunk in enumerate(chunks):
            logger.info(f"  Chunk {i+1}: {chunk[:50]}... (长度: {len(chunk)})")
    except Exception as e:
        logger.error(f"  ERNIE切分失败: {e}")
    
    # 测试混合智能切分
    logger.info("\n5. 混合智能切分:")
    try:
        hybrid_chunker = create_hybrid_smart_chunker()
        chunks = hybrid_chunker.chunk_document(test_text)
        for i, chunk in enumerate(chunks):
            logger.info(f"  Chunk {i+1}: {chunk[:50]}... (长度: {len(chunk)})")
    except Exception as e:
        logger.error(f"  混合智能切分失败: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)
