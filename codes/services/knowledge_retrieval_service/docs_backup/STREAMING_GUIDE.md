# RAG流式查询功能使用指南

## 🚀 新功能概述

本次更新为RAG知识检索系统添加了两个重要功能：

1. **内容摘要功能** - 将检索到的内容先摘要到50字以内，提高回答质量
2. **流式输出功能** - 支持实时流式响应，提供更好的用户体验

## 📋 功能特性

### 1. 内容摘要功能
- **自动摘要**: 检索到的文档内容会自动摘要到50字以内
- **保持关键信息**: 摘要过程保留最重要的医学信息
- **提高效率**: 减少大模型处理的内容量，提高响应速度

### 2. 流式输出功能
- **实时响应**: 大模型生成的内容会实时显示
- **状态反馈**: 提供查询进度和状态信息
- **文档展示**: 实时显示检索到的相关文档
- **错误处理**: 完善的错误提示和异常处理

## 🛠️ 技术实现

### 核心组件更新

#### 1. RAG Pipeline (`core/rag_pipeline.py`)
```python
# 新增摘要功能
def _summarize_content(self, content: str, max_length: int = 50) -> str:
    """将内容摘要到指定长度"""
    
# 新增流式查询方法
async def query_stream(self, question: str, top_k: int = 5, 
                      response_type: str = "general", 
                      similarity_threshold: float = 200.0):
    """流式查询方法"""
```

#### 2. LLM Service (`core/llm_service.py`)
```python
# 新增流式生成方法
async def generate_stream(self, prompt: str, max_tokens: int = 1000) -> AsyncGenerator[str, None]:
    """流式生成回答"""
```

#### 3. API端点 (`api/rag_api.py`)
```python
# 新增流式查询端点
@router.post("/query/stream")
async def query_stream(request: QueryRequest):
    """流式查询端点"""
```

## 📡 API接口

### 1. 流式查询接口

**端点**: `POST /query/stream`

**请求参数**:
```json
{
    "question": "心肌梗死有什么症状？",
    "top_k": 5,
    "response_type": "general",
    "similarity_threshold": 200.0
}
```

**响应格式** (Server-Sent Events):
```
data: {"type": "status", "message": "开始检索相关文档..."}

data: {"type": "content", "content": "心肌梗死的主要症状包括："}

data: {"type": "content", "content": "1. 胸痛"}

data: {"type": "documents", "documents": [...]}

data: {"type": "complete", "message": "查询完成"}
```

### 2. 常规查询接口

**端点**: `POST /query`

保持原有功能不变，用于对比测试。

## 🧪 测试方法

### 1. 命令行测试

```bash
# 激活环境
conda activate nlp

# 启动服务
python start_rag_service.py

# 运行流式测试
python test_streaming.py
```

### 2. Web界面测试

1. 启动服务后访问: `http://localhost:8000/../test_streaming.html`
2. 输入问题并选择查询方式
3. 观察流式响应效果

### 3. API测试

```bash
# 流式查询测试
curl -X POST "http://localhost:8000/query/stream" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "心肌梗死有什么症状？",
       "top_k": 3,
       "response_type": "general",
       "similarity_threshold": 200.0
     }'

# 常规查询测试
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "心肌梗死有什么症状？",
       "top_k": 3,
       "response_type": "general",
       "similarity_threshold": 200.0
     }'
```

## 📊 性能对比

| 功能 | 常规查询 | 流式查询 |
|------|----------|----------|
| 响应方式 | 一次性返回 | 实时流式 |
| 用户体验 | 等待完整结果 | 实时看到进度 |
| 错误处理 | 统一错误信息 | 实时错误提示 |
| 文档展示 | 最后显示 | 检索后立即显示 |
| 适用场景 | 简单查询 | 复杂查询、演示 |

## 🔧 配置说明

### 环境要求
- Python 3.9+
- PyTorch 2.0+
- Transformers 4.30+
- FastAPI 0.100+
- Uvicorn 0.20+

### 模型配置
- 确保模型路径正确: `ai_models/llm_models/Medical_Qwen3_17B`
- 检查模型文件完整性
- 确保有足够的GPU内存

### 服务配置
- 默认端口: 8000
- 支持CORS跨域请求
- 自动重载开发模式

## 🚨 故障排除

### 常见问题

1. **流式响应中断**
   - 检查网络连接
   - 确认服务正常运行
   - 查看服务日志

2. **摘要功能异常**
   - 检查模型加载状态
   - 确认GPU内存充足
   - 验证输入内容格式

3. **API调用失败**
   - 检查请求格式
   - 确认参数类型正确
   - 查看错误日志

### 调试方法

```bash
# 查看服务日志
tail -f logs/rag_service.log

# 检查服务状态
curl http://localhost:8000/health

# 测试模型加载
python -c "from core.llm_service import LLMService; print('模型加载成功')"
```

## 📈 未来规划

1. **性能优化**
   - 缓存机制优化
   - 并发处理改进
   - 内存使用优化

2. **功能扩展**
   - 多模态支持
   - 个性化推荐
   - 历史记录管理

3. **用户体验**
   - 更丰富的交互界面
   - 智能建议功能
   - 语音输入支持

## 📞 技术支持

如有问题，请检查：
1. 服务日志文件
2. 模型文件完整性
3. 环境配置正确性
4. 网络连接状态

---

**更新日期**: 2024年12月
**版本**: v2.0.0
**作者**: RAG开发团队
