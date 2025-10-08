#!/bin/bash

# 智诊通系统一键启动脚本 - 正确的启动顺序
# 启动顺序：向量化服务 → RAG服务 → 后端服务 → 前端服务

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

# 初始化conda环境
echo -e "${YELLOW}🔄 初始化conda环境...${NC}"

# 尝试多种conda路径
CONDA_PATHS=(
    "$HOME/miniconda3/etc/profile.d/conda.sh"
    "$HOME/anaconda3/etc/profile.d/conda.sh"
    "/opt/miniconda3/etc/profile.d/conda.sh"
    "/opt/anaconda3/etc/profile.d/conda.sh"
    "/usr/local/miniconda3/etc/profile.d/conda.sh"
    "/usr/local/anaconda3/etc/profile.d/conda.sh"
)

CONDA_INIT_FOUND=false
for conda_path in "${CONDA_PATHS[@]}"; do
    if [ -f "$conda_path" ]; then
        source "$conda_path"
        CONDA_INIT_FOUND=true
        echo -e "${GREEN}✅ conda环境初始化成功 (路径: $conda_path)${NC}"
        break
    fi
done

if [ "$CONDA_INIT_FOUND" = false ]; then
    echo -e "${RED}❌ conda未安装或未正确配置${NC}"
    echo -e "${YELLOW}💡 请先安装conda: https://docs.conda.io/en/latest/miniconda.html${NC}"
    echo -e "${YELLOW}💡 或者确保conda在PATH中可用${NC}"
    exit 1
fi

# 检查必要的命令
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ 命令 '$1' 未找到，请先安装${NC}"
        exit 1
    fi
}

echo -e "${CYAN}🔍 检查系统环境...${NC}"
check_command "/opt/anaconda3/bin/conda run -n nlp python"
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

echo -e "${CYAN}🚀 智诊通系统启动脚本${NC}"
echo -e "${CYAN}================================${NC}"
echo -e "${YELLOW}启动顺序: Docker客户端 → Docker基础服务 → 向量化服务 → 知识检索服务 → 智能诊断服务 → 后端服务 → 前端服务${NC}"
echo ""

# 创建必要的目录
echo -e "${CYAN}📁 创建必要的目录...${NC}"
mkdir -p logs
mkdir -p backend/logs
mkdir -p backend/uploads
echo -e "${GREEN}✅ 目录创建完成${NC}"
echo ""

# 函数：检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ 端口 $port 已被占用${NC}"
        return 1
    else
        echo -e "${GREEN}✅ 端口 $port 可用${NC}"
        return 0
    fi
}

# 函数：等待服务启动
wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=$3
    local sleep_time=$4
    
    echo -e "${YELLOW}⏳ 等待 $service_name 启动...${NC}"
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name 启动成功${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        echo -e "${YELLOW}⏳ 等待 $service_name 启动... ($attempt/$max_attempts)${NC}"
        sleep $sleep_time
    done
    
    echo -e "${RED}❌ $service_name 启动超时${NC}"
    return 1
}

