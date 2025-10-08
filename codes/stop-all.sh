#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 智诊通系统停止脚本${NC}"
echo "=================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 停止后端服务
echo -e "${CYAN}🛑 停止后端服务...${NC}"

# 检查是否有进程ID文件
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "  正在停止后端进程 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        sleep 2
        
        # 强制停止如果还在运行
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            echo -e "  强制停止后端进程..."
            kill -9 $BACKEND_PID
        fi
        
        echo -e "${GREEN}✅ 后端服务已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  后端进程已不存在${NC}"
    fi
    rm -f .backend.pid
else
    echo -e "${YELLOW}⚠️  未找到后端进程ID文件${NC}"
fi

# 停止向量化服务
echo -e "${CYAN}🛑 停止向量化服务...${NC}"

# 检查是否有进程ID文件
if [ -f ".vectorization.pid" ]; then
    VECTORIZATION_PID=$(cat .vectorization.pid)
    if ps -p $VECTORIZATION_PID > /dev/null 2>&1; then
        echo -e "  正在停止向量化进程 (PID: $VECTORIZATION_PID)..."
        kill $VECTORIZATION_PID
        sleep 2
        
        # 强制停止如果还在运行
        if ps -p $VECTORIZATION_PID > /dev/null 2>&1; then
            echo -e "  强制停止向量化进程..."
            kill -9 $VECTORIZATION_PID
        fi
        
        echo -e "${GREEN}✅ 向量化服务已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  向量化进程已不存在${NC}"
    fi
    rm -f .vectorization.pid
else
    echo -e "${YELLOW}⚠️  未找到向量化进程ID文件${NC}"
fi

# 停止智能诊断服务
echo -e "${CYAN}🛑 停止智能诊断服务...${NC}"

# 检查是否有进程ID文件
if [ -f ".diagnosis.pid" ]; then
    DIAGNOSIS_PID=$(cat .diagnosis.pid)
    if ps -p $DIAGNOSIS_PID > /dev/null 2>&1; then
        echo -e "  正在停止智能诊断进程 (PID: $DIAGNOSIS_PID)..."
        kill $DIAGNOSIS_PID
        sleep 2
        
        # 强制停止如果还在运行
        if ps -p $DIAGNOSIS_PID > /dev/null 2>&1; then
            echo -e "  强制停止智能诊断进程..."
            kill -9 $DIAGNOSIS_PID
        fi
        
        echo -e "${GREEN}✅ 智能诊断服务已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  智能诊断进程已不存在${NC}"
    fi
    rm -f .diagnosis.pid
else
    echo -e "${YELLOW}⚠️  未找到智能诊断进程ID文件${NC}"
fi

# 停止前端服务
echo -e "${CYAN}🛑 停止前端服务...${NC}"

# 检查是否有进程ID文件
if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "  正在停止前端进程 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        sleep 2
        
        # 强制停止如果还在运行
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            echo -e "  强制停止前端进程..."
            kill -9 $FRONTEND_PID
        fi
        
        echo -e "${GREEN}✅ 前端服务已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  前端进程已不存在${NC}"
    fi
    rm -f .frontend.pid
else
    echo -e "${YELLOW}⚠️  未找到前端进程ID文件${NC}"
fi

# 通过端口查找并停止服务
echo -e "${CYAN}🔍 检查端口占用情况...${NC}"

# 停止占用8000端口的进程
PORT_8000_PIDS=$(lsof -ti:8000 2>/dev/null)
if [ -n "$PORT_8000_PIDS" ]; then
    echo -e "  发现占用8000端口的进程: $PORT_8000_PIDS"
    for pid in $PORT_8000_PIDS; do
        echo -e "  正在停止进程 (PID: $pid)..."
        kill $pid
    done
    sleep 2
    
    # 强制停止如果还在运行
    PORT_8000_PIDS=$(lsof -ti:8000 2>/dev/null)
    if [ -n "$PORT_8000_PIDS" ]; then
        echo -e "  强制停止占用8000端口的进程..."
        for pid in $PORT_8000_PIDS; do
            kill -9 $pid
        done
    fi
    echo -e "${GREEN}✅ 8000端口已释放${NC}"
else
    echo -e "${GREEN}✅ 8000端口未被占用${NC}"
fi

# 停止占用8001端口的进程（向量化服务）
PORT_8001_PIDS=$(lsof -ti:8001 2>/dev/null)
if [ -n "$PORT_8001_PIDS" ]; then
    echo -e "  发现占用8001端口的进程: $PORT_8001_PIDS"
    for pid in $PORT_8001_PIDS; do
        echo -e "  正在停止进程 (PID: $pid)..."
        kill $pid
    done
    sleep 2
    
    # 强制停止如果还在运行
    PORT_8001_PIDS=$(lsof -ti:8001 2>/dev/null)
    if [ -n "$PORT_8001_PIDS" ]; then
        echo -e "  强制停止占用8001端口的进程..."
        for pid in $PORT_8001_PIDS; do
            kill -9 $pid
        done
    fi
    echo -e "${GREEN}✅ 8001端口已释放${NC}"
