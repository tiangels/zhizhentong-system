# 智诊通向量化服务 API 接口层详细说明

## 📋 模块概述

API 接口层是智诊通向量化服务的外部接口，基于 FastAPI 框架构建，提供 RESTful API 服务。该层负责接收客户端请求，调用核心服务层进行处理，并返回标准化的响应结果。

### 🎯 核心功能

- **RESTful API 设计**: 提供标准化的 HTTP 接口
- **异步处理支持**: 支持高并发请求处理
- **自动文档生成**: 自动生成 API 文档和交互式界面
- **请求验证**: 使用 Pydantic 进行请求参数验证
- **错误处理**: 统一的错误处理和响应格式
- **CORS 支持**: 支持跨域请求
- **健康检查**: 提供服务健康状态检查

## 📁 目录结构

```
api/                                    # API接口层目录
├── embedding_api.py                   # 🔌 FastAPI接口实现
├── config/                            # ⚙️ API配置目录
│   └── api_config.json               # API配置文件
└── __pycache__/                       # Python缓存目录
```

## 🔌 核心文件详解

### 1. embedding_api.py - FastAPI 接口实现

#### 1.1 文件概述

- **文件路径**: `api/embedding_api.py`
- **主要功能**: FastAPI 应用实现，提供向量化服务的 HTTP 接口
- **技术栈**: FastAPI, Pydantic, Uvicorn
- **端口**: 8001

#### 1.2 核心组件

##### 1.2.1 FastAPI 应用配置

```python
app = FastAPI(
    title="智诊通向量化服务API",
    description="提供文本、图像、多模态向量化服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
```

**配置说明**:

- **title**: API 服务名称
- **description**: API 服务描述
- **version**: API 版本号
- **docs_url**: Swagger UI 文档地址
- **redoc_url**: ReDoc 文档地址

##### 1.2.2 CORS 中间件配置

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**配置说明**:

- **allow_origins**: 允许的源地址（\*表示所有）
- **allow_credentials**: 允许携带凭证
- **allow_methods**: 允许的 HTTP 方法
- **allow_headers**: 允许的请求头

##### 1.2.3 API 路由器配置

```python
api_router = APIRouter(prefix="/api/v1")
```

**配置说明**:

- **prefix**: API 路径前缀
- **版本控制**: 支持 API 版本管理

#### 1.3 请求模型定义

##### 1.3.1 文本向量化请求模型

```python
class TextVectorizeRequest(BaseModel):
    """文本向量化请求"""
    texts: List[str] = Field(..., description="待向量化的文本列表")
    chunk_strategy: str = Field(default="medical_structured", description="文档切分策略")
    preprocessing: bool = Field(default=True, description="是否进行预处理")
    model_name: Optional[str] = Field(default=None, description="指定模型名称")
```

**参数说明**:

- **texts**: 必填，待向量化的文本列表
- **chunk_strategy**: 可选，文档切分策略，默认为医疗结构化切分
- **preprocessing**: 可选，是否进行预处理，默认为 True
- **model_name**: 可选，指定使用的模型名称

##### 1.3.2 图像向量化请求模型

```python
class ImageVectorizeRequest(BaseModel):
    """图像向量化请求"""
    image_paths: List[str] = Field(..., description="图像文件路径列表")
    extract_text: bool = Field(default=True, description="是否提取图像中的文本")
    model_name: Optional[str] = Field(default=None, description="指定模型名称")
```

**参数说明**:

- **image_paths**: 必填，图像文件路径列表
- **extract_text**: 可选，是否提取图像中的文本，默认为 True
- **model_name**: 可选，指定使用的模型名称

##### 1.3.3 多模态向量化请求模型

```python
class MultimodalVectorizeRequest(BaseModel):
    """多模态向量化请求"""
    texts: Optional[List[str]] = Field(default=None, description="文本列表")
    image_paths: Optional[List[str]] = Field(default=None, description="图像路径列表")
    fusion_method: str = Field(default="concat", description="融合方法: concat, add, multiply")
    model_name: Optional[str] = Field(default=None, description="指定模型名称")
```

**参数说明**:

