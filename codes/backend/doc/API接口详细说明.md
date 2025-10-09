# 智诊通系统 API 接口详细说明

## 📋 概述

本文档详细说明智诊通系统后端提供的所有 API 接口，包括请求参数、响应格式、错误处理等信息。

---

## 🔐 认证相关接口

### 基础信息

- **基础路径**: `/auth`
- **认证方式**: JWT Bearer Token
- **内容类型**: `application/json`

### 1. 用户注册

**接口**: `POST /auth/register`

**功能**: 用户注册新账户

**请求参数**:

```json
{
  "username": "string", // 用户名（唯一，必填）
  "email": "string", // 邮箱（唯一，必填）
  "password": "string", // 密码（必填）
  "full_name": "string", // 全名（可选）
  "phone": "string" // 手机号（可选）
}
```

**响应格式**:

```json
{
  "access_token": "string", // JWT访问令牌
  "token_type": "bearer", // 令牌类型
  "expires_in": 1800, // 过期时间（秒）
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "full_name": "string",
    "phone": "string",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

**错误响应**:

- `400`: 用户名或邮箱已存在
- `422`: 请求参数验证失败

### 2. 用户登录

**接口**: `POST /auth/login`

**功能**: 用户登录获取访问令牌

**请求参数**:

```json
{
  "username": "string", // 用户名或邮箱
  "password": "string" // 密码
}
```

**响应格式**: 同注册接口

**错误响应**:

- `401`: 用户名或密码错误
- `422`: 请求参数验证失败

### 3. 获取当前用户信息

**接口**: `GET /auth/me`

**功能**: 获取当前登录用户的详细信息

**请求头**: `Authorization: Bearer <token>`

**响应格式**:

```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "full_name": "string",
  "phone": "string",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

### 4. 更新用户信息

**接口**: `PUT /auth/me`

**功能**: 更新当前用户的基本信息

**请求头**: `Authorization: Bearer <token>`

**请求参数**:

```json
{
  "full_name": "string", // 全名（可选）
  "phone": "string" // 手机号（可选）
}
```

### 5. 用户登出

**接口**: `POST /auth/logout`

**功能**: 用户登出，使当前令牌失效

**请求头**: `Authorization: Bearer <token>`

**响应格式**:

```json
{
  "message": "登出成功"
}
```

---

## 💬 对话管理接口

### 基础信息

- **基础路径**: `/api/v1/conversations`
- **认证方式**: JWT Bearer Token
- **内容类型**: `application/json`

### 1. 获取对话列表

**接口**: `GET /api/v1/conversations/`

**功能**: 获取当前用户的所有对话列表

**请求头**: `Authorization: Bearer <token>`

**查询参数**:

- `page`: 页码（默认 1）
- `size`: 每页数量（默认 10，最大 100）
- `status`: 对话状态筛选（可选）

**响应格式**:

```json
{
  "conversations": [
    {
      "id": "uuid",
      "title": "string",
      "conversation_type": "general",
      "status": "active",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z",
      "message_count": 10
    }
  ],
  "total": 50,
  "page": 1,
  "size": 10,
  "pages": 5
}
```

### 2. 创建对话

**接口**: `POST /api/v1/conversations/`

**功能**: 创建新的对话会话

**请求头**: `Authorization: Bearer <token>`

**请求参数**:

```json
{
  "title": "string", // 对话标题（可选）
  "conversation_type": "general", // 对话类型：general/diagnosis/consultation
  "status": "active" // 对话状态（可选，默认active）
}
```

**响应格式**:

