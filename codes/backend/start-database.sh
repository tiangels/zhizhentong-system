#!/bin/bash

# 智诊通系统数据库启动脚本
# 使用方法: ./start-database.sh

echo "🚀 启动智诊通系统数据库服务..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker Desktop"
    echo "💡 在macOS上，请打开Docker Desktop应用程序"
    exit 1
fi

# 检查docker-compose是否可用
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ 未找到docker-compose或docker compose命令"
    exit 1
fi

echo "📦 使用命令: $COMPOSE_CMD"

# 启动PostgreSQL数据库
echo "🐘 启动PostgreSQL数据库..."
$COMPOSE_CMD up -d postgres

# 等待数据库启动
echo "⏳ 等待数据库启动..."
sleep 10

# 检查数据库状态
if docker ps | grep -q "zhizhentong_postgres"; then
    echo "✅ PostgreSQL数据库启动成功！"
    echo "📊 数据库连接信息:"
    echo "   - 主机: localhost"
    echo "   - 端口: 5432"
    echo "   - 数据库: zhizhentong"
    echo "   - 用户: zhizhentong"
    echo "   - 密码: zhizhentong123"
    echo ""
    echo "🔗 连接字符串: postgresql://zhizhentong:zhizhentong123@localhost:5432/zhizhentong"
else
    echo "❌ PostgreSQL数据库启动失败"
    echo "📋 查看日志: $COMPOSE_CMD logs postgres"
    exit 1
fi

# 可选：启动Redis
read -p "🤔 是否同时启动Redis缓存服务? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔴 启动Redis缓存服务..."
    $COMPOSE_CMD up -d redis
    
    if docker ps | grep -q "zhizhentong_redis"; then
        echo "✅ Redis缓存服务启动成功！"
        echo "🔗 Redis连接: redis://localhost:6379/0"
    else
        echo "❌ Redis缓存服务启动失败"
    fi
fi

echo ""
echo "🎉 数据库服务启动完成！"
echo "📝 使用以下命令管理服务:"
echo "   - 查看状态: $COMPOSE_CMD ps"
echo "   - 查看日志: $COMPOSE_CMD logs [服务名]"
echo "   - 停止服务: $COMPOSE_CMD down"
echo "   - 重启服务: $COMPOSE_CMD restart [服务名]"