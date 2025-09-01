#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 智诊通系统一键启动脚本${NC}"
echo "=================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查必要的命令
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ 命令 '$1' 未找到，请先安装${NC}"
        exit 1
    fi
}

echo -e "${CYAN}🔍 检查系统环境...${NC}"
check_command "python3"
check_command "node"
check_command "npm"
check_command "curl"
check_command "docker"

# 检查 Docker Compose（支持新旧版本）
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo -e "${RED}❌ Docker Compose 未找到，请先安装${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 系统环境检查通过${NC}"
echo ""

# 创建必要的目录
echo -e "${CYAN}📁 创建必要的目录...${NC}"
mkdir -p backend/logs
mkdir -p backend/uploads
mkdir -p ../frontend/node_modules
echo -e "${GREEN}✅ 目录创建完成${NC}"
echo ""

# 启动 Docker 服务
echo -e "${CYAN}🐳 启动 Docker 服务...${NC}"
cd backend

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 服务未运行，请先启动 Docker${NC}"
    exit 1
fi

# 启动 Docker Compose 服务
echo -e "${YELLOW}🔄 启动数据库和缓存服务...${NC}"
$DOCKER_COMPOSE_CMD up -d postgres redis rabbitmq

# 等待服务启动
echo -e "${YELLOW}⏳ 等待数据库服务启动...${NC}"
sleep 10

# 检查 PostgreSQL 是否就绪
echo -e "${YELLOW}🔍 检查 PostgreSQL 连接...${NC}"
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker exec zhizhentong_postgres pg_isready -U postgres -d zhizhentong > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL 数据库就绪${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo -e "${YELLOW}⏳ 等待 PostgreSQL 启动... ($attempt/$max_attempts)${NC}"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ PostgreSQL 启动超时${NC}"
    exit 1
fi

# 检查 Redis 是否就绪
echo -e "${YELLOW}🔍 检查 Redis 连接...${NC}"
if docker exec zhizhentong_redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis 缓存就绪${NC}"
else
    echo -e "${YELLOW}⚠️  Redis 可能还在启动中${NC}"
fi

cd ..
echo -e "${GREEN}✅ Docker 服务启动完成${NC}"
echo ""

# 检查并安装后端依赖
echo -e "${CYAN}📦 检查后端依赖...${NC}"
if [ ! -f "backend/requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt 文件不存在${NC}"
    exit 1
fi

if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}⚠️  虚拟环境不存在，正在创建...${NC}"
    cd backend
    python3 -m venv venv
    echo -e "${GREEN}✅ 虚拟环境创建完成${NC}"
    cd ..
fi

# 激活虚拟环境
echo -e "${YELLOW}🔄 激活虚拟环境...${NC}"
cd backend
source venv/bin/activate

# 安装Python依赖
echo -e "${YELLOW}📥 安装Python依赖...${NC}"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Python依赖安装失败${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python依赖安装完成${NC}"

# 检查并安装前端依赖
echo -e "${CYAN}📦 检查前端依赖...${NC}"
cd ../frontend

if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ package.json 文件不存在${NC}"
    exit 1
fi

if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
    echo -e "${YELLOW}⚠️  前端依赖未安装，正在安装...${NC}"
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 前端依赖安装失败${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ 前端依赖安装完成${NC}"
else
    echo -e "${GREEN}✅ 前端依赖已安装${NC}"
fi

# 返回后端目录
cd ../backend

# 数据库已通过 Docker Compose 和 init-db.sql 自动初始化
echo -e "${CYAN}🗄️  数据库状态...${NC}"
echo -e "${GREEN}✅ PostgreSQL 数据库已通过 Docker 初始化${NC}"

# 启动后端服务
echo -e "${CYAN}🚀 启动后端服务...${NC}"
echo -e "${YELLOW}💡 后端服务将在后台启动，端口: 8000${NC}"
echo -e "${YELLOW}💡 可以通过 ./status.sh 查看服务状态${NC}"
echo ""

# 设置环境变量
export DATABASE_URL="postgresql://zhizhentong:zhizhentong123@localhost:5432/zhizhentong"
export REDIS_URL="redis://localhost:6379/0"
export RABBITMQ_URL="amqp://zhizhentong:zhizhentong123@localhost:5672/"
export DEBUG="true"
export LOG_LEVEL="INFO"
export VECTOR_DB_TYPE="none"

# 在后台启动后端服务
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &
BACKEND_PID=$!

# 等待后端服务启动
echo -e "${YELLOW}⏳ 等待后端服务启动...${NC}"
sleep 5

# 检查后端服务是否启动成功
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 后端服务启动成功${NC}"
else
    echo -e "${RED}❌ 后端服务启动失败，请检查日志: logs/backend.log${NC}"
    exit 1
fi

# 启动前端服务
echo -e "${CYAN}🚀 启动前端服务...${NC}"
echo -e "${YELLOW}💡 前端服务将在后台启动，端口: 8080${NC}"
echo ""

cd ../frontend

# 在后台启动前端服务
nohup npm run dev > ../backend/logs/frontend.log 2>&1 &
FRONTEND_PID=$!

# 等待前端服务启动
echo -e "${YELLOW}⏳ 等待前端服务启动...${NC}"
sleep 10

# 检查前端服务是否启动成功
if curl -s http://localhost:8080 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 前端服务启动成功${NC}"
else
    echo -e "${YELLOW}⚠️  前端服务可能还在启动中，请稍后检查${NC}"
fi

# 返回后端目录
cd ../backend

# 保存进程ID到文件
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo ""
echo -e "${BLUE}🎉 智诊通系统启动完成！${NC}"
echo "=================================="
echo -e "${GREEN}✅ 后端API服务: http://localhost:8000${NC}"
echo -e "${GREEN}✅ 前端界面: http://localhost:8080${NC}"
echo -e "${GREEN}✅ API文档: http://localhost:8000/docs${NC}"
echo -e "${GREEN}✅ 健康检查: http://localhost:8000/health${NC}"
echo ""

echo -e "${BLUE}📋 常用命令:${NC}"
echo "=================================="
echo -e "查看系统状态: ${GREEN}./status.sh${NC}"
echo -e "查看后端日志: ${GREEN}tail -f backend/logs/backend.log${NC}"
echo -e "查看前端日志: ${GREEN}tail -f backend/logs/frontend.log${NC}"
echo -e "查看Docker日志: ${GREEN}cd backend && docker compose logs -f${NC}"
echo -e "停止所有服务: ${GREEN}./stop-all.sh${NC}"
echo ""

echo -e "${BLUE}🔍 服务状态检查:${NC}"
echo "=================================="
# 运行状态检查
./status.sh

echo ""
echo -e "${YELLOW}💡 提示: 所有服务已在后台启动，可以关闭此终端${NC}"
echo -e "${YELLOW}💡 如需停止服务，请运行: ./stop-all.sh${NC}"
