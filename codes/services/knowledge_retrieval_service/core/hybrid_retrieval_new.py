"""
新的混合检索方法，使用RRF融合算法
"""

def _hybrid_retrieval_new(self, query_vector, top_k: int, query_text: str = None):
    """
    混合检索策略（语义 + 关键词 + ES）使用RRF融合算法
    
    Args:
        query_vector: 查询向量
        top_k: 返回文档数量
        query_text: 查询文本
        
    Returns:
        检索结果列表
    """
    try:
        self.logger.info(f"开始混合检索: '{query_text}', top_k={top_k}")
        
        # 获取配置参数
        es_weight = self.config.get('es_weight', 0.6)
        vector_weight = self.config.get('vector_weight', 0.4)
        rrf_k = self.config.get('rrf_k', 60)
        max_es_results = self.config.get('max_es_results', 3)
        max_vector_results = self.config.get('max_vector_results', 3)
        
        # 1. ES检索用户病例信息（优先级最高）
        self.logger.info("=== 混合检索 - 步骤1: ES检索用户病例信息 ===")
        es_results = []
        if self.es_client and self.es_client.ping():
            try:
                self.logger.info("开始ES关键词检索...")
                
                # 构建关键词查询
                keywords = query_text.split() if query_text else []
                if keywords:
                    keyword_query = {
                        "query": {
                            "bool": {
                                "should": [
                                    {
                                        "terms": {
                                            "content": keywords,
                                            "boost": 2.0
                                        }
                                    },
                                    {
                                        "terms": {
                                            "symptoms": keywords,
                                            "boost": 1.8
                                        }
                                    },
                                    {
                                        "terms": {
                                            "diagnosis": keywords,
                                            "boost": 1.5
                                        }
                                    },
                                    {
                                        "terms": {
                                            "treatment": keywords,
                                            "boost": 1.2
                                        }
                                    }
                                ]
                            }
                        },
                        "size": max_es_results * 3,  # 为时间权重排序预留空间
                        "_source": ["id", "title", "content", "symptoms", "diagnosis", "treatment", "department", "visit_date"],
                        "sort": [
                            {"_score": {"order": "desc"}},
                            {"visit_date": {"order": "desc"}}
                        ]
                    }
                    
                    self.logger.info(f"ES查询条件: {keyword_query}")
                    
                    # 尝试多个索引
                    es_indices = ["medical_records", "medical_records_enhanced"]
                    
                    for index in es_indices:
                        try:
                            if self.es_client.indices.exists(index=index):
                                es_response = self.es_client.search(
                                    index=index,
                                    body=keyword_query
                                )
                                
                                self.logger.info(f"ES索引 {index} 查询结果: 找到{es_response['hits']['total']['value']}个文档")
                                
                                if es_response['hits']['hits']:
                                    for hit in es_response['hits']['hits']:
                                        result = hit["_source"]
                                        result["_score"] = hit["_score"]
                                        result["source"] = "Elasticsearch_Keywords"
                                        result["similarity"] = hit["_score"] / 10.0  # 归一化ES分数
                                        es_results.append(result)
                                    break  # 找到结果就停止
                            else:
                                self.logger.info(f"ES索引 {index} 不存在")
                        except Exception as e:
                            self.logger.warning(f"ES索引 {index} 查询失败: {e}")
                            continue
                
            except Exception as e:
                self.logger.warning(f"关键词检索失败: {e}")
        
        self.logger.info(f"ES检索结果: {len(es_results)} 个文档")
        
        # 2. 向量化医疗知识检索
        self.logger.info("=== 混合检索 - 步骤2: 向量化医疗知识检索 ===")
        vector_results = self._semantic_retrieval(query_vector, max_vector_results, query_text)
        self.logger.info(f"向量检索结果: {len(vector_results)} 个文档")
        
        # 3. 使用RRF融合算法
        self.logger.info("=== 混合检索 - 步骤3: RRF融合算法 ===")
        from services.knowledge_retrieval_service.hybrid.hybrid_core import UserCentricHybrid
        hybrid_core = UserCentricHybrid(es_weight=es_weight, rrf_k=rrf_k)
        fused_results = hybrid_core.rrf_fuse(es_results, vector_results)
        
        self.logger.info(f"RRF融合结果: {len(fused_results)} 个文档")
        
        # 4. 限制返回数量并添加调试信息
        final_results = fused_results[:top_k]
        
        self.logger.info("=== 混合检索最终结果 ===")
        self.logger.info(f"混合检索完成: ES{len(es_results)} + 向量{len(vector_results)} = RRF融合{len(fused_results)} -> 最终{len(final_results)}")
        
        for i, result in enumerate(final_results):
            self.logger.info(f"最终结果 {i+1}:")
            self.logger.info(f"  - RRF分数: {result.get('_hybrid_score', 0):.4f}")
            self.logger.info(f"  - 原始相似度: {result.get('similarity', 0):.4f}")
            self.logger.info(f"  - 来源: {result.get('source', 'N/A')}")
            self.logger.info(f"  - 标题: {result.get('title', 'N/A')}")
            self.logger.info(f"  - 内容预览: {result.get('content', '')[:100]}...")
            self.logger.info("  ---")
        
        return final_results
        
    except Exception as e:
        self.logger.error(f"混合检索失败: {e}")
        import traceback
        traceback.print_exc()
        return []
