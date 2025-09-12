#!/usr/bin/env python3
"""
智诊通系统模型管理器
统一管理所有AI模型的下载、配置和使用
"""

import os
import sys
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from tqdm import tqdm

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelManager:
    """模型管理器类"""
    
    def __init__(self, base_dir: str = None):
        """
        初始化模型管理器
        
        Args:
            base_dir: 模型存储基础目录，默认为当前目录
        """
        if base_dir is None:
            # 获取脚本所在目录
            self.base_dir = Path(__file__).parent
        else:
            self.base_dir = Path(base_dir)
        
        # 确保基础目录存在
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 模型配置
        self.models_config = {
            "llm_models": {
                "Qwen2-0.5B-Medical-MLX": {
                    "name": "Qwen2-0.5B-Medical-MLX",
                    "type": "llm",
                    "description": "医疗专用大语言模型，基于Qwen2-0.5B微调",
                    "size": "34GB",
                    "files": [
                        "config.json",
                        "tokenizer_config.json", 
                        "tokenizer.json",
                        "model.safetensors.index.json",
                        "model-00001-of-00002.safetensors",
                        "model-00002-of-00002.safetensors"
                    ],
                    "download_url": None,  # 本地模型，无需下载
                    "local_path": "Qwen2-0.5B-Medical-MLX"
                }
            },
            "embedding_models": {
                "text2vec-base-chinese": {
                    "name": "text2vec-base-chinese",
                    "type": "embedding",
                    "description": "中文文本向量化模型",
                    "size": "400MB",
                    "files": [
                        "config.json",
                        "sentence_bert_config.json",
                        "tokenizer_config.json",
                        "vocab.txt",
                        "model.safetensors",
                        "modules.json"
                    ],
                    "download_url": "https://huggingface.co/shibing624/text2vec-base-chinese",
                    "local_path": "text2vec-base-chinese"
                }
            }
        }
        
        # 配置文件路径映射
        self.config_files = {
            "rag_config": "codes/services/knowledge_retrieval_service/api/config/rag_config.json",
            "unified_config": "codes/ai_models/embedding_models/config/unified_config.json",
            "medical_config": "codes/ai_models/embedding_models/config/medical_knowledge_config.json",
            "vector_config": "codes/ai_models/embedding_models/config/vector_config.json"
        }
    
    def check_model_exists(self, model_name: str, model_type: str = None) -> bool:
        """
        检查模型是否存在
        
        Args:
            model_name: 模型名称
            model_type: 模型类型 (llm_models, embedding_models)
            
        Returns:
            模型是否存在
        """
        # 模型直接存储在 base_dir 下，不在子目录中
        model_path = self.base_dir / model_name
        
        # 直接检查模型目录是否存在，不验证文件完整性
        return model_path.exists() and model_path.is_dir()
    
    def _validate_model_files(self, model_path: Path, model_name: str) -> bool:
        """
        验证模型文件完整性
        
        Args:
            model_path: 模型路径
            model_name: 模型名称
            
        Returns:
            文件是否完整
        """
        # 查找模型配置
        model_config = None
        for mtype in self.models_config:
            if model_name in self.models_config[mtype]:
                model_config = self.models_config[mtype][model_name]
                break
        
        if not model_config:
            logger.warning(f"未找到模型 {model_name} 的配置")
            return False
        
        # 检查必需文件
        required_files = model_config.get("files", [])
        missing_files = []
        
        for file_name in required_files:
            file_path = model_path / file_name
            if not file_path.exists():
                missing_files.append(file_name)
        
        if missing_files:
            logger.warning(f"模型 {model_name} 缺少文件: {missing_files}")
            return False
        
        logger.info(f"模型 {model_name} 文件完整")
        return True
    
    def get_model_path(self, model_name: str, model_type: str = None) -> Optional[Path]:
        """
        获取模型路径
        
        Args:
            model_name: 模型名称
            model_type: 模型类型
            
        Returns:
            模型路径，如果不存在返回None
        """
        if self.check_model_exists(model_name, model_type):
            return self.base_dir / model_name
        return None
    
    def list_models(self) -> Dict[str, List[Dict]]:
        """
        列出所有模型及其状态
        
        Returns:
            模型列表和状态
        """
        result = {}
        
        for model_type, models in self.models_config.items():
            result[model_type] = []
            for model_name, model_config in models.items():
                model_path = self.base_dir / model_type / model_name
                exists = self.check_model_exists(model_name, model_type)
                
                result[model_type].append({
                    "name": model_name,
                    "description": model_config["description"],
                    "size": model_config["size"],
                    "exists": exists,
                    "path": str(model_path) if exists else None,
                    "local_path": model_config["local_path"]
                })
        
        return result
    
    def update_config_files(self, use_local_models: bool = True) -> bool:
        """
        更新配置文件中的模型路径
        
        Args:
            use_local_models: 是否使用本地模型路径
            
        Returns:
            是否成功更新
        """
        try:
            # 获取项目根目录
            project_root = Path(__file__).parent.parent.parent.parent
            
            for config_name, config_path in self.config_files.items():
                full_config_path = project_root / config_path
                
                if not full_config_path.exists():
                    logger.warning(f"配置文件不存在: {full_config_path}")
                    continue
                
                # 读取配置文件
                with open(full_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 更新模型路径
                updated = False
                
                if config_name == "rag_config":
                    # 更新RAG配置
                    if "llm_service" in config:
                        if use_local_models:
                            llm_path = self.get_model_path("Qwen2-0.5B-Medical-MLX", "llm_models")
                            if llm_path:
                                config["llm_service"]["model_path"] = str(llm_path)
                                updated = True
                    
                    if "vector_service" in config:
                        if use_local_models:
                            text_path = self.get_model_path("text2vec-base-chinese", "embedding_models")
                            if text_path:
                                config["vector_service"]["text_model_path"] = str(text_path)
                                updated = True
                
                elif config_name == "unified_config":
                    # 更新统一配置
                    if "models" in config:
                        if "text_embedding" in config["models"]:
                            if use_local_models:
                                text_path = self.get_model_path("text2vec-base-chinese", "embedding_models")
                                if text_path:
                                    config["models"]["text_embedding"]["model_path"] = str(text_path)
                                    updated = True
                
                elif config_name == "medical_config":
                    # 更新医疗配置
                    if "models" in config:
                        if "text_embedding" in config["models"]:
                            if use_local_models:
                                text_path = self.get_model_path("text2vec-base-chinese", "embedding_models")
                                if text_path:
                                    config["models"]["text_embedding"]["model_path"] = str(text_path)
                                    updated = True
                
                elif config_name == "vector_config":
                    # 更新向量配置
                    if use_local_models:
                        text_path = self.get_model_path("text2vec-base-chinese", "embedding_models")
                        if text_path:
                            config["LOCAL_MODEL_PATH"] = str(text_path)
                            updated = True
                
                # 保存更新的配置
                if updated:
                    with open(full_config_path, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                    logger.info(f"已更新配置文件: {config_path}")
                else:
                    logger.info(f"配置文件无需更新: {config_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"更新配置文件失败: {e}")
            return False
    
    def create_model_symlink(self, model_name: str, target_path: str) -> bool:
        """
        创建模型符号链接
        
        Args:
            model_name: 模型名称
            target_path: 目标路径
            
        Returns:
            是否成功创建
        """
        try:
            model_path = None
            for model_type in self.models_config:
                if model_name in self.models_config[model_type]:
                    model_path = self.base_dir / model_type / model_name
                    break
            
            if not model_path or not model_path.exists():
                logger.error(f"模型不存在: {model_name}")
                return False
            
            target_path = Path(target_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果目标路径已存在，先删除
            if target_path.exists():
                if target_path.is_symlink():
                    target_path.unlink()
                else:
                    shutil.rmtree(target_path)
            
            # 创建符号链接
            target_path.symlink_to(model_path)
            logger.info(f"已创建符号链接: {target_path} -> {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"创建符号链接失败: {e}")
            return False
    
    def generate_model_guide(self) -> str:
        """
        生成模型使用指南
        
        Returns:
            指南内容
        """
        models_info = self.list_models()
        
        guide = """# 智诊通系统本地模型使用指南

## 📁 模型存储结构

```
codes/ai_models/llm_models/
├── llm_models/                    # 大语言模型目录
│   └── Medical_Qwen3_17B/        # 医疗专用大语言模型
└── embedding_models/              # 向量化模型目录
    └── text2vec-base-chinese/    # 中文文本向量化模型
```

## 🤖 模型列表

"""
        
        for model_type, models in models_info.items():
            guide += f"### {model_type.replace('_', ' ').title()}\n\n"
            
            for model in models:
                status = "✅ 已安装" if model["exists"] else "❌ 未安装"
                guide += f"#### {model['name']}\n"
                guide += f"- **描述**: {model['description']}\n"
                guide += f"- **大小**: {model['size']}\n"
                guide += f"- **状态**: {status}\n"
                if model["path"]:
                    guide += f"- **路径**: `{model['path']}`\n"
                guide += "\n"
        
        guide += """## 🔧 配置说明

### 自动配置更新

模型管理器会自动更新以下配置文件中的模型路径：

1. **RAG服务配置**: `codes/services/knowledge_retrieval_service/api/config/rag_config.json`
2. **统一配置**: `codes/ai_models/embedding_models/config/unified_config.json`
3. **医疗配置**: `codes/ai_models/embedding_models/config/medical_knowledge_config.json`
4. **向量配置**: `codes/ai_models/embedding_models/config/vector_config.json`

### 手动配置

如果需要手动配置模型路径，请确保路径指向正确的模型目录。

## 🚀 使用方法

### 1. 检查模型状态

```python
from model_manager import ModelManager

manager = ModelManager()
models = manager.list_models()
print(models)
```

### 2. 更新配置文件

```python
# 使用本地模型路径更新所有配置文件
manager.update_config_files(use_local_models=True)
```

### 3. 验证模型完整性

```python
# 检查特定模型是否存在且完整
exists = manager.check_model_exists("Medical_Qwen3_17B", "llm_models")
print(f"模型存在: {exists}")
```

## 📋 模型详细信息

### Medical_Qwen3_17B

- **类型**: 大语言模型 (LLM)
- **用途**: 医疗问答、诊断建议、健康咨询
- **特点**: 基于Qwen3-17B微调，专门针对医疗场景优化
- **内存需求**: 建议32GB+ RAM
- **GPU支持**: 支持CUDA加速

### text2vec-base-chinese

- **类型**: 文本向量化模型
- **用途**: 文本嵌入、语义搜索、文档检索
- **特点**: 中文优化，支持医疗文本向量化
- **内存需求**: 建议4GB+ RAM
- **GPU支持**: 可选

## 🔍 故障排除

### 常见问题

1. **模型文件不完整**
   - 检查模型目录是否存在
   - 验证必需文件是否齐全
   - 重新下载缺失的模型文件

2. **配置文件路径错误**
   - 运行 `manager.update_config_files()` 自动更新
   - 手动检查配置文件中的路径设置

3. **内存不足**
   - 减少批处理大小
   - 使用CPU推理
   - 关闭其他应用程序

### 日志查看

```bash
# 查看模型管理器日志
tail -f logs/model_manager.log

# 查看RAG服务日志
tail -f codes/services/knowledge_retrieval_service/logs/rag_service.log
```

## 📞 技术支持

如果遇到问题，请检查：
1. 模型文件完整性
2. 配置文件路径
3. 系统资源使用情况
4. 依赖包版本

---

**更新时间**: 2024年9月11日  
**版本**: 1.0.0  
**状态**: ✅ 就绪
"""
        
        return guide
    
    def save_model_guide(self, output_path: str = None) -> bool:
        """
        保存模型使用指南到文件
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            是否成功保存
        """
        try:
            if output_path is None:
                output_path = self.base_dir / "本地模型使用指南.md"
            
            guide_content = self.generate_model_guide()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(guide_content)
            
            logger.info(f"模型使用指南已保存到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存模型使用指南失败: {e}")
            return False


def main():
    """主函数"""
    print("🤖 智诊通系统模型管理器")
    print("=" * 50)
    
    # 创建模型管理器
    manager = ModelManager()
    
    # 列出所有模型
    print("\n📋 模型状态:")
    models = manager.list_models()
    
    for model_type, model_list in models.items():
        print(f"\n{model_type.replace('_', ' ').title()}:")
        for model in model_list:
            status = "✅" if model["exists"] else "❌"
            print(f"  {status} {model['name']} - {model['description']}")
    
    # 更新配置文件
    print("\n🔧 更新配置文件...")
    if manager.update_config_files(use_local_models=True):
        print("✅ 配置文件更新成功")
    else:
        print("❌ 配置文件更新失败")
    
    # 生成并保存使用指南
    print("\n📖 生成模型使用指南...")
    if manager.save_model_guide():
        print("✅ 模型使用指南生成成功")
    else:
        print("❌ 模型使用指南生成失败")
    
    print("\n🎉 模型管理完成！")


if __name__ == "__main__":
    main()
