"""
医疗知识数据管理器
统一管理纯文本、图文、语音等不同类型的数据存储和处理
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class DataType:
    """数据类型枚举"""
    TEXT = "text"
    IMAGE_TEXT = "image_text"
    VOICE = "voice"
    MULTIMODAL = "multimodal"

class MedicalKnowledgeManager:
    """医疗知识数据管理器"""
    
    def __init__(self, base_dir: str = None):
        """
        初始化医疗知识数据管理器
        
        Args:
            base_dir: 基础数据目录，默认为 datas/medical_knowledge
        """
        if base_dir is None:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(current_dir, "..", "..", "..", "..")
            self.base_dir = os.path.join(project_root, "datas", "medical_knowledge")
        else:
            self.base_dir = base_dir
            
        self.base_dir = os.path.abspath(self.base_dir)
        
        # 确保基础目录存在
        os.makedirs(self.base_dir, exist_ok=True)
        
        # 设置日志
        self.logger = self._setup_logger()
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化目录结构
        self._init_directory_structure()
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        log_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        logger = logging.getLogger("MedicalKnowledgeManager")
        logger.setLevel(logging.INFO)
        
        # 创建文件处理器
        log_file = os.path.join(log_dir, "medical_knowledge_manager.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config_file = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "config", 
            "medical_knowledge_config.json"
        )
        
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 返回默认配置
            return self._get_default_config()
            
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "data_structure": {
                "base_dir": self.base_dir,
                "text_data": {
                    "raw_dir": "text_data/raw",
                    "processed_dir": "text_data/processed",
                    "embeddings_dir": "text_data/embeddings",
                    "vector_db_dir": "vector_databases/text"
                },
                "image_text_data": {
                    "raw_dir": "image_text_data/raw",
                    "processed_dir": "image_text_data/processed",
                    "embeddings_dir": "image_text_data/embeddings",
                    "vector_db_dir": "vector_databases/image"
                },
                "voice_data": {
                    "raw_dir": "voice_data/raw",
                    "processed_dir": "voice_data/processed",
                    "embeddings_dir": "voice_data/embeddings",
                    "vector_db_dir": "vector_databases/voice"
                },
                "multimodal": {
                    "vector_db_dir": "vector_databases/multimodal"
                },
                "training_data": "training_data",
                "test_data": "test_data",
                "logs": "logs"
            }
        }
        
    def _init_directory_structure(self):
        """初始化目录结构"""
        data_structure = self.config["data_structure"]
        
        # 创建各类型数据的目录
        for data_type in ["text_data", "image_text_data", "voice_data"]:
            if data_type in data_structure:
                type_config = data_structure[data_type]
                for subdir in ["raw", "processed", "embeddings"]:
                    if f"{subdir}_dir" in type_config:
                        dir_path = os.path.join(self.base_dir, type_config[f"{subdir}_dir"])
                        os.makedirs(dir_path, exist_ok=True)
                        self.logger.info(f"创建目录: {dir_path}")
                        
        # 添加数据类型映射
        self.data_type_mapping = {
            "text": "text_data",
            "image_text": "image_text_data", 
            "voice": "voice_data"
        }
        
        # 创建向量数据库目录
        for data_type in ["text", "image", "voice", "multimodal"]:
            # 向量数据库目录应该在项目根目录的 datas/vector_databases 下
            # self.base_dir 是 datas/medical_knowledge，所以项目根目录是 self.base_dir 的父目录的父目录
            project_root = os.path.dirname(os.path.dirname(self.base_dir))
            vector_db_dir = os.path.join(project_root, "datas", "vector_databases", data_type)
            os.makedirs(vector_db_dir, exist_ok=True)
            self.logger.info(f"创建向量数据库目录: {vector_db_dir}")
            
        # 创建训练和测试数据目录
        for data_type in ["training_data", "test_data"]:
            dir_path = os.path.join(self.base_dir, data_type)
            os.makedirs(dir_path, exist_ok=True)
            self.logger.info(f"创建目录: {dir_path}")
            
    def get_path(self, data_type: str, subdir: str, filename: str = None) -> str:
        """
        获取指定类型数据的路径
        
        Args:
            data_type: 数据类型 (text, image_text, voice)
            subdir: 子目录 (raw, processed, embeddings)
            filename: 文件名（可选）
            
        Returns:
            完整路径
        """
        data_structure = self.config["data_structure"]
        
        # 映射数据类型
        mapped_type = self.data_type_mapping.get(data_type, data_type)
        
        if mapped_type not in data_structure:
            raise ValueError(f"不支持的数据类型: {data_type} (映射为: {mapped_type})")
            
        type_config = data_structure[mapped_type]
        subdir_key = f"{subdir}_dir"
        
        if subdir_key not in type_config:
            raise ValueError(f"不支持的子目录: {subdir}")
            
        base_path = os.path.join(self.base_dir, type_config[subdir_key])
        
        if filename:
            return os.path.join(base_path, filename)
        else:
            return base_path
            
    def get_vector_db_path(self, data_type: str) -> str:
        """
        获取向量数据库路径
        
        Args:
            data_type: 数据类型 (text, image, voice, multimodal)
            
        Returns:
            向量数据库路径
        """
        # 向量数据库目录应该在项目根目录的 datas/vector_databases 下
        # self.base_dir 是 datas/medical_knowledge，所以项目根目录是 self.base_dir 的父目录的父目录
        project_root = os.path.dirname(os.path.dirname(self.base_dir))
        return os.path.join(project_root, "datas", "vector_databases", data_type)
                
    def list_files(self, data_type: str, subdir: str, pattern: str = "*") -> List[str]:
        """
        列出指定目录下的文件
        
        Args:
            data_type: 数据类型
            subdir: 子目录
            pattern: 文件匹配模式
            
        Returns:
            文件列表
        """
        import glob
        
        dir_path = self.get_path(data_type, subdir)
        search_pattern = os.path.join(dir_path, pattern)
        return glob.glob(search_pattern)
        
    def get_data_summary(self) -> Dict[str, Any]:
        """获取数据摘要信息"""
        summary = {
            "base_dir": self.base_dir,
            "data_types": {},
            "total_files": 0
        }
        
        for data_type in ["text", "image_text", "voice"]:
            type_summary = {}
            for subdir in ["raw", "processed", "embeddings"]:
                try:
                    files = self.list_files(data_type, subdir)
                    type_summary[subdir] = {
                        "file_count": len(files),
                        "files": [os.path.basename(f) for f in files]
                    }
                    summary["total_files"] += len(files)
                except Exception as e:
                    type_summary[subdir] = {"error": str(e)}
                    
            summary["data_types"][data_type] = type_summary
            
        return summary
        
    def cleanup_old_files(self, data_type: str, subdir: str, days: int = 30):
        """
        清理旧文件
        
        Args:
            data_type: 数据类型
            subdir: 子目录
            days: 保留天数
        """
        import time
        
        dir_path = self.get_path(data_type, subdir)
        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 60 * 60)
        
        cleaned_count = 0
        for file_path in self.list_files(data_type, subdir):
            if os.path.isfile(file_path):
                file_time = os.path.getmtime(file_path)
                if file_time < cutoff_time:
                    try:
                        os.remove(file_path)
                        cleaned_count += 1
                        self.logger.info(f"删除旧文件: {file_path}")
                    except Exception as e:
                        self.logger.error(f"删除文件失败 {file_path}: {e}")
                        
        self.logger.info(f"清理完成，删除了 {cleaned_count} 个文件")
        return cleaned_count

# 全局实例
knowledge_manager = MedicalKnowledgeManager()

if __name__ == "__main__":
    # 测试管理器
    manager = MedicalKnowledgeManager()
    
    # 打印数据摘要
    summary = manager.get_data_summary()
    print("数据摘要:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    # 测试路径获取
    print(f"\n文本数据原始目录: {manager.get_path('text', 'raw')}")
    print(f"图像文本数据向量化目录: {manager.get_path('image_text', 'embeddings')}")
    print(f"文本向量数据库路径: {manager.get_vector_db_path('text')}")
