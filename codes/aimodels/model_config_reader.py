#!/usr/bin/env python3
"""
统一模型管理器
管理项目中的核心模型，包括配置读取、模型下载、状态检查等功能
"""

import os
import sys
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import requests
from tqdm import tqdm
from huggingface_hub import snapshot_download

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ModelConfigReader:
    """统一模型管理器类"""
    
    def __init__(self, config_path: str = None, base_dir: str = None):
        """
        初始化统一模型管理器
        
        Args:
            config_path: 配置文件路径，默认为当前目录下的model_config.json
            base_dir: 模型存储基础目录，默认为当前目录
        """
        if config_path is None:
            current_dir = Path(__file__).parent
            config_path = current_dir / "model_config.json"
        
        self.config_path = str(config_path)
        self.config = self._load_config()
        
        # 设置模型存储基础目录
        if base_dir is None:
            self.base_dir = Path(__file__).parent
        else:
            self.base_dir = Path(base_dir)
        
        # 确保基础目录存在
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 核心模型配置
        self.models_config = {
            "BiomedCLIP-PubMedBERT_256-vit_base_patch16_224": {
                "type": "multimodal_embedding",
                "huggingface_id": "microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224",
                "description": "多模态向量化模型-用于数据向量化",
                "vector_dim": 512,
                "supports": ["text", "image"],
                "required_files": [
                    "config.json",
                    "preprocessor_config.json", 
                    "pytorch_model.bin",
                    "tokenizer.json",
                    "tokenizer_config.json",
                    "vocab.txt"
                ]
            },
            "whisper-tiny": {
                "type": "voice_to_text",
                "huggingface_id": "openai/whisper-tiny",
                "description": "语音转文本模型-用于语音识别",
                "supports": ["audio"],
                "sample_rate": 16000,
                "required_files": [
                    "config.json",
                    "preprocessor_config.json",
                    "pytorch_model.bin",
                    "tokenizer.json",
                    "tokenizer_config.json",
                    "vocab.json"
                ]
            },
            "Apollo-0.5B": {
                "type": "text_generation",
                "huggingface_id": "FreedomIntelligence/Apollo-0.5B",
                "description": "大语言模型-用于生成用户问题的答案",
                "supports": ["text"],
                "max_length": 2048,
                "required_files": [
                    "config.json",
                    "generation_config.json",
                    "pytorch_model.bin",
                    "tokenizer.json",
                    "tokenizer_config.json",
                    "vocab.txt"
                ]
            },
            "Falconsai_text_summarization": {
                "type": "text_summarization",
                "huggingface_id": "Falconsai/text_summarization",
                "description": "文本摘要模型-用于文本摘要",
                "supports": ["text"],
                "required_files": [
                    "config.json",
                    "generation_config.json",
                    "pytorch_model.bin",
                    "tokenizer.json",
                    "tokenizer_config.json",
                    "vocab.txt"
                ]
            },
            "paraphrase-multilingual-MiniLM-L12-v2": {
                "type": "quality_analysis",
                "huggingface_id": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "description": "质量分析模型-用于文本质量评估和相似度计算",
                "supports": ["text"],
                "vector_dim": 384,
                "required_files": [
                    "config.json",
                    "config_sentence_transformers.json",
                    "model.safetensors",
                    "tokenizer.json",
                    "tokenizer_config.json",
                    "vocab.txt"
                ]
            },
            "distilbert-base-multilingual-cased": {
                "type": "classifier",
                "huggingface_id": "distilbert/distilbert-base-multilingual-cased",
                "description": "文本分类模型-用于文本分类和质量评估",
                "supports": ["text"],
                "required_files": [
                    "config.json",
                    "pytorch_model.bin",
                    "tokenizer.json",
                    "tokenizer_config.json",
                    "vocab.txt"
                ]
            },
            "ernie-3.0-base-zh": {
                "type": "semantic_chunking",
                "huggingface_id": "nghuyong/ernie-3.0-base-zh",
                "description": "ERNIE语义切分模型-用于文档语义切分和相似度计算",
                "supports": ["text"],
                "max_length": 512,
                "vector_dim": 768,
                "required_files": [
                    "config.json",
                    "pytorch_model.bin",
                    "tokenizer.json",
                    "tokenizer_config.json",
                    "vocab.txt"
                ]
            }
        }
        
        # 加载模型状态配置
        self.model_status_path = self.base_dir / "model_status.json"
        self.model_status = self._load_model_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载模型配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"成功加载模型配置文件: {self.config_path}")
                return config
            else:
                logger.warning(f"模型配置文件不存在: {self.config_path}")
                return {}
        except Exception as e:
            logger.error(f"加载模型配置文件失败: {e}")
            return {}
    
    def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """
        获取指定类型模型的配置信息
        
        Args:
            model_type: 模型类型 ('text_embedding', 'image_embedding', 'voice_to_text', 'llm', 'summarization', 'semantic_model', 'classifier_model')
        
        Returns:
            模型配置信息字典
        """
        model_configs = self.config.get('models', {})
        return model_configs.get(model_type, {})
    
    def get_model_path(self, model_type: str) -> str:
        """
        获取模型本地路径
        
        Args:
            model_type: 模型类型
        
        Returns:
            模型本地路径
        """
        model_info = self.get_model_info(model_type)
        return model_info.get('local_model_path', '')
    
    def get_model_name(self, model_type: str) -> str:
        """
        获取模型名称（用于HuggingFace下载）
        
        Args:
            model_type: 模型类型
        
        Returns:
            模型名称
        """
        model_info = self.get_model_info(model_type)
        return model_info.get('model_name', '')
    
    def get_multimodal_embedding_model(self) -> Dict[str, str]:
        """
        获取多模态向量化模型信息
        
        Returns:
            包含模型路径和名称的字典
        """
        # 尝试从text_embedding获取，因为BiomedCLIP是多模态的
        text_model_info = self.get_model_info('text_embedding')
        image_model_info = self.get_model_info('image_embedding')
        
        # 优先使用text_embedding的信息
        model_info = text_model_info if text_model_info else image_model_info
        
        return {
            'model_path': model_info.get('local_model_path', ''),
            'model_name': model_info.get('model_name', ''),
            'huggingface_name': model_info.get('huggingface_id', '')
        }
    
    def get_text_summarization_model(self) -> Dict[str, str]:
        """
        获取文本摘要模型信息
        
        Returns:
            包含模型路径和名称的字典
        """
        model_info = self.get_model_info('summarization')
        return {
            'model_path': model_info.get('local_model_path', ''),
            'model_name': model_info.get('model_name', ''),
            'huggingface_name': model_info.get('huggingface_id', '')
        }
    
    def get_text_generation_model(self) -> Dict[str, str]:
        """
        获取文本生成模型信息
        
        Returns:
            包含模型路径和名称的字典
        """
        model_info = self.get_model_info('llm')
        return {
            'model_path': model_info.get('local_model_path', ''),
            'model_name': model_info.get('model_name', ''),
            'huggingface_name': model_info.get('huggingface_id', '')
        }
    
    def get_voice_to_text_model(self) -> Dict[str, str]:
        """
        获取语音转文本模型信息
        
        Returns:
            包含模型路径和名称的字典
        """
        model_info = self.get_model_info('voice_to_text')
        return {
            'model_path': model_info.get('local_model_path', ''),
            'model_name': model_info.get('model_name', ''),
            'huggingface_name': model_info.get('huggingface_id', ''),
            'sample_rate': model_info.get('sample_rate', 16000),
            'batch_size': model_info.get('batch_size', 1)
        }
    
    def get_semantic_model(self) -> Dict[str, str]:
        """
        获取语义模型信息
        
        Returns:
            包含模型路径和名称的字典
        """
        model_info = self.get_model_info('semantic_model')
        return {
            'model_path': model_info.get('local_model_path', ''),
            'model_name': model_info.get('model_name', ''),
            'huggingface_name': model_info.get('huggingface_id', ''),
            'vector_dim': model_info.get('vector_dim', 384)
        }
    
    def get_classifier_model(self) -> Dict[str, str]:
        """
        获取分类模型信息
        
        Returns:
            包含模型路径和名称的字典
        """
        model_info = self.get_model_info('classifier_model')
        return {
            'model_path': model_info.get('local_model_path', ''),
            'model_name': model_info.get('model_name', ''),
            'huggingface_name': model_info.get('huggingface_id', '')
        }
    
    def get_quality_analysis_models(self) -> Dict[str, Dict[str, str]]:
        """
        获取质量分析模型信息（兼容性方法）
        
        Returns:
            包含语义模型和分类模型信息的字典
        """
        return {
            'semantic_model': self.get_semantic_model(),
            'classifier_model': self.get_classifier_model()
        }
    
    def get_all_models(self) -> Dict[str, Dict[str, str]]:
        """
        获取所有模型信息
        
        Returns:
            包含所有模型信息的字典
        """
        return {
            'text_embedding': self.get_multimodal_embedding_model(),
            'image_embedding': self.get_multimodal_embedding_model(),
            'voice_to_text': self.get_voice_to_text_model(),
            'text_summarization': self.get_text_summarization_model(),
            'text_generation': self.get_text_generation_model(),
            'quality_analysis': self.get_quality_analysis_models()
        }
    
    def _load_model_config(self):
        """加载模型状态配置"""
        try:
            if self.model_status_path.exists():
                with open(self.model_status_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error(f"加载模型状态配置失败: {e}")
            return {}
    
    def _save_model_config(self):
        """保存模型状态配置"""
        try:
            with open(self.model_status_path, 'w', encoding='utf-8') as f:
                json.dump(self.model_status, f, ensure_ascii=False, indent=2)
            logger.info(f"模型状态配置已保存到: {self.model_status_path}")
        except Exception as e:
            logger.error(f"保存模型状态配置失败: {e}")
    
    def check_model_exists(self, model_name: str) -> bool:
        """
        检查模型是否存在且完整
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型是否存在且完整
        """
        if model_name not in self.models_config:
            logger.error(f"未知的模型名称: {model_name}")
            return False
        
        model_path = self.base_dir / model_name
        if not model_path.exists():
            logger.info(f"模型目录不存在: {model_path}")
            return False
        
        # 检查必需文件
        required_files = self.models_config[model_name]["required_files"]
        missing_files = []
        
        for file_name in required_files:
            file_path = model_path / file_name
            if not file_path.exists():
                missing_files.append(file_name)
        
        if missing_files:
            logger.warning(f"模型 {model_name} 缺少文件: {missing_files}")
            return False
        
        # 更新状态
        self.model_status[model_name] = {
            "exists": True,
            "path": str(model_path),
            "last_checked": str(Path().cwd())
        }
        self._save_model_config()
        
        logger.info(f"模型 {model_name} 存在且完整")
        return True
    
    def download_model(self, model_name: str) -> bool:
        """
        下载指定模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            下载是否成功
        """
        if model_name not in self.models_config:
            logger.error(f"未知的模型名称: {model_name}")
            return False
        
        model_info = self.models_config[model_name]
        huggingface_id = model_info["huggingface_id"]
        model_path = self.base_dir / model_name
        
        try:
            logger.info(f"开始下载模型: {model_name} ({huggingface_id})")
            
            # 使用huggingface_hub下载
            snapshot_download(
                repo_id=huggingface_id,
                local_dir=str(model_path),
                local_dir_use_symlinks=False
            )
            
            # 验证下载
            if self.check_model_exists(model_name):
                logger.info(f"模型 {model_name} 下载成功")
                return True
            else:
                logger.error(f"模型 {model_name} 下载后验证失败")
                return False
                
        except Exception as e:
            logger.error(f"下载模型 {model_name} 失败: {e}")
            return False
    
    def get_model_path(self, model_name: str) -> Optional[Path]:
        """
        获取模型路径
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型路径，如果不存在则返回None
        """
        if model_name not in self.models_config:
            logger.error(f"未知的模型名称: {model_name}")
            return None
        
        model_path = self.base_dir / model_name
        if model_path.exists():
            return model_path
        else:
            logger.warning(f"模型路径不存在: {model_path}")
            return None
    
    def list_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        列出所有模型及其状态
        
        Returns:
            按类型分组的模型列表
        """
        result = {}
        
        for model_name, model_info in self.models_config.items():
            model_type = model_info["type"]
            if model_type not in result:
                result[model_type] = []
            
            model_path = self.base_dir / model_name
            exists = self.check_model_exists(model_name)
            
            model_data = {
                "name": model_name,
                "description": model_info["description"],
                "huggingface_id": model_info["huggingface_id"],
                "path": str(model_path),
                "exists": exists,
                "supports": model_info["supports"]
            }
            
            if "vector_dim" in model_info:
                model_data["vector_dim"] = model_info["vector_dim"]
            
            result[model_type].append(model_data)
        
        return result
    
    def ensure_models_available(self) -> bool:
        """
        确保所有核心模型都可用
        
        Returns:
            所有模型是否都可用
        """
        core_models = [
            "BiomedCLIP-PubMedBERT_256-vit_base_patch16_224",
            "Falconsai_text_summarization", 
            "Qwen2-0.5B-Medical-MLX"
        ]
        
        all_available = True
        
        for model_name in core_models:
            if not self.check_model_exists(model_name):
                logger.info(f"模型 {model_name} 不存在，开始下载...")
                if not self.download_model(model_name):
                    logger.error(f"下载模型 {model_name} 失败")
                    all_available = False
        
        return all_available
    
    def get_model_config(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        获取模型配置信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型配置信息
        """
        if model_name in self.models_config:
            return self.models_config[model_name].copy()
        else:
            logger.error(f"未知的模型名称: {model_name}")
            return None
    
    def update_all_configs(self) -> bool:
        """
        更新所有相关配置文件
        
        Returns:
            更新是否成功
        """
        try:
            # 更新RAG配置
            rag_config_path = self.base_dir.parent / "services" / "knowledge_retrieval_service" / "config" / "rag_config.json"
            if rag_config_path.exists():
                self._update_rag_config(rag_config_path)
            
            # 更新向量配置
            vector_config_path = self.base_dir.parent / "ai_models" / "embedding_models" / "config" / "vector_config.json"
            if vector_config_path.exists():
                self._update_vector_config(vector_config_path)
            
            logger.info("所有配置文件更新完成")
            return True
            
        except Exception as e:
            logger.error(f"更新配置文件失败: {e}")
            return False
    
    def _update_rag_config(self, config_path: Path):
        """更新RAG配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新模型路径
            if "BiomedCLIP-PubMedBERT_256-vit_base_patch16_224" in self.model_status:
                model_path = self.model_status["BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"]["path"]
                config["embedding_model"]["model_path"] = model_path
            
            if "Falconsai_text_summarization" in self.model_status:
                model_path = self.model_status["Falconsai_text_summarization"]["path"]
                config["summarization_model"]["model_path"] = model_path
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"RAG配置文件已更新: {config_path}")
            
        except Exception as e:
            logger.error(f"更新RAG配置文件失败: {e}")
    
    def _update_vector_config(self, config_path: Path):
        """更新向量配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新模型路径
            if "BiomedCLIP-PubMedBERT_256-vit_base_patch16_224" in self.model_status:
                model_path = self.model_status["BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"]["path"]
                config["model_path"] = model_path
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"向量配置文件已更新: {config_path}")
            
        except Exception as e:
            logger.error(f"更新向量配置文件失败: {e}")
    
    def replace_text2vec_references(self) -> bool:
        """
        替换项目中的text2vec引用为BiomedCLIP
        
        Returns:
            替换是否成功
        """
        try:
            # 需要替换的文件模式
            search_patterns = [
                "text2vec",
                "Text2Vec",
                "TEXT2VEC"
            ]
            
            # 搜索需要替换的文件
            project_root = self.base_dir.parent.parent
            replaced_files = []
            
            for root, dirs, files in os.walk(project_root):
                # 跳过一些不需要处理的目录
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules']]
                
                for file in files:
                    if file.endswith(('.py', '.json', '.md', '.txt')):
                        file_path = Path(root) / file
                        if self._replace_in_file(file_path, search_patterns):
                            replaced_files.append(str(file_path))
            
            logger.info(f"已替换 {len(replaced_files)} 个文件中的text2vec引用")
            for file_path in replaced_files:
                logger.info(f"  - {file_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"替换text2vec引用失败: {e}")
            return False
    
    def _replace_in_file(self, file_path: Path, search_patterns: List[str]) -> bool:
        """
        在文件中替换指定模式
        
        Args:
            file_path: 文件路径
            search_patterns: 搜索模式列表
            
        Returns:
            是否进行了替换
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 替换各种text2vec变体
            replacements = {
                "text2vec": "BiomedCLIP-PubMedBERT_256-vit_base_patch16_224",
                "Text2Vec": "BiomedCLIP-PubMedBERT_256-vit_base_patch16_224", 
                "TEXT2VEC": "BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"
            }
            
            for old, new in replacements.items():
                content = content.replace(old, new)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"处理文件 {file_path} 时出错: {e}")
            return False


# 全局实例
_model_config_reader = None

def get_model_config_reader() -> ModelConfigReader:
    """获取全局模型配置读取器实例"""
    global _model_config_reader
    if _model_config_reader is None:
        _model_config_reader = ModelConfigReader()
    return _model_config_reader


def get_multimodal_embedding_model() -> Dict[str, str]:
    """获取多模态向量化模型信息"""
    return get_model_config_reader().get_multimodal_embedding_model()


def get_text_summarization_model() -> Dict[str, str]:
    """获取文本摘要模型信息"""
    return get_model_config_reader().get_text_summarization_model()


def get_text_generation_model() -> Dict[str, str]:
    """获取文本生成模型信息"""
    return get_model_config_reader().get_text_generation_model()


def get_voice_to_text_model() -> Dict[str, str]:
    """获取语音转文本模型信息"""
    return get_model_config_reader().get_voice_to_text_model()


def get_semantic_model() -> Dict[str, str]:
    """获取语义模型信息"""
    return get_model_config_reader().get_semantic_model()


def get_classifier_model() -> Dict[str, str]:
    """获取分类模型信息"""
    return get_model_config_reader().get_classifier_model()


def get_quality_analysis_models() -> Dict[str, Dict[str, str]]:
    """获取质量分析模型信息（兼容性方法）"""
    return get_model_config_reader().get_quality_analysis_models()


def main():
    """主函数 - 统一模型管理器命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="统一模型管理器")
    parser.add_argument("--action", choices=["list", "check", "download", "ensure", "update"], 
                       default="list", help="执行的操作")
    parser.add_argument("--model", help="指定模型名称")
    parser.add_argument("--base-dir", help="模型存储基础目录")
    
    args = parser.parse_args()
    
    # 创建管理器实例
    manager = ModelConfigReader(base_dir=args.base_dir)
    
    if args.action == "list":
        print("=== 模型列表 ===")
        models = manager.list_models()
        for model_type, model_list in models.items():
            print(f"\n{model_type.upper()}:")
            for model in model_list:
                status = "✓" if model["exists"] else "✗"
                print(f"  {status} {model['name']}")
                print(f"    描述: {model['description']}")
                print(f"    路径: {model['path']}")
                if "vector_dim" in model:
                    print(f"    向量维度: {model['vector_dim']}")
                print()
    
    elif args.action == "check":
        if not args.model:
            print("请指定模型名称 (--model)")
            return
        
        exists = manager.check_model_exists(args.model)
        print(f"模型 {args.model}: {'存在' if exists else '不存在'}")
    
    elif args.action == "download":
        if not args.model:
            print("请指定模型名称 (--model)")
            return
        
        success = manager.download_model(args.model)
        print(f"下载模型 {args.model}: {'成功' if success else '失败'}")
    
    elif args.action == "ensure":
        print("确保所有核心模型可用...")
        success = manager.ensure_models_available()
        print(f"所有模型可用: {'是' if success else '否'}")
    
    elif args.action == "update":
        print("更新所有配置文件...")
        success = manager.update_all_configs()
        print(f"配置文件更新: {'成功' if success else '失败'}")


if __name__ == "__main__":
    # 测试代码
    reader = ModelConfigReader()
    print("多模态向量化模型:", reader.get_multimodal_embedding_model())
    print("文本摘要模型:", reader.get_text_summarization_model())
    print("文本生成模型:", reader.get_text_generation_model())
    
    # 如果直接运行，执行main函数
    if len(sys.argv) > 1:
        main()
