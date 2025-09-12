#!/bin/bash

# RAG检索增强系统快速启动脚本

echo "🚀 启动RAG检索增强系统..."

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ Python 未安装，请先安装Python"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖包..."
python -c "import torch, transformers, sentence_transformers, fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📥 安装依赖包..."
    pip install -r requirements.txt
fi

# 检查模型路径
MODEL_PATH="ai_models/llm_models/Qwen2-0.5B-Medical-MLX"
if [ ! -d "$MODEL_PATH" ]; then
    echo "⚠️  模型路径不存在: $MODEL_PATH"
    echo "请确保Qwen2-0.5B-Medical-MLX模型已下载到正确位置"
    echo "或者修改配置文件中的模型路径"
fi

# 创建必要目录
mkdir -p logs data

# 启动服务
echo "🎯 启动RAG服务..."
python start_rag_service.py --host 0.0.0.0 --port 8000

echo "✅ RAG服务已启动！"
echo "📖 API文档: http://localhost:8000/docs"
echo "🔍 健康检查: http://localhost:8000/health"
echo "🧪 运行测试: python test_rag_service.py"
