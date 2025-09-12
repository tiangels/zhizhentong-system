# RAG知识检索系统项目结构

## 📁 项目目录结构

```
knowledge_retrieval_service/
├── 📁 api/                          # API接口层
│   ├── 📁 config/                   # 配置文件
│   │   └── rag_config.json         # RAG系统配置
│   └── rag_api.py                  # API路由和端点
├── 📁 core/                         # 核心业务逻辑
│   ├── config_manager.py           # 配置管理
│   ├── llm_service.py              # 大模型服务 (已更新)
│   ├── rag_pipeline.py             # RAG处理管道 (已更新)
│   ├── retrieval_service.py        # 检索服务
│   └── vector_service.py           # 向量服务
├── 📁 docs_backup/                  # 文档备份
├── 📁 venv/                         # 虚拟环境
├── 🚀 启动脚本
│   ├── start_rag_service.py        # 主启动脚本
│   ├── start_with_streaming.sh     # 流式功能启动脚本
│   ├── quick_start.py              # 快速启动脚本
│   └── deploy_rag_service.sh       # 部署脚本
├── 🧪 测试和演示
│   ├── test_streaming.py           # 流式功能测试
│   ├── test_streaming.html         # Web测试界面
│   └── demo.py                     # 功能演示脚本
├── 📖 文档
│   ├── STREAMING_GUIDE.md          # 流式功能使用指南
│   ├── UPDATE_SUMMARY.md           # 更新总结
│   ├── PROJECT_STRUCTURE.md        # 项目结构说明
│   └── 智诊通RAG检索增强系统完整说明文档.md
├── 🐳 部署文件
│   ├── Dockerfile                  # Docker镜像
│   ├── docker-compose.yml          # Docker编排
│   ├── nginx.conf                  # Nginx配置
│   └── requirements.txt            # Python依赖
└── 🔧 工具脚本
    ├── monitor.sh                  # 监控脚本
    └── quick_start.sh              # 快速启动脚本
```

## 🆕 新增文件说明

### 核心功能文件
- **`core/rag_pipeline.py`** - 添加了内容摘要和流式查询功能
- **`core/llm_service.py`** - 添加了流式生成支持
- **`api/rag_api.py`** - 添加了流式查询API端点

### 测试和演示文件
- **`test_streaming.py`** - 流式功能命令行测试
- **`test_streaming.html`** - Web界面测试页面
- **`demo.py`** - 功能演示脚本

### 启动脚本
- **`start_with_streaming.sh`** - 支持流式功能的启动脚本
- **`quick_start.py`** - 完整的启动和测试流程

### 文档文件
- **`STREAMING_GUIDE.md`** - 详细的使用指南
- **`UPDATE_SUMMARY.md`** - 更新内容总结
- **`PROJECT_STRUCTURE.md`** - 项目结构说明

## 🔧 核心功能更新

### 1. 内容摘要功能
**位置**: `core/rag_pipeline.py`
```python
def _summarize_content(self, content: str, max_length: int = 50) -> str:
    """将内容摘要到指定长度"""
```

### 2. 流式查询功能
**位置**: `core/rag_pipeline.py`
```python
async def query_stream(self, question: str, top_k: int = 5, 
                      response_type: str = "general", 
                      similarity_threshold: float = 200.0):
    """流式查询方法"""
```

### 3. 流式生成支持
**位置**: `core/llm_service.py`
```python
async def generate_stream(self, prompt: str, max_tokens: int = 1000) -> AsyncGenerator[str, None]:
    """流式生成回答"""
```

### 4. 流式API端点
**位置**: `api/rag_api.py`
```python
@router.post("/query/stream")
async def query_stream(request: QueryRequest):
    """流式查询端点"""
```

## 🚀 快速开始

### 1. 环境准备
```bash
conda activate nlp
pip install -r requirements.txt
```

### 2. 启动服务
```bash
# 方式1: 快速启动（推荐）
python quick_start.py

# 方式2: 使用启动脚本
./start_with_streaming.sh

# 方式3: 直接启动
python start_rag_service.py
```

### 3. 测试功能
```bash
# 命令行测试
python test_streaming.py

# 功能演示
python demo.py

# Web界面测试
# 访问: http://localhost:8000/../test_streaming.html
```

## 📡 API接口

### 流式查询
- **端点**: `POST /query/stream`
- **功能**: 实时流式响应
- **格式**: Server-Sent Events

### 常规查询
- **端点**: `POST /query`
- **功能**: 一次性返回结果
- **格式**: JSON

### 健康检查
- **端点**: `GET /health`
- **功能**: 服务状态检查

## 🎯 主要特性

### ✅ 内容摘要
- 自动将检索内容摘要到50字以内
- 保留关键医学信息
- 提高处理效率

### ✅ 流式输出
- 实时显示生成过程
- 状态反馈和进度提示
- 更好的用户体验

### ✅ 错误处理
- 完善的异常处理
- 实时错误提示
- 优雅的降级机制

### ✅ 测试工具
- 命令行测试脚本
- Web界面测试页面
- 功能演示脚本

## 📊 性能优化

### 响应时间
- 流式查询: 实时响应
- 常规查询: 等待完整结果

### 资源使用
- 内容摘要: 减少处理内容量
- 流式输出: 降低内存占用
- 异步处理: 提高并发能力

## 🔍 监控和调试

### 日志文件
- 服务日志: 控制台输出
- 错误日志: 异常信息记录
- 性能日志: 响应时间统计

### 调试工具
- 健康检查端点
- 状态监控脚本
- 错误追踪功能

## 📈 未来规划

### 短期优化
1. 性能调优
2. 错误处理完善
3. 监控和日志

### 长期扩展
1. 多模态支持
2. 个性化推荐
3. 语音交互

---

**项目状态**: ✅ 完成
**版本**: v2.0.0
**最后更新**: 2024年12月
