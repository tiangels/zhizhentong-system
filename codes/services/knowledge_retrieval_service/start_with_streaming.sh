#!/bin/bash

# RAG服务启动脚本（支持流式查询）
echo "🚀 启动RAG知识检索服务（支持流式查询）"
echo "=================================="

# 检查conda环境
if ! command -v conda &> /dev/null; then
    echo "❌ 未找到conda，请先安装Anaconda或Miniconda"
    exit 1
fi

# 激活nlp环境
echo "📦 激活conda环境: nlp"
source ~/miniconda3/etc/profile.d/conda.sh
conda activate nlp

if [ $? -ne 0 ]; then
    echo "❌ 激活nlp环境失败，请检查环境是否存在"
    echo "💡 可以运行: conda create -n nlp python=3.9"
    exit 1
fi

# 检查Python包
echo "🔍 检查必要的Python包..."
python -c "import torch, transformers, fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 缺少必要的Python包，请安装："
    echo "pip install torch transformers fastapi uvicorn"
    exit 1
fi

# 检查模型文件
MODEL_PATH="ai_models/llm_models/Qwen2-0.5B-Medical-MLX"
if [ ! -d "$MODEL_PATH" ]; then
    echo "⚠️  模型路径不存在: $MODEL_PATH"
    echo "💡 请确保模型已正确下载到指定路径"
fi

# 启动服务
echo "🌟 启动RAG服务..."
echo "📍 服务地址: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo "🧪 流式测试页面: http://localhost:8000/../test_streaming.html"
echo "=================================="

# 启动API服务
python start_rag_service.py
