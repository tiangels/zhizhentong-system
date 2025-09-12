# 智真通RAG系统 - 构建知识库模块

## 概述

本模块是智真通RAG系统的核心组件，负责构建医疗知识库，包括文档加载、数据清洗、文档切分、向量化、质量检查和索引构建等完整流程。为RAG系统提供高质量的向量表示和知识检索服务。

## 🆕 最新更新

- ✅ **新增文档切分功能**: 支持多种切分策略，包括医疗结构化切分
- ✅ **跨模态检索功能**: 支持文本和图像的联合检索
- ✅ **统一向量化服务**: 消除重复功能，优化系统架构
- ✅ **完整测试套件**: 提供全面的系统测试和验证
- ✅ **详细文档**: 完整的系统架构和使用说明

## 目录结构

```
embedding_models/
├── core/                           # 核心功能模块
│   ├── vectorization_service.py    # 统一向量化服务 ⭐
│   ├── medical_knowledge_manager.py # 医疗知识管理器
│   ├── data_analyzer.py            # 数据分析器
│   ├── build_vector_database.py    # 向量数据库构建
│   ├── image_vectorization.py      # 图像向量化
│   ├── simple_cross_modal_retrieval.py # 跨模态检索 ⭐
│   ├── config.json                 # 配置文件
│   └── offline_test.py             # 离线测试
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
├── README_RAG_SYSTEM.md           # 系统架构文档 ⭐ 新增
└── README.md                      # 本文档
```

## 功能特性

### 1. 文档加载与处理
- 支持多种格式：Word、PDF、TXT、Excel、JSON
- 统一的数据预处理管道
- 数据质量分析和清洗
- 格式转换和标准化

### 2. 文档切分 ⭐ 新增
- **多种切分策略**：
  - 固定大小切分
  - 基于句子切分
  - 基于段落切分
  - 基于语义切分
  - **医疗结构化切分**（识别医疗文档章节）
- 保持句子和段落完整性
- 支持重叠切分
- 批量处理优化

### 3. 向量化服务
- **文本向量化**：使用text2vec-base-chinese模型（768维）
- **图像向量化**：使用CLIP模型进行图像编码（512维）
- **多模态处理**：支持文本和图像的联合向量化
- **批量处理优化**：提高处理效率

### 4. 向量数据库
- 基于ChromaDB的向量存储
- 支持相似性搜索
- 持久化存储
- 多模态向量支持

### 5. 跨模态检索 ⭐ 新增
- **文本到文本检索**：通过文本查询找到相关文档
- **图像到文本检索**：通过图像找到相关文本描述
- **混合检索**：结合文本和图像进行更精确的检索
- 支持多种检索策略和重排序

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 下载预训练模型
python models/download_model.py
```

### 2. 基本使用

#### 文档切分

```python
from processors.document_chunker import create_medical_chunker

# 创建医疗文档切分器
chunker = create_medical_chunker()

# 切分文档
chunks = chunker.chunk_document(medical_text, metadata)

# 批量处理文件
results = chunker.batch_chunk_files(input_dir, output_dir)
```

#### 向量化服务

```python
from core.vectorization_service import VectorizationService

# 初始化向量化服务
service = VectorizationService()

# 文本向量化
text_vectors = service.process_texts(texts)

# 图像向量化
image_vectors = service.process_images(image_paths)

# 多模态处理
result = service.process_multimodal(texts, image_paths)
```

#### 跨模态检索

```python
from core.simple_cross_modal_retrieval import SimpleCrossModalRetrieval

# 初始化检索系统
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

### 3. 系统测试

```bash
# 运行完整系统测试
python rag_system_test.py

# 运行离线测试
python core/offline_test.py

# 测试文档切分功能
python processors/document_chunker.py
```

## 配置说明

主要配置文件位于 `config/unified_config.json`：

- `models`: 模型配置（文本和图像向量化模型）
- `data`: 数据路径配置（原始数据、处理后数据、向量数据库）
- `processing`: 处理参数配置（文本处理、图像处理）
- `vector_database`: 向量数据库配置（ChromaDB设置）
- `logging`: 日志配置

## 系统架构

### RAG系统完整流程

```
构建知识库模块：
原始数据 → 文档加载 → 数据清洗 → 文档切分 → 向量化 → 质量检查 → 索引构建

检索生成模块：
用户输入 → 问题预处理 → 问题向量化 → 检索 → 重排序 → 提示词构建 → 大模型生成 → 返回结果
```

### 模块职责分工

- **构建知识库模块**：负责知识库的构建和维护
- **检索生成模块**：负责用户查询的处理和回答生成
- **跨模态检索**：支持文本和图像的联合检索
- **统一向量化服务**：避免重复实现，提高系统一致性

## 开发指南

### 添加新的文档切分策略

1. 在 `processors/document_chunker.py` 中添加新的切分策略
2. 继承 `ChunkStrategy` 枚举
3. 实现对应的切分方法
4. 更新配置和测试

### 扩展向量化模型

1. 在 `models/` 目录下创建新的模型类
2. 实现标准向量化接口
3. 更新配置文件
4. 添加相应的测试

### 添加新的检索策略

1. 在 `core/simple_cross_modal_retrieval.py` 中扩展检索方法
2. 实现新的检索算法
3. 更新配置和文档

## 测试和验证

### 运行测试

```bash
# 完整系统测试
python rag_system_test.py

# 离线功能测试
python core/offline_test.py

# 文档切分测试
python processors/document_chunker.py
```

### 测试报告

测试完成后会生成详细的测试报告，包括：
- 功能测试结果
- 性能指标
- 改进建议
- 系统状态

## 注意事项

1. **模型下载**：首次运行需要下载预训练模型
2. **存储空间**：确保有足够的磁盘空间存储向量数据
3. **GPU加速**：建议使用GPU加速向量化过程
4. **配置一致性**：确保构建知识库模块和检索生成模块使用相同的配置
5. **日志管理**：定期清理日志文件

## 相关文档

- **系统架构文档**: `README_RAG_SYSTEM.md` - 完整的系统架构和使用说明
- **测试报告**: `rag_system_test_report.json` - 详细的测试结果
- **配置文档**: `config/unified_config.json` - 系统配置说明

## 更新日志

- **v2.0.0**: 
  - ✅ 新增文档切分功能，支持多种切分策略
  - ✅ 实现跨模态检索功能
  - ✅ 优化系统架构，消除重复功能
  - ✅ 完善测试套件和文档
- **v1.0.0**: 初始版本，整合现有向量化功能