else
    echo -e "${GREEN}✅ 8001端口未被占用${NC}"
fi

# 停止占用8003端口的进程（智能诊断服务）
PORT_8003_PIDS=$(lsof -ti:8003 2>/dev/null)
if [ -n "$PORT_8003_PIDS" ]; then
    echo -e "  发现占用8003端口的进程: $PORT_8003_PIDS"
    for pid in $PORT_8003_PIDS; do
        echo -e "  正在停止进程 (PID: $pid)..."
        kill $pid
    done
    sleep 2
    
    # 强制停止如果还在运行
    PORT_8003_PIDS=$(lsof -ti:8003 2>/dev/null)
    if [ -n "$PORT_8003_PIDS" ]; then
        echo -e "  强制停止占用8003端口的进程..."
        for pid in $PORT_8003_PIDS; do
            kill -9 $pid
        done
    fi
    echo -e "${GREEN}✅ 8003端口已释放${NC}"
else
    echo -e "${GREEN}✅ 8003端口未被占用${NC}"
fi

# 停止占用8004端口的进程（ChromaDB）
PORT_8004_PIDS=$(lsof -ti:8004 2>/dev/null)
if [ -n "$PORT_8004_PIDS" ]; then
    echo -e "  发现占用8004端口的进程: $PORT_8004_PIDS"
    for pid in $PORT_8004_PIDS; do
        echo -e "  正在停止进程 (PID: $pid)..."
        kill $pid
    done
    sleep 2
    
    # 强制停止如果还在运行
    PORT_8004_PIDS=$(lsof -ti:8004 2>/dev/null)
    if [ -n "$PORT_8004_PIDS" ]; then
        echo -e "  强制停止占用8004端口的进程..."
        for pid in $PORT_8004_PIDS; do
            kill -9 $pid
        done
    fi
    echo -e "${GREEN}✅ 8004端口已释放${NC}"
else
    echo -e "${GREEN}✅ 8004端口未被占用${NC}"
fi

:# 不再单独使用8004/8005端口（ES/混合检索服务已合并）

# 停止占用8080端口的进程
PORT_8080_PIDS=$(lsof -ti:8080 2>/dev/null)
if [ -n "$PORT_8080_PIDS" ]; then
    echo -e "  发现占用8080端口的进程: $PORT_8080_PIDS"
    for pid in $PORT_8080_PIDS; do
        echo -e "  正在停止进程 (PID: $pid)..."
        kill $pid
    done
    sleep 2
    
    # 强制停止如果还在运行
    PORT_8080_PIDS=$(lsof -ti:8080 2>/dev/null)
    if [ -n "$PORT_8080_PIDS" ]; then
        echo -e "  强制停止占用8080端口的进程..."
        for pid in $PORT_8080_PIDS; do
            kill -9 $pid
        done
    fi
    echo -e "${GREEN}✅ 8080端口已释放${NC}"
else
    echo -e "${GREEN}✅ 8080端口未被占用${NC}"
fi

# 停止所有相关的Python和Node.js进程
echo -e "${CYAN}🛑 停止相关进程...${NC}"

# 停止智诊通相关的Python进程
PYTHON_PIDS=$(ps aux | grep "zhizhentong\|uvicorn.*app.main:app\|start_retrieval_service\|start_embedding_service\|start_diagnosis_service" | grep -v grep | awk '{print $2}')
if [ -n "$PYTHON_PIDS" ]; then
    echo -e "  发现智诊通相关Python进程: $PYTHON_PIDS"
    for pid in $PYTHON_PIDS; do
        echo -e "  正在停止Python进程 (PID: $pid)..."
        kill $pid
    done
    sleep 2
    
    # 强制停止如果还在运行
    PYTHON_PIDS=$(ps aux | grep "zhizhentong\|uvicorn.*app.main:app\|start_retrieval_service\|start_embedding_service\|start_diagnosis_service" | grep -v grep | awk '{print $2}')
    if [ -n "$PYTHON_PIDS" ]; then
        echo -e "  强制停止Python进程..."
        for pid in $PYTHON_PIDS; do
            kill -9 $pid
        done
    fi
    echo -e "${GREEN}✅ Python进程已停止${NC}"
else
    echo -e "${GREEN}✅ 未发现相关Python进程${NC}"
fi

