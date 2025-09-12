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

# 导入文档切分模块
from processors.document_chunker import DocumentChunker, ChunkConfig, ChunkStrategy, create_medical_chunker, create_general_chunker

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置文档切分器的日志级别为DEBUG，以便看到详细的切分过程
document_chunker_logger = logging.getLogger('processors.document_chunker')
document_chunker_logger.setLevel(logging.INFO)

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 尝试导入图像向量化模块
try:
    # 添加models目录到路径
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
    sys.path.append(models_dir)
    from image_embedder import ImageEmbedderFactory, batch_embed_images
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
        self.config = self._load_config(config_path)
        self.text_embedder = None
        self.image_embedder = None
        self.text_vector_db = None
        self.image_vector_db = None
        self.multimodal_vector_db = None
        self.image_text_mapping = {}
        self.document_chunker = None  # 文档切分器
        
        # 初始化组件
        self._init_components()
    
    def _load_config(self, config_path: str = None) -> Dict:
        """加载配置文件"""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.json")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"已加载配置文件: {config_path}")
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        base_data_dir = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge"
        
        return {
            # 数据路径
            "BASE_DATA_DIR": base_data_dir,
            "PROCESSED_REPORTS_PATH": os.path.join(base_data_dir, "image_text_data", "processed", "processed_reports.csv"),
            "TRAIN_REPORTS_PATH": os.path.join(base_data_dir, "training_data", "dialogue_train.csv"),
            "TEST_REPORTS_PATH": os.path.join(base_data_dir, "test_data", "dialogue_test.csv"),
            "PROCESSED_IMAGES_PATH": os.path.join(base_data_dir, "image_text_data", "processed", "processed_images.npy"),
            "TRAIN_IMAGES_PATH": os.path.join(base_data_dir, "image_text_data", "processed", "train_images.npy"),
            "TEST_IMAGES_PATH": os.path.join(base_data_dir, "image_text_data", "processed", "test_images.npy"),
            
            # 向量数据库路径
            "TEXT_VECTOR_DB_PATH": os.path.join(project_root, "datas", "vector_databases", "text"),
            "IMAGE_VECTOR_DB_PATH": os.path.join(project_root, "datas", "vector_databases", "image"),
            "MULTIMODAL_VECTOR_DB_PATH": os.path.join(project_root, "datas", "vector_databases", "multimodal"),
            
            # 模型配置
            "TEXT_EMBEDDING_MODEL": "shibing624/text2vec-base-chinese",
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
            "TEXT_COLLECTION_NAME": "medical_text_vectors",
            "IMAGE_COLLECTION_NAME": "medical_image_vectors",
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
    
    def _init_document_chunker(self):
        """初始化文档切分器"""
        try:
            # 创建通用文档切分器（更适合处理各种类型的文本）
            self.document_chunker = create_general_chunker()
            logger.info("文档切分器初始化成功")
        except Exception as e:
            logger.error(f"文档切分器初始化失败: {e}")
            # 使用默认切分器作为备用
            self.document_chunker = DocumentChunker()
            logger.warning("使用默认文档切分器")
    
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
            logger.info(f"已设置HF_HUB_DOWNLOAD_TIMEOUT: {self.config['DOWNLOAD_TIMEOUT']}秒")
    
    def _init_text_embedder(self):
        """初始化文本嵌入模型"""
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            
            # 加载嵌入模型的参数
            model_kwargs = {"device": "cpu"}
            
            # 检查是否使用本地模型
            if self.config.get("LOCAL_MODEL_PATH"):
                logger.info(f"使用本地模型: {self.config['LOCAL_MODEL_PATH']}")
                self.text_embedder = HuggingFaceEmbeddings(
                    model_name=self.config["LOCAL_MODEL_PATH"],
                    model_kwargs=model_kwargs
                )
            else:
                # 在线下载模型，添加重试机制
                from tenacity import retry, stop_after_attempt, wait_exponential
                
                @retry(stop=stop_after_attempt(self.config["MAX_RETRIES"]), 
                       wait=wait_exponential(multiplier=1, min=1, max=10))
                def load_embeddings_with_retry():
                    from langchain_huggingface import HuggingFaceEmbeddings
                    return HuggingFaceEmbeddings(
                        model_name=self.config["TEXT_EMBEDDING_MODEL"],
                        model_kwargs=model_kwargs
                    )
                
                logger.info(f"尝试下载模型，最多重试 {self.config['MAX_RETRIES']} 次...")
                self.text_embedder = load_embeddings_with_retry()
            
            logger.info(f"文本嵌入模型初始化成功: {self.config['TEXT_EMBEDDING_MODEL']}")
            
        except Exception as e:
            logger.error(f"文本嵌入模型初始化失败: {e}")
            raise
    
    def _init_image_embedder(self):
        """初始化图像嵌入模型"""
        if not self.config.get("IMAGE_EMBEDDING_ENABLED", False) or not IMAGE_EMBEDDING_AVAILABLE:
            logger.info("图像向量化功能已禁用或模块不可用")
            return
        
        try:
            logger.info(f"初始化图像向量化器: {self.config['IMAGE_EMBEDDER_TYPE']} ({self.config['IMAGE_EMBEDDING_MODEL']})")
            logger.info(f"使用设备: {self.config['IMAGE_EMBEDDER_DEVICE']}")
            
            # 创建图像向量化器
            self.image_embedder = ImageEmbedderFactory.create_embedder(
                embedder_type=self.config["IMAGE_EMBEDDER_TYPE"],
                model_name=self.config["IMAGE_EMBEDDING_MODEL"],
                device=self.config["IMAGE_EMBEDDER_DEVICE"]
            )
            
            logger.info(f"图像向量化器初始化成功，模型类型: {self.config['IMAGE_EMBEDDER_TYPE']}")
            
        except Exception as e:
            logger.error(f"图像向量化器初始化失败: {e}")
            self.image_embedder = None
    
    def _init_vector_databases(self):
        """初始化向量数据库"""
        try:
            from langchain_chroma import Chroma
            
            # 创建向量数据库目录
            os.makedirs(self.config["TEXT_VECTOR_DB_PATH"], exist_ok=True)
            os.makedirs(self.config["IMAGE_VECTOR_DB_PATH"], exist_ok=True)
            os.makedirs(self.config["MULTIMODAL_VECTOR_DB_PATH"], exist_ok=True)
            
            # 初始化文本向量数据库（已注释 - 冗余功能）
            # self.text_vector_db = Chroma(
            #     persist_directory=self.config["TEXT_VECTOR_DB_PATH"],
            #     embedding_function=self.text_embedder,
            #     collection_name=self.config["TEXT_COLLECTION_NAME"]
            # )
            
            # 初始化图像向量数据库（已注释 - 冗余功能）
            # if self.image_embedder:
            #     # 为图像向量创建一个简单的嵌入函数
            #     class DummyEmbedding:
            #         def embed_documents(self, texts):
            #             return [[0.0] * 2048] * len(texts)  # ResNet50输出2048维
            #         
            #         def embed_query(self, text):
            #             return [0.0] * 2048
            #     
            #     self.image_vector_db = Chroma(
            #         collection_name=self.config["IMAGE_COLLECTION_NAME"],
            #         embedding_function=DummyEmbedding(),
            #         persist_directory=self.config["IMAGE_VECTOR_DB_PATH"]
            #     )
            
            # 初始化多模态向量数据库
            self.multimodal_vector_db = Chroma(
                persist_directory=self.config["MULTIMODAL_VECTOR_DB_PATH"],
                embedding_function=self.text_embedder,
                collection_name=self.config["MULTIMODAL_COLLECTION_NAME"]
            )
            
            logger.info("向量数据库初始化成功")
            
        except Exception as e:
            logger.error(f"向量数据库初始化失败: {e}")
            raise
    
    def load_data(self) -> Dict[str, Any]:
        """加载数据"""
        try:
            print("=" * 50)
            print("📁 文档加载开始")
            print("=" * 50)
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
            logger.info("正在加载纯文本数据...")
            text_data_base = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/text_data/processed"
            general_text_train = pd.read_csv(f"{text_data_base}/training_data/general_text_train.csv") if os.path.exists(f"{text_data_base}/training_data/general_text_train.csv") else pd.DataFrame()
            general_text_test = pd.read_csv(f"{text_data_base}/test_data/general_text_test.csv") if os.path.exists(f"{text_data_base}/test_data/general_text_test.csv") else pd.DataFrame()
            
            logger.info(f"纯文本数据加载完成:")
            logger.info(f"  - 纯文本训练数据: {len(general_text_train)} 条")
            logger.info(f"  - 纯文本测试数据: {len(general_text_test)} 条")
            
            # 数据加载统计
            total_documents = len(processed_reports) + len(train_reports) + len(test_reports) + len(general_text_train) + len(general_text_test)
            total_images = len(processed_images) + len(train_images) + len(test_images)
            
            print("✅ 文档加载成功")
            print(f"📊 数据统计:")
            print(f"  - 总文档数: {total_documents} 条")
            print(f"  - 总图像数: {total_images} 张")
            print("=" * 50)
            print("📁 文档加载结束")
            print("=" * 50)
            
            logger.info(f"数据加载完成，总计: {total_documents} 个文档, {total_images} 张图像")
            
            return {
                "processed_reports": processed_reports,
                "train_reports": train_reports,
                "test_reports": test_reports,
                "processed_images": processed_images,
                "train_images": train_images,
                "test_images": test_images,
                "general_text_train": general_text_train,
                "general_text_test": general_text_test
            }
            
        except Exception as e:
            print("❌ 文档加载失败")
            logger.error(f"加载数据失败: {e}")
            raise
    
    def convert_to_basic_type(self, value):
        """将值转换为ChromaDB支持的基本类型"""
        if pd.isna(value):
            return None
        elif isinstance(value, (str, int, float, bool)):
            return value
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
        """准备纯文本文档数据用于向量存储（包含文档切分）"""
        documents = []
        metadatas = []
        
        print("=" * 50)
        print("🧹 数据清洗开始")
        print("=" * 50)
        logger.info(f"开始准备 {dataset_type} 数据集的纯文本文档...")
        
        # 数据清洗统计
        total_rows = len(text_df)
        valid_rows = 0
        invalid_rows = 0
        empty_content_rows = 0
        short_content_rows = 0
        
        logger.info(f"开始数据清洗，总行数: {total_rows}")
        
        for idx, row in tqdm(text_df.iterrows(), total=len(text_df)):
            # 获取文档内容
            content = row.get('content', '')
            
            # 数据清洗步骤
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
                
                print("=" * 50)
                print("✂️ 文档切分开始")
                print("=" * 50)
                logger.info(f"正在切分文档 {idx}: {content[:100]}...")
                
                # 切分文档
                chunks = self.document_chunker.chunk_document(content, base_metadata)
                
                print("✅ 文档切分完成")
                print(f"📊 切分统计:")
                print(f"  - 文档ID: {idx}")
                print(f"  - 原始长度: {len(content)} 字符")
                print(f"  - 切分片段数: {len(chunks)}")
                print("=" * 50)
                print("✂️ 文档切分结束")
                print("=" * 50)
                
                logger.info(f"文档 {idx} 切分为 {len(chunks)} 个片段")
                
                # 将切分后的文档添加到结果中
                for chunk in chunks:
                    documents.append(chunk['content'])
                    metadatas.append(chunk['metadata'])
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
        
        # 数据清洗结果统计
        print("✅ 数据清洗完成")
        print(f"📊 清洗统计:")
        print(f"  - 总行数: {total_rows}")
        print(f"  - 有效行数: {valid_rows}")
        print(f"  - 无效行数: {invalid_rows}")
        print(f"  - 空内容行数: {empty_content_rows}")
        print(f"  - 短内容行数: {short_content_rows}")
        print(f"  - 清洗后文档块数: {len(documents)}")
        print("=" * 50)
        print("🧹 数据清洗结束")
        print("=" * 50)
        
        logger.info(f"数据清洗完成:")
        logger.info(f"  - 总行数: {total_rows}")
        logger.info(f"  - 有效行数: {valid_rows}")
        logger.info(f"  - 无效行数: {invalid_rows}")
        logger.info(f"  - 空内容行数: {empty_content_rows}")
        logger.info(f"  - 短内容行数: {short_content_rows}")
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
        
        # 数据清洗统计
        total_rows = len(reports_df)
        valid_rows = 0
        invalid_rows = 0
        empty_content_rows = 0
        
        logger.info(f"开始数据清洗，总行数: {total_rows}")
        
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
                    base_metadata["has_image"] = True
                    base_metadata["image_shape"] = self.convert_to_basic_type(images[idx].shape)
                else:
                    base_metadata["has_image"] = False
                
                print("=" * 50)
                print("✂️ 文档切分开始")
                print("=" * 50)
                logger.info(f"正在切分文档 {idx}: {content[:100]}...")
                
                # 切分文档
                chunks = self.document_chunker.chunk_document(content, base_metadata)
                
                print("✅ 文档切分完成")
                print(f"📊 切分统计:")
                print(f"  - 文档ID: {idx}")
                print(f"  - 原始长度: {len(content)} 字符")
                print(f"  - 切分片段数: {len(chunks)}")
                print("=" * 50)
                print("✂️ 文档切分结束")
                print("=" * 50)
                
                logger.info(f"文档 {idx} 切分为 {len(chunks)} 个片段")
                
                # 将切分后的文档添加到结果中
                for chunk in chunks:
                    documents.append(chunk['content'])
                    metadatas.append(chunk['metadata'])
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
                    metadata["has_image"] = True
                    metadata["image_shape"] = self.convert_to_basic_type(images[idx].shape)
                else:
                    metadata["has_image"] = False
                
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
                    "index": idx,
                    "content_type": "image",
                    "vector_dim": len(embeddings[idx])
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
                    'index': idx,
                    'metadata': {
                        'uid': uid,
                        'MeSH': row.get('MeSH', ''),
                        'Problems': row.get('Problems', ''),
                        'image': row.get('image', ''),
                        'indication': row.get('indication', ''),
                        'comparison': row.get('comparison', ''),
                        'findings': row.get('findings', ''),
                        'impression': row.get('impression', ''),
                        'description': row.get('description', ''),
                        'diagnosis': row.get('diagnosis', ''),
                        'suggestions': row.get('suggestions', ''),
                        'dialogue_content': row.get('dialogue_content', '')
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
            idx = mapping_info['index']
            text_content = mapping_info['text']
            metadata = mapping_info['metadata'].copy()
            
            # 检查是否有对应的图像
            if idx < len(images):
                # 有图像的情况：使用图像向量
                image = images[idx]
                
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
                    image_vector = self.image_embedder.embed_image(image)
                    
                    # 使用图像向量作为嵌入
                    embeddings.append(image_vector)
                    image_vectors += 1
                    
                    # 更新元数据
                    metadata.update({
                        'content_type': 'multimodal',
                        'has_image': True,
                        'image_index': idx,
                        'vector_type': 'image'
                    })
                    
                except Exception as e:
                    logger.warning(f"图像向量化失败 (UID: {uid}): {e}")
                    # 回退到文本向量
                    text_vector = self.text_embedder.embed_query(text_content)
                    embeddings.append(text_vector)
                    text_vectors += 1
                    metadata.update({
                        'content_type': 'text',
                        'has_image': False,
                        'vector_type': 'text'
                    })
            else:
                # 没有图像的情况：使用文本向量
                text_vector = self.text_embedder.embed_query(text_content)
                embeddings.append(text_vector)
                text_vectors += 1
                metadata.update({
                    'content_type': 'text',
                    'has_image': False,
                    'vector_type': 'text'
                })
            
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
        print("=" * 50)
        print("🔢 向量化结束")
        print("=" * 50)
        
        logger.info(f"多模态数据向量化完成:")
        logger.info(f"  - 总图文对数: {total_pairs}")
        logger.info(f"  - 图像向量数: {image_vectors}")
        logger.info(f"  - 文本向量数: {text_vectors}")
        logger.info(f"  - 总文档数: {len(documents)}")
        return documents, metadatas, embeddings
    
    def add_documents_to_db(self, vector_db, documents: List[str], metadatas: List[Dict], embeddings: List[np.ndarray] = None):
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
            for i in range(0, len(documents), self.config["BATCH_SIZE"]):
                batch_end = min(i + self.config["BATCH_SIZE"], len(documents))
                batch_docs = documents[i:batch_end]
                batch_metadatas = metadatas[i:batch_end]
                batch_ids = [f"doc_{i+j}" for j in range(len(batch_docs))]
                
                # 如果提供了预计算的嵌入向量，则使用它们
                if embeddings is not None and i < len(embeddings):
                    batch_embeddings = embeddings[i:batch_end]
                    vector_db.add_texts(
                        texts=batch_docs,
                        metadatas=batch_metadatas,
                        ids=batch_ids,
                        embeddings=batch_embeddings
                    )
                else:
                    vector_db.add_texts(
                        texts=batch_docs,
                        metadatas=batch_metadatas,
                        ids=batch_ids
                    )
                logger.info(f"已添加 {batch_end}/{len(documents)} 个文档")
            
            # 数据库会自动持久化
            print("✅ 索引构建完成")
            print(f"📊 索引构建统计:")
            print(f"  - 成功添加文档数: {valid_docs}")
            print(f"  - 批次大小: {self.config['BATCH_SIZE']}")
            print(f"  - 总批次数: {(len(documents) + self.config['BATCH_SIZE'] - 1) // self.config['BATCH_SIZE']}")
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
    
    def build_database(self, build_multimodal: bool = True):
        """
        构建多模态向量数据库（优化版本）
        
        注意：已注释掉单独的文本和图像向量数据库构建，只保留多模态数据库
        这样可以减少存储空间和构建时间，提高系统效率
        
        Args:
            build_multimodal: 是否构建多模态向量数据库
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
            print("=" * 80)
            
            logger.info("开始构建多模态向量数据库...")
            
            # 1. 加载数据
            data = self.load_data()
            
            # 2. 处理每种数据集
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
                    self.add_documents_to_db(self.multimodal_vector_db, documents, metadatas, embeddings)
            
            # 3. 处理纯文本数据集
            general_text_datasets = [
                ("general_text_train", data["general_text_train"]),
                ("general_text_test", data["general_text_test"])
            ]
            
            for dataset_type, text_df in general_text_datasets:
                if text_df.empty:
                    continue
                
                logger.info(f"\n处理 {dataset_type} 纯文本数据集...")
                
                # 构建纯文本向量数据库
                if build_multimodal:
                    logger.info(f"构建 {dataset_type} 纯文本向量数据库...")
                    docs, metadatas = self.prepare_general_text_documents(text_df, dataset_type)
                    
                    # 添加文档到多模态向量数据库
                    if docs and self.multimodal_vector_db is not None:
                        self.add_documents_to_db(self.multimodal_vector_db, docs, metadatas)
            
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
            print("=" * 80)
            print("📁 数据库位置:")
            print(f"  - 多模态向量数据库: {self.config['MULTIMODAL_VECTOR_DB_PATH']}")
            print("=" * 80)
            print("🚀 智诊通多模态向量数据库构建流程结束")
            print("=" * 80)
            
            logger.info("多模态向量数据库构建完成！")
            logger.info(f"多模态向量数据库: {self.config['MULTIMODAL_VECTOR_DB_PATH']}")
            
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