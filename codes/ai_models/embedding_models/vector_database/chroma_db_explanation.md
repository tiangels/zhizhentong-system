# 向量数据库文件说明

## 简介
本文档详细解释了Chroma向量数据库生成的文件及其作用，帮助您更好地理解和使用向量数据库。

## 文件结构
Chroma向量数据库的核心文件位于`chroma_db`目录下，结构如下：
```
chroma_db/
├── 3e8fbce4-330e-4de8-b0ef-ce7e99a31c95/
│   ├── data_level0.bin
│   ├── header.bin
│   ├── index_metadata.pickle
│   ├── length.bin
│   └── link_lists.bin
└── chroma.sqlite3
```

## 文件作用详解

### 1. chroma.sqlite3
- **作用**：存储向量数据库的元数据
- **详细说明**：
  - 包含数据库的集合(collection)信息
  - 存储文档的元数据（如ID、标签等）
  - 保存索引配置参数
  - 使用SQLite数据库格式，支持高效的结构化查询

### 2. UUID命名目录
例如：`3e8fbce4-330e-4de8-b0ef-ce7e99a31c95`
- **作用**：存储具体的向量索引数据
- **详细说明**：
  - 每个集合(collection)通常对应一个唯一的UUID目录
  - 目录名称由Chroma自动生成，用于唯一标识一个索引

### 3. data_level0.bin
- **作用**：存储实际的向量数据
- **详细说明**：
  - 采用二进制格式存储高维向量数据
  - 优化存储效率和检索性能
  - 包含所有嵌入向量的原始数值

### 4. header.bin
- **作用**：存储索引的头部信息
- **详细说明**：
  - 包含索引类型（如HNSW）
  - 向量维度信息
  - 其他索引元数据

### 5. index_metadata.pickle
- **作用**：存储索引的配置参数
- **详细说明**：
  - 使用Python的pickle格式序列化
  - 包含HNSW索引的构建参数（如M值、ef值等）
  - 存储索引版本信息

### 6. length.bin
- **作用**：存储向量的长度信息
- **详细说明**：
  - 记录每个向量的长度（模长）
  - 用于向量相似度计算的优化

### 7. link_lists.bin
- **作用**：存储HNSW索引的链接列表结构
- **详细说明**：
  - 包含分层navigable small world图的节点连接信息
  - 用于高效的近似最近邻搜索
  - 是Chroma实现快速向量检索的核心数据结构

## 工作原理
Chroma向量数据库采用混合存储架构：
1. **元数据存储**：文档内容和元数据存储在SQLite数据库中，便于结构化查询
2. **向量存储**：高维向量数据存储在专门优化的二进制文件中，提高存储效率
3. **索引结构**：使用HNSW（分层Navigable Small World）索引加速向量相似性搜索
4. **检索流程**：查询时先通过SQLite过滤元数据，再通过HNSW索引快速找到相似向量

## 图像向量化原理

### 当前实现机制
在当前的系统实现中，图像采用了以下处理方式：

1. **图像预处理**：
   - 图像首先在`image_text_preprocessing.py`中进行标准化处理
   - 处理步骤包括：统一尺寸（224×224像素）、数据增强（随机水平翻转）、归一化等
   - 处理后的图像保存为NumPy数组格式（`.npy`文件）

2. **元数据关联存储**：
   - 在向量数据库构建过程中（`build_vector_database.py`），图像并未被直接转换为向量
   - 图像信息以**元数据形式**与文本向量关联存储
   - 存储的图像元数据包括：
     - `has_image`：标记该记录是否包含图像
     - `image_shape`：记录图像的形状信息

3. **文本主导的检索机制**：
   - 系统主要依赖医学报告文本（findings、impression等字段）生成向量
   - 向量数据库中存储的是这些文本内容的嵌入向量
   - 检索时，通过文本向量相似度找到相关记录，再通过元数据关联获取对应的图像

### 潜在的图像直接向量化方案
如需实现真正的图像向量化（例如用于跨模态检索），可考虑以下方案：

1. **使用多模态模型**：
   ```python
   from transformers import CLIPProcessor, CLIPModel
   
   # 加载CLIP模型（支持图文跨模态理解）
   model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
   processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
   
   # 图像向量化
   def vectorize_image(image):
       inputs = processor(images=image, return_tensors="pt")
       image_embeddings = model.get_image_features(**inputs)
       # 归一化向量以提高检索性能
       image_embeddings = image_embeddings / image_embeddings.norm(dim=-1, keepdim=True)
       return image_embeddings.detach().numpy()[0]
   ```

2. **使用CNN特征提取器**：
   ```python
   from torchvision import models, transforms
   import torch
   
   # 加载预训练的ResNet模型作为特征提取器
   model = models.resnet50(pretrained=True)
   model.eval()  # 设置为评估模式
   
   # 移除最后的分类层，只保留特征提取部分
   feature_extractor = torch.nn.Sequential(*list(model.children())[:-1])
   
   # 图像向量化函数
   def vectorize_image(image):
       # 图像预处理
       preprocess = transforms.Compose([
           transforms.Resize(256),
           transforms.CenterCrop(224),
           transforms.ToTensor(),
           transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
       ])
       input_tensor = preprocess(image).unsqueeze(0)  # 添加批次维度
       
       # 提取特征
       with torch.no_grad():
           features = feature_extractor(input_tensor)
       
       # 展平特征并归一化
       features = features.squeeze().numpy()
       return features / np.linalg.norm(features)
   ```

3. **实现跨模态检索**：
   - 使用CLIP等模型将图像和文本映射到同一嵌入空间
   - 支持"以文搜图"和"以图搜文"的跨模态检索功能
   - 可通过融合图像向量和文本向量提升检索准确性

## 使用指南
1. **无需手动修改**：这些文件由`build_vector_database.py`脚本自动生成和管理，无需手动编辑
2. **备份方法**：如需备份向量数据库，只需复制整个`chroma_db`目录
3. **使用方式**：后续RAG应用可以通过Chroma的Python客户端直接连接到这个目录进行查询
4. **注意事项**：删除或修改这些文件可能导致向量数据库损坏，请谨慎操作

## 示例代码
以下是连接到现有向量数据库的示例代码：
```python
import chromadb

# 连接到本地向量数据库
client = chromadb.PersistentClient(path="d:\Consultation system\processed_vqa_data\vector_database\chroma_db")

# 获取已存在的集合
collection = client.get_collection(name="medical_data")

# 进行向量查询
h_results = collection.query(
    query_texts=["患者有咳嗽症状，可能是什么疾病？"],
    n_results=5
)
print(h_results)
```