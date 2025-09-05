# 多模态智能医生问诊系统 - 文件夹说明

## Medical-Dialogue-Dataset-Chinese

### 作用
存储中文医疗对话文本数据集，用于训练和评估系统的文本理解能力。

### 内容
- 包含 2010 年至 2020 年的医疗对话记录，共 11 个文本文件（`2010.txt` 到 `2020.txt`）
- 每条记录以 "id=" 开头，包含丰富的医疗对话信息

### 数据格式
每条对话记录包含以下关键信息：
- 医生科室信息
- 患者描述（疾病、病情、希望获得的帮助）
- 过敏史、既往病史
- 部分记录包含完整对话内容和诊断建议

### 用途
- 用于训练系统理解患者症状描述
- 帮助系统学习医生的问诊思路和诊断逻辑
- 提升系统生成专业医疗建议的能力

## VQA_data

### 作用
存储医学图像问答（VQA）数据集，用于训练系统的图像理解和图文关联能力。

### 内容
包含多个医学图像问答数据集：
- `COV-CTR with English reports`：包含英文报告的 COVID-CT 相关数据
- `ChestX-rays`：胸部 X 光片数据集
  - `images`：胸部 X 光片图像文件
  - `indiana_projections.csv`：投影数据 CSV 文件
  - `indiana_reports.csv`：放射报告 CSV 文件，包含 uid、MeSH、Problems 等字段
- `LAVIS-main`：视觉语言模型相关库
- `VQA-Med-2019-master`：2019 年医学 VQA 数据集
- `VQA-RAD`：放射学 VQA 数据集
- `archive`：归档的路径 VQA 数据
- `pvqa`：特定医学 VQA 数据集

### 数据格式
- 图像数据：主要为 DICOM 或 PNG/JPG 格式的医学影像
- 文本数据：CSV 格式的报告和问答对，包含患者症状、检查结果和诊断印象等

### 用途
- 训练系统理解医学图像内容
- 建立图像与文本报告之间的关联
- 提升系统基于图像和文本综合回答医疗问题的能力

## processed_vqa_data

### 作用
存储预处理后的视觉问答数据，为模型训练提供直接可用的标准化数据。

### 内容
- 预处理脚本：
  - `image_text_preprocessing.py`：图像文本预处理模块
  - `text_preprocessing.py`：文本数据预处理模块（包含中文分词功能）
  - `preprocess_all.py`：预处理总控脚本
  - `standalone_preprocessing.py`：独立的预处理脚本
- 预处理后的数据：
  - `processed_images.npy`：预处理后的图像数据（NumPy 数组）
  - `processed_reports.csv`：预处理后的报告文本
  - `train_images.npy`、`train_reports.csv`：训练集数据
  - `test_images.npy`、`test_reports.csv`：测试集数据
- 其他文件：
  - `requirements.txt`：项目依赖库列表
  - `preprocessing_plan.md`：预处理阶段的详细计划

### 分词处理说明
项目包含完整的中文分词步骤，主要通过以下两个模块实现：

1. **文本数据分词**（在`text_preprocessing.py`中）：
   - 使用`jieba`库对医疗对话文本进行分词处理
   - 主要对`description`（病情描述）、`diagnosis`（诊断结果）、`suggestions`（医生建议）字段进行分词
   - 分词结果存储在`{字段名}_tokens`列中，以空格分隔的形式保存
   - 通过`text_enhancement()`方法实现并在预处理流程中自动执行

2. **图文数据分词**（在`image_text_preprocessing.py`中）：
   - 同样使用`jieba`库对医学影像报告文本进行分词处理
   - 主要对`findings`（检查所见）、`impression`（诊断印象）字段进行分词
   - 分词结果存储在`{字段名}_tokens`列中
   - 通过`clean_reports()`方法实现并在图像文本预处理流程中自动执行

分词处理为后续的文本向量化和模型训练提供了必要的基础，使系统能够更好地理解中文医疗文本的语义结构。

### 数据格式
- 图像数据：标准化为 NumPy 数组，统一尺寸和格式
- 文本数据：清洗和结构化后的 CSV 格式
- 训练集和测试集：按照一定比例划分，便于模型训练和评估

### 用途
- 直接用于多模态模型的训练
- 支持系统快速加载和处理数据
- 确保输入模型的数据质量和一致性

## vector_database

### 作用
存储用于构建和管理向量数据库的相关文件，支持系统的检索增强生成（RAG）功能。

### 内容
- 向量数据库脚本：
  - `build_vector_database.py`：构建向量数据库的主脚本
  - `run_vector_db.py`：运行向量数据库服务的脚本
  - `download_model.py`：下载所需模型的脚本
  - `config.json`：配置文件
- 启动脚本：
  - `run_build_vector_db.bat` 和 `run_build_vector_db.ps1`：构建向量数据库的启动脚本
  - `run_simple.bat`：简单运行向量数据库的批处理脚本
- 文档：
  - `README.md`：向量数据库相关说明文档
  - `chroma_db_explanation.md`：Chroma向量数据库详细解释文档
- `requirements.txt`：向量数据库相关依赖库
- 子目录：
  - `models`：存储嵌入模型
  - `chroma_db`：存储向量数据库文件

### 用途
- 支持文本和图像的向量化存储
- 提供高效的相似度检索功能
- 为多模态智能问诊系统提供检索增强生成能力

## vector_database\models

### 作用
存储用于文本向量化的预训练模型。

### 内容
- `text2vec-base-chinese`：中文文本向量化模型
  - 包含模型配置文件、权重文件、词汇表等
  - 支持将中文文本转换为高质量的向量表示

### 数据格式
- 标准Hugging Face模型格式
- 包含model.safetensors、config.json、tokenizer_config.json、vocab.txt等文件

### 用途
- 为医疗文本生成语义向量表示
- 支持基于语义的文本检索
- 为RAG系统提供文本嵌入能力

## vector_database\chroma_db

### 作用
存储向量数据库的实际数据文件，用于持久化存储向量化的医疗数据。

### 内容
- `chroma.sqlite3`：Chroma向量数据库的主数据库文件
- UUID命名的文件夹（如`3e8fbce4-330e-4de8-b0ef-ce7e99a31c95`）：
  - `data_level0.bin`：向量数据文件
  - `header.bin`：数据头文件
  - `index_metadata.pickle`：索引元数据
  - `length.bin`：长度信息文件
  - `link_lists.bin`：链表数据文件

### 数据格式
- 混合存储格式：SQLite数据库存储元数据，二进制文件存储向量数据
- 支持高效的向量相似度计算和检索

### 用途
- 持久化存储向量化的医疗对话和图像报告数据
- 支持快速的语义相似度查询
- 为多模态智能问诊系统提供检索支持

## 总结
这五个文件夹共同构成了系统的核心数据层：`Medical-Dialogue-Dataset-Chinese` 提供文本语料，`VQA_data` 提供原始图文数据，`processed_vqa_data` 提供预处理后的标准化数据，`vector_database\models` 提供文本向量化模型，`vector_database\chroma_db` 提供向量存储能力，为构建多模态智能医生问诊系统奠定了完整的数据基础。