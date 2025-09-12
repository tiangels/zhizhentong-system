# 智真通RAG系统完整架构文档

## 📋 系统概述

智真通RAG（Retrieval-Augmented Generation）系统是一个基于医疗知识的智能问答系统，采用检索增强生成技术，结合向量化、检索和大语言模型，为医疗领域提供准确、可靠的智能问答服务。

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        智真通RAG系统                              │
├─────────────────────────────────────────────────────────────────┤
│  前端用户界面  │  后端API服务  │  检索生成模块  │  构建知识库模块  │
│  (Vue.js)     │  (FastAPI)   │  (RAG Pipeline) │  (Vectorization) │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌─────────────────────┐
                    │    数据存储层        │
                    │  ┌─────────────────┐ │
                    │  │  向量数据库     │ │
                    │  │  (ChromaDB)     │ │
                    │  └─────────────────┘ │
                    │  ┌─────────────────┐ │
                    │  │  原始数据       │ │
                    │  │  (医疗文档)     │ │
                    │  └─────────────────┘ │
                    └─────────────────────┘
```

## 🔄 RAG系统完整流程

### 1. 构建知识库模块流程

```
原始数据 → 文档加载 → 数据清洗 → 文档切分 → 向量化 → 质量检查 → 索引构建
   ↓         ↓         ↓         ↓         ↓         ↓         ↓
Word/PDF  多格式    去重/过滤   Chunk    向量表示   去重/过滤   向量数据库
TXT/Excel 支持      标准化     切分      生成      质量评估   ChromaDB
```

#### 1.1 文档加载 (Document Loading)
- **功能**: 支持多种格式的医疗文档加载
- **支持格式**: Word、PDF、TXT、Excel、JSON等
- **实现位置**: `codes/ai_models/embedding_models/processors/data_pipeline.py`
- **核心类**: `DataPipeline`

```python
# 使用示例
from processors.data_pipeline import DataPipeline

pipeline = DataPipeline(config)
pipeline.process_vqa_dataset(data_dir, output_dir)
```

#### 1.2 数据清洗 (Data Cleaning)
- **功能**: 去除重复数据、标准化格式、处理缺失值
- **实现位置**: `codes/ai_models/embedding_models/processors/text_preprocessing.py`
- **核心类**: `OptimizedMedicalTextPreprocessor`

**清洗策略**:
- 去除重复记录
- 处理缺失值
- 中文分词处理
- 特殊字符清理
- 格式标准化

#### 1.3 文档切分 (Document Chunking) ⭐ **新增功能**
- **功能**: 将长文档切分为适合向量化的小片段
- **实现位置**: `codes/ai_models/embedding_models/processors/document_chunker.py`
- **核心类**: `DocumentChunker`

**切分策略**:
- `FIXED_SIZE`: 固定大小切分
- `SENTENCE_BASED`: 基于句子切分
- `PARAGRAPH_BASED`: 基于段落切分
- `SEMANTIC_BASED`: 基于语义切分
- `MEDICAL_STRUCTURED`: 医疗结构化切分 ⭐

```python
# 使用示例
from processors.document_chunker import create_medical_chunker

chunker = create_medical_chunker()
chunks = chunker.chunk_document(medical_text, metadata)
```

#### 1.4 向量化 (Vectorization)
- **功能**: 将文本和图像转换为向量表示
- **实现位置**: `codes/ai_models/embedding_models/core/vectorization_service.py`
- **核心类**: `VectorizationService`

**向量化模型**:
- **文本模型**: `text2vec-base-chinese` (768维)
- **图像模型**: `openai/clip-vit-base-patch32` (512维)

```python
# 使用示例
from core.vectorization_service import VectorizationService

service = VectorizationService()
text_vectors = service.process_texts(texts)
image_vectors = service.process_images(image_paths)
```

#### 1.5 质量检查 (Quality Control)
- **功能**: 向量质量评估、去重、过滤
- **实现位置**: `codes/ai_models/embedding_models/core/data_analyzer.py`
- **核心类**: `MedicalDataAnalyzer`

#### 1.6 索引构建 (Index Building)
- **功能**: 构建向量数据库索引
- **实现位置**: `codes/ai_models/embedding_models/core/build_vector_database.py`
- **数据库**: ChromaDB

### 2. 检索生成模块流程

```
用户输入 → 问题预处理 → 问题向量化 → 检索 → 重排序 → 提示词构建 → 大模型生成 → 返回结果
    ↓         ↓           ↓         ↓       ↓         ↓           ↓         ↓
  前端界面   文本清洗    向量表示   相似度   结果优化   上下文构建   Qwen3    格式化
            标准化      生成       搜索     排序      模板填充    生成      输出
