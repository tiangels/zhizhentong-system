from typing import List, Dict, Any
from collections import defaultdict

from pathlib import Path
import sys

current_file = Path(__file__)
project_root = current_file.parent.parent.parent  # codes
sys.path.insert(0, str(project_root))

from common.log_config import setup_service_logging

logger = setup_service_logging("retrieval_service")


class UserCentricHybrid:
    def __init__(self, es_weight: float = 0.6, rrf_k: int = 60):
        self.es_weight = es_weight
        self.rrf_k = rrf_k

    def rrf_fuse(self, es_results: List[Dict[str, Any]], vector_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        try:
            # 生成唯一的融合ID
            import time
            fusion_id = f"rrf_{int(time.time() * 1000)}"
            
            logger.info(f"🔄 [{fusion_id}] RRF融合算法开始")
            logger.info(f"📊 [{fusion_id}] 输入参数: ES结果={len(es_results)}个, 向量结果={len(vector_results)}个")
            logger.info(f"⚙️ [{fusion_id}] 融合配置: ES权重={self.es_weight}, RRF_K={self.rrf_k}")
            
            rrf_scores: Dict[str, float] = defaultdict(float)
            
            # ES结果RRF计算
            logger.info(f"🔍 [{fusion_id}] 开始ES结果RRF计算")
            for rank, result in enumerate(es_results):
                # 使用实际的ID字段，如果没有则使用索引
                doc_id = result.get("id") or result.get("_id") or f"es_{rank}"
                rrf = 1.0 / (self.rrf_k + rank)
                base_score = self.es_weight * rrf
                
                # 医疗逻辑权重增强
                medical_boost = self._calculate_medical_weight(result)
                final_score = base_score + medical_boost
                
                rrf_scores[doc_id] += final_score
                
                # 详细记录每个ES结果的处理过程
                logger.info(f"📄 [{fusion_id}] ES结果 {rank+1}:")
                logger.info(f"   - 文档ID: {doc_id}")
                logger.info(f"   - 排名: {rank+1}")
                logger.info(f"   - RRF分数: {rrf:.6f}")
                logger.info(f"   - 基础分数: {base_score:.6f}")
                logger.info(f"   - 医疗权重: {medical_boost:.6f}")
                logger.info(f"   - 最终分数: {final_score:.6f}")
                logger.info(f"   - 标题: {result.get('title', 'N/A')}")
                logger.info(f"   - 来源: {result.get('source', 'N/A')}")
                logger.info(f"   - 内容预览: {result.get('content', '')[:50]}...")
                
                if "_source" not in result:
                    result["_source"] = result.copy()
            
            # 向量结果RRF计算
            logger.info(f"🔍 [{fusion_id}] 开始向量结果RRF计算")
            for rank, result in enumerate(vector_results):
                # 使用实际的ID字段，如果没有则使用索引
                doc_id = result.get("id") or result.get("_id") or f"vector_{rank}"
                rrf = 1.0 / (self.rrf_k + rank)
                base_score = (1 - self.es_weight) * rrf
                
                # 医疗逻辑权重增强
                medical_boost = self._calculate_medical_weight(result)
                final_score = base_score + medical_boost
                
                rrf_scores[doc_id] += final_score
                
                # 详细记录每个向量结果的处理过程
                logger.info(f"📄 [{fusion_id}] 向量结果 {rank+1}:")
                logger.info(f"   - 文档ID: {doc_id}")
                logger.info(f"   - 排名: {rank+1}")
                logger.info(f"   - RRF分数: {rrf:.6f}")
                logger.info(f"   - 基础分数: {base_score:.6f}")
                logger.info(f"   - 医疗权重: {medical_boost:.6f}")
                logger.info(f"   - 最终分数: {final_score:.6f}")
                logger.info(f"   - 相似度: {result.get('similarity', 0):.4f}")
                logger.info(f"   - 标题: {result.get('title', 'N/A')}")
                logger.info(f"   - 来源: {result.get('source', 'N/A')}")
                logger.info(f"   - 内容预览: {result.get('content', '')[:50]}...")
                
                if "_source" not in result:
                    result["_source"] = result.copy()
            
            logger.info(f"📊 [{fusion_id}] RRF分数汇总: {dict(rrf_scores)}")
            
            # 构建融合结果
            logger.info(f"🔧 [{fusion_id}] 开始构建融合结果")
            hybrid: List[Dict[str, Any]] = []
            for doc_id, score in rrf_scores.items():
                original = None
                # 先尝试从ES结果中查找
                for r in es_results:
                    actual_id = r.get("id") or r.get("_id") or f"es_{es_results.index(r)}"
                    if actual_id == doc_id:
                        original = r.copy()
                        break
                # 如果没找到，再从向量结果中查找
                if not original:
                    for r in vector_results:
                        actual_id = r.get("id") or r.get("_id") or f"vector_{vector_results.index(r)}"
                        if actual_id == doc_id:
                            original = r.copy()
                            break
                
                if original:
                    original["_hybrid_score"] = score
                    original["_rrf_score"] = score
                    hybrid.append(original)
                    logger.info(f"✅ [{fusion_id}] 添加融合结果: doc_id={doc_id}, score={score:.6f}")
                else:
                    logger.warning(f"⚠️ [{fusion_id}] 未找到原始结果: doc_id={doc_id}")
                    # 调试信息：显示所有可用的ID
                    es_ids = [r.get("id") or r.get("_id") or f"es_{i}" for i, r in enumerate(es_results)]
                    vector_ids = [r.get("id") or r.get("_id") or f"vector_{i}" for i, r in enumerate(vector_results)]
                    logger.warning(f"🔍 [{fusion_id}] ES结果ID: {es_ids}")
                    logger.warning(f"🔍 [{fusion_id}] 向量结果ID: {vector_ids}")
            
            # 按RRF分数排序
            logger.info(f"📈 [{fusion_id}] 开始按RRF分数排序")
            hybrid.sort(key=lambda x: x.get("_hybrid_score", 0.0), reverse=True)
            
            # 记录最终排序结果
            logger.info(f"🎯 [{fusion_id}] 最终排序结果:")
            for i, result in enumerate(hybrid):
                logger.info(f"   {i+1}. 文档ID: {result.get('id', 'N/A')}")
                logger.info(f"      - RRF分数: {result.get('_hybrid_score', 0):.6f}")
                logger.info(f"      - 标题: {result.get('title', 'N/A')}")
                logger.info(f"      - 来源: {result.get('source', 'N/A')}")
                logger.info(f"      - 内容预览: {result.get('content', '')[:50]}...")
            
            logger.info(f"🎉 [{fusion_id}] RRF融合完成: {len(hybrid)}个结果")
            return hybrid
            
        except Exception as e:
            logger.error(f"RRF融合失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _calculate_medical_weight(self, result: Dict[str, Any]) -> float:
        """
        计算医疗逻辑权重
        基于医疗专业性的额外加分
        """
        try:
            medical_boost = 0.0
            
            # 症状匹配权重
            if result.get('symptoms'):
                medical_boost += 0.05
                logger.debug(f"医疗权重: 症状匹配 +0.05")
            
            # 诊断匹配权重
            if result.get('diagnosis'):
                medical_boost += 0.08
                logger.debug(f"医疗权重: 诊断匹配 +0.08")
            
            # 治疗匹配权重
            if result.get('treatment'):
                medical_boost += 0.06
                logger.debug(f"医疗权重: 治疗匹配 +0.06")
            
            # 科室匹配权重
            if result.get('department'):
                medical_boost += 0.03
                logger.debug(f"医疗权重: 科室匹配 +0.03")
            
            # 医生信息权重
            if result.get('doctor'):
                medical_boost += 0.02
                logger.debug(f"医疗权重: 医生信息 +0.02")
            
            # 就诊时间权重（越新越重要）
            if result.get('visit_date'):
                try:
                    from datetime import datetime
                    visit_date = result['visit_date']
                    if isinstance(visit_date, str):
                        # 尝试解析日期
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d']:
                            try:
                                visit_dt = datetime.strptime(visit_date, fmt)
                                break
                            except ValueError:
                                continue
                        else:
                            logger.debug(f"医疗权重: 时间解析失败，返回当前权重 {medical_boost:.4f}")
                            return medical_boost
                    else:
                        visit_dt = visit_date
                    
                    # 计算时间权重
                    now = datetime.now()
                    days_diff = (now - visit_dt).days
                    
                    if days_diff <= 30:      
                        medical_boost += 0.1
                        logger.debug(f"医疗权重: 30天内 +0.1 (总权重: {medical_boost:.4f})")
                    elif days_diff <= 90:    
                        medical_boost += 0.08
                        logger.debug(f"医疗权重: 90天内 +0.08 (总权重: {medical_boost:.4f})")
                    elif days_diff <= 180:   
                        medical_boost += 0.06
                        logger.debug(f"医疗权重: 180天内 +0.06 (总权重: {medical_boost:.4f})")
                    elif days_diff <= 365:   
                        medical_boost += 0.04
                        logger.debug(f"医疗权重: 365天内 +0.04 (总权重: {medical_boost:.4f})")
                    else:                    
                        medical_boost += 0.02
                        logger.debug(f"医疗权重: 365天以上 +0.02 (总权重: {medical_boost:.4f})")
                    
                except Exception as e:
                    logger.warning(f"计算时间权重失败: {e}")
            
            logger.debug(f"医疗权重计算完成: {medical_boost:.4f}")
            return medical_boost
            
        except Exception as e:
            logger.error(f"计算医疗权重失败: {e}")
            return 0.0


