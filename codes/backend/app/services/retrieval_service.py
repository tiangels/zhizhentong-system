"""
检索服务客户端
用于与知识检索服务通信
"""

import httpx
import logging
from typing import Optional, Dict, Any, List
from ..config.settings import settings

logger = logging.getLogger(__name__)


class RetrievalServiceClient:
    """检索服务客户端"""
    
    def __init__(self):
        self.base_url = settings.RETRIEVAL_SERVICE_URL
        self.timeout = 30.0
    
    async def search_knowledge(
        self,
        query: str,
        top_k: int = 5,
        user_id: Optional[str] = None,
        patient_unique_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        搜索知识库
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            搜索结果
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload: Dict[str, Any] = {"query": query, "top_k": top_k}
                if user_id:
                    payload["user_id"] = user_id
                if patient_unique_ids:
                    payload["patient_unique_ids"] = patient_unique_ids
                response = await client.post(f"{self.base_url}/search", json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            logger.error(f"检索服务请求失败: {e}")
            return {"error": f"检索服务请求失败: {e}", "results": []}
        except httpx.HTTPStatusError as e:
            logger.error(f"检索服务HTTP错误: {e.response.status_code}")
            return {"error": f"检索服务HTTP错误: {e.response.status_code}", "results": []}
        except Exception as e:
            logger.error(f"检索服务未知错误: {e}")
            return {"error": f"检索服务未知错误: {e}", "results": []}
    
    async def get_context(self, query: str, context_type: str = "medical") -> str:
        """
        获取上下文信息
        
        Args:
            query: 查询文本
            context_type: 上下文类型
            
        Returns:
            上下文信息
        """
        try:
            search_result = await self.search_knowledge(query, top_k=3)
            
            if "error" in search_result:
                logger.warning(f"检索服务搜索失败: {search_result['error']}")
                return ""
            
            # 提取搜索结果中的文本内容
            context_parts = []
            for result in search_result.get("results", []):
                if "content" in result:
                    context_parts.append(result["content"])
                elif "text" in result:
                    context_parts.append(result["text"])
            
            context = "\n\n".join(context_parts)
            logger.info(f"获取到上下文信息，长度: {len(context)}")
            return context
            
        except Exception as e:
            logger.error(f"获取上下文失败: {e}")
            return ""
    
    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict] = None,
        top_k: int = 5,
        multimodal_data: Dict[str, Any] = None,
        user_id: Optional[str] = None,
        patient_unique_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        生成回复（非流式）
        
        Args:
            user_message: 用户消息
            conversation_history: 对话历史
            top_k: 检索结果数量
            multimodal_data: 多模态数据
            
        Returns:
            生成的回复结果
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload: Dict[str, Any] = {
                    "question": user_message,
                    "top_k": top_k,
                    "conversation_history": conversation_history or [],
                    "multimodal_data": multimodal_data or {},
                }
                if user_id:
                    payload["user_id"] = user_id
                if patient_unique_ids:
                    payload["patient_unique_ids"] = patient_unique_ids
                response = await client.post(f"{self.base_url}/query", json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            logger.error(f"生成回复请求失败: {e}")
            return {
                "success": False,
                "answer": "抱歉，检索服务暂时不可用。请稍后重试。",
                "error": f"生成回复请求失败: {e}",
                "rag_used": False,
                "retrieved_documents": [],
                "processing_time": 0
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"生成回复HTTP错误: {e.response.status_code}")
            return {
                "success": False,
                "answer": "抱歉，检索服务暂时不可用。请稍后重试。",
                "error": f"生成回复HTTP错误: {e.response.status_code}",
                "rag_used": False,
                "retrieved_documents": [],
                "processing_time": 0
            }
        except Exception as e:
            logger.error(f"生成回复未知错误: {e}")
            return {
                "success": False,
                "answer": "抱歉，检索服务暂时不可用。请稍后重试。",
                "error": f"生成回复未知错误: {e}",
                "rag_used": False,
                "retrieved_documents": [],
                "processing_time": 0
            }

    async def generate_response_stream(self, user_message: str, conversation_history: List[Dict] = None, top_k: int = 5):
        """
        流式生成回复
        
        Args:
            user_message: 用户消息
            conversation_history: 对话历史
            top_k: 检索结果数量
            
        Yields:
            流式响应块
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/query/stream",
                    json={
                        "question": user_message,
                        "top_k": top_k,
                        "conversation_history": conversation_history or []
                    }
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                # 尝试解析JSON
                                import json
                                chunk_data = json.loads(line)
                                yield chunk_data
                            except json.JSONDecodeError:
                                # 如果不是JSON，直接作为文本处理
                                yield {"type": "text", "content": line}
                                
        except httpx.RequestError as e:
            logger.error(f"流式生成请求失败: {e}")
            yield {"type": "error", "message": f"流式生成请求失败: {e}"}
        except httpx.HTTPStatusError as e:
            logger.error(f"流式生成HTTP错误: {e.response.status_code}")
            yield {"type": "error", "message": f"流式生成HTTP错误: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"流式生成未知错误: {e}")
            yield {"type": "error", "message": f"流式生成未知错误: {e}"}

    async def health_check(self) -> bool:
        """
        检查检索服务健康状态
        
        Returns:
            服务是否健康
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"检索服务健康检查失败: {e}")
            return False


# 全局检索服务客户端实例
_retrieval_service_client: Optional[RetrievalServiceClient] = None


def get_retrieval_service() -> RetrievalServiceClient:
    """获取检索服务客户端实例"""
    global _retrieval_service_client
    if _retrieval_service_client is None:
        _retrieval_service_client = RetrievalServiceClient()
    return _retrieval_service_client


async def search_knowledge(query: str, top_k: int = 5) -> Dict[str, Any]:
    """便捷函数：搜索知识库"""
    client = get_retrieval_service()
    return await client.search_knowledge(query, top_k)


async def get_context(query: str, context_type: str = "medical") -> str:
    """便捷函数：获取上下文信息"""
    client = get_retrieval_service()
    return await client.get_context(query, context_type)


async def check_retrieval_service_health() -> bool:
    """便捷函数：检查检索服务健康状态"""
    client = get_retrieval_service()
    return await client.health_check()
