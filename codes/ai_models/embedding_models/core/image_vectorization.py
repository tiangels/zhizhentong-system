"""
图像向量化脚本
将医疗图像转换为向量并存储到chroma_db中
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from tqdm import tqdm
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入医疗知识管理器
try:
    from .medical_knowledge_manager import MedicalKnowledgeManager
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.medical_knowledge_manager import MedicalKnowledgeManager

# 导入图像向量化模块
try:
    from models.image_embedder import ImageEmbedderFactory, batch_embed_images
    IMAGE_EMBEDDING_AVAILABLE = True
except ImportError:
    print("警告: 图像向量化模块未找到，请确保已安装相关依赖")
    IMAGE_EMBEDDING_AVAILABLE = False

# 配置类
class Config:
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_FILE_PATH = os.path.join(CURRENT_DIR, "config.json")
    
    @classmethod
    def load_config(cls):
        """加载配置文件"""
        try:
            with open(cls.CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"配置文件未找到: {cls.CONFIG_FILE_PATH}")
            return {}
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}

# 图像向量化器类
class ImageVectorizer:
    """图像向量化器"""
    
    def __init__(self, config_path: str = None):
        """初始化图像向量化器"""
        self.config = Config()
        if config_path:
            self.config.CONFIG_FILE_PATH = config_path
        
        # 加载配置
        self.config_data = Config.load_config()
        
        # 初始化组件
        self.image_embedder = None
        self.vector_store = None
        
        self._initialize_components()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            with open(self.config.CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"配置文件未找到: {self.config.CONFIG_FILE_PATH}")
            return {}
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}
    
    def _initialize_components(self):
        """初始化组件"""
        try:
            if IMAGE_EMBEDDING_AVAILABLE:
                # 初始化图像嵌入器
                model_config = self.config_data.get('models', {}).get('image', {})
                self.image_embedder = ImageEmbedderFactory.create_embedder(
                    embedder_type=model_config.get('embedder_type', 'clip'),
                    model_name=model_config.get('model_name', 'openai/clip-vit-base-patch32'),
                    device=model_config.get('device', 'cpu')
                )
                print("✓ 图像嵌入器初始化成功")
            else:
                print("! 图像嵌入器不可用")
        except Exception as e:
            print(f"! 图像嵌入器初始化失败: {e}")
    
    def vectorize_images(self, image_paths: list) -> np.ndarray:
        """向量化图像"""
        if not self.image_embedder:
            raise RuntimeError("图像嵌入器未初始化")
        
        try:
            vectors = batch_embed_images(image_paths, self.image_embedder)
            return vectors
        except Exception as e:
            print(f"图像向量化失败: {e}")
            raise
    
    def get_status(self) -> dict:
        """获取状态信息"""
        return {
            'image_embedder_available': self.image_embedder is not None,
            'config_loaded': bool(self.config_data),
            'image_embedding_module_available': IMAGE_EMBEDDING_AVAILABLE
        }

    # 初始化医疗知识管理器
    _knowledge_manager = MedicalKnowledgeManager()
    
    # 数据文件路径 - 使用医疗知识管理器
    @classmethod
    def get_image_path(cls, subdir: str, filename: str) -> str:
        """获取图像数据路径"""
        return cls._knowledge_manager.get_path("image_text", subdir, filename)
    
    @classmethod
    def get_text_path(cls, subdir: str, filename: str) -> str:
        """获取文本数据路径"""
        return cls._knowledge_manager.get_path("text", subdir, filename)
    
    # 图像数据路径 - 使用静态方法调用
    @classmethod
    def get_processed_images_path(cls):
        return cls.get_image_path("processed", "processed_images.npy")
    
    @classmethod
    def get_train_images_path(cls):
        return cls.get_image_path("processed", "train_images.npy")
    
    @classmethod
    def get_test_images_path(cls):
        return cls.get_image_path("processed", "test_images.npy")
    
    @classmethod
    def get_processed_reports_path(cls):
        return cls.get_image_path("processed", "processed_reports.csv")
    
    @classmethod
    def get_train_reports_path(cls):
        return cls.get_image_path("processed", "train_reports.csv")
    
    @classmethod
    def get_test_reports_path(cls):
        return cls.get_image_path("processed", "test_reports.csv")

    # 默认配置
    DEFAULT_CONFIG = {
        "VECTOR_DB_PATH": _knowledge_manager.get_vector_db_path("image"),
        "EMBEDDING_MODEL": "shibing624/text2vec-base-chinese",
        "LOCAL_MODEL_PATH": os.path.join(Config.CURRENT_DIR, "models", "text2vec-base-chinese"),
        "PROXY": None,
        "BATCH_SIZE": 100,
        "DOWNLOAD_TIMEOUT": 30,
        "MAX_RETRIES": 3,
        "COLLECTION_NAME": "medical_knowledge",
        "IMAGE_EMBEDDING": {
            "ENABLED": True,
            "EMBEDDER_TYPE": "resnet",
            "MODEL_NAME": "resnet50",
            "DEVICE": "cpu",
            "BATCH_SIZE": 32,
            "OUTPUT_PATH": _knowledge_manager.get_path("image_text", "embeddings", "image_embeddings.npy")
        },
        "MULTIMODAL_OPTIONS": {
            "FUSE_TEXT_IMAGE": False,
            "FUSION_METHOD": "concat",
            "NORMALIZE_EMBEDDINGS": True,
            "SAVE_SEPARATE_EMBEDDINGS": True
        }
    }

    # 加载配置
    @classmethod
    def load_config(cls):
        config = cls.DEFAULT_CONFIG.copy()
        if os.path.exists(cls.CONFIG_FILE_PATH):
            try:
                with open(cls.CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    config.update(user_config)
                    
                    # 确保IMAGE_EMBEDDING配置存在
                    if "IMAGE_EMBEDDING" not in config:
                        config["IMAGE_EMBEDDING"] = cls.DEFAULT_CONFIG["IMAGE_EMBEDDING"]
                    else:
                        # 合并默认配置
                        for key, value in cls.DEFAULT_CONFIG["IMAGE_EMBEDDING"].items():
                            if key not in config["IMAGE_EMBEDDING"]:
                                config["IMAGE_EMBEDDING"][key] = value
                    
                    # 确保MULTIMODAL_OPTIONS配置存在
                    if "MULTIMODAL_OPTIONS" not in config:
                        config["MULTIMODAL_OPTIONS"] = cls.DEFAULT_CONFIG["MULTIMODAL_OPTIONS"]
                    else:
                        # 合并默认配置
                        for key, value in cls.DEFAULT_CONFIG["MULTIMODAL_OPTIONS"].items():
                            if key not in config["MULTIMODAL_OPTIONS"]:
                                config["MULTIMODAL_OPTIONS"][key] = value
                                
                print(f"已加载配置文件: {cls.CONFIG_FILE_PATH}")
            except Exception as e:
                print(f"加载配置文件出错: {e}，使用默认配置")
        else:
            print(f"配置文件不存在: {cls.CONFIG_FILE_PATH}，使用默认配置")
            # 创建示例配置文件
            try:
                with open(cls.CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
                    json.dump(cls.DEFAULT_CONFIG, f, ensure_ascii=False, indent=4)
                print(f"已创建示例配置文件: {cls.CONFIG_FILE_PATH}")
            except Exception as e:
                print(f"创建示例配置文件失败: {e}")
        return config

# 初始化配置
config = Config.load_config()
VECTOR_DB_PATH = config.get("TEXT_VECTOR_DB_PATH", config.get("VECTOR_DB_PATH", ""))
EMBEDDING_MODEL = config.get("TEXT_EMBEDDING_MODEL", config.get("EMBEDDING_MODEL", ""))
LOCAL_MODEL_PATH = config.get("LOCAL_MODEL_PATH", "")
PROXY = config.get("PROXY", "")
BATCH_SIZE = config.get("BATCH_SIZE", 100)
DOWNLOAD_TIMEOUT = config.get("DOWNLOAD_TIMEOUT", 30)
MAX_RETRIES = config.get("MAX_RETRIES", 3)
COLLECTION_NAME = config.get("TEXT_COLLECTION_NAME", config.get("COLLECTION_NAME", ""))

# 图像向量化配置
IMAGE_EMBEDDING_CONFIG = config.get("IMAGE_EMBEDDING", {})
IMAGE_EMBEDDING_ENABLED = IMAGE_EMBEDDING_CONFIG.get("ENABLED", False) and IMAGE_EMBEDDING_AVAILABLE
IMAGE_EMBEDDER_TYPE = IMAGE_EMBEDDING_CONFIG.get("EMBEDDER_TYPE", "resnet")
IMAGE_EMBEDDER_MODEL = IMAGE_EMBEDDING_CONFIG.get("MODEL_NAME", "resnet50")
IMAGE_EMBEDDER_DEVICE = IMAGE_EMBEDDING_CONFIG.get("DEVICE", "cpu")
IMAGE_BATCH_SIZE = IMAGE_EMBEDDING_CONFIG.get("BATCH_SIZE", 32)
# 延迟初始化输出路径
def get_image_output_path():
    return IMAGE_EMBEDDING_CONFIG.get("OUTPUT_PATH", ImageVectorizer.get_image_path("embeddings", "image_embeddings.npy"))

IMAGE_OUTPUT_PATH = get_image_output_path()

# 多模态选项
MULTIMODAL_OPTIONS = config.get("MULTIMODAL_OPTIONS", {})
FUSE_TEXT_IMAGE = MULTIMODAL_OPTIONS.get("FUSE_TEXT_IMAGE", False)
FUSION_METHOD = MULTIMODAL_OPTIONS.get("FUSION_METHOD", "concat")
NORMALIZE_EMBEDDINGS = MULTIMODAL_OPTIONS.get("NORMALIZE_EMBEDDINGS", True)
SAVE_SEPARATE_EMBEDDINGS = MULTIMODAL_OPTIONS.get("SAVE_SEPARATE_EMBEDDINGS", True)

def load_data():
    """加载处理后的图像数据"""
    print("加载处理后的图像数据...")
    try:
        # 加载图像数据
        processed_images_path = ImageVectorizer.get_processed_images_path()
        train_images_path = ImageVectorizer.get_train_images_path()
        test_images_path = ImageVectorizer.get_test_images_path()
        
        processed_images = np.load(processed_images_path, allow_pickle=True) if os.path.exists(processed_images_path) else np.array([])
        train_images = np.load(train_images_path, allow_pickle=True) if os.path.exists(train_images_path) else np.array([])
        test_images = np.load(test_images_path, allow_pickle=True) if os.path.exists(test_images_path) else np.array([])
        
        # 加载报告数据
        processed_reports_path = ImageVectorizer.get_processed_reports_path()
        train_reports_path = ImageVectorizer.get_train_reports_path()
        test_reports_path = ImageVectorizer.get_test_reports_path()
        
        processed_reports = pd.read_csv(processed_reports_path) if os.path.exists(processed_reports_path) else pd.DataFrame()
        train_reports = pd.read_csv(train_reports_path) if os.path.exists(train_reports_path) else pd.DataFrame()
        test_reports = pd.read_csv(test_reports_path) if os.path.exists(test_reports_path) else pd.DataFrame()

        print(f"""成功加载数据:
