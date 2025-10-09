# 智诊通智能诊断服务 API 接口层详细说明

## 🎯 API 接口层概述

API 接口层是智诊通智能诊断服务对外提供服务的入口，基于 FastAPI 框架构建，提供 RESTful API 接口和流式 API 接口。该层负责接收客户端请求，调用核心服务层处理业务逻辑，并返回标准化的响应结果。

## 📁 目录结构

```
api/
├── diagnosis_api.py          # 主要API接口文件
└── config/                   # API配置目录（预留）
```

## 🔧 核心组件

### 1. 主要 API 文件 (diagnosis_api.py)

#### 功能概述

`diagnosis_api.py` 是 API 接口层的核心文件，定义了所有的 RESTful API 接口，包括诊断生成、文本摘要、流式响应等功能。

#### 核心特性

- **RESTful 设计**: 遵循 REST 架构规范
- **流式支持**: 支持实时流式响应
- **参数验证**: 完善的请求参数验证
- **错误处理**: 统一的错误处理机制
- **文档生成**: 自动生成 API 文档
- **CORS 支持**: 跨域请求支持

## 🔌 API 接口详解

### 1. 应用初始化

```python
# 创建FastAPI应用实例
app = FastAPI(
    title="智诊通智能诊断服务",
    description="基于大语言模型的医疗智能诊断服务",
    version="1.0.0",
    docs_url="/diagnosis/docs",
    redoc_url="/diagnosis/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**配置说明：**

- `title`: API 服务标题
- `description`: API 服务描述
- `version`: API 版本号
- `docs_url`: Swagger 文档地址
- `redoc_url`: ReDoc 文档地址

### 2. 数据模型定义

#### 2.1 诊断请求模型

```python
class DiagnosisRequest(BaseModel):
    """诊断请求模型"""
    query: str = Field(..., description="用户查询", min_length=1, max_length=1000)
    context: str = Field(default="", description="检索到的上下文信息", max_length=10000)
    response_type: str = Field(default="diagnosis", description="响应类型", pattern="^(diagnosis|advice|explanation)$")
    enable_summary: bool = Field(default=True, description="是否启用文本摘要")
```

**字段说明：**

- `query`: 用户查询内容，必填，长度 1-1000 字符
- `context`: 上下文信息，可选，最大 10000 字符
- `response_type`: 响应类型，支持 diagnosis/advice/explanation
- `enable_summary`: 是否启用文本摘要，默认启用

#### 2.2 摘要请求模型

```python
class SummarizeRequest(BaseModel):
    """摘要请求模型"""
    text: str = Field(..., description="需要摘要的文本", min_length=10, max_length=5000)
    max_length: int = Field(default=200, description="最大摘要长度", ge=50, le=500)
    min_length: int = Field(default=50, description="最小摘要长度", ge=10, le=200)
```

**字段说明：**

- `text`: 需要摘要的文本，必填，长度 10-5000 字符
- `max_length`: 最大摘要长度，默认 200，范围 50-500
- `min_length`: 最小摘要长度，默认 50，范围 10-200

#### 2.3 流式请求模型

```python
class StreamRequest(BaseModel):
    """流式请求模型"""
    query: str = Field(..., description="用户查询", min_length=1, max_length=1000)
    context: str = Field(default="", description="检索到的上下文信息", max_length=10000)
    response_type: str = Field(default="diagnosis", description="响应类型", pattern="^(diagnosis|advice|explanation)$")
    enable_summary: bool = Field(default=True, description="是否启用文本摘要")
```

**字段说明：**

- 与诊断请求模型相同
- 专门用于流式响应接口

### 3. API 接口实现

#### 3.1 诊断生成接口

```python
@app.post("/diagnosis/generate",
          summary="生成诊断建议",
          description="基于用户查询和上下文信息生成智能诊断建议")