# 函数：启动Docker客户端
start_docker_desktop() {
    echo -e "${CYAN}🐳 启动Docker Desktop...${NC}"
    
    # 检查Docker是否已经运行
    if docker info > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker Desktop 已在运行${NC}"
        return 0
    fi
    
    # 检查操作系统
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo -e "${YELLOW}🚀 启动Docker Desktop (macOS)...${NC}"
        
        # 检查Docker Desktop是否已安装
        if [ -d "/Applications/Docker.app" ]; then
            # 启动Docker Desktop
            open -a Docker
            echo -e "${YELLOW}⏳ 等待Docker Desktop启动...${NC}"
            
            # 等待Docker启动（最多等待60秒）
            max_attempts=60
            attempt=0
            while [ $attempt -lt $max_attempts ]; do
                if docker info > /dev/null 2>&1; then
                    echo -e "${GREEN}✅ Docker Desktop 启动成功${NC}"
                    return 0
                fi
                attempt=$((attempt + 1))
                echo -e "${YELLOW}⏳ 等待Docker启动... ($attempt/$max_attempts)${NC}"
                sleep 1
            done
            
            echo -e "${RED}❌ Docker Desktop 启动超时${NC}"
            echo -e "${YELLOW}💡 请手动启动Docker Desktop后重新运行脚本${NC}"
            exit 1
        else
            echo -e "${RED}❌ Docker Desktop 未安装${NC}"
            echo -e "${YELLOW}💡 请从 https://www.docker.com/products/docker-desktop 下载并安装Docker Desktop${NC}"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo -e "${YELLOW}🚀 启动Docker服务 (Linux)...${NC}"
        
        # 检查Docker服务状态
        if systemctl is-active --quiet docker; then
            echo -e "${GREEN}✅ Docker服务已在运行${NC}"
            return 0
        fi
        
        # 启动Docker服务
        echo -e "${YELLOW}🔄 启动Docker服务...${NC}"
        sudo systemctl start docker
        
        # 等待Docker启动
        sleep 3
        
        if docker info > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Docker服务启动成功${NC}"
            return 0
        else
            echo -e "${RED}❌ Docker服务启动失败${NC}"
            echo -e "${YELLOW}💡 请检查Docker安装和权限设置${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ 不支持的操作系统: $OSTYPE${NC}"
        echo -e "${YELLOW}💡 请手动启动Docker后重新运行脚本${NC}"
        exit 1
    fi
}

# 函数：启动Docker服务
start_docker_services() {
    echo -e "${CYAN}🐳 启动Docker基础服务...${NC}"
    echo -e "${YELLOW}启动PostgreSQL、Redis、RabbitMQ...${NC}"
    
    cd docker
    
    # 检查Docker是否运行
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker服务未运行，请先启动Docker${NC}"
        exit 1
    fi
    
    # 启动Docker Compose基础设施服务
    $DOCKER_COMPOSE_CMD -f docker-compose.infrastructure.yml up -d
    
    # 等待数据库服务启动
    echo -e "${YELLOW}⏳ 等待数据库服务启动...${NC}"
    sleep 15
    
    # 检查PostgreSQL是否就绪
    echo -e "${YELLOW}🔍 检查PostgreSQL连接...${NC}"
    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if docker exec zhizhentong_postgres pg_isready -U postgres -d zhizhentong > /dev/null 2>&1; then
            echo -e "${GREEN}✅ PostgreSQL数据库就绪${NC}"
            break
        fi
        attempt=$((attempt + 1))
        echo -e "${YELLOW}⏳ 等待PostgreSQL启动... ($attempt/$max_attempts)${NC}"
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}❌ PostgreSQL启动超时${NC}"
        exit 1
    fi
    
    # 检查Redis是否就绪
    echo -e "${YELLOW}🔍 检查Redis连接...${NC}"
    if docker exec zhizhentong_redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis缓存就绪${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis可能还在启动中${NC}"
    fi
    
    # 检查Elasticsearch是否就绪
    echo -e "${YELLOW}🔍 检查Elasticsearch连接...${NC}"
    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Elasticsearch搜索引擎就绪${NC}"
            break
        fi
        attempt=$((attempt + 1))
        echo -e "${YELLOW}⏳ 等待Elasticsearch启动... ($attempt/$max_attempts)${NC}"
        sleep 3
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${YELLOW}⚠️  Elasticsearch启动可能较慢，继续启动其他服务${NC}"
    fi
    
    cd ..
    echo -e "${GREEN}✅ Docker服务启动完成${NC}"
    echo ""
}

# 函数：启动向量化服务
start_vectorization_service() {
    echo -e "${CYAN}🔧 启动向量化服务 (端口 8001)...${NC}"
    echo -e "${YELLOW}--------------------------------${NC}"
    
    if ! check_port 8001; then
        echo -e "${RED}❌ 无法启动向量化服务，端口8001被占用${NC}"
        return 1
    fi
    
    cd services/embedding_service
    
    # 启动向量化服务（使用 Python 脚本）
    echo -e "${YELLOW}🚀 启动向量化服务...${NC}"
    nohup python start_embedding_service.py > ../../logs/embedding_service.log 2>&1 &
    VECTORIZATION_PID=$!
    echo -e "${GREEN}✅ 向量化服务已启动 (PID: $VECTORIZATION_PID)${NC}"
    
    cd ../..
    
    # 等待向量化服务启动
    if wait_for_service "向量化服务" "http://localhost:8001/health" 30 3; then
        return 0
    else
        echo -e "${YELLOW}💡 检查日志: logs/embedding_service.log${NC}"
        return 1
    fi
}

