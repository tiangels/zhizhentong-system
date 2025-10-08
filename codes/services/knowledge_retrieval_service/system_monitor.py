#!/usr/bin/env python3
"""
智诊通系统监控和健康检查脚本
检查各个服务的状态和功能
"""

import requests
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess
import psutil

class SystemMonitor:
    def __init__(self):
        self.services = {
            "elasticsearch": {
                "url": "http://localhost:9200",
                "health_endpoint": "/_cluster/health",
                "status": "unknown"
            },
            "embedding_service": {
                "url": "http://localhost:8001",
                "health_endpoint": "/health",
                "status": "unknown"
            },
            "knowledge_retrieval_service": {
                "url": "http://localhost:8002", 
                "health_endpoint": "/health",
                "status": "unknown"
            },
            "intelligent_diagnosis_service": {
                "url": "http://localhost:8003",
                "health_endpoint": "/health", 
                "status": "unknown"
            },
            "backend_api": {
                "url": "http://localhost:8000",
                "health_endpoint": "/health",
                "status": "unknown"
            }
        }
        
        self.databases = {
            "chromadb": {
                "path": "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/chroma_db",
                "status": "unknown"
            },
            "postgresql": {
                "host": "localhost",
                "port": 5432,
                "status": "unknown"
            }
        }
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "services": {},
            "databases": {},
            "system_resources": {},
            "recommendations": []
        }

    def check_service_health(self, service_name: str, service_config: Dict) -> Dict:
        """检查单个服务的健康状态"""
        try:
            url = f"{service_config['url']}{service_config['health_endpoint']}"
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
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        except requests.exceptions.ConnectionError:
            return {
                "status": "unreachable",
                "error": "Connection refused - service may not be running"
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

    def check_chromadb(self) -> Dict:
        """检查ChromaDB状态"""
        try:
            import chromadb
            
            # 检查数据库文件是否存在
            db_path = self.databases["chromadb"]["path"]
            if not os.path.exists(db_path):
                return {
                    "status": "not_found",
                    "error": f"Database path not found: {db_path}"
                }
            
            # 检查chroma.sqlite3文件
            sqlite_file = os.path.join(db_path, "chroma.sqlite3")
            if not os.path.exists(sqlite_file):
                return {
                    "status": "incomplete",
                    "error": "ChromaDB database file not found"
                }
            
            # 尝试连接数据库
            client = chromadb.PersistentClient(path=db_path)
            collections = client.list_collections()
            
            return {
                "status": "healthy",
                "collections_count": len(collections),
                "collections": [col.name for col in collections],
                "db_size": self.get_directory_size(db_path)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def check_postgresql(self) -> Dict:
        """检查PostgreSQL状态"""
        try:
            import psycopg2
            
            conn = psycopg2.connect(
                host=self.databases["postgresql"]["host"],
                port=self.databases["postgresql"]["port"],
                database="zhizhentong",
                user="zhizhentong",
                password="zhizhentong123"
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # 检查表是否存在
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                );
            """)
            users_table_exists = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'medical_records'
                );
            """)
            medical_records_table_exists = cursor.fetchone()[0]
            
            user_count = 0
            record_count = 0
            
            if users_table_exists:
                cursor.execute("SELECT COUNT(*) FROM users;")
                user_count = cursor.fetchone()[0]
            
            if medical_records_table_exists:
                cursor.execute("SELECT COUNT(*) FROM medical_records;")
                record_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return {
                "status": "healthy",
                "version": version,
                "users_table_exists": users_table_exists,
                "medical_records_table_exists": medical_records_table_exists,
                "user_count": user_count,
                "record_count": record_count
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def get_directory_size(self, path: str) -> str:
        """获取目录大小"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
            
            # 转换为人类可读的格式
            for unit in ['B', 'KB', 'MB', 'GB']:
                if total_size < 1024.0:
                    return f"{total_size:.1f} {unit}"
                total_size /= 1024.0
            return f"{total_size:.1f} TB"
        except:
            return "Unknown"

    def check_system_resources(self) -> Dict:
        """检查系统资源使用情况"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                }
            }
        except Exception as e:
            return {
                "error": str(e)
            }

    def test_retrieval_functionality(self) -> Dict:
        """测试检索功能"""
        try:
            # 测试向量化服务检索
            embedding_url = "http://localhost:8001/retrieve"
            embedding_payload = {
                "query": "感冒症状",
                "top_k": 5
            }
            
            embedding_response = requests.post(
                embedding_url, 
                json=embedding_payload, 
                timeout=10
            )
            
            embedding_result = {
                "status": "success" if embedding_response.status_code == 200 else "failed",
                "status_code": embedding_response.status_code,
                "response": embedding_response.json() if embedding_response.status_code == 200 else None
            }
            
            # 测试知识检索服务
            retrieval_url = "http://localhost:8002/retrieve"
            retrieval_payload = {
                "query": "感冒症状",
                "top_k": 5,
                "use_es": True,
                "use_vector": True
            }
            
            retrieval_response = requests.post(
                retrieval_url,
                json=retrieval_payload,
                timeout=10
            )
            
            retrieval_result = {
                "status": "success" if retrieval_response.status_code == 200 else "failed",
                "status_code": retrieval_response.status_code,
                "response": retrieval_response.json() if retrieval_response.status_code == 200 else None
            }
            
            return {
                "embedding_service": embedding_result,
                "retrieval_service": retrieval_result
            }
            
        except Exception as e:
            return {
                "error": str(e)
            }

    def generate_recommendations(self) -> List[str]:
        """生成系统优化建议"""
        recommendations = []
        
        # 检查服务状态
        unhealthy_services = []
        for service_name, service_data in self.results["services"].items():
            if service_data["status"] not in ["healthy"]:
                unhealthy_services.append(service_name)
        
        if unhealthy_services:
            recommendations.append(f"需要修复以下服务: {', '.join(unhealthy_services)}")
        
        # 检查数据库状态
        if self.results["databases"]["chromadb"]["status"] != "healthy":
            recommendations.append("ChromaDB数据库需要检查和修复")
        
        if self.results["databases"]["postgresql"]["status"] != "healthy":
            recommendations.append("PostgreSQL数据库需要检查和修复")
        
        # 检查系统资源
        if "system_resources" in self.results:
            resources = self.results["system_resources"]
            if "cpu_percent" in resources and resources["cpu_percent"] > 80:
                recommendations.append("CPU使用率过高，建议优化系统性能")
            
            if "memory" in resources and resources["memory"]["percent"] > 80:
                recommendations.append("内存使用率过高，建议增加内存或优化内存使用")
            
            if "disk" in resources and resources["disk"]["percent"] > 90:
                recommendations.append("磁盘空间不足，建议清理或扩容")
        
        # 检查检索功能
        if "retrieval_test" in self.results:
            retrieval_test = self.results["retrieval_test"]
            if "embedding_service" in retrieval_test and retrieval_test["embedding_service"]["status"] != "success":
                recommendations.append("向量化服务检索功能异常，需要检查")
            
            if "retrieval_service" in retrieval_test and retrieval_test["retrieval_service"]["status"] != "success":
                recommendations.append("知识检索服务功能异常，需要检查")
        
        if not recommendations:
            recommendations.append("系统运行正常，无需特殊处理")
        
        return recommendations

    def run_full_check(self) -> Dict:
        """运行完整的系统检查"""
        print("=== 智诊通系统健康检查 ===")
        print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 检查服务状态
        print("🔍 检查服务状态...")
        for service_name, service_config in self.services.items():
            print(f"  检查 {service_name}...")
            result = self.check_service_health(service_name, service_config)
            self.results["services"][service_name] = result
            
            status_emoji = {
                "healthy": "✅",
                "unhealthy": "❌", 
                "unreachable": "🔴",
                "timeout": "⏰",
                "error": "💥"
            }.get(result["status"], "❓")
            
            print(f"    {status_emoji} {service_name}: {result['status']}")
            if "error" in result:
                print(f"      错误: {result['error']}")
        
        print()
        
        # 检查数据库状态
        print("🗄️ 检查数据库状态...")
        
        print("  检查 ChromaDB...")
        chromadb_result = self.check_chromadb()
        self.results["databases"]["chromadb"] = chromadb_result
        
        status_emoji = {
            "healthy": "✅",
            "not_found": "❌",
            "incomplete": "⚠️",
            "error": "💥"
        }.get(chromadb_result["status"], "❓")
        
        print(f"    {status_emoji} ChromaDB: {chromadb_result['status']}")
        if "error" in chromadb_result:
            print(f"      错误: {chromadb_result['error']}")
        elif chromadb_result["status"] == "healthy":
            print(f"      集合数量: {chromadb_result['collections_count']}")
            print(f"      数据库大小: {chromadb_result['db_size']}")
        
        print("  检查 PostgreSQL...")
        postgresql_result = self.check_postgresql()
        self.results["databases"]["postgresql"] = postgresql_result
        
        status_emoji = "✅" if postgresql_result["status"] == "healthy" else "❌"
        print(f"    {status_emoji} PostgreSQL: {postgresql_result['status']}")
        if "error" in postgresql_result:
            print(f"      错误: {postgresql_result['error']}")
        elif postgresql_result["status"] == "healthy":
            print(f"      用户表存在: {postgresql_result['users_table_exists']}")
            print(f"      医疗记录表存在: {postgresql_result['medical_records_table_exists']}")
            print(f"      用户数量: {postgresql_result['user_count']}")
            print(f"      医疗记录数量: {postgresql_result['record_count']}")
        
        print()
        
        # 检查系统资源
        print("💻 检查系统资源...")
        system_resources = self.check_system_resources()
        self.results["system_resources"] = system_resources
        
        if "error" not in system_resources:
            print(f"  CPU使用率: {system_resources['cpu_percent']:.1f}%")
            print(f"  内存使用率: {system_resources['memory']['percent']:.1f}%")
            print(f"  磁盘使用率: {system_resources['disk']['percent']:.1f}%")
        else:
            print(f"  ❌ 系统资源检查失败: {system_resources['error']}")
        
        print()
        
        # 测试检索功能
        print("🔍 测试检索功能...")
        retrieval_test = self.test_retrieval_functionality()
        self.results["retrieval_test"] = retrieval_test
        
        if "error" not in retrieval_test:
            embedding_status = retrieval_test["embedding_service"]["status"]
            retrieval_status = retrieval_test["retrieval_service"]["status"]
            
            embedding_emoji = "✅" if embedding_status == "success" else "❌"
            retrieval_emoji = "✅" if retrieval_status == "success" else "❌"
            
            print(f"  {embedding_emoji} 向量化服务检索: {embedding_status}")
            print(f"  {retrieval_emoji} 知识检索服务: {retrieval_status}")
        else:
            print(f"  ❌ 检索功能测试失败: {retrieval_test['error']}")
        
        print()
        
        # 生成建议
        print("💡 系统建议...")
        recommendations = self.generate_recommendations()
        self.results["recommendations"] = recommendations
        
        for i, recommendation in enumerate(recommendations, 1):
            print(f"  {i}. {recommendation}")
        
        print()
        
        # 确定整体状态
        healthy_services = sum(1 for s in self.results["services"].values() if s["status"] == "healthy")
        total_services = len(self.results["services"])
        
        if healthy_services == total_services and all(db["status"] == "healthy" for db in self.results["databases"].values()):
            self.results["overall_status"] = "healthy"
            print("🎉 系统整体状态: 健康")
        elif healthy_services >= total_services * 0.8:
            self.results["overall_status"] = "warning"
            print("⚠️ 系统整体状态: 警告")
        else:
            self.results["overall_status"] = "critical"
            print("🚨 系统整体状态: 严重")
        
        return self.results

    def save_report(self, filename: str = None):
        """保存检查报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"system_health_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"📄 检查报告已保存到: {filename}")

def main():
    """主函数"""
    monitor = SystemMonitor()
    
    # 运行完整检查
    results = monitor.run_full_check()
    
    # 保存报告
    monitor.save_report()
    
    # 返回适当的退出码
    if results["overall_status"] == "healthy":
        sys.exit(0)
    elif results["overall_status"] == "warning":
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()