- **texts**: 可选，文本列表
- **image_paths**: 可选，图像路径列表
- **fusion_method**: 可选，融合方法，默认为 concat
- **model_name**: 可选，指定使用的模型名称

##### 1.3.4 批量向量化请求模型

```python
class BatchVectorizeRequest(BaseModel):
    """批量向量化请求"""
    data: List[Dict[str, Any]] = Field(..., description="批量数据列表")
    model_name: Optional[str] = Field(default=None, description="指定模型名称")
```

**参数说明**:

- **data**: 必填，批量数据列表
- **model_name**: 可选，指定使用的模型名称

##### 1.3.5 检索请求模型

```python
class RetrieveRequest(BaseModel):
    """检索请求"""
    query: str = Field(..., description="查询文本")
    top_k: int = Field(default=5, description="返回结果数量")
    retrieval_type: str = Field(default="text", description="检索类型: text, image, multimodal")
    similarity_threshold: float = Field(default=0.3, description="相似度阈值")
```

**参数说明**:

- **query**: 必填，查询文本
- **top_k**: 可选，返回结果数量，默认为 5
- **retrieval_type**: 可选，检索类型，默认为 text
- **similarity_threshold**: 可选，相似度阈值，默认为 0.3

#### 1.4 响应模型定义

##### 1.4.1 向量化响应模型

```python
class VectorizeResponse(BaseModel):
    """向量化响应"""
    success: bool
    message: str
    data: Dict[str, Any]
    error: Optional[str] = None
```

**字段说明**:

- **success**: 请求是否成功
- **message**: 响应消息
- **data**: 响应数据
- **error**: 错误信息（可选）

##### 1.4.2 健康检查响应模型

```python
class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: str
    version: str
    services: Dict[str, str]
```

**字段说明**:

- **status**: 服务状态
- **timestamp**: 时间戳
- **version**: 服务版本
- **services**: 各服务状态

#### 1.5 生命周期管理

##### 1.5.1 启动事件

```python
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化服务"""
    global embedding_service

    try:
        logger.info("🚀 向量化服务启动中...")

        # 初始化向量化服务
        embedding_service = EmbeddingService(device="cpu")
        logger.info("✅ 向量化服务初始化完成")

        logger.info("🎉 所有服务启动完成")

    except Exception as e:
        logger.error(f"❌ 服务启动失败: {str(e)}")
        raise
```

**功能说明**:

- 初始化全局向量化服务实例
- 设置设备配置（CPU）
- 记录启动日志
- 异常处理和错误记录

##### 1.5.2 关闭事件

```python
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    global embedding_service

    try:
        logger.info("🔄 向量化服务关闭中...")

        if embedding_service:
            await embedding_service.cleanup()
            logger.info("✅ 向量化服务清理完成")

        logger.info("👋 所有服务已关闭")

    except Exception as e:
        logger.error(f"❌ 服务关闭失败: {str(e)}")
```

**功能说明**:

- 清理全局向量化服务实例
- 释放资源
- 记录关闭日志
- 异常处理和错误记录

#### 1.6 API 端点详解

##### 1.6.1 健康检查端点

**根路径健康检查**

- **路径**: `GET /`
- **功能**: 根路径健康检查
- **响应**: HealthResponse

**健康检查端点**

- **路径**: `GET /health`
- **功能**: 服务健康状态检查
- **响应**: HealthResponse

##### 1.6.2 文本向量化端点

**路径**: `POST /api/v1/vectorize/text`

**功能**: 文本向量化处理

**请求示例**:

```json
{
  "texts": ["患者主诉胸痛", "心电图显示异常"],
  "chunk_strategy": "medical_structured",
  "preprocessing": true,
  "model_name": "biomedclip"
}
```

**响应示例**:

```json
{
    "success": true,
    "message": "文本向量化成功",
    "data": {
        "vectors": [[0.1, 0.2, ...], [0.3, 0.4, ...]],
        "texts": ["患者主诉胸痛", "心电图显示异常"],
        "model_name": "biomedclip",
        "dimension": 512,
        "count": 2
    }
}
```

**处理流程**:

1. 接收请求参数
2. 验证参数有效性
3. 调用核心服务进行向量化
4. 记录处理日志
5. 返回标准化响应