# 函数：启动ES检索服务
start_es_service() { return 0; }

# 函数：启动混合检索服务
start_hybrid_service() { return 0; }

# 函数：启动知识检索服务
start_rag_service() {
    echo -e "${CYAN}🔧 启动知识检索服务 (端口 8002)...${NC}"
    echo -e "${YELLOW}--------------------------------${NC}"
    
    if ! check_port 8002; then
        echo -e "${RED}❌ 无法启动知识检索服务，端口8002被占用${NC}"
        return 1
    fi
    
    cd services/knowledge_retrieval_service
    
    # 检查启动脚本是否存在
    if [ ! -f "start_retrieval_service.py" ]; then
        echo -e "${RED}❌ 知识检索服务启动脚本不存在${NC}"
        cd ../..
        return 1
    fi
    
    # 启动知识检索服务
    echo -e "${YELLOW}🚀 启动知识检索服务...${NC}"
    nohup python start_retrieval_service.py > ../../logs/retrieval_service.log 2>&1 &
    RAG_PID=$!
    echo -e "${GREEN}✅ 知识检索服务已启动 (PID: $RAG_PID)${NC}"
    
    cd ../..
    
    # 等待知识检索服务启动
    if wait_for_service "知识检索服务" "http://localhost:8002/health" 30 3; then
        return 0
    else
        echo -e "${YELLOW}💡 检查日志: logs/retrieval_service.log${NC}"
        return 1
    fi
}

# 函数：启动智能诊断服务
start_diagnosis_service() {
    echo -e "${CYAN}🔧 启动智能诊断服务 (端口 8003)...${NC}"
    echo -e "${YELLOW}--------------------------------${NC}"
    
    if ! check_port 8003; then
        echo -e "${RED}❌ 无法启动智能诊断服务，端口8003被占用${NC}"
        return 1
    fi
    
    cd services/intelligent_diagnosis_service
    
    # 检查启动脚本是否存在
    if [ ! -f "start_diagnosis_service.py" ]; then
        echo -e "${RED}❌ 智能诊断服务启动脚本不存在${NC}"
        cd ../..
        return 1
    fi
    
    # 启动智能诊断服务
    echo -e "${YELLOW}🚀 启动智能诊断服务...${NC}"
    nohup python start_diagnosis_service.py > ../../logs/diagnosis_service.log 2>&1 &
    DIAGNOSIS_PID=$!
    echo -e "${GREEN}✅ 智能诊断服务已启动 (PID: $DIAGNOSIS_PID)${NC}"
    
    cd ../..
    
    # 等待智能诊断服务启动
    if wait_for_service "智能诊断服务" "http://localhost:8003/diagnosis/health" 30 3; then
        return 0
    else
        echo -e "${YELLOW}💡 检查日志: logs/diagnosis_service.log${NC}"
        return 1
    fi
}