- 处理后的图像: {len(processed_images)} 张
- 训练集图像: {len(train_images)} 张
- 测试集图像: {len(test_images)} 张
- 处理后的报告: {len(processed_reports)} 条
- 训练集报告: {len(train_reports)} 条
- 测试集报告: {len(test_reports)} 条""")

        return {
            "processed_images": processed_images,
            "train_images": train_images,
            "test_images": test_images,
            "processed_reports": processed_reports,
            "train_reports": train_reports,
            "test_reports": test_reports
        }
    except Exception as e:
        print(f"加载数据时出错: {e}")
        raise

def set_environment_variables():
    """设置环境变量，包括代理"""
    if PROXY:
        os.environ["HTTP_PROXY"] = PROXY
        os.environ["HTTPS_PROXY"] = PROXY
        print(f"已设置代理: {PROXY}")
    else:
        # 清除可能存在的代理设置
        if "HTTP_PROXY" in os.environ:
            del os.environ["HTTP_PROXY"]
        if "HTTPS_PROXY" in os.environ:
            del os.environ["HTTPS_PROXY"]

def init_text_embeddings():
    """初始化文本嵌入模型"""
    print(f"初始化文本嵌入模型: {EMBEDDING_MODEL}")
    
    try:
        # 先设置环境变量（包括代理）
        set_environment_variables()
        
        # 然后设置下载超时环境变量
        if DOWNLOAD_TIMEOUT:
            os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = str(DOWNLOAD_TIMEOUT)
            print(f"已设置HF_HUB_DOWNLOAD_TIMEOUT: {DOWNLOAD_TIMEOUT}秒")
        
        # 加载嵌入模型的参数
        model_kwargs = {"device": "cpu"}

        # 检查是否使用本地模型
        if LOCAL_MODEL_PATH and os.path.exists(LOCAL_MODEL_PATH):
            print(f"使用本地模型: {LOCAL_MODEL_PATH}")
            embeddings = HuggingFaceEmbeddings(
                model_name=LOCAL_MODEL_PATH,
                model_kwargs=model_kwargs
            )
        else:
            # 在线下载模型，添加重试机制
            from tenacity import retry, stop_after_attempt, wait_exponential

            @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(multiplier=1, min=1, max=10))
            def load_embeddings_with_retry():
                return HuggingFaceEmbeddings(
                    model_name=EMBEDDING_MODEL,
                    model_kwargs=model_kwargs
                )

            print(f"尝试下载模型，最多重试 {MAX_RETRIES} 次...")
            embeddings = load_embeddings_with_retry()

        return embeddings
    except Exception as e:
        print(f"初始化文本嵌入模型时出错: {e}")
        print("提示: 您可以尝试以下解决方法:")
        print("1. 检查网络连接是否正常")
        print("2. 在Config类中设置正确的代理服务器")
        print("3. 提前下载模型并设置LOCAL_MODEL_PATH指向本地模型目录")
        raise

def init_image_embedder():
    """初始化图像向量化器"""
    if not IMAGE_EMBEDDING_ENABLED:
        print("图像向量化功能已禁用或模块不可用")
        return None
    
    try:
        print(f"初始化图像向量化器: {IMAGE_EMBEDDER_TYPE} ({IMAGE_EMBEDDER_MODEL})")
        print(f"使用设备: {IMAGE_EMBEDDER_DEVICE}")
        
        # 创建图像向量化器
        embedder = ImageEmbedderFactory.create_embedder(
            embedder_type=IMAGE_EMBEDDER_TYPE,
            model_name=IMAGE_EMBEDDER_MODEL,
            device=IMAGE_EMBEDDER_DEVICE
        )
        
        print(f"图像向量化器初始化成功，模型类型: {IMAGE_EMBEDDER_TYPE}")
        return embedder
    except Exception as e:
        print(f"初始化图像向量化器时出错: {e}")
        print("提示: 您可以尝试:")
        print("1. 检查PyTorch是否正确安装")
        print("2. 尝试使用不同的EMBEDDER_TYPE (resnet, clip, vit)")
        print("3. 在配置文件中设置IMAGE_EMBEDDING.ENABLED = false 以禁用图像向量化")
        return None

def init_vector_db(embeddings):
    """初始化向量数据库"""
    print(f"初始化向量数据库，存储路径: {VECTOR_DB_PATH}")
    
    try:
        # 确保向量数据库目录存在
        os.makedirs(VECTOR_DB_PATH, exist_ok=True)
        
        # 初始化向量数据库
        vector_db = Chroma(
            persist_directory=VECTOR_DB_PATH,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME
        )

        print(f"向量数据库初始化成功，存储路径: {VECTOR_DB_PATH}")
        return vector_db
    except Exception as e:
        print(f"初始化向量数据库时出错: {e}")
        raise

def vectorize_images(embedder, images, dataset_type="processed"):
    """将图像数据转换为向量"""
    if embedder is None or len(images) == 0:
        return None, None
    
    print(f"将 {len(images)} 张图像转换为向量...")
    
    try:
        # 使用batch_embed_images函数批量处理图像
        embeddings = batch_embed_images(embedder, images, batch_size=IMAGE_BATCH_SIZE)
        
        # 创建元数据
        metadatas = []
        for idx in range(len(embeddings)):
            metadata = {
                "document_id": f"{dataset_type}_image_{idx}",
                "dataset_type": dataset_type,
                "index": idx,
                "content_type": "image",
                "vector_dim": len(embeddings[idx])
            }
            metadatas.append(metadata)
        
        print(f"图像向量化完成，共生成 {len(embeddings)} 个图像向量")
        return embeddings, metadatas
    except Exception as e:
        print(f"图像向量化过程中出错: {e}")
        raise

def add_image_vectors_to_db(vector_db, image_embeddings, image_metadatas):
    """批量添加图像向量到向量数据库"""
    if image_embeddings is None or len(image_embeddings) == 0:
        print("没有图像向量可添加")
        return
    
    print(f"将 {len(image_embeddings)} 个图像向量添加到向量数据库...")
    try:
        # 批量处理
        for i in range(0, len(image_embeddings), IMAGE_BATCH_SIZE):
            batch_end = min(i + IMAGE_BATCH_SIZE, len(image_embeddings))
            batch_embeddings = image_embeddings[i:batch_end]
            batch_metadatas = image_metadatas[i:batch_end]
            batch_ids = [f"image_{i+j}" for j in range(len(batch_embeddings))]
            
            # 为每个向量创建一个占位符文本
            batch_texts = [f"图像向量 {i+j}" for j in range(len(batch_embeddings))]

            # 添加向量到数据库
            vector_db.add_texts(
                texts=batch_texts,
                metadatas=batch_metadatas,
                ids=batch_ids,
                embeddings=batch_embeddings
            )
            print(f"已添加 {batch_end}/{len(image_embeddings)} 个图像向量")

        # 持久化数据库
        vector_db.persist()
        print("图像向量添加完成并已持久化")
    except Exception as e:
        print(f"添加图像向量到向量数据库时出错: {e}")
        raise

def save_image_embeddings(embeddings, metadatas, output_path):
    """保存图像向量和元数据"""
    if embeddings is None or len(embeddings) == 0:
        print("没有图像向量可保存")
        return
    
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 保存向量
        np.save(output_path, embeddings)
        print(f"图像向量已保存到: {output_path}")
        
        # 保存元数据
        metadata_path = output_path.replace('.npy', '_metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadatas, f, ensure_ascii=False, indent=2)
        print(f"图像元数据已保存到: {metadata_path}")
    except Exception as e:
        print(f"保存图像向量时出错: {e}")
        raise

def main():
    """主函数"""
    try:
        print("=" * 50)
        print("图像向量化与存储程序")
        print("=" * 50)
        
        # 1. 加载数据
        data = load_data()
        
        # 2. 初始化文本嵌入模型
        text_embeddings = init_text_embeddings()
        
        # 3. 初始化向量数据库
        vector_db = init_vector_db(text_embeddings)
        
        # 4. 初始化图像向量化器
        image_embedder = init_image_embedder()
        
        if image_embedder is None:
            print("图像向量化器初始化失败，程序退出")
            return
        
        # 5. 处理和添加每种数据集
        datasets = [
            ("processed", data["processed_images"]),
            ("train", data["train_images"]),
            ("test", data["test_images"])
        ]
        
        for dataset_type, images in datasets:
            if len(images) > 0:
                print(f"\n处理 {dataset_type} 图像数据...")
                
                # 限制每次处理的图像数量，防止内存问题
                max_images_per_batch = 500  # 可根据系统内存调整
                for i in range(0, len(images), max_images_per_batch):
                    batch_end = min(i + max_images_per_batch, len(images))
                    batch_images = images[i:batch_end]
                    
                    # 向量化当前批次的图像
                    image_embeddings, image_metadatas = vectorize_images(image_embedder, batch_images, dataset_type)
                    
                    # 添加图像向量到数据库
                    if image_embeddings is not None:
                        add_image_vectors_to_db(vector_db, image_embeddings, image_metadatas)
                    
                    # 保存图像向量到文件
                    if SAVE_SEPARATE_EMBEDDINGS and image_embeddings is not None:
                        output_path = IMAGE_OUTPUT_PATH.replace('.npy', f'_{dataset_type}.npy')
                        save_image_embeddings(image_embeddings, image_metadatas, output_path)
        
        print("\n图像向量化与存储完成！")
        print(f"数据库存储位置: {VECTOR_DB_PATH}")
        print("你可以在后续的RAG应用中使用这个向量数据库进行检索。")
        
        # 打印配置摘要
        print("\n配置摘要:")
        print(f"- 文本嵌入模型: {EMBEDDING_MODEL}")
        print(f"- 图像向量化: {'启用' if IMAGE_EMBEDDING_ENABLED else '禁用'}")
        if IMAGE_EMBEDDING_ENABLED:
            print(f"  - 向量化器类型: {IMAGE_EMBEDDER_TYPE}")
            print(f"  - 模型名称: {IMAGE_EMBEDDER_MODEL}")
            print(f"  - 使用设备: {IMAGE_EMBEDDER_DEVICE}")
    except Exception as e:
        print(f"程序执行出错: {e}")
        raise

if __name__ == "__main__":
    main()