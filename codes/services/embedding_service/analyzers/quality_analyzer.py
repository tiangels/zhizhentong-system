#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗数据质量检查器
实现完整性、唯一性、相关性和向量化前置检查
"""

import os
import re
import hashlib
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter
import jieba
import json
from datetime import datetime

# 导入配置管理器
from config.config_manager import get_config, get_model_path

# 可选依赖
try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False
    print("Warning: chardet not available, encoding detection disabled")

# 第三方库导入（可选）
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Warning: sentence-transformers not available, semantic similarity check disabled")

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers not available, semantic filtering disabled")

try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: sklearn not available, using alternative similarity calculation")

class QualityAnalyzer:
    """医疗数据质量检查器"""
    
    def __init__(self, data_dir: str, config: Optional[Dict] = None, log_dir: Optional[str] = None):
        """
        初始化质量检查器
        
        Args:
            data_dir: 数据目录路径
            config: 配置参数
            log_dir: 日志目录路径（可选）
        """
        self.data_dir = Path(data_dir)
        self.config = self._load_config(config)
        self.log_dir = log_dir
        self.logger = self._setup_logging()
        
        # 初始化模型（延迟加载）
        self.sentence_model = None
        self.classifier_model = None
        self.classifier_tokenizer = None
        self.vectorizer_tokenizer = None
        
        # 统计信息
        self.stats = {
            'total_texts': 0,
            'completeness_passed': 0,
            'uniqueness_passed': 0,
            'relevance_passed': 0,
            'vectorization_passed': 0,
            'final_passed': 0,
            'filtered_reasons': Counter()
        }
        
        # 质量检查历史记录
        self.quality_history = []
        self.stage_stats = {
            'completeness': {'passed': 0, 'failed': 0, 'reasons': Counter()},
            'uniqueness': {'passed': 0, 'failed': 0, 'reasons': Counter()},
            'relevance': {'passed': 0, 'failed': 0, 'reasons': Counter()},
            'vectorization': {'passed': 0, 'failed': 0, 'reasons': Counter()}
        }
        
        # 创建统计存储目录
        self.stats_dir = self.data_dir / "quality_stats"
        self.stats_dir.mkdir(exist_ok=True)
        
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            # 完整性检查参数
            'min_length': 10,  # 最小文本长度
            'max_length_ratio': 1.2,  # 最大长度比例（相对于模型最大token数）
            'model_max_tokens': 512,  # 模型最大token数（适合文档片段长度）
            
            # 唯一性检查参数
            'semantic_similarity_threshold': 0.95,  # 语义相似度阈值
            'batch_size': 32,  # 批处理大小
            
            # 相关性检查参数
            'irrelevant_keywords': ['金融', '游戏', '娱乐', '体育', '政治', '军事', '科技'],
            'special_char_ratio_threshold': 0.3,  # 特殊字符比例阈值
            'medical_keywords': ['疾病', '症状', '治疗', '诊断', '药物', '医院', '医生', '患者', '健康', '医疗'],
            
            # 向量化检查参数
            'encoding': 'utf-8',
            'token_overhead': 10,  # token开销（用于特殊token）
            
            # 模型配置
            'semantic_model_name': 'paraphrase-multilingual-MiniLM-L12-v2',  # 语义相似度模型
            'classifier_model_name': 'distilbert-base-multilingual-cased',  # 文本分类模型
            'embedding_model_name': 'microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224',  # 向量化模型
        }
    
    def _load_config(self, config: Optional[Dict] = None) -> Dict:
        """加载配置，支持从文件加载"""
        if config is not None:
            return config
        
        # 尝试从配置文件加载
        try:
            config_path = self.data_dir.parent.parent.parent / "ai_models" / "embedding_models" / "config" / "embed_config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                
                # 合并配置
                default_config = self._get_default_config()
                if 'quality_analyzer' in file_config:
                    default_config.update(file_config['quality_analyzer'])
                
                # 从模型配置中获取模型信息
                if 'models' in file_config:
                    models_config = file_config['models']
                    if 'text_embedding' in models_config:
                        embedding_config = models_config['text_embedding']
                        default_config['embedding_model_name'] = embedding_config.get('model_name', default_config['embedding_model_name'])
                        default_config['embedding_model_path'] = embedding_config.get('model_path')
                
                self.logger.info("已从配置文件加载质量分析器配置")
                return default_config
        except Exception as e:
            self.logger.warning(f"配置文件加载失败: {e}")
        
        # 返回默认配置
        return self._get_default_config()
        
    def _setup_logging(self) -> logging.Logger:
        """设置日志 - 使用统一的日志系统"""
        import sys
        from pathlib import Path
        
        # 添加common模块到路径
        current_file = Path(__file__)
        common_dir = current_file.parent.parent.parent.parent / "common"
        sys.path.insert(0, str(common_dir))
        
        from log_config import setup_service_logging
        
        # 使用统一的日志管理器
        return setup_service_logging("quality_check_analysis")
    
    def _load_models(self):
        """延迟加载模型"""
        if SENTENCE_TRANSFORMERS_AVAILABLE and self.sentence_model is None:
            try:
                # 优先使用本地模型路径
                model_path = self._get_semantic_model_path()
                self.sentence_model = SentenceTransformer(model_path)
                self.logger.info(f"语义相似度模型加载成功: {model_path}")
            except Exception as e:
                self.logger.warning(f"语义相似度模型加载失败: {e}")
                self.sentence_model = None
        
        if TRANSFORMERS_AVAILABLE and self.classifier_model is None:
            try:
                # 优先使用本地模型路径
                model_path = self._get_classifier_model_path()
                self.classifier_tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.classifier_model = AutoModelForSequenceClassification.from_pretrained(
                    model_path, num_labels=2
                )
                self.logger.info(f"文本分类模型加载成功: {model_path}")
            except Exception as e:
                self.logger.warning(f"文本分类模型加载失败: {e}")
                self.classifier_model = None
                self.classifier_tokenizer = None
    
    def _load_vectorizer_tokenizer(self):
        """加载向量化模型的tokenizer"""
        if self.vectorizer_tokenizer is None:
            try:
                # 尝试从配置中获取模型路径
                model_path = self._get_embedding_model_path()
                self.vectorizer_tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.logger.info(f"向量化tokenizer加载成功: {model_path}")
            except Exception as e:
                self.logger.warning(f"向量化tokenizer加载失败: {e}")
                self.vectorizer_tokenizer = None
    
    def _get_embedding_model_path(self) -> str:
        """获取向量化模型路径"""
        try:
            # 使用配置管理器获取模型路径
            return get_model_path("text_embedding")
        except Exception as e:
            self.logger.warning(f"获取嵌入模型路径失败: {e}")
            # 回退到配置中的模型名称
            return self.config.get('embedding_model_name', 'microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224')
    
    def _get_semantic_model_path(self) -> str:
        """获取语义相似度模型路径"""
        try:
            # 使用配置管理器获取模型路径
            return get_model_path("semantic_model")
        except Exception as e:
            self.logger.warning(f"获取语义模型路径失败: {e}")
            # 回退到配置中的模型名称
            return self.config.get('semantic_model_name', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    
    def _get_classifier_model_path(self) -> str:
        """获取分类模型路径"""
        try:
            # 使用配置管理器获取模型路径
            return get_model_path("classifier_model")
        except Exception as e:
            self.logger.warning(f"获取分类模型路径失败: {e}")
            # 回退到配置中的模型名称
            return self.config.get('classifier_model_name', 'distilbert/distilbert-base-multilingual-cased')
    
    def check_completeness(self, text: str) -> Tuple[bool, str]:
        """
        完整性检查
        
        Args:
            text: 待检查的文本
            
        Returns:
            (是否通过, 失败原因)
        """
        if not isinstance(text, str):
            self._record_stage_result('completeness', False, "非字符串类型")
            return False, "非字符串类型"
        
        # 去除首尾空白
        text = text.strip()
        
        # 检查是否为空或仅含标点
        if len(text) == 0:
            self._record_stage_result('completeness', False, "空白文本")
            return False, "空白文本"
        
        # 检查是否仅含标点符号
        if re.match(r'^[^\w\u4e00-\u9fff]+$', text):
            self._record_stage_result('completeness', False, "仅含标点符号")
            return False, "仅含标点符号"
        
        # 检查长度
        if len(text) < self.config['min_length']:
            reason = f"文本过短 (长度: {len(text)}, 最小要求: {self.config['min_length']})"
            self._record_stage_result('completeness', False, reason)
            return False, reason
        
        # 检查是否过长（基于字符数估算）
        max_chars = int(self.config['model_max_tokens'] * self.config['max_length_ratio'] * 2)  # 粗略估算
        if len(text) > max_chars:
            reason = f"文本过长 (长度: {len(text)}, 最大允许: {max_chars})"
            self._record_stage_result('completeness', False, reason)
            return False, reason
        
        self._record_stage_result('completeness', True, "")
        return True, ""
    
    def check_uniqueness(self, texts: List[str]) -> Tuple[List[bool], Dict[str, int]]:
        """
        唯一性检查
        
        Args:
            texts: 待检查的文本列表
            
        Returns:
            (通过列表, 重复组信息)
        """
        n = len(texts)
        passed = [True] * n
        duplicate_groups = {}
        
        # 1. 基于哈希的精确去重
        text_hashes = {}
        for i, text in enumerate(texts):
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            if text_hash in text_hashes:
                passed[i] = False
                duplicate_groups[text_hash] = duplicate_groups.get(text_hash, 0) + 1
                self.stats['filtered_reasons']['哈希重复'] += 1
            else:
                text_hashes[text_hash] = i
        
        # 2. 基于语义相似度的去重（如果模型可用）
        if SENTENCE_TRANSFORMERS_AVAILABLE and self.sentence_model is not None:
            try:
                self._load_models()
                if self.sentence_model is not None:
                    # 只对通过哈希检查的文本进行语义相似度检查
                    valid_indices = [i for i, p in enumerate(passed) if p]
                    valid_texts = [texts[i] for i in valid_indices]
                    
                    if len(valid_texts) > 1:
                        # 计算语义相似度
                        embeddings = self.sentence_model.encode(valid_texts, batch_size=self.config['batch_size'])
                        
                        # 计算相似度矩阵
                        if SKLEARN_AVAILABLE:
                            similarity_matrix = cosine_similarity(embeddings)
                        else:
                            # 使用numpy计算余弦相似度
                            import numpy as np
                            normalized_embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
                            similarity_matrix = np.dot(normalized_embeddings, normalized_embeddings.T)
                        
                        # 标记相似度超过阈值的文本
                        for i in range(len(valid_texts)):
                            for j in range(i + 1, len(valid_texts)):
                                if similarity_matrix[i][j] > self.config['semantic_similarity_threshold']:
                                    # 保留第一个，标记后续为重复
                                    original_idx = valid_indices[j]
                                    passed[original_idx] = False
                                    duplicate_groups[f"语义相似_{i}_{j}"] = duplicate_groups.get(f"语义相似_{i}_{j}", 0) + 1
                                    self.stats['filtered_reasons']['语义重复'] += 1
            except Exception as e:
                self.logger.warning(f"语义相似度检查失败: {e}")
        
        return passed, duplicate_groups
    
    def check_relevance(self, text: str) -> Tuple[bool, str]:
        """
        相关性检查
        
        Args:
            text: 待检查的文本
            
        Returns:
            (是否通过, 失败原因)
        """
        if not isinstance(text, str):
            self._record_stage_result('relevance', False, "非字符串类型")
            return False, "非字符串类型"
        
        text = text.strip()
        
        # 1. 关键词过滤
        irrelevant_keywords = self.config['irrelevant_keywords']
        for keyword in irrelevant_keywords:
            if keyword in text:
                reason = f"包含无关关键词: {keyword}"
                self._record_stage_result('relevance', False, reason)
                return False, reason
        
        # 2. 检查特殊字符比例
        special_chars = re.findall(r'[^\w\u4e00-\u9fff\s]', text)
        special_char_ratio = len(special_chars) / len(text) if len(text) > 0 else 0
        
        if special_char_ratio > self.config['special_char_ratio_threshold']:
            reason = f"特殊字符比例过高: {special_char_ratio:.2%}"
            self._record_stage_result('relevance', False, reason)
            return False, reason
        
        # 3. 检查是否包含医疗相关关键词（可选）
        medical_keywords = self.config['medical_keywords']
        has_medical_content = any(keyword in text for keyword in medical_keywords)
        
        # 如果文本很短且不包含医疗关键词，可能不相关
        if len(text) < 50 and not has_medical_content:
            reason = "文本过短且不包含医疗相关内容"
            self._record_stage_result('relevance', False, reason)
            return False, reason
        
        # 4. 语义分类（如果模型可用）
        if TRANSFORMERS_AVAILABLE and self.classifier_model is not None:
            try:
                self._load_models()
                if self.classifier_model is not None and self.classifier_tokenizer is not None:
                    # 使用分类模型判断文本是否与医疗相关
                    inputs = self.classifier_tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
                    with torch.no_grad():
                        outputs = self.classifier_model(**inputs)
                        predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                        # 这里需要根据具体模型调整，假设0表示不相关，1表示相关
                        relevance_score = predictions[0][1].item()
                        if relevance_score < 0.5:  # 阈值可调整
                            reason = f"语义分类不相关 (得分: {relevance_score:.3f})"
                            self._record_stage_result('relevance', False, reason)
                            return False, reason
            except Exception as e:
                self.logger.warning(f"语义分类检查失败: {e}")
        
        self._record_stage_result('relevance', True, "")
        return True, ""
    
    def check_vectorization_readiness(self, text: str) -> Tuple[bool, str]:
        """
        向量化前置检查
        
        Args:
            text: 待检查的文本
            
        Returns:
            (是否通过, 失败原因)
        """
        if not isinstance(text, str):
            self._record_stage_result('vectorization', False, "非字符串类型")
            return False, "非字符串类型"
        
        # 1. 检查文本编码
        try:
            text.encode(self.config['encoding'])
        except UnicodeEncodeError:
            reason = f"文本编码错误，无法编码为{self.config['encoding']}"
            self._record_stage_result('vectorization', False, reason)
            return False, reason
        
        # 2. 检测文本编码
        if CHARDET_AVAILABLE:
            try:
                detected = chardet.detect(text.encode())
                if detected['encoding'] and detected['encoding'].lower() != 'utf-8':
                    self.logger.warning(f"检测到非UTF-8编码: {detected['encoding']}")
            except Exception as e:
                self.logger.warning(f"编码检测失败: {e}")
        else:
            self.logger.debug("chardet不可用，跳过编码检测")
        
        # 3. 预计算Token数量
        try:
            self._load_vectorizer_tokenizer()
            if self.vectorizer_tokenizer is not None:
                tokens = self.vectorizer_tokenizer.encode(text, add_special_tokens=True)
                token_count = len(tokens)
                max_tokens = self.config['model_max_tokens']
                
                if token_count > max_tokens:
                    reason = f"Token数量超限 (当前: {token_count}, 最大: {max_tokens})"
                    self._record_stage_result('vectorization', False, reason)
                    return False, reason
                
                # 检查是否需要重新切分
                if token_count > max_tokens * 0.8:  # 80%阈值
                    self.logger.info(f"文本接近Token上限，建议重新切分 (Token数: {token_count})")
            else:
                # 如果无法加载tokenizer，使用字符数估算
                estimated_tokens = len(text) // 2  # 粗略估算
                max_tokens = self.config['model_max_tokens']
                if estimated_tokens > max_tokens:
                    reason = f"估算Token数量超限 (估算: {estimated_tokens}, 最大: {max_tokens})"
                    self._record_stage_result('vectorization', False, reason)
                    return False, reason
        except Exception as e:
            self.logger.warning(f"Token计算失败: {e}")
        
        self._record_stage_result('vectorization', True, "")
        return True, ""
    
    def analyze_text_quality(self, texts: List[str]) -> Dict:
        """
        分析文本质量
        
        Args:
            texts: 待分析的文本列表
            
        Returns:
            质量分析结果
        """
        self.logger.info(f"开始分析 {len(texts)} 个文本的质量")
        
        # 重置统计信息
        self.stats = {
            'total_texts': len(texts),
            'completeness_passed': 0,
            'uniqueness_passed': 0,
            'relevance_passed': 0,
            'vectorization_passed': 0,
            'final_passed': 0,
            'filtered_reasons': Counter()
        }
        
        results = []
        valid_texts = []
        
        # 1. 完整性检查
        self.logger.info("执行完整性检查...")
        for i, text in enumerate(texts):
            passed, reason = self.check_completeness(text)
            if passed:
                self.stats['completeness_passed'] += 1
                valid_texts.append(text)
            else:
                self.stats['filtered_reasons'][reason] += 1
            
            results.append({
                'index': i,
                'text': text,
                'completeness_passed': passed,
                'completeness_reason': reason
            })
        
        # 2. 唯一性检查
        if valid_texts:
            self.logger.info("执行唯一性检查...")
            uniqueness_passed, duplicate_groups = self.check_uniqueness(valid_texts)
            
            # 更新结果
            valid_idx = 0
            for i, result in enumerate(results):
                if result['completeness_passed']:
                    result['uniqueness_passed'] = uniqueness_passed[valid_idx]
                    if uniqueness_passed[valid_idx]:
                        self.stats['uniqueness_passed'] += 1
                    else:
                        self.stats['filtered_reasons']['重复文本'] += 1
                    valid_idx += 1
                else:
                    result['uniqueness_passed'] = False
                    result['uniqueness_reason'] = "未通过完整性检查"
        
        # 3. 相关性检查
        self.logger.info("执行相关性检查...")
        for result in results:
            if result['completeness_passed'] and result.get('uniqueness_passed', True):
                passed, reason = self.check_relevance(result['text'])
                result['relevance_passed'] = passed
                result['relevance_reason'] = reason
                if passed:
                    self.stats['relevance_passed'] += 1
                else:
                    self.stats['filtered_reasons'][reason] += 1
            else:
                result['relevance_passed'] = False
                result['relevance_reason'] = "未通过前置检查"
        
        # 4. 向量化前置检查
        self.logger.info("执行向量化前置检查...")
        for result in results:
            if (result['completeness_passed'] and 
                result.get('uniqueness_passed', True) and 
                result.get('relevance_passed', True)):
                passed, reason = self.check_vectorization_readiness(result['text'])
                result['vectorization_passed'] = passed
                result['vectorization_reason'] = reason
                if passed:
                    self.stats['vectorization_passed'] += 1
                    self.stats['final_passed'] += 1
                else:
                    self.stats['filtered_reasons'][reason] += 1
            else:
                result['vectorization_passed'] = False
                result['vectorization_reason'] = "未通过前置检查"
        
        # 生成分析报告
        analysis_result = {
            'statistics': self.stats,
            'results': results,
            'duplicate_groups': duplicate_groups if 'duplicate_groups' in locals() else {},
            'summary': self._generate_summary()
        }
        
        self.logger.info("质量分析完成")
        return analysis_result
    
    def _generate_summary(self) -> Dict:
        """生成分析摘要"""
        total = self.stats['total_texts']
        return {
            'total_texts': total,
            'completeness_rate': f"{self.stats['completeness_passed']/total*100:.2f}%" if total > 0 else "0%",
            'uniqueness_rate': f"{self.stats['uniqueness_passed']/total*100:.2f}%" if total > 0 else "0%",
            'relevance_rate': f"{self.stats['relevance_passed']/total*100:.2f}%" if total > 0 else "0%",
            'vectorization_rate': f"{self.stats['vectorization_passed']/total*100:.2f}%" if total > 0 else "0%",
            'final_pass_rate': f"{self.stats['final_passed']/total*100:.2f}%" if total > 0 else "0%",
            'top_filter_reasons': dict(self.stats['filtered_reasons'].most_common(5))
        }
    
    def save_analysis_report(self, analysis_result: Dict, output_path: Optional[str] = None):
        """保存分析报告"""
        if output_path is None:
            output_path = self.data_dir / "quality_analysis_report.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"分析报告已保存: {output_path}")
    
    def get_clean_texts(self, analysis_result: Dict) -> List[str]:
        """获取通过所有检查的清洁文本"""
        clean_texts = []
        for result in analysis_result['results']:
            if (result['completeness_passed'] and 
                result.get('uniqueness_passed', True) and 
                result.get('relevance_passed', True) and 
                result.get('vectorization_passed', True)):
                clean_texts.append(result['text'])
        
        return clean_texts
    
    def _record_stage_result(self, stage: str, passed: bool, reason: str):
        """
        记录阶段检查结果
        
        Args:
            stage: 检查阶段
            passed: 是否通过
            reason: 失败原因
        """
        if stage in self.stage_stats:
            if passed:
                self.stage_stats[stage]['passed'] += 1
            else:
                self.stage_stats[stage]['failed'] += 1
                if reason:
                    self.stage_stats[stage]['reasons'][reason] += 1
        
        # 记录到历史
        self.quality_history.append({
            'timestamp': datetime.now().isoformat(),
            'stage': stage,
            'passed': passed,
            'reason': reason
        })
    
    def save_quality_stats(self, output_path: Optional[str] = None):
        """
        保存质量检查统计数据
        
        Args:
            output_path: 输出文件路径
        """
        if output_path is None:
            output_path = self.stats_dir / "quality_stats.json"
        
        stats_data = {
            'timestamp': datetime.now().isoformat(),
            'overall_stats': self.stats,
            'stage_stats': self.stage_stats,
            'quality_history': self.quality_history[-1000:],  # 只保存最近1000条记录
            'config': self.config
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"质量检查统计数据已保存: {output_path}")
    
    def load_quality_stats(self, stats_file: str = None) -> Dict:
        """
        加载质量检查统计数据
        
        Args:
            stats_file: 统计文件路径
            
        Returns:
            统计数据
        """
        if stats_file is None:
            stats_file = self.stats_dir / "quality_stats.json"
        
        if not Path(stats_file).exists():
            self.logger.warning(f"质量统计文件不存在: {stats_file}")
            return {}
        
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats_data = json.load(f)
            
            # 恢复统计数据
            if 'overall_stats' in stats_data:
                self.stats.update(stats_data['overall_stats'])
            if 'stage_stats' in stats_data:
                self.stage_stats.update(stats_data['stage_stats'])
            if 'quality_history' in stats_data:
                self.quality_history = stats_data['quality_history']
            
            self.logger.info(f"质量检查统计数据已加载: {stats_file}")
            return stats_data
        except Exception as e:
            self.logger.error(f"加载质量检查统计数据失败: {e}")
            return {}
    
    def get_quality_summary(self) -> Dict:
        """
        获取质量检查摘要
        
        Returns:
            质量检查摘要
        """
        total = self.stats['total_texts']
        if total == 0:
            return {"error": "没有质量检查数据"}
        
        summary = {
            'total_texts': total,
            'completeness_rate': f"{self.stats['completeness_passed']/total*100:.2f}%",
            'uniqueness_rate': f"{self.stats['uniqueness_passed']/total*100:.2f}%",
            'relevance_rate': f"{self.stats['relevance_passed']/total*100:.2f}%",
            'vectorization_rate': f"{self.stats['vectorization_passed']/total*100:.2f}%",
            'final_pass_rate': f"{self.stats['final_passed']/total*100:.2f}%",
            'top_filter_reasons': dict(self.stats['filtered_reasons'].most_common(5)),
            'stage_breakdown': {}
        }
        
        # 各阶段详细统计
        for stage, stats in self.stage_stats.items():
            stage_total = stats['passed'] + stats['failed']
            if stage_total > 0:
                summary['stage_breakdown'][stage] = {
                    'passed': stats['passed'],
                    'failed': stats['failed'],
                    'pass_rate': f"{stats['passed']/stage_total*100:.2f}%",
                    'top_failure_reasons': dict(stats['reasons'].most_common(3))
                }
        
        return summary


def main():
    """主函数示例"""
    # 示例用法
    data_dir = "medical_knowledge"
    analyzer = QualityAnalyzer(data_dir)
    
    # 示例文本
    sample_texts = [
        "患者出现发热、咳嗽等症状，建议进行血常规检查。",
        "这是一个关于金融投资的文章。",  # 应该被过滤
        "",  # 空白文本，应该被过滤
        "!!!@@@###",  # 仅标点，应该被过滤
        "感冒",  # 过短，应该被过滤
        "患者出现发热、咳嗽等症状，建议进行血常规检查。"  # 重复文本
    ]
    
    # 执行质量分析
    result = analyzer.analyze_text_quality(sample_texts)
    
    # 打印摘要
    print("\n=== 质量分析摘要 ===")
    for key, value in result['summary'].items():
        print(f"{key}: {value}")
    
    # 保存报告
    analyzer.save_analysis_report(result)
    
    # 获取清洁文本
    clean_texts = analyzer.get_clean_texts(result)
    print(f"\n通过所有检查的文本数量: {len(clean_texts)}")


if __name__ == "__main__":
    main()
