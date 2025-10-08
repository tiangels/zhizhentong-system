# 🌊 真流式输出系统

## 📖 简介

本系统实现了真正的流式输出功能，支持 AI 回复的实时生成和传输，提供极佳的用户体验。

## ✨ 核心特性

- **🚀 真流式输出**: 每个 token 实时传输，无延迟
- **⚡ 低延迟**: 首次响应 < 0.5 秒
- **🛑 可中断**: 支持中途停止生成
- **📊 状态监控**: 实时显示生成进度
- **🔄 智能回退**: 自动降级到伪流式模式

## 🏗️ 系统架构

```
用户 → 前端 → 后端API → RAG服务 → AI模型
 ↓      ↓       ↓        ↓        ↓
显示 ← SSE流 ← 流处理 ← 流生成 ← 流输出
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

### 2. 测试功能

```bash
# 快速测试
python codes/quick_streaming_test.py

# 完整测试
python codes/test_real_streaming.py
```

### 3. 访问界面

- 前端界面: http://localhost:3000
- 后端 API: http://localhost:8000
- RAG 服务: http://localhost:8001

## 📁 文件结构

```
codes/
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   └── rag_service.py      # RAG服务集成
│   │   └── api/
│   │       └── chat.py             # 聊天API
│   └── streaming.env               # 流式输出配置
├── start_with_real_streaming.sh   # 启动脚本
├── test_real_streaming.py         # 完整测试
├── quick_streaming_test.py        # 快速测试
├── STREAMING_OUTPUT_GUIDE.md      # 详细文档
└── README_STREAMING.md            # 本文件
```

## 🔧 配置说明

### 环境变量

```bash
# 流式输出模式
STREAMING_MODE=real

# 真流式配置
REAL_STREAMING_ENABLED=true
REAL_STREAMING_CHUNK_SIZE=1
REAL_STREAMING_DELAY_MS=0
REAL_STREAMING_TIMEOUT=60.0
```

### 模式选择

1. **真流式模式** (推荐)

   - 每个 token 实时传输
   - 最低延迟
   - 需要模型支持

2. **伪流式模式** (回退)

   - 分块传输
   - 兼容性好
   - 延迟稍高

3. **混合模式** (智能)
   - 自动选择最佳模式
   - 智能降级
   - 平衡性能

## 🧪 测试功能

### 基础测试

```bash
# 检查服务状态
curl http://localhost:8000/health
curl http://localhost:8001/health

# 测试流式输出
curl -X POST "http://localhost:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"question": "测试问题", "streaming": true}'
```

### 性能测试

```bash
# 运行性能测试
python codes/test_real_streaming.py

# 查看测试结果
# - 首次响应时间
# - 总响应时间
# - 吞吐量统计
```

## 📊 性能指标

- **首次响应时间**: < 0.5 秒
- **平均响应时间**: < 2 秒
- **吞吐量**: > 10 tokens/秒
- **连接稳定性**: > 99%

## 🔍 故障排除

### 常见问题

1. **服务未启动**

   ```bash
   # 检查端口占用
   lsof -i :8000
   lsof -i :8001

   # 重启服务
   ./codes/start_with_real_streaming.sh
   ```

2. **流式输出不工作**

   ```bash
   # 检查配置
   echo $STREAMING_MODE

   # 查看日志
   tail -f logs/streaming.log
   ```

3. **响应延迟高**
   ```bash
   # 优化配置
   export REAL_STREAMING_DELAY_MS=0
   export REAL_STREAMING_CHUNK_SIZE=1
   ```

### 调试模式

```bash
# 启用调试
export STREAMING_DEBUG=true
export STREAMING_LOG_LEVEL=DEBUG

# 查看详细日志
tail -f logs/streaming_debug.log
```

## 📈 优化建议

### 性能优化

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

### 前端优化

```javascript
// 使用EventSource API
const eventSource = new EventSource("/api/chat/stream");

eventSource.onmessage = function (event) {
  const data = JSON.parse(event.data);
  if (data.type === "content") {
    // 实时显示内容
    displayContent(data.content);
  }
};
```

## 📚 文档链接

- [详细使用指南](STREAMING_OUTPUT_GUIDE.md)
- [API 文档](backend/app/api/)
- [配置说明](backend/streaming.env)

## 🆘 技术支持

如遇到问题：

1. 查看日志文件
2. 运行测试脚本
3. 检查服务状态
4. 参考故障排除指南

---

**注意**: 真流式输出需要 AI 模型支持流式生成功能。
