# 智诊通知识检索服务 API 接口层详细说明

## 📋 API 接口层概述

API 接口层是智诊通知识检索服务对外提供服务的入口，基于 FastAPI 框架构建，提供 RESTful API 接口和流式 API 接口。该层负责接收客户端请求，调用核心服务层处理业务逻辑，并返回标准化的响应结果。

## 📁 目录结构

### API 接口层文件结构

```
api/
├── retrieval_api.py              # 主要API接口实现
└── config/                       # 配置文件
    ├── retrieval_config.json     # 检索服务配置
    └── retrieval_config.py       # 配置管理类
```

### 组件关系图

```
┌─────────────────────────────────────────────────────────────┐
│                    API 接口层架构                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   FastAPI应用    │    │   中间件配置     │                │
│  │   (FastAPI)     │    │  (CORS, 日志)   │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                       │                        │
│           └───────────┬───────────┘                        │
│                       │                                    │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 API 端点                                │ │
│  │                                                         │ │
│  │ • 基础接口 (/, /health, /stats)                        │ │
│  │ • 文档管理 (/documents, /documents/images)              │ │
│  │ • 查询接口 (/query, /query/stream, /chat)              │ │
│  │ • 批量处理 (/batch_query)                              │ │
│  │ • 文档搜索 (/search)                                   │ │
│  │ • 系统管理 (/save, /load, /clear)                      │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 核心组件

### 1. 主要 API 文件 (retrieval_api.py)

#### 功能概述

`retrieval_api.py` 是 API 接口层的核心文件，定义了所有的 RESTful API 接口，包括文档管理、查询处理、流式响应等功能。

#### 核心特性

- **RESTful 设计**: 遵循 REST 架构规范
- **流式支持**: 支持实时流式响应
- **参数验证**: 完善的请求参数验证
- **错误处理**: 统一的错误处理机制
- **文档生成**: 自动生成 API 文档
- **CORS 支持**: 跨域请求支持

---

## 🔌 API 接口详解

### 1. 应用初始化

```python
# 创建FastAPI应用
app = FastAPI(
    title="知识检索 API",
    description="知识检索与生成一体化 API",
    version="1.0.0"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**配置说明**：

- `title`: API 服务标题
- `description`: API 服务描述
- `version`: API 版本号
- `docs_url`: Swagger 文档地址
- `redoc_url`: ReDoc 文档地址

### 2. 数据模型定义

#### 2.1 查询请求模型

```python
class QueryRequest(BaseModel):
    question: str = Field(..., description="用户问题", min_length=1, max_length=1000)
    top_k: int = Field(5, description="检索文档数量", ge=1, le=20)
    response_type: str = Field("general", description="响应类型")
    similarity_threshold: float = Field(0.5, description="相似度阈值", ge=0.0, le=1.0)
    enable_summary: bool = Field(True, description="是否启用文本摘要")
```

**字段说明**：

- `question`: 用户查询内容，必填，长度 1-1000 字符
- `top_k`: 检索文档数量，默认 5，范围 1-20
- `response_type`: 响应类型，支持 general/diagnosis/advice/explanation
- `similarity_threshold`: 相似度阈值，默认 0.5，范围 0.0-1.0
- `enable_summary`: 是否启用文本摘要，默认启用

#### 2.2 文档请求模型

```python
class DocumentRequest(BaseModel):
    content: str = Field(..., description="文档内容", min_length=10, max_length=5000)
    title: str = Field(..., description="文档标题", min_length=1, max_length=200)
    category: str = Field("general", description="文档分类")
    source: str = Field("unknown", description="文档来源")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    type: str = Field("text", description="文档类型")
```

**字段说明**：

- `content`: 文档内容，必填，长度 10-5000 字符
- `title`: 文档标题，必填，长度 1-200 字符
- `category`: 文档分类，默认 general
- `source`: 文档来源，默认 unknown
- `metadata`: 元数据，默认为空字典
- `type`: 文档类型，默认 text

#### 2.3 流式请求模型

```python
class StreamRequest(BaseModel):
    question: str = Field(..., description="用户问题", min_length=1, max_length=1000)
    top_k: int = Field(5, description="检索文档数量", ge=1, le=20)
    response_type: str = Field("general", description="响应类型")
    similarity_threshold: float = Field(200.0, description="相似度阈值")
```

**字段说明**：

- 与查询请求模型相同
- 专门用于流式响应接口

---

## 🔌 API 接口实现

### 1. 基础接口

#### 1.1 根路径信息

```python
@app.get("/", summary="根路径信息", description="获取API基本信息")
async def root():
    """获取API基本信息"""
    return {
        "service": "知识检索 API",
        "version": "1.0.0",
        "description": "知识检索与生成一体化 API",
        "endpoints": {
            "health": "/health",
            "stats": "/stats",
            "query": "/query",
            "chat": "/chat",
            "documents": "/documents",
            "search": "/search"
        }
    }
```

**接口特性**：

- **GET 方法**: 使用 GET 方法获取信息
- **基本信息**: 返回服务名称、版本、描述
- **端点列表**: 提供所有可用端点

#### 1.2 健康检查

```python
@app.get("/health", summary="健康检查", description="检查服务健康状态")
async def health_check():
    """健康检查"""
    try:
        # 检查核心服务状态
        pipeline = KnowledgeRetrievalPipelineFactory.create_rag_pipeline()
        stats = pipeline.get_system_stats()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "知识检索服务",
            "version": "1.0.0",
            "uptime": stats.get("uptime", 0),
            "total_documents": stats.get("total_documents", 0),
            "total_queries": stats.get("total_queries", 0)
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=503, detail=f"服务不可用: {str(e)}")
```

**接口特性**：

- **状态监控**: 实时监控服务状态
- **统计信息**: 提供运行时间、文档数量、查询次数
- **错误处理**: 服务异常时返回 503 状态码

#### 1.3 系统统计

```python
@app.get("/stats", summary="系统统计", description="获取系统统计信息")
async def get_stats():
    """获取系统统计信息"""
    try:
        pipeline = KnowledgeRetrievalPipelineFactory.create_rag_pipeline()
        stats = pipeline.get_system_stats()

        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")
```

**接口特性**：

- **详细信息**: 提供完整的系统统计信息
- **实时数据**: 包含文档数量、查询次数、响应时间等
- **错误处理**: 统一的错误处理机制

### 2. 文档管理接口

#### 2.1 添加文本文档

```python
@app.post("/documents", summary="添加文本文档", description="添加文本文档到知识库")
async def add_documents(documents: List[DocumentRequest]):
    """添加文本文档到知识库"""
    try:
        logger.info(f"收到添加文档请求: 数量={len(documents)}")

        # 转换文档格式
        doc_list = []
        for doc in documents:
            doc_dict = {
                "content": doc.content,
                "title": doc.title,
                "category": doc.category,
                "source": doc.source,
                "metadata": doc.metadata,
                "type": doc.type
            }
            doc_list.append(doc_dict)

        # 调用核心服务
        pipeline = KnowledgeRetrievalPipelineFactory.create_rag_pipeline()
        success = pipeline.add_documents(doc_list)

        if success:
            logger.info(f"文档添加成功: 数量={len(documents)}")
            return {
                "success": True,
                "message": f"成功添加 {len(documents)} 个文档",
                "data": {
                    "added_count": len(documents),
                    "total_documents": pipeline.get_system_stats().get("total_documents", 0)
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error("文档添加失败")
            raise HTTPException(status_code=500, detail="文档添加失败")

    except Exception as e:
        logger.error(f"添加文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"添加文档失败: {str(e)}")
```

**接口特性**：

- **批量添加**: 支持批量添加多个文档
- **格式验证**: 自动验证文档格式和内容
- **统计更新**: 实时更新文档统计信息
- **错误处理**: 详细的错误信息和状态码

#### 2.2 添加图像文档

```python
@app.post("/documents/images", summary="添加图像文档", description="添加图像文档到知识库")
async def add_image_documents(documents: List[DocumentRequest]):
    """添加图像文档到知识库"""
    try:
        logger.info(f"收到添加图像文档请求: 数量={len(documents)}")

        # 转换文档格式
        doc_list = []
        for doc in documents:
            doc_dict = {
                "content": doc.content,
                "title": doc.title,
                "category": doc.category,
                "source": doc.source,
                "metadata": doc.metadata,
                "type": "image"
            }
            doc_list.append(doc_dict)

        # 调用核心服务
        pipeline = KnowledgeRetrievalPipelineFactory.create_rag_pipeline()
        success = pipeline.add_documents(doc_list, vectorize_images=True)

        if success:
            logger.info(f"图像文档添加成功: 数量={len(documents)}")
            return {
                "success": True,
                "message": f"成功添加 {len(documents)} 个图像文档",
                "data": {
                    "added_count": len(documents),
                    "total_documents": pipeline.get_system_stats().get("total_documents", 0)
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error("图像文档添加失败")
            raise HTTPException(status_code=500, detail="图像文档添加失败")

    except Exception as e:
        logger.error(f"添加图像文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"添加图像文档失败: {str(e)}")
```

**接口特性**：

- **图像处理**: 专门处理图像文档
- **向量化**: 自动进行图像向量化
- **格式支持**: 支持多种图像格式
- **元数据**: 完整的图像元数据管理

### 3. 查询接口

#### 3.1 单次查询

```python
@app.post("/query", summary="单次查询", description="基于用户问题生成回答")
async def query_documents(request: QueryRequest):
    """基于用户问题生成回答"""
    try:
        logger.info(f"收到查询请求: question='{request.question}', top_k={request.top_k}")

        # 调用核心服务
        pipeline = KnowledgeRetrievalPipelineFactory.create_rag_pipeline()
        result = pipeline.query(
            question=request.question,
            top_k=request.top_k,
            response_type=request.response_type
        )

        logger.info(f"查询请求处理完成: success={result['success']}")
        return result

    except Exception as e:
        logger.error(f"查询请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
```

**接口特性**：

- **POST 方法**: 使用 POST 方法接收请求
- **参数验证**: 自动验证请求参数
- **错误处理**: 统一的错误处理机制
- **日志记录**: 详细的操作日志

#### 3.2 流式查询

```python
@app.post("/query/stream", summary="流式查询", description="流式生成回答")
async def query_stream(request: StreamRequest):
    """流式生成回答"""
    try:
        logger.info(f"收到流式查询请求: question='{request.question}', top_k={request.top_k}")

        def generate_response():
            """生成流式响应"""
            try:
                pipeline = KnowledgeRetrievalPipelineFactory.create_rag_pipeline()

                # 生成流式响应
                for chunk in pipeline.query_stream(
                    question=request.question,
                    top_k=request.top_k,
                    response_type=request.response_type
                ):
                    yield f"data: {chunk}\n\n"

                # 发送结束标记
                yield "data: [DONE]\n\n"

            except Exception as e:
                logger.error(f"流式响应生成失败: {e}")
                yield f"data: 生成回答时出现错误：{str(e)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )

    except Exception as e:
        logger.error(f"流式查询请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"流式查询失败: {str(e)}")
```

**接口特性**：

- **实时响应**: 逐步返回生成结果
- **流式格式**: 使用 Server-Sent Events 格式
- **错误恢复**: 流式错误处理
- **连接管理**: 保持连接状态

#### 3.3 对话功能

```python
@app.post("/chat", summary="对话功能", description="多轮对话交互")
async def chat_with_context(request: ChatRequest):
    """多轮对话交互"""
    try:
        logger.info(f"收到对话请求: messages_count={len(request.messages)}")

        # 调用核心服务
        pipeline = KnowledgeRetrievalPipelineFactory.create_rag_pipeline()
        result = pipeline.chat(
            messages=request.messages,
            top_k=request.top_k
        )

        logger.info(f"对话请求处理完成: success={result['success']}")
        return result

    except Exception as e:
        logger.error(f"对话请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")
```

**接口特性**：

- **多轮对话**: 支持上下文理解
- **消息历史**: 维护对话历史
- **智能回复**: 基于上下文的智能回复
- **状态管理**: 对话状态管理

### 4. 批量处理接口

#### 4.1 批量查询

```python
@app.post("/batch_query", summary="批量查询", description="批量处理多个问题")
async def batch_query_documents(request: BatchQueryRequest):
    """批量处理多个问题"""
    try:
        logger.info(f"收到批量查询请求: questions_count={len(request.questions)}")

        # 调用核心服务
        pipeline = KnowledgeRetrievalPipelineFactory.create_rag_pipeline()
        results = pipeline.batch_query(
            questions=request.questions,
            top_k=request.top_k
        )

        logger.info(f"批量查询请求处理完成: results_count={len(results)}")
        return {
            "success": True,
            "data": {
                "results": results,
                "total_questions": len(request.questions),
                "processed_count": len(results)
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"批量查询请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量查询失败: {str(e)}")
```

**接口特性**：

- **批量处理**: 支持批量处理多个问题
- **并行处理**: 并行处理提高效率
- **结果汇总**: 统一的结果格式
- **进度跟踪**: 处理进度跟踪

### 5. 文档搜索接口

#### 5.1 文档搜索

```python
@app.post("/search", summary="文档搜索", description="搜索相关文档")
async def search_documents(request: SearchRequest):
    """搜索相关文档"""
    try:
        logger.info(f"收到搜索请求: query='{request.query}', search_type='{request.search_type}'")

        # 调用核心服务
        pipeline = KnowledgeRetrievalPipelineFactory.create_rag_pipeline()
        results = pipeline.search_documents(
            query=request.query,
            search_type=request.search_type,
            top_k=request.top_k
        )

        logger.info(f"搜索请求处理完成: results_count={len(results)}")
        return {
            "success": True,
            "data": {
                "results": results,
                "query": request.query,
                "search_type": request.search_type,
                "total_results": len(results)
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"搜索请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")
```

**接口特性**：

- **多种搜索**: 支持语义搜索、关键词搜索、混合搜索
- **结果排序**: 智能的结果排序
- **元数据**: 完整的文档元数据
- **相似度**: 相似度分数

### 6. 系统管理接口

#### 6.1 保存系统状态

```python
@app.post("/save", summary="保存系统状态", description="保存当前系统状态")
async def save_system(save_dir: str):
    """保存当前系统状态"""
    try:
        logger.info(f"收到保存系统请求: save_dir='{save_dir}'")

        # 调用核心服务
        pipeline = KnowledgeRetrievalPipelineFactory.create_rag_pipeline()
        pipeline.save_system(save_dir)

        logger.info(f"系统保存成功: save_dir='{save_dir}'")
        return {
            "success": True,
            "message": f"系统状态已保存到 {save_dir}",
            "data": {
                "save_directory": save_dir,
                "save_time": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"保存系统失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存系统失败: {str(e)}")
```

**接口特性**：

- **状态保存**: 保存完整的系统状态
- **数据持久化**: 确保数据不丢失
- **备份恢复**: 支持系统备份和恢复
- **版本管理**: 支持多版本管理

#### 6.2 加载系统状态

```python
@app.post("/load", summary="加载系统状态", description="加载系统状态")
async def load_system(load_dir: str):
    """加载系统状态"""
    try:
        logger.info(f"收到加载系统请求: load_dir='{load_dir}'")

        # 调用核心服务
        pipeline = KnowledgeRetrievalPipelineFactory.create_rag_pipeline()
        pipeline.load_system(load_dir)

        logger.info(f"系统加载成功: load_dir='{load_dir}'")
        return {
            "success": True,
            "message": f"系统状态已从 {load_dir} 加载",
            "data": {
                "load_directory": load_dir,
                "load_time": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"加载系统失败: {e}")
        raise HTTPException(status_code=500, detail=f"加载系统失败: {str(e)}")
```

**接口特性**：

- **状态恢复**: 恢复系统到指定状态
- **数据完整性**: 确保数据完整性
- **快速启动**: 快速恢复系统状态
- **错误处理**: 加载失败时的错误处理

#### 6.3 清空系统数据

```python
@app.delete("/clear", summary="清空系统数据", description="清空所有系统数据")
async def clear_system():
    """清空所有系统数据"""
    try:
        logger.info("收到清空系统请求")

        # 调用核心服务
        pipeline = KnowledgeRetrievalPipelineFactory.create_rag_pipeline()
        pipeline.clear_system()

        logger.info("系统清空成功")
        return {
            "success": True,
            "message": "系统数据已清空",
            "data": {
                "clear_time": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"清空系统失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空系统失败: {str(e)}")
```

**接口特性**：

- **数据清空**: 清空所有系统数据
- **安全操作**: 安全的清空操作
- **状态重置**: 重置系统状态
- **确认机制**: 操作确认机制

---

## 🔧 中间件配置

### 1. CORS 中间件

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**配置说明**：

- `allow_origins`: 允许的源地址
- `allow_credentials`: 允许凭证
- `allow_methods`: 允许的 HTTP 方法
- `allow_headers`: 允许的请求头

### 2. 请求日志中间件

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    start_time = time.time()

    # 记录请求信息
    logger.info(f"收到请求: {request.method} {request.url}")

    # 处理请求
    response = await call_next(request)

    # 记录响应信息
    process_time = time.time() - start_time
    logger.info(f"请求处理完成: {response.status_code} 耗时: {process_time:.2f}s")

    return response
```

---

## 📚 API 文档

### 1. Swagger 文档

- **访问地址**: http://localhost:8002/docs
- **功能**: 交互式 API 文档
- **特性**: 在线测试、参数说明、响应示例

### 2. ReDoc 文档

- **访问地址**: http://localhost:8002/redoc
- **功能**: 静态 API 文档
- **特性**: 详细说明、格式规范、易于阅读

### 3. OpenAPI 规范

```yaml
openapi: 3.0.0
info:
  title: 知识检索 API
  description: 知识检索与生成一体化 API
  version: 1.0.0
paths:
  /query:
    post:
      summary: 单次查询
      description: 基于用户问题生成回答
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/QueryRequest"
      responses:
        "200":
          description: 成功响应
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/QueryResponse"
```

---

## 🎯 使用示例

### 1. Python 客户端示例

```python
import requests

# 基础查询
def query_documents(question: str, top_k: int = 5):
    url = "http://localhost:8002/query"
    data = {
        "question": question,
        "top_k": top_k,
        "response_type": "general",
        "enable_summary": True
    }

    response = requests.post(url, json=data)
    return response.json()

# 使用示例
result = query_documents("什么是心肌梗死？", top_k=3)
print(f"问题: {result['data']['question']}")
print(f"回答: {result['data']['answer']}")
```

### 2. JavaScript 客户端示例

```javascript
// 查询请求示例
async function queryDocuments(question, topK = 5) {
  const url = "http://localhost:8002/query";
  const data = {
    question: question,
    top_k: topK,
    response_type: "general",
    enable_summary: true,
  };

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  return await response.json();
}

// 使用示例
queryDocuments("什么是心肌梗死？")
  .then((result) => console.log(result))
  .catch((error) => console.error(error));
```

### 3. 流式查询示例

```python
import requests

# 流式查询
def query_stream(question: str, top_k: int = 5):
    url = "http://localhost:8002/query/stream"
    data = {
        "question": question,
        "top_k": top_k,
        "response_type": "general",
        "similarity_threshold": 200.0
    }

    response = requests.post(url, json=data, stream=True)

    for line in response.iter_lines():
        if line:
            # 处理流式响应
            print(line.decode('utf-8'))
```

---

## 🔧 部署配置

### 1. 服务配置

```python
# 服务启动配置
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "retrieval_api:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
```

### 2. Docker 配置

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8002

CMD ["python", "retrieval_api.py"]
```

### 3. Nginx 配置

```nginx
server {
    listen 80;
    server_name retrieval.example.com;

    location / {
        proxy_pass http://localhost:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /query/stream {
        proxy_pass http://localhost:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 流式响应设置
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

---

## 🧪 测试和验证

### 1. API 测试

```python
# 测试健康检查
def test_health_check():
    response = requests.get("http://localhost:8002/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

# 测试查询功能
def test_query():
    data = {
        "question": "什么是心肌梗死？",
        "top_k": 5,
        "response_type": "general"
    }
    response = requests.post("http://localhost:8002/query", json=data)
    assert response.status_code == 200
    result = response.json()
    assert result["success"] == True
    assert "answer" in result["data"]
```

### 2. 性能测试

```python
# 性能测试
def test_performance():
    import time

    start_time = time.time()
    response = requests.post("http://localhost:8002/query", json={
        "question": "性能测试查询",
        "top_k": 5
    })
    end_time = time.time()

    assert response.status_code == 200
    assert end_time - start_time < 5.0  # 5秒内完成
```

### 3. 流式测试

```python
# 流式测试
def test_stream():
    response = requests.post("http://localhost:8002/query/stream", json={
        "question": "流式测试查询",
        "top_k": 5
    }, stream=True)

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"

    # 检查流式响应
    chunks = []
    for line in response.iter_lines():
        if line:
            chunks.append(line.decode('utf-8'))

    assert len(chunks) > 0
    assert any("data:" in chunk for chunk in chunks)
```

---

## ⚠️ 故障排除

### 1. 常见问题

#### 服务启动失败

- **检查端口**: 确保 8002 端口未被占用
- **检查依赖**: 运行 `pip install -r requirements.txt`
- **检查配置**: 确保配置文件正确

#### 请求超时

- **增加超时**: 设置合适的请求超时时间
- **检查网络**: 确保网络连接正常
- **优化查询**: 减少查询复杂度

#### 流式响应中断

- **检查连接**: 确保客户端连接稳定
- **增加超时**: 设置合适的流式超时时间
- **错误处理**: 实现客户端错误处理

### 2. 调试方法

```python
# 启用调试模式
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查API状态
def check_api_status():
    try:
        response = requests.get("http://localhost:8002/health")
        print(f"API状态: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"API检查失败: {e}")
```

---

## 🔮 未来规划

### 1. 功能扩展

- **认证授权**: 添加用户认证和权限控制
- **速率限制**: 实现 API 调用速率限制
- **缓存机制**: 添加响应缓存机制
- **监控告警**: 完善监控和告警系统

### 2. 性能优化

- **异步处理**: 更多异步操作
- **连接池**: 数据库连接池优化
- **负载均衡**: 支持负载均衡部署
- **CDN 集成**: 静态资源 CDN 加速

### 3. 用户体验

- **API 版本管理**: 支持 API 版本管理
- **文档完善**: 更详细的 API 文档
- **SDK 开发**: 提供多语言 SDK
- **示例代码**: 丰富的使用示例

---

## 📈 监控和维护

### 1. 性能监控

```python
# 性能监控装饰器
def monitor_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        # 记录性能数据
        logger.info(f"API {func.__name__} took {end_time - start_time:.2f}s")
        return result
    return wrapper
```

### 2. 错误监控

```python
# 错误监控
def monitor_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 记录错误
            logger.error(f"API Error in {func.__name__}: {e}")
            # 发送告警
            send_alert(f"API Error: {e}")
            raise
    return wrapper
```

### 3. 使用统计

```python
# 使用统计
def track_usage(func):
    def wrapper(*args, **kwargs):
        # 记录使用统计
        logger.info(f"API {func.__name__} called")
        return func(*args, **kwargs)
    return wrapper
```

---

## 🎉 总结

### API 接口层优势

✅ **功能完整**：提供完整的 RAG 功能 API  
✅ **设计规范**：遵循 REST 架构规范  
✅ **文档完善**：自动生成 API 文档  
✅ **错误处理**：统一的错误处理机制  
✅ **流式支持**：支持实时流式响应  
✅ **易于使用**：清晰的接口设计和示例

### 核心成就

1. **RESTful API**：完整的 RESTful API 设计
2. **流式响应**：支持实时流式响应
3. **批量处理**：支持批量操作
4. **文档管理**：完整的文档管理功能
5. **系统管理**：系统状态管理功能

### 技术特色

- **FastAPI 框架**：现代化的 Python Web 框架
- **自动文档**：自动生成 API 文档
- **类型验证**：Pydantic 模型验证
- **异步支持**：支持异步操作
- **中间件**：CORS 和日志中间件

---

**版本**：v2.2.0  
**更新时间**：2024 年 12 月  
**维护团队**：智诊通开发团队  
**文档状态**：完整、清晰、合理、与代码同步

_本文档详细说明了智诊通知识检索服务 API 接口层的架构设计、接口实现、使用示例、部署配置、测试验证、故障排除、未来规划等全面内容。_
