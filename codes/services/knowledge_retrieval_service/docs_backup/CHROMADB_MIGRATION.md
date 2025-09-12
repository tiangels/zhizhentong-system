# ChromaDB迁移说明

## 概述
将knowledge_retrieval_service中的FAISS向量数据库替换为ChromaDB，以统一整个系统的向量数据库使用。

## 主要更改

### 1. vector_service.py
- **初始化方法**: 将FAISS索引替换为ChromaDB实例
- **添加向量**: 使用`add_documents`方法替代FAISS的`add`方法
- **搜索方法**: 使用`similarity_search_with_score_by_vector`替代FAISS的`search`方法
- **保存/加载**: ChromaDB自动持久化，简化了保存和加载逻辑
- **统计信息**: 使用`_collection.count()`替代FAISS的`ntotal`属性

### 2. retrieval_service.py
- **初始化**: 集成ChromaDB和HuggingFaceEmbeddings
- **文档添加**: 同时支持ChromaDB和本地numpy数组存储
- **语义检索**: 使用ChromaDB的相似度搜索API
- **结果格式**: 统一返回格式，包含文档内容和元数据

### 3. requirements.txt
- 移除FAISS依赖
- 添加ChromaDB相关依赖：
  - `chromadb>=0.4.0`
  - `langchain-chroma>=0.1.0`
  - `langchain-community>=0.0.10`

## 优势

1. **统一性**: 整个系统现在都使用ChromaDB作为向量数据库
2. **持久化**: ChromaDB提供更好的持久化支持
3. **元数据**: 更好的元数据管理和查询能力
4. **扩展性**: ChromaDB支持更复杂的查询和过滤
5. **维护性**: 减少了对FAISS的依赖，简化了部署

## 兼容性

- 保留了numpy数组作为备用存储
- 保持了原有的API接口不变
- 结果格式保持一致

## 注意事项

1. 需要安装新的依赖包
2. 现有的向量数据库文件需要重新构建
3. 确保ChromaDB的持久化目录有适当的权限

## 安装新依赖

```bash
pip install chromadb>=0.4.0 langchain-chroma>=0.1.0 langchain-community>=0.0.10
```

## 测试建议

1. 测试向量添加功能
2. 测试相似度搜索功能
3. 测试持久化功能
4. 验证检索结果的一致性


