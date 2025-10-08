#!/bin/bash

# 智诊通向量化服务启动脚本

echo "🚀 启动智诊通向量化服务..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查依赖
echo "🔍 检查依赖..."
python3 -c "import fastapi, uvicorn, torch" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️ 缺少依赖，请安装: pip install fastapi uvicorn torch transformers"
fi

# 启动服务
echo "📍 服务地址: http://localhost:8001"
echo "📖 API文档: http://localhost:8001/docs"
echo "🔧 管理界面: http://localhost:8001/redoc"
echo "=" * 50

python3 start_embedding_service.py
