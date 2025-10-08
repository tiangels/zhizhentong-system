"""
检索服务模块
负责从向量数据库中检索相关文档，为知识检索生成提供上下文
"""

import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
# import faiss  # 暂时注释掉，使用numpy替代
from datetime import datetime

# 使用统一日志配置
import sys
from pathlib import Path

# 添加common模块到路径
current_file = Path(__file__)
common_dir = current_file.parent.parent.parent.parent / "common"
sys.path.insert(0, str(common_dir))

# 添加项目根目录到路径
import sys
from pathlib import Path
current_file = Path(__file__)
project_root = current_file.parent.parent.parent.parent  # 回到codes目录
sys.path.insert(0, str(project_root))

from common.log_config import setup_logging, get_logger
from services.knowledge_retrieval_service.hybrid.hybrid_core import UserCentricHybrid

setup_logging("retrieval_service")
logger = get_logger(__name__)


class RetrievalService:
    """检索服务类，负责文档检索和排序"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化检索服务
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.vector_db = None
        self.metadata_db = {}  # 存储文档元数据
        self.vector_dim = config.get('vector_dim', 384)
        self.max_results = config.get('max_results', 20)
        self.similarity_threshold = config.get('similarity_threshold', 0.5)  # 调整阈值为0.5
        
        # 检索策略配置
        self.retrieval_strategies = {
            'semantic': self._semantic_retrieval,
            'es': None,  # 占位，初始化后绑定到 _es_retrieval
            'hybrid': self._hybrid_retrieval,
            'rerank': self._rerank_retrieval
        }
        
        self.current_strategy = config.get('retrieval_strategy', 'semantic')
        
        # 初始化向量数据库
        self._init_vector_db()
        # 绑定 ES 策略实现（依赖于已初始化的 self.es_client）
        self.retrieval_strategies['es'] = lambda _qv, top_k, query_text=None: self._es_retrieval(top_k=top_k, query_text=query_text)
    
    def _init_vector_db(self):
        """初始化向量数据库连接"""
        try:
            # 尝试初始化ChromaDB
            try:
                import chromadb
                from chromadb.config import Settings
                import os
                
                # 获取ChromaDB配置
                vector_db_path = self.config.get('vector_db_path', '/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/chroma_db')
                collection_name = self.config.get('collection_name', 'medical_multimodal_vectors')
                
                # 添加详细的数据库目录日志
                logger.info("=" * 80)
                logger.info("🗄️ 向量化数据库初始化开始")
                logger.info("=" * 80)
                logger.info(f"📁 向量数据库路径: {vector_db_path}")
                logger.info(f"📂 路径是否存在: {os.path.exists(vector_db_path)}")
                
                if os.path.exists(vector_db_path):
                    try:
                        db_contents = os.listdir(vector_db_path)
                        logger.info(f"📋 数据库目录内容: {db_contents}")
                        
                        # 检查关键文件
                        sqlite_file = os.path.join(vector_db_path, 'chroma.sqlite3')
                        mapping_file = os.path.join(vector_db_path, 'image_text_mapping.json')
                        
                        logger.info(f"🗃️ SQLite数据库文件: {os.path.exists(sqlite_file)}")
                        if os.path.exists(sqlite_file):
                            sqlite_size = os.path.getsize(sqlite_file)
                            logger.info(f"📊 SQLite文件大小: {sqlite_size} bytes ({sqlite_size/1024:.2f} KB)")
                        
                        logger.info(f"🔗 图像文本映射文件: {os.path.exists(mapping_file)}")
                        if os.path.exists(mapping_file):
                            mapping_size = os.path.getsize(mapping_file)
                            logger.info(f"📊 映射文件大小: {mapping_size} bytes ({mapping_size/1024:.2f} KB)")
                            
                    except Exception as e:
                        logger.warning(f"⚠️ 读取数据库目录内容失败: {e}")
                else:
                    logger.warning(f"⚠️ 向量数据库目录不存在: {vector_db_path}")
                
                logger.info(f"🏷️ 集合名称: {collection_name}")
                logger.info("=" * 80)
                
                # 初始化ChromaDB客户端
                self.chroma_client = chromadb.PersistentClient(
                    path=vector_db_path,
                    settings=Settings(anonymized_telemetry=False)
                )
                logger.info("✅ ChromaDB客户端初始化成功")
                
                # 直接使用原生ChromaDB集合
                try:
                    self.multimodal_collection = self.chroma_client.get_collection(
                        name=collection_name
                    )
                    logger.info(f"✅ 成功连接到ChromaDB集合: {collection_name}")
                    
                    # 检查集合中的文档数量
                    doc_count = self.multimodal_collection.count()
                    logger.info(f"📊 ChromaDB集合中有 {doc_count} 个文档")
                    
                    # 获取集合的详细信息
                    try:
                        # 获取少量样本数据以验证集合状态
                        sample_data = self.multimodal_collection.peek(limit=3)
                        logger.info(f"📝 集合样本数据预览:")
                        logger.info(f"   - 样本ID数量: {len(sample_data.get('ids', []))}")
                        logger.info(f"   - 样本文档数量: {len(sample_data.get('documents', []))}")
                        logger.info(f"   - 样本元数据数量: {len(sample_data.get('metadatas', []))}")
                        logger.info(f"   - 样本嵌入向量数量: {len(sample_data.get('embeddings', []))}")
                        
                        if sample_data.get('ids'):
                            logger.info(f"   - 第一个文档ID: {sample_data['ids'][0]}")
                        if sample_data.get('metadatas') and sample_data['metadatas'][0]:
                            first_metadata = sample_data['metadatas'][0]
                            logger.info(f"   - 第一个文档类型: {first_metadata.get('data_type', 'unknown')}")
                            logger.info(f"   - 第一个文档来源: {first_metadata.get('source', 'unknown')}")
                            
                    except Exception as e:
                        logger.warning(f"⚠️ 获取集合详细信息失败: {e}")
                    
                except ValueError:
                    # 集合不存在，创建新集合
                    logger.warning(f"⚠️ 集合 {collection_name} 不存在，创建新集合")
                    self.multimodal_collection = self.chroma_client.create_collection(
                        name=collection_name,
                        metadata={'description': '智诊通多模态向量数据库'}
                    )
                    logger.info(f"✅ 创建新ChromaDB集合: {collection_name}")
                
                # 为了兼容性，设置vector_db为None（使用原生客户端）
            self.vector_db = None
                logger.info("🎯 向量数据库初始化完成")
                logger.info("=" * 80)
                
            except ImportError:
                logger.warning("ChromaDB未安装，使用备用存储")
                self.vector_db = None
                self.chroma_client = None
            
            # 初始化ES检索客户端
            try:
                from elasticsearch import Elasticsearch
                # 修复ES客户端初始化，添加正确的配置
                self.es_client = Elasticsearch(
                    hosts=['http://localhost:9200'],
                    timeout=30,
                    max_retries=3,
                    retry_on_timeout=True,
                    verify_certs=False,
                    ssl_show_warn=False
                )
                
                # 检查ES连接
                if self.es_client.ping():
                    logger.info("成功连接到Elasticsearch")
                    
                    # 检查medical_records索引
                    if self.es_client.indices.exists(index="medical_records"):
                        doc_count = self.es_client.count(index="medical_records")['count']
                        logger.info(f"Elasticsearch medical_records索引中有 {doc_count} 个文档")
                    else:
                        logger.warning("Elasticsearch中没有medical_records索引")
                        
                    # 检查medical_records_enhanced索引
                    if self.es_client.indices.exists(index="medical_records_enhanced"):
                        doc_count = self.es_client.count(index="medical_records_enhanced")['count']
                        logger.info(f"Elasticsearch medical_records_enhanced索引中有 {doc_count} 个文档")
                    else:
                        logger.warning("Elasticsearch中没有medical_records_enhanced索引")
                else:
                    logger.warning("无法连接到Elasticsearch")
                    self.es_client = None
                    
            except ImportError:
                logger.warning("Elasticsearch客户端未安装")
                self.es_client = None
            except Exception as e:
                logger.warning(f"ES连接失败: {e}")
                self.es_client = None
            
            # 保留numpy数组作为备用
            self.vectors = []  # 存储向量
            self.documents = []  # 存储文档
            logger.info("检索服务初始化完成")
            
        except Exception as e:
            logger.error(f"初始化检索服务失败: {e}")
            # 设置默认值，确保服务不会崩溃
            self.vector_db = None
            self.chroma_client = None
            self.es_client = None
            self.vectors = []
            self.documents = []
    
    def add_documents(self, vectors: np.ndarray, documents: List[Dict[str, Any]]):
        """
        添加文档到检索系统（已弃用 - 知识检索服务不管理向量数据库）
        
        Args:
            vectors: 文档向量矩阵
            documents: 文档元数据列表
        """
        logger.warning("知识检索服务不再支持添加文档，请使用向量化服务来添加文档")
        logger.info("知识检索服务只负责检索已存在的向量化数据")
        return True
    
    def retrieve_documents(self, query_vector: np.ndarray, top_k: int = 10, 
                          strategy: str = None, query_text: str = None) -> List[Dict[str, Any]]:
        """
        检索相关文档（通过向量化服务API）
        
        Args:
            query_vector: 查询向量
            top_k: 返回文档数量
            strategy: 检索策略
            query_text: 查询文本
            
        Returns:
            检索到的文档列表
        """
        try:
            print("=" * 50)
            print("🔍 文档检索开始")
            print("=" * 50)
            logger.info("开始文档检索...")
            
            # 1. 获取用户输入
            print("==========")
            print("获取用户输入开始")
            print("==========")
            logger.info(f"获取用户输入细节日志：向量维度={len(query_vector) if query_vector is not None else 'None'}, top_k={top_k}, strategy='{strategy}'")
            logger.info("获取用户输入成功")
            print("获取用户输入结束")
            print("==========")
            
            # 2. 用户数据处理
            print("==========")
            print("用户数据处理开始")
            print("==========")
            logger.info("用户数据处理的细节日志：开始验证检索参数")
            
            if not query_text:
                logger.warning("没有提供查询文本，无法进行检索")
                return []
            
            # 使用指定的检索策略
            strategy = strategy or self.current_strategy
            if strategy not in self.retrieval_strategies:
                strategy = 'semantic'
                logger.info(f"使用默认检索策略: {strategy}")
            
            logger.info(f"检索策略: {strategy}")
            logger.info(f"相似度阈值: {self.similarity_threshold}")
            logger.info("用户数据处理完成")
            logger.info("用户数据处理成功")
            print("==========")
            
            # 3. 执行检索（根据策略分发）
            print("==========")
            print("执行检索开始")
            print("==========")

            if strategy == 'hybrid':
                logger.info("执行混合检索策略 (语义 + 关键词/ES + 融合)")
                results = self._hybrid_retrieval(query_vector, top_k, query_text)
            elif strategy == 'es':
                logger.info("执行纯 ES 检索策略")
                results = self._es_retrieval(top_k=top_k, query_text=query_text)
            else:
                logger.info("执行语义检索策略（向量化服务）")
                logger.info("执行检索的细节日志：开始通过向量化服务API执行文档检索")
                logger.info(f"开始调用_retrieve_from_vectorization_service: query='{query_text}', top_k={top_k}")
            results = self._retrieve_from_vectorization_service(query_text, top_k)

            logger.info(f"初步检索完成，找到 {len(results)} 个文档")
            
            # 详细记录检索结果
            if results:
                logger.info("=== 检索结果详情 ===")
                for i, result in enumerate(results):
                    logger.info(f"结果 {i+1}: 相似度={result.get('similarity', 0):.3f}, 来源={result.get('source', 'unknown')}, 标题='{result.get('title', '无标题')}'")
                logger.info("=== 检索结果详情结束 ===")
            else:
                logger.warning("⚠️ 初步检索没有找到任何文档")
            
            # 过滤低相似度结果
            if strategy == 'hybrid':
                # 混合检索使用融合分数进行排序，不对相似度做阈值过滤，直接取前 top_k
                filtered_results = results
                logger.info("混合检索模式：跳过相似度阈值过滤，直接使用融合结果")
            else:
            filtered_results = [
                result for result in results 
                if result.get('similarity', 0) >= self.similarity_threshold
            ]
            logger.info(f"相似度过滤完成，保留 {len(filtered_results)} 个文档（阈值: {self.similarity_threshold:.1%}）")
            
            # 记录相似度分布信息
            if results:
                similarities = [result.get('similarity', 0) for result in results]
                max_sim = max(similarities)
                min_sim = min(similarities)
                avg_sim = sum(similarities) / len(similarities)
                logger.info(f"相似度分布: 最高={max_sim:.3f}, 最低={min_sim:.3f}, 平均={avg_sim:.3f}")
            
            final_results = filtered_results[:top_k]
            logger.info(f"最终返回 {len(final_results)} 个文档")
            
            # 如果没有相关结果，记录警告
            if not final_results:
                logger.warning(f"⚠️ 没有找到相似度大于 {self.similarity_threshold:.1%} 的相关文档")
                if results:
                    logger.warning(f"最高相似度仅为: {max_sim:.3f}")
                else:
                    logger.warning("知识库中没有任何文档")
            logger.info("执行检索成功")
            print("执行检索结束")
            print("==========")
            
            # 4. 返回用户结果
            print("==========")
            print("返回用户结果开始")
            print("==========")
            logger.info("返回用户结果的细节日志：开始构建检索结果")
            logger.info(f"检索结果数量: {len(final_results)}")
            for i, result in enumerate(final_results):
                similarity = result.get('similarity', 0)
                hybrid_score = result.get('_hybrid_score', None)
                title = result.get('title', '无标题')
                if hybrid_score is not None:
                    logger.info(f"结果 {i+1}: 融合分数={hybrid_score:.6f}, 相似度={similarity:.3f}, 标题='{title}'")
                else:
                logger.info(f"结果 {i+1}: 相似度={similarity:.3f}, 标题='{title}'")
            logger.info("返回用户结果成功")
            print("返回用户结果结束")
            print("==========")
            
            print("=" * 50)
            print("🎉 文档检索完成")
            print("=" * 50)
            logger.info("文档检索成功完成")
            
            return final_results
            
        except Exception as e:
            print("=" * 50)
            print("❌ 文档检索失败")
            print("=" * 50)
            logger.error(f"文档检索失败: {e}")
            logger.error(f"Error retrieving documents: {e}")
            return []

    def _es_retrieval(self, top_k: int, query_text: str = None) -> List[Dict[str, Any]]:
        """
        仅使用 Elasticsearch 执行关键词/全文检索，并输出详细 ES 日志
        """
        try:
            results: List[Dict[str, Any]] = []
            logger.info("=== ES 检索开始 ===")
            logger.info(f"查询文本: '{query_text}'，top_k={top_k}")

            # 检查 ES 连接
            if self.es_client is None:
                logger.warning("ES 客户端未初始化，无法执行 ES 检索")
                return []
            if not self.es_client.ping():
                logger.warning("ES 连接失败，无法执行 ES 检索")
                return []

            # 构建 ES 查询（沿用向量化服务检索中的 fallback 查询）
            es_query = {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "multi_match": {
                                    "query": query_text or "",
                                    "fields": [
                                        "content^2",
                                        "symptoms^1.5",
                                        "diagnosis^1.5",
                                        "treatment^1.2",
                                        "title^1.8"
                                    ],
                                    "type": "best_fields",
                                    "fuzziness": "AUTO"
                                }
                            },
                            {
                                "match_phrase": {
                                    "content": {
                                        "query": query_text or "",
                                        "boost": 2.0
                                    }
                                }
                            }
                        ],
                        "minimum_should_match": 1
                    }
                },
                "size": top_k,
                "_source": [
                    "id",
                    "title",
                    "content",
                    "symptoms",
                    "diagnosis",
                    "treatment",
                    "department",
                    "visit_date"
                ],
                "sort": [
                    {"_score": {"order": "desc"}},
                    {"visit_date": {"order": "desc"}}
                ]
            }

            logger.info(f"ES 查询条件: {es_query}")

            es_indices = ["medical_records", "medical_records_enhanced"]
            logger.info(f"尝试 ES 索引: {es_indices}")

            for index in es_indices:
                try:
                    logger.info(f"检查索引: {index}")
                    if not self.es_client.indices.exists(index=index):
                        logger.info(f"索引不存在: {index}")
                        continue

                    es_response = self.es_client.search(index=index, body=es_query)
                    total = es_response['hits']['total']['value']
                    max_score = es_response['hits'].get('max_score', 0)
                    logger.info(f"ES 索引 {index} 响应: 总命中数={total}, 最大分数={max_score}")

                    hits = es_response['hits']['hits']
                    if not hits:
                        logger.info(f"索引 {index} 无命中结果")
                        continue

                    logger.info(f"处理 ES 命中结果: {len(hits)} 个文档")
                    for i, hit in enumerate(hits):
                        source = hit['_source']
                        score = hit['_score']

                        content_parts = []
                        if source.get('content'):
                            content_parts.append(source['content'])
                        if source.get('symptoms'):
                            content_parts.append(f"症状: {source['symptoms']}")
                        if source.get('diagnosis'):
                            content_parts.append(f"诊断: {source['diagnosis']}")
                        if source.get('treatment'):
                            content_parts.append(f"治疗: {source['treatment']}")
                        content = " | ".join(content_parts) if content_parts else "无内容"

                        import math
                        normalized_score = 1 / (1 + math.exp(-score / 5))

                        result = {
                            'content': content,
                            'title': source.get('title', f"病历_{source.get('id', 'unknown')}"),
                            'source': 'Elasticsearch',
                            'category': 'medical_record',
                            'similarity': normalized_score,
                            'metadata': {
                                'department': source.get('department', ''),
                                'visit_date': source.get('visit_date', ''),
                                'es_score': score,
                                'es_index': hit.get('_index', 'unknown')
                            }
                        }
                        results.append(result)

                        logger.info(f"ES结果 {i+1}:")
                        logger.info(f"  - ES原始分数: {score:.4f}")
                        logger.info(f"  - 归一化相似度: {normalized_score:.4f}")
                        logger.info(f"  - 标题: {result['title']}")
                        logger.info(f"  - 索引: {hit.get('_index', 'unknown')}")
                        logger.info(f"  - 科室: {source.get('department', 'N/A')}")
                        logger.info(f"  - 就诊日期: {source.get('visit_date', 'N/A')}")
                        logger.info(f"  - 内容长度: {len(content)} 字符")
                        logger.info(f"  - 内容预览: {content[:100]}...")
                        logger.info("  ---")

                    # 已拿到该索引的结果即可返回（避免跨索引重复）
                    break
                except Exception as e:
                    logger.warning(f"ES 索引 {index} 查询失败: {e}")
                    continue

            if not results:
                logger.info("ES 中没有找到相关文档")

            logger.info(f"=== ES 检索完成: {len(results)} 个文档 ===")
            return results[:top_k]

        except Exception as e:
            logger.error(f"ES 检索失败: {e}")
            return []
    
    def _retrieve_from_vectorization_service(self, query_text: str, top_k: int) -> List[Dict[str, Any]]:
        """
        通过ES和ChromaDB进行检索
        
        Args:
            query_text: 查询文本
            top_k: 返回文档数量
            
        Returns:
            检索结果列表
        """
        try:
            logger.info(f"开始检索: '{query_text}', top_k={top_k}")
            logger.info(f"ChromaDB状态: {'已连接' if self.multimodal_collection is not None else '未连接'}")
            logger.info(f"ES状态: {'已连接' if self.es_client is not None else '未连接'}")
            
            results = []
            
            # 1. 尝试从向量化服务检索
            try:
                logger.info("开始向量化服务检索...")
                
                # 通过HTTP API调用向量化服务
                import requests
                
                # 调用向量化服务的检索API
                api_url = "http://localhost:8001/api/v1/retrieve"
            payload = {
                "query": query_text,
                    "top_k": top_k,
                    "retrieval_type": "text"
                }
                
                response = requests.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                    api_result = response.json()
                    if api_result.get('success') and api_result.get('data', {}).get('results'):
                        search_results = api_result['data']['results']
                        
                        logger.info(f"向量化服务API检索到 {len(search_results)} 个文档")
                        
                        # 处理检索结果
                        logger.info("=== 向量化检索结果详情 ===")
                        for i, result in enumerate(search_results):
                            # ChromaDB返回的是L2距离，需要转换为相似度分数
                            l2_distance = result.get('similarity_score', 0)
                            # 将L2距离转换为相似度分数 (0-1之间)
                            # 对于单位向量，最大L2距离是sqrt(2) ≈ 1.414
                            # 使用公式: similarity = 1 - (distance / sqrt(2))
                            import math
                            similarity = max(0, 1 - (l2_distance / math.sqrt(2)))
                            
                            document = {
                                'content': result.get('content', ''),
                                'title': f"向量化文档_{i+1}",
                                'source': 'VectorizationService',
                                'category': 'medical',
                                'similarity': similarity,
                                'metadata': result.get('metadata', {}),
                                'l2_distance': l2_distance  # 保留原始距离用于调试
                            }
                            results.append(document)
                            
                            # 详细记录每个向量化检索结果
                            logger.info(f"向量化结果 {i+1}:")
                            logger.info(f"  - L2距离: {l2_distance:.4f}")
                            logger.info(f"  - 相似度: {similarity:.4f}")
                            logger.info(f"  - 标题: {document['title']}")
                            logger.info(f"  - 内容长度: {len(document['content'])} 字符")
                            logger.info(f"  - 内容预览: {document['content'][:100]}...")
                            logger.info(f"  - 元数据: {document['metadata']}")
                            logger.info("  ---")
                        
                        logger.info(f"向量化服务检索完成，共找到 {len(results)} 个文档")
                else:
                        logger.warning("向量化服务API返回失败")
            else:
                    logger.warning(f"向量化服务API调用失败: {response.status_code}")
                
        except Exception as e:
                logger.warning(f"向量化服务检索失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 2. 尝试从ES检索（fallback机制）
            if len(results) < top_k:
                try:
                    logger.info(f"开始ES检索fallback，当前已有{len(results)}个结果，需要{top_k - len(results)}个")
                    
                    # 检查ES连接
                    if self.es_client is None:
                        logger.warning("ES客户端未初始化，跳过ES检索")
                    elif not self.es_client.ping():
                        logger.warning("ES连接失败，跳过ES检索")
                    else:
                        # 构建ES查询
                        es_query = {
                            "query": {
                                "bool": {
                                    "should": [
                                        {
                                            "multi_match": {
                                                "query": query_text,
                                                "fields": ["content^2", "symptoms^1.5", "diagnosis^1.5", "treatment^1.2", "title^1.8"],
                                                "type": "best_fields",
                                                "fuzziness": "AUTO"
                                            }
                                        },
                                        {
                                            "match_phrase": {
                                                "content": {
                                                    "query": query_text,
                                                    "boost": 2.0
                                                }
                                            }
                                        }
                                    ],
                                    "minimum_should_match": 1
                                }
                            },
                            "size": top_k - len(results),
                            "_source": ["id", "title", "content", "symptoms", "diagnosis", "treatment", "department", "visit_date"],
                            "sort": [
                                {"_score": {"order": "desc"}},
                                {"visit_date": {"order": "desc"}}
                            ]
                        }
                        
                        logger.info(f"ES查询条件: {es_query}")
                        
                        # 尝试多个索引
                        es_indices = ["medical_records", "medical_records_enhanced"]
                        es_results = []
                        
                        for index in es_indices:
                            try:
                                if self.es_client.indices.exists(index=index):
                                    es_response = self.es_client.search(
                                        index=index,
                                        body=es_query
                                    )
                                    
                                    logger.info(f"ES索引 {index} 查询结果: 找到{es_response['hits']['total']['value']}个文档")
                                    
                                    if es_response['hits']['hits']:
                                        es_results.extend(es_response['hits']['hits'])
                                        break  # 找到结果就停止
                                else:
                                    logger.info(f"ES索引 {index} 不存在")
                            except Exception as e:
                                logger.warning(f"ES索引 {index} 查询失败: {e}")
                                continue
                        
                        # 处理ES检索结果
                        if es_results:
                            logger.info("=== ES检索结果详情 ===")
                            for i, hit in enumerate(es_results):
                                source = hit['_source']
                                score = hit['_score']
                                
                                # 构建内容
                                content_parts = []
                                if source.get('content'):
                                    content_parts.append(source['content'])
                                if source.get('symptoms'):
                                    content_parts.append(f"症状: {source['symptoms']}")
                                if source.get('diagnosis'):
                                    content_parts.append(f"诊断: {source['diagnosis']}")
                                if source.get('treatment'):
                                    content_parts.append(f"治疗: {source['treatment']}")
                                
                                content = " | ".join(content_parts) if content_parts else "无内容"
                                
                                # 将ES分数转换为0-1相似度
                                # ES分数通常范围较大，使用sigmoid函数进行归一化
                                import math
                                normalized_score = 1 / (1 + math.exp(-score / 5))  # 使用sigmoid归一化
                                
                                result = {
                                    'content': content,
                                    'title': source.get('title', f"病历_{source.get('id', 'unknown')}"),
                                    'source': 'Elasticsearch',
                                    'category': 'medical_record',
                                    'similarity': normalized_score,
                                    'metadata': {
                                        'department': source.get('department', ''),
                                        'visit_date': source.get('visit_date', ''),
                                        'es_score': score,
                                        'es_index': hit.get('_index', 'unknown')
                                    }
                                }
                                results.append(result)
                                
                                # 详细记录每个ES检索结果
                                logger.info(f"ES结果 {i+1}:")
                                logger.info(f"  - ES原始分数: {score:.4f}")
                                logger.info(f"  - 归一化相似度: {normalized_score:.4f}")
                                logger.info(f"  - 标题: {result['title']}")
                                logger.info(f"  - 索引: {hit.get('_index', 'unknown')}")
                                logger.info(f"  - 科室: {source.get('department', 'N/A')}")
                                logger.info(f"  - 就诊日期: {source.get('visit_date', 'N/A')}")
                                logger.info(f"  - 内容长度: {len(content)} 字符")
                                logger.info(f"  - 内容预览: {content[:100]}...")
                                logger.info("  ---")
                            
                            logger.info(f"ES检索完成，共找到 {len(es_results)} 个文档")
                        else:
                            logger.info("ES中没有找到相关文档")
                        
                except Exception as e:
                    logger.warning(f"ES检索fallback失败: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 3. 按相似度排序
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
            # 4. 限制返回数量
            final_results = results[:top_k]
            
            logger.info(f"检索完成，共找到 {len(final_results)} 个文档")
            for i, result in enumerate(final_results):
                logger.info(f"结果 {i+1}: 相似度={result['similarity']:.3f}, 来源={result['source']}, 标题='{result['title']}'")
            
            return final_results
            
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []
    
    def _semantic_retrieval(self, query_vector: np.ndarray, top_k: int, query_text: str = None) -> List[Dict[str, Any]]:
        """
        语义检索策略
        
        Args:
            query_vector: 查询向量
            top_k: 返回文档数量
            query_text: 查询文本（用于ChromaDB文本搜索）
            
        Returns:
            检索结果列表
        """
        try:
            # 使用新的检索方法
            return self._retrieve_from_vectorization_service(query_text or "", top_k)
            
        except Exception as e:
            logger.error(f"Error in semantic retrieval: {e}")
            return []
    
    def _hybrid_retrieval(self, query_vector: np.ndarray, top_k: int, query_text: str = None) -> List[Dict[str, Any]]:
        """
        混合检索策略（语义 + 关键词 + ES）
        
        Args:
            query_vector: 查询向量
            top_k: 返回文档数量
            query_text: 查询文本
            
        Returns:
            检索结果列表
        """
        try:
            # 生成唯一的混合检索ID
            import time
            hybrid_id = f"hybrid_{int(time.time() * 1000)}"
            
            logger.info(f"🔄 [{hybrid_id}] 开始混合检索")
            logger.info(f"📊 [{hybrid_id}] 检索参数: query='{query_text}', top_k={top_k}")
            logger.info(f"⚙️ [{hybrid_id}] 混合检索配置: ES权重={self.config.get('es_weight', 0.6)}, 向量权重={self.config.get('vector_weight', 0.4)}")
            
            # 1. 语义检索（向量化服务）
            logger.info(f"🔍 [{hybrid_id}] === 步骤1: 语义检索 ===")
            max_vector_results = self.config.get('max_vector_results', 3)
            semantic_results = self._semantic_retrieval(query_vector, max_vector_results, query_text)
            logger.info(f"✅ [{hybrid_id}] 语义检索完成: {len(semantic_results)} 个文档")
            
            # 详细记录语义检索结果
            for i, result in enumerate(semantic_results):
                logger.info(f"📄 [{hybrid_id}] 语义结果 {i+1}:")
                logger.info(f"   - 相似度: {result.get('similarity', 0):.4f}")
                logger.info(f"   - 来源: {result.get('source', 'N/A')}")
                logger.info(f"   - 标题: {result.get('title', 'N/A')}")
                logger.info(f"   - 内容预览: {result.get('content', '')[:50]}...")
            
            logger.info(f"🔍 [{hybrid_id}] === 语义检索完成 ===")
            
            # 2. 关键词检索（ES）
            logger.info(f"🔍 [{hybrid_id}] === 步骤2: 关键词检索 ===")
            keyword_results = []
            seen_keyword_ids = set()
            seen_keyword_hashes = set()
            if self.es_client and self.es_client.ping():
                try:
                    logger.info(f"🔍 [{hybrid_id}] 开始关键词检索...")
                    
                    # 构建关键词查询
                    keywords = query_text.split() if query_text else []
                    logger.info(f"📝 [{hybrid_id}] 提取关键词: {keywords}")
                    
                    if keywords:
                        keyword_text = " ".join(keywords)
                        logger.info(f"📝 [{hybrid_id}] 关键词查询文本: '{keyword_text}'")
                        keyword_query = {
                        "query": {
                            "bool": {
                                "should": [
                                    {
                                        "match": {
                                            "content": {
                                                "query": keyword_text,
                                                "boost": 2.0
                                            }
                                        }
                                    },
                                    {
                                        "match": {
                                            "symptoms": {
                                                "query": keyword_text,
                                                "boost": 1.8
                                            }
                                        }
                                    },
                                    {
                                        "match": {
                                            "diagnosis": {
                                                "query": keyword_text,
                                                "boost": 1.5
                                            }
                                        }
                                    },
                                    {
                                        "match": {
                                            "treatment": {
                                                "query": keyword_text,
                                                "boost": 1.2
                                            }
                                        }
                                    },
                                    {
                                        "match": {
                                            "title": {
                                                "query": keyword_text,
                                                "boost": 1.0
                                            }
                                        }
                                    }
                                ],
                                "minimum_should_match": 1
                            }
                        },
                        "size": self.config.get('max_es_results', 3) * 3,  # 为时间权重排序预留空间
                        "_source": ["id", "title", "content", "symptoms", "diagnosis", "treatment", "department", "visit_date"],
                        "sort": [
                            {"_score": {"order": "desc"}},
                            {"visit_date": {"order": "desc"}}
                        ]
                    }
                    
                    logger.info(f"🔍 [{hybrid_id}] ES查询构建完成:")
                    logger.info(f"   - 查询字段: content(2.0), symptoms(1.8), diagnosis(1.5), treatment(1.2), title(1.0)")
                    logger.info(f"   - 返回数量: {self.config.get('max_es_results', 3) * 3}")
                    logger.info(f"   - 排序方式: _score desc, visit_date desc")
                    
                    # 尝试多个索引
                    es_indices = ["medical_records", "medical_records_enhanced"]
                    logger.info(f"🔍 [{hybrid_id}] 开始尝试ES索引查询: {es_indices}")
                    
                    for index in es_indices:
                        try:
                            logger.info(f"🔍 [{hybrid_id}] 检查索引: {index}")
                            if self.es_client.indices.exists(index=index):
                                logger.info(f"✅ [{hybrid_id}] 索引存在: {index}")
                                logger.info(f"🔍 [{hybrid_id}] 执行ES查询...")
                                
                                es_response = self.es_client.search(
                                    index=index,
                                    body=keyword_query
                                )
                                
                                logger.info(f"📊 [{hybrid_id}] ES查询响应: 总命中数={es_response['hits']['total']['value']}, 最大分数={es_response['hits']['max_score']}")
                                
                                if es_response['hits']['hits']:
                                    logger.info(f"📄 [{hybrid_id}] 处理ES命中结果: {len(es_response['hits']['hits'])} 个文档")
                                    
                                    for i, hit in enumerate(es_response['hits']['hits']):
                                        source = hit['_source']
                                        score = hit['_score']
                                        
                                        logger.info(f"📄 [{hybrid_id}] ES结果 {i+1}:")
                                        logger.info(f"   - ES分数: {score:.4f}")
                                        logger.info(f"   - 文档ID: {source.get('id', 'N/A')}")
                                        logger.info(f"   - 标题: {source.get('title', 'N/A')}")
                                        
                                        # 构建内容
                                        content_parts = []
                                        if source.get('content'):
                                            content_parts.append(source['content'])
                                        if source.get('symptoms'):
                                            content_parts.append(f"症状: {source['symptoms']}")
                                        if source.get('diagnosis'):
                                            content_parts.append(f"诊断: {source['diagnosis']}")
                                        if source.get('treatment'):
                                            content_parts.append(f"治疗: {source['treatment']}")
                                        
                                        content = " | ".join(content_parts) if content_parts else "无内容"
                                        
                                        # 计算关键词匹配度
                                        keyword_matches = 0
                                        content_lower = content.lower()
                                        for keyword in keywords:
                                            if keyword.lower() in content_lower:
                                                keyword_matches += 1
                                        
                                        keyword_similarity = keyword_matches / len(keywords) if keywords else 0
                                        
                                        logger.info(f"   - 关键词匹配: {keyword_matches}/{len(keywords)}")
                                        logger.info(f"   - 关键词相似度: {keyword_similarity:.4f}")
                                        logger.info(f"   - 科室: {source.get('department', 'N/A')}")
                                        logger.info(f"   - 就诊日期: {source.get('visit_date', 'N/A')}")
                                        logger.info(f"   - 内容预览: {content[:100]}...")
                                        
                                        # 使用ES分数进行归一化作为相似度，并进行去重
                                        import math
                                        normalized_score = 1 / (1 + math.exp(-score / 5))
                                        
                                        # 去重：按文档ID和内容指纹
                                        result_id = hit.get('_id') or source.get('id') or f"{hit.get('_index', 'unknown')}_{i}"
                                        content_key = f"{source.get('title', '')[:50]}|{content[:200]}|{hit.get('_index', 'unknown')}"
                                        if result_id in seen_keyword_ids:
                                            logger.info(f"🔁 [{hybrid_id}] 跳过重复ES结果（按ID）：{result_id}")
                                            continue
                                        if content_key in seen_keyword_hashes:
                                            logger.info(f"🔁 [{hybrid_id}] 跳过重复ES结果（按内容）：{source.get('title', 'N/A')}")
                                            continue
                                        seen_keyword_ids.add(result_id)
                                        seen_keyword_hashes.add(content_key)

                                        result = {
                                            'id': result_id,
                                            'content': content,
                                            'title': source.get('title', f"病历_{source.get('id', 'unknown')}") ,
                                            'source': 'Elasticsearch_Keywords',
                                            'category': 'medical_record',
                                            'similarity': normalized_score,
                                            'metadata': {
                                                'department': source.get('department', ''),
                                                'visit_date': source.get('visit_date', ''),
                                                'es_score': score,
                                                'keyword_matches': keyword_matches,
                                                'es_index': hit.get('_index', 'unknown')
                                            }
                                        }
                                        keyword_results.append(result)
                                        
                                        logger.info(f"✅ [{hybrid_id}] 添加ES结果 {len(keyword_results)}: {result['title']}")
                                    
                                    logger.info(f"✅ [{hybrid_id}] ES索引 {index} 检索完成: {len(es_response['hits']['hits'])} 个文档")
                                    break  # 找到结果就停止
                                else:
                                    logger.info(f"⚠️ [{hybrid_id}] ES索引 {index} 无命中结果")
                            else:
                                logger.info(f"⚠️ [{hybrid_id}] ES索引不存在: {index}")
        except Exception as e:
                            logger.warning(f"❌ [{hybrid_id}] ES索引 {index} 查询失败: {e}")
                            continue
                    
                except Exception as e:
                    logger.warning(f"❌ [{hybrid_id}] 关键词检索失败: {e}")
            
            logger.info(f"✅ [{hybrid_id}] === 关键词检索完成 ===")
            logger.info(f"📊 [{hybrid_id}] 关键词检索结果: {len(keyword_results)} 个文档")
            
            # 3. 使用RRF融合算法
            logger.info(f"🔄 [{hybrid_id}] === 步骤3: RRF融合算法 ===")
            hybrid_core = UserCentricHybrid(es_weight=0.6, rrf_k=60)
            fused_results = hybrid_core.rrf_fuse(keyword_results, semantic_results)
            
            logger.info(f"✅ [{hybrid_id}] RRF融合完成: {len(fused_results)} 个文档")
            
            # 4. 限制返回数量并添加调试信息
            final_results = fused_results[:top_k]
            
            logger.info(f"🎯 [{hybrid_id}] === 混合检索最终结果 ===")
            logger.info(f"📈 [{hybrid_id}] 混合检索统计: ES{len(keyword_results)} + 向量{len(semantic_results)} = RRF融合{len(fused_results)} -> 最终{len(final_results)}")
            
            for i, result in enumerate(final_results):
                logger.info(f"🏆 [{hybrid_id}] 最终结果 {i+1}:")
                logger.info(f"   - RRF分数: {result.get('_hybrid_score', 0):.6f}")
                logger.info(f"   - 原始相似度: {result.get('similarity', 0):.4f}")
                logger.info(f"   - 来源: {result.get('source', 'N/A')}")
                logger.info(f"   - 标题: {result.get('title', 'N/A')}")
                logger.info(f"   - 内容预览: {result.get('content', '')[:100]}...")
                logger.info("   ---")
            
            logger.info(f"🎉 [{hybrid_id}] 混合检索全部完成")
            return final_results
            
        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _rerank_retrieval(self, query_vector: np.ndarray, top_k: int, query_text: str = None) -> List[Dict[str, Any]]:
        """
        重排序检索策略
        
        Args:
            query_vector: 查询向量
            top_k: 返回文档数量
            query_text: 查询文本
            
        Returns:
            检索结果列表
        """
        try:
            # 先获取更多候选文档
            candidates = self._semantic_retrieval(query_vector, top_k * 3, query_text)
            
            # 这里可以添加重排序逻辑
            # 目前简单返回前top_k个结果
            return candidates[:top_k]
            
        except Exception as e:
            logger.error(f"Error in rerank retrieval: {e}")
            return []
    
    def search_by_keywords(self, keywords: List[str], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        基于关键词搜索文档
        
        Args:
            keywords: 关键词列表
            top_k: 返回文档数量
            
        Returns:
            搜索结果列表
        """
        try:
            results = []
            keyword_set = set(keywords)
            
            for doc_id, doc in self.metadata_db.items():
                # 简单的关键词匹配
                content = doc.get('content', '').lower()
                title = doc.get('title', '').lower()
                
                # 计算匹配的关键词数量
                matches = sum(1 for keyword in keyword_set if keyword.lower() in content or keyword.lower() in title)
                
                if matches > 0:
                    doc_copy = doc.copy()
                    doc_copy['keyword_matches'] = matches
                    doc_copy['similarity'] = matches / len(keyword_set)
                    results.append(doc_copy)
            
            # 按匹配度排序
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            文档信息
        """
        return self.metadata_db.get(doc_id)
    
    def get_documents_by_category(self, category: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        根据类别获取文档
        
        Args:
            category: 文档类别
            top_k: 返回文档数量
            
        Returns:
            文档列表
        """
        try:
            results = []
            for doc in self.metadata_db.values():
                if doc.get('category', '').lower() == category.lower():
                    results.append(doc)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error getting documents by category: {e}")
            return []
    
    def get_documents_by_source(self, source: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        根据来源获取文档
        
        Args:
            source: 文档来源
            top_k: 返回文档数量
            
        Returns:
            文档列表
        """
        try:
            results = []
            for doc in self.metadata_db.values():
                if doc.get('source', '').lower() == source.lower():
                    results.append(doc)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error getting documents by source: {e}")
            return []
    
    def update_document(self, doc_id: int, updates: Dict[str, Any]):
        """
        更新文档信息
        
        Args:
            doc_id: 文档ID
            updates: 更新内容
        """
        try:
            if doc_id in self.metadata_db:
                self.metadata_db[doc_id].update(updates)
                logger.info(f"Updated document {doc_id}")
            else:
                logger.warning(f"Document {doc_id} not found")
                
        except Exception as e:
            logger.error(f"Error updating document: {e}")
    
    def delete_document(self, doc_id: int):
        """
        删除文档
        
        Args:
            doc_id: 文档ID
        """
        try:
            if doc_id in self.metadata_db:
                del self.metadata_db[doc_id]
                logger.info(f"Deleted document {doc_id}")
            else:
                logger.warning(f"Document {doc_id} not found")
                
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取检索系统统计信息
        
        Returns:
            统计信息
        """
        try:
            # 知识检索服务不再管理向量数据库，只返回检索相关配置
            return {
                'total_documents': 0,  # 不再管理文档数量
                'vector_database_size': 0,  # 不再管理向量数据库
                'categories': [],  # 不再管理分类
                'sources': [],  # 不再管理来源
                'retrieval_strategy': self.current_strategy,
                'similarity_threshold': self.similarity_threshold,
                'note': '知识检索服务不再管理向量数据库，数据通过向量化服务获取'
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def save_metadata(self, metadata_path: str):
        """
        保存元数据到文件
        
        Args:
            metadata_path: 元数据文件路径
        """
        try:
            os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata_db, f, ensure_ascii=False, indent=2)
            logger.info(f"Metadata saved to {metadata_path}")
            
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            raise
    
    def load_metadata(self, metadata_path: str):
        """
        从文件加载元数据
        
        Args:
            metadata_path: 元数据文件路径
        """
        try:
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata_db = json.load(f)
                logger.info(f"Metadata loaded from {metadata_path}")
            else:
                logger.warning(f"Metadata file not found: {metadata_path}")
                
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            raise
    
    def clear_all(self):
        """清空所有数据"""
        try:
            # 清空向量数据库
            if hasattr(self.vector_db, '_collection') and self.vector_db._collection:
                results = self.vector_db._collection.get()
                if results and 'ids' in results and results['ids']:
                    self.vector_db._collection.delete(ids=results['ids'])
                    logger.info(f"Deleted {len(results['ids'])} documents from vector database")
                else:
                    logger.info("No documents found to delete in vector database")
            
            # 清空元数据
            self.metadata_db.clear()
            logger.info("All data cleared")
        except Exception as e:
            logger.error(f"Error clearing data: {e}")
            # 不抛出异常，避免影响服务关闭


class RetrievalServiceFactory:
    """检索服务工厂类"""
    
    @staticmethod
    def create_retrieval_service(config_path: str = None) -> RetrievalService:
        """
        创建检索服务实例
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            检索服务实例
        """
        # 默认配置
        default_config = {
            'vector_dim': 512,  # 修复向量维度，匹配ChromaDB中的实际维度
            'max_results': 20,
            'similarity_threshold': 0.5,  # 调整阈值为0.5，符合优先级需求
            'retrieval_strategy': 'semantic',
            'vector_db_path': '../../../datas/chroma_db',  # 添加ChromaDB路径
            'collection_name': 'medical_multimodal_vectors',  # 添加集合名称
            'es_weight': 0.6,
            'vector_weight': 0.4,
            'rrf_k': 60,
            'max_es_results': 3,
            'max_vector_results': 3
        }
        
        # 如果提供了配置文件，则加载配置
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                logger.info(f"从配置文件加载配置: {config_path}")
            except Exception as e:
                logger.warning(f"Error loading config file: {e}, using default config")
        
        logger.info(f"最终检索服务配置: {default_config}")
        return RetrievalService(default_config)


if __name__ == "__main__":
    # 测试检索服务
    config = {
        'vector_dim': 384,
        'max_results': 10,
        'similarity_threshold': 0.3,  # 调整阈值适应L2距离转换后的相似度分数
        'retrieval_strategy': 'semantic'
    }
    
    retrieval_service = RetrievalService(config)
    
    # 模拟添加文档
    test_documents = [
        {
            'content': '胸痛是心肌梗死的常见症状，通常表现为胸骨后压榨性疼痛',
            'title': '心肌梗死症状',
            'category': '心血管疾病',
            'source': '医学教科书'
        },
        {
            'content': '呼吸困难可能由多种原因引起，包括肺部疾病和心脏疾病',
            'title': '呼吸困难原因',
            'category': '呼吸系统疾病',
            'source': '临床指南'
        },
        {
            'content': '发热是感染性疾病的主要症状之一，需要及时治疗',
            'title': '发热症状',
            'category': '感染性疾病',
            'source': '医学期刊'
        }
    ]
    
    # 模拟向量（实际使用中应该通过向量化服务生成）
    test_vectors = np.random.rand(len(test_documents), 384).astype('float32')
    
    # 添加文档
    retrieval_service.add_documents(test_vectors, test_documents)
    
    # 测试检索
    query_vector = np.random.rand(384).astype('float32')
    results = retrieval_service.retrieve_documents(query_vector, top_k=2)
    
    print(f"Retrieved {len(results)} documents")
    for result in results:
        print(f"Title: {result['title']}, Similarity: {result['similarity']:.3f}")
    
    # 测试关键词搜索
    keyword_results = retrieval_service.search_by_keywords(['胸痛', '心肌梗死'], top_k=2)
    print(f"\nKeyword search results: {len(keyword_results)}")
    
    # 获取统计信息
    stats = retrieval_service.get_statistics()
    print(f"\nStatistics: {stats}")