# 函数：启动后端服务
start_backend_service() {
    echo -e "${CYAN}🔧 启动后端API服务 (端口 8000)...${NC}"
    echo -e "${YELLOW}--------------------------------${NC}"
    
    if ! check_port 8000; then
        echo -e "${RED}❌ 无法启动后端服务，端口8000被占用${NC}"
        return 1
    fi
    
    cd backend
    
    # 检查conda环境
    if ! /opt/anaconda3/bin/conda info --envs | grep -q "nlp"; then
        echo -e "${RED}❌ conda nlp环境不存在${NC}"
        echo -e "${YELLOW}💡 创建命令: /opt/anaconda3/bin/conda create -n nlp python=3.11${NC}"
        cd ..
        return 1
    fi
    
    # 检查并安装后端依赖
    echo -e "${CYAN}📦 检查后端依赖...${NC}"
    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}❌ requirements.txt 文件不存在${NC}"
        cd ..
        return 1
    fi
    
    # 激活conda环境
    echo -e "${YELLOW}🔄 激活conda nlp环境...${NC}"
    eval "$(/opt/anaconda3/bin/conda shell.bash hook)"
    conda activate nlp
    
    # 安装Python依赖
    echo -e "${YELLOW}📥 安装Python依赖...${NC}"
    
    # 设置环境变量以避免编译问题
    export GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=1
    export GRPC_PYTHON_BUILD_SYSTEM_ZLIB=1
    
    # 先尝试安装预编译的包
    pip install --upgrade pip
    echo -e "${YELLOW}📦 检查已安装的包...${NC}"
    pip install --only-binary=all -r requirements.txt 2>/dev/null || {
        echo -e "${YELLOW}⚠️  预编译包安装失败，跳过有问题的包...${NC}"
        # 跳过有编译问题的包，安装其他包
        pip install fastapi uvicorn sqlalchemy psycopg2-binary redis alembic python-jose passlib python-multipart pydantic pydantic-settings email-validator httpx aiohttp loguru prometheus-client python-dotenv pytz celery kombu pytest pytest-asyncio black isort flake8 mkdocs mkdocs-material 2>/dev/null || true
    }
    
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️  Python依赖安装可能有问题，但继续启动服务${NC}"
        echo -e "${YELLOW}💡 建议手动检查依赖: pip install -r requirements.txt${NC}"
    else
        echo -e "${GREEN}✅ Python依赖安装完成${NC}"
    fi
    
    # 设置环境变量
    export DATABASE_URL="postgresql://zhizhentong:zhizhentong123@localhost:5432/zhizhentong"
    export REDIS_URL="redis://localhost:6379/0"
    export RABBITMQ_URL="amqp://zhizhentong:zhizhentong123@localhost:5672/"
    export ELASTICSEARCH_URL="http://localhost:9200"
    export CHROMADB_URL="http://localhost:8004"
    export DEBUG="true"
    export LOG_LEVEL="INFO"
    export VECTOR_DB_TYPE="chromadb"
    
    # 启动后端服务
    echo -e "${YELLOW}🚀 启动后端服务...${NC}"
    nohup /opt/anaconda3/bin/conda run -n nlp python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo -e "${GREEN}✅ 后端服务已启动 (PID: $BACKEND_PID)${NC}"
    
    cd ..
    
    # 等待后端服务启动
    if wait_for_service "后端服务" "http://localhost:8000/health" 30 3; then
        return 0
    else
        echo -e "${YELLOW}💡 检查日志: logs/backend.log${NC}"
        return 1
    fi
}

# 函数：启动前端服务
start_frontend_service() {
    echo -e "${CYAN}🔧 启动前端服务 (端口 8080)...${NC}"
    echo -e "${YELLOW}--------------------------------${NC}"
    
    if ! check_port 8080; then
        echo -e "${RED}❌ 无法启动前端服务，端口8080被占用${NC}"
        return 1
    fi
    
    cd frontend
    
    # 检查package.json是否存在
    if [ ! -f "package.json" ]; then
        echo -e "${RED}❌ package.json文件不存在${NC}"
        cd ..
        return 1
    fi
    
    # 检查node_modules是否存在
    if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
        echo -e "${YELLOW}⚠️  前端依赖未安装，正在安装...${NC}"
        npm install
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ 前端依赖安装失败${NC}"
            cd ..
            return 1
        fi
        echo -e "${GREEN}✅ 前端依赖安装完成${NC}"
    else
        echo -e "${GREEN}✅ 前端依赖已安装${NC}"
    fi
    
    # 启动前端服务
    echo -e "${YELLOW}🚀 启动前端服务...${NC}"
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo -e "${GREEN}✅ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"
    
    cd ..
    
    # 等待前端服务启动
    if wait_for_service "前端服务" "http://localhost:8080" 30 3; then
        return 0
    else
        echo -e "${YELLOW}💡 检查日志: logs/frontend.log${NC}"
        return 1
    fi
}

