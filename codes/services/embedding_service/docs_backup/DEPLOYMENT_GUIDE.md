# 智诊通多模态检索系统部署指南

## 🎯 系统概述

智诊通多模态检索系统是一个统一的医疗知识检索平台，支持：
- **文本检索**：通过医疗文本查询相关文档
- **图像检索**：通过医疗图像查询相关文本内容
- **混合检索**：同时支持文本和图像输入

## ✅ 测试状态

### 当前测试结果
- ✅ **数据文件检查**：通过
- ✅ **文本检索功能**：正常工作
- ✅ **统一检索接口**：已实现
- ✅ **向量数据库**：已构建
- ⚠️ **图像检索**：需要完善图像嵌入模型

### 测试命令
```bash
# 检查数据文件
python run_vectorization.py --mode check

# 测试检索功能
python run_vectorization.py --mode test

# 完整测试
python test_unified_retrieval.py
```

## 🚀 部署准备

### 1. 环境要求

**Python环境：**
- Python 3.8+
- 推荐使用conda环境

**系统要求：**
- 内存：至少8GB RAM
- 存储：至少10GB可用空间
- CPU：多核处理器推荐

### 2. 依赖安装

```bash
# 安装核心依赖
pip install -r requirements.txt

# 或者使用conda
conda install numpy pandas pillow scikit-learn
pip install torch transformers sentence-transformers
pip install chromadb faiss-cpu
pip install jieba pypinyin
```

### 3. 数据准备

**数据目录结构：**
```
datas/medical_knowledge/
├── text_data/raw/          # 文本数据文件
├── image_text_data/raw/    # 图像数据文件
├── image_text_data/processed/  # 预处理后的数据
└── vector_databases/       # 向量数据库
    ├── text/              # 文本向量数据库
    ├── image/             # 图像向量数据库
    └── multimodal/        # 多模态向量数据库
```

## 🔧 部署步骤

### 步骤1：环境配置

```bash
# 1. 克隆或复制项目
cd /path/to/zhi_zhen_tong_system

# 2. 进入向量化模块目录
cd codes/ai_models/embedding_models

# 3. 安装依赖
pip install -r requirements.txt
```

### 步骤2：数据检查

```bash
# 检查数据文件是否完整
python run_vectorization.py --mode check
```

### 步骤3：构建向量数据库

```bash
# 完整构建（推荐）
python run_vectorization.py --mode all

# 或者分步构建
python run_vectorization.py --mode preprocess  # 数据预处理
python run_vectorization.py --mode multimodal  # 多模态向量化
```

### 步骤4：测试系统

```bash
# 测试检索功能
python run_vectorization.py --mode test

# 详细测试
python test_unified_retrieval.py
```

## 📋 部署检查清单

### 基础检查
- [ ] Python环境正确安装
- [ ] 所有依赖包已安装
- [ ] 数据文件完整
- [ ] 配置文件正确

### 功能检查
- [ ] 文本检索正常工作
- [ ] 向量数据库构建成功
- [ ] 统一检索接口可用
- [ ] 错误处理机制正常

### 性能检查
- [ ] 检索响应时间合理（<2秒）
- [ ] 内存使用正常
- [ ] 并发处理能力

## 🎯 生产环境配置

### 1. 配置文件调整

**config.json 关键配置：**
```json
{
    "BASE_DATA_DIR": "/production/path/datas/medical_knowledge",
    "TEXT_EMBEDDING_MODEL": "shibing624/text2vec-base-chinese",
    "IMAGE_EMBEDDING_MODEL": "resnet50",
    "BATCH_SIZE": 100,
    "IMAGE_BATCH_SIZE": 32
}
```

### 2. 性能优化

**内存优化：**
- 调整 `BATCH_SIZE` 和 `IMAGE_BATCH_SIZE`
- 使用GPU加速（如果可用）

**存储优化：**
- 定期清理临时文件
- 压缩向量数据库

### 3. 监控和日志

**日志配置：**
- 启用详细日志记录
- 设置日志轮转
- 监控系统性能

## 🔍 故障排除

### 常见问题

**1. 模型下载失败**
```bash
# 解决方案：使用代理或本地模型
export HF_ENDPOINT=https://hf-mirror.com
```

**2. 内存不足**
```bash
# 解决方案：减少批处理大小
# 修改config.json中的BATCH_SIZE
```

**3. 图像处理失败**
```bash
# 解决方案：检查图像文件格式
# 确保支持PNG、JPG、JPEG格式
```

### 错误代码

| 错误代码 | 描述 | 解决方案 |
|---------|------|----------|
| E001 | 数据文件不存在 | 检查数据目录结构 |
| E002 | 模型加载失败 | 检查网络连接和模型路径 |
| E003 | 内存不足 | 减少批处理大小 |
| E004 | 向量数据库错误 | 重新构建向量数据库 |

## 📞 技术支持

### 日志收集
```bash
# 收集系统日志
python run_vectorization.py --mode test > test.log 2>&1
```

### 性能监控
```bash
# 监控系统资源
top -p $(pgrep -f "python.*run_vectorization")
```

## 🎉 部署完成

部署成功后，您将拥有：

1. **统一的多模态检索系统**
2. **高效的向量数据库**
3. **完整的医疗知识库**
4. **可扩展的架构设计**

### 下一步
- 集成到前端系统
- 配置API接口
- 设置监控和告警
- 进行性能调优

---

**部署状态：** ✅ 测试通过，可以部署
**最后更新：** 2025-09-08
**版本：** v1.0.0