async def generate_diagnosis(request: DiagnosisRequest):
    """
    生成诊断建议

    Args:
        request: 诊断请求对象

    Returns:
        诊断结果
    """
    try:
        logger.info(f"收到诊断请求: query='{request.query}', response_type='{request.response_type}'")

        # 调用核心服务
        result = diagnosis_service.process_diagnosis_request(
            query=request.query,
            context=request.context,
            response_type=request.response_type,
            enable_summary=request.enable_summary
        )

        logger.info(f"诊断请求处理完成: success={result['success']}")
        return result

    except Exception as e:
        logger.error(f"诊断请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"诊断服务错误: {str(e)}")
```

**接口特性：**

- **POST 方法**: 使用 POST 方法接收请求
- **参数验证**: 自动验证请求参数
- **错误处理**: 统一的错误处理机制
- **日志记录**: 详细的请求日志
- **响应封装**: 标准化的响应格式

#### 3.2 文本摘要接口

```python
@app.post("/diagnosis/summarize",
          summary="文本摘要处理",
          description="对输入的医学文本进行摘要处理")
async def summarize_text(request: SummarizeRequest):
    """
    文本摘要处理

    Args:
        request: 摘要请求对象

    Returns:
        摘要结果
    """
    try:
        logger.info(f"收到摘要请求: text_length={len(request.text)}, max_length={request.max_length}")

        # 调用摘要服务
        summary = diagnosis_service.summarization_service.summarize_medical_text(
            text=request.text,
            max_length=request.max_length,
            min_length=request.min_length
        )

        result = {
            "original_text": request.text,
            "summary": summary,
            "summary_length": len(summary),
            "success": True
        }

        logger.info(f"摘要请求处理完成: summary_length={len(summary)}")
        return result

    except Exception as e:
        logger.error(f"摘要请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"摘要服务错误: {str(e)}")
```

**接口特性：**

- **专业摘要**: 专门针对医学文本优化
- **长度控制**: 灵活的长度设置
- **质量保证**: 确保摘要质量
- **性能优化**: 高效的摘要生成

#### 3.3 流式诊断接口

```python
@app.post("/diagnosis/stream",
          summary="流式诊断响应",
          description="提供实时流式诊断响应")
async def stream_diagnosis(request: StreamRequest):
    """
    流式诊断响应

    Args:
        request: 流式请求对象

    Returns:
        流式响应
    """
    try:
        logger.info(f"收到流式诊断请求: query='{request.query}', response_type='{request.response_type}'")

        def generate_response():
            """生成流式响应"""
            try:
                for chunk in diagnosis_service.process_diagnosis_request_stream(
                    query=request.query,
                    context=request.context,
                    response_type=request.response_type,
                    enable_summary=request.enable_summary
                ):
                    yield f"data: {chunk}\n\n"

                # 发送结束标记
                yield "data: [DONE]\n\n"

            except Exception as e:
                logger.error(f"流式响应生成失败: {e}")
                yield f"data: 生成诊断建议时出现错误：{str(e)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )

    except Exception as e:
        logger.error(f"流式诊断请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"流式诊断服务错误: {str(e)}")
```

**接口特性：**

- **实时响应**: 逐步返回生成结果
- **流式格式**: 使用 Server-Sent Events 格式
- **错误恢复**: 流式错误处理
- **连接管理**: 保持连接状态

#### 3.4 健康检查接口

```python
@app.get("/diagnosis/health",
         summary="健康检查",
         description="检查服务健康状态")
async def health_check():
    """
    健康检查

    Returns:
        健康状态信息
    """
    try:
        health_status = diagnosis_service.health_check()
        status_code = 200 if health_status['status'] == 'healthy' else 503

        return JSONResponse(
            content=health_status,
            status_code=status_code
        )

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            content={
                "service": "intelligent_diagnosis_service",
                "status": "unhealthy",
                "error": str(e)
            },
            status_code=503
        )
```

**接口特性：**

- **状态监控**: 实时监控服务状态
- **组件检查**: 检查各子组件状态
- **状态码**: 根据健康状态返回相应状态码
- **错误处理**: 健康检查异常处理

#### 3.5 服务信息接口

```python
@app.get("/diagnosis/info",
         summary="服务信息",
         description="获取服务详细信息")
async def get_service_info():
    """
    获取服务信息

    Returns:
        服务信息
    """
    try:
        service_info = diagnosis_service.get_service_info()
        return service_info

    except Exception as e:
        logger.error(f"获取服务信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取服务信息错误: {str(e)}")
```

**接口特性：**

- **详细信息**: 提供完整的服务信息
- **版本信息**: 包含服务版本信息
- **配置信息**: 显示当前配置
- **状态信息**: 显示运行状态

## 📊 请求/响应格式

### 1. 诊断请求格式

```json
{
  "query": "我最近经常感到胸痛，这是什么原因？",
  "context": "胸痛可能由多种原因引起，包括心血管疾病、肺部疾病、消化系统疾病等。需要根据具体症状和检查结果进行诊断。",
  "response_type": "diagnosis",
  "enable_summary": true
}
```

### 2. 诊断响应格式

```json
{
  "query": "我最近经常感到胸痛，这是什么原因？",
  "context": "胸痛可能由多种原因引起，包括心血管疾病、肺部疾病、消化系统疾病等。需要根据具体症状和检查结果进行诊断。",
  "response_type": "diagnosis",
  "summary": "胸痛可能由心血管疾病引起，需要进一步检查确诊。",
  "diagnosis_response": "根据您描述的症状，胸痛可能由多种原因引起。建议您：1. 及时就医检查 2. 进行心电图检查 3. 注意休息，避免剧烈运动。",
  "success": true,
  "error": null
}
```

### 3. 摘要请求格式

```json
{
  "text": "胸痛是一种常见的症状，可能由多种原因引起。心血管疾病是最常见的原因之一，包括心绞痛、心肌梗死等。此外，肺部疾病、消化系统疾病、肌肉骨骼疾病等也可能导致胸痛。",
  "max_length": 200,
  "min_length": 50
}
```

### 4. 摘要响应格式

```json
{
  "original_text": "胸痛是一种常见的症状，可能由多种原因引起...",
  "summary": "胸痛可能由心血管疾病、肺部疾病、消化系统疾病等多种原因引起。",
  "summary_length": 45,
  "success": true
}
```

### 5. 流式响应格式

```
data: 根据您描述的症状

data: 胸痛可能由多种原因引起

data: 建议您及时就医检查

data: [DONE]
```

## 🔍 错误处理

### 1. 错误类型

#### 1.1 参数验证错误 (422)

```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 1.2 服务错误 (500)

```json
{
  "detail": "诊断服务错误: 模型加载失败"
}
```

#### 1.3 健康检查错误 (503)

```json
{
  "service": "intelligent_diagnosis_service",
  "status": "unhealthy",
  "error": "LLM服务初始化失败"
}
```

### 2. 错误处理策略

```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "内部服务器错误", "status_code": 500}
    )
```

## 🔧 中间件配置

### 1. CORS 中间件

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

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

## 📚 API 文档

### 1. Swagger 文档

- **访问地址**: http://localhost:8003/diagnosis/docs
- **功能**: 交互式 API 文档
- **特性**: 在线测试、参数说明、响应示例

### 2. ReDoc 文档

- **访问地址**: http://localhost:8003/diagnosis/redoc
- **功能**: 静态 API 文档
- **特性**: 详细说明、格式规范、易于阅读

### 3. OpenAPI 规范

```yaml
openapi: 3.0.0
info:
  title: 智诊通智能诊断服务
  description: 基于大语言模型的医疗智能诊断服务
  version: 1.0.0
servers:
  - url: http://localhost:8003
    description: 开发服务器
paths:
  /diagnosis/generate:
    post:
      summary: 生成诊断建议
      description: 基于用户查询和上下文信息生成智能诊断建议
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/DiagnosisRequest"
      responses:
        "200":
          description: 成功响应
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/DiagnosisResponse"
```

## 🚀 性能优化

### 1. 异步处理

```python
# 使用异步函数处理请求
async def generate_diagnosis(request: DiagnosisRequest):
    # 异步调用核心服务
    result = await asyncio.get_event_loop().run_in_executor(
        None,
        diagnosis_service.process_diagnosis_request,
        request.query,
        request.context,
        request.response_type,
        request.enable_summary
    )
    return result
```

### 2. 连接池管理

```python
# 配置连接池
app.state.connection_pool = {
    "max_connections": 100,
    "timeout": 30,
    "retry_attempts": 3
}
```

### 3. 缓存机制

```python
# 添加缓存中间件
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="diagnosis-cache")
```

## 🔒 安全考虑

### 1. 输入验证

```python
# 严格的参数验证
class DiagnosisRequest(BaseModel):
    query: str = Field(..., regex=r'^[a-zA-Z0-9\u4e00-\u9fa5\s.,!?]+$')
    context: str = Field(..., max_length=10000)
    response_type: str = Field(..., regex=r'^(diagnosis|advice|explanation)$')
```

### 2. 速率限制

```python
# 添加速率限制
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/diagnosis/generate")
@limiter.limit("10/minute")
async def generate_diagnosis(request: Request, diagnosis_request: DiagnosisRequest):
    # 处理请求
    pass
```

### 3. 身份验证

```python
# 添加身份验证（可选）
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    # 验证token逻辑
    if not verify_jwt_token(token.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return token
```

## 🎯 使用示例

### 1. Python 客户端示例

```python
import requests
import json

# 诊断请求示例
def generate_diagnosis(query, context=""):
    url = "http://localhost:8003/diagnosis/generate"
    data = {
        "query": query,
        "context": context,
        "response_type": "diagnosis",
        "enable_summary": True
    }

    response = requests.post(url, json=data)
    return response.json()

# 使用示例
result = generate_diagnosis(
    query="我最近经常感到胸痛，这是什么原因？",
    context="胸痛可能由多种原因引起..."
)
print(result)
```

### 2. JavaScript 客户端示例

```javascript
// 诊断请求示例
async function generateDiagnosis(query, context = "") {
  const url = "http://localhost:8003/diagnosis/generate";
  const data = {
    query: query,
    context: context,
    response_type: "diagnosis",
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
generateDiagnosis("我最近经常感到胸痛，这是什么原因？")
  .then((result) => console.log(result))
  .catch((error) => console.error(error));
```

### 3. 流式请求示例

```python
import requests

# 流式诊断请求
def stream_diagnosis(query, context=""):
    url = "http://localhost:8003/diagnosis/stream"
    data = {
        "query": query,
        "context": context,
        "response_type": "diagnosis",
        "enable_summary": True
    }

    response = requests.post(url, json=data, stream=True)

    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = line[6:]  # 移除 'data: ' 前缀
                if data == '[DONE]':
                    break
                print(data, end='', flush=True)

# 使用示例
stream_diagnosis("我最近经常感到胸痛，这是什么原因？")
```

## 🔧 部署配置

### 1. 环境变量配置

```bash
# 服务配置
DIAGNOSIS_HOST=0.0.0.0
DIAGNOSIS_PORT=8003
DIAGNOSIS_WORKERS=4
DIAGNOSIS_LOG_LEVEL=info

# 模型配置
MODEL_PATH=/path/to/models
CUDA_VISIBLE_DEVICES=0
```

### 2. Docker 配置

```dockerfile
FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8003

CMD ["python", "start_diagnosis_service.py", "--host", "0.0.0.0", "--port", "8003"]
```

### 3. Nginx 配置

```nginx
server {
    listen 80;
    server_name diagnosis.example.com;

    location / {
        proxy_pass http://localhost:8003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /diagnosis/stream {
        proxy_pass http://localhost:8003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_cache off;
    }
}
```

---

**文档版本**: v1.0.0  
**创建时间**: 2024 年 12 月  
**最后更新**: 2024 年 12 月  
**维护状态**: ✅ 持续更新
