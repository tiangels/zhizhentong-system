"""
智能诊断服务客户端
用于与智能诊断服务通信
"""

import httpx
import logging
from typing import Optional, Dict, Any, List
from ..config.settings import settings

logger = logging.getLogger(__name__)


class DiagnosisServiceClient:
    """智能诊断服务客户端"""
    
    def __init__(self):
        self.base_url = settings.DIAGNOSIS_SERVICE_URL
        self.timeout = 30.0
    
    async def generate_diagnosis(self, query: str, context: str = "", 
                                response_type: str = "diagnosis",
                                enable_summary: bool = True) -> Dict[str, Any]:
        """
        生成诊断建议
        
        Args:
            query: 用户查询
            context: 上下文信息
            response_type: 响应类型
            enable_summary: 是否启用摘要
            
        Returns:
            诊断结果
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/diagnosis/generate",
                    json={
                        "query": query,
                        "context": context,
                        "response_type": response_type,
                        "enable_summary": enable_summary
                    }
                )
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            logger.error(f"智能诊断服务请求失败: {e}")
            return {
                "success": False,
                "query": query,
                "context": context,
                "response_type": response_type,
                "summary": "",
                "diagnosis_response": "抱歉，智能诊断服务暂时不可用。请咨询专业医生。",
                "error": f"智能诊断服务请求失败: {e}"
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"智能诊断服务HTTP错误: {e.response.status_code}")
            return {
                "success": False,
                "query": query,
                "context": context,
                "response_type": response_type,
                "summary": "",
                "diagnosis_response": "抱歉，智能诊断服务暂时不可用。请咨询专业医生。",
                "error": f"智能诊断服务HTTP错误: {e.response.status_code}"
            }
        except Exception as e:
            logger.error(f"智能诊断服务未知错误: {e}")
            return {
                "success": False,
                "query": query,
                "context": context,
                "response_type": response_type,
                "summary": "",
                "diagnosis_response": "抱歉，智能诊断服务暂时不可用。请咨询专业医生。",
                "error": f"智能诊断服务未知错误: {e}"
            }
    
    async def generate_diagnosis_stream(self, query: str, context: str = "", 
                                       response_type: str = "diagnosis",
                                       enable_summary: bool = True):
        """
        流式生成诊断建议
        
        Args:
            query: 用户查询
            context: 上下文信息
            response_type: 响应类型
            enable_summary: 是否启用摘要
            
        Yields:
            流式响应块
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/diagnosis/stream",
                    json={
                        "query": query,
                        "context": context,
                        "response_type": response_type,
                        "enable_summary": enable_summary
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
            logger.error(f"流式诊断请求失败: {e}")
            yield {"type": "error", "message": f"流式诊断请求失败: {e}"}
        except httpx.HTTPStatusError as e:
            logger.error(f"流式诊断HTTP错误: {e.response.status_code}")
            yield {"type": "error", "message": f"流式诊断HTTP错误: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"流式诊断未知错误: {e}")
            yield {"type": "error", "message": f"流式诊断未知错误: {e}"}

    async def health_check(self) -> bool:
        """
        检查智能诊断服务健康状态
        
        Returns:
            服务是否健康
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/diagnosis/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"智能诊断服务健康检查失败: {e}")
            return False


# 全局智能诊断服务客户端实例
_diagnosis_service_client: Optional[DiagnosisServiceClient] = None


def get_diagnosis_service() -> DiagnosisServiceClient:
    """获取智能诊断服务客户端实例"""
    global _diagnosis_service_client
    if _diagnosis_service_client is None:
        _diagnosis_service_client = DiagnosisServiceClient()
    return _diagnosis_service_client


async def generate_diagnosis(query: str, context: str = "", 
                           response_type: str = "diagnosis",
                           enable_summary: bool = True) -> Dict[str, Any]:
    """便捷函数：生成诊断建议"""
    client = get_diagnosis_service()
    return await client.generate_diagnosis(query, context, response_type, enable_summary)


async def check_diagnosis_service_health() -> bool:
    """便捷函数：检查智能诊断服务健康状态"""
    client = get_diagnosis_service()
    return await client.health_check()
