# 医疗知识数据存储结构

## 目录结构说明

### 📁 text_data/ - 纯文本数据
- `raw/` - 原始文本数据（PDF、TXT、CSV等）
- `processed/` - 预处理后的文本数据
- `embeddings/` - 文本向量化数据

### 📁 image_text_data/ - 图文数据
- `raw/` - 原始图像和文本数据
- `processed/` - 预处理后的图像和文本数据
- `embeddings/` - 图像和文本向量化数据

### 📁 voice_data/ - 语音数据
- `raw/` - 原始语音文件（WAV、MP3等）
- `processed/` - 预处理后的语音数据
- `embeddings/` - 语音向量化数据

### 📁 vector_databases/ - 向量数据库
- `text/` - 纯文本向量数据库
- `image/` - 图像向量数据库
- `multimodal/` - 多模态向量数据库

### 📁 training_data/ - 训练数据
- 用于模型训练的数据集

### 📁 test_data/ - 测试数据
- 用于模型测试和评估的数据集

### 📁 logs/ - 日志文件
- 数据处理和模型训练的日志

## 数据格式规范

### 文本数据
- 原始数据：支持 PDF、TXT、CSV、JSON 格式
- 处理后：统一为 CSV 格式，包含 id、content、metadata 字段
- 向量化：NPY 格式的向量数组

### 图像数据
- 原始数据：支持 JPG、PNG、DICOM 格式
- 处理后：NPY 格式的预处理图像数组
- 向量化：NPY 格式的图像特征向量

### 语音数据
- 原始数据：支持 WAV、MP3、M4A 格式
- 处理后：NPY 格式的音频特征数组
- 向量化：NPY 格式的语音特征向量

## 使用说明

1. 将原始数据放入对应的 `raw/` 目录
2. 运行数据处理脚本，生成预处理数据到 `processed/` 目录
3. 运行向量化脚本，生成向量数据到 `embeddings/` 目录
4. 构建向量数据库到 `vector_databases/` 目录
