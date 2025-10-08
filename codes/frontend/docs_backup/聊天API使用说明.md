# 智诊通聊天 API 使用说明

## 概述

智诊通系统新增了专门的聊天 API 端点，让前端可以更方便地与 AI 进行智能对话。这些 API 支持普通聊天和流式聊天两种模式。

## 新增 API 端点

### 1. 普通聊天 API

**端点**: `POST /api/v1/conversations/chat`

**功能**: 与 AI 进行智能聊天，自动创建或使用现有对话

**请求参数**:

```json
{
  "content": "你好，我最近感觉头痛，请问可能是什么原因？",
  "message_type": "text",
  "conversation_id": "可选，如果不提供则自动创建新对话"
}
```

**响应示例**:

```json
{
  "message": {
    "id": "msg_123",
    "conversation_id": "conv_456",
    "role": "user",
    "content": "你好，我最近感觉头痛，请问可能是什么原因？",
    "content_type": "text",
    "message_data": {},
    "is_processed": true,
    "created_at": "2024-01-01T12:00:00Z"
  },
  "conversation": {
    "id": "conv_456",
    "user_id": "user_789",
    "title": "你好，我最近感觉头痛，请问可能是什么原因？",
    "status": "active",
    "conversation_type": "chat",
    "meta_data": { "auto_created": true },
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z",
    "message_count": 2
  },
  "ai_response": "您好！头痛可能有很多原因，包括紧张性头痛、偏头痛、感冒等。建议您详细描述症状，如疼痛位置、持续时间、伴随症状等，这样我可以更好地帮助您分析可能的原因。"
}
```

### 2. 流式聊天 API

**端点**: `POST /api/v1/conversations/chat/stream`

**功能**: 与 AI 进行流式智能聊天，实时接收 AI 回复

**请求参数**: 与普通聊天 API 相同

**响应格式**: Server-Sent Events (SSE)

**流式数据格式**:

```
data: {"type": "start", "message": "开始生成回复...", "timestamp": "2024-01-01T12:00:00Z"}

data: {"type": "content", "content": "您好！", "full_content": "您好！"}

data: {"type": "content", "content": "头痛可能有很多原因", "full_content": "您好！头痛可能有很多原因"}

data: {"type": "done", "message": "回复生成完成", "user_message_id": "msg_123", "ai_message_id": "msg_124", "full_content": "完整的AI回复内容", "timestamp": "2024-01-01T12:00:00Z"}

data: {"type": "end", "timestamp": "2024-01-01T12:00:00Z"}
```

## 使用示例

### Python 示例

```python
import requests
import json

# 设置API基础URL和认证头
BASE_URL = "http://localhost:8000"
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN",
    "Content-Type": "application/json"
}

# 普通聊天
def chat_with_ai(message):
    data = {
        "content": message,
        "message_type": "text"
    }

    response = requests.post(f"{BASE_URL}/api/v1/conversations/chat",
                           json=data, headers=headers)

    if response.status_code == 200:
        result = response.json()
        return result['ai_response']
    else:
        return f"错误: {response.status_code} - {response.text}"

# 流式聊天
def chat_with_ai_stream(message):
    data = {
        "content": message,
        "message_type": "text"
    }

    response = requests.post(f"{BASE_URL}/api/v1/conversations/chat/stream",
                           json=data, headers=headers, stream=True)

    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        if data.get('type') == 'content':
                            print(data.get('content', ''), end='', flush=True)
                        elif data.get('type') == 'done':
                            print(f"\n\n完整回复: {data.get('full_content', '')}")
                    except json.JSONDecodeError:
                        pass

# 使用示例
if __name__ == "__main__":
    # 普通聊天
    print("普通聊天:")
    response = chat_with_ai("你好，我最近感觉头痛，请问可能是什么原因？")
    print(response)

    print("\n" + "="*50 + "\n")

    # 流式聊天
    print("流式聊天:")
    chat_with_ai_stream("请详细解释一下高血压的症状和预防方法")
```

### JavaScript 示例

```javascript
// 普通聊天
async function chatWithAI(message) {
  const response = await fetch("/api/v1/conversations/chat", {
    method: "POST",
    headers: {
      Authorization: "Bearer YOUR_ACCESS_TOKEN",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      content: message,
      message_type: "text",
    }),
  });

  if (response.ok) {
    const result = await response.json();
    return result.ai_response;
  } else {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
}

// 流式聊天
async function chatWithAIStream(message, onContent, onComplete) {
  const response = await fetch("/api/v1/conversations/chat/stream", {
    method: "POST",
    headers: {
      Authorization: "Bearer YOUR_ACCESS_TOKEN",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      content: message,
      message_type: "text",
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split("\n");

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.type === "content") {
            onContent(data.content);
          } else if (data.type === "done") {
            onComplete(data.full_content);
          }
        } catch (e) {
          console.error("解析SSE数据失败:", e);
        }
      }
    }
  }
}

// 使用示例
document.getElementById("sendButton").addEventListener("click", async () => {
  const message = document.getElementById("messageInput").value;

  // 普通聊天
  try {
    const response = await chatWithAI(message);
    document.getElementById("response").textContent = response;
  } catch (error) {
    console.error("聊天失败:", error);
  }

  // 流式聊天
  try {
    await chatWithAIStream(
      message,
      (content) => {
        // 实时显示内容
        document.getElementById("streamResponse").textContent += content;
      },
      (fullContent) => {
        // 显示完整内容
        console.log("完整回复:", fullContent);
      }
    );
  } catch (error) {
    console.error("流式聊天失败:", error);
  }
});
```

## 特性说明

### 1. 自动对话管理

- 如果不提供 `conversation_id`，系统会自动创建新对话
- 如果提供 `conversation_id`，系统会使用现有对话继续聊天
- 自动维护对话上下文，支持多轮对话

### 2. RAG 增强

- 集成了 RAG（检索增强生成）技术
- 基于医疗知识库提供更准确的回答
- 支持文档检索和上下文理解

### 3. 错误处理

- 完善的错误处理机制
- 当 RAG 服务不可用时，提供备用回复
- 详细的日志记录和错误信息

### 4. 性能优化

- 支持异步处理
- 流式响应减少延迟
- 数据库操作优化

## 测试

运行测试脚本：

```bash
python test_chat_api.py
```

测试脚本会：

1. 注册测试用户
2. 用户登录获取访问令牌
3. 测试普通聊天 API
4. 测试流式聊天 API
5. 测试获取对话列表

## 注意事项

1. **认证要求**: 所有聊天 API 都需要有效的 JWT 访问令牌
2. **内容长度**: 建议单次消息内容不超过 1000 字符
3. **并发限制**: 建议单个用户同时最多进行 3 个流式聊天会话
4. **错误处理**: 请妥善处理网络错误和 API 错误
5. **流式连接**: 流式聊天需要保持连接，注意处理连接断开的情况

## 相关 API

- `GET /api/v1/conversations/` - 获取对话列表
- `GET /api/v1/conversations/{conversation_id}` - 获取对话详情
- `GET /api/v1/conversations/{conversation_id}/messages` - 获取对话消息
- `POST /api/v1/conversations/{conversation_id}/messages` - 发送消息到指定对话
- `POST /api/v1/conversations/{conversation_id}/messages/stream` - 流式发送消息到指定对话

## 更新日志

- **2024-01-01**: 新增普通聊天 API (`/chat`)
- **2024-01-01**: 新增流式聊天 API (`/chat/stream`)
- **2024-01-01**: 支持自动对话创建和管理
- **2024-01-01**: 集成 RAG 服务增强回答质量
