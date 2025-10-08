from typing import List, Dict, Any, Optional, Tuple
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta

from pathlib import Path
import sys

current_file = Path(__file__)
project_root = current_file.parent.parent.parent  # codes
sys.path.insert(0, str(project_root))

from common.log_config import setup_service_logging

logger = setup_service_logging("retrieval_service")


class EnhancedESMapping:
    def __init__(self, es_client: Elasticsearch):
        self.es = es_client
        self.index_name = "medical_records_enhanced"

    def create_enhanced_mapping(self) -> Dict[str, Any]:
        return {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "record_id": {"type": "keyword"},
                    "user_id": {"type": "keyword"},
                    "user_unique_id": {"type": "keyword"},
                    "patient_unique_id": {"type": "keyword"},
                    "patient_name": {"type": "text", "analyzer": "ik_max_word"},
                    "record_type": {"type": "keyword"},
                    "title": {"type": "text", "analyzer": "ik_max_word"},
                    "content": {"type": "text", "analyzer": "ik_max_word"},
                    "department": {"type": "keyword"},
                    "doctor": {"type": "keyword"},
                    "visit_date": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"},
                    "symptoms": {"type": "text", "analyzer": "ik_max_word"},
                    "diagnosis": {"type": "text", "analyzer": "ik_max_word"},
                    "treatment": {"type": "text", "analyzer": "ik_max_word"},
                    "medications": {"type": "text", "analyzer": "ik_max_word"},
                    "notes": {"type": "text", "analyzer": "ik_max_word"},
                    "patient_age": {"type": "integer"},
                    "patient_gender": {"type": "keyword"},
                    "patient_phone": {"type": "keyword"},
                    "patient_id_card": {"type": "keyword"},
                    "medical_history": {"type": "text", "analyzer": "ik_max_word"},
                    "allergies": {"type": "text", "analyzer": "ik_max_word"},
                    "current_medications": {"type": "text", "analyzer": "ik_max_word"},
                    "relationship": {"type": "keyword"},
                    "owner_user_id": {"type": "keyword"},
                    "attachments": {
                        "type": "nested",
                        "properties": {
                            "type": {"type": "keyword"},
                            "filename": {"type": "keyword"},
                            "url": {"type": "keyword"},
                            "size": {"type": "integer"}
                        }
                    },
                    "is_active": {"type": "boolean"},
                    "created_at": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"},
                    "updated_at": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"},
                    "search_content": {
                        "type": "text",
                        "analyzer": "ik_max_word",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "suggest": {"type": "completion"}
                        }
                    }
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "ik_max_word": {"type": "ik_max_word"},
                        "ik_smart": {"type": "ik_smart"}
                    }
                }
            }
        }

    def create_index(self) -> bool:
        try:
            if self.es.indices.exists(index=self.index_name):
                logger.info(f"索引 {self.index_name} 已存在")
                return True
            mapping = self.create_enhanced_mapping()
            self.es.indices.create(index=self.index_name, body=mapping)
            logger.info(f"成功创建索引: {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            return False


class EnhancedESRetrieval:
    def __init__(self, es_client: Elasticsearch):
        self.es = es_client
        self.index_name = "medical_records_enhanced"
        self.mapping = EnhancedESMapping(es_client)

    def calculate_time_weight(self, visit_date: str) -> float:
        """
        根据就诊时间计算权重
        1个月内：权重 × 0.9
        3个月内：权重 × 0.75
        6个月内：权重 × 0.6
        1年以内：权重 × 0.45
        1年以上：权重 × 0.3
        """
        try:
            # 解析日期
            if isinstance(visit_date, str):
                # 尝试多种日期格式
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d']:
                    try:
                        visit_dt = datetime.strptime(visit_date, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    logger.warning(f"无法解析日期格式: {visit_date}")
                    return 0.3  # 默认最低权重
            else:
                visit_dt = visit_date
            
            # 计算时间差
            now = datetime.now()
            days_diff = (now - visit_dt).days
            
            # 应用权重规则
            if days_diff <= 30:      return 0.9
            elif days_diff <= 90:    return 0.75
            elif days_diff <= 180:   return 0.6
            elif days_diff <= 365:   return 0.45
            else:                    return 0.3
            
        except Exception as e:
            logger.error(f"计算时间权重失败: {e}")
            return 0.3  # 默认最低权重

    def search_by_user_and_keywords(
        self,
        user_id: str,
        keywords: List[str],
        patient_unique_ids: Optional[List[str]] = None,
        department: Optional[str] = None,
        date_range: Optional[Tuple[str, str]] = None,
        record_type: Optional[str] = None,
        top_k: int = 3,  # 默认返回3条，符合优先级需求
        apply_time_weight: bool = True,  # 新增参数，控制是否应用时间权重
    ) -> List[Dict[str, Any]]:
        try:
            must_conditions: List[Dict[str, Any]] = []
            must_conditions.append({
                "bool": {"should": [{"term": {"user_id": user_id}}, {"term": {"owner_user_id": user_id}}]}
            })
            if patient_unique_ids:
                must_conditions.append({"terms": {"patient_unique_id": patient_unique_ids}})
            if keywords:
                keyword_text = " ".join(keywords)
                must_conditions.append({
                    "bool": {
                        "should": [
                            {"match": {"content": {"query": keyword_text, "boost": 2.0}}},  # 内容权重最高
                            {"match": {"symptoms": {"query": keyword_text, "boost": 1.8}}},  # 症状权重
                            {"match": {"diagnosis": {"query": keyword_text, "boost": 1.5}}},  # 诊断权重
                            {"match": {"treatment": {"query": keyword_text, "boost": 1.2}}},  # 治疗权重
                            {"match": {"title": {"query": keyword_text, "boost": 1.0}}},
                            {"match": {"search_content": {"query": keyword_text, "boost": 1.0}}},
                        ]
                    }
                })
            if department:
                must_conditions.append({"term": {"department": department}})
            if record_type:
                must_conditions.append({"term": {"record_type": record_type}})
            if date_range:
                start_date, end_date = date_range
                must_conditions.append({
                    "range": {"visit_date": {"gte": start_date, "lte": end_date}}
                })

            query: Dict[str, Any] = {
                "bool": {"must": must_conditions, "filter": [{"term": {"is_active": True}}]}
            }

            # 增加检索数量，为时间权重排序预留空间
            search_size = top_k * 3 if apply_time_weight else top_k

            response = self.es.search(
                index=self.index_name,
                body={
                    "query": query,
                    "size": search_size,
                    "sort": [{"visit_date": {"order": "desc"}}, {"_score": {"order": "desc"}}],
                    "_source": [
                        "id",
                        "record_id",
                        "patient_unique_id",
                        "patient_name",
                        "title",
                        "content",
                        "department",
                        "doctor",
                        "visit_date",
                        "symptoms",
                        "diagnosis",
                        "treatment",
                        "medications",
                    ],
                },
            )

            results: List[Dict[str, Any]] = []
            for i, hit in enumerate(response["hits"]["hits"]):
                result = hit["_source"]
                result["_score"] = hit["_score"]
                result["_rank"] = i + 1
                
                # 应用时间权重
                if apply_time_weight and "visit_date" in result:
                    time_weight = self.calculate_time_weight(result["visit_date"])
                    result["_time_weight"] = time_weight
                    result["_weighted_score"] = result["_score"] * time_weight
                    logger.info(f"记录 {result.get('id', 'N/A')}: 原始分数={result['_score']:.4f}, 时间权重={time_weight:.2f}, 加权分数={result['_weighted_score']:.4f}")
                else:
                    result["_weighted_score"] = result["_score"]
                
                results.append(result)
            
            # 如果应用了时间权重，按加权分数重新排序
            if apply_time_weight:
                results.sort(key=lambda x: x.get("_weighted_score", 0), reverse=True)
                logger.info(f"应用时间权重排序，取前{top_k}条结果")
            
            # 限制返回数量
            final_results = results[:top_k]
            
            logger.info(f"ES检索完成: 用户{user_id}, 关键词{keywords}, 返回{len(final_results)}条结果")
            return final_results
            
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []

    def get_user_patient_records(self, user_id: str, patient_unique_id: str, top_k: int = 20) -> List[Dict[str, Any]]:
        try:
            query = {
                "bool": {
                    "must": [
                        {"term": {"user_id": user_id}},
                        {"term": {"patient_unique_id": patient_unique_id}},
                        {"term": {"is_active": True}},
                    ]
                }
            }
            response = self.es.search(index=self.index_name, body={"query": query, "size": top_k, "sort": [{"visit_date": {"order": "desc"}}]})
            results: List[Dict[str, Any]] = []
            for i, hit in enumerate(response["hits"]["hits"]):
                result = hit["_source"]
                result["_rank"] = i + 1
                results.append(result)
            return results
        except Exception as e:
            logger.error(f"获取就诊人记录失败: {e}")
            return []

    def search_similar_cases(self, user_id: str, symptoms: List[str], department: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        try:
            must_conditions: List[Dict[str, Any]] = [
                {"term": {"user_id": user_id}},
                {"term": {"is_active": True}},
            ]
            if department:
                must_conditions.append({"term": {"department": department}})
            symptom_text = " ".join(symptoms)
            must_conditions.append({
                "bool": {
                    "should": [
                        {"match": {"symptoms": {"query": symptom_text, "boost": 2.0}}},
                        {"match": {"diagnosis": {"query": symptom_text, "boost": 1.5}}},
                        {"match": {"content": {"query": symptom_text, "boost": 1.0}}},
                    ]
                }
            })
            query = {"bool": {"must": must_conditions}}
            response = self.es.search(index=self.index_name, body={"query": query, "size": top_k, "sort": [{"_score": {"order": "desc"}}]})
            results: List[Dict[str, Any]] = []
            for i, hit in enumerate(response["hits"]["hits"]):
                result = hit["_source"]
                result["_score"] = hit["_score"]
                result["_rank"] = i + 1
                results.append(result)
            return results
        except Exception as e:
            logger.error(f"搜索相似病例失败: {e}")
            return []