# 函数：显示服务状态
show_service_status() {
    echo ""
    echo -e "${CYAN}📊 服务状态总览${NC}"
    echo -e "${CYAN}================${NC}"
    
    # 检查各服务状态
    services=(
        "向量化服务:8001:http://localhost:8001/health"
        "知识检索服务:8002:http://localhost:8002/health"
        "智能诊断服务:8003:http://localhost:8003/diagnosis/health"
        "后端服务:8000:http://localhost:8000/health"
        "前端服务:8080:http://localhost:8080"
        "Elasticsearch:9200:http://localhost:9200/_cluster/health"
        "Kibana:5601:http://localhost:5601/api/status"
    )
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r name port url <<< "$service_info"
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $name (端口 $port) - 运行中${NC}"
        else
            echo -e "${RED}❌ $name (端口 $port) - 未运行${NC}"
        fi
    done
    
    echo ""
    echo -e "${YELLOW}💡 访问地址:${NC}"
    echo -e "${BLUE}  前端界面: http://localhost:8080${NC}"
    echo -e "${BLUE}  后端API: http://localhost:8000${NC}"
    echo -e "${BLUE}  API文档: http://localhost:8000/docs${NC}"
    echo -e "${BLUE}  知识检索服务: http://localhost:8002${NC}"
    echo -e "${BLUE}  智能诊断服务: http://localhost:8003${NC}"
    echo -e "${BLUE}  诊断API文档: http://localhost:8003/diagnosis/docs${NC}"
    echo -e "${BLUE}  向量化服务: http://localhost:8001${NC}"
    echo -e "${BLUE}  ChromaDB: http://localhost:8004${NC}"
    echo -e "${BLUE}  Elasticsearch: http://localhost:9200${NC}"
    echo -e "${BLUE}  Kibana: http://localhost:5601${NC}"
    echo ""
}

# 主启动流程
main() {
    echo -e "${YELLOW}开始按正确顺序启动智诊通系统...${NC}"
    echo ""
    
    # 1. 启动Docker客户端
    start_docker_desktop
    
    # 2. 启动Docker基础服务
    start_docker_services
    
    # 3. 启动向量化服务
    if start_vectorization_service; then
        echo -e "${GREEN}✅ 向量化服务启动成功${NC}"
    else
        echo -e "${RED}❌ 向量化服务启动失败，停止后续服务启动${NC}"
        exit 1
    fi
    
    # 4. 启动知识检索服务
    if start_rag_service; then
        echo -e "${GREEN}✅ 知识检索服务启动成功${NC}"
    else
        echo -e "${RED}❌ 知识检索服务启动失败，停止后续服务启动${NC}"
        exit 1
    fi
    
    # 5. 启动智能诊断服务
    if start_diagnosis_service; then
        echo -e "${GREEN}✅ 智能诊断服务启动成功${NC}"
    else
        echo -e "${RED}❌ 智能诊断服务启动失败，停止后续服务启动${NC}"
        exit 1
    fi
    
    # 6: 不再单独启动 ES/混合检索服务（已并入知识检索服务）
    
    # 7. 启动后端服务
    if start_backend_service; then
        echo -e "${GREEN}✅ 后端服务启动成功${NC}"
    else
        echo -e "${RED}❌ 后端服务启动失败，停止后续服务启动${NC}"
        exit 1
    fi
    
    # 8. 启动前端服务
    if start_frontend_service; then
        echo -e "${GREEN}✅ 前端服务启动成功${NC}"
    else
        echo -e "${YELLOW}⚠️  前端服务启动失败，但其他服务已启动${NC}"
    fi
    
    # 9. 显示服务状态
    show_service_status
    
    echo -e "${GREEN}🎉 智诊通系统启动完成！${NC}"
    echo -e "${YELLOW}💡 使用 ./status.sh 查看服务状态${NC}"
    echo -e "${YELLOW}💡 使用 ./stop-all.sh 停止所有服务${NC}"
}

# 执行主函数
main "$@"