```

#### 2.1 问题预处理 (Query Preprocessing)
- **功能**: 清洗和标准化用户输入
- **实现位置**: `codes/services/knowledge_retrieval_service/core/rag_pipeline.py`
- **处理内容**: 去除特殊字符、标准化格式、长度控制

#### 2.2 问题向量化 (Query Vectorization)
- **功能**: 将用户问题转换为向量表示
- **实现位置**: `codes/services/knowledge_retrieval_service/core/vector_service.py`
- **核心类**: `VectorService`

**重要优化**: 现在调用构建知识库模块的向量化服务，避免重复实现

```python
# 使用示例
from core.vector_service import VectorServiceFactory

vector_service = VectorServiceFactory.create_vector_service()
query_vector = vector_service.text_to_vector(user_question)
```

#### 2.3 检索 (Retrieval)
- **功能**: 从向量数据库中检索相关文档
- **实现位置**: `codes/services/knowledge_retrieval_service/core/retrieval_service.py`
- **核心类**: `RetrievalService`

**检索策略**:
- `semantic`: 语义检索
- `hybrid`: 混合检索（语义+关键词）
- `rerank`: 重排序检索

```python
# 使用示例
from core.retrieval_service import RetrievalService

retrieval_service = RetrievalService(config)
results = retrieval_service.retrieve_documents(query_vector, top_k=5)
```

#### 2.4 重排序 (Reranking)
- **功能**: 对检索结果进行重新排序优化
- **实现位置**: `codes/services/knowledge_retrieval_service/core/retrieval_service.py`
- **策略**: 基于相似度分数和相关性权重

#### 2.5 提示词构建 (Prompt Construction)
- **功能**: 构建大语言模型的输入提示词
- **实现位置**: `codes/services/knowledge_retrieval_service/core/rag_pipeline.py`
- **模板**: 包含上下文、问题、指令的完整提示词

#### 2.6 大模型生成 (LLM Generation)
- **功能**: 调用大语言模型生成回答
- **实现位置**: `codes/services/knowledge_retrieval_service/core/llm_service.py`
- **核心类**: `LLMService`
- **模型**: `Medical_Qwen3_17B`

```python
# 使用示例
from core.llm_service import LLMService

llm_service = LLMService(config)
answer = llm_service.generate_medical_response(question, context)
```

## 🗂️ 目录结构详解

### 构建知识库模块 (`codes/ai_models/embedding_models/`)

```
embedding_models/
├── core/                           # 核心功能模块
│   ├── vectorization_service.py    # 统一向量化服务 ⭐
│   ├── medical_knowledge_manager.py # 医疗知识管理器
│   ├── data_analyzer.py            # 数据分析器
│   ├── build_vector_database.py    # 向量数据库构建
│   ├── image_vectorization.py      # 图像向量化
│   ├── simple_cross_modal_retrieval.py # 跨模态检索 ⭐
│   └── config.json                 # 配置文件
├── processors/                     # 数据处理器
│   ├── document_chunker.py         # 文档切分器 ⭐ 新增
│   ├── text_preprocessing.py       # 文本预处理
│   ├── image_text_preprocessing.py # 图像文本联合处理
│   └── data_pipeline.py           # 数据处理管道
├── models/                         # 模型相关
│   ├── image_embedder.py          # 图像嵌入器
│   └── pretrained/                # 预训练模型
├── config/                         # 配置文件
│   ├── unified_config.json        # 统一配置
│   └── medical_knowledge_config.json # 医疗知识配置
├── rag_system_test.py             # RAG系统测试 ⭐ 新增
└── README_RAG_SYSTEM.md           # 系统文档 ⭐ 新增
```

### 检索生成模块 (`codes/services/knowledge_retrieval_service/`)

```
knowledge_retrieval_service/
├── core/                          # 核心服务模块
│   ├── vector_service.py          # 向量化服务（已优化）
│   ├── retrieval_service.py       # 检索服务
│   ├── llm_service.py            # 大语言模型服务
│   ├── rag_pipeline.py           # RAG完整流程
│   └── config_manager.py         # 配置管理器
├── api/                           # API接口
│   ├── rag_api.py                # FastAPI接口
│   └── config/
│       └── rag_config.json       # 配置文件
├── start_rag_service.py          # 启动脚本
├── test_rag_service.py           # 测试脚本
└── README.md                     # 模块文档
```

## 🔧 核心功能实现

### 1. 跨模态检索功能 ⭐

**实现位置**: `codes/ai_models/embedding_models/core/simple_cross_modal_retrieval.py`

**功能特性**:
- 文本到文本检索
- 图像到文本检索
- 混合检索（文本+图像）

```python
# 使用示例
from core.simple_cross_modal_retrieval import SimpleCrossModalRetrieval

retrieval_system = SimpleCrossModalRetrieval()

# 文本检索
text_results = retrieval_system.search_by_text("冠心病症状", top_k=5)

# 图像到文本检索
image_results = retrieval_system.search_by_image("path/to/image.jpg", top_k=5)

# 混合检索
mixed_results = retrieval_system.search_by_text_with_image(
    "心脏疾病", "path/to/image.jpg", top_k=5
)
```

### 2. 文档切分功能 ⭐

**实现位置**: `codes/ai_models/embedding_models/processors/document_chunker.py`

**切分策略**:
- 医疗结构化切分：识别医疗文档章节
- 句子边界切分：保持句子完整性
- 段落边界切分：保持段落完整性
- 固定大小切分：适合批量处理

```python
# 使用示例
from processors.document_chunker import create_medical_chunker

