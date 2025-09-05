#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智诊通系统 - 向量检索测试脚本
用于测试向量数据库的检索功能
"""

import os
import sys
import time
import traceback
from pathlib import Path

def test_retrieval():
    """测试向量检索功能"""
    try:
        # 导入必要的库
        from langchain_community.vectorstores import Chroma
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            print("✅ 使用langchain-huggingface导入HuggingFaceEmbeddings")
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            print("✅ 使用langchain-community导入HuggingFaceEmbeddings")
        
        print("=== 智诊通向量检索测试 ===")
        print(f"当前目录: {os.getcwd()}")
        
        # 检查向量数据库是否存在
        db_path = "./vector_database/chroma_db"
        if not os.path.exists(db_path):
            print(f"错误: 向量数据库不存在: {db_path}")
            print("请先运行数据预处理和向量数据库构建脚本")
            return False
        
        print(f"加载向量数据库: {db_path}")
        
        # 初始化嵌入模型
        print("初始化嵌入模型...")
        # 使用本地模型路径
        local_model_path = "./models/text2vec-base-chinese"
        if os.path.exists(local_model_path):
            print(f"使用本地模型: {local_model_path}")
            embeddings = HuggingFaceEmbeddings(
                model_name=local_model_path,
                model_kwargs={"device": "cpu"}
            )
        else:
            print("使用在线模型: shibing624/text2vec-base-chinese")
            embeddings = HuggingFaceEmbeddings(
                model_name="shibing624/text2vec-base-chinese",
                model_kwargs={"device": "cpu"}
            )
        
        # 加载向量数据库
        print("加载向量数据库...")
        vector_db = Chroma(
            persist_directory=db_path,
            embedding_function=embeddings
        )
        
        # 获取数据库统计信息
        try:
            collection = vector_db._collection
            count = collection.count()
            print(f"数据库中的文档数量: {count}")
        except Exception as e:
            print(f"无法获取文档数量: {e}")
        
        # 测试查询列表
        test_queries = [
            "胸痛患者的诊断建议",
            "发热咳嗽的治疗方法",
            "腹痛的可能原因",
            "头痛的诊断思路",
            "呼吸困难的检查项目"
        ]
        
        print("\n=== 开始检索测试 ===")
        
        total_time = 0
        successful_queries = 0
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n测试查询 {i}: {query}")
            print("-" * 50)
            
            try:
                start_time = time.time()
                results = vector_db.similarity_search(query, k=3)
                end_time = time.time()
                
                query_time = end_time - start_time
                total_time += query_time
                successful_queries += 1
                
                print(f"查询耗时: {query_time:.3f}秒")
                print(f"检索到 {len(results)} 个结果:")
                
                for j, result in enumerate(results, 1):
                    print(f"\n结果 {j}:")
                    print(f"内容: {result.page_content[:200]}...")
                    if hasattr(result, 'metadata') and result.metadata:
                        print(f"元数据: {result.metadata}")
                
            except Exception as e:
                print(f"查询失败: {e}")
                traceback.print_exc()
        
        # 输出统计信息
        print("\n=== 测试统计 ===")
        if successful_queries > 0:
            avg_time = total_time / successful_queries
            print(f"成功查询: {successful_queries}/{len(test_queries)}")
            print(f"平均查询时间: {avg_time:.3f}秒")
            print(f"总查询时间: {total_time:.3f}秒")
        else:
            print("所有查询都失败了")
            return False
        
        print("\n=== 测试完成 ===")
        return True
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请安装必要的依赖:")
        print("pip install langchain chromadb sentence-transformers")
        return False
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        traceback.print_exc()
        return False

def benchmark_performance():
    """性能基准测试"""
    try:
        import psutil
        from langchain_community.vectorstores import Chroma
        from langchain_community.embeddings import HuggingFaceEmbeddings
        
        print("\n=== 性能基准测试 ===")
        
        # 检查系统资源
        memory = psutil.virtual_memory()
        print(f"系统内存: {memory.total / (1024**3):.1f}GB")
        print(f"可用内存: {memory.available / (1024**3):.1f}GB")
        print(f"内存使用率: {memory.percent}%")
        
        # 加载向量数据库
        embeddings = HuggingFaceEmbeddings(
            model_name="shibing624/text2vec-base-chinese",
            model_kwargs={"device": "cpu"}
        )
        vector_db = Chroma(
            persist_directory="./vector_database/chroma_db",
            embedding_function=embeddings
        )
        
        # 批量查询测试
        queries = [f"症状{i}" for i in range(10)]
        
        print("执行批量查询测试...")
        start_time = time.time()
        
        for query in queries:
            results = vector_db.similarity_search(query, k=5)
        
        end_time = time.time()
        batch_time = end_time - start_time
        
        print(f"批量查询({len(queries)}次)耗时: {batch_time:.3f}秒")
        print(f"平均每次查询: {batch_time/len(queries):.3f}秒")
        
        # 检查内存使用变化
        memory_after = psutil.virtual_memory()
        print(f"测试后内存使用率: {memory_after.percent}%")
        
    except ImportError:
        print("性能测试需要psutil库: pip install psutil")
    except Exception as e:
        print(f"性能测试失败: {e}")

def main():
    """主函数"""
    print("智诊通向量检索测试工具")
    print("=" * 50)
    
    # 切换到脚本目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # 运行基本检索测试
    success = test_retrieval()
    
    if success:
        # 运行性能测试
        try:
            benchmark_performance()
        except Exception as e:
            print(f"性能测试跳过: {e}")
        
        print("\n✅ 向量检索功能正常!")
        print("\n接下来可以:")
        print("1. 将向量数据库集成到智诊通后端")
        print("2. 在RAG模块中使用检索功能")
        print("3. 根据实际需求调整检索参数")
    else:
        print("\n❌ 向量检索测试失败!")
        print("\n请检查:")
        print("1. 是否已运行数据预处理脚本")
        print("2. 是否已构建向量数据库")
        print("3. 依赖库是否正确安装")

if __name__ == "__main__":
    main()

"""
智诊通系统 - 向量检索测试脚本
用于测试向量数据库的检索功能
"""

import os
import sys
import time
import traceback
from pathlib import Path

def test_retrieval():
    """测试向量检索功能"""
    try:
        # 导入必要的库
        from langchain_community.vectorstores import Chroma
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            print("✅ 使用langchain-huggingface导入HuggingFaceEmbeddings")
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            print("✅ 使用langchain-community导入HuggingFaceEmbeddings")
        
        print("=== 智诊通向量检索测试 ===")
        print(f"当前目录: {os.getcwd()}")
        
        # 检查向量数据库是否存在
        db_path = "./vector_database/chroma_db"
        if not os.path.exists(db_path):
            print(f"错误: 向量数据库不存在: {db_path}")
            print("请先运行数据预处理和向量数据库构建脚本")
            return False
        
        print(f"加载向量数据库: {db_path}")
        
        # 初始化嵌入模型
        print("初始化嵌入模型...")
        # 使用本地模型路径
        local_model_path = "./models/text2vec-base-chinese"
        if os.path.exists(local_model_path):
            print(f"使用本地模型: {local_model_path}")
            embeddings = HuggingFaceEmbeddings(
                model_name=local_model_path,
                model_kwargs={"device": "cpu"}
            )
        else:
            print("使用在线模型: shibing624/text2vec-base-chinese")
            embeddings = HuggingFaceEmbeddings(
                model_name="shibing624/text2vec-base-chinese",
                model_kwargs={"device": "cpu"}
            )
        
        # 加载向量数据库
        print("加载向量数据库...")
        vector_db = Chroma(
            persist_directory=db_path,
            embedding_function=embeddings
        )
        
        # 获取数据库统计信息
        try:
            collection = vector_db._collection
            count = collection.count()
            print(f"数据库中的文档数量: {count}")
        except Exception as e:
            print(f"无法获取文档数量: {e}")
        
        # 测试查询列表
        test_queries = [
            "胸痛患者的诊断建议",
            "发热咳嗽的治疗方法",
            "腹痛的可能原因",
            "头痛的诊断思路",
            "呼吸困难的检查项目"
        ]
        
        print("\n=== 开始检索测试 ===")
        
        total_time = 0
        successful_queries = 0
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n测试查询 {i}: {query}")
            print("-" * 50)
            
            try:
                start_time = time.time()
                results = vector_db.similarity_search(query, k=3)
                end_time = time.time()
                
                query_time = end_time - start_time
                total_time += query_time
                successful_queries += 1
                
                print(f"查询耗时: {query_time:.3f}秒")
                print(f"检索到 {len(results)} 个结果:")
                
                for j, result in enumerate(results, 1):
                    print(f"\n结果 {j}:")
                    print(f"内容: {result.page_content[:200]}...")
                    if hasattr(result, 'metadata') and result.metadata:
                        print(f"元数据: {result.metadata}")
                
            except Exception as e:
                print(f"查询失败: {e}")
                traceback.print_exc()
        
        # 输出统计信息
        print("\n=== 测试统计 ===")
        if successful_queries > 0:
            avg_time = total_time / successful_queries
            print(f"成功查询: {successful_queries}/{len(test_queries)}")
            print(f"平均查询时间: {avg_time:.3f}秒")
            print(f"总查询时间: {total_time:.3f}秒")
        else:
            print("所有查询都失败了")
            return False
        
        print("\n=== 测试完成 ===")
        return True
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请安装必要的依赖:")
        print("pip install langchain chromadb sentence-transformers")
        return False
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        traceback.print_exc()
        return False

def benchmark_performance():
    """性能基准测试"""
    try:
        import psutil
        from langchain_community.vectorstores import Chroma
        from langchain_community.embeddings import HuggingFaceEmbeddings
        
        print("\n=== 性能基准测试 ===")
        
        # 检查系统资源
        memory = psutil.virtual_memory()
        print(f"系统内存: {memory.total / (1024**3):.1f}GB")
        print(f"可用内存: {memory.available / (1024**3):.1f}GB")
        print(f"内存使用率: {memory.percent}%")
        
        # 加载向量数据库
        embeddings = HuggingFaceEmbeddings(
            model_name="shibing624/text2vec-base-chinese",
            model_kwargs={"device": "cpu"}
        )
        vector_db = Chroma(
            persist_directory="./vector_database/chroma_db",
            embedding_function=embeddings
        )
        
        # 批量查询测试
        queries = [f"症状{i}" for i in range(10)]
        
        print("执行批量查询测试...")
        start_time = time.time()
        
        for query in queries:
            results = vector_db.similarity_search(query, k=5)
        
        end_time = time.time()
        batch_time = end_time - start_time
        
        print(f"批量查询({len(queries)}次)耗时: {batch_time:.3f}秒")
        print(f"平均每次查询: {batch_time/len(queries):.3f}秒")
        
        # 检查内存使用变化
        memory_after = psutil.virtual_memory()
        print(f"测试后内存使用率: {memory_after.percent}%")
        
    except ImportError:
        print("性能测试需要psutil库: pip install psutil")
    except Exception as e:
        print(f"性能测试失败: {e}")

def main():
    """主函数"""
    print("智诊通向量检索测试工具")
    print("=" * 50)
    
    # 切换到脚本目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # 运行基本检索测试
    success = test_retrieval()
    
    if success:
        # 运行性能测试
        try:
            benchmark_performance()
        except Exception as e:
            print(f"性能测试跳过: {e}")
        
        print("\n✅ 向量检索功能正常!")
        print("\n接下来可以:")
        print("1. 将向量数据库集成到智诊通后端")
        print("2. 在RAG模块中使用检索功能")
        print("3. 根据实际需求调整检索参数")
    else:
        print("\n❌ 向量检索测试失败!")
        print("\n请检查:")
        print("1. 是否已运行数据预处理脚本")
        print("2. 是否已构建向量数据库")
        print("3. 依赖库是否正确安装")

if __name__ == "__main__":
    main()
