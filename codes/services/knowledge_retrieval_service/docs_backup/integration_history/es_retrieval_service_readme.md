# ES 检索服务

## 📋 服务概述

ES 检索服务提供 Elasticsearch 关键词检索功能，支持医疗数据查询和用户中心化检索。该服务是智诊通 RAG 系统的重要组成部分，与向量检索服务配合实现混合检索。

## 🏗️ 服务架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    混合检索架构                                  │
├─────────────────────────────────────────────────────────────────┤
│  用户查询 → 查询理解 → 并行检索 → RRF融合 → 重排序 → 生成回答    │
│           │                                                    │
│           ├── 向量检索 (ChromaDB)                              │
│           │   ├── 医疗知识库                                   │
│           │   ├── 症状-疾病关系                                │
│           │   └── 诊疗指南                                    │
│           │                                                    │
│           └── 关键词检索 (Elasticsearch)                      │
│               ├── 真实病历数据                                 │
│               ├── 患者历史记录                                 │
│               └── 家族病史                                     │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 Elasticsearch

```bash
# 使用Docker启动ES
docker-compose up -d elasticsearch
```

### 3. 启动 ES 检索服务

```bash
python es_retrieval_service.py
```

### 4. 生成测试数据（可选）

```bash
python data_generator.py
```

## 📡 API 接口

### ES 检索服务 (端口: 8004)

#### 关键词检索

```http
POST /search/keywords
Content-Type: application/json

{
    "keywords": ["头痛", "发热"],
    "user_id": "user_123",
    "patient_unique_ids": ["PATIENT_001"],
    "department": "神经内科",
    "top_k": 10
}
```

#### 用户中心化检索

```http
POST /search/user
Content-Type: application/json

{
    "user_id": "user_123",
    "keywords": ["高血压", "头痛"],
    "patient_unique_ids": ["PATIENT_001", "PATIENT_002"],
    "department": "心血管内科",
    "top_k": 10
}
```

#### 获取就诊人记录

```http
POST /search/patient-records
Content-Type: application/json

{
    "user_id": "user_123",
    "patient_unique_id": "PATIENT_001",
    "top_k": 20
}
```

#### 搜索相似病例

```http
POST /search/similar-cases
Content-Type: application/json

{
    "user_id": "user_123",
    "symptoms": ["头痛", "头晕"],
    "department": "神经内科",
    "top_k": 5
}
```

### 混合检索服务 (端口: 8005)

#### 混合检索

```http
POST /search/hybrid
Content-Type: application/json

{
    "query": "头痛症状",
    "query_context": {
        "patient_id": "110101197801010001",
        "symptom": "头痛"
    },
    "top_k": 10,
    "fusion_weights": [0.6, 0.4]
}
```

#### 医疗专用检索

```http
POST /search/medical
Content-Type: application/json

{
    "query": "心肌梗死症状",
    "query_context": {
        "patient_id": "110101197801010001",
        "symptom": "胸痛"
    },
    "top_k": 5
}
```

## 🔧 核心功能

### 1. ES 检索服务

- **关键词检索**: 基于关键词的医疗数据检索
- **用户中心化检索**: 基于用户 ID 的精准检索
- **就诊人记录查询**: 查询特定就诊人的所有记录
- **相似病例搜索**: 基于症状搜索相似病例
- **统计信息**: 获取 ES 索引统计信息

### 2. 混合检索服务

- **并行检索**: 同时执行向量检索和 ES 检索
- **RRF 融合**: 使用 Reciprocal Rank Fusion 算法融合结果
- **重排序**: 基于医疗逻辑权重重排序结果
- **医疗相关性**: 计算医疗领域相关性分数

### 3. RRF 融合算法

- **RRF 分数计算**: `1 / (k + rank)`
- **权重融合**: 向量检索权重 + ES 检索权重
- **医疗权重**: 症状匹配、诊断匹配、治疗匹配等
- **时间相关性**: 最近的就诊记录权重更高

## 🧪 测试

### 运行测试

```bash
python test_hybrid_service.py
```

### 测试内容

1. **健康检查测试**: 验证服务状态
2. **混合检索测试**: 测试多种查询场景
3. **医疗专用检索测试**: 测试医疗领域查询

## 📊 性能优化

### 1. 并行检索

- 向量检索和 ES 检索并行执行
- 减少总体响应时间

### 2. 缓存机制

- 查询结果缓存
- 减少重复计算

### 3. 权重优化

- 医疗领域权重调整
- 患者匹配权重优化

## 🔍 监控和日志

### 日志级别

- INFO: 正常操作日志
- ERROR: 错误日志
- DEBUG: 调试日志

### 监控指标

- 检索响应时间
- 检索成功率
- 融合效果评估

## 🚀 部署

### Docker 部署

```bash
# 构建镜像
docker build -t es-retrieval-service .

# 运行容器
docker run -p 8004:8004 es-retrieval-service
```

### Docker Compose 部署

```bash
# 启动所有服务
docker-compose up -d
```

## 📚 技术栈

- **FastAPI**: Web 框架
- **Elasticsearch**: 搜索引擎
- **aiohttp**: 异步 HTTP 客户端
- **Pydantic**: 数据验证
- **uvicorn**: ASGI 服务器

## 🔗 相关服务

- **向量检索服务**: 端口 8001
- **混合检索服务**: 端口 8003
- **RAG 服务**: 端口 8000

## 📝 更新日志

### v1.0.0

- 初始版本发布
- 支持 ES 关键词检索
- 支持混合检索
- 支持 RRF 融合算法
- 支持医疗专用检索
