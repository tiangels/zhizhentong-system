# 智诊通系统 Docker 容器化部署完整指南

## 目录

1. [系统概述](#系统概述)
2. [Docker 环境要求](#docker环境要求)
3. [项目结构说明](#项目结构说明)
4. [基础服务配置](#基础服务配置)
5. [应用服务配置](#应用服务配置)
6. [部署架构说明](#部署架构说明)
7. [本地启动指南](#本地启动指南)
8. [生产环境部署](#生产环境部署)
9. [服务监控与维护](#服务监控与维护)
10. [故障排除](#故障排除)

## 系统概述

智诊通系统是一个基于 Docker 容器化部署的智能医疗诊断平台，采用微服务架构，包含以下核心组件：

### 核心服务

- **后端 API 服务**: 基于 FastAPI 的 RESTful API 服务
- **向量化服务**: 多模态数据向量化处理服务
- **智能诊断服务**: AI 模型推理服务
- **数据库服务**: PostgreSQL 关系型数据库
- **缓存服务**: Redis 内存数据库
- **搜索引擎**: Elasticsearch 全文搜索引擎
- **消息队列**: RabbitMQ 异步消息处理
- **向量数据库**: ChromaDB 向量存储

### 技术栈

- **容器化**: Docker & Docker Compose
- **后端框架**: FastAPI (Python 3.11)
- **数据库**: PostgreSQL 14
- **缓存**: Redis 6
- **搜索引擎**: Elasticsearch 8.11.0
- **消息队列**: RabbitMQ 3
- **向量数据库**: ChromaDB
- **反向代理**: Nginx (可选)

## Docker 环境要求

### 系统要求

- **操作系统**: Linux/macOS/Windows (支持 Docker)
- **Docker 版本**: >= 20.10.0
- **Docker Compose 版本**: >= 2.0.0
- **内存**: 最少 8GB，推荐 16GB
- **存储**: 最少 50GB 可用空间
- **CPU**: 最少 4 核心，推荐 8 核心

### 安装 Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# macOS (使用Homebrew)
brew install docker docker-compose

# Windows (下载Docker Desktop)
# https://www.docker.com/products/docker-desktop
```

### 验证安装

```bash
docker --version
docker-compose --version
docker info
```

## 项目结构说明

```
codes/docker/
├── docker-compose.yml              # 主服务编排文件
├── docker-compose.infrastructure.yml  # 基础设施服务编排
├── Dockerfile                      # 通用Docker镜像构建文件
├── Dockerfile.backend              # 后端服务Docker镜像
├── Dockerfile.embedding            # 向量化服务Docker镜像
├── nginx.conf                      # Nginx反向代理配置
├── requirements.txt                # Python依赖包列表
├── start-docker.sh                 # Docker服务启动脚本
├── start-services.sh               # 服务启动脚本
├── logs/                           # 日志目录
├── ssl/                            # SSL证书目录
└── scripts/                        # 初始化脚本目录
    └── init-db.sql/                # 数据库初始化脚本
```

## 基础服务配置

### PostgreSQL 数据库服务

**配置详情**:

- **镜像**: postgres:14-alpine
- **容器名**: zhizhentong_postgres
- **端口**: 5432
- **数据库**: zhizhentong
- **用户名**: zhizhentong
- **密码**: zhizhentong123

**数据持久化**:

```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
  - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
```

**健康检查**:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres -d zhizhentong"]
  interval: 10s
  timeout: 5s
  retries: 5
```

### Redis 缓存服务

**配置详情**:

- **镜像**: redis:6-alpine
- **容器名**: zhizhentong_redis
- **端口**: 6379
- **持久化**: AOF 模式

**配置命令**:

```yaml
command: redis-server --appendonly yes
```

**健康检查**:

```yaml
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s
  timeout: 5s
  retries: 5
```

### Elasticsearch 搜索引擎

**配置详情**:

- **镜像**: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
- **容器名**: zhizhentong_elasticsearch
- **端口**: 9200 (HTTP), 9300 (Transport)
- **内存配置**: 1GB 堆内存

**环境变量**:

```yaml
environment:
  - discovery.type=single-node
  - xpack.security.enabled=false
  - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
  - bootstrap.memory_lock=true
```

**系统限制**:

```yaml
ulimits:
  memlock:
    soft: -1
    hard: -1
```

### Kibana 可视化服务

**配置详情**:

- **镜像**: docker.elastic.co/kibana/kibana:8.11.0
- **容器名**: zhizhentong_kibana
- **端口**: 5601
- **依赖**: Elasticsearch

**环境变量**:

```yaml
environment:
  - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
  - xpack.security.enabled=false
```

### RabbitMQ 消息队列

**配置详情**:

- **镜像**: rabbitmq:3-management-alpine
- **容器名**: zhizhentong_rabbitmq
- **端口**: 5672 (AMQP), 15672 (管理界面)
- **用户名**: zhizhentong
- **密码**: zhizhentong123

**管理界面访问**:

- URL: http://localhost:15672
- 用户名: zhizhentong
- 密码: zhizhentong123

### ChromaDB 向量数据库

**配置详情**:

- **镜像**: chromadb/chroma:latest
- **容器名**: zhizhentong_chromadb
- **端口**: 8003 (映射到容器内 8000)
- **数据持久化**: chromadb_data 卷

**环境变量**:

```yaml
environment:
  - CHROMA_SERVER_HOST=0.0.0.0
  - CHROMA_SERVER_HTTP_PORT=8000
```

**健康检查**:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
```

## 应用服务配置

### 后端 API 服务

**技术栈**:

- **框架**: FastAPI
- **Python 版本**: 3.11
- **端口**: 8000
- **工作目录**: /app

**Dockerfile 配置**:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update --fix-missing && apt-get install -y \
    build-essential curl git libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用文件
COPY backend/app/ ./app/
COPY common/ ./common/

# 创建目录和设置权限
RUN mkdir -p /app/logs /app/uploads && chmod -R 755 /app

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 向量化服务

**技术栈**:

- **框架**: FastAPI
- **Python 版本**: 3.11
- **端口**: 8001
- **功能**: 多模态数据向量化处理

**Dockerfile 配置**:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV HF_HUB_DOWNLOAD_TIMEOUT=30

# 安装系统依赖（包含图像处理库）
RUN apt-get update --fix-missing && apt-get install -y \
    build-essential curl git \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 \
    libxrender-dev libgomp1 libgcc-s1 gcc g++ libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY ai_models/embedding_models/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制服务文件
COPY ai_models/embedding_models/ ./codes/ai_models/embedding_models/
COPY aimodels/ ./codes/aimodels/
COPY datas/ ./datas/

# 创建目录
RUN mkdir -p /app/logs /app/datas/chroma_db/multimodal /app/uploads

EXPOSE 8000
CMD ["python", "codes/ai_models/embedding_models/api/vectorization_api.py"]
```

## 部署架构说明

### 网络架构

**Docker 网络配置**:

```yaml
networks:
  zhizhentong_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

**服务通信**:

- 所有服务运行在同一 Docker 网络中
- 服务间通过容器名进行通信
- 外部访问通过端口映射

### 数据持久化

**数据卷配置**:

```yaml
volumes:
  postgres_data: # PostgreSQL数据
  redis_data: # Redis数据
  elasticsearch_data: # Elasticsearch数据
  rabbitmq_data: # RabbitMQ数据
  chromadb_data: # ChromaDB数据
```

**数据备份策略**:

- 定期备份 PostgreSQL 数据库
- Redis AOF 持久化
- Elasticsearch 快照备份
- 向量数据定期导出

### 服务依赖关系

```
┌─────────────────┐    ┌─────────────────┐
│   前端应用      │    │   移动端应用    │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
            ┌────────▼────────┐
            │   Nginx反向代理  │
            └─────────┬───────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐ ┌───▼────┐ ┌──────▼──────┐
│ 后端API服务  │ │向量化服务│ │智能诊断服务 │
└───────┬──────┘ └────────┘ └─────────────┘
        │
┌───────▼─────────────────────────────────┐
│           基础服务层                     │
├─────────┬─────────┬─────────┬───────────┤
│PostgreSQL│  Redis  │Elasticsearch│ChromaDB│
└─────────┴─────────┴─────────┴───────────┘
```

### 端口分配

| 服务          | 内部端口   | 外部端口   | 说明        |
| ------------- | ---------- | ---------- | ----------- |
| 后端 API      | 8000       | 8000       | RESTful API |
| 向量化服务    | 8000       | 8001       | 向量化处理  |
| 智能诊断      | 8000       | 8002       | AI 推理服务 |
| PostgreSQL    | 5432       | 5432       | 数据库      |
| Redis         | 6379       | 6379       | 缓存        |
| Elasticsearch | 9200       | 9200       | 搜索引擎    |
| Kibana        | 5601       | 5601       | 可视化      |
| RabbitMQ      | 5672/15672 | 5672/15672 | 消息队列    |
| ChromaDB      | 8000       | 8003       | 向量数据库  |

## 本地启动指南

### 快速启动

**1. 启动基础服务**

```bash
# 进入docker目录
cd codes/docker

# 使用启动脚本
chmod +x start-docker.sh
./start-docker.sh

# 或手动启动
docker-compose up -d
```

**2. 验证服务状态**

```bash
# 查看所有服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f [服务名]

# 检查服务健康状态
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
```

**3. 启动应用服务**

```bash
# 启动后端API服务（本地模式）
cd ../backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 启动向量化服务（本地模式）
cd ../ai_models/embedding_models
python api/vectorization_api.py

# 启动智能诊断服务（本地模式）
cd ../ai_models/diagnosis_models
python api/diagnosis_api.py
```

### 详细启动步骤

**步骤 1: 环境准备**

```bash
# 确保Docker服务运行
sudo systemctl start docker  # Linux
# 或启动Docker Desktop (macOS/Windows)

# 检查Docker版本
docker --version
docker-compose --version
```

**步骤 2: 克隆项目**

```bash
git clone <repository-url>
cd zhi_zhen_tong_system
```

**步骤 3: 配置环境变量**

```bash
# 复制环境变量模板
cp codes/backend/.env.example codes/backend/.env

# 编辑配置文件
vim codes/backend/.env
```

**步骤 4: 启动基础服务**

```bash
cd codes/docker

# 创建必要目录
mkdir -p logs ssl

# 启动所有基础服务
docker-compose up -d postgres redis elasticsearch kibana rabbitmq chromadb

# 等待服务启动完成
sleep 30

# 验证服务状态
docker-compose ps
```

**步骤 5: 初始化数据库**

```bash
# 等待PostgreSQL完全启动
sleep 10

# 运行数据库迁移
cd ../backend
python -m alembic upgrade head

# 或手动初始化
python scripts/init_db.py
```

**步骤 6: 启动应用服务**

**后端 API 服务**:

```bash
cd codes/backend

# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**向量化服务**:

```bash
cd codes/ai_models/embedding_models

# 安装依赖
pip install -r requirements.txt

# 启动服务
python api/vectorization_api.py
```

**智能诊断服务**:

```bash
cd codes/ai_models/diagnosis_models

# 安装依赖
pip install -r requirements.txt

# 启动服务
python api/diagnosis_api.py
```

### 服务访问地址

启动完成后，可以通过以下地址访问各服务：

| 服务          | 访问地址                   | 说明             |
| ------------- | -------------------------- | ---------------- |
| 后端 API      | http://localhost:8000      | RESTful API 接口 |
| API 文档      | http://localhost:8000/docs | Swagger UI       |
| 向量化服务    | http://localhost:8001      | 向量化处理接口   |
| 智能诊断      | http://localhost:8002      | AI 诊断接口      |
| PostgreSQL    | localhost:5432             | 数据库连接       |
| Redis         | localhost:6379             | 缓存服务         |
| Elasticsearch | http://localhost:9200      | 搜索引擎         |
| Kibana        | http://localhost:5601      | 数据可视化       |
| RabbitMQ 管理 | http://localhost:15672     | 消息队列管理     |
| ChromaDB      | http://localhost:8003      | 向量数据库       |

### 开发模式配置

**热重载配置**:

```bash
# 后端服务热重载
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app

# 向量化服务热重载
python api/vectorization_api.py --reload

# 智能诊断服务热重载
python api/diagnosis_api.py --reload
```

**调试模式**:

```bash
# 启用调试日志
export LOG_LEVEL=DEBUG

# 启动调试模式
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

### 常见问题解决

**端口冲突**:

```bash
# 检查端口占用
netstat -tulpn | grep :8000
lsof -i :8000

# 修改端口配置
export PORT=8001
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Docker 服务启动失败**:

```bash
# 查看详细日志
docker-compose logs [服务名]

# 重启服务
docker-compose restart [服务名]

# 清理并重新启动
docker-compose down
docker-compose up -d
```

**数据库连接问题**:

```bash
# 检查PostgreSQL状态
docker exec zhizhentong_postgres pg_isready -U postgres -d zhizhentong

# 查看数据库日志
docker-compose logs postgres

# 重置数据库
docker-compose down -v
docker-compose up -d postgres
```

## 生产环境部署

### 生产环境配置

**环境变量配置**:

```bash
# 生产环境变量
export ENVIRONMENT=production
export DEBUG=false
export LOG_LEVEL=INFO

# 数据库配置
export DATABASE_URL=postgresql://zhizhentong:zhizhentong123@postgres:5432/zhizhentong
export REDIS_URL=redis://redis:6379/0

# 安全配置
export SECRET_KEY=your-production-secret-key
export JWT_SECRET=your-jwt-secret-key
export ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

**Docker Compose 生产配置**:

```yaml
# docker-compose.prod.yml
version: "3.8"
services:
  backend:
    build: .
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: "1.0"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
    restart: unless-stopped
```

### 安全配置

**SSL/TLS 配置**:

```bash
# 生成SSL证书
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/nginx.key \
  -out ssl/nginx.crt
```

**防火墙配置**:

```bash
# 只开放必要端口
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

**Docker 安全配置**:

```yaml
services:
  backend:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /var/tmp
    user: "1000:1000"
```

### 监控和日志

**日志配置**:

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**健康检查**:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**监控配置**:

```yaml
# 添加Prometheus监控
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin123
```

## 服务监控与维护

### 服务状态监控

**查看服务状态**:

```bash
# 查看所有服务状态
docker-compose ps

# 查看服务资源使用情况
docker stats

# 查看服务日志
docker-compose logs -f --tail=100 [服务名]

# 查看服务健康状态
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}"
```

**服务重启和更新**:

```bash
# 重启单个服务
docker-compose restart [服务名]

# 重启所有服务
docker-compose restart

# 更新服务镜像
docker-compose pull [服务名]
docker-compose up -d [服务名]

# 滚动更新
docker-compose up -d --no-deps [服务名]
```

### 数据备份

**PostgreSQL 备份**:

```bash
# 创建备份
docker exec zhizhentong_postgres pg_dump -U zhizhentong zhizhentong > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复备份
docker exec -i zhizhentong_postgres psql -U zhizhentong zhizhentong < backup.sql
```

**Redis 备份**:

```bash
# 创建Redis备份
docker exec zhizhentong_redis redis-cli BGSAVE

# 复制备份文件
docker cp zhizhentong_redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d_%H%M%S).rdb
```

**Elasticsearch 备份**:

```bash
# 创建快照仓库
curl -X PUT "localhost:9200/_snapshot/backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/usr/share/elasticsearch/backup"
  }
}'

# 创建快照
curl -X PUT "localhost:9200/_snapshot/backup/snapshot_$(date +%Y%m%d_%H%M%S)"
```

### 性能优化

**Docker 资源限制**:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "1.0"
        reservations:
          memory: 1G
          cpus: "0.5"
```

**数据库优化**:

```yaml
postgres:
  environment:
    - POSTGRES_SHARED_BUFFERS=256MB
    - POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
    - POSTGRES_WORK_MEM=4MB
```

**Redis 优化**:

```yaml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

## 故障排除

### 常见问题

**1. 服务启动失败**

```bash
# 查看详细错误日志
docker-compose logs [服务名]

# 检查端口占用
netstat -tulpn | grep :8000

# 检查磁盘空间
df -h

# 检查内存使用
free -h
```

**2. 数据库连接问题**

```bash
# 检查PostgreSQL状态
docker exec zhizhentong_postgres pg_isready -U postgres -d zhizhentong

# 查看数据库连接
docker exec zhizhentong_postgres psql -U zhizhentong -d zhizhentong -c "SELECT * FROM pg_stat_activity;"

# 重置数据库连接
docker-compose restart postgres
```

**3. 内存不足问题**

```bash
# 检查内存使用
docker stats --no-stream

# 清理未使用的容器和镜像
docker system prune -a

# 增加交换空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**4. 网络连接问题**

```bash
# 检查Docker网络
docker network ls
docker network inspect zhizhentong_zhizhentong_network

# 测试服务间连通性
docker exec zhizhentong_backend ping postgres
docker exec zhizhentong_backend ping redis
```

### 日志分析

**应用日志**:

```bash
# 查看应用日志
docker-compose logs -f backend

# 过滤错误日志
docker-compose logs backend | grep ERROR

# 查看最近100行日志
docker-compose logs --tail=100 backend
```

**系统日志**:

```bash
# 查看Docker守护进程日志
sudo journalctl -u docker.service

# 查看系统资源使用
top
htop
iostat
```

### 性能调优

**数据库性能调优**:

```sql
-- 查看慢查询
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

-- 查看索引使用情况
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes ORDER BY idx_scan DESC;
```

**Redis 性能调优**:

```bash
# 查看Redis统计信息
docker exec zhizhentong_redis redis-cli INFO stats

# 查看内存使用
docker exec zhizhentong_redis redis-cli INFO memory

# 查看慢查询
docker exec zhizhentong_redis redis-cli SLOWLOG GET 10
```

**应用性能监控**:

```bash
# 使用htop监控进程
htop

# 监控网络连接
netstat -tulpn

# 监控磁盘IO
iotop
```

### 紧急恢复

**服务快速恢复**:

```bash
# 停止所有服务
docker-compose down

# 清理资源
docker system prune -f

# 重新启动服务
docker-compose up -d

# 检查服务状态
docker-compose ps
```

**数据恢复**:

```bash
# 从备份恢复数据库
docker exec -i zhizhentong_postgres psql -U zhizhentong zhizhentong < backup.sql

# 恢复Redis数据
docker cp redis_backup.rdb zhizhentong_redis:/data/dump.rdb
docker-compose restart redis
```

---

## 总结

本指南提供了智诊通系统 Docker 容器化部署的完整解决方案，包括：

1. **系统架构设计**: 微服务架构，容器化部署
2. **基础服务配置**: 数据库、缓存、搜索引擎等
3. **应用服务部署**: 后端 API、向量化服务、智能诊断服务
4. **本地开发环境**: 快速启动和开发配置
5. **生产环境部署**: 安全配置和性能优化
6. **监控和维护**: 日志管理、数据备份、性能监控
7. **故障排除**: 常见问题解决方案

通过遵循本指南，您可以成功部署和维护智诊通系统的 Docker 容器化环境。

---

**文档版本**: v1.0  
**最后更新**: 2024 年 12 月  
**维护团队**: 智诊通开发团队
