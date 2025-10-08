#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智诊通系统监控和健康检查
监控向量数据库、ES数据库、检索服务等关键组件的状态
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('system_monitor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class SystemMonitor:
    """系统监控器"""
    
    def __init__(self):
        self.config = {
            "CHROMA_DB_PATH": "../../../datas/chroma_db",
            "ES_HOST": "localhost",
            "ES_PORT": 9200,
            "ES_INDEX": "medical_records",
            "VECTOR_COLLECTION": "medical_multimodal_vectors",
            "RETRIEVAL_SERVICE_PORT": 8001,
            "EMBEDDING_SERVICE_PORT": 8002
        }
        
    def check_chromadb_status(self) -> Dict[str, Any]:
        """检查ChromaDB状态"""
        try:
            import chromadb
            
            # 检查数据库文件
            db_path = self.config["CHROMA_DB_PATH"]
            db_exists = os.path.exists(db_path)
            sqlite_file = os.path.join(db_path, "chroma.sqlite3")
            sqlite_exists = os.path.exists(sqlite_file)
            
            if sqlite_exists:
                sqlite_size = os.path.getsize(sqlite_file)
            else:
                sqlite_size = 0
            
            # 连接数据库
            client = chromadb.PersistentClient(path=db_path)
            collections = client.list_collections()
            
            # 检查目标集合
            target_collection = None
            doc_count = 0
            if collections:
                for collection in collections:
                    if collection.name == self.config["VECTOR_COLLECTION"]:
                        target_collection = client.get_collection(collection.name)
                        doc_count = target_collection.count()
                        break
            
            return {
                "status": "healthy" if target_collection else "unhealthy",
                "db_path": db_path,
                "db_exists": db_exists,
                "sqlite_exists": sqlite_exists,
                "sqlite_size_mb": round(sqlite_size / 1024 / 1024, 2),
                "collections_count": len(collections),
                "target_collection_exists": target_collection is not None,
                "document_count": doc_count,
                "collection_names": [c.name for c in collections]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_elasticsearch_status(self) -> Dict[str, Any]:
        """检查Elasticsearch状态"""
        try:
            es_url = f"http://{self.config['ES_HOST']}:{self.config['ES_PORT']}"
            
            # 检查ES连接
            response = requests.get(es_url, timeout=5)
            es_healthy = response.status_code == 200
            
            if es_healthy:
                # 检查索引
                index_url = f"{es_url}/{self.config['ES_INDEX']}"
                index_response = requests.get(index_url, timeout=5)
                index_exists = index_response.status_code == 200
                
                if index_exists:
                    # 获取文档数量
                    count_url = f"{index_url}/_count"
                    count_response = requests.get(count_url, timeout=5)
                    if count_response.status_code == 200:
                        doc_count = count_response.json().get("count", 0)
                    else:
                        doc_count = 0
                else:
                    doc_count = 0
            else:
                index_exists = False
                doc_count = 0
            
            return {
                "status": "healthy" if es_healthy and index_exists else "unhealthy",
                "es_url": es_url,
                "es_healthy": es_healthy,
                "index_exists": index_exists,
                "document_count": doc_count,
                "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2) if es_healthy else None
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_retrieval_service_status(self) -> Dict[str, Any]:
        """检查检索服务状态"""
        try:
            service_url = f"http://localhost:{self.config['RETRIEVAL_SERVICE_PORT']}/health"
            response = requests.get(service_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "service_url": service_url,
                    "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
                    "service_data": data
                }
            else:
                return {
                    "status": "unhealthy",
                    "service_url": service_url,
                    "http_status": response.status_code
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_embedding_service_status(self) -> Dict[str, Any]:
        """检查向量化服务状态"""
        try:
            service_url = f"http://localhost:{self.config['EMBEDDING_SERVICE_PORT']}/health"
            response = requests.get(service_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "service_url": service_url,
                    "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
                    "service_data": data
                }
            else:
                return {
                    "status": "unhealthy",
                    "service_url": service_url,
                    "http_status": response.status_code
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_disk_space(self) -> Dict[str, Any]:
        """检查磁盘空间"""
        try:
            import shutil
            
            # 检查项目根目录磁盘空间
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            total, used, free = shutil.disk_usage(project_root)
            
            # 检查ChromaDB目录空间
            chroma_path = self.config["CHROMA_DB_PATH"]
            chroma_total = 0
            chroma_used = 0
            if os.path.exists(chroma_path):
                for root, dirs, files in os.walk(chroma_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            chroma_used += os.path.getsize(file_path)
                        except:
                            pass
            
            return {
                "status": "healthy",
                "project_root": project_root,
                "total_gb": round(total / 1024**3, 2),
                "used_gb": round(used / 1024**3, 2),
                "free_gb": round(free / 1024**3, 2),
                "usage_percent": round(used / total * 100, 2),
                "chroma_db_size_mb": round(chroma_used / 1024**2, 2)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def run_health_check(self) -> Dict[str, Any]:
        """运行完整健康检查"""
        logger.info("🔍 开始系统健康检查...")
        
        start_time = time.time()
        
        # 检查各个组件
        chromadb_status = self.check_chromadb_status()
        es_status = self.check_elasticsearch_status()
        retrieval_status = self.check_retrieval_service_status()
        embedding_status = self.check_embedding_service_status()
        disk_status = self.check_disk_space()
        
        # 计算总体健康状态
        all_healthy = all([
            chromadb_status.get("status") == "healthy",
            es_status.get("status") == "healthy",
            disk_status.get("status") == "healthy"
        ])
        
        # 服务状态（可选）
        services_healthy = all([
            retrieval_status.get("status") in ["healthy", "error"],  # 服务可能未启动
            embedding_status.get("status") in ["healthy", "error"]   # 服务可能未启动
        ])
        
        total_time = round((time.time() - start_time) * 1000, 2)
        
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy" if all_healthy else "unhealthy",
            "services_status": "healthy" if services_healthy else "unhealthy",
            "check_duration_ms": total_time,
            "components": {
                "chromadb": chromadb_status,
                "elasticsearch": es_status,
                "retrieval_service": retrieval_status,
                "embedding_service": embedding_status,
                "disk_space": disk_status
            }
        }
        
        logger.info(f"✅ 健康检查完成，耗时: {total_time}ms")
        logger.info(f"📊 总体状态: {health_report['overall_status']}")
        
        return health_report
    
    def print_health_report(self, report: Dict[str, Any]):
        """打印健康检查报告"""
        print("\n" + "="*80)
        print("🏥 智诊通系统健康检查报告")
        print("="*80)
        print(f"⏰ 检查时间: {report['timestamp']}")
        print(f"🎯 总体状态: {report['overall_status'].upper()}")
        print(f"🔧 服务状态: {report['services_status'].upper()}")
        print(f"⏱️  检查耗时: {report['check_duration_ms']}ms")
        
        print("\n📋 组件状态详情:")
        print("-" * 50)
        
        # ChromaDB状态
        chromadb = report['components']['chromadb']
        print(f"🗄️  ChromaDB:")
        print(f"   状态: {chromadb['status']}")
        if chromadb['status'] == 'healthy':
            print(f"   文档数量: {chromadb['document_count']}")
            print(f"   数据库大小: {chromadb['sqlite_size_mb']}MB")
            print(f"   集合数量: {chromadb['collections_count']}")
        elif chromadb['status'] == 'error':
            print(f"   错误: {chromadb['error']}")
        
        # Elasticsearch状态
        es = report['components']['elasticsearch']
        print(f"🔍 Elasticsearch:")
        print(f"   状态: {es['status']}")
        if es['status'] == 'healthy':
            print(f"   文档数量: {es['document_count']}")
            print(f"   响应时间: {es['response_time_ms']}ms")
        elif es['status'] == 'error':
            print(f"   错误: {es['error']}")
        
        # 检索服务状态
        retrieval = report['components']['retrieval_service']
        print(f"🔎 检索服务:")
        print(f"   状态: {retrieval['status']}")
        if retrieval['status'] == 'healthy':
            print(f"   响应时间: {retrieval['response_time_ms']}ms")
        elif retrieval['status'] == 'error':
            print(f"   错误: {retrieval['error']}")
        
        # 向量化服务状态
        embedding = report['components']['embedding_service']
        print(f"🧠 向量化服务:")
        print(f"   状态: {embedding['status']}")
        if embedding['status'] == 'healthy':
            print(f"   响应时间: {embedding['response_time_ms']}ms")
        elif embedding['status'] == 'error':
            print(f"   错误: {embedding['error']}")
        
        # 磁盘空间状态
        disk = report['components']['disk_space']
        print(f"💾 磁盘空间:")
        print(f"   状态: {disk['status']}")
        if disk['status'] == 'healthy':
            print(f"   总空间: {disk['total_gb']}GB")
            print(f"   已使用: {disk['used_gb']}GB ({disk['usage_percent']}%)")
            print(f"   可用空间: {disk['free_gb']}GB")
            print(f"   ChromaDB大小: {disk['chroma_db_size_mb']}MB")
        elif disk['status'] == 'error':
            print(f"   错误: {disk['error']}")
        
        print("\n" + "="*80)
        
        # 健康建议
        if report['overall_status'] == 'unhealthy':
            print("⚠️  系统健康建议:")
            if chromadb['status'] != 'healthy':
                print("   - 检查ChromaDB数据库连接和集合状态")
            if es['status'] != 'healthy':
                print("   - 检查Elasticsearch服务是否运行")
            if disk['status'] != 'healthy':
                print("   - 检查磁盘空间是否充足")
        else:
            print("✅ 系统运行正常，所有核心组件健康！")
        
        print("="*80)

def main():
    """主函数"""
    print("🚀 智诊通系统监控启动")
    
    monitor = SystemMonitor()
    
    # 运行健康检查
    health_report = monitor.run_health_check()
    
    # 打印报告
    monitor.print_health_report(health_report)
    
    # 保存报告到文件
    report_file = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(health_report, f, ensure_ascii=False, indent=2)
    
    print(f"📄 健康检查报告已保存到: {report_file}")
    
    return health_report

if __name__ == "__main__":
    main()