##### 1.6.3 图像向量化端点

**路径**: `POST /api/v1/vectorize/image`

**功能**: 图像向量化处理

**请求示例**:

```json
{
  "image_paths": ["chest_xray.jpg", "ecg.png"],
  "extract_text": true,
  "model_name": "biomedclip"
}
```

**响应示例**:

```json
{
    "success": true,
    "message": "图像向量化成功",
    "data": {
        "vectors": [[0.1, 0.2, ...], [0.3, 0.4, ...]],
        "image_paths": ["chest_xray.jpg", "ecg.png"],
        "model_name": "biomedclip",
        "dimension": 512,
        "count": 2
    }
}
```

##### 1.6.4 多模态向量化端点

**路径**: `POST /api/v1/vectorize/multimodal`

**功能**: 多模态数据向量化处理

**请求示例**:

```json
{
  "texts": ["患者主诉胸痛"],
  "image_paths": ["chest_xray.jpg"],
  "fusion_method": "concat",
  "model_name": "biomedclip"
}
```

**响应示例**:

```json
{
    "success": true,
    "message": "多模态向量化成功",
    "data": {
        "combined_vectors": [[0.1, 0.2, ...]],
        "text_vectors": [[0.1, 0.2, ...]],
        "image_vectors": [[0.3, 0.4, ...]],
        "fusion_method": "concat",
        "model_name": "biomedclip",
        "dimension": 512,
        "count": 1
    }
}
```

##### 1.6.5 文档检索端点

**路径**: `POST /api/v1/retrieve`

**功能**: 文档检索处理

**请求示例**:

```json
{
  "query": "心脏疾病",
  "top_k": 5,
  "retrieval_type": "text",
  "similarity_threshold": 0.3
}
```

**响应示例**:

```json
{
  "success": true,
  "message": "文档检索成功",
  "data": {
    "results": [
      {
        "content": "患者主诉胸痛，心电图显示异常",
        "similarity_score": 0.85,
        "metadata": {
          "source": "medical_record_001",
          "type": "text"
        }
      }
    ],
    "query": "心脏疾病",
    "total_results": 1,
    "processing_time": 0.123
  }
}
```

##### 1.6.6 模型列表端点

**路径**: `GET /api/v1/models`

**功能**: 获取可用模型列表

**响应示例**:

```json
{
  "success": true,
  "message": "模型列表获取成功",
  "data": {
    "text_models": ["biomedclip"],
    "image_models": ["biomedclip"],
    "voice_models": ["whisper"],
    "current_text_model": "biomedclip",
    "current_image_model": "biomedclip",
    "current_voice_model": "whisper"
  }
}
```

##### 1.6.7 统计信息端点

**路径**: `GET /api/v1/stats`

**功能**: 获取服务统计信息

**响应示例**:

```json
{
  "success": true,
  "message": "统计信息获取成功",
  "data": {
    "total_requests": 1000,
    "successful_requests": 950,
    "failed_requests": 50,
    "average_response_time": 0.123,
    "memory_usage": "512MB",
    "cpu_usage": "45%"
  }
}
```

#### 1.7 日志记录

##### 1.7.1 日志配置

```python
from log_config import setup_embedding_service_logging
logger = setup_embedding_service_logging()
```

##### 1.7.2 日志记录内容

- **请求开始**: 记录请求 ID 和参数
- **处理过程**: 记录处理步骤和中间结果
- **处理完成**: 记录处理结果和性能指标
- **错误处理**: 记录错误信息和堆栈跟踪

##### 1.7.3 日志格式示例

```
2025-01-XX 10:30:15 - INFO - 🔤 [req_20250101_103015_123456] 开始文本向量化请求
2025-01-XX 10:30:15 - INFO - 📊 [req_20250101_103015_123456] 请求参数: texts_count=2, chunk_strategy=medical_structured, preprocessing=True
2025-01-XX 10:30:15 - INFO - 📝 [req_20250101_103015_123456] 文本 1: 长度=6 字符, 内容='患者主诉胸痛'
2025-01-XX 10:30:15 - INFO - ✅ [req_20250101_103015_123456] 文本向量化完成
2025-01-XX 10:30:15 - INFO - 📈 [req_20250101_103015_123456] 处理结果: vectors_count=2, dimension=512, processing_time=0.123s
```

