"""
智诊通向量化系统配置管理器
统一管理所有配置，避免硬编码路径
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """统一配置管理器"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        config_path = Path(__file__).parent / "embed_config.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            print(f"✅ 配置加载成功: {config_path}")
        except Exception as e:
            print(f"❌ 配置加载失败: {e}")
            self._config = {}
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号分隔的路径
        例如: get('model_configurations.text_embedding.model_name')
        """
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_project_root(self) -> Path:
        """获取项目根目录"""
        # 从embedding_service/config/config_manager.py
        # 需要回到项目根目录: codes/services/embedding_service/config -> 项目根目录
        # 路径: config_manager.py -> config -> embedding_service -> services -> codes -> 项目根目录
        current_dir = Path(__file__).parent.parent.parent.parent.parent
        return current_dir
    
    def get_base_data_dir(self) -> Path:
        """获取基础数据目录"""
        project_root = self.get_project_root()
        return project_root / "datas" / "medical_knowledge"
    
    def get_model_path(self, model_type: str) -> str:
        """获取模型路径，从统一的model_config.json加载"""
        try:
            # 导入模型配置读取器
            import sys
            from pathlib import Path
            current_dir = Path(__file__).parent
            llm_models_path = current_dir.parent.parent / "llm_models"
            sys.path.insert(0, str(llm_models_path))
            
            from model_config_reader import get_model_config_reader
            
            # 获取模型配置读取器
            reader = get_model_config_reader()
            
            # 根据模型类型获取配置
            if model_type in ['text_embedding', 'image_embedding']:
                model_info = reader.get_multimodal_embedding_model()
            elif model_type == 'voice_to_text':
                model_info = reader.get_voice_to_text_model()
            elif model_type == 'semantic_model':
                model_info = reader.get_semantic_model()
            elif model_type == 'classifier_model':
                model_info = reader.get_classifier_model()
            elif model_type == 'quality_analysis':
                # 兼容性：返回语义模型的路径
                model_info = reader.get_semantic_model()
            else:
                raise ValueError(f"不支持的模型类型: {model_type}")
            
            model_path = model_info.get('model_path', '')
            
            # 如果是相对路径，转换为绝对路径
            if model_path and not os.path.isabs(model_path):
                # 获取项目根目录
                project_root = self.get_project_root()
                
                # 处理相对路径，如 "../../aimodels/..."
                if model_path.startswith("../../"):
                    # 去掉 "../../" 前缀，然后构建完整路径
                    relative_path = model_path[6:]  # 去掉 "../../"
                    model_path = str(project_root / "codes" / relative_path)
                else:
                    # 将相对路径转换为绝对路径
                    model_path = str(project_root / model_path)
            
            return model_path
            
        except Exception as e:
            raise ValueError(f"获取模型路径失败: {e}")
    
    def get_data_path(self, data_type: str, sub_type: str = None) -> Path:
        """获取数据路径"""
        base_dir = self.get_base_data_dir()
        
        if sub_type:
            data_config = self.get(f'data_directories.{data_type}.{sub_type}')
            if data_config:
                return base_dir / data_config
        else:
            data_config = self.get(f'data_directories.{data_type}')
            if data_config and isinstance(data_config, dict):
                # 返回数据类型的目录
                return base_dir / data_type
            elif data_config:
                return base_dir / data_config
        
        # 如果配置中找不到，使用默认路径
        if sub_type:
            return base_dir / data_type / sub_type
        else:
            return base_dir / data_type
    
    def get_file_path(self, file_key: str) -> Path:
        """获取具体文件路径"""
        base_dir = self.get_base_data_dir()
        file_path = self.get(f'file_paths.{file_key}')
        if file_path:
            return base_dir / file_path
        raise ValueError(f"未找到文件路径配置: {file_key}")
    
    def get_vector_db_path(self, collection_type: str = None) -> Path:
        """获取向量数据库路径"""
        persist_dir = self.get('vector_database.persist_directory')
        if persist_dir:
            # 处理相对路径
            if persist_dir.startswith('../../../'):
                # 移除相对路径前缀，直接使用datas/chroma_db
                return self.get_project_root() / "datas" / "chroma_db"
            elif persist_dir.startswith('datas/'):
                # 直接使用datas路径
                return self.get_project_root() / persist_dir
            else:
                # 绝对路径或相对路径
                return Path(persist_dir)
        
        # 默认路径 - 统一使用chroma_db目录
        return self.get_project_root() / "datas" / "chroma_db"
    
    def get_collection_name(self, collection_type: str) -> str:
        """获取集合名称"""
        collections = self.get('vector_database.collections', {})
        # 统一使用multimodal集合
        return collections.get('multimodal', 'medical_multimodal_vectors')
    
    def get_log_file_path(self) -> Path:
        """获取日志文件路径"""
        # 使用统一的日志目录：codes/logs/
        logs_dir = self.get_project_root() / "codes" / "logs"
        # 不自动创建logs目录，由log_config.py统一管理
        log_file = self.get('logging.file', 'embedding_service.log')
        return logs_dir / log_file
    
    def is_local_only(self) -> bool:
        """是否仅使用本地模型"""
        return self.get('network_settings.use_local_only', True)
    
    def get_processing_config(self, data_type: str) -> Dict[str, Any]:
        """获取处理配置"""
        return self.get(f'processing_settings.{data_type}', {})
    
    def get_quality_config(self) -> Dict[str, Any]:
        """获取质量分析配置"""
        return self.get('quality_analyzer', {})
    
    def get_multimodal_config(self) -> Dict[str, Any]:
        """获取多模态配置"""
        return self.get('multimodal_options', {})
    
    def reload_config(self):
        """重新加载配置"""
        self._load_config()


# 全局配置管理器实例
config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """获取配置管理器实例"""
    return config_manager


# 便捷函数
def get_model_path(model_type: str) -> str:
    """获取模型路径"""
    return config_manager.get_model_path(model_type)


def get_data_path(data_type: str, sub_type: str = None) -> Path:
    """获取数据路径"""
    return config_manager.get_data_path(data_type, sub_type)


def get_file_path(file_key: str) -> Path:
    """获取文件路径"""
    return config_manager.get_file_path(file_key)


def get_vector_db_path(collection_type: str = None) -> Path:
    """获取向量数据库路径"""
    return config_manager.get_vector_db_path(collection_type)


def get_collection_name(collection_type: str) -> str:
    """获取集合名称"""
    return config_manager.get_collection_name(collection_type)


def get_log_file_path() -> Path:
    """获取日志文件路径"""
    return config_manager.get_log_file_path()


if __name__ == "__main__":
    # 测试配置管理器
    print("=== 配置管理器测试 ===")
    print(f"项目根目录: {config_manager.get_project_root()}")
    print(f"基础数据目录: {config_manager.get_base_data_dir()}")
    print(f"文本嵌入模型路径: {config_manager.get_model_path('text_embedding')}")
    print(f"文本数据原始目录: {config_manager.get_data_path('text_data', 'raw_dir')}")
    print(f"向量数据库路径: {config_manager.get_vector_db_path()}")
    print(f"日志文件路径: {config_manager.get_log_file_path()}")
    print(f"是否仅使用本地模型: {config_manager.is_local_only()}")
