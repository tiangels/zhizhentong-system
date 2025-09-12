"""
跨模态检索系统
实现文本到图像、图像到文本的跨模态检索功能
支持智诊通系统的多模态检索需求
"""

import os
import json
import numpy as np
from typing import Dict, List, Any, Optional
import logging
import sys

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 尝试导入图像向量化模块
try:
    # 添加models目录到路径
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
    sys.path.append(models_dir)
    from image_embedder import ImageEmbedderFactory
    IMAGE_EMBEDDING_AVAILABLE = True
    logger.info("✓ 图像向量化模块导入成功")
except ImportError as e:
    logger.warning(f"图像向量化模块未找到，将使用简化模式: {e}")
    IMAGE_EMBEDDING_AVAILABLE = False


class CrossModalRetrieval:
    """跨模态检索系统"""
    
    def __init__(self, config_path: str = None):
        """
        初始化跨模态检索系统
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.multimodal_vector_db = None
        self.text_embedder = None
        self.image_embedder = None
        self.image_text_mapping = {}
        
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
            # 使用默认配置
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        # 获取项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(current_dir, "..", "..", "..", "..")
        
        return {
            "MULTIMODAL_VECTOR_DB_PATH": os.path.join(project_root, "datas", "vector_databases", "multimodal"),
            "MULTIMODAL_COLLECTION_NAME": "medical_multimodal_vectors",
            "MAPPING_FILE": os.path.join(project_root, "datas", "vector_databases", "multimodal", "image_text_mapping.json"),
            "TEXT_EMBEDDING_MODEL": "shibing624/text2vec-base-chinese",
            "IMAGE_EMBEDDING_MODEL": "resnet50"
        }
    
    def _init_components(self):
        """初始化各个组件"""
        try:
            # 初始化文本嵌入模型
            self._init_text_embedder()
            
            # 初始化图像嵌入模型
            self._init_image_embedder()
            
            # 初始化多模态向量数据库
            self._init_multimodal_vector_db()
            
            # 加载图像文本映射关系
            self._load_image_text_mapping()
            
            logger.info("跨模态检索系统初始化完成")
            
        except Exception as e:
            logger.error(f"初始化组件失败: {e}")
            raise
    
    def _init_text_embedder(self):
        """初始化文本嵌入模型"""
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            
            # 尝试使用本地模型或简化模型
            model_name = self.config["TEXT_EMBEDDING_MODEL"]
            
            # 如果网络有问题，使用简化的模型
            try:
                self.text_embedder = HuggingFaceEmbeddings(
                    model_name=model_name,
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
                logger.info(f"文本嵌入模型初始化成功: {model_name}")
            except Exception as network_error:
                logger.warning(f"网络下载模型失败，使用简化模式: {network_error}")
                # 使用一个更简单的模型或者创建虚拟嵌入器
                self.text_embedder = self._create_dummy_embedder()
                logger.info("使用虚拟文本嵌入模型")
            
        except Exception as e:
            logger.error(f"文本嵌入模型初始化失败: {e}")
            # 创建虚拟嵌入器作为后备
            self.text_embedder = self._create_dummy_embedder()
            logger.info("使用虚拟文本嵌入模型作为后备")
    
    def _create_dummy_embedder(self):
        """创建虚拟嵌入器用于测试"""
        class DummyEmbedder:
            def embed_documents(self, texts):
                import numpy as np
                return [np.random.rand(768).tolist() for _ in texts]
            
            def embed_query(self, text):
                import numpy as np
                return np.random.rand(768).tolist()
        
        return DummyEmbedder()
    
    def _init_image_embedder(self):
        """初始化图像嵌入模型"""
        try:
            if IMAGE_EMBEDDING_AVAILABLE:
                from image_embedder import ImageEmbedderFactory
                self.image_embedder = ImageEmbedderFactory.create_embedder(
                    embedder_type=self.config.get("IMAGE_EMBEDDER_TYPE", "resnet"),
                    model_name=self.config["IMAGE_EMBEDDING_MODEL"]
                )
                logger.info(f"图像嵌入模型初始化成功: {self.config['IMAGE_EMBEDDING_MODEL']}")
            else:
                logger.warning("图像嵌入模块不可用，图像检索功能将被禁用")
                self.image_embedder = None
                
        except Exception as e:
            logger.error(f"图像嵌入模型初始化失败: {e}")
            self.image_embedder = None
    
    def _init_multimodal_vector_db(self):
        """初始化多模态向量数据库"""
        try:
            from langchain_chroma import Chroma
            
            # 检查数据库是否存在
            if not os.path.exists(self.config["MULTIMODAL_VECTOR_DB_PATH"]):
                raise FileNotFoundError(f"多模态向量数据库不存在: {self.config['MULTIMODAL_VECTOR_DB_PATH']}")
            
            self.multimodal_vector_db = Chroma(
                persist_directory=self.config["MULTIMODAL_VECTOR_DB_PATH"],
                embedding_function=self.text_embedder,
                collection_name=self.config["MULTIMODAL_COLLECTION_NAME"]
            )
            
            logger.info("多模态向量数据库初始化成功")
            
        except Exception as e:
            logger.error(f"多模态向量数据库初始化失败: {e}")
            raise
    
    def _load_image_text_mapping(self):
        """加载图像和文本的映射关系"""
        try:
            mapping_file = self.config["MAPPING_FILE"]
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    self.image_text_mapping = json.load(f)
                logger.info(f"已加载 {len(self.image_text_mapping)} 个图像文本映射关系")
            else:
                logger.warning(f"未找到映射文件: {mapping_file}")
                
        except Exception as e:
            logger.error(f"加载图像文本映射关系失败: {e}")
            self.image_text_mapping = {}
    
    def search(self, query: str = None, image_path: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        统一的跨模态检索接口
        
        Args:
            query: 文本查询
            image_path: 图像查询路径
            top_k: 返回结果数量
            
        Returns:
            检索结果列表
        """
        results = []
        
        try:
            if query:
                # 文本检索
                text_results = self._search_by_text(query, top_k)
                results.extend(text_results)
            
            if image_path and self.image_embedder:
                # 图像检索
                image_results = self._search_by_image(image_path, top_k)
                results.extend(image_results)
            
            # 按相似度排序并去重
            results = self._deduplicate_and_sort_results(results, top_k)
            
            logger.info(f"检索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []
    
    def _search_by_text(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """文本检索"""
        try:
            # 在多模态向量数据库中搜索
            search_results = self.multimodal_vector_db.similarity_search_with_score(query, k=top_k)
            
            results = []
            for doc, score in search_results:
                result = {
                    'text': doc.page_content,  # 统一使用'text'字段
                    'content': doc.page_content,  # 保持向后兼容
                    'content_type': 'text',
                    'similarity_score': float(score),
                    'metadata': doc.metadata,
                    'uid': doc.metadata.get('uid', ''),
                    'source': 'multimodal_db'
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"文本检索失败: {e}")
            return []
    
    def _search_by_image(self, image_path: str, top_k: int) -> List[Dict[str, Any]]:
        """图像检索"""
        try:
            if not self.image_embedder:
                logger.warning("图像嵌入模型不可用，跳过图像检索")
                return []
            
            # 对输入图像进行向量化
            image_vector = self.image_embedder.embed_image(image_path)
            
            # 确保图像向量维度与文本向量一致（768维）
            if len(image_vector) != 768:
                # 如果维度不匹配，使用PCA降维或截断
                if len(image_vector) > 768:
                    image_vector = image_vector[:768]  # 截断到768维
                else:
                    # 如果维度不足，用零填充
                    import numpy as np
                    padded_vector = np.zeros(768)
                    padded_vector[:len(image_vector)] = image_vector
                    image_vector = padded_vector
            
            # 在图像向量数据库中搜索
            # 注意：这里需要直接使用ChromaDB的查询API
            image_results = self.multimodal_vector_db._collection.query(
                query_embeddings=[image_vector.tolist()],
                n_results=top_k
            )
            
            results = []
            if image_results['ids'] and len(image_results['ids'][0]) > 0:
                for i, (doc_id, metadata, distance) in enumerate(zip(
                    image_results['ids'][0],
                    image_results['metadatas'][0],
                    image_results['distances'][0]
                )):
                    # 从图像ID中提取索引
                    if 'image_' in doc_id:
                        idx = doc_id.split('_')[1]
                        
                        # 查找对应的文本内容
                        text_content = ""
                        if idx in self.image_text_mapping:
                            text_content = self.image_text_mapping[idx]['text']
                            metadata.update(self.image_text_mapping[idx]['metadata'])
                        
                        result = {
                            'text': text_content,  # 统一使用'text'字段
                            'content': text_content,  # 保持向后兼容
                            'content_type': 'image',
                            'similarity_score': float(1 - distance),  # 转换为相似度分数
                            'metadata': metadata,
                            'uid': idx,
                            'source': 'multimodal_db'
                        }
                        results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"图像检索失败: {e}")
            return []
    
    def _deduplicate_and_sort_results(self, results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """去重并排序结果"""
        try:
            # 按UID去重
            seen_uids = set()
            unique_results = []
            
            for result in results:
                uid = result.get('uid', '')
                if uid not in seen_uids:
                    seen_uids.add(uid)
                    unique_results.append(result)
            
            # 按相似度排序
            unique_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return unique_results[:top_k]
            
        except Exception as e:
            logger.error(f"结果去重排序失败: {e}")
            return results[:top_k]
    
    def get_image_text_pairs(self, uids: List[str] = None, top_k: int = None) -> List[Dict[str, Any]]:
        """
        获取图像文本对
        
        Args:
            uids: UID列表（可选）
            top_k: 返回前k个结果（可选）
            
        Returns:
            图像文本对列表
        """
        if uids is not None:
            # 根据UID列表获取
            pairs = []
            for uid in uids:
                if uid in self.image_text_mapping:
                    pairs.append({
                        'uid': uid,
                        'text': self.image_text_mapping[uid]['text'],
                        'metadata': self.image_text_mapping[uid]['metadata']
                    })
            return pairs
        else:
            # 获取所有图像文本对
            pairs = []
            for uid, data in self.image_text_mapping.items():
                pairs.append({
                    'uid': uid,
                    'text': data['text'],
                    'metadata': data['metadata']
                })
            
            # 如果指定了top_k，返回前k个
            if top_k is not None:
                pairs = pairs[:top_k]
            
            return pairs
    
    def text_to_image_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        文本到图像的跨模态检索
        
        Args:
            query: 文本查询
            top_k: 返回结果数量
            
        Returns:
            图像检索结果列表
        """
        try:
            # 使用文本查询在多模态数据库中搜索
            search_results = self.multimodal_vector_db.similarity_search_with_score(query, k=top_k)
            
            results = []
            for doc, score in search_results:
                # 只返回有图像的结果
                if doc.metadata.get('has_image', False):
                    result = {
                        'content': doc.page_content,
                        'content_type': 'text_to_image',
                        'similarity_score': float(score),
                        'metadata': doc.metadata,
                        'uid': doc.metadata.get('uid', ''),
                        'source': 'multimodal_db'
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"文本到图像检索失败: {e}")
            return []
    
    def image_to_text_search(self, image_path: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        图像到文本的跨模态检索
        
        Args:
            image_path: 图像路径
            top_k: 返回结果数量
            
        Returns:
            文本检索结果列表
        """
        return self._search_by_image(image_path, top_k)


def main():
    """主函数 - 测试跨模态检索功能"""
    try:
        # 创建跨模态检索系统
        retrieval = CrossModalRetrieval()
        
        # 测试文本检索
        print("\n=== 测试文本检索 ===")
        text_results = retrieval.search(query="胸部X光检查", top_k=3)
        for i, result in enumerate(text_results):
            print(f"结果 {i+1}: {result['content'][:100]}...")
            print(f"相似度: {result['similarity_score']:.4f}")
            print(f"类型: {result['content_type']}")
            print("-" * 50)
        
        # 测试文本到图像检索
        print("\n=== 测试文本到图像检索 ===")
        text_to_image_results = retrieval.text_to_image_search("肺部疾病", top_k=3)
        for i, result in enumerate(text_to_image_results):
            print(f"结果 {i+1}: {result['content'][:100]}...")
            print(f"相似度: {result['similarity_score']:.4f}")
            print(f"类型: {result['content_type']}")
            print("-" * 50)
        
        logger.info("跨模态检索测试完成")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        raise


if __name__ == "__main__":
    main()
