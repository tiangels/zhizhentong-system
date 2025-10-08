# 混合检索服务

混合检索服务整合了向量检索和 ES 关键词检索，使用 RRF（Reciprocal Rank Fusion）融合算法提供更准确的检索结果。支持用户中心化的精准检索。

## 功能特性

- **用户中心化检索**: 基于用户 ID 的精准检索
- **混合检索**: 结合向量检索和 ES 关键词检索
- **RRF 融合算法**: 使用 Reciprocal Rank Fusion 算法融合结果
- **就诊人隔离**: 支持多就诊人数据隔离
- **异步处理**: 支持高并发的异步检索
- **智能重排序**: 基于医疗逻辑的智能重排序

## 服务架构

```
混合检索服务 (8007)
├── 向量检索服务 (8005) - Milvus
├── ES检索服务 (8004) - Elasticsearch
└── RRF融合算法 - 结果融合
```

## API 接口

### 健康检查

- **GET** `/health` - 服务健康状态

### 用户中心化检索

- **POST** `/search/user-centric` - 用户中心化混合检索
- **GET** `/patients/{user_id}` - 获取用户就诊人列表

## 启动服务

### 本地启动

```bash
cd services/hybrid_retrieval_service
python start_hybrid_service.py
```

### Docker 启动

```bash
docker-compose up -d
```

## 测试服务

```bash
python test_hybrid_retrieval_service.py
```

## 配置说明

- **端口**: 8007
- **日志**: `../../logs/hybrid_service.log`
- **依赖服务**:
  - 向量检索服务 (8005)
  - ES 检索服务 (8004)

## 融合算法

使用 RRF (Reciprocal Rank Fusion) 算法：

- 向量检索权重: 0.6
- ES 检索权重: 0.4
- 用户中心化权重: 基于用户和就诊人关联

## 用户中心化特性

- 基于用户 ID 的数据隔离
- 多就诊人支持
- 就诊人特定检索
- 跨用户数据隔离
- 医疗记录关联
