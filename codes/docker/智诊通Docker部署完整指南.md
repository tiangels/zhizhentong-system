# 智诊通 Docker 部署完整指南

## 📋 目录

- [系统架构](#系统架构)
- [服务列表](#服务列表)
- [快速部署](#快速部署)
- [服务配置](#服务配置)
- [环境变量](#环境变量)
- [数据持久化](#数据持久化)
- [生产环境配置](#生产环境配置)
- [批量向量化处理](#批量向量化处理)
- [监控和维护](#监控和维护)
- [Docker 问题解决方案](#docker-问题解决方案)
- [故障排除](#故障排除)
- [安全配置](#安全配置)

## 🏗️ 系统架构

### 基础服务层

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │      Redis      │    │    RabbitMQ     │
│   (主数据库)     │    │   (缓存服务)     │    │   (消息队列)     │
│   Port: 5432    │    │   Port: 6379    │    │ Port: 5672/15672│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Elasticsearch   │    │     Kibana      │    │    ChromaDB     │
│  (搜索引擎)      │    │   (ES可视化)     │    │  (向量数据库)    │
│  Port: 9200     │    │   Port: 5601    │    │   Port: 8003    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 应用服务层

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   后端API服务    │    │   向量化服务     │    │     Nginx       │
│   (智诊通后端)   │    │  (多模态向量化)  │    │   (反向代理)     │
│   Port: 8000    │    │   Port: 8001    │    │  Port: 80/443   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 服务列表

### 基础服务

- **PostgreSQL** (端口: 5432) - 主数据库，存储用户数据和医疗记录
- **Redis** (端口: 6379) - 缓存服务，提升系统性能
- **RabbitMQ** (端口: 5672, 管理界面: 15672) - 消息队列，处理异步任务
- **Elasticsearch** (端口: 9200) - 搜索引擎，存储和检索医疗数据
- **Kibana** (端口: 5601) - Elasticsearch 可视化界面
- **ChromaDB** (端口: 8003) - 向量数据库，存储向量化数据

### 应用服务

- **后端 API 服务** (端口: 8000) - 智诊通后端 API
- **向量化服务** (端口: 8001) - 多模态向量化服务
- **Nginx** (端口: 80, 443) - 反向代理和负载均衡

## 🚀 快速部署

### 1. 环境准备

```bash
# 检查Docker环境
docker --version
docker compose --version

# 检查系统资源
free -h
df -h
```

### 2. 启动基础服务（推荐）

```bash
# 进入docker目录
cd codes/docker

# 启动基础服务（数据库、缓存、搜索引擎等）
./start-services.sh

# 或者手动启动基础服务
docker compose up -d postgres redis elasticsearch kibana rabbitmq chromadb
```

### 3. 启动应用服务

```bash
# 启动后端API和向量化服务
docker compose up -d backend zhi-zhen-tong-embedding

# 启动Nginx反向代理（可选）
docker compose up -d nginx
```

### 4. 一键启动所有服务

```bash
# 启动所有服务（包括基础服务和应用服务）
docker compose up -d

# 或者使用完整系统启动
cd codes
./start-all.sh
```

### 5. 验证部署

```bash
# 检查服务状态
docker compose ps

# 健康检查
curl http://localhost:8000/health
curl http://localhost:9200/_cluster/health
curl http://localhost:8003/api/v1/heartbeat
```

## ⚙️ 服务配置

### Elasticsearch 配置

- **版本**: 8.11.0
- **内存**: 1GB (可通过环境变量调整)
- **安全**: 已禁用 (开发环境)
- **单节点模式**: 适合开发环境
- **健康检查**: 每 30 秒检查一次

### 模型配置

- **ERNIE-3.0-base-zh**: 中文文本向量化
- **Chinese-CLIP**: 图像向量化
- **向量维度**: 768
- **批处理大小**: 32

### 端口映射

```yaml
services:
  postgres:
    ports:
      - "5432:5432"
  redis:
    ports:
      - "6379:6379"
  elasticsearch:
    ports:
      - "9200:9200"
  kibana:
    ports:
      - "5601:5601"
  chromadb:
    ports:
      - "8003:8000"
  backend:
    ports:
      - "8000:8000"
  zhi-zhen-tong-embedding:
    ports:
      - "8001:8000"
  nginx:
    ports:
      - "80:80"
      - "443:443"
```

## 🔧 环境变量

### 后端服务环境变量

```bash
# 数据库连接
DATABASE_URL=postgresql://zhizhentong:zhizhentong123@postgres:5432/zhizhentong

# 缓存服务
REDIS_URL=redis://redis:6379/0

# 消息队列
RABBITMQ_URL=amqp://zhizhentong:zhizhentong123@rabbitmq:5672/

# 搜索引擎
ELASTICSEARCH_URL=http://elasticsearch:9200

# 向量数据库
CHROMADB_URL=http://chromadb:8000

# 向量化服务配置
EMBEDDING_BATCH_SIZE=32
MAX_CONCURRENT_REQUESTS=10
VECTOR_DIMENSION=768
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

### 生产环境优化变量

```bash
# 资源限制
WORKERS=4
TIMEOUT=300
KEEP_ALIVE=2
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=100

# 日志级别
LOG_LEVEL=WARNING
```

## 💾 数据持久化

所有数据都通过 Docker volumes 持久化：

```yaml
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  elasticsearch_data:
    driver: local
  rabbitmq_data:
    driver: local
  chromadb_data:
    driver: local
```

### 数据备份

```bash
# 备份所有数据
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# 恢复数据
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

## 🏭 生产环境配置

### 1. 资源限制

```yaml
# 在docker compose.yml中添加资源限制
deploy:
  resources:
    limits:
      memory: 8G
      cpus: "4.0"
    reservations:
      memory: 4G
      cpus: "2.0"
```

### 2. 生产环境启动

```bash
# 使用生产环境配置
docker compose -f docker compose.yml -f 生产环境配置.yml up -d
```

### 3. 监控配置

```bash
# 添加监控服务
docker compose -f docker compose.yml -f docker compose.monitoring.yml up -d
```

## 📊 批量向量化处理

### 1. 使用批量处理脚本

```bash
# 安装依赖
pip install requests pandas

# 批量向量化处理
python 批量向量化脚本.py --input data.json --output vectors.json --batch-size 32
```

### 2. API 批量处理

```python
import requests
import json

def batch_vectorize(file_path, batch_size=100):
    """批量向量化处理"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = []
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        response = requests.post(
            'http://localhost:8000/vectorize/batch',
            json={'texts': batch}
        )
        results.extend(response.json()['vectors'])

    return results
```

### 3. 性能调优

- **并发处理**: 调整 `MAX_CONCURRENT_REQUESTS`
- **批处理大小**: 调整 `EMBEDDING_BATCH_SIZE`
- **内存优化**: 根据服务器配置调整资源限制

## 📈 监控和维护

### 1. 服务状态监控

```bash
# 查看所有服务状态
docker compose ps

# 查看服务资源使用
docker stats

# 查看服务日志
docker compose logs -f [服务名]
```

### 2. 健康检查

```bash
# API服务健康检查
curl http://localhost:8000/health

# Elasticsearch健康检查
curl http://localhost:9200/_cluster/health

# ChromaDB健康检查
curl http://localhost:8003/api/v1/heartbeat
```

### 3. 维护命令

```bash
# 重启服务
docker compose restart [服务名]

# 更新服务
docker compose pull
docker compose up -d

# 清理资源
docker compose down
docker system prune -f

# 备份数据
tar -czf backup_$(date +%Y%m%d).tar.gz datas/ codes/logs/
```

## 🛠️ 故障排除

### 常见问题

#### 1. Docker 构建失败

**问题**: Docker 构建时出现文件路径错误

```
ERROR: failed to calculate checksum of ref: "/app": not found
```

**解决方案**:

```bash
# 1. 检查项目目录结构
ls -la codes/backend/app/
ls -la codes/ai_models/embedding_models/

# 2. 使用正确的Dockerfile
# 后端服务使用: Dockerfile.backend
# 向量化服务使用: Dockerfile.embedding

# 3. 分步启动服务
# 先启动基础服务
docker compose up -d postgres redis elasticsearch kibana rabbitmq chromadb

# 再启动应用服务
docker compose up -d backend zhi-zhen-tong-embedding
```

#### 2. 容器名称冲突

**问题**: 容器名称已存在

```
Error: The container name "/zhizhentong_redis" is already in use
```

**解决方案**:

```bash
# 停止并删除现有容器
docker compose down

# 清理所有相关容器
docker stop $(docker ps -aq --filter "name=zhizhentong") 2>/dev/null || true
docker rm $(docker ps -aq --filter "name=zhizhentong") 2>/dev/null || true

# 重新启动服务
docker compose up -d
```

#### 3. 端口冲突

```bash
# 检查端口占用
netstat -tlnp | grep :8000

# 修改端口映射
# 编辑docker compose.yml中的ports配置
```

#### 4. 内存不足

```bash
# 检查系统内存
free -h

# 调整Elasticsearch内存
export ES_JAVA_OPTS="-Xms512m -Xmx512m"
docker compose restart elasticsearch
```

#### 5. 服务启动失败

```bash
# 查看详细日志
docker compose logs [服务名]

# 检查模型文件
ls -la codes/aimodels/

# 检查权限
chmod -R 755 codes/ai_models/
```

#### 6. 数据重置

```bash
# 重置所有数据
docker compose down -v
docker compose up -d
```

### 性能优化

#### 1. Elasticsearch 优化

```yaml
environment:
  - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
  - "discovery.type=single-node"
  - "xpack.security.enabled=false"
```

#### 2. Redis 优化

```yaml
command: >
  redis-server 
  --appendonly yes 
  --maxmemory 1.5gb 
  --maxmemory-policy allkeys-lru
```

#### 3. 网络优化

```yaml
networks:
  zhi-zhen-tong-network:
    driver: bridge
    driver_opts:
      com.docker.network.driver.mtu: "1500"
```

## 🔐 安全配置

### 1. 网络隔离

- 使用内部网络通信
- 限制外部访问端口
- 配置防火墙规则

### 2. 数据加密

- 启用 HTTPS
- 数据库连接加密
- 敏感数据加密存储

### 3. 访问控制

- API 密钥认证
- 请求频率限制
- 用户权限管理

### 4. 生产环境安全

```bash
# 启用Elasticsearch安全功能
xpack.security.enabled=true
xpack.security.transport.ssl.enabled=true

# 配置ChromaDB认证
CHROMA_SERVER_AUTH_PROVIDER=chromadb.auth.basic.BasicAuthProvider
```

## 📊 监控指标

### 关键指标

- **API 响应时间**: < 2 秒
- **内存使用率**: < 80%
- **CPU 使用率**: < 70%
- **向量化成功率**: > 99%
- **Elasticsearch 健康状态**: green

### 监控工具

- **Prometheus**: 指标收集
- **Grafana**: 可视化监控
- **ELK Stack**: 日志分析

## 🌐 访问地址

### 服务访问

- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **Elasticsearch**: http://localhost:9200
- **Kibana**: http://localhost:5601
- **ChromaDB**: http://localhost:8003
- **RabbitMQ 管理界面**: http://localhost:15672

### 管理界面

- **向量化服务管理**: http://localhost:8001
- **系统监控**: http://localhost:3000 (Grafana)
- **日志分析**: http://localhost:5601 (Kibana)

## 🚨 Docker 问题解决方案

### 常见问题及解决方案

#### 问题描述

在启动 Docker 服务时可能遇到以下错误：

```
ERROR: failed to calculate checksum of ref: "/app": not found
```

#### 问题分析

1. **Dockerfile 路径问题**: 原始 Dockerfile 中的 COPY 命令指向了不存在的目录
2. **容器名称冲突**: 系统中已存在同名的容器
3. **Docker Compose 版本**: 使用了过时的`docker-compose`命令

#### 解决方案

##### 1. 修复 Dockerfile

创建了专门的 Dockerfile：

- `Dockerfile.backend` - 用于后端 API 服务
- `Dockerfile.embedding` - 用于向量化服务

##### 2. 更新 docker-compose.yml

- 移除了过时的`version`字段
- 更新了构建上下文和 Dockerfile 路径
- 修复了卷挂载路径

##### 3. 分步启动服务

**推荐方式**：

```bash
# 1. 启动基础服务
cd codes/docker
./start-services.sh

# 2. 启动应用服务
docker compose up -d backend zhi-zhen-tong-embedding
```

**手动方式**：

```bash
# 启动基础服务
docker compose up -d postgres redis elasticsearch kibana rabbitmq chromadb

# 启动应用服务
docker compose up -d backend zhi-zhen-tong-embedding
```

##### 4. 清理冲突容器

```bash
# 停止并删除现有容器
docker compose down

# 清理所有相关容器
docker stop $(docker ps -aq --filter "name=zhizhentong") 2>/dev/null || true
docker rm $(docker ps -aq --filter "name=zhizhentong") 2>/dev/null || true
```

#### 当前状态

##### ✅ 已解决的问题

1. **基础服务启动成功**：

   - PostgreSQL (端口: 5432) ✅
   - Redis (端口: 6379) ✅
   - Elasticsearch (端口: 9200) ✅
   - Kibana (端口: 5601) ✅
   - RabbitMQ (端口: 5672/15672) ✅
   - ChromaDB (端口: 8003) ✅

2. **服务健康检查**：
   - Elasticsearch 集群状态: green ✅
   - 所有基础服务正常运行 ✅

##### 📋 下一步操作

1. **启动应用服务**：

   ```bash
   docker compose up -d backend zhi-zhen-tong-embedding
   ```

2. **验证应用服务**：

   ```bash
   # 检查后端API
   curl http://localhost:8000/health

   # 检查向量化服务
   curl http://localhost:8001/health
   ```

3. **启动 Nginx 反向代理**（可选）：
   ```bash
   docker compose up -d nginx
   ```

## 📚 相关文档

- [Docker Compose 官方文档](https://docs.docker.com/compose/)
- [Elasticsearch 官方文档](https://www.elastic.co/guide/en/elasticsearch/reference/current/)
- [Kibana 官方文档](https://www.elastic.co/guide/en/kibana/current/)
- [ChromaDB 官方文档](https://docs.trychroma.com/)
- [PostgreSQL 官方文档](https://www.postgresql.org/docs/)
- [Redis 官方文档](https://redis.io/documentation)

---

## 🎯 快速开始

1. **克隆项目**: `git clone [项目地址]`
2. **进入目录**: `cd codes/docker`
3. **启动服务**: `./start-docker.sh`
4. **访问服务**: http://localhost:8000
5. **查看状态**: `docker compose ps`

**部署完成后，您可以通过以下方式开始使用：**

- **Web 界面**: http://localhost:8001
- **API 接口**: http://localhost:8000/docs
- **批量处理**: 使用提供的 Python 脚本
- **监控面板**: http://localhost:5601

---

_最后更新: 2024 年 12 月 19 日_
_版本: v1.0.0_
