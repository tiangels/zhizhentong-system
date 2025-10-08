# 真流式输出系统使用指南

## 🚀 概述

本系统实现了真正的流式输出功能，支持实时生成和传输 AI 回复内容，提供更好的用户体验。

## ✨ 核心特性

### 🌊 真流式输出

- **实时传输**: 每个 token 生成后立即传输给用户
- **低延迟**: 首次响应时间 < 0.5 秒
- **可中断**: 支持中途停止生成过程
- **状态监控**: 实时显示生成进度和状态

### 🔧 技术实现

- **SSE 协议**: 使用 Server-Sent Events 进行实时数据传输
- **异步处理**: 基于 FastAPI 的异步架构
- **智能回退**: 支持伪流式和混合模式
- **性能优化**: 最小化延迟和资源消耗

## 🏗️ 系统架构

```
用户请求 → 前端界面 → 后端API → RAG服务 → AI模型
    ↓           ↓         ↓        ↓        ↓
实时显示 ← SSE流式 ← 流式处理 ← 流式生成 ← 流式输出
```

## 📋 配置说明

### 环境变量配置

```bash
# 流式输出模式
STREAMING_MODE=real          # 可选: real, pseudo, hybrid

# 真流式配置
REAL_STREAMING_ENABLED=true
REAL_STREAMING_CHUNK_SIZE=1
REAL_STREAMING_DELAY_MS=0
REAL_STREAMING_TIMEOUT=60.0

# 伪流式配置（回退模式）
PSEUDO_STREAMING_CHUNK_SIZE=20
PSEUDO_STREAMING_DELAY_MS=100
PSEUDO_STREAMING_TIMEOUT=30.0

# 混合模式配置
HYBRID_STREAMING_THRESHOLD=0.8
HYBRID_STREAMING_FALLBACK=true
HYBRID_STREAMING_TIMEOUT=45.0
```

### 配置文件

使用 `streaming.env` 文件进行配置：

```bash
# 加载配置
source codes/backend/streaming.env
```

## 🚀 快速开始

### 1. 启动服务

```bash
# 使用启动脚本（推荐）
./codes/start_with_real_streaming.sh

# 或手动启动
cd codes/backend
source streaming.env
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. 测试流式输出

```bash
# 运行测试脚本
python codes/test_real_streaming.py

# 或使用curl测试
curl -X POST "http://localhost:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"question": "什么是人工智能？", "streaming": true}'
```

### 3. 前端集成

```javascript
// 前端流式输出示例
const eventSource = new EventSource("/api/chat/stream");

eventSource.onmessage = function (event) {
  const data = JSON.parse(event.data);

  if (data.type === "content") {
    // 实时显示内容
    document.getElementById("response").innerHTML += data.content;
  } else if (data.type === "done") {
    // 生成完成
    eventSource.close();
  }
};
```

## 🔌 API 接口

### 流式聊天接口

**端点**: `POST /api/chat/stream`

**请求参数**:

```json
{
  "question": "用户问题",
  "streaming": true,
  "streaming_mode": "real"
}
```

**响应格式** (SSE):

```
data: {"type": "content", "content": "部分回复内容"}
data: {"type": "content", "content": "更多内容"}
data: {"type": "done", "total_tokens": 150, "duration": 2.5}
data: [DONE]
```

### 状态监控接口

**端点**: `GET /api/streaming/status`

**响应**:

```json
{
  "streaming_mode": "real",
  "active_connections": 5,
  "total_requests": 100,
  "average_response_time": 1.2
}
```

## 🧪 测试和调试

### 测试脚本

```bash
# 运行完整测试套件
python codes/test_real_streaming.py

# 测试特定功能
python -c "
import asyncio
from test_real_streaming import StreamingTester
tester = StreamingTester()
asyncio.run(tester.test_streaming_chat('测试问题', '单次测试'))
"
```

### 性能监控

```bash
# 监控服务状态
curl http://localhost:8000/api/streaming/status

# 查看日志
tail -f logs/streaming.log
```

## 🔧 故障排除

### 常见问题

1. **流式输出不工作**

   ```bash
   # 检查服务状态
   curl http://localhost:8000/health
   curl http://localhost:8001/health

   # 检查配置
   echo $STREAMING_MODE
   ```

2. **响应延迟过高**

   ```bash
   # 调整配置
   export REAL_STREAMING_DELAY_MS=0
   export REAL_STREAMING_CHUNK_SIZE=1
   ```

3. **连接中断**

   ```bash
   # 检查网络连接
   ping localhost

   # 检查端口占用
   lsof -i :8000
   lsof -i :8001
   ```

### 调试模式

```bash
# 启用调试日志
export STREAMING_DEBUG=true
export STREAMING_LOG_LEVEL=DEBUG

# 查看详细日志
tail -f logs/streaming_debug.log
```

## 📊 性能优化

### 配置优化

1. **最小化延迟**:

   ```bash
   REAL_STREAMING_DELAY_MS=0
   REAL_STREAMING_CHUNK_SIZE=1
   ```

2. **提高吞吐量**:

   ```bash
   REAL_STREAMING_CHUNK_SIZE=5
   REAL_STREAMING_DELAY_MS=50
   ```

3. **平衡模式**:
   ```bash
   REAL_STREAMING_CHUNK_SIZE=3
   REAL_STREAMING_DELAY_MS=20
   ```

### 监控指标

- **首次响应时间**: < 0.5 秒
- **平均响应时间**: < 2 秒
- **吞吐量**: > 10 tokens/秒
- **连接稳定性**: > 99%

## 🔄 模式切换

### 真流式模式 (推荐)

```bash
export STREAMING_MODE=real
export REAL_STREAMING_ENABLED=true
```

### 伪流式模式 (回退)

```bash
export STREAMING_MODE=pseudo
export PSEUDO_STREAMING_CHUNK_SIZE=20
```

### 混合模式 (智能)

```bash
export STREAMING_MODE=hybrid
export HYBRID_STREAMING_THRESHOLD=0.8
```

## 📈 最佳实践

1. **前端实现**:

   - 使用 EventSource API
   - 实现错误重连机制
   - 显示加载状态和进度

2. **后端优化**:

   - 合理设置超时时间
   - 监控资源使用情况
   - 实现优雅降级

3. **用户体验**:
   - 提供中断功能
   - 显示生成进度
   - 支持多轮对话

## 🆘 技术支持

如遇到问题，请：

1. 查看日志文件
2. 运行测试脚本
3. 检查服务状态
4. 参考故障排除指南

---

**注意**: 真流式输出需要 AI 模型支持流式生成，请确保使用的模型支持此功能。