# 停止智诊通相关的Node.js进程
NODE_PIDS=$(ps aux | grep "npm.*run.*dev\|vite" | grep -v grep | awk '{print $2}')
if [ -n "$NODE_PIDS" ]; then
    echo -e "  发现智诊通相关Node.js进程: $NODE_PIDS"
    for pid in $NODE_PIDS; do
        echo -e "  正在停止Node.js进程 (PID: $pid)..."
        kill $pid
    done
    sleep 2
    
    # 强制停止如果还在运行
    NODE_PIDS=$(ps aux | grep "npm.*run.*dev\|vite" | grep -v grep | awk '{print $2}')
    if [ -n "$NODE_PIDS" ]; then
        echo -e "  强制停止Node.js进程..."
        for pid in $NODE_PIDS; do
            kill -9 $pid
        done
    fi
    echo -e "${GREEN}✅ Node.js进程已停止${NC}"
else
    echo -e "${GREEN}✅ 未发现相关Node.js进程${NC}"
fi

# 停止 Docker 容器（不停止Docker服务）
echo -e "${CYAN}🐳 停止 Docker 容器...${NC}"
cd docker
if [ -f "docker-compose.yml" ]; then
    # 检查 Docker Compose 命令
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        echo -e "${YELLOW}⚠️  Docker Compose 未找到${NC}"
        cd ..
        return
    fi
    
    echo -e "  正在停止 Docker Compose 容器..."
    $DOCKER_COMPOSE_CMD down
    echo -e "${GREEN}✅ Docker 容器已停止（Docker服务保持运行）${NC}"
else
    echo -e "${YELLOW}⚠️  未找到 docker-compose.yml 文件${NC}"
fi
cd ..

echo ""
echo -e "${BLUE}🔍 最终状态检查:${NC}"
echo "=================================="

# 检查端口占用
echo -e "端口8000: $(lsof -i :8000 | wc -l | tr -d ' ') 个进程"
echo -e "端口8001: $(lsof -i :8001 | wc -l | tr -d ' ') 个进程"
echo -e "端口8002: $(lsof -i :8002 | wc -l | tr -d ' ') 个进程"
echo -e "端口8003: $(lsof -i :8003 | wc -l | tr -d ' ') 个进程"
echo -e "端口8004: $(lsof -i :8004 | wc -l | tr -d ' ') 个进程"
echo -e "端口8080: $(lsof -i :8080 | wc -l | tr -d ' ') 个进程"
echo -e "端口9200: $(lsof -i :9200 | wc -l | tr -d ' ') 个进程"
echo -e "端口5601: $(lsof -i :5601 | wc -l | tr -d ' ') 个进程"

# 检查进程
PYTHON_COUNT=$(ps aux | grep python | grep -v grep | wc -l | tr -d ' ')
NODE_COUNT=$(ps aux | grep node | grep -v grep | wc -l | tr -d ' ')

echo -e "Python进程: $PYTHON_COUNT 个"
echo -e "Node.js进程: $NODE_COUNT 个"

echo ""
echo -e "${BLUE}🎯 停止结果总结:${NC}"
echo "=================================="

if [ $(lsof -i :8000 | wc -l | tr -d ' ') -eq 0 ] && [ $(lsof -i :8001 | wc -l | tr -d ' ') -eq 0 ] && [ $(lsof -i :8002 | wc -l | tr -d ' ') -eq 0 ] && [ $(lsof -i :8003 | wc -l | tr -d ' ') -eq 0 ] && [ $(lsof -i :8004 | wc -l | tr -d ' ') -eq 0 ] && [ $(lsof -i :8080 | wc -l | tr -d ' ') -eq 0 ] && [ $(lsof -i :9200 | wc -l | tr -d ' ') -eq 0 ] && [ $(lsof -i :5601 | wc -l | tr -d ' ') -eq 0 ]; then
    echo -e "${GREEN}✅ 所有服务已成功停止${NC}"
    echo -e "${GREEN}✅ 端口8000、8001、8002、8003、8004、8080、9200和5601已释放${NC}"
else
    echo -e "${YELLOW}⚠️  部分服务可能仍在运行${NC}"
    echo -e "${YELLOW}💡 可以手动检查: lsof -i :8000, lsof -i :8001, lsof -i :8002, lsof -i :8003, lsof -i :8004, lsof -i :8080, lsof -i :9200, lsof -i :5601${NC}"
fi

echo ""
echo -e "${BLUE}💡 重新启动命令:${NC}"
echo "=================================="
echo -e "一键启动所有服务: ${GREEN}./start-all.sh${NC}"
echo -e "单独启动后端: ${GREEN}./start-dev.sh${NC}"
echo -e "单独启动前端: ${GREEN}cd ../frontend && ./start-dev.sh${NC}"
echo -e "查看系统状态: ${GREEN}./status.sh${NC}"
echo ""

echo -e "${YELLOW}💡 提示: 所有服务已停止，Docker服务保持运行，可以安全关闭终端${NC}"
