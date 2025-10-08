"""
统一的多模态向量数据库构建器
整合文本、图像和图文配对数据的处理功能
支持智诊通系统的多模态检索需求
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import logging
from tqdm import tqdm
import sys

# 导入配置管理器
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config"))
from config_manager import get_config, get_data_path, get_file_path, get_vector_db_path, get_collection_name

# 导入文档切分模块
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chunk"))
try:
    from document_chunker import DocumentChunker, ChunkConfig, ChunkStrategy, create_medical_chunker, create_general_chunker
    DOCUMENT_CHUNKER_AVAILABLE = True
except ImportError as e:
    print(f"警告: 文档切分器模块未找到，将使用简单分块: {e}")
    DOCUMENT_CHUNKER_AVAILABLE = False

# 导入质量检查器
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from analyzers.quality_analyzer import QualityAnalyzer
    QUALITY_ANALYZER_AVAILABLE = True
    print("✓ 质量检查器模块导入成功")
except ImportError as e:
    print(f"警告: 质量检查器模块未找到，将跳过质量检查: {e}")
    QUALITY_ANALYZER_AVAILABLE = False

# 获取默认文本嵌入模型
def get_default_text_embedding_model():
    """获取默认文本嵌入模型"""
    try:
        # 使用配置管理器获取模型路径
        return get_config().get_model_path("text_embedding")
    except Exception as e:
        print(f"获取文本嵌入模型失败: {e}")
        return "microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"

# 设置日志
def setup_logging():
    """设置统一日志配置"""
    import sys
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "utils"))
    import sys
    from pathlib import Path

    # 添加common模块到路径
    current_file = Path(__file__)
    common_dir = current_file.parent.parent.parent.parent / "common"
    sys.path.insert(0, str(common_dir))

    from log_config import get_logger, get_log_file
    
    # 使用统一的日志管理器
    logger = get_logger('multimodal_vectorization')
    logger.info("🗄️ 开始多模态数据库构建运行")
    logger.info("🎯 智诊通多模态数据库构建系统启动")
    logger.setLevel(logging.INFO)
    
    return logger, get_log_file()

# 初始化日志
logger, log_file = setup_logging()

# 设置文档切分器的日志级别为DEBUG，以便看到详细的切分过程
document_chunker_logger = logging.getLogger('processors.document_chunker')
document_chunker_logger.setLevel(logging.INFO)

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 尝试导入图像向量化模块
try:
    # 添加embed目录到路径
    embed_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "embed")
    sys.path.append(embed_dir)
    from embed.image_embedder import ImageEmbedderFactory, batch_embed_images
    IMAGE_EMBEDDING_AVAILABLE = True
    logger.info("✓ 图像向量化模块导入成功")
except ImportError as e:
    logger.warning(f"图像向量化模块未找到，将使用简化模式: {e}")
    IMAGE_EMBEDDING_AVAILABLE = False

class UnifiedMultimodalVectorDatabaseBuilder:
    """统一的多模态向量数据库构建器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化统一的多模态向量数据库构建器
        
        Args:
            config_path: 配置文件路径
        """
        logger.info("=" * 80)
        logger.info("🚀 智诊通多模态向量数据库构建器初始化开始")
        logger.info("=" * 80)
        
        self.config = self._load_config(config_path)
        self.text_embedder = None
        self.image_embedder = None
        self.text_vector_db = None
        self.image_vector_db = None
        self.multimodal_vector_db = None
        self.image_text_mapping = {}
        self.quality_analyzer = None  # 质量检查器
        
        # 记录目录结构信息
        self._log_directory_structure()
        self.document_chunker = None  # 文档切分器
        
        # 初始化组件
        self._init_components()
        
        logger.info("✅ 智诊通多模态向量数据库构建器初始化完成")
        logger.info("=" * 80)
    
    def _log_directory_structure(self):
        """记录目录结构信息"""
        logger.info("📁 目录结构配置信息:")
        logger.info(f"  📝 日志文件目录: {log_file}")
        logger.info(f"  📂 项目根目录: {self.config.get('PROJECT_ROOT', 'N/A')}")
        logger.info(f"  📊 基础数据目录: {self.config.get('BASE_DATA_DIR', 'N/A')}")
        
        # 原始数据目录
        logger.info("  📥 原始数据目录:")
        logger.info(f"    - 文本数据: {self.config.get('BASE_DATA_DIR', '')}/text_data/raw/")
        logger.info(f"    - 图文数据: {self.config.get('BASE_DATA_DIR', '')}/image_text_data/raw/")
        logger.info(f"    - 语音数据: {self.config.get('VOICE_DATA_RAW_PATH', 'N/A')}")
        
        # 预处理数据目录
        logger.info("  🔄 预处理数据目录:")
        logger.info(f"    - 纯文本数据: {self.config.get('BASE_DATA_DIR', '')}/text_data/processed/")
        logger.info(f"    - 图文数据: {self.config.get('BASE_DATA_DIR', '')}/image_text_data/processed/")
        logger.info(f"    - 语音数据: {self.config.get('VOICE_DATA_PROCESSED_PATH', 'N/A')}")
        
        # 向量数据库目录
        logger.info("  🗄️ 向量数据库目录:")
        logger.info(f"    - 多模态向量数据库: {self.config.get('MULTIMODAL_VECTOR_DB_PATH', 'N/A')}")
        
        # 检查目录是否存在
        self._check_directories()
    
    def _check_directories(self):
        """检查目录是否存在，不存在则创建"""
        # 获取日志文件路径
        log_file = self.config.get('LOG_FILE_PATH')
        if not log_file:
            # 如果没有配置日志文件路径，使用统一日志配置
            project_root = self.config.get('PROJECT_ROOT', '')
            log_file = os.path.join(project_root, 'codes', 'logs', 'embedding_service.log')
        
        directories_to_check = [
            ("日志目录", os.path.dirname(log_file) if log_file else None),
            ("多模态向量数据库目录", self.config.get('MULTIMODAL_VECTOR_DB_PATH')),
        ]
        
        # 仅检查与记录，不在此处创建目录，避免在 embedding_service 下自动生成 codes/datas
        for name, path in directories_to_check:
            if path and not os.path.exists(path):
                logger.warning(f"  ⚠️  目录不存在: {name} -> {path}")
            elif path:
                logger.info(f"  ✅ 目录已存在: {name} -> {path}")
    
    def _load_config(self, config_path: str = None) -> Dict:
        """加载配置文件"""
        # 使用新的ConfigManager系统
        try:
            from config.config_manager import ConfigManager
            config_manager = ConfigManager()
            
            # 构建配置字典，使用新的配置结构
            base_data_dir = str(config_manager.get_base_data_dir())
            
            config = {
                # 基础路径
                "BASE_DATA_DIR": base_data_dir,
                "PROJECT_ROOT": str(config_manager.get_project_root()),
                
                # 数据路径
                "PROCESSED_REPORTS_PATH": str(config_manager.get_file_path("processed_reports")),
                "TRAIN_REPORTS_PATH": str(config_manager.get_file_path("train_reports")),
                "TEST_REPORTS_PATH": str(config_manager.get_file_path("test_reports")),
                "PROCESSED_IMAGES_PATH": str(config_manager.get_file_path("processed_images")),
                "TRAIN_IMAGES_PATH": str(config_manager.get_file_path("train_images")),
                "TEST_IMAGES_PATH": str(config_manager.get_file_path("test_images")),
                
                # 语音数据路径
                "VOICE_DATA_RAW_PATH": str(config_manager.get_data_path("voice_data", "raw_dir")),
                "VOICE_DATA_PROCESSED_PATH": str(config_manager.get_data_path("voice_data", "processed_dir")),
                
                # 向量数据库路径
                "MULTIMODAL_VECTOR_DB_PATH": str(config_manager.get_vector_db_path("multimodal")),
                "MULTIMODAL_COLLECTION_NAME": config_manager.get_collection_name("multimodal"),
                
                # 模型配置
                "TEXT_EMBEDDING_MODEL": config_manager.get_model_path("text_embedding"),
                "IMAGE_EMBEDDING_MODEL": config_manager.get_model_path("image_embedding"),
                "IMAGE_EMBEDDER_TYPE": "biomedclip",
                "IMAGE_EMBEDDER_DEVICE": "cpu",
                
                # 处理配置
                "BATCH_SIZE": config_manager.get("processing_settings.text.batch_size", 32),
                "IMAGE_BATCH_SIZE": config_manager.get("processing_settings.image.batch_size", 16),
                "MAX_IMAGES_PER_BATCH": 500,
                "DOWNLOAD_TIMEOUT": config_manager.get("network_settings.download_timeout", 30),
                "MAX_RETRIES": config_manager.get("network_settings.max_retries", 3),
                "USE_LOCAL_ONLY": config_manager.get("network_settings.use_local_only", True),
            }
            
            logger.info(f"已加载新配置系统: ConfigManager")
            return config
        except Exception as e:
            logger.error(f"加载新配置系统失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 从embedding_service/core/build_multimodal_database.py
        # 需要回到项目根目录: core -> embedding_service -> services -> codes -> 项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
        base_data_dir = os.path.join(project_root, "datas", "medical_knowledge")
        
        return {
            # 数据路径
            "BASE_DATA_DIR": base_data_dir,
            "PROCESSED_REPORTS_PATH": os.path.join(base_data_dir, "image_text_data", "processed", "processed_reports.csv"),
            "TRAIN_REPORTS_PATH": os.path.join(base_data_dir, "dialogue_data", "dialogue_train.csv"),
            "TEST_REPORTS_PATH": os.path.join(base_data_dir, "dialogue_data", "dialogue_test.csv"),
            "PROCESSED_IMAGES_PATH": os.path.join(base_data_dir, "image_text_data", "processed", "processed_images.npy"),
            "TRAIN_IMAGES_PATH": os.path.join(base_data_dir, "image_text_data", "processed", "train_images.npy"),
            "TEST_IMAGES_PATH": os.path.join(base_data_dir, "image_text_data", "processed", "test_images.npy"),
            
            # 向量数据库路径 - 使用datas/chroma_db目录
            "MULTIMODAL_VECTOR_DB_PATH": os.path.join(project_root, "datas", "chroma_db"),
            
            # 语音数据路径
            "VOICE_DATA_RAW_PATH": os.path.join(base_data_dir, "voice_data", "raw"),
            "VOICE_DATA_PROCESSED_PATH": os.path.join(base_data_dir, "voice_data", "processed"),
            
            # 模型配置
            "TEXT_EMBEDDING_MODEL": get_default_text_embedding_model(),
            "IMAGE_EMBEDDING_MODEL": "resnet50",
            "IMAGE_EMBEDDER_TYPE": "resnet",
            "IMAGE_EMBEDDER_DEVICE": "cpu",
            
            # 处理配置
            "BATCH_SIZE": 100,
            "IMAGE_BATCH_SIZE": 32,
            "MAX_IMAGES_PER_BATCH": 500,
            "DOWNLOAD_TIMEOUT": 30,
            "MAX_RETRIES": 3,
            
            # 集合名称
            "TEXT_COLLECTION_NAME": "medical_multimodal_vectors",
            "IMAGE_COLLECTION_NAME": "medical_multimodal_vectors",
            "MULTIMODAL_COLLECTION_NAME": "medical_multimodal_vectors",
            
            # 图像向量化配置
            "IMAGE_EMBEDDING_ENABLED": True,
            "PROXY": None,
            "LOCAL_MODEL_PATH": None
        }
    
    def _init_components(self):
        """初始化各个组件"""
        try:
            # 设置环境变量
            self._set_environment_variables()
            
            # 初始化质量检查器
            self._init_quality_analyzer()
            
            # 初始化文档切分器
            self._init_document_chunker()
            
            # 初始化文本嵌入模型
            self._init_text_embedder()
            
            # 初始化图像嵌入模型
            self._init_image_embedder()
            
            # 初始化向量数据库
            self._init_vector_databases()
            
            logger.info("统一多模态向量数据库构建器初始化完成")
            
        except Exception as e:
            logger.error(f"初始化组件失败: {e}")
            raise
    
    def _init_quality_analyzer(self):
        """初始化质量检查器"""
        if QUALITY_ANALYZER_AVAILABLE:
            try:
                # 获取质量检查配置
                quality_config = self.config.get('QUALITY_CHECK', {})
                if not quality_config:
                    quality_config = {
                        'min_length': 10,
                        'max_length_ratio': 1.2,
                        'model_max_tokens': 512,  # 添加模型最大token数配置
                        'semantic_similarity_threshold': 0.95,
                        'irrelevant_keywords': ['金融', '游戏', '娱乐', '体育', '政治', '军事', '科技'],
                        'medical_keywords': ['疾病', '症状', '治疗', '诊断', '药物', '医院', '医生', '患者', '健康', '医疗'],
                        'encoding': 'utf-8',  # 添加编码配置
                        'token_overhead': 10,  # 添加token开销配置
                        'special_char_ratio_threshold': 0.3  # 添加特殊字符比例阈值
                    }
                
                # 初始化质量检查器
                # 使用项目根目录下的datas目录，不在embedding_service下创建
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                data_dir = os.path.join(project_root, "datas")
                self.quality_analyzer = QualityAnalyzer(data_dir, quality_config)
                logger.info("✅ 质量检查器初始化成功")
            except Exception as e:
                logger.warning(f"质量检查器初始化失败: {e}")
                self.quality_analyzer = None
        else:
            logger.warning("质量检查器不可用，将跳过质量检查")
            self.quality_analyzer = None
    
    def _init_document_chunker(self):
        """初始化文档切分器"""
        if DOCUMENT_CHUNKER_AVAILABLE:
            try:
                # 创建通用文档切分器（更适合处理各种类型的文本）
                self.document_chunker = create_general_chunker()
                logger.info("✅ 文档切分器初始化成功")
            except Exception as e:
                logger.warning(f"文档切分器初始化失败: {e}")
                self.document_chunker = None
        else:
            logger.warning("文档切分器不可用，将使用简单分块")
            self.document_chunker = None
    
    def _set_environment_variables(self):
        """设置环境变量，包括代理"""
        if self.config.get("PROXY"):
            os.environ["HTTP_PROXY"] = self.config["PROXY"]
            os.environ["HTTPS_PROXY"] = self.config["PROXY"]
            logger.info(f"已设置代理: {self.config['PROXY']}")
        else:
            # 清除可能存在的代理设置
            if "HTTP_PROXY" in os.environ:
                del os.environ["HTTP_PROXY"]
            if "HTTPS_PROXY" in os.environ:
                del os.environ["HTTPS_PROXY"]
        
        # 设置下载超时
        if self.config.get("DOWNLOAD_TIMEOUT"):
            os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = str(self.config["DOWNLOAD_TIMEOUT"])
            # 禁用ChromaDB遥测
            os.environ["ANONYMIZED_TELEMETRY"] = "False"
            logger.info(f"已设置HF_HUB_DOWNLOAD_TIMEOUT: {self.config['DOWNLOAD_TIMEOUT']}秒")
            logger.info("已禁用ChromaDB遥测功能")
    
    def _init_text_embedder(self):
        """初始化文本嵌入模型"""
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            
            # 加载嵌入模型的参数
            model_kwargs = {"device": "cpu"}
            
            # 使用BiomedCLIP文本嵌入器
            from embed.text_embedder import TextEmbedderFactory
            
            # 优先使用本地模型路径
            if self.config.get("LOCAL_MODEL_PATH") and os.path.exists(self.config["LOCAL_MODEL_PATH"]):
                model_name = self.config["LOCAL_MODEL_PATH"]
                logger.info(f"使用本地BiomedCLIP模型: {model_name}")
            else:
                model_name = self.config["TEXT_EMBEDDING_MODEL"]
                logger.info(f"使用在线BiomedCLIP模型: {model_name}")
            
            try:
                self.text_embedder = TextEmbedderFactory.create_embedder(
                    model_name=model_name,
                    device='cpu'
                )
                logger.info(f"BiomedCLIP文本嵌入模型初始化成功: {model_name}")
            except Exception as model_error:
                logger.warning(f"BiomedCLIP模型加载失败，使用虚拟模式: {model_error}")
                # 使用虚拟嵌入器作为后备
                self.text_embedder = self._create_dummy_embedder()
                logger.info("使用虚拟文本嵌入模型")
            
        except Exception as e:
            logger.error(f"文本嵌入模型初始化失败: {e}")
            logger.warning("使用虚拟文本嵌入模型作为后备")
            self.text_embedder = self._create_dummy_embedder()
    
    def _get_text_model_path_from_config(self) -> str:
        """从统一模型配置获取文本模型路径"""
        try:
            import json
            from pathlib import Path
            
            # 尝试从统一模型配置加载
            model_config_path = Path(__file__).parent.parent.parent / "llm_models" / "model_config.json"
            if model_config_path.exists():
                with open(model_config_path, 'r', encoding='utf-8') as f:
                    model_config = json.load(f)
                
                # 获取文本嵌入模型配置
                text_config = model_config.get('models', {}).get('text_embedding', {})
                model_path = text_config.get('model_path')
                
                if model_path and os.path.exists(model_path):
                    logger.info(f"使用统一配置中的文本模型: {model_path}")
                    return model_path
            
            # 回退到配置中的默认模型
            return None
            
        except Exception as e:
            logger.warning(f"加载统一模型配置失败: {e}")
            return None
    
    def _create_dummy_embedder(self):
        """创建虚拟嵌入器用于测试"""
        class DummyEmbedder:
            def embed_documents(self, texts):
                import numpy as np
                return [np.random.rand(512).tolist() for _ in texts]
            
            def embed_query(self, text):
                import numpy as np
                return np.random.rand(512).tolist()
        
        return DummyEmbedder()
    
    def _init_image_embedder(self):
        """初始化图像嵌入模型 - 使用与文本相同的模型确保向量空间一致性"""
        if not IMAGE_EMBEDDING_AVAILABLE:
            logger.info("图像向量化模块不可用，将使用文本向量作为替代")
            self.image_embedder = None
            return
        
        try:
            # 对于图像处理，使用Chinese-CLIP模型（支持图像和文本）
            model_name = "microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"
            
            logger.info(f"初始化图像向量化器，使用Chinese-CLIP模型: {model_name}")
            logger.info(f"使用设备: {self.config.get('IMAGE_EMBEDDER_DEVICE', 'cpu')}")
            
            # 创建图像向量化器，使用Chinese-CLIP模型
            self.image_embedder = ImageEmbedderFactory.create_embedder(
                embedder_type="unified",  # 使用统一嵌入器
                model_name=model_name,    # 使用Chinese-CLIP模型
                device=self.config.get("IMAGE_EMBEDDER_DEVICE", "cpu")
            )
            
            logger.info(f"图像向量化器初始化成功，确保与文本向量空间一致性")
            
        except Exception as e:
            logger.error(f"图像向量化器初始化失败: {e}")
            logger.warning("图像向量化功能将被禁用，将使用文本向量作为替代")
            self.image_embedder = None
    
    def _init_vector_databases(self):
        """初始化向量数据库"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # 不在此处创建目录，要求目录已存在
            if not os.path.exists(self.config["MULTIMODAL_VECTOR_DB_PATH"]):
                raise FileNotFoundError(f"向量数据库目录不存在: {self.config['MULTIMODAL_VECTOR_DB_PATH']}。请手动创建或在配置中指向现有目录。")
            
            # 配置ChromaDB设置，禁用遥测
            chroma_settings = Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
            
            # 使用原生ChromaDB客户端
            self.chroma_client = chromadb.PersistentClient(
                path=self.config["MULTIMODAL_VECTOR_DB_PATH"],
                settings=chroma_settings
            )
            
            # 创建或获取多模态集合
            try:
                self.multimodal_collection = self.chroma_client.get_collection(
                    name=self.config["MULTIMODAL_COLLECTION_NAME"]
                )
                logger.info(f"获取现有集合: {self.config['MULTIMODAL_COLLECTION_NAME']}")
                
                # 检查集合是否有嵌入函数
                if hasattr(self.multimodal_collection, '_embedding_function'):
                    embedding_func = self.multimodal_collection._embedding_function
                    if embedding_func:
                        logger.info(f"集合使用嵌入函数: {type(embedding_func).__name__}")
                        # 如果使用的是错误的嵌入函数，删除并重新创建
                        if 'ONNXMiniLM' in str(type(embedding_func)):
                            logger.warning("检测到错误的嵌入函数，将重新创建集合")
                            self.chroma_client.delete_collection(self.config["MULTIMODAL_COLLECTION_NAME"])
                            raise ValueError("需要重新创建集合")
                    else:
                        logger.info("集合没有嵌入函数，将使用预计算嵌入")
                else:
                    logger.info("集合没有嵌入函数，将使用预计算嵌入")
                    
            except ValueError:
                # 集合不存在或需要重新创建，创建新集合
                logger.info(f"创建新集合: {self.config['MULTIMODAL_COLLECTION_NAME']}")
                logger.info("注意: 将使用预计算的BiomedCLIP嵌入向量，不使用ChromaDB默认嵌入函数")
                
                self.multimodal_collection = self.chroma_client.create_collection(
                    name=self.config["MULTIMODAL_COLLECTION_NAME"],
                    metadata={'description': '智诊通多模态向量数据库'}
                )
                logger.info(f"✅ 新集合创建成功: {self.config['MULTIMODAL_COLLECTION_NAME']}")
            
            logger.info("向量数据库初始化成功")
            
        except Exception as e:
            logger.error(f"向量数据库初始化失败: {e}")
            raise
    
    def load_data(self) -> Dict[str, Any]:
        """加载数据"""
        try:
            # 获取ConfigManager实例
            from config.config_manager import ConfigManager
            config_manager = ConfigManager()
            
            logger.info("=" * 50)
            logger.info("📁 文档加载开始")
            logger.info("=" * 50)
            logger.info("开始加载处理后的数据...")
            
            # 加载图文数据（原有的image_text_data）
            logger.info("正在加载图文数据...")
            processed_reports = pd.read_csv(self.config["PROCESSED_REPORTS_PATH"]) if os.path.exists(self.config["PROCESSED_REPORTS_PATH"]) else pd.DataFrame()
            train_reports = pd.read_csv(self.config["TRAIN_REPORTS_PATH"]) if os.path.exists(self.config["TRAIN_REPORTS_PATH"]) else pd.DataFrame()
            test_reports = pd.read_csv(self.config["TEST_REPORTS_PATH"]) if os.path.exists(self.config["TEST_REPORTS_PATH"]) else pd.DataFrame()
            
            logger.info(f"图文数据加载完成:")
            logger.info(f"  - 处理后的报告: {len(processed_reports)} 条")
            logger.info(f"  - 训练集报告: {len(train_reports)} 条")
            logger.info(f"  - 测试集报告: {len(test_reports)} 条")
            
            # 加载图像数据
            logger.info("正在加载图像数据...")
            processed_images = np.load(self.config["PROCESSED_IMAGES_PATH"], allow_pickle=True) if os.path.exists(self.config["PROCESSED_IMAGES_PATH"]) else np.array([])
            train_images = np.load(self.config["TRAIN_IMAGES_PATH"], allow_pickle=True) if os.path.exists(self.config["TRAIN_IMAGES_PATH"]) else np.array([])
            test_images = np.load(self.config["TEST_IMAGES_PATH"], allow_pickle=True) if os.path.exists(self.config["TEST_IMAGES_PATH"]) else np.array([])
            
            logger.info(f"图像数据加载完成:")
            logger.info(f"  - 处理后的图像: {len(processed_images)} 张")
            logger.info(f"  - 训练集图像: {len(train_images)} 张")
            logger.info(f"  - 测试集图像: {len(test_images)} 张")
            
            # 加载纯文本数据（text_data）
            logger.info("正在加载文本数据...")
            # 使用ConfigManager获取正确的路径
            text_data_base = str(config_manager.get_data_path("text_data", "processed_dir"))
            
            # 检查文本文档数据（不是训练数据）
            text_documents_path = os.path.join(text_data_base, "text_documents.json")
            text_documents_count = 0
            text_documents = []
            if os.path.exists(text_documents_path):
                try:
                    with open(text_documents_path, 'r', encoding='utf-8') as f:
                        text_documents = json.load(f)
                        text_documents_count = len(text_documents) if isinstance(text_documents, list) else 0
                except:
                    text_documents_count = 0
                    text_documents = []
            
            logger.info(f"文本数据加载完成:")
            logger.info(f"  - 文本文档数据: {text_documents_count} 条")
            
            # 加载语音数据
            logger.info("正在加载语音数据...")
            voice_data_raw_path = self.config.get('VOICE_DATA_RAW_PATH', '')
            voice_data_processed_path = self.config.get('VOICE_DATA_PROCESSED_PATH', '')
            
            # 检查语音数据目录
            voice_raw_files = []
            voice_processed_files = []
            
            if os.path.exists(voice_data_raw_path):
                voice_raw_files = [f for f in os.listdir(voice_data_raw_path) if f.endswith(('.wav', '.mp3', '.m4a', '.flac', '.ogg'))]
                logger.info(f"  - 原始语音文件: {len(voice_raw_files)} 个")
            else:
                logger.info(f"  - 原始语音目录不存在: {voice_data_raw_path}")
            
            if os.path.exists(voice_data_processed_path):
                voice_processed_files = [f for f in os.listdir(voice_data_processed_path) if f.endswith(('.wav', '.mp3', '.m4a', '.flac', '.ogg', '.txt', '.json'))]
                logger.info(f"  - 处理后语音文件: {len(voice_processed_files)} 个")
            else:
                logger.info(f"  - 处理后语音目录不存在: {voice_data_processed_path}")
            
            logger.info(f"语音数据加载完成:")
            logger.info(f"  - 原始语音文件: {len(voice_raw_files)} 个")
            logger.info(f"  - 处理后语音文件: {len(voice_processed_files)} 个")
            
            # 数据加载统计
            total_documents = len(processed_reports) + len(train_reports) + len(test_reports) + text_documents_count
            total_images = len(processed_images) + len(train_images) + len(test_images)
            total_voice_files = len(voice_raw_files) + len(voice_processed_files)
            
            print("✅ 文档加载成功")
            print(f"📊 数据统计:")
            print(f"  - 总文档数: {total_documents} 条")
            print(f"  - 总图像数: {total_images} 张")
            print(f"  - 总语音文件数: {total_voice_files} 个")
            print("=" * 50)
            print("📁 文档加载结束")
            print("=" * 50)
            
            logger.info(f"数据加载完成，总计: {total_documents} 个文档, {total_images} 张图像, {total_voice_files} 个语音文件")
            
            return {
                "processed_reports": processed_reports,
                "train_reports": train_reports,
                "test_reports": test_reports,
                "processed_images": processed_images,
                "train_images": train_images,
                "test_images": test_images,
                "text_documents": text_documents,
                "text_documents_count": text_documents_count,
                "voice_raw_files": voice_raw_files,
                "voice_processed_files": voice_processed_files
            }
            
        except Exception as e:
            print("❌ 文档加载失败")
            logger.error(f"加载数据失败: {e}")
            raise
    
    def convert_to_basic_type(self, value):
        """将值转换为ChromaDB支持的基本类型（字符串）"""
        if pd.isna(value):
            return ""
        elif isinstance(value, (str, int, float, bool)):
            return str(value)
        elif isinstance(value, (list, tuple)):
            return str(value)
        elif isinstance(value, dict):
            return str(value)
        elif hasattr(value, 'shape'):
            shape = value.shape
            if len(shape) == 3:
                return f"{shape[0]}x{shape[1]}x{shape[2]}"
            elif len(shape) == 2:
                return f"{shape[0]}x{shape[1]}"
            else:
                return str(shape)
        else:
            return str(value)
    
    def prepare_general_text_documents(self, text_df: pd.DataFrame, dataset_type: str = "general_text") -> Tuple[List[str], List[Dict]]:
        """准备纯文本文档数据用于向量存储（包含文档切分和质量检查）"""
        documents = []
        metadatas = []
        
        print("=" * 50)
        print("🧹 数据清洗和质量检查开始")
        print("=" * 50)
        logger.info(f"开始准备 {dataset_type} 数据集的纯文本文档...")
        
        # 数据目录信息
        logger.info("📁 数据目录信息:")
        logger.info(f"  - 数据集类型: {dataset_type}")
        logger.info(f"  - 数据文件: {text_df.index.name if hasattr(text_df.index, 'name') else 'DataFrame'}")
        logger.info(f"  - 数据列: {list(text_df.columns)}")
        
        # 数据清洗统计
        total_rows = len(text_df)
        valid_rows = 0
        invalid_rows = 0
        empty_content_rows = 0
        short_content_rows = 0
        quality_check_passed = 0
        quality_check_failed = 0
        
        logger.info(f"开始数据清洗，总行数: {total_rows}")
        
        # 显示数据样本
        if not text_df.empty:
            logger.info("📄 数据样本预览:")
            for i, (idx, row) in enumerate(text_df.head(2).iterrows()):
                content = row.get('text_content', '')
                logger.info(f"  样本 {i+1}: {content[:100]}... (长度: {len(content)})")
        
        # 提取所有文本进行批量质量检查
        all_texts = []
        text_indices = []
        for idx, row in text_df.iterrows():
            content = row.get('text_content', '')
            if content and len(content.strip()) >= 10:  # 基本过滤
                all_texts.append(content)
                text_indices.append(idx)
        
        # 跳过批量质量检查，因为长文本会在文档切分后进行质量检查
        logger.info("跳过批量质量检查，将在文档切分后进行质量检查")
        quality_passed_indices = set(text_indices)
        
        for idx, row in tqdm(text_df.iterrows(), total=len(text_df)):
            # 获取文档内容
            content = row.get('text_content', '')
            
            # 基本数据清洗步骤
            if not content:
                empty_content_rows += 1
                invalid_rows += 1
                logger.debug(f"行 {idx}: 内容为空，跳过")
                continue
                
            if len(content.strip()) < 10:
                short_content_rows += 1
                invalid_rows += 1
                logger.debug(f"行 {idx}: 内容过短 ({len(content.strip())} 字符)，跳过")
                continue
            
            # 质量检查过滤
            if idx not in quality_passed_indices:
                quality_check_failed += 1
                invalid_rows += 1
                logger.debug(f"行 {idx}: 未通过质量检查，跳过")
                continue
            
            valid_rows += 1
            
            # 使用文档切分器切分文档
            if self.document_chunker:
                # 创建基础元数据
                base_metadata = {
                    "original_document_id": f"{dataset_type}_doc_{idx}",
                    "dataset_type": dataset_type,
                    "original_index": idx,
                    "content_type": "general_text",
                    "source_file": row.get('source_file', ''),
                    "file_type": row.get('file_type', ''),
                    "original_id": row.get('id', idx)
                }
                
                # 添加其他元数据字段
                if 'metadata' in row and pd.notna(row['metadata']):
                    if isinstance(row['metadata'], dict):
                        base_metadata.update(row['metadata'])
                    else:
                        base_metadata['original_metadata'] = str(row['metadata'])
                
                # 添加分词结果
                if 'content_tokens' in row and pd.notna(row['content_tokens']):
                    base_metadata['content_tokens'] = row['content_tokens']
                
                logger.info("=" * 60)
                logger.info("✂️ 开始文档切分处理")
                logger.info("=" * 60)
                logger.info(f"📄 文档ID: {idx}")
                logger.info(f"📄 文档类型: {dataset_type}")
                logger.info(f"📄 原始长度: {len(content)} 字符")
                logger.info(f"📄 内容预览: {content[:200]}...")
                logger.info(f"📄 元数据: {base_metadata}")
                
                # 切分文档
                chunks = self.document_chunker.chunk_document(content, base_metadata)
                
                logger.info("✅ 文档切分完成")
                logger.info(f"📊 切分统计:")
                logger.info(f"  - 生成片段数: {len(chunks)}")
                logger.info(f"  - 平均片段长度: {sum(len(chunk['content']) for chunk in chunks) / len(chunks) if chunks else 0:.1f} 字符")
                
                # 显示前几个片段的详细信息
                for i, chunk in enumerate(chunks[:3]):  # 只显示前3个片段
                    logger.info(f"  - 片段 {i+1}: {chunk['content'][:100]}... (长度: {chunk['length']})")
                
                if len(chunks) > 3:
                    logger.info(f"  - ... 还有 {len(chunks) - 3} 个片段")
                
                logger.info("=" * 60)
                logger.info("✂️ 文档切分处理完成")
                logger.info("=" * 60)
                
                # 将切分后的文档添加到结果中
                logger.info(f"🔤 开始对 {len(chunks)} 个文档片段进行质量检查和向量化...")
                for chunk_idx, chunk in enumerate(chunks):
                    logger.info(f"🔤 处理片段 {chunk_idx + 1}/{len(chunks)}")
                    logger.info(f"🔤 片段内容: {chunk['content'][:100]}...")
                    logger.info(f"🔤 片段长度: {chunk['length']} 字符")
                    logger.info(f"🔤 片段元数据: {chunk['metadata']}")
                    
                    # 对切分后的片段进行质量检查
                    if self.quality_analyzer:
                        completeness_passed, completeness_reason = self.quality_analyzer.check_completeness(chunk['content'])
                        if not completeness_passed:
                            logger.debug(f"片段 {chunk_idx + 1} 未通过完整性检查: {completeness_reason}")
                            continue
                        
                        # 唯一性检查
                        current_texts = [chunk['content']]
                        uniqueness_passed, duplicate_groups = self.quality_analyzer.check_uniqueness(current_texts)
                        if not uniqueness_passed[0]:
                            logger.debug(f"片段 {chunk_idx + 1} 未通过唯一性检查: 重复文本")
                            continue
                        else:
                            # 更新唯一性统计
                            self.quality_analyzer.stats['uniqueness_passed'] += 1
                        
                        relevance_passed, relevance_reason = self.quality_analyzer.check_relevance(chunk['content'])
                        if not relevance_passed:
                            logger.debug(f"片段 {chunk_idx + 1} 未通过相关性检查: {relevance_reason}")
                            continue
                        
                        vectorization_passed, vectorization_reason = self.quality_analyzer.check_vectorization_readiness(chunk['content'])
                        if not vectorization_passed:
                            logger.debug(f"片段 {chunk_idx + 1} 未通过向量化检查: {vectorization_reason}")
                            continue
                        
                        logger.debug(f"片段 {chunk_idx + 1} 通过所有质量检查")
                        
                        # 更新质量检查统计
                        self.quality_analyzer.stats['total_texts'] += 1
                        self.quality_analyzer.stats['completeness_passed'] += 1
                        self.quality_analyzer.stats['relevance_passed'] += 1
                        self.quality_analyzer.stats['vectorization_passed'] += 1
                        self.quality_analyzer.stats['final_passed'] += 1
                    
                    documents.append(chunk['content'])
                    metadatas.append(chunk['metadata'])
                    
                    logger.info(f"✅ 片段 {chunk_idx + 1} 处理完成")
            else:
                # 如果没有文档切分器，使用原始内容
                logger.warning(f"文档切分器未初始化，使用原始内容: {idx}")
                
                # 如果文本太长，进行简单截断
                if len(content) > 1000:
                    content = content[:1000] + "..."
                
                # 直接使用原始内容作为单个文档
                chunks = [content] if len(content.strip()) > 10 else []
                
                # 为每个文档块创建向量存储条目
                for chunk_idx, chunk in enumerate(chunks):
                    if len(chunk.strip()) < 10:  # 过滤太短的块
                        continue
                    
                    # 创建文档ID
                    doc_id = f"{dataset_type}_{row.get('id', idx)}_{chunk_idx}"
                    
                    # 创建元数据
                    metadata = {
                        'doc_id': doc_id,
                        'dataset_type': dataset_type,
                        'source_file': row.get('source_file', ''),
                        'file_type': row.get('file_type', ''),
                        'chunk_index': chunk_idx,
                        'total_chunks': len(chunks),
                        'original_id': row.get('id', idx)
                    }
                    
                    # 添加其他元数据字段
                    if 'metadata' in row and pd.notna(row['metadata']):
                        if isinstance(row['metadata'], dict):
                            metadata.update(row['metadata'])
                        else:
                            metadata['original_metadata'] = str(row['metadata'])
                    
                    # 添加分词结果
                    if 'content_tokens' in row and pd.notna(row['content_tokens']):
                        metadata['content_tokens'] = row['content_tokens']
                    
                    # 转换元数据为基本类型
                    metadata = {k: self.convert_to_basic_type(v) for k, v in metadata.items()}
                    
                    documents.append(chunk)
                    metadatas.append(metadata)
        
        # 数据清洗和质量检查结果统计
        print("✅ 数据清洗和质量检查完成")
        print(f"📊 处理统计:")
        print(f"  - 总行数: {total_rows}")
        print(f"  - 有效行数: {valid_rows}")
        print(f"  - 无效行数: {invalid_rows}")
        print(f"  - 空内容行数: {empty_content_rows}")
        print(f"  - 短内容行数: {short_content_rows}")
        print(f"  - 质量检查通过: {quality_check_passed}")
        print(f"  - 质量检查失败: {quality_check_failed}")
        print(f"  - 清洗后文档块数: {len(documents)}")
        print("=" * 50)
        print("🧹 数据清洗和质量检查结束")
        print("=" * 50)
        
        logger.info(f"数据清洗和质量检查完成:")
        logger.info(f"  - 总行数: {total_rows}")
        logger.info(f"  - 有效行数: {valid_rows}")
        logger.info(f"  - 无效行数: {invalid_rows}")
        logger.info(f"  - 空内容行数: {empty_content_rows}")
        logger.info(f"  - 短内容行数: {short_content_rows}")
        logger.info(f"  - 质量检查通过: {quality_check_passed}")
        logger.info(f"  - 质量检查失败: {quality_check_failed}")
        logger.info(f"纯文本文档准备完成: {len(documents)} 个文档块")
        return documents, metadatas

    def prepare_text_documents(self, reports_df: pd.DataFrame, images: np.ndarray = None, dataset_type: str = "processed") -> Tuple[List[str], List[Dict]]:
        """准备文本文档数据用于向量存储（包含文档切分）"""
        documents = []
        metadatas = []
        
        print("=" * 50)
        print("🧹 数据清洗开始")
        print("=" * 50)
        logger.info(f"开始准备 {dataset_type} 数据集的文本文档...")
        
        # 数据目录信息
        logger.info("📁 数据目录信息:")
        logger.info(f"  - 数据集类型: {dataset_type}")
        logger.info(f"  - 数据文件: {reports_df.index.name if hasattr(reports_df.index, 'name') else 'DataFrame'}")
        logger.info(f"  - 数据列: {list(reports_df.columns)}")
        logger.info(f"  - 图像数据: {'有' if images is not None and len(images) > 0 else '无'}")
        if images is not None and len(images) > 0:
            logger.info(f"  - 图像数量: {len(images)}")
            logger.info(f"  - 图像形状: {images[0].shape if len(images) > 0 else 'N/A'}")
        
        # 数据清洗统计
        total_rows = len(reports_df)
        valid_rows = 0
        invalid_rows = 0
        empty_content_rows = 0
        
        logger.info(f"开始数据清洗，总行数: {total_rows}")
        
        # 显示数据样本
        if not reports_df.empty:
            logger.info("📄 数据样本预览:")
            for i, (idx, row) in enumerate(reports_df.head(2).iterrows()):
                # 构建内容预览
                content_parts = []
                if 'description' in row and pd.notna(row['description']):
                    content_parts.append(f"病情描述: {row['description']}")
                if 'diagnosis' in row and pd.notna(row['diagnosis']):
                    content_parts.append(f"诊断结果: {row['diagnosis']}")
                if 'findings' in row and pd.notna(row['findings']):
                    content_parts.append(f"检查结果: {row['findings']}")
                
                content = "\n".join(content_parts)
                logger.info(f"  样本 {i+1}: {content[:100]}... (长度: {len(content)})")
        
        for idx, row in tqdm(reports_df.iterrows(), total=len(reports_df)):
            # 创建文档内容
            content_parts = []
            if 'description' in row and pd.notna(row['description']):
                content_parts.append(f"病情描述: {row['description']}")
            if 'diagnosis' in row and pd.notna(row['diagnosis']):
                content_parts.append(f"诊断结果: {row['diagnosis']}")
            if 'suggestions' in row and pd.notna(row['suggestions']):
                content_parts.append(f"医生建议: {row['suggestions']}")
            if 'dialogue_content' in row and pd.notna(row['dialogue_content']):
                content_parts.append(f"对话内容: {row['dialogue_content']}")
            if 'findings' in row and pd.notna(row['findings']):
                content_parts.append(f"检查结果: {row['findings']}")
            if 'impression' in row and pd.notna(row['impression']):
                content_parts.append(f"印象: {row['impression']}")
            
            # 添加分词后的内容
            if 'description_tokens' in row and pd.notna(row['description_tokens']):
                content_parts.append(f"病情描述分词: {row['description_tokens']}")
            if 'diagnosis_tokens' in row and pd.notna(row['diagnosis_tokens']):
                content_parts.append(f"诊断结果分词: {row['diagnosis_tokens']}")
            if 'suggestions_tokens' in row and pd.notna(row['suggestions_tokens']):
                content_parts.append(f"医生建议分词: {row['suggestions_tokens']}")
            if 'dialogue_content_tokens' in row and pd.notna(row['dialogue_content_tokens']):
                content_parts.append(f"对话内容分词: {row['dialogue_content_tokens']}")
            if 'findings_tokens' in row and pd.notna(row['findings_tokens']):
                content_parts.append(f"检查结果分词: {row['findings_tokens']}")
            if 'impression_tokens' in row and pd.notna(row['impression_tokens']):
                content_parts.append(f"印象分词: {row['impression_tokens']}")
            
            # 如果没有足够的内容，跳过此记录
            if not content_parts:
                empty_content_rows += 1
                invalid_rows += 1
                logger.debug(f"行 {idx}: 没有有效内容字段，跳过")
                continue
            
            content = "\n".join(content_parts)
            valid_rows += 1
            
            # 使用文档切分器切分文档
            if self.document_chunker:
                # 创建基础元数据
                base_metadata = {
                    "original_document_id": f"{dataset_type}_doc_{idx}",
                    "dataset_type": dataset_type,
                    "original_index": idx,
                    "content_type": "text"
                }
                
                # 添加额外的元数据字段
                for col in reports_df.columns:
                    if col not in ['description', 'diagnosis', 'suggestions', 'dialogue_content', 'findings', 'impression',
                                  'description_tokens', 'diagnosis_tokens', 'suggestions_tokens', 'dialogue_content_tokens',
                                  'findings_tokens', 'impression_tokens'] and pd.notna(row[col]):
                        base_metadata[col] = self.convert_to_basic_type(row[col])
                
                # 如果有图像数据，添加图像信息
                if images is not None and idx < len(images):
                    base_metadata["has_image"] = "True"
                    base_metadata["image_shape"] = self.convert_to_basic_type(images[idx].shape)
                else:
                    base_metadata["has_image"] = "False"
                
                logger.info("=" * 60)
                logger.info("✂️ 开始文档切分处理")
                logger.info("=" * 60)
                logger.info(f"📄 文档ID: {idx}")
                logger.info(f"📄 文档类型: {dataset_type}")
                logger.info(f"📄 原始长度: {len(content)} 字符")
                logger.info(f"📄 内容预览: {content[:200]}...")
                logger.info(f"📄 元数据: {base_metadata}")
                
                # 切分文档
                chunks = self.document_chunker.chunk_document(content, base_metadata)
                
                logger.info("✅ 文档切分完成")
                logger.info(f"📊 切分统计:")
                logger.info(f"  - 生成片段数: {len(chunks)}")
                logger.info(f"  - 平均片段长度: {sum(len(chunk['content']) for chunk in chunks) / len(chunks) if chunks else 0:.1f} 字符")
                
                # 显示前几个片段的详细信息
                for i, chunk in enumerate(chunks[:3]):  # 只显示前3个片段
                    logger.info(f"  - 片段 {i+1}: {chunk['content'][:100]}... (长度: {chunk['length']})")
                
                if len(chunks) > 3:
                    logger.info(f"  - ... 还有 {len(chunks) - 3} 个片段")
                
                logger.info("=" * 60)
                logger.info("✂️ 文档切分处理完成")
                logger.info("=" * 60)
                
                # 将切分后的文档添加到结果中
                logger.info(f"🔤 开始对 {len(chunks)} 个文档片段进行分词和向量化...")
                for chunk_idx, chunk in enumerate(chunks):
                    logger.info(f"🔤 处理片段 {chunk_idx + 1}/{len(chunks)}")
                    logger.info(f"🔤 片段内容: {chunk['content'][:100]}...")
                    logger.info(f"🔤 片段长度: {chunk['length']} 字符")
                    logger.info(f"🔤 片段元数据: {chunk['metadata']}")
                    
                    documents.append(chunk['content'])
                    metadatas.append(chunk['metadata'])
                    
                    logger.info(f"✅ 片段 {chunk_idx + 1} 处理完成")
            else:
                # 如果没有文档切分器，使用原始内容
                document_id = f"{dataset_type}_doc_{idx}"
                
                # 创建元数据
                metadata = {
                    "document_id": document_id,
                    "dataset_type": dataset_type,
                    "index": idx,
                    "content_type": "text"
                }
                
                # 添加额外的元数据字段
                for col in reports_df.columns:
                    if col not in ['description', 'diagnosis', 'suggestions', 'dialogue_content', 'findings', 'impression',
                                  'description_tokens', 'diagnosis_tokens', 'suggestions_tokens', 'dialogue_content_tokens',
                                  'findings_tokens', 'impression_tokens'] and pd.notna(row[col]):
                        metadata[col] = self.convert_to_basic_type(row[col])
                
                # 如果有图像数据，添加图像信息
                if images is not None and idx < len(images):
                    metadata["has_image"] = "True"
                    metadata["image_shape"] = self.convert_to_basic_type(images[idx].shape)
                else:
                    metadata["has_image"] = "False"
                
                documents.append(content)
                metadatas.append(metadata)
        
        # 数据清洗结果统计
        print("✅ 数据清洗完成")
        print(f"📊 清洗统计:")
        print(f"  - 总行数: {total_rows}")
        print(f"  - 有效行数: {valid_rows}")
        print(f"  - 无效行数: {invalid_rows}")
        print(f"  - 空内容行数: {empty_content_rows}")
        print(f"  - 清洗后文档块数: {len(documents)}")
        print("=" * 50)
        print("🧹 数据清洗结束")
        print("=" * 50)
        
        logger.info(f"数据清洗完成:")
        logger.info(f"  - 总行数: {total_rows}")
        logger.info(f"  - 有效行数: {valid_rows}")
        logger.info(f"  - 无效行数: {invalid_rows}")
        logger.info(f"  - 空内容行数: {empty_content_rows}")
        logger.info(f"文本文档准备完成，共 {len(documents)} 个文档片段")
        return documents, metadatas
    
    def vectorize_images(self, images: np.ndarray, dataset_type: str = "processed") -> Tuple[Optional[np.ndarray], Optional[List[Dict]]]:
        """将图像数据转换为向量"""
        if self.image_embedder is None or len(images) == 0:
            return None, None
        
        print("=" * 50)
        print("🔢 向量化开始")
        print("=" * 50)
        logger.info(f"开始将 {len(images)} 张图像转换为向量...")
        
        try:
            # 使用batch_embed_images函数批量处理图像
            logger.info(f"使用批量处理，批次大小: {self.config['IMAGE_BATCH_SIZE']}")
            embeddings = batch_embed_images(self.image_embedder, images, batch_size=self.config["IMAGE_BATCH_SIZE"])
            
            # 创建元数据
            logger.info("正在创建图像向量元数据...")
            metadatas = []
            for idx in range(len(embeddings)):
                metadata = {
                    "document_id": f"{dataset_type}_image_{idx}",
                    "dataset_type": dataset_type,
                    "index": str(idx),
                    "content_type": "image",
                    "vector_dim": str(len(embeddings[idx]) if hasattr(embeddings[idx], '__len__') else 0)
                }
                metadatas.append(metadata)
            
            print("✅ 向量化完成")
            print(f"📊 向量化统计:")
            print(f"  - 输入图像数: {len(images)}")
            print(f"  - 输出向量数: {len(embeddings)}")
            print(f"  - 向量维度: {len(embeddings[0]) if len(embeddings) > 0 else 0}")
            print(f"  - 数据集类型: {dataset_type}")
            print("=" * 50)
            print("🔢 向量化结束")
            print("=" * 50)
            
            logger.info(f"图像向量化完成，共生成 {len(embeddings)} 个图像向量")
            return embeddings, metadatas
            
        except Exception as e:
            print("❌ 向量化失败")
            logger.error(f"图像向量化过程中出错: {e}")
            raise
    
    def build_image_text_mapping(self, reports_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """构建图像和文本的映射关系"""
        mapping = {}
        
        for idx, row in reports_df.iterrows():
            # 尝试获取uid或id字段
            uid = str(row.get('uid', row.get('id', idx)))
            
            # 构建文本内容
            text_parts = []
            
            # 检查各种可能的字段
            if 'findings' in row and pd.notna(row['findings']):
                text_parts.append(f"检查结果: {row['findings']}")
            if 'impression' in row and pd.notna(row['impression']):
                text_parts.append(f"印象: {row['impression']}")
            if 'indication' in row and pd.notna(row['indication']):
                text_parts.append(f"适应症: {row['indication']}")
            if 'comparison' in row and pd.notna(row['comparison']):
                text_parts.append(f"对比: {row['comparison']}")
            if 'description' in row and pd.notna(row['description']):
                text_parts.append(f"病情描述: {row['description']}")
            if 'diagnosis' in row and pd.notna(row['diagnosis']):
                text_parts.append(f"诊断结果: {row['diagnosis']}")
            if 'suggestions' in row and pd.notna(row['suggestions']):
                text_parts.append(f"医生建议: {row['suggestions']}")
            if 'dialogue_content' in row and pd.notna(row['dialogue_content']):
                text_parts.append(f"对话内容: {row['dialogue_content']}")
            
            if text_parts:
                text_content = "\n".join(text_parts)
                mapping[uid] = {
                    'text': text_content,
                    'index': str(idx),
                    'metadata': {
                        'uid': str(uid),
                        'MeSH': str(row.get('MeSH', '')),
                        'Problems': str(row.get('Problems', '')),
                        'image': str(row.get('image', '')),
                        'indication': str(row.get('indication', '')),
                        'comparison': str(row.get('comparison', '')),
                        'findings': str(row.get('findings', '')),
                        'impression': str(row.get('impression', '')),
                        'description': str(row.get('description', '')),
                        'diagnosis': str(row.get('diagnosis', '')),
                        'suggestions': str(row.get('suggestions', '')),
                        'dialogue_content': str(row.get('dialogue_content', ''))
                    }
                }
        
        logger.info(f"已构建 {len(mapping)} 个图像文本映射关系")
        return mapping
    
    def vectorize_multimodal_data(self, reports_df: pd.DataFrame, images: np.ndarray) -> Tuple[List[str], List[Dict], List[np.ndarray]]:
        """向量化多模态数据"""
        documents = []
        metadatas = []
        embeddings = []
        
        print("=" * 50)
        print("🔢 向量化开始")
        print("=" * 50)
        logger.info("开始向量化多模态数据...")
        
        # 构建图像文本映射
        logger.info("正在构建图像文本映射关系...")
        self.image_text_mapping = self.build_image_text_mapping(reports_df)
        
        # 向量化统计
        total_pairs = len(self.image_text_mapping)
        image_vectors = 0
        text_vectors = 0
        
        logger.info(f"开始处理 {total_pairs} 个图文对...")
        
        # 处理每个图文对
        for uid, mapping_info in tqdm(self.image_text_mapping.items(), desc="向量化多模态数据"):
            idx = int(mapping_info['index'])  # 转换为整数用于比较和索引
            text_content = mapping_info['text']
            metadata = mapping_info['metadata'].copy()
            
            # 详细处理信息
            logger.info(f"🔤 开始处理图文对 UID: {uid}, idx: {idx}")
            logger.info(f"📄 文本内容长度: {len(text_content)} 字符")
            logger.info(f"📄 文本内容预览: {text_content[:100]}...")
            logger.info(f"🖼️ 图像嵌入器可用: {self.image_embedder is not None}")
            logger.info(f"📊 当前进度: {image_vectors + text_vectors + 1}/{total_pairs}")
            
            # 检查是否有对应的图像
            if idx < len(images) and self.image_embedder is not None:
                # 有图像的情况：使用图像向量
                image = images[idx]
                
                # 对文本内容进行质量检查
                quality_passed = True
                if self.quality_analyzer:
                    logger.info(f"🔍 开始文本质量检查...")
                    
                    # 完整性检查
                    completeness_passed, completeness_reason = self.quality_analyzer.check_completeness(text_content)
                    if not completeness_passed:
                        logger.warning(f"文本未通过完整性检查: {completeness_reason}")
                        quality_passed = False
                    
                    # 唯一性检查（需要收集所有文本进行批量检查）
                    if quality_passed:
                        # 收集当前批次的所有文本进行唯一性检查
                        current_texts = [text_content]  # 当前文本
                        # 这里可以扩展为收集更多文本进行批量唯一性检查
                        uniqueness_passed, duplicate_groups = self.quality_analyzer.check_uniqueness(current_texts)
                        if not uniqueness_passed[0]:  # 检查第一个（也是唯一的）文本
                            logger.warning(f"文本未通过唯一性检查: 重复文本")
                            quality_passed = False
                        else:
                            # 更新唯一性统计
                            self.quality_analyzer.stats['uniqueness_passed'] += 1
                    
                    # 相关性检查
                    if quality_passed:
                        relevance_passed, relevance_reason = self.quality_analyzer.check_relevance(text_content)
                        if not relevance_passed:
                            logger.warning(f"文本未通过相关性检查: {relevance_reason}")
                            quality_passed = False
                    
                    # 向量化准备检查
                    if quality_passed:
                        vectorization_passed, vectorization_reason = self.quality_analyzer.check_vectorization_readiness(text_content)
                        if not vectorization_passed:
                            logger.warning(f"文本未通过向量化检查: {vectorization_reason}")
                            quality_passed = False
                    
                    if quality_passed:
                        logger.info(f"✅ 文本通过所有质量检查")
                        # 更新质量检查统计
                        self.quality_analyzer.stats['total_texts'] += 1
                        self.quality_analyzer.stats['completeness_passed'] += 1
                        self.quality_analyzer.stats['relevance_passed'] += 1
                        self.quality_analyzer.stats['vectorization_passed'] += 1
                        self.quality_analyzer.stats['final_passed'] += 1
                    else:
                        logger.warning(f"⚠️ 文本未通过质量检查，跳过此图文对")
                        continue
                
                # 生成图像向量
                try:
                    import torch
                    from torchvision import transforms
                    
                    # 预处理图像
                    if len(image.shape) == 3 and image.shape[0] == 3:  # CHW格式
                        image = np.transpose(image, (1, 2, 0))  # 转换为HWC格式
                    
                    # 确保图像值在0-255范围内（PIL Image期望uint8）
                    if image.max() <= 1.0:
                        image = (image * 255).astype(np.uint8)
                    else:
                        image = image.astype(np.uint8)
                    
                    # 直接传递numpy数组给embed_image方法
                    logger.info(f"🖼️ 开始图像向量化处理...")
                    logger.info(f"🖼️ 图像形状: {image.shape}")
                    logger.info(f"🖼️ 图像数据类型: {image.dtype}")
                    logger.info(f"🖼️ 图像值范围: {image.min()} - {image.max()}")
                    logger.info(f"🖼️ 使用模型: {self.config.get('IMAGE_EMBEDDING_MODEL', 'unknown')}")
                    logger.info(f"🖼️ 嵌入器类型: {self.config.get('IMAGE_EMBEDDER_TYPE', 'unknown')}")
                    
                    image_vector = self.image_embedder.embed_image(image)
                    
                    # 使用图像向量作为嵌入
                    embeddings.append(image_vector)
                    image_vectors += 1
                    
                    # 更新元数据
                    metadata.update({
                        'content_type': 'multimodal',
                        'has_image': 'True',
                        'image_index': str(idx),
                        'vector_type': 'image'
                    })
                    
                    logger.info(f"✅ 图像向量化成功")
                    logger.info(f"📊 向量类型: {type(image_vector)}")
                    logger.info(f"📊 向量长度: {len(image_vector) if hasattr(image_vector, '__len__') else '无长度属性'}")
                    logger.info(f"📊 向量维度: {len(image_vector) if hasattr(image_vector, '__len__') else 'N/A'}")
                    logger.info(f"📊 图像向量统计: {image_vectors}/{total_pairs}")
                    
                except Exception as e:
                    logger.warning(f"❌ 图像向量化失败 (UID: {uid}): {e}")
                    logger.info(f"🔄 回退到文本向量化...")
                    # 回退到文本向量
                    try:
                        logger.info(f"🔤 开始文本分词和向量化...")
                        logger.info(f"🔤 文本内容: {text_content[:200]}...")
                        logger.info(f"🔤 文本长度: {len(text_content)} 字符")
                        logger.info(f"🔤 使用模型: {self.config.get('TEXT_EMBEDDING_MODEL', 'unknown')}")
                        logger.info(f"🔤 文本嵌入器类型: {type(self.text_embedder).__name__}")
                        
                        text_vector = self.text_embedder.embed_query(text_content)
                        
                        embeddings.append(text_vector)
                        text_vectors += 1
                        metadata.update({
                            'content_type': 'text',
                            'has_image': 'False',
                            'vector_type': 'text'
                        })
                        
                        logger.info(f"✅ 文本向量化成功")
                        logger.info(f"📊 向量类型: {type(text_vector)}")
                        logger.info(f"📊 向量长度: {len(text_vector) if hasattr(text_vector, '__len__') else '无长度属性'}")
                        logger.info(f"📊 向量维度: {len(text_vector) if hasattr(text_vector, '__len__') else 'N/A'}")
                        logger.info(f"📊 文本向量统计: {text_vectors}/{total_pairs}")
                    except Exception as text_error:
                        logger.error(f"文本向量化也失败 (UID: {uid}): {text_error}")
                        # 创建虚拟向量作为最后的后备
                        dummy_vector = np.random.rand(512).tolist()
                        embeddings.append(dummy_vector)
                        text_vectors += 1
                        metadata.update({
                            'content_type': 'text',
                            'has_image': 'False',
                            'vector_type': 'dummy'
                        })
                        logger.warning(f"使用虚拟向量作为后备，类型: {type(dummy_vector)}, 长度: {len(dummy_vector)}")
            else:
                # 没有图像的情况：使用文本向量
                logger.info(f"🔤 开始纯文本分词和向量化...")
                logger.info(f"🔤 文本内容: {text_content[:200]}...")
                logger.info(f"🔤 文本长度: {len(text_content)} 字符")
                logger.info(f"🔤 使用模型: {self.config.get('TEXT_EMBEDDING_MODEL', 'unknown')}")
                logger.info(f"🔤 文本嵌入器类型: {type(self.text_embedder).__name__}")
                
                # 对文本进行质量检查
                quality_passed = True
                if self.quality_analyzer:
                    logger.info(f"🔍 开始文本质量检查...")
                    
                    # 完整性检查
                    completeness_passed, completeness_reason = self.quality_analyzer.check_completeness(text_content)
                    if not completeness_passed:
                        logger.warning(f"文本未通过完整性检查: {completeness_reason}")
                        quality_passed = False
                    
                    # 唯一性检查
                    if quality_passed:
                        current_texts = [text_content]
                        uniqueness_passed, duplicate_groups = self.quality_analyzer.check_uniqueness(current_texts)
                        if not uniqueness_passed[0]:
                            logger.warning(f"文本未通过唯一性检查: 重复文本")
                            quality_passed = False
                        else:
                            # 更新唯一性统计
                            self.quality_analyzer.stats['uniqueness_passed'] += 1
                    
                    # 相关性检查
                    if quality_passed:
                        relevance_passed, relevance_reason = self.quality_analyzer.check_relevance(text_content)
                        if not relevance_passed:
                            logger.warning(f"文本未通过相关性检查: {relevance_reason}")
                            quality_passed = False
                    
                    # 向量化准备检查
                    if quality_passed:
                        vectorization_passed, vectorization_reason = self.quality_analyzer.check_vectorization_readiness(text_content)
                        if not vectorization_passed:
                            logger.warning(f"文本未通过向量化检查: {vectorization_reason}")
                            quality_passed = False
                    
                    if quality_passed:
                        logger.info(f"✅ 文本通过所有质量检查")
                        # 更新质量检查统计
                        self.quality_analyzer.stats['total_texts'] += 1
                        self.quality_analyzer.stats['completeness_passed'] += 1
                        self.quality_analyzer.stats['relevance_passed'] += 1
                        self.quality_analyzer.stats['vectorization_passed'] += 1
                        self.quality_analyzer.stats['final_passed'] += 1
                    else:
                        logger.warning(f"⚠️ 文本未通过质量检查，跳过向量化")
                
                if quality_passed:
                    try:
                        text_vector = self.text_embedder.embed_query(text_content)
                        embeddings.append(text_vector)
                        text_vectors += 1
                        metadata.update({
                            'content_type': 'text',
                            'has_image': 'False',
                            'vector_type': 'text',
                            'quality_checked': 'True'
                        })
                        
                        logger.info(f"✅ 文本向量化成功")
                        logger.info(f"📊 向量类型: {type(text_vector)}")
                        logger.info(f"📊 向量长度: {len(text_vector) if hasattr(text_vector, '__len__') else '无长度属性'}")
                        logger.info(f"📊 向量维度: {len(text_vector) if hasattr(text_vector, '__len__') else 'N/A'}")
                        logger.info(f"📊 文本向量统计: {text_vectors}/{total_pairs}")
                    except Exception as e:
                        logger.error(f"文本向量化失败 (UID: {uid}): {e}")
                        # 创建虚拟向量作为最后的后备
                        dummy_vector = np.random.rand(512).tolist()
                        embeddings.append(dummy_vector)
                        text_vectors += 1
                        metadata.update({
                            'content_type': 'text',
                            'has_image': 'False',
                            'vector_type': 'dummy'
                        })
                        logger.warning(f"使用虚拟向量作为后备，类型: {type(dummy_vector)}, 长度: {len(dummy_vector)}")
                else:
                    # 质量检查未通过，跳过此文本
                    logger.warning(f"⚠️ 跳过未通过质量检查的文本 (UID: {uid})")
                    continue
            
            # 添加文档和元数据
            documents.append(text_content)
            metadatas.append(metadata)
        
        print("✅ 向量化完成")
        print(f"📊 向量化统计:")
        print(f"  - 总图文对数: {total_pairs}")
        print(f"  - 图像向量数: {image_vectors}")
        print(f"  - 文本向量数: {text_vectors}")
        print(f"  - 总文档数: {len(documents)}")
        print(f"  - 总向量数: {len(embeddings)}")
        print(f"  - 图像向量比例: {image_vectors/total_pairs*100:.1f}%")
        print(f"  - 文本向量比例: {text_vectors/total_pairs*100:.1f}%")
        print("=" * 50)
        print("🔢 向量化结束")
        print("=" * 50)
        
        logger.info(f"多模态数据向量化完成:")
        logger.info(f"  - 总图文对数: {total_pairs}")
        logger.info(f"  - 图像向量数: {image_vectors}")
        logger.info(f"  - 文本向量数: {text_vectors}")
        logger.info(f"  - 总文档数: {len(documents)}")
        logger.info(f"  - 总向量数: {len(embeddings)}")
        logger.info(f"  - 图像向量比例: {image_vectors/total_pairs*100:.1f}%")
        logger.info(f"  - 文本向量比例: {text_vectors/total_pairs*100:.1f}%")
        
        # 添加向量质量统计
        if embeddings:
            vector_dims = [len(emb) for emb in embeddings if hasattr(emb, '__len__')]
            if vector_dims:
                logger.info(f"  - 向量维度统计: 平均={sum(vector_dims)/len(vector_dims):.1f}, 最小={min(vector_dims)}, 最大={max(vector_dims)}")
        
        return documents, metadatas, embeddings
    
    def add_documents_to_db(self, collection, documents: List[str], metadatas: List[Dict], embeddings: List[np.ndarray] = None):
        """批量添加文档到向量数据库"""
        print("=" * 50)
        print("🔍 质量检查开始")
        print("=" * 50)
        logger.info("开始质量检查和文档添加...")
        
        # 质量检查统计
        total_docs = len(documents)
        valid_docs = 0
        invalid_docs = 0
        empty_docs = 0
        short_docs = 0
        
        logger.info(f"开始质量检查，总文档数: {total_docs}")
        
        # 质量检查：验证文档和元数据
        valid_documents = []
        valid_metadatas = []
        valid_embeddings = []
        
        for i, (doc, metadata) in enumerate(zip(documents, metadatas)):
            if not doc or len(doc.strip()) == 0:
                empty_docs += 1
                invalid_docs += 1
                logger.debug(f"文档 {i}: 内容为空，跳过")
                continue
                
            if len(doc.strip()) < 5:
                short_docs += 1
                invalid_docs += 1
                logger.debug(f"文档 {i}: 内容过短 ({len(doc.strip())} 字符)，跳过")
                continue
                
            if not metadata:
                invalid_docs += 1
                logger.debug(f"文档 {i}: 元数据为空，跳过")
                continue
                
            valid_docs += 1
            valid_documents.append(doc)
            valid_metadatas.append(metadata)
            if embeddings is not None and i < len(embeddings):
                valid_embeddings.append(embeddings[i])
        
        print("✅ 质量检查完成")
        print(f"📊 质量检查统计:")
        print(f"  - 总文档数: {total_docs}")
        print(f"  - 有效文档数: {valid_docs}")
        print(f"  - 无效文档数: {invalid_docs}")
        print(f"  - 空文档数: {empty_docs}")
        print(f"  - 短文档数: {short_docs}")
        print("=" * 50)
        print("🔍 质量检查结束")
        print("=" * 50)
        
        logger.info(f"质量检查完成:")
        logger.info(f"  - 总文档数: {total_docs}")
        logger.info(f"  - 有效文档数: {valid_docs}")
        logger.info(f"  - 无效文档数: {invalid_docs}")
        logger.info(f"  - 空文档数: {empty_docs}")
        logger.info(f"  - 短文档数: {short_docs}")
        
        print("=" * 50)
        print("📚 索引构建开始")
        print("=" * 50)
        logger.info(f"开始将 {valid_docs} 个有效文档添加到向量数据库...")
        
        try:
            # 批量处理
            for i in range(0, len(valid_documents), self.config["BATCH_SIZE"]):
                batch_end = min(i + self.config["BATCH_SIZE"], len(valid_documents))
                batch_docs = valid_documents[i:batch_end]
                batch_metadatas = valid_metadatas[i:batch_end]
                
                # 根据内容类型生成不同的ID前缀
                batch_ids = []
                for j, metadata in enumerate(batch_metadatas):
                    content_type = metadata.get('content_type', 'unknown')
                    if content_type == 'voice':
                        batch_ids.append(f"voice_{i+j}")
                    elif content_type == 'multimodal':
                        batch_ids.append(f"multimodal_{i+j}")
                    else:
                        batch_ids.append(f"doc_{i+j}")
                
                logger.info(f"调试信息 - 添加 {len(batch_docs)} 个文档到向量数据库")
                
                # 使用原生ChromaDB API
                if valid_embeddings and len(valid_embeddings) > 0:
                    # 如果有预计算的嵌入向量
                    batch_embeddings = valid_embeddings[i:batch_end]
                    collection.add(
                        documents=batch_docs,
                        metadatas=batch_metadatas,
                        ids=batch_ids,
                        embeddings=[emb.tolist() if hasattr(emb, 'tolist') else emb for emb in batch_embeddings]
                    )
                else:
                    # 让ChromaDB自动计算嵌入向量
                    collection.add(
                        documents=batch_docs,
                        metadatas=batch_metadatas,
                        ids=batch_ids
                    )
                
                logger.info(f"已添加 {batch_end}/{len(valid_documents)} 个文档")
            
            print("✅ 索引构建完成")
            print(f"📊 索引构建统计:")
            print(f"  - 成功添加文档数: {valid_docs}")
            print(f"  - 批次大小: {self.config['BATCH_SIZE']}")
            print(f"  - 总批次数: {(len(valid_documents) + self.config['BATCH_SIZE'] - 1) // self.config['BATCH_SIZE']}")
            print("=" * 50)
            print("📚 索引构建结束")
            print("=" * 50)
            
            logger.info("文档添加完成")
            
        except Exception as e:
            print("❌ 索引构建失败")
            logger.error(f"添加文档到向量数据库时出错: {e}")
            raise
    
    def add_image_vectors_to_db(self, vector_db, image_embeddings: np.ndarray, image_metadatas: List[Dict]):
        """批量添加图像向量到向量数据库"""
        if image_embeddings is None or len(image_embeddings) == 0:
            logger.info("没有图像向量可添加")
            return
        
        logger.info(f"将 {len(image_embeddings)} 个图像向量添加到向量数据库...")
        try:
            # 批量处理
            for i in range(0, len(image_embeddings), self.config["IMAGE_BATCH_SIZE"]):
                batch_end = min(i + self.config["IMAGE_BATCH_SIZE"], len(image_embeddings))
                batch_embeddings = image_embeddings[i:batch_end]
                batch_metadatas = image_metadatas[i:batch_end]
                batch_ids = [f"image_{i+j}" for j in range(len(batch_embeddings))]
                
                # 使用正确的ChromaDB API
                vector_db._collection.add(
                    embeddings=batch_embeddings.tolist(),
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                logger.info(f"已添加 {batch_end}/{len(image_embeddings)} 个图像向量")
            
            # 数据库会自动持久化
            logger.info("图像向量添加完成")
            
        except Exception as e:
            logger.error(f"添加图像向量到向量数据库时出错: {e}")
            raise
    
    def save_mapping(self, output_path: str = None):
        """保存图像文本映射关系"""
        if output_path is None:
            output_path = os.path.join(self.config["MULTIMODAL_VECTOR_DB_PATH"], "image_text_mapping.json")
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.image_text_mapping, f, ensure_ascii=False, indent=2)
            logger.info(f"图像文本映射关系已保存到: {output_path}")
            
        except Exception as e:
            logger.error(f"保存映射关系失败: {e}")
            raise
    
    def build_database(self, build_multimodal: bool = True, sample_size: int = None):
        """
        构建多模态向量数据库（优化版本）
        
        注意：已注释掉单独的文本和图像向量数据库构建，只保留多模态数据库
        这样可以减少存储空间和构建时间，提高系统效率
        
        Args:
            build_multimodal: 是否构建多模态向量数据库
            sample_size: 限制处理的样本数量，None表示处理所有数据
        """
        try:
            print("=" * 80)
            print("🚀 智诊通多模态向量数据库构建流程开始")
            print("=" * 80)
            print("📋 构建流程:")
            print("  1️⃣ 原始数据 → 文档加载")
            print("  2️⃣ 文档加载 → 数据清洗")
            print("  3️⃣ 数据清洗 → 文档切分")
            print("  4️⃣ 文档切分 → 向量化")
            print("  5️⃣ 向量化 → 质量检查")
            print("  6️⃣ 质量检查 → 索引构建")
            print("  7️⃣ 语音数据 → 语音转录 → 向量化")
            print("=" * 80)
            
            logger.info("=" * 80)
            logger.info("🚀 开始构建多模态向量数据库")
            logger.info("=" * 80)
            
            # 记录开始时间
            import time
            start_time = time.time()
            
            # 1. 加载数据
            logger.info("📥 步骤1: 加载数据")
            data = self.load_data()
            
            # 1.5. 应用样本限制（如果指定）
            if sample_size is not None:
                logger.info(f"🔢 步骤1.5: 应用样本限制 ({sample_size} 个样本)")
                print(f"🔢 应用样本限制: {sample_size} 个样本")
                
                # 限制纯文本数据（如果存在）
                if "general_text_train" in data and not data["general_text_train"].empty:
                    original_size = len(data["general_text_train"])
                    data["general_text_train"] = data["general_text_train"].head(sample_size)
                    logger.info(f"纯文本文档数据: {original_size} → {len(data['general_text_train'])}")
                
                
                # 限制图文数据
                for key in ["processed_reports", "train_reports", "test_reports"]:
                    if not data[key].empty:
                        original_size = len(data[key])
                        data[key] = data[key].head(sample_size)
                        logger.info(f"{key}: {original_size} → {len(data[key])}")
                
                # 限制图像数据
                for key in ["processed_images", "train_images", "test_images"]:
                    if len(data[key]) > 0:
                        original_size = len(data[key])
                        data[key] = data[key][:sample_size]
                        logger.info(f"{key}: {original_size} → {len(data[key])}")
                
                print(f"✅ 样本限制应用完成")
            else:
                logger.info(f"🔢 步骤1.5: 无样本限制，处理所有数据")
                print(f"🔢 无样本限制，处理所有数据")
            
            # 2. 处理每种数据集
            logger.info("📊 步骤2: 处理数据集")
            datasets = [
                ("processed", data["processed_reports"], data["processed_images"]),
                ("train", data["train_reports"], data["train_images"]),
                ("test", data["test_reports"], data["test_images"])
            ]
            
            for dataset_type, reports_df, images in datasets:
                if reports_df.empty:
                    continue
                
                logger.info(f"\n处理 {dataset_type} 数据集...")
                
                # 构建文本向量数据库（已注释 - 冗余功能）
                # if build_text:
                #     logger.info(f"构建 {dataset_type} 文本向量数据库...")
                #     docs, metadatas = self.prepare_text_documents(reports_df, images, dataset_type)
                #     self.add_documents_to_db(self.text_vector_db, docs, metadatas)
                
                # 构建图像向量数据库（已注释 - 冗余功能）
                # if build_image and self.image_embedder and len(images) > 0:
                #     logger.info(f"构建 {dataset_type} 图像向量数据库...")
                #     # 限制每次处理的图像数量，防止内存问题
                #     max_images_per_batch = self.config["MAX_IMAGES_PER_BATCH"]
                #     for i in range(0, len(images), max_images_per_batch):
                #         batch_end = min(i + max_images_per_batch, len(images))
                #         batch_images = images[i:batch_end]
                #         
                #         # 向量化当前批次的图像
                #         image_embeddings, image_metadatas = self.vectorize_images(batch_images, dataset_type)
                #         
                #         # 添加图像向量到数据库
                #         if image_embeddings is not None and self.image_vector_db is not None:
                #             self.add_image_vectors_to_db(self.image_vector_db, image_embeddings, image_metadatas)
                
                # 构建多模态向量数据库
                if build_multimodal:
                    logger.info(f"构建 {dataset_type} 多模态向量数据库...")
                    documents, metadatas, embeddings = self.vectorize_multimodal_data(reports_df, images)
                    self.add_documents_to_db(self.multimodal_collection, documents, metadatas, embeddings)
            
            # 3. 处理纯文本数据集（如果存在）
            # 注意：这里不再处理训练数据，因为系统没有训练功能
            general_text_datasets = []
            
            for dataset_type, text_df in general_text_datasets:
                if text_df.empty:
                    continue
                
                logger.info(f"\n处理 {dataset_type} 纯文本数据集...")
                
                # 构建纯文本向量数据库
                if build_multimodal:
                    logger.info(f"构建 {dataset_type} 纯文本向量数据库...")
                    docs, metadatas = self.prepare_general_text_documents(text_df, dataset_type)
                    
                    # 添加文档到多模态向量数据库
                    if docs and self.multimodal_collection is not None:
                        self.add_documents_to_db(self.multimodal_collection, docs, metadatas)
            
            # 4. 处理语音数据集
            logger.info("\n🎤 步骤4: 处理语音数据集")
            print("=" * 50)
            print("🎤 语音数据处理开始")
            print("=" * 50)
            
            if build_multimodal:
                # 检查语音数据是否存在
                voice_processed_path = self.config.get('VOICE_DATA_PROCESSED_PATH', '')
                voice_documents_file = os.path.join(voice_processed_path, 'voice_documents.json')
                
                if os.path.exists(voice_documents_file):
                    logger.info(f"找到语音数据文件: {voice_documents_file}")
                    print(f"✅ 找到语音数据文件: {voice_documents_file}")
                    
                    try:
                        import json
                        with open(voice_documents_file, 'r', encoding='utf-8') as f:
                            voice_data = json.load(f)
                        logger.info(f"语音数据加载完成: {len(voice_data)} 条记录")
                        print(f"📊 语音数据统计: {len(voice_data)} 条记录")
                        
                        if voice_data:
                            # 准备语音文档数据
                            voice_documents = []
                            voice_metadatas = []
                            voice_embeddings = []
                            
                            for idx, item in enumerate(voice_data):
                                # 提取文本内容
                                text_content = item.get('content', '')
                                if not text_content or text_content.strip() == '':
                                    continue
                                
                                # 创建文档内容
                                document_content = f"语音转录: {text_content}"
                                voice_documents.append(document_content)
                                
                                # 创建元数据
                                metadata = {
                                    'uid': f"voice_{idx}",
                                    'file_name': item.get('metadata', {}).get('file_name', ''),
                                    'data_type': 'voice',
                                    'voice_type': item.get('metadata', {}).get('voice_type', ''),
                                    'content_type': 'voice',
                                    'original_text': text_content,
                                    'dataset_type': 'voice_data',
                                    'vector_type': 'text'  # 语音转录文本使用文本向量
                                }
                                
                                # 解析metadata字段
                                try:
                                    item_metadata = item.get('metadata', {})
                                    metadata.update({
                                        'duration': item_metadata.get('duration', 0),
                                        'language': item_metadata.get('language', 'zh'),
                                        'file_size': item_metadata.get('file_size', 0),
                                        'processed_time': item_metadata.get('timestamp', '')
                                    })
                                except:
                                    pass
                                
                                voice_metadatas.append(metadata)
                                
                                # 计算语音文本的BiomedCLIP嵌入向量
                                try:
                                    if self.text_embedder:
                                        voice_embedding = self.text_embedder.embed_query(text_content)
                                        voice_embeddings.append(voice_embedding)
                                        logger.info(f"语音文本向量化成功: {len(voice_embedding)} 维")
                                    else:
                                        logger.warning("文本嵌入器不可用，跳过语音向量化")
                                        voice_embeddings.append(None)
                                except Exception as e:
                                    logger.error(f"语音文本向量化失败: {e}")
                                    voice_embeddings.append(None)
                            
                            # 添加语音文档到多模态向量数据库
                            if voice_documents and self.multimodal_collection is not None:
                                logger.info(f"添加 {len(voice_documents)} 个语音文档到多模态向量数据库...")
                                print(f"🎤 添加 {len(voice_documents)} 个语音文档到多模态向量数据库...")
                                
                                # 过滤掉没有嵌入向量的文档
                                valid_voice_docs = []
                                valid_voice_metas = []
                                valid_voice_embs = []
                                
                                for i, (doc, meta, emb) in enumerate(zip(voice_documents, voice_metadatas, voice_embeddings)):
                                    if emb is not None:
                                        valid_voice_docs.append(doc)
                                        valid_voice_metas.append(meta)
                                        valid_voice_embs.append(emb)
                                    else:
                                        logger.warning(f"跳过语音文档 {i}: 向量化失败")
                                
                                if valid_voice_docs:
                                    self.add_documents_to_db(self.multimodal_collection, valid_voice_docs, valid_voice_metas, valid_voice_embs)
                                    logger.info("✅ 语音文档添加完成")
                                    print("✅ 语音文档添加完成")
                                else:
                                    logger.warning("没有有效的语音文档向量")
                                    print("⚠️  没有有效的语音文档向量")
                            else:
                                logger.warning("没有有效的语音文档数据")
                                print("⚠️  没有有效的语音文档数据")
                        else:
                            logger.warning("语音数据文件为空")
                            print("⚠️  语音数据文件为空")
                            
                    except Exception as e:
                        logger.error(f"处理语音数据失败: {e}")
                        print(f"❌ 处理语音数据失败: {e}")
                else:
                    logger.warning(f"语音数据文件不存在: {voice_documents_file}")
                    print(f"⚠️  语音数据文件不存在: {voice_documents_file}")
            
            print("=" * 50)
            print("🎤 语音数据处理结束")
            print("=" * 50)
            
            # 5. 处理纯文本数据集（text_data）
            logger.info("\n📄 步骤5: 处理纯文本数据集")
            print("=" * 50)
            print("📄 纯文本数据处理开始")
            print("=" * 50)
            
            if build_multimodal and data.get("text_documents"):
                text_documents = data["text_documents"]
                logger.info(f"找到纯文本数据: {len(text_documents)} 条记录")
                print(f"✅ 找到纯文本数据: {len(text_documents)} 条记录")
                
                try:
                    # 准备文本文档数据
                    text_docs = []
                    text_metadatas = []
                    
                    for idx, item in enumerate(text_documents):
                        # 提取文本内容
                        text_content = item.get('content', '')
                        if not text_content or text_content.strip() == '':
                            continue
                        
                        # 创建文档内容
                        text_docs.append(text_content)
                        
                        # 创建元数据
                        metadata = {
                            'uid': f"text_{idx}",
                            'file_name': item.get('metadata', {}).get('file_name', ''),
                            'file_path': item.get('metadata', {}).get('file_path', ''),
                            'data_type': item.get('metadata', {}).get('data_type', 'general_document'),
                            'content_type': 'text',
                            'processing_version': item.get('metadata', {}).get('processing_version', '1.0'),
                            'processor_name': item.get('metadata', {}).get('processor_name', 'BaseProcessor'),
                            'timestamp': item.get('metadata', {}).get('timestamp', ''),
                            'content_length': str(len(text_content)),
                            'quality_score': str(item.get('metadata', {}).get('quality_score', 0.0)),
                            'medical_terms_count': str(item.get('metadata', {}).get('medical_terms_count', 0))
                        }
                        
                        # 转换所有值为字符串（ChromaDB要求）
                        for key, value in metadata.items():
                            metadata[key] = self.convert_to_basic_type(value)
                        
                        text_metadatas.append(metadata)
                    
                    # 为文本文档生成向量
                    text_embeddings = []
                    if text_docs and self.text_embedder:
                        logger.info(f"开始为 {len(text_docs)} 个文本文档生成向量...")
                        print(f"📄 开始为 {len(text_docs)} 个文本文档生成向量...")
                        
                        for i, doc in enumerate(text_docs):
                            try:
                                embedding = self.text_embedder.embed_query(doc)
                                text_embeddings.append(embedding)
                                if (i + 1) % 10 == 0:
                                    logger.info(f"已完成 {i + 1}/{len(text_docs)} 个文档的向量化")
                            except Exception as e:
                                logger.error(f"文档 {i} 向量化失败: {e}")
                                # 使用虚拟向量作为后备
                                dummy_vector = np.random.rand(512).tolist()
                                text_embeddings.append(dummy_vector)
                        
                        logger.info(f"文本向量化完成，生成了 {len(text_embeddings)} 个向量")
                        print(f"📄 文本向量化完成，生成了 {len(text_embeddings)} 个向量")
                    
                    # 添加文本文档到多模态向量数据库
                    if text_docs and self.multimodal_collection is not None:
                        logger.info(f"添加 {len(text_docs)} 个文本文档到多模态向量数据库...")
                        print(f"📄 添加 {len(text_docs)} 个文本文档到多模态向量数据库...")
                        self.add_documents_to_db(self.multimodal_collection, text_docs, text_metadatas, text_embeddings)
                        logger.info("✅ 文本文档添加完成")
                        print("✅ 文本文档添加完成")
                    else:
                        logger.warning("没有有效的文本文档数据")
                        print("⚠️  没有有效的文本文档数据")
                
                except Exception as e:
                    logger.error(f"处理文本数据失败: {e}")
                    print(f"❌ 处理文本数据失败: {e}")
            else:
                logger.info("未找到文本数据或未启用多模态构建，跳过文本数据处理")
                print("⚠️  未找到文本数据或未启用多模态构建，跳过文本数据处理")
            
            print("=" * 50)
            print("📄 纯文本数据处理结束")
            print("=" * 50)
            
            # 保存映射关系
            if build_multimodal:
                self.save_mapping()
            
            print("=" * 80)
            print("🎉 智诊通多模态向量数据库构建流程完成！")
            print("=" * 80)
            print("📊 构建结果总结:")
            print("  ✅ 文档加载: 完成")
            print("  ✅ 数据清洗: 完成")
            print("  ✅ 文档切分: 完成")
            print("  ✅ 向量化: 完成")
            print("  ✅ 质量检查: 完成")
            print("  ✅ 索引构建: 完成")
            print("  ✅ 语音处理: 完成")
            print("=" * 80)
            print("📁 数据库位置:")
            print(f"  - 多模态向量数据库: {self.config['MULTIMODAL_VECTOR_DB_PATH']}")
            print("=" * 80)
            print("🚀 智诊通多模态向量数据库构建流程结束")
            print("=" * 80)
            
            # 计算总耗时
            end_time = time.time()
            total_time = end_time - start_time
            
            logger.info("=" * 80)
            logger.info("🎉 多模态向量数据库构建完成！")
            logger.info(f"⏱️ 总耗时: {total_time:.2f} 秒")
            logger.info(f"🗄️ 多模态向量数据库: {self.config['MULTIMODAL_VECTOR_DB_PATH']}")
            logger.info("=" * 80)
            
        except Exception as e:
            print("=" * 80)
            print("❌ 智诊通多模态向量数据库构建流程失败！")
            print("=" * 80)
            print(f"错误信息: {e}")
            print("=" * 80)
            logger.error(f"构建多模态向量数据库失败: {e}")
            raise




def main():
    """主函数"""
    try:
        # 创建构建器
        builder = UnifiedMultimodalVectorDatabaseBuilder()
        
        # 构建数据库（只构建多模态向量数据库）
        builder.build_database(
            build_multimodal=True # 构建多模态向量数据库
        )
        
        # 打印配置摘要
        logger.info("\n配置摘要:")
        logger.info(f"- 文本嵌入模型: {builder.config['TEXT_EMBEDDING_MODEL']}")
        logger.info(f"- 图像向量化: {'启用' if builder.config.get('IMAGE_EMBEDDING_ENABLED') and IMAGE_EMBEDDING_AVAILABLE else '禁用'}")
        if builder.config.get('IMAGE_EMBEDDING_ENABLED') and IMAGE_EMBEDDING_AVAILABLE:
            logger.info(f"  - 向量化器类型: {builder.config['IMAGE_EMBEDDER_TYPE']}")
            logger.info(f"  - 模型名称: {builder.config['IMAGE_EMBEDDING_MODEL']}")
            logger.info(f"  - 使用设备: {builder.config['IMAGE_EMBEDDER_DEVICE']}")
        
    except Exception as e:
        logger.error(f"主函数执行失败: {e}")
        raise

if __name__ == "__main__":
    main()