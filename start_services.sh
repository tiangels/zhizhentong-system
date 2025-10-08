#!/bin/bash

# 智诊通服务启动脚本
# 同时启动向量化服务和RAG服务

echo "🚀 启动智诊通服务系统..."
echo "=================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 设置工作目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 工作目录: $SCRIPT_DIR"

# 函数：检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  端口 $port 已被占用"
        return 1
    else
        echo "✅ 端口 $port 可用"
        return 0
    fi
}

# 函数：启动向量化服务
start_vectorization_service() {
    echo ""
    echo "🔧 启动向量化服务 (端口 8001)..."
    echo "--------------------------------"
    
    if ! check_port 8001; then
        echo "❌ 无法启动向量化服务，端口 8001 被占用"
        return 1
    fi
    
    # 启动向量化服务 (新目录)
    cd codes/services/embedding_service
    python3 start_embedding_service.py &
    VECTORIZATION_PID=$!
    echo "✅ 向量化服务已启动 (PID: $VECTORIZATION_PID)"
    
    # 等待服务启动
    echo "⏳ 等待向量化服务启动..."
    sleep 10
    
    # 检查服务是否正常启动
    if curl -s http://localhost:8001/health > /dev/null; then
        echo "✅ 向量化服务启动成功"
    else
        echo "❌ 向量化服务启动失败"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
    return 0
}

# 函数：启动RAG服务
start_rag_service() {
    echo ""
    echo "🔧 启动RAG服务 (端口 8002)..."
    echo "--------------------------------"
    
    if ! check_port 8002; then
        echo "❌ 无法启动RAG服务，端口 8002 被占用"
        return 1
    fi
    
    # 启动RAG服务
    cd codes/services/knowledge_retrieval_service/api
    python3 rag_api.py &
    RAG_PID=$!
    echo "✅ RAG服务已启动 (PID: $RAG_PID)"
    
    # 等待服务启动
    echo "⏳ 等待RAG服务启动..."
    sleep 10
    
    # 检查服务是否正常启动
    if curl -s http://localhost:8002/health > /dev/null; then
        echo "✅ RAG服务启动成功"
    else
        echo "❌ RAG服务启动失败"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
    return 0
}

# 函数：清理进程
cleanup() {
    echo ""
    echo "🧹 清理服务进程..."
    if [ ! -z "$VECTORIZATION_PID" ]; then
        kill $VECTORIZATION_PID 2>/dev/null
        echo "✅ 向量化服务已停止"
    fi
    if [ ! -z "$RAG_PID" ]; then
        kill $RAG_PID 2>/dev/null
        echo "✅ RAG服务已停止"
    fi
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 主启动流程
echo "🔍 检查服务依赖..."

# 启动向量化服务
if start_vectorization_service; then
    echo "✅ 向量化服务启动成功"
else
    echo "❌ 向量化服务启动失败"
    exit 1
fi

# 启动RAG服务
if start_rag_service; then
    echo "✅ RAG服务启动成功"
else
    echo "❌ RAG服务启动失败"
    cleanup
    exit 1
fi

echo ""
echo "🎉 所有服务启动成功！"
echo "=================================="
echo "📊 服务状态:"
echo "   • 向量化服务: http://localhost:8001"
echo "   • RAG服务:     http://localhost:8002"
echo ""
echo "📋 可用接口:"
echo "   • 向量化服务健康检查: curl http://localhost:8001/health"
echo "   • RAG服务健康检查:    curl http://localhost:8002/health"
echo "   • 向量化API文档:      http://localhost:8001/docs"
echo "   • RAG服务API文档:     http://localhost:8002/docs"
echo ""
echo "🧪 运行集成测试:"
echo "   python3 test_rag_vectorization_integration.py"
echo ""
echo "⏹️  按 Ctrl+C 停止所有服务"

# 保持脚本运行
wait
