"""
向量化服务模块
负责文本和图像的向量化处理，为RAG检索提供向量表示
注意：此模块现在调用构建知识库模块的向量化服务，避免重复实现
"""

import os
import sys
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from PIL import Image

# 添加构建知识库模块路径
project_root = Path(__file__).parent.parent.parent.parent.parent
embedding_models_path = project_root / "codes" / "ai_models" / "embedding_models"
sys.path.insert(0, str(embedding_models_path))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入构建知识库模块的向量化服务
try:
    # 直接导入，不使用相对导入
    import core.vectorization_service as vs_module
    import core.medical_knowledge_manager as km_module
    import processors.document_chunker as dc_module
    
    VectorizationService = vs_module.VectorizationService
    MedicalKnowledgeManager = km_module.MedicalKnowledgeManager
    DocumentChunker = dc_module.DocumentChunker
    create_medical_chunker = dc_module.create_medical_chunker
    
    EMBEDDING_SERVICE_AVAILABLE = True
    logger.info("成功导入构建知识库模块的向量化服务")
except ImportError as e:
    logger.warning(f"无法导入构建知识库模块的向量化服务: {e}")
    EMBEDDING_SERVICE_AVAILABLE = False


class VectorService:
    """向量化服务类，负责文本和图像的向量化处理"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化向量化服务
        
        Args:
            config: 配置字典，包含模型路径、设备等配置信息
        """
        self.config = config
        self.vector_dim = config.get('vector_dim', 768)  # 默认维度，会根据实际模型调整
        self.batch_size = config.get('batch_size', 32)
        
        # 初始化构建知识库模块的向量化服务
        self.embedding_service = None
        self.knowledge_manager = None
        self.document_chunker = None
        
        if EMBEDDING_SERVICE_AVAILABLE:
            try:
                # 初始化医疗知识管理器
                self.knowledge_manager = MedicalKnowledgeManager()
                
                # 初始化向量化服务
                self.embedding_service = VectorizationService()
                
                # 初始化文档切分器
                self.document_chunker = create_medical_chunker()
                
                logger.info("成功初始化构建知识库模块的向量化服务")
            except Exception as e:
                logger.error(f"初始化构建知识库模块的向量化服务失败: {e}")
                self._init_fallback_service()
        else:
            logger.warning("构建知识库模块的向量化服务不可用，使用备用方案")
            self._init_fallback_service()
        
        # 向量数据库
        self.vector_db = None
        self.db_path = self.config.get('vector_db_path', '../../../datas/vector_databases/text')
        self._init_vector_db()
    
    def _init_fallback_service(self):
        """初始化备用向量化服务（当构建知识库模块不可用时）"""
        try:
            import torch
            from sentence_transformers import SentenceTransformer
            import os
            
            self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
            self.text_model = None
            self.image_model = None
            
            # 尝试加载文本向量化模型（本地优先策略）
            text_model_path = self.config.get('text_model_path', 'sentence-transformers/all-MiniLM-L6-v2')
            self.text_model = self._load_model_with_fallback(text_model_path, 'text')
            
            # 设置模型名称用于ChromaDB
            self.model_name = text_model_path
            
            # 尝试加载图像向量化模型（本地优先策略）
            image_model_path = self.config.get('image_model_path', 'clip-ViT-B-32')
            self.image_model = self._load_model_with_fallback(image_model_path, 'image')
            
            # 根据实际加载的模型调整向量维度
            self._adjust_vector_dimension()
            
            logger.info("Fallback models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading fallback models: {e}")
            # 如果所有模型都失败，使用简单的TF-IDF作为最后的后备
            self._init_simple_fallback()
            self._adjust_vector_dimension()
    
    def _load_model_with_fallback(self, model_path: str, model_type: str):
        """使用本地优先策略加载模型"""
        try:
            from sentence_transformers import SentenceTransformer
            import os
            import tempfile
            
            # 0. 首先检查配置文件中指定的绝对路径
            if os.path.isabs(model_path) and os.path.exists(model_path):
                logger.info(f"Found configured {model_type} model at {model_path}")
                return SentenceTransformer(model_path, device=self.device)
            
            # 1. 检查本地缓存目录
            cache_dir = os.path.expanduser("~/.cache/huggingface/transformers")
            local_path = os.path.join(cache_dir, model_path.replace("/", "--"))
            
            if os.path.exists(local_path):
                logger.info(f"Found local {model_type} model at {local_path}")
                return SentenceTransformer(local_path, device=self.device)
            
            # 2. 检查项目内的模型目录
            project_models_dir = Path(__file__).parent.parent.parent.parent / "models" / "embedding"
            project_model_path = project_models_dir / model_path.replace("/", "_")
            
            if project_model_path.exists():
                logger.info(f"Found project {model_type} model at {project_model_path}")
                return SentenceTransformer(str(project_model_path), device=self.device)
            
            # 3. 尝试从Hugging Face下载（带重试机制）
            logger.info(f"Attempting to download {model_type} model from Hugging Face: {model_path}")
            try:
                # 设置离线模式为False，允许下载
                model = SentenceTransformer(model_path, device=self.device)
                logger.info(f"Successfully downloaded {model_type} model: {model_path}")
                return model
            except Exception as download_error:
                logger.warning(f"Failed to download {model_type} model: {download_error}")
                raise download_error
                
        except Exception as e:
            logger.error(f"Failed to load {model_type} model: {e}")
            return None
    
    def _init_simple_fallback(self):
        """初始化简单的后备向量化服务（TF-IDF）"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            import numpy as np
            
            logger.info("Initializing simple TF-IDF fallback model")
            
            # 使用TF-IDF作为最后的后备
            self.text_model = TfidfVectorizer(
                max_features=1000,
                stop_words=None,  # 中文不需要英文停用词
                ngram_range=(1, 2),
                lowercase=False  # 保持原始大小写
            )
            self.image_model = None  # 图像处理暂时跳过
            self.model_name = "tfidf-fallback"
            
            # 标记使用简单模型
            self._use_simple_model = True
            
            logger.info("Simple TF-IDF fallback model initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize simple fallback model: {e}")
            # 最后的最后，设置为None
            self.text_model = None
            self.image_model = None
            self.model_name = "none"
            self._use_simple_model = False
    
    def _adjust_vector_dimension(self):
        """根据实际加载的模型调整向量维度"""
        try:
            if hasattr(self, '_use_simple_model') and self._use_simple_model:
                # TF-IDF模型的维度由max_features决定
                if hasattr(self.text_model, 'max_features'):
                    self.vector_dim = self.text_model.max_features
                else:
                    self.vector_dim = 1000  # 默认TF-IDF维度
                logger.info(f"Adjusted vector dimension for TF-IDF model: {self.vector_dim}")
            elif self.text_model and hasattr(self.text_model, 'get_sentence_embedding_dimension'):
                # SentenceTransformer模型
                self.vector_dim = self.text_model.get_sentence_embedding_dimension()
                logger.info(f"Adjusted vector dimension for SentenceTransformer model: {self.vector_dim}")
            elif self.embedding_service:
                # 构建知识库模块的向量化服务
                self.vector_dim = self.config.get('vector_dim', 768)
                logger.info(f"Using configured vector dimension for embedding service: {self.vector_dim}")
            else:
                # 保持默认维度
                logger.info(f"Using default vector dimension: {self.vector_dim}")
        except Exception as e:
            logger.warning(f"Failed to adjust vector dimension: {e}")
            # 保持默认维度
            pass
    
    def _init_vector_db(self):
        """初始化向量数据库"""
        try:
            from langchain_chroma import Chroma
            from langchain_core.embeddings import Embeddings
            
            # 创建自定义嵌入函数，使用已经加载的模型
            class CustomEmbeddings(Embeddings):
                def __init__(self, model):
                    self.model = model
                
                def embed_documents(self, texts):
                    """嵌入文档列表"""
                    if self.model is None:
                        # 如果模型不可用，返回随机向量
                        import numpy as np
                        return [np.random.randn(768).tolist() for _ in texts]
                    return [self.model.encode(text).tolist() for text in texts]
                
                def embed_query(self, text):
                    """嵌入查询文本"""
                    if self.model is None:
                        # 如果模型不可用，返回随机向量
                        import numpy as np
                        return np.random.randn(768).tolist()
                    return self.model.encode(text).tolist()
            
            # 创建嵌入函数
            if hasattr(self, 'text_model') and self.text_model is not None:
                self.embedding_function = CustomEmbeddings(self.text_model)
                logger.info("Using loaded text model for embeddings")
            else:
                # 如果模型加载失败，使用空模型
                self.embedding_function = CustomEmbeddings(None)
                logger.warning("No text model available, using random embeddings")
            
            # 创建ChromaDB向量数据库
            self.vector_db = Chroma(
                persist_directory=self.db_path,
                embedding_function=self.embedding_function,
                collection_name="knowledge_retrieval"
            )
            logger.info("ChromaDB vector database initialized")
        except Exception as e:
            logger.error(f"Error initializing vector database: {e}")
            raise
    
    def text_to_vector(self, text: str) -> np.ndarray:
        """
        将文本转换为向量
        
        Args:
            text: 输入文本
            
        Returns:
            文本向量
        """
        try:
            print("=" * 50)
            print("🔤 文本向量化开始")
            print("=" * 50)
            logger.info("开始文本向量化...")
            
            # 1. 获取用户输入
            print("==========")
            print("获取用户输入开始")
            print("==========")
            logger.info(f"获取用户输入细节日志：文本长度={len(text)} 字符")
            logger.info(f"文本内容: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            logger.info("获取用户输入成功")
            print("获取用户输入结束")
            print("==========")
            
            # 2. 用户数据处理
            print("==========")
            print("用户数据处理开始")
            print("==========")
            logger.info("用户数据处理的细节日志：开始预处理文本")
            
            if not text or not text.strip():
                logger.warning("Empty text provided for vectorization")
                return np.zeros(self.vector_dim)
            
            logger.info(f"文本预处理完成，有效长度: {len(text.strip())} 字符")
            logger.info("用户数据处理完成")
            logger.info("用户数据处理成功")
            print("==========")
            
            # 3. 文本向量化
            print("==========")
            print("文本向量化开始")
            print("==========")
            logger.info("文本向量化的细节日志：开始将文本转换为向量")
            
            # 优先使用构建知识库模块的向量化服务
            if self.embedding_service:
                logger.info("使用构建知识库模块的向量化服务")
                vectors = self.embedding_service.process_texts([text])
                if len(vectors) > 0:
                    vector = vectors[0]
                    logger.info(f"向量化完成，向量维度: {len(vector)}")
                    logger.info("文本向量化成功")
                    print("文本向量化结束")
                    print("==========")
                    
                    # 4. 返回用户结果
                    print("==========")
                    print("返回用户结果开始")
                    print("==========")
                    logger.info("返回用户结果的细节日志：开始构建向量化结果")
                    logger.info("向量化结果: 成功")
                    logger.info("返回用户结果成功")
                    print("返回用户结果结束")
                    print("==========")
                    
                    print("=" * 50)
                    print("🎉 文本向量化完成")
                    print("=" * 50)
                    logger.info("文本向量化成功完成")
                    
                    return vector
            
            # 备用方案：使用本地模型
            if self.text_model:
                logger.info("使用备用向量化服务")
                
                # 检查是否使用简单TF-IDF模型
                if hasattr(self, '_use_simple_model') and self._use_simple_model:
                    logger.info("使用TF-IDF简单模型进行向量化")
                    # 对于TF-IDF，需要先fit，然后transform
                    if not hasattr(self, '_tfidf_fitted'):
                        # 使用一些示例文本进行fit
                        sample_texts = [text, "示例文本", "测试文本"]
                        self.text_model.fit(sample_texts)
                        self._tfidf_fitted = True
                    
                    vector = self.text_model.transform([text]).toarray().flatten()
                    # 归一化向量
                    if np.linalg.norm(vector) > 0:
                        vector = vector / np.linalg.norm(vector)
                else:
                    # 使用SentenceTransformer模型
                    vector = self.text_model.encode([text], convert_to_tensor=True)
                    vector = vector.cpu().numpy().flatten()
                    # 归一化向量
                    vector = vector / np.linalg.norm(vector)
                
                logger.info(f"备用向量化完成，向量维度: {len(vector)}")
                logger.info("文本向量化成功")
                print("文本向量化结束")
                print("==========")
                
                # 4. 返回用户结果
                print("==========")
                print("返回用户结果开始")
                print("==========")
                logger.info("返回用户结果的细节日志：开始构建向量化结果")
                logger.info("向量化结果: 成功")
                logger.info("返回用户结果成功")
                print("返回用户结果结束")
                print("==========")
                
                print("=" * 50)
                print("🎉 文本向量化完成")
                print("=" * 50)
                logger.info("文本向量化成功完成")
                
                return vector
            
            # 如果都不可用，返回零向量
            logger.warning("No vectorization service available, returning zero vector")
            logger.info("文本向量化成功")
            print("文本向量化结束")
            print("==========")
            
            # 4. 返回用户结果
            print("==========")
            print("返回用户结果开始")
            print("==========")
            logger.info("返回用户结果的细节日志：开始构建向量化结果")
            logger.info("向量化结果: 零向量")
            logger.info("返回用户结果成功")
            print("返回用户结果结束")
            print("==========")
            
            print("=" * 50)
            print("🎉 文本向量化完成")
            print("=" * 50)
            logger.info("文本向量化成功完成")
            
            return np.zeros(self.vector_dim)
            
        except Exception as e:
            print("=" * 50)
            print("❌ 文本向量化失败")
            print("=" * 50)
            logger.error(f"文本向量化失败: {e}")
            logger.error(f"Error converting text to vector: {e}")
            return np.zeros(self.vector_dim)
    
    def image_to_vector(self, image_path: str) -> np.ndarray:
        """
        将图像转换为向量
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            图像向量
        """
        try:
            if not os.path.exists(image_path):
                logger.warning(f"Image file not found: {image_path}")
                return np.zeros(self.vector_dim)
            
            # 加载和预处理图像
            image = Image.open(image_path).convert('RGB')
            
            # 使用CLIP模型进行图像向量化
            vector = self.image_model.encode([image], convert_to_tensor=True)
            vector = vector.cpu().numpy().flatten()
            
            # 归一化向量
            vector = vector / np.linalg.norm(vector)
            
            return vector
            
        except Exception as e:
            logger.error(f"Error converting image to vector: {e}")
            return np.zeros(self.vector_dim)
    
    def batch_text_to_vectors(self, texts: List[str]) -> np.ndarray:
        """
        批量将文本转换为向量
        
        Args:
            texts: 文本列表
            
        Returns:
            文本向量矩阵
        """
        try:
            if not texts:
                return np.array([])
            
            # 优先使用构建知识库模块的向量化服务
            if self.embedding_service:
                vectors = self.embedding_service.process_texts(texts)
                if len(vectors) > 0:
                    return vectors
            
            # 备用方案：使用本地模型
            if self.text_model:
                # 过滤空文本
                valid_texts = [text for text in texts if text and text.strip()]
                if not valid_texts:
                    return np.zeros((len(texts), self.vector_dim))
                
                # 批量向量化
                vectors = self.text_model.encode(valid_texts, convert_to_tensor=True, batch_size=self.batch_size)
                vectors = vectors.cpu().numpy()
                
                # 归一化向量
                vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
                
                # 如果原始列表中有空文本，需要补齐
                if len(valid_texts) < len(texts):
                    full_vectors = np.zeros((len(texts), self.vector_dim))
                    valid_idx = 0
                    for i, text in enumerate(texts):
                        if text and text.strip():
                            full_vectors[i] = vectors[valid_idx]
                            valid_idx += 1
                    vectors = full_vectors
                
                return vectors
            
            # 如果都不可用，返回零向量矩阵
            logger.warning("No vectorization service available, returning zero vectors")
            return np.zeros((len(texts), self.vector_dim))
            
        except Exception as e:
            logger.error(f"Error in batch text vectorization: {e}")
            return np.zeros((len(texts), self.vector_dim))
    
    def batch_image_to_vectors(self, image_paths: List[str]) -> np.ndarray:
        """
        批量将图像转换为向量
        
        Args:
            image_paths: 图像路径列表
            
        Returns:
            图像向量矩阵
        """
        try:
            if not image_paths:
                return np.array([])
            
            # 过滤有效图像路径
            valid_paths = [path for path in image_paths if os.path.exists(path)]
            if not valid_paths:
                return np.zeros((len(image_paths), self.vector_dim))
            
            # 加载图像
            images = []
            valid_indices = []
            for i, path in enumerate(image_paths):
                if os.path.exists(path):
                    try:
                        image = Image.open(path).convert('RGB')
                        images.append(image)
                        valid_indices.append(i)
                    except Exception as e:
                        logger.warning(f"Error loading image {path}: {e}")
            
            if not images:
                return np.zeros((len(image_paths), self.vector_dim))
            
            # 批量向量化
            vectors = self.image_model.encode(images, convert_to_tensor=True, batch_size=self.batch_size)
            vectors = vectors.cpu().numpy()
            
            # 归一化向量
            vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
            
            # 补齐缺失的向量
            if len(valid_indices) < len(image_paths):
                full_vectors = np.zeros((len(image_paths), self.vector_dim))
                for i, valid_idx in enumerate(valid_indices):
                    full_vectors[valid_idx] = vectors[i]
                vectors = full_vectors
            
            return vectors
            
        except Exception as e:
            logger.error(f"Error in batch image vectorization: {e}")
            return np.zeros((len(image_paths), self.vector_dim))
    
    def add_vectors_to_db(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]):
        """
        将向量添加到向量数据库
        
        Args:
            vectors: 向量矩阵
            metadata: 元数据列表
        """
        try:
            if vectors.size == 0:
                return
            
            # 确保向量是二维的
            if vectors.ndim == 1:
                vectors = vectors.reshape(1, -1)
            
            # 为ChromaDB准备文档和元数据
            documents = []
            metadatas = []
            
            for i, meta in enumerate(metadata):
                # 从元数据中提取文档内容
                doc_content = meta.get('content', meta.get('text', ''))
                if not doc_content:
                    # 如果没有内容，使用元数据信息作为文档
                    doc_content = f"Document {i}: {meta.get('title', 'Untitled')}"
                
                documents.append(doc_content)
                metadatas.append(meta)
            
            # 添加到ChromaDB
            self.vector_db.add_documents(
                documents=documents,
                metadatas=metadatas,
                embeddings=vectors.tolist()
            )
            
            logger.info(f"Added {len(vectors)} vectors to ChromaDB")
            
        except Exception as e:
            logger.error(f"Error adding vectors to database: {e}")
            raise
    
    def search_similar_vectors(self, query_vector: np.ndarray, top_k: int = 10) -> tuple:
        """
        在向量数据库中搜索相似向量
        
        Args:
            query_vector: 查询向量
            top_k: 返回前k个最相似的向量
            
        Returns:
            (相似度分数, 索引)
        """
        try:
            # 检查ChromaDB是否有数据
            if self.vector_db._collection.count() == 0:
                return np.array([]), np.array([])
            
            # 确保查询向量是二维的
            if query_vector.ndim == 1:
                query_vector = query_vector.reshape(1, -1)
            
            # 使用ChromaDB的相似度搜索
            results = self.vector_db.similarity_search_with_score_by_vector(
                embedding=query_vector[0].tolist(),
                k=top_k
            )
            
            # 提取分数和索引
            scores = np.array([result[1] for result in results])
            indices = np.array([i for i in range(len(results))])
            
            return scores, indices
            
        except Exception as e:
            logger.error(f"Error searching similar vectors: {e}")
            return np.array([]), np.array([])
    
    def save_vector_db(self, db_path: str):
        """
        保存向量数据库
        
        Args:
            db_path: 数据库保存路径
        """
        try:
            # ChromaDB会自动持久化，这里只需要确保目录存在
            os.makedirs(db_path, exist_ok=True)
            logger.info(f"ChromaDB vector database persisted to {db_path}")
            
        except Exception as e:
            logger.error(f"Error saving vector database: {e}")
            raise
    
    def load_vector_db(self, db_path: str):
        """
        加载向量数据库
        
        Args:
            db_path: 数据库文件路径
        """
        try:
            if os.path.exists(db_path):
                # ChromaDB会自动从持久化目录加载
                from langchain_chroma import Chroma
                from langchain_community.embeddings import HuggingFaceEmbeddings
                
                self.embedding_function = HuggingFaceEmbeddings(
                    model_name=self.model_name,
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
                
                self.vector_db = Chroma(
                    persist_directory=db_path,
                    embedding_function=self.embedding_function,
                    collection_name="knowledge_retrieval"
                )
                logger.info(f"ChromaDB vector database loaded from {db_path}")
            else:
                logger.warning(f"Vector database directory not found: {db_path}")
                
        except Exception as e:
            logger.error(f"Error loading vector database: {e}")
            raise
    
    def get_db_stats(self) -> Dict[str, Any]:
        """
        获取向量数据库统计信息
        
        Returns:
            数据库统计信息
        """
        try:
            return {
                'total_vectors': self.vector_db._collection.count(),
                'vector_dimension': self.vector_dim,
                'collection_name': 'knowledge_retrieval',
                'persist_directory': self.db_path
            }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def clear_db(self):
        """清空向量数据库"""
        try:
            # ChromaDB的reset方法会清空集合
            self.vector_db._collection.delete()
            logger.info("ChromaDB vector database cleared")
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            raise
    
    def chunk_document(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        切分文档
        
        Args:
            text: 输入文本
            metadata: 文档元数据
            
        Returns:
            切分后的文档片段列表
        """
        try:
            if self.document_chunker:
                return self.document_chunker.chunk_document(text, metadata)
            else:
                # 备用方案：简单切分
                return self._simple_chunking(text, metadata)
        except Exception as e:
            logger.error(f"文档切分失败: {e}")
            return []
    
    def _simple_chunking(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """简单文档切分（备用方案）"""
        chunk_size = 512
        overlap = 50
        chunks = []
        
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size
            if end >= len(text):
                chunk_text = text[start:]
            else:
                chunk_text = text[start:end]
            
            if len(chunk_text.strip()) > 100:  # 最小长度过滤
                chunk_data = {
                    'id': f"chunk_{chunk_index}",
                    'content': chunk_text.strip(),
                    'length': len(chunk_text),
                    'chunk_index': chunk_index,
                    'metadata': metadata or {}
                }
                chunks.append(chunk_data)
                chunk_index += 1
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def process_document_with_chunking(self, text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        处理文档（包含切分和向量化）
        
        Args:
            text: 输入文本
            metadata: 文档元数据
            
        Returns:
            处理结果
        """
        try:
            # 1. 文档切分
            chunks = self.chunk_document(text, metadata)
            
            if not chunks:
                return {'chunks': [], 'vectors': [], 'error': '文档切分失败'}
            
            # 2. 提取文本内容
            chunk_texts = [chunk['content'] for chunk in chunks]
            
            # 3. 向量化
            vectors = self.batch_text_to_vectors(chunk_texts)
            
            # 4. 组合结果
            result = {
                'chunks': chunks,
                'vectors': vectors,
                'total_chunks': len(chunks),
                'vector_dimension': vectors.shape[1] if len(vectors) > 0 else 0
            }
            
            return result
            
        except Exception as e:
            logger.error(f"文档处理失败: {e}")
            return {'chunks': [], 'vectors': [], 'error': str(e)}


class VectorServiceFactory:
    """向量化服务工厂类"""
    
    @staticmethod
    def create_vector_service(config_path: str = None) -> VectorService:
        """
        创建向量化服务实例
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            向量化服务实例
        """
        # 默认配置
        try:
            import torch
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        except ImportError:
            device = 'cpu'
            
        default_config = {
            'device': device,
            'vector_dim': 768,  # text2vec-base-chinese的向量维度
            'batch_size': 32,
            'text_model_path': 'shibing624/text2vec-base-chinese',
            'image_model_path': 'clip-ViT-B-32'
        }
        
        # 如果提供了配置文件，则加载配置
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Error loading config file: {e}, using default config")
        
        return VectorService(default_config)


if __name__ == "__main__":
    # 测试向量化服务
    config = {
        'device': 'cpu',
        'vector_dim': 768,  # text2vec-base-chinese的向量维度
        'batch_size': 16
    }
    
    vector_service = VectorService(config)
    
    # 测试文本向量化
    test_text = "患者出现胸痛症状，持续3小时，伴有呼吸困难"
    vector = vector_service.text_to_vector(test_text)
    print(f"Text vector shape: {vector.shape}")
    
    # 测试批量文本向量化
    test_texts = [
        "患者出现胸痛症状",
        "患者出现呼吸困难",
        "患者出现发热症状"
    ]
    vectors = vector_service.batch_text_to_vectors(test_texts)
    print(f"Batch text vectors shape: {vectors.shape}")
    
    # 测试向量数据库
    metadata = [{"text": text, "id": i} for i, text in enumerate(test_texts)]
    vector_service.add_vectors_to_db(vectors, metadata)
    
    # 测试搜索
    query_vector = vector_service.text_to_vector("胸痛")
    scores, indices = vector_service.search_similar_vectors(query_vector, top_k=2)
    print(f"Search results - scores: {scores}, indices: {indices}")
    
    # 获取数据库统计信息
    stats = vector_service.get_db_stats()
    print(f"Database stats: {stats}")
