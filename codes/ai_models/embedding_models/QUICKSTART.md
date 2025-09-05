# 智诊通词向量模型 - 快速启动指南

## 🚀 快速开始

### 1. 环境检查
```bash
# 检查Python版本 (需要3.8+)
python3 --version

# 检查数据目录
ls -la Medical-Dialogue-Dataset-Chinese/
ls -la VQA_data/
```

### 2. 一键启动 (推荐)
```bash
# 使用跨平台Python脚本
python3 run_cross_platform.py --all

# 或者分步执行
python3 run_cross_platform.py --install-deps
python3 run_cross_platform.py --text-only
python3 run_cross_platform.py --image-only  
python3 run_cross_platform.py --build-vector-db
```

### 3. 手动执行 (如果一键启动失败)

#### 步骤1: 安装依赖
```bash
pip3 install -r processed_vqa_data/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 步骤2: 文本数据预处理
```bash
cd processed_vqa_data/
python3 text_preprocessing.py
cd ..
```

#### 步骤3: 图像数据预处理
```bash
cd processed_vqa_data/
python3 image_text_preprocessing.py
cd ..
```

#### 步骤4: 构建向量数据库
```bash
cd vector_database/
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
python3 build_vector_database.py
cd ..
```

## 📁 预期输出文件

处理完成后，你应该看到以下文件：

```
processed_vqa_data/
├── processed_medical_dialogues.csv    # 处理后的医疗对话
├── processed_reports.csv              # 处理后的医疗报告
├── processed_images.npy               # 处理后的图像数据
├── train_reports.csv                  # 训练集报告
├── test_reports.csv                   # 测试集报告
├── train_images.npy                   # 训练集图像
└── test_images.npy                    # 测试集图像

vector_database/
└── chroma_db/                         # 向量数据库文件
    ├── chroma.sqlite3
    └── [UUID文件夹]/
        ├── data_level0.bin
        ├── header.bin
        └── ...
```

## 🔧 测试向量检索

创建测试脚本 `test_retrieval.py`:

```python
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# 加载向量数据库
embeddings = HuggingFaceEmbeddings(
    model_name="shibing624/text2vec-base-chinese"
)
vector_db = Chroma(
    persist_directory="./vector_database/chroma_db",
    embedding_function=embeddings
)

# 测试检索
query = "胸痛患者的诊断建议"
results = vector_db.similarity_search(query, k=3)

print(f"查询: {query}")
print("检索结果:")
for i, result in enumerate(results, 1):
    print(f"{i}. {result.page_content[:200]}...")
    print(f"   元数据: {result.metadata}")
    print()
```

运行测试:
```bash
python3 test_retrieval.py
```

## ⚠️ 常见问题

### 1. Python命令不存在
```bash
# 尝试不同的Python命令
python --version
python3 --version
py --version  # Windows
```

### 2. 依赖安装失败
```bash
# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或者使用conda
conda install -c conda-forge chromadb langchain
```

### 3. 图像目录不存在
如果VQA_data目录为空，可以下载示例数据或跳过图像处理：
```bash
python3 run_cross_platform.py --text-only --build-vector-db
```

### 4. 内存不足
处理大量数据时可能出现内存不足，可以：
- 减少batch_size
- 分批处理数据
- 使用更小的图像尺寸

## 🔗 与智诊通系统集成

将生成的向量数据库集成到智诊通后端：

```python
# 在智诊通后端中添加RAG服务
# backend/app/services/rag_service.py

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

class MedicalRAGService:
    def __init__(self):
        # 向量数据库路径
        db_path = os.path.join(
            os.path.dirname(__file__), 
            "../../ai_models/embedding_models/vector_database/chroma_db"
        )
        
        # 初始化嵌入模型
        self.embeddings = HuggingFaceEmbeddings(
            model_name="shibing624/text2vec-base-chinese"
        )
        
        # 加载向量数据库
        self.vector_db = Chroma(
            persist_directory=db_path,
            embedding_function=self.embeddings
        )
    
    def search_medical_cases(self, symptoms: str, k: int = 5):
        """根据症状搜索相似病例"""
        results = self.vector_db.similarity_search(symptoms, k=k)
        return [
            {
                "content": result.page_content,
                "metadata": result.metadata,
                "relevance_score": result.metadata.get("score", 0)
            }
            for result in results
        ]
