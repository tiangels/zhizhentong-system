#!/bin/bash

# 智诊通Docker服务启动脚本
# 专门用于启动Docker基础服务（数据库、缓存、搜索引擎等）

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 智诊通Docker服务启动脚本${NC}"
echo "=================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker服务未运行，请先启动Docker${NC}"
    exit 1
fi

# 检查 Docker Compose（支持新旧版本）
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo -e "${RED}❌ Docker Compose 未找到，请先安装${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker环境检查通过${NC}"
echo ""

# 创建必要的目录
echo -e "${CYAN}📁 创建必要的目录...${NC}"
mkdir -p logs
mkdir -p ssl
echo -e "${GREEN}✅ 目录创建完成${NC}"
echo ""

# 启动Docker服务
echo -e "${CYAN}🚀 启动Docker服务...${NC}"
echo -e "${YELLOW}启动服务: PostgreSQL, Redis, RabbitMQ, Elasticsearch, Kibana, ChromaDB${NC}"

# 启动所有服务
$DOCKER_COMPOSE_CMD up -d

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker服务启动成功${NC}"
else
    echo -e "${RED}❌ Docker服务启动失败${NC}"
    exit 1
fi

# 等待服务启动
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 30

# 检查服务状态
echo -e "${CYAN}🔍 检查服务状态...${NC}"

# 检查PostgreSQL
if docker exec zhizhentong_postgres pg_isready -U postgres -d zhizhentong > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL 就绪${NC}"
else
    echo -e "${YELLOW}⚠️  PostgreSQL 可能还在启动中${NC}"
fi

# 检查Redis
if docker exec zhizhentong_redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis 就绪${NC}"
else
    echo -e "${YELLOW}⚠️  Redis 可能还在启动中${NC}"
fi

# 检查Elasticsearch
if curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Elasticsearch 就绪${NC}"
else
    echo -e "${YELLOW}⚠️  Elasticsearch 可能还在启动中${NC}"
fi

# 检查Kibana
if curl -s http://localhost:5601/api/status > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Kibana 就绪${NC}"
else
    echo -e "${YELLOW}⚠️  Kibana 可能还在启动中${NC}"
fi

# 检查ChromaDB
if curl -s http://localhost:8003/api/v1/heartbeat > /dev/null 2>&1; then
    echo -e "${GREEN}✅ ChromaDB 就绪${NC}"
else
    echo -e "${YELLOW}⚠️  ChromaDB 可能还在启动中${NC}"
fi

echo ""
echo -e "${BLUE}🎉 Docker服务启动完成！${NC}"
echo ""
echo -e "${YELLOW}💡 服务访问地址:${NC}"
echo -e "${BLUE}  PostgreSQL: localhost:5432${NC}"
echo -e "${BLUE}  Redis: localhost:6379${NC}"
echo -e "${BLUE}  RabbitMQ: localhost:5672 (管理界面: localhost:15672)${NC}"
echo -e "${BLUE}  Elasticsearch: http://localhost:9200${NC}"
echo -e "${BLUE}  Kibana: http://localhost:5601${NC}"
echo -e "${BLUE}  ChromaDB: http://localhost:8003${NC}"
echo ""
echo -e "${YELLOW}💡 管理命令:${NC}"
echo -e "${GREEN}  查看服务状态: docker-compose ps${NC}"
echo -e "${GREEN}  查看日志: docker-compose logs -f [服务名]${NC}"
echo -e "${GREEN}  停止服务: docker-compose down${NC}"
echo -e "${GREEN}  重启服务: docker-compose restart [服务名]${NC}"
echo ""
