#!/bin/bash

# 智诊通Docker服务启动脚本
# 用于启动所有基础服务，不包含应用服务

echo "🚀 启动智诊通基础服务..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 进入docker目录
cd "$(dirname "$0")"

# 启动基础服务（数据库、缓存、搜索引擎等）
echo "📦 启动基础服务..."
docker compose up -d postgres redis elasticsearch kibana rabbitmq chromadb

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "🔍 检查服务状态..."
docker compose ps

# 显示服务访问地址
echo ""
echo "✅ 基础服务启动完成！"
echo ""
echo "📋 服务访问地址："
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - Elasticsearch: http://localhost:9200"
echo "  - Kibana: http://localhost:5601"
echo "  - RabbitMQ: http://localhost:15672 (用户名: zhizhentong, 密码: zhizhentong123)"
echo "  - ChromaDB: http://localhost:8003"
echo ""
echo "💡 要启动应用服务，请运行："
echo "   docker compose up -d backend zhi-zhen-tong-embedding"
echo ""
