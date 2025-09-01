#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 智诊通系统状态检查${NC}"
echo "=================================="
echo ""

# 检查后端服务状态
echo -e "${CYAN}📋 后端服务状态:${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ 后端API服务运行正常 (端口: 8000)${NC}"
else
    echo -e "  ${RED}❌ 后端API服务未运行或无法访问${NC}"
fi

# 检查前端服务状态
echo -e "${CYAN}📋 前端服务状态:${NC}"
if curl -s http://localhost:8080 > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ 前端服务运行正常 (端口: 8080)${NC}"
else
    echo -e "  ${RED}❌ 前端服务未运行或无法访问${NC}"
fi

# 检查 Docker 服务状态
echo -e "${CYAN}📋 Docker 服务状态:${NC}"
cd backend

# 检查 Docker Compose 命令
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo -e "  ${YELLOW}⚠️  Docker Compose 未找到${NC}"
    cd ..
    return
fi

if $DOCKER_COMPOSE_CMD ps | grep -q "Up"; then
    echo -e "  ${GREEN}✅ Docker 服务运行正常${NC}"
    $DOCKER_COMPOSE_CMD ps | grep -E "(postgres|redis|rabbitmq)" | while read line; do
        echo -e "  $line"
    done
else
    echo -e "  ${YELLOW}⚠️  Docker 服务未运行${NC}"
fi
cd ..

# 检查数据库状态
echo -e "${CYAN}📋 PostgreSQL 数据库状态:${NC}"
if docker exec zhizhentong_postgres pg_isready -U postgres -d zhizhentong > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ PostgreSQL 数据库连接正常${NC}"
else
    echo -e "  ${RED}❌ PostgreSQL 数据库连接失败${NC}"
fi

# 检查Redis状态
echo -e "${CYAN}📋 Redis状态:${NC}"
if docker exec zhizhentong_redis redis-cli ping > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Redis服务运行正常${NC}"
else
    echo -e "  ${RED}❌ Redis服务未运行${NC}"
fi

# 检查Milvus状态
echo -e "${CYAN}📋 Milvus向量数据库状态:${NC}"
if command -v curl &> /dev/null; then
    if curl -s http://localhost:19530/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Milvus服务运行正常 (端口: 19530)${NC}"
    else
        echo -e "  ${YELLOW}⚠️  Milvus服务未运行或无法访问${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠️  curl命令不可用${NC}"
fi

# 检查RabbitMQ状态
echo -e "${CYAN}📋 RabbitMQ状态:${NC}"
if curl -s -u zhizhentong:zhizhentong123 http://localhost:15672/api/overview > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ RabbitMQ服务运行正常 (端口: 5672)${NC}"
else
    echo -e "  ${YELLOW}⚠️  RabbitMQ服务未运行或无法访问${NC}"
fi

# 检查端口占用情况
echo -e "${CYAN}📋 端口占用情况:${NC}"
echo -e "  端口 8000 (后端): $(lsof -i :8000 | wc -l | tr -d ' ') 个进程"
echo -e "  端口 8080 (前端): $(lsof -i :8080 | wc -l | tr -d ' ') 个进程"

# 检查日志文件
echo -e "${CYAN}📋 日志文件状态:${NC}"
if [ -d "backend/logs" ] && [ "$(ls -A backend/logs 2>/dev/null)" ]; then
    echo -e "  ${GREEN}✅ 日志目录存在且有日志文件${NC}"
    LATEST_LOG=$(ls -t backend/logs/*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        LOG_SIZE=$(du -h "$LATEST_LOG" | cut -f1)
        echo -e "  最新日志: $LATEST_LOG (大小: $LOG_SIZE)${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠️  日志目录不存在或为空${NC}"
fi

# 检查上传目录
echo -e "${CYAN}📋 上传目录状态:${NC}"
if [ -d "backend/uploads" ]; then
    UPLOAD_COUNT=$(find backend/uploads -type f | wc -l | tr -d ' ')
    echo -e "  ${GREEN}✅ 上传目录存在 (文件数量: $UPLOAD_COUNT)${NC}"
else
    echo -e "  ${YELLOW}⚠️  上传目录不存在${NC}"
fi

echo ""
echo -e "${BLUE}📊 系统资源使用情况:${NC}"
echo "=================================="

# 检查内存使用
if command -v free &> /dev/null; then
    MEMORY_INFO=$(free -h | grep "Mem:")
    echo -e "内存使用: $MEMORY_INFO"
fi

# 检查磁盘使用
if command -v df &> /dev/null; then
    DISK_INFO=$(df -h . | tail -1)
    echo -e "磁盘使用: $DISK_INFO"
fi

# 检查Python进程
echo -e "${CYAN}📋 Python进程:${NC}"
PYTHON_COUNT=$(ps aux | grep python | grep -v grep | wc -l | tr -d ' ')
echo -e "  运行中的Python进程: $PYTHON_COUNT 个"

# 检查Node.js进程
echo -e "${CYAN}📋 Node.js进程:${NC}"
NODE_COUNT=$(ps aux | grep node | grep -v grep | wc -l | tr -d ' ')
echo -e "  运行中的Node.js进程: $NODE_COUNT 个"

echo ""
echo -e "${BLUE}💡 快速启动命令:${NC}"
echo "=================================="
echo -e "一键启动所有服务: ${GREEN}./start-all.sh${NC}"
echo -e "单独启动后端: ${GREEN}cd backend && ./start-dev.sh${NC}"
echo -e "查看后端日志: ${GREEN}tail -f backend/logs/backend.log${NC}"
echo -e "查看前端日志: ${GREEN}tail -f backend/logs/frontend.log${NC}"
echo -e "查看Docker日志: ${GREEN}cd backend && docker compose logs -f${NC}"
echo -e "检查API健康: ${GREEN}curl http://localhost:8000/health${NC}"
echo ""

echo -e "${BLUE}🎯 系统状态总结:${NC}"
echo "=================================="

# 计算健康状态
HEALTH_SCORE=0
TOTAL_CHECKS=6

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    ((HEALTH_SCORE++))
fi

if curl -s http://localhost:8080 > /dev/null 2>&1; then
    ((HEALTH_SCORE++))
fi

if docker exec zhizhentong_postgres pg_isready -U postgres -d zhizhentong > /dev/null 2>&1; then
    ((HEALTH_SCORE++))
fi

if [ -d "backend/logs" ] && [ "$(ls -A backend/logs 2>/dev/null)" ]; then
    ((HEALTH_SCORE++))
fi

if [ -d "backend/uploads" ]; then
    ((HEALTH_SCORE++))
fi

if [ -d "../frontend/node_modules" ]; then
    ((HEALTH_SCORE++))
fi

HEALTH_PERCENT=$((HEALTH_SCORE * 100 / TOTAL_CHECKS))

if [ $HEALTH_PERCENT -ge 80 ]; then
    echo -e "${GREEN}✅ 系统状态良好 ($HEALTH_PERCENT%)${NC}"
elif [ $HEALTH_PERCENT -ge 60 ]; then
    echo -e "${YELLOW}⚠️  系统状态一般 ($HEALTH_PERCENT%)${NC}"
else
    echo -e "${RED}❌ 系统状态较差 ($HEALTH_PERCENT%)${NC}"
fi

echo -e "健康检查通过: $HEALTH_SCORE/$TOTAL_CHECKS"
echo ""