```

## 📊 性能监控

创建性能监控脚本：

```python
import time
import psutil
from langchain_community.vectorstores import Chroma

def benchmark_retrieval():
    # 加载向量数据库
    vector_db = Chroma(persist_directory="./vector_database/chroma_db")
    
    queries = [
        "头痛发热咳嗽",
        "胸痛呼吸困难", 
        "腹痛恶心呕吐",
        "关节疼痛肿胀"
    ]
    
    total_time = 0
    for query in queries:
        start_time = time.time()
        results = vector_db.similarity_search(query, k=5)
        end_time = time.time()
        
        query_time = end_time - start_time
        total_time += query_time
        
        print(f"查询: {query}")
        print(f"耗时: {query_time:.3f}秒")
        print(f"结果数: {len(results)}")
        print()
    
    print(f"平均查询时间: {total_time/len(queries):.3f}秒")
    print(f"内存使用: {psutil.virtual_memory().percent}%")

if __name__ == "__main__":
    benchmark_retrieval()
```

## 📚 更多资源

- [完整分析文档](./EMBEDDING_MODELS_ANALYSIS.md)
- [原始README](./README.md)
- [数据预处理计划](./processed_vqa_data/preprocessing_plan.md)
- [向量数据库说明](./vector_database/README.md)

## 💡 提示

1. **首次运行**: 下载模型需要时间，请耐心等待
2. **数据质量**: 确保原始数据完整性
3. **系统资源**: 处理大量数据需要足够的内存和存储空间
4. **网络环境**: 使用国内镜像源加速依赖安装

如果遇到问题，请查看详细的[分析文档](./EMBEDDING_MODELS_ANALYSIS.md)或提交Issue。

## 🚀 快速开始

### 1. 环境检查
```bash
# 检查Python版本 (需要3.8+)
python3 --version

# 检查数据目录
ls -la Medical-Dialogue-Dataset-Chinese/
ls -la VQA_data/
```

### 2. 一键启动 (推荐)
```bash
# 使用跨平台Python脚本
python3 run_cross_platform.py --all

# 或者分步执行
python3 run_cross_platform.py --install-deps
python3 run_cross_platform.py --text-only
python3 run_cross_platform.py --image-only  
python3 run_cross_platform.py --build-vector-db
```

### 3. 手动执行 (如果一键启动失败)

#### 步骤1: 安装依赖
```bash
pip3 install -r processed_vqa_data/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 步骤2: 文本数据预处理
```bash
cd processed_vqa_data/
python3 text_preprocessing.py
cd ..
```

#### 步骤3: 图像数据预处理
```bash
cd processed_vqa_data/
python3 image_text_preprocessing.py
cd ..
```

#### 步骤4: 构建向量数据库
```bash
cd vector_database/
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
python3 build_vector_database.py
cd ..
```

## 📁 预期输出文件

处理完成后，你应该看到以下文件：

```
processed_vqa_data/
├── processed_medical_dialogues.csv    # 处理后的医疗对话
├── processed_reports.csv              # 处理后的医疗报告
├── processed_images.npy               # 处理后的图像数据
├── train_reports.csv                  # 训练集报告
├── test_reports.csv                   # 测试集报告
├── train_images.npy                   # 训练集图像
└── test_images.npy                    # 测试集图像

vector_database/
└── chroma_db/                         # 向量数据库文件
    ├── chroma.sqlite3
    └── [UUID文件夹]/
        ├── data_level0.bin
        ├── header.bin
        └── ...
```

## 🔧 测试向量检索

创建测试脚本 `test_retrieval.py`:

```python
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# 加载向量数据库
embeddings = HuggingFaceEmbeddings(
    model_name="shibing624/text2vec-base-chinese"
)
vector_db = Chroma(
    persist_directory="./vector_database/chroma_db",
    embedding_function=embeddings
)

# 测试检索
query = "胸痛患者的诊断建议"
results = vector_db.similarity_search(query, k=3)

print(f"查询: {query}")
print("检索结果:")
for i, result in enumerate(results, 1):
    print(f"{i}. {result.page_content[:200]}...")
    print(f"   元数据: {result.metadata}")
    print()
```

运行测试:
```bash
python3 test_retrieval.py
```

## ⚠️ 常见问题

### 1. Python命令不存在
```bash
# 尝试不同的Python命令
python --version
python3 --version
py --version  # Windows
```

### 2. 依赖安装失败
```bash
# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或者使用conda
conda install -c conda-forge chromadb langchain
```

### 3. 图像目录不存在
如果VQA_data目录为空，可以下载示例数据或跳过图像处理：
```bash
python3 run_cross_platform.py --text-only --build-vector-db
```

### 4. 内存不足
处理大量数据时可能出现内存不足，可以：
- 减少batch_size
- 分批处理数据
- 使用更小的图像尺寸

## 🔗 与智诊通系统集成

将生成的向量数据库集成到智诊通后端：

```python
# 在智诊通后端中添加RAG服务
# backend/app/services/rag_service.py

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

class MedicalRAGService:
    def __init__(self):
        # 向量数据库路径
        db_path = os.path.join(
            os.path.dirname(__file__), 
            "../../ai_models/embedding_models/vector_database/chroma_db"
        )
        
        # 初始化嵌入模型
        self.embeddings = HuggingFaceEmbeddings(
            model_name="shibing624/text2vec-base-chinese"
        )
        
        # 加载向量数据库
        self.vector_db = Chroma(
            persist_directory=db_path,
            embedding_function=self.embeddings
        )
    
    def search_medical_cases(self, symptoms: str, k: int = 5):
        """根据症状搜索相似病例"""
        results = self.vector_db.similarity_search(symptoms, k=k)
        return [
            {
                "content": result.page_content,
                "metadata": result.metadata,
                "relevance_score": result.metadata.get("score", 0)
            }
            for result in results
        ]
```

## 📊 性能监控

创建性能监控脚本：

```python
import time
import psutil
from langchain_community.vectorstores import Chroma

def benchmark_retrieval():
    # 加载向量数据库
    vector_db = Chroma(persist_directory="./vector_database/chroma_db")
    
    queries = [
        "头痛发热咳嗽",
        "胸痛呼吸困难", 
        "腹痛恶心呕吐",
        "关节疼痛肿胀"
    ]
    
    total_time = 0
    for query in queries:
        start_time = time.time()
        results = vector_db.similarity_search(query, k=5)
        end_time = time.time()
        
        query_time = end_time - start_time
        total_time += query_time
        
        print(f"查询: {query}")
        print(f"耗时: {query_time:.3f}秒")
        print(f"结果数: {len(results)}")
        print()
    
    print(f"平均查询时间: {total_time/len(queries):.3f}秒")
    print(f"内存使用: {psutil.virtual_memory().percent}%")

if __name__ == "__main__":
    benchmark_retrieval()
```

## 📚 更多资源

- [完整分析文档](./EMBEDDING_MODELS_ANALYSIS.md)
- [原始README](./README.md)
- [数据预处理计划](./processed_vqa_data/preprocessing_plan.md)
- [向量数据库说明](./vector_database/README.md)

## 💡 提示

1. **首次运行**: 下载模型需要时间，请耐心等待
2. **数据质量**: 确保原始数据完整性
3. **系统资源**: 处理大量数据需要足够的内存和存储空间
4. **网络环境**: 使用国内镜像源加速依赖安装

如果遇到问题，请查看详细的[分析文档](./EMBEDDING_MODELS_ANALYSIS.md)或提交Issue。




