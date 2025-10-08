#!/usr/bin/env python3
"""
智诊通系统监控脚本
检查所有服务的状态和健康情况
"""

import sys
import os
import requests
import json
import time
from datetime import datetime
from pathlib import Path
import logging

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "codes" / "common"))

from log_config import setup_service_logging
logger = setup_service_logging("system_monitor", show_config_logs=True)

class SystemMonitor:
    """系统监控器"""
    
    def __init__(self):
        """初始化系统监控器"""
        self.services = {
            "embedding_service": {
                "url": "http://localhost:8001",
                "health_endpoint": "/health",
                "status": "unknown"
            },
            "retrieval_service": {
                "url": "http://localhost:8002", 
                "health_endpoint": "/health",
                "status": "unknown"
            },
            "backend_service": {
                "url": "http://localhost:8000",
                "health_endpoint": "/health", 
                "status": "unknown"
            }
        }
        
        # 数据库路径
        self.chroma_db_path = project_root / "datas" / "chroma_db"
        self.es_status = "unknown"
        
    def check_service_health(self, service_name: str, service_info: dict) -> dict:
        """检查单个服务健康状态"""
        try:
            url = f"{service_info['url']}{service_info['health_endpoint']}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "response_time": response.elapsed.total_seconds(),
                    "data": data
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "status": "offline",
                "error": "Connection refused"
            }
        except requests.exceptions.Timeout:
            return {
                "status": "timeout", 
                "error": "Request timeout"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_chroma_db(self) -> dict:
        """检查ChromaDB状态"""
        try:
            import chromadb
            
            if not self.chroma_db_path.exists():
                return {
                    "status": "not_found",
                    "error": f"Database path does not exist: {self.chroma_db_path}"
                }
            
            # 连接数据库
            client = chromadb.PersistentClient(path=str(self.chroma_db_path))
            collections = client.list_collections()
            
            return {
                "status": "healthy",
                "collections_count": len(collections),
                "collections": [col.name for col in collections],
                "path": str(self.chroma_db_path)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_elasticsearch(self) -> dict:
        """检查Elasticsearch状态"""
        try:
            response = requests.get("http://localhost:9200/_cluster/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "cluster_status": data.get("status", "unknown"),
                    "data": data
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "status": "offline",
                "error": "Connection refused"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_vectorization_functionality(self) -> dict:
        """检查向量化功能"""
        try:
            # 测试文本向量化
            response = requests.post(
                "http://localhost:8001/api/v1/vectorize/text",
                json={
                    "texts": ["测试文本"],
                    "chunk_strategy": "medical_structured"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "text_vectorization": "working",
                    "data": data
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_retrieval_functionality(self) -> dict:
        """检查检索功能"""
        try:
            # 测试文档检索
            response = requests.post(
                "http://localhost:8001/api/v1/retrieve",
                json={
                    "query": "感冒症状",
                    "top_k": 3,
                    "retrieval_type": "text"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results_count = len(data.get("data", {}).get("results", []))
                return {
                    "status": "healthy",
                    "retrieval": "working",
                    "results_count": results_count,
                    "data": data
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def run_full_check(self) -> dict:
        """运行完整系统检查"""
        logger.info("🔍 开始系统健康检查...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "databases": {},
            "functionality": {}
        }
        
        # 检查服务健康状态
        logger.info("📡 检查服务健康状态...")
        for service_name, service_info in self.services.items():
            logger.info(f"  检查 {service_name}...")
            health_result = self.check_service_health(service_name, service_info)
            results["services"][service_name] = health_result
            
            status_emoji = {
                "healthy": "✅",
                "unhealthy": "⚠️",
                "offline": "❌",
                "timeout": "⏰",
                "error": "💥"
            }.get(health_result["status"], "❓")
            
            logger.info(f"    {status_emoji} {service_name}: {health_result['status']}")
            if "error" in health_result:
                logger.info(f"      错误: {health_result['error']}")
        
        # 检查数据库状态
        logger.info("🗄️ 检查数据库状态...")
        
        # ChromaDB
        logger.info("  检查 ChromaDB...")
        chroma_result = self.check_chroma_db()
        results["databases"]["chromadb"] = chroma_result
        
        status_emoji = {
            "healthy": "✅",
            "not_found": "❌",
            "error": "💥"
        }.get(chroma_result["status"], "❓")
        
        logger.info(f"    {status_emoji} ChromaDB: {chroma_result['status']}")
        if chroma_result["status"] == "healthy":
            logger.info(f"      集合数量: {chroma_result['collections_count']}")
            logger.info(f"      集合名称: {', '.join(chroma_result['collections'])}")
        elif "error" in chroma_result:
            logger.info(f"      错误: {chroma_result['error']}")
        
        # Elasticsearch
        logger.info("  检查 Elasticsearch...")
        es_result = self.check_elasticsearch()
        results["databases"]["elasticsearch"] = es_result
        
        status_emoji = {
            "healthy": "✅",
            "unhealthy": "⚠️",
            "offline": "❌",
            "error": "💥"
        }.get(es_result["status"], "❓")
        
        logger.info(f"    {status_emoji} Elasticsearch: {es_result['status']}")
        if es_result["status"] == "healthy":
            logger.info(f"      集群状态: {es_result['cluster_status']}")
        elif "error" in es_result:
            logger.info(f"      错误: {es_result['error']}")
        
        # 检查功能状态
        logger.info("🔧 检查功能状态...")
        
        # 向量化功能
        logger.info("  检查向量化功能...")
        vectorization_result = self.check_vectorization_functionality()
        results["functionality"]["vectorization"] = vectorization_result
        
        status_emoji = {
            "healthy": "✅",
            "unhealthy": "⚠️",
            "error": "💥"
        }.get(vectorization_result["status"], "❓")
        
        logger.info(f"    {status_emoji} 向量化功能: {vectorization_result['status']}")
        if "error" in vectorization_result:
            logger.info(f"      错误: {vectorization_result['error']}")
        
        # 检索功能
        logger.info("  检查检索功能...")
        retrieval_result = self.check_retrieval_functionality()
        results["functionality"]["retrieval"] = retrieval_result
        
        status_emoji = {
            "healthy": "✅",
            "unhealthy": "⚠️",
            "error": "💥"
        }.get(retrieval_result["status"], "❓")
        
        logger.info(f"    {status_emoji} 检索功能: {retrieval_result['status']}")
        if retrieval_result["status"] == "healthy":
            logger.info(f"      检索结果数量: {retrieval_result['results_count']}")
        elif "error" in retrieval_result:
            logger.info(f"      错误: {retrieval_result['error']}")
        
        return results
    
    def print_summary(self, results: dict):
        """打印检查结果摘要"""
        print("\n" + "=" * 80)
        print("📊 智诊通系统健康检查报告")
        print("=" * 80)
        print(f"🕐 检查时间: {results['timestamp']}")
        print()
        
        # 服务状态摘要
        print("📡 服务状态:")
        for service_name, service_result in results["services"].items():
            status_emoji = {
                "healthy": "✅",
                "unhealthy": "⚠️", 
                "offline": "❌",
                "timeout": "⏰",
                "error": "💥"
            }.get(service_result["status"], "❓")
            
            print(f"  {status_emoji} {service_name}: {service_result['status']}")
            if "response_time" in service_result:
                print(f"     响应时间: {service_result['response_time']:.3f}s")
        
        print()
        
        # 数据库状态摘要
        print("🗄️ 数据库状态:")
        for db_name, db_result in results["databases"].items():
            status_emoji = {
                "healthy": "✅",
                "unhealthy": "⚠️",
                "offline": "❌", 
                "not_found": "❌",
                "error": "💥"
            }.get(db_result["status"], "❓")
            
            print(f"  {status_emoji} {db_name}: {db_result['status']}")
            if db_name == "chromadb" and db_result["status"] == "healthy":
                print(f"     集合数量: {db_result['collections_count']}")
            elif db_name == "elasticsearch" and db_result["status"] == "healthy":
                print(f"     集群状态: {db_result['cluster_status']}")
        
        print()
        
        # 功能状态摘要
        print("🔧 功能状态:")
        for func_name, func_result in results["functionality"].items():
            status_emoji = {
                "healthy": "✅",
                "unhealthy": "⚠️",
                "error": "💥"
            }.get(func_result["status"], "❓")
            
            print(f"  {status_emoji} {func_name}: {func_result['status']}")
            if func_name == "retrieval" and func_result["status"] == "healthy":
                print(f"     检索结果数量: {func_result['results_count']}")
        
        print()
        
        # 总体状态
        all_healthy = True
        for category in ["services", "databases", "functionality"]:
            for item_name, item_result in results[category].items():
                if item_result["status"] not in ["healthy"]:
                    all_healthy = False
                    break
        
        if all_healthy:
            print("🎉 系统状态: 全部正常")
        else:
            print("⚠️ 系统状态: 存在问题")
        
        print("=" * 80)

def main():
    """主函数"""
    print("🚀 智诊通系统监控器启动")
    print("=" * 50)
    
    monitor = SystemMonitor()
    
    try:
        # 运行完整检查
        results = monitor.run_full_check()
        
        # 打印摘要
        monitor.print_summary(results)
        
        # 保存详细结果到文件 - 使用统一的logs目录
        project_root = Path(__file__).parent.parent.parent.parent
        output_file = project_root / "codes" / "logs" / f"system_health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        # 不自动创建logs目录，由统一日志系统管理
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📄 详细检查结果已保存到: {output_file}")
        
    except Exception as e:
        logger.error(f"❌ 系统检查失败: {e}")
        print(f"❌ 系统检查失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