```json
{
  "id": "uuid",
  "title": "string",
  "conversation_type": "general",
  "status": "active",
  "user_id": "uuid",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

### 3. 获取对话详情

**接口**: `GET /api/v1/conversations/{conversation_id}`

**功能**: 获取指定对话的详细信息

**请求头**: `Authorization: Bearer <token>`

**路径参数**:

- `conversation_id`: 对话 ID（UUID 格式）

**响应格式**:

```json
{
  "id": "uuid",
  "title": "string",
  "conversation_type": "general",
  "status": "active",
  "user_id": "uuid",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z",
  "messages": [
    {
      "id": "uuid",
      "content": "string",
      "message_type": "user",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

### 4. 更新对话

**接口**: `PUT /api/v1/conversations/{conversation_id}`

**功能**: 更新对话信息

**请求头**: `Authorization: Bearer <token>`

**请求参数**:

```json
{
  "title": "string", // 对话标题（可选）
  "status": "string" // 对话状态（可选）
}
```

### 5. 删除对话

**接口**: `DELETE /api/v1/conversations/{conversation_id}`

**功能**: 删除指定对话

**请求头**: `Authorization: Bearer <token>`

**响应格式**:

```json
{
  "message": "对话删除成功"
}
```

### 6. 发送消息（同步）

**接口**: `POST /api/v1/conversations/{conversation_id}/messages`

**功能**: 向对话发送消息并获取 AI 回复

**请求头**: `Authorization: Bearer <token>`

**请求参数**:

```json
{
  "content": "string", // 消息内容（必填）
  "message_type": "user", // 消息类型：user/assistant/system
  "metadata": {} // 附加元数据（可选）
}
```

**响应格式**:

```json
{
  "user_message": {
    "id": "uuid",
    "content": "string",
    "message_type": "user",
    "created_at": "2025-01-01T00:00:00Z"
  },
  "assistant_message": {
    "id": "uuid",
    "content": "string",
    "message_type": "assistant",
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

### 7. 发送消息（流式）

**接口**: `POST /api/v1/conversations/{conversation_id}/messages/stream`

**功能**: 向对话发送消息并获取 AI 流式回复

**请求头**: `Authorization: Bearer <token>`

**请求参数**: 同同步消息接口

**响应格式**: Server-Sent Events (SSE)

```
data: {"type": "start", "message": "开始生成回复"}

data: {"type": "content", "content": "部分回复内容"}

data: {"type": "end", "message": "回复生成完成"}
```

---

## 🏥 诊断相关接口

### 基础信息

- **基础路径**: `/api/v1/diagnosis`
- **认证方式**: JWT Bearer Token
- **内容类型**: `application/json`

### 1. 症状分析

**接口**: `POST /api/v1/diagnosis/analyze-symptoms`

**功能**: 分析用户输入的症状信息

**请求参数**:

```json
{
  "symptoms": ["string"], // 症状列表
  "duration": "string", // 持续时间
  "severity": "mild", // 严重程度：mild/moderate/severe
  "additional_info": "string" // 附加信息
}
```

**响应格式**:

```json
{
  "analysis_id": "uuid",
  "possible_conditions": [
    {
      "condition": "string",
      "probability": 0.85,
      "description": "string"
    }
  ],
  "recommendations": [
    {
      "type": "immediate_care",
      "description": "string"
    }
  ],
  "risk_level": "low"
}
```

### 2. 获取诊断历史

**接口**: `GET /api/v1/diagnosis/history`

**功能**: 获取用户的诊断历史记录

**请求头**: `Authorization: Bearer <token>`

**查询参数**:

- `page`: 页码（默认 1）
- `size`: 每页数量（默认 10）

**响应格式**:

```json
{
  "diagnoses": [
    {
      "id": "uuid",
      "symptoms": ["string"],
      "possible_conditions": ["string"],
      "risk_level": "low",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 20,
  "page": 1,
  "size": 10
}
```

---

## 📚 知识检索接口

### 基础信息

- **基础路径**: `/api/v1/knowledge`
- **认证方式**: JWT Bearer Token
- **内容类型**: `application/json`

### 1. 搜索医疗知识

**接口**: `POST /api/v1/knowledge/search`

**功能**: 搜索相关的医疗知识

**请求参数**:

```json
{
  "query": "string", // 搜索查询
  "category": "string", // 知识分类（可选）
  "limit": 10 // 返回结果数量（默认10）
}
```

**响应格式**:

```json
{
  "results": [
    {
      "id": "uuid",
      "title": "string",
      "content": "string",
      "category": "string",
      "relevance_score": 0.95,
      "source": "string"
    }
  ],
  "total": 50
}
```

### 2. 获取知识详情

**接口**: `GET /api/v1/knowledge/{knowledge_id}`

**功能**: 获取指定知识的详细信息

**响应格式**:

```json
{
  "id": "uuid",
  "title": "string",
  "content": "string",
  "category": "string",
  "tags": ["string"],
  "source": "string",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

---

## 🎯 多模态处理接口

### 基础信息

- **基础路径**: `/api/v1/multimodal`
- **认证方式**: JWT Bearer Token
- **内容类型**: `multipart/form-data`

### 1. 处理图像

**接口**: `POST /api/v1/multimodal/process-image`

**功能**: 处理上传的医疗图像

**请求参数**:

- `file`: 图像文件（支持 jpg, png, gif 等格式）
- `analysis_type`: 分析类型（可选）

**响应格式**:

```json
{
  "file_id": "uuid",
  "analysis_results": {
    "detected_objects": ["string"],
    "confidence_scores": [0.95],
    "recommendations": ["string"]
  },
  "processed_at": "2025-01-01T00:00:00Z"
}
```

### 2. 处理音频

**接口**: `POST /api/v1/multimodal/process-audio`

**功能**: 处理上传的音频文件

**请求参数**:

- `file`: 音频文件（支持 mp3, wav, m4a 等格式）

**响应格式**:

```json
{
  "file_id": "uuid",
  "transcription": "string",
  "analysis_results": {
    "sentiment": "positive",
    "key_points": ["string"]
  },
  "processed_at": "2025-01-01T00:00:00Z"
}
```

---

## 🏥 患者管理接口

### 基础信息

- **基础路径**: `/api/v1/patients`
- **认证方式**: JWT Bearer Token
- **内容类型**: `application/json`

### 1. 创建患者档案

**接口**: `POST /api/v1/patients/`

**功能**: 创建新的患者档案

**请求参数**:

```json
{
  "name": "string", // 患者姓名
  "gender": "male", // 性别：male/female/other
  "birth_date": "1990-01-01", // 出生日期
  "phone": "string", // 联系电话
  "emergency_contact": "string", // 紧急联系人
  "medical_history": "string", // 病史
  "allergies": ["string"], // 过敏史
  "medications": ["string"] // 当前用药
}
```

### 2. 获取患者列表

**接口**: `GET /api/v1/patients/`

**功能**: 获取患者列表

**查询参数**:

- `page`: 页码（默认 1）
- `size`: 每页数量（默认 10）
- `search`: 搜索关键词（可选）

### 3. 获取患者详情

**接口**: `GET /api/v1/patients/{patient_id}`

**功能**: 获取指定患者的详细信息

### 4. 更新患者信息

**接口**: `PUT /api/v1/patients/{patient_id}`

**功能**: 更新患者档案信息

### 5. 删除患者档案

**接口**: `DELETE /api/v1/patients/{patient_id}`

**功能**: 删除患者档案

---

## 📁 文件管理接口

### 基础信息

- **基础路径**: `/api/v1/files`
- **认证方式**: JWT Bearer Token
- **内容类型**: `multipart/form-data`

### 1. 上传文件

**接口**: `POST /api/v1/files/upload`

**功能**: 上传文件到服务器

**请求参数**:

- `file`: 文件（支持多种格式）
- `category`: 文件分类（可选）

**响应格式**:

```json
{
  "file_id": "uuid",
  "filename": "string",
  "file_size": 1024000,
  "file_type": "image/jpeg",
  "upload_url": "/api/v1/files/{file_id}",
  "uploaded_at": "2025-01-01T00:00:00Z"
}
```

### 2. 获取文件信息

**接口**: `GET /api/v1/files/{file_id}`

**功能**: 获取文件信息和下载链接

### 3. 删除文件

**接口**: `DELETE /api/v1/files/{file_id}`

**功能**: 删除指定文件

---

## ⚙️ 系统管理接口

### 基础信息

- **基础路径**: `/api/v1/system`
- **认证方式**: JWT Bearer Token
- **内容类型**: `application/json`

### 1. 获取系统信息

**接口**: `GET /api/v1/system/info`

**功能**: 获取系统运行信息

**响应格式**:

```json
{
  "version": "1.0.0",
  "uptime": 3600,
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "vector_db": "healthy"
  },
  "statistics": {
    "total_users": 1000,
    "total_conversations": 5000,
    "total_diagnoses": 2000
  }
}
```

### 2. 健康检查

**接口**: `GET /health`

**功能**: 系统健康检查（无需认证）

**响应格式**:

```json
{
  "status": "healthy",
  "timestamp": 1640995200,
  "uptime_seconds": 3600,
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

---

## 🔧 错误处理

### 标准错误响应格式

```json
{
  "error": "错误描述",
  "detail": "详细错误信息",
  "timestamp": 1640995200,
  "path": "/api/v1/conversations"
}
```

### 常见错误码

| 状态码 | 错误类型              | 描述             |
| ------ | --------------------- | ---------------- |
| 400    | Bad Request           | 请求参数错误     |
| 401    | Unauthorized          | 未认证或令牌无效 |
| 403    | Forbidden             | 权限不足         |
| 404    | Not Found             | 资源不存在       |
| 422    | Unprocessable Entity  | 请求参数验证失败 |
| 500    | Internal Server Error | 服务器内部错误   |

---

## 📝 使用示例

### 完整的对话流程示例

```bash
# 1. 用户注册
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "full_name": "测试用户"
  }'

# 2. 用户登录
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'

# 3. 创建对话（使用返回的token）
curl -X POST "http://localhost:8000/api/v1/conversations/" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "健康咨询",
    "conversation_type": "consultation"
  }'

# 4. 发送消息
curl -X POST "http://localhost:8000/api/v1/conversations/{conversation_id}/messages" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "我最近感觉头痛，请问可能是什么原因？"
  }'
```

---

_本文档基于当前系统实现生成，具体接口可能根据开发进度有所调整。详细 API 文档请参考 `/docs` 接口。_
