#!/usr/bin/env conda run -n nlp python
"""
RAG流式查询系统快速启动脚本
"""

import os
import sys
import subprocess
import time
import requests
import webbrowser
from pathlib import Path

def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")
    
    # 检查Python版本
    if sys.version_info < (3, 9):
        print("❌ Python版本过低，需要3.9+")
        return False
    
    # 检查必要的包
    required_packages = ['torch', 'transformers', 'fastapi', 'uvicorn']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少必要的包: {', '.join(missing_packages)}")
        print("💡 请运行: pip install " + " ".join(missing_packages))
        return False
    
    # 检查模型路径
    model_path = Path("ai_models/llm_models/Qwen2-0.5B-Medical-MLX")
    if not model_path.exists():
        print(f"⚠️  模型路径不存在: {model_path}")
        print("💡 请确保模型已正确下载到指定路径")
    
    print("✅ 环境检查完成")
    return True

def start_service():
    """启动RAG服务"""
    print("🚀 启动RAG服务...")
    
    try:
        # 启动服务进程
        process = subprocess.Popen([
            sys.executable, "start_rag_service.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待服务启动
        print("⏳ 等待服务启动...")
        time.sleep(5)
        
        # 检查服务状态
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ 服务启动成功")
                return process
            else:
                print("❌ 服务启动失败")
                return None
        except requests.exceptions.RequestException:
            print("❌ 无法连接到服务")
            return None
            
    except Exception as e:
        print(f"❌ 启动服务时出错: {e}")
        return None

def run_tests():
    """运行测试"""
    print("🧪 运行功能测试...")
    
    try:
        # 运行流式测试
        result = subprocess.run([
            sys.executable, "test_streaming.py"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ 测试完成")
            print(result.stdout)
        else:
            print("❌ 测试失败")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏰ 测试超时")
    except Exception as e:
        print(f"❌ 运行测试时出错: {e}")

def open_web_interface():
    """打开Web界面"""
    print("🌐 打开Web测试界面...")
    
    try:
        # 打开测试页面
        test_page = Path("test_streaming.html").absolute()
        webbrowser.open(f"file://{test_page}")
        
        # 打开API文档
        webbrowser.open("http://localhost:8000/docs")
        
        print("✅ Web界面已打开")
        
    except Exception as e:
        print(f"❌ 打开Web界面时出错: {e}")

def show_usage_info():
    """显示使用信息"""
    print("\n" + "="*60)
    print("🎉 RAG流式查询系统启动完成！")
    print("="*60)
    print("📡 服务地址: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    print("🧪 测试页面: test_streaming.html")
    print("="*60)
    print("🔧 可用命令:")
    print("  • 流式查询: POST /query/stream")
    print("  • 常规查询: POST /query")
    print("  • 健康检查: GET /health")
    print("="*60)
    print("📖 详细文档: STREAMING_GUIDE.md")
    print("="*60)
    print("💡 按 Ctrl+C 停止服务")
    print("="*60)

def main():
    """主函数"""
    print("🌟 RAG流式查询系统快速启动")
    print("="*50)
    
    # 检查环境
    if not check_environment():
        print("❌ 环境检查失败，请修复后重试")
        return
    
    # 启动服务
    service_process = start_service()
    if not service_process:
        print("❌ 服务启动失败")
        return
    
    try:
        # 运行测试
        run_tests()
        
        # 打开Web界面
        open_web_interface()
        
        # 显示使用信息
        show_usage_info()
        
        # 保持服务运行
        print("\n🔄 服务正在运行，按 Ctrl+C 停止...")
        service_process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 正在停止服务...")
        service_process.terminate()
        service_process.wait()
        print("✅ 服务已停止")
    except Exception as e:
        print(f"❌ 运行时出错: {e}")
        if service_process:
            service_process.terminate()

if __name__ == "__main__":
    main()