chunker = create_medical_chunker()
chunks = chunker.chunk_document(medical_text, metadata)

# 批量处理文件
results = chunker.batch_chunk_files(input_dir, output_dir)
```

### 3. 统一向量化服务

**实现位置**: `codes/ai_models/embedding_models/core/vectorization_service.py`

**服务特性**:
- 文本向量化
- 图像向量化
- 多模态处理
- 批量处理优化

## 📊 数据流程详解

### 数据存储结构

```
datas/medical_knowledge/
├── text_data/                     # 文本数据
│   ├── raw/                      # 原始数据
│   ├── processed/                # 处理后数据
│   └── embeddings/               # 向量数据
├── image_text_data/              # 图像文本数据
│   ├── raw/                      # 原始数据
│   ├── processed/                # 处理后数据
│   └── embeddings/               # 向量数据
├── voice_data/                   # 语音数据
│   ├── raw/                      # 原始数据
│   ├── processed/                # 处理后数据
│   └── embeddings/               # 向量数据
└── vector_databases/             # 向量数据库
    ├── text/                     # 文本向量数据库
    ├── image/                    # 图像向量数据库
    ├── voice/                    # 语音向量数据库
    └── multimodal/               # 多模态向量数据库
```

### 配置管理

**统一配置文件**: `codes/ai_models/embedding_models/config/unified_config.json`

```json
{
  "models": {
    "text_embedding": {
      "model_name": "text2vec-base-chinese",
      "model_path": "../llm_models/text2vec-base-chinese",
      "max_length": 512,
      "batch_size": 32
    },
    "image_embedding": {
      "model_name": "clip-vit-base-patch32",
      "model_path": "models/pretrained/clip-vit-base-patch32",
      "image_size": 224,
      "batch_size": 16
    }
  },
  "data": {
    "base_dir": "/path/to/medical_knowledge",
    "text_data": {
      "raw_dir": "text_data/raw",
      "processed_dir": "text_data/processed",
      "embeddings_dir": "text_data/embeddings",
      "vector_db_dir": "vector_databases/text"
    }
  }
}
```

## 🧪 测试和验证

### 1. 系统测试

**测试脚本**: `codes/ai_models/embedding_models/rag_system_test.py`

**测试内容**:
- 文档切分功能测试
- 知识库构建功能测试
- 检索生成模块功能测试
- 跨模态检索功能测试
- 系统集成测试

```bash
# 运行完整系统测试
cd codes/ai_models/embedding_models
python rag_system_test.py
```

### 2. 模块测试

```bash
# 测试文档切分功能
python processors/document_chunker.py

# 测试跨模态检索
python core/offline_test.py

# 测试向量化服务
python core/vectorization_service.py
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 下载预训练模型
python models/download_model.py
```

### 2. 构建知识库

```bash
# 数据预处理
python processors/data_pipeline.py

# 构建向量数据库
python core/build_vector_database.py
```

### 3. 启动服务

```bash
# 启动RAG服务
cd codes/services/knowledge_retrieval_service
python start_rag_service.py

# 启动前端
cd codes/frontend
npm run dev
```

## 🔍 系统优化

### 1. 重复功能消除

**优化前问题**:
- 构建知识库模块和检索生成模块都实现了向量化功能
- 配置不一致，模型维度不匹配

**优化后方案**:
- 检索生成模块调用构建知识库模块的向量化服务
- 统一配置管理，确保模型一致性
- 保留备用方案，确保系统稳定性

### 2. 性能优化

- 批量处理优化
- 向量数据库索引优化
- 缓存机制实现
- 异步处理支持

### 3. 扩展性设计

- 模块化架构
- 插件式扩展
- 配置驱动
- 多模态支持

## 📈 系统监控

### 1. 性能指标

- 向量化处理速度
- 检索响应时间
- 生成质量评估
- 系统资源使用

### 2. 日志记录

- 操作日志
- 错误日志
- 性能日志
- 审计日志

## 🔮 未来规划

### 1. 功能扩展

- 支持更多文档格式
- 实现实时学习
- 添加多语言支持
- 增强图像理解能力

### 2. 性能提升

- GPU加速优化
- 分布式处理
- 模型压缩
- 边缘计算支持

### 3. 用户体验

- 智能推荐
- 个性化定制
- 多轮对话
- 可视化界面

## 📞 技术支持

如有问题或建议，请联系开发团队或查看相关文档：

- 系统架构文档: `codes/ai_models/embedding_models/README_RAG_SYSTEM.md`
- 模块使用文档: `codes/services/knowledge_retrieval_service/README.md`
- 测试报告: `rag_system_test_report.json`

---

**版本**: v2.0.0  
**更新时间**: 2024年9月  
**维护团队**: 智真通开发团队