#### 1.8 错误处理

##### 1.8.1 错误类型

- **HTTPException**: HTTP 状态码错误
- **ValidationError**: 参数验证错误
- **ServiceError**: 服务内部错误
- **TimeoutError**: 请求超时错误

##### 1.8.2 错误处理机制

```python
try:
    # 处理逻辑
    result = embedding_service.vectorize_text(...)
    return VectorizeResponse(success=True, message="成功", data=result)
except Exception as e:
    logger.error(f"❌ 处理失败: {str(e)}")
    return VectorizeResponse(
        success=False,
        message="处理失败",
        data={},
        error=str(e)
    )
```

#### 1.9 性能优化

##### 1.9.1 异步处理

- 使用 async/await 模式
- 支持并发请求处理
- 非阻塞 I/O 操作

##### 1.9.2 请求 ID 追踪

- 为每个请求生成唯一 ID
- 便于日志追踪和调试
- 支持请求链路追踪

##### 1.9.3 批量处理支持

- 支持批量文本向量化
- 支持批量图像向量化
- 优化批处理性能

## 🚀 部署和运行

### 1. 启动服务

```bash
# 直接运行
python api/embedding_api.py

# 使用Uvicorn
uvicorn api.embedding_api:app --host 0.0.0.0 --port 8001

# 生产环境
uvicorn api.embedding_api:app --host 0.0.0.0 --port 8001 --workers 4
```

### 2. 访问文档

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **健康检查**: http://localhost:8001/health

### 3. 测试接口

```bash
# 健康检查
curl http://localhost:8001/health

# 文本向量化
curl -X POST "http://localhost:8001/api/v1/vectorize/text" \
     -H "Content-Type: application/json" \
     -d '{"texts": ["患者主诉胸痛"]}'

# 图像向量化
curl -X POST "http://localhost:8001/api/v1/vectorize/image" \
     -H "Content-Type: application/json" \
     -d '{"image_paths": ["chest_xray.jpg"]}'
```

## 🔧 配置管理

### 1. API 配置

```json
{
  "host": "0.0.0.0",
  "port": 8001,
  "workers": 4,
  "log_level": "INFO",
  "cors_origins": ["*"],
  "request_timeout": 30,
  "max_request_size": "10MB"
}
```

### 2. 环境变量

```bash
export EMBEDDING_SERVICE_HOST=0.0.0.0
export EMBEDDING_SERVICE_PORT=8001
export EMBEDDING_SERVICE_LOG_LEVEL=INFO
export EMBEDDING_SERVICE_DEVICE=cpu
```

## 📊 监控和指标

### 1. 性能指标

- **请求处理时间**: 平均响应时间
- **并发处理能力**: 同时处理的请求数
- **错误率**: 请求失败的比例
- **吞吐量**: 每秒处理的请求数

### 2. 健康检查

- **服务状态**: 服务是否正常运行
- **依赖检查**: 核心服务是否可用
- **资源使用**: CPU、内存使用情况

### 3. 日志监控

- **请求日志**: 记录所有 API 请求
- **错误日志**: 记录错误和异常
- **性能日志**: 记录性能指标

## 🔮 未来规划

### 1. 功能扩展

- **WebSocket 支持**: 实时通信支持
- **流式处理**: 支持流式数据处理
- **缓存机制**: 实现智能缓存
- **限流控制**: 实现请求限流

### 2. 性能优化

- **连接池**: 数据库连接池优化
- **异步优化**: 进一步优化异步处理
- **内存优化**: 优化内存使用
- **CPU 优化**: 优化 CPU 使用

### 3. 安全增强

- **认证授权**: 实现 API 认证
- **HTTPS 支持**: 支持 HTTPS 协议
- **请求签名**: 实现请求签名验证
- **访问控制**: 实现细粒度访问控制

---

**版本**: v2.0.0  
**更新时间**: 2025 年 1 月  
**维护团队**: 智诊通开发团队
