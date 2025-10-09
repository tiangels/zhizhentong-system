# 智诊通系统 AI 模型管理文档

## 📋 概述

本目录包含智诊通系统使用的所有 AI 模型，包括大语言模型、多模态向量化模型、语音识别模型、文本摘要模型等。系统已完全配置为优先使用本地模型，确保离线运行和快速启动。

## 🗂️ 目录结构

```
codes/aimodels/
├── Apollo-0.5B/                                    # 多语言医疗大语言模型 (0.5B参数)
├── BiomedCLIP-PubMedBERT_256-vit_base_patch16_224/ # 多模态向量化模型 (753MB)
├── distilbert-base-multilingual-cased/             # 多语言文本分类模型
├── ernie-3.0-base-zh/                              # 中文语义切分模型
├── Falconsai_text_summarization/                   # 文本摘要模型
├── paraphrase-multilingual-MiniLM-L12-v2/          # 多语言语义相似度模型
├── whisper-tiny/                                   # 语音转文本模型 (39M参数)
├── model_config_reader.py                          # 统一模型管理器 ⭐
├── check_project_models.py                         # 项目模型使用检查器 ⭐
├── model_config.json                               # 统一模型配置文件 ⭐
├── docs_backup/                                    # 文档备份目录
├── __pycache__/                                    # Python缓存目录
└── 智诊通系统AI模型管理文档.md                      # 本文档
```

## 🤖 模型详细信息

### 1. Apollo-0.5B - 多语言医疗大语言模型

**模型类型**: 多语言医疗领域大语言模型  
**参数量**: 0.5B  
**模型大小**: 约 1GB  
**支持语言**: 英语、中文、法语、印地语、西班牙语、阿拉伯语等  
**用途**: 医疗文本生成、问答、诊断建议、多语言医疗对话

**在系统中的应用**:

- 后端 RAG 服务中的文本生成
- 用户问题的智能回答
- 医疗诊断建议生成
- 多语言医疗文本处理

**模型文件结构**:

```
Apollo-0.5B/
├── config.json                    # 模型配置文件
├── generation_config.json         # 生成配置
├── tokenizer_config.json          # 分词器配置
├── tokenizer.json                 # 分词器文件
├── vocab.json                     # 词汇表
├── merges.txt                     # BPE合并规则
├── added_tokens.json              # 额外token
├── special_tokens_map.json        # 特殊token映射
├── model.safetensors              # 模型权重文件
├── README.md                      # 模型说明文档
└── assets/                        # 资源文件
    ├── apollo_medium_final.png
    ├── dataset.png
    ├── logo
    └── result.png
```

### 2. BiomedCLIP-PubMedBERT_256-vit_base_patch16_224 - 多模态向量化模型

**模型类型**: 生物医学多模态向量化模型  
**模型大小**: 753MB  
**向量维度**: 512  
**支持模态**: 文本、图像  
**用途**: 文本向量化、图像向量化、语义搜索、相似度计算

**在系统中的应用**:

- 知识库文档向量化
- 用户问题向量化
- 图像医疗数据向量化
- RAG 检索中的相似度计算

**模型文件结构**:

```
BiomedCLIP-PubMedBERT_256-vit_base_patch16_224/
├── config.json                    # 模型配置
├── open_clip_config.json          # OpenCLIP配置
├── open_clip_pytorch_model.bin    # PyTorch模型权重
├── tokenizer.json                 # 分词器
├── tokenizer_config.json          # 分词器配置
├── vocab.txt                      # 词汇表
├── special_tokens_map.json        # 特殊token映射
├── LICENSE.md                     # 许可证
├── README.md                      # 模型说明
├── biomed-vlp-eval.svg            # 评估结果图
├── biomed_clip_example.ipynb      # 使用示例
└── example_data/                  # 示例数据
    └── biomed_image_classification_example_data/
        ├── adenocarcinoma_histopathology.jpg
        ├── bone_X-ray.jpg
        ├── brain_MRI.jpg
        ├── chest_X-ray.jpg
        ├── covid_line_chart.png
        ├── H_and_E_histopathology.jpg
        ├── IHC_histopathology.jpg
        ├── pie_chart.png
        └── squamous_cell_carcinoma_histopathology.jpeg
```

### 3. whisper-tiny - 语音转文本模型

**模型类型**: 自动语音识别模型  
**参数量**: 39M  
**模型大小**: 约 150MB  
**支持语言**: 99 种语言（包括中文、英语等）  
**采样率**: 16kHz  
**用途**: 语音转文本、语音识别、多语言语音处理

**在系统中的应用**:

- 用户语音输入转文本
- 医疗语音记录转录
- 多语言语音识别
- 语音交互功能

**模型文件结构**:

```
whisper-tiny/
├── config.json                    # 模型配置
├── configuration.json             # 配置信息
├── generation_config.json         # 生成配置
├── preprocessor_config.json       # 预处理器配置
├── model.safetensors              # 模型权重
├── pytorch_model.bin              # PyTorch权重
├── tf_model.h5                    # TensorFlow权重
├── flax_model.msgpack             # Flax权重
├── tokenizer.json                 # 分词器
├── tokenizer_config.json          # 分词器配置
├── vocab.json                     # 词汇表
├── merges.txt                     # BPE合并规则
├── added_tokens.json              # 额外token
├── special_tokens_map.json        # 特殊token映射
├── normalizer.json                # 标准化器
└── README.md                      # 模型说明
```

### 4. Falconsai_text_summarization - 文本摘要模型

**模型类型**: 文本摘要模型  
**基础模型**: T5 Small  
**用途**: 文本摘要、内容压缩、关键信息提取

**在系统中的应用**:

- 长文档摘要生成
- 医疗报告摘要
- 知识库内容压缩
- 用户回答摘要

**模型文件结构**:

```
Falconsai_text_summarization/
├── config.json                    # 模型配置
├── generation_config.json         # 生成配置
├── model.safetensors              # 模型权重
├── pytorch_model.bin              # PyTorch权重
├── tokenizer.json                 # 分词器
├── tokenizer_config.json          # 分词器配置
├── added_tokens.json              # 额外token
├── special_tokens_map.json        # 特殊token映射
├── spiece.model                   # SentencePiece模型
├── model_info.json                # 模型信息
├── README.md                      # 模型说明
├── onnx/                          # ONNX格式模型
│   ├── config.json
│   ├── decoder_model_merged.onnx
│   ├── decoder_model.onnx
│   ├── decoder_with_past_model.onnx
│   ├── encoder_model.onnx
│   ├── generation_config.json
│   ├── added_tokens.json
│   ├── special_tokens_map.json
│   ├── spiece.model
│   ├── tokenizer_config.json
│   └── tokenizer.json
└── coreml/                        # CoreML格式模型
    └── text2text-generation/
        ├── decoder_float32_model.mlpackage/
        └── encoder_float32_model.mlpackage/
```

### 5. paraphrase-multilingual-MiniLM-L12-v2 - 多语言语义相似度模型

**模型类型**: 多语言语义相似度模型  
**向量维度**: 384  
**支持语言**: 50+种语言  
**用途**: 语义相似度计算、文本质量评估、多语言文本匹配

**在系统中的应用**:

- 文本质量评估
- 语义相似度计算
- 多语言文本匹配
- 内容去重

**模型文件结构**:

```
paraphrase-multilingual-MiniLM-L12-v2/
├── config.json                    # 模型配置
├── config_sentence_transformers.json  # SentenceTransformers配置
├── sentence_bert_config.json      # Sentence-BERT配置
├── model.safetensors              # 模型权重
├── pytorch_model.bin              # PyTorch权重
├── tf_model.h5                    # TensorFlow权重
├── tokenizer.json                 # 分词器
├── tokenizer_config.json          # 分词器配置
├── vocab.txt                      # 词汇表
├── special_tokens_map.json        # 特殊token映射
├── sentencepiece.bpe.model        # SentencePiece模型
├── unigram.json                   # 单字符映射
├── modules.json                   # 模块配置
├── README.md                      # 模型说明
├── 1_Pooling/                     # 池化层配置
│   └── config.json
├── onnx/                          # ONNX格式模型
│   ├── model.onnx
│   ├── model_O1.onnx
│   ├── model_O2.onnx
│   ├── model_O3.onnx
│   ├── model_O4.onnx
│   ├── model_qint8_arm64.onnx
│   ├── model_qint8_avx512_vnni.onnx
│   ├── model_qint8_avx512.onnx
│   └── model_quint8_avx2.onnx
└── openvino/                      # OpenVINO格式模型
    ├── openvino_model.bin
    ├── openvino_model.xml
    ├── openvino_model_qint8_quantized.bin
    └── openvino_model_qint8_quantized.xml
```

### 6. distilbert-base-multilingual-cased - 多语言文本分类模型

**模型类型**: 多语言文本分类模型  
**基础模型**: DistilBERT  
**支持语言**: 104 种语言  
**用途**: 文本分类、质量评估、多语言文本处理

**在系统中的应用**:

- 文本质量分类
- 内容类型识别
- 多语言文本处理
- 质量评估

**模型文件结构**:

```
distilbert-base-multilingual-cased/
├── config.json                    # 模型配置
├── model.safetensors              # 模型权重
├── tf_model.h5                    # TensorFlow权重
├── tokenizer.json                 # 分词器
├── tokenizer_config.json          # 分词器配置
├── vocab.txt                      # 词汇表
└── README.md                      # 模型说明
```

### 7. ernie-3.0-base-zh - 中文语义切分模型

**模型类型**: 中文语义切分模型  
**向量维度**: 768  
**支持语言**: 中文  
**用途**: 文档语义切分、相似度计算、中文文本处理

**在系统中的应用**:

- 中文文档语义切分
- 中文文本相似度计算
- 中文知识库处理
- 中文 RAG 检索

**模型文件结构**:

```
ernie-3.0-base-zh/
├── config.json                    # 模型配置
├── pytorch_model.bin              # PyTorch权重
├── tokenizer.json                 # 分词器
├── tokenizer_config.json          # 分词器配置
└── vocab.txt                      # 词汇表
```

## 🛠️ 管理工具

### 1. 统一模型管理器 (model_config_reader.py)

**功能**: 统一管理所有 AI 模型的配置和使用

**主要功能**:

- 检查模型状态和完整性
- 自动下载缺失的模型
- 自动更新配置文件中的模型路径
- 替换硬编码的模型引用
- 生成详细的模型使用指南

**使用方法**:

```bash
cd codes/aimodels
python model_config_reader.py
```

**API 接口**:

```python
from model_config_reader import get_model_config_reader

# 获取模型管理器
manager = get_model_config_reader()

# 检查模型状态
models = manager.list_models()
print(models)

# 确保所有模型都可用
manager.ensure_models_available()

# 更新所有配置文件
manager.update_all_configs()
```

### 2. 项目模型使用检查器 (check_project_models.py)

**功能**: 检查项目中所有模型使用的地方

**主要功能**:

- 扫描项目文件，检查模型使用情况
- 排除第三方库，只检查项目文件
- 生成详细的检查报告
- 识别需要更新的文件

**使用方法**:

```bash
python check_project_models.py
```

**检查报告**:

- 生成 `项目模型使用检查报告.md` - 详细的项目模型使用情况

### 3. 统一模型配置文件 (model_config.json)

**功能**: 统一配置所有模型的路径和参数

**配置内容**:

- 文本嵌入模型配置
- 图像嵌入模型配置
- 语音转文本模型配置
- 大语言模型配置
- 文本摘要模型配置
- 语义模型配置
- 分类模型配置
- 语义切分模型配置

**配置示例**:

```json
{
  "version": "2.0.0",
  "description": "统一模型配置文件",
  "models": {
    "text_embedding": {
      "model_name": "BiomedCLIP-PubMedBERT_256-vit_base_patch16_224",
      "local_model_path": "../../aimodels/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224",
      "vector_dim": 512,
      "use_local_only": true
    }
  }
}
```

## 📁 其他文件说明

### docs_backup/ - 文档备份目录

包含历史文档和备份文件：

- `文件合并完成报告.md` - 文件合并操作报告
- `本地模型使用指南.md` - 本地模型使用指南
- `模型统一管理完成报告.md` - 模型统一管理报告
- `项目模型使用检查报告.md` - 项目模型使用检查报告

### **pycache**/ - Python 缓存目录

包含 Python 字节码缓存文件，用于提高程序运行速度。

## 🚀 快速开始

### 1. 检查模型状态

```bash
cd codes/aimodels
python model_config_reader.py
```

### 2. 验证系统配置

```bash
python check_project_models.py
```

### 3. 测试模型功能

```python
from codes.backend.app.services.rag_service import get_rag_service

rag_service = get_rag_service()
print(f'RAG服务可用: {rag_service.is_available()}')

if rag_service.is_available():
    print('✅ 系统配置正确，使用本地模型')
else:
    print('❌ 系统配置有问题')
```

## 📊 系统状态

### ✅ 当前状态

- **Apollo-0.5B**: ✅ 已安装并可用
- **BiomedCLIP-PubMedBERT_256-vit_base_patch16_224**: ✅ 已安装并可用
- **whisper-tiny**: ✅ 已安装并可用
- **Falconsai_text_summarization**: ✅ 已安装并可用
- **paraphrase-multilingual-MiniLM-L12-v2**: ✅ 已安装并可用
- **distilbert-base-multilingual-cased**: ✅ 已安装并可用
- **ernie-3.0-base-zh**: ✅ 已安装并可用

### ✅ 配置状态

- **所有配置文件**: ✅ 已更新为本地路径
- **模型路径**: ✅ 统一管理
- **自动检查**: ✅ 优先使用本地模型
- **本地化率**: ✅ 100%

## 🔧 配置管理

### 自动配置更新

系统会自动更新以下配置文件为本地模型路径：

1. **RAG 服务配置**: `codes/services/knowledge_retrieval_service/config/rag_config.json`
2. **统一配置**: `codes/ai_models/embedding_models/config/unified_config.json`
3. **医疗配置**: `codes/ai_models/embedding_models/config/medical_knowledge_config.json`
4. **向量配置**: `codes/ai_models/embedding_models/config/vector_config.json`

### 手动配置

如果需要手动配置模型路径，请确保路径指向正确的模型目录。

## 💻 使用方法

### 1. 使用 Transformers 库加载

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_path = "codes/aimodels/Apollo-0.5B"

# 加载分词器
tokenizer = AutoTokenizer.from_pretrained(model_path)

# 加载模型
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.float16,  # 使用半精度以节省显存
    device_map="auto"           # 自动分配设备
)

# 生成文本
def generate_response(prompt, max_length=512):
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)
```

### 2. 使用多模态模型

```python
from transformers import CLIPProcessor, CLIPModel
import torch

model_path = "codes/aimodels/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"

# 加载模型和处理器
model = CLIPModel.from_pretrained(model_path)
processor = CLIPProcessor.from_pretrained(model_path)

# 处理文本和图像
def get_embeddings(text, image):
    inputs = processor(text=text, images=image, return_tensors="pt", padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.text_embeds, outputs.image_embeds
```

### 3. 使用语音识别模型

```python
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import torch

model_path = "codes/aimodels/whisper-tiny"

# 加载模型和处理器
processor = WhisperProcessor.from_pretrained(model_path)
model = WhisperForConditionalGeneration.from_pretrained(model_path)

# 语音转文本
def transcribe_audio(audio):
    inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
    with torch.no_grad():
        predicted_ids = model.generate(inputs["input_features"])
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
    return transcription[0]
```

## 🔍 故障排除

### 常见问题

1. **模型路径错误**

   ```bash
   # 运行统一模型管理器自动修复
   python model_config_reader.py
   ```

2. **配置文件不一致**

   ```bash
   # 检查项目模型使用情况
   python check_project_models.py
   ```

3. **模型文件缺失**
   - 检查模型目录是否存在
   - 验证模型文件完整性
   - 重新下载缺失的模型

### 检查清单

- [ ] 所有 Python 文件使用本地模型路径
- [ ] 配置文件中的模型路径正确
- [ ] 启动脚本检查本地模型存在性
- [ ] 文档中的模型路径信息准确

## 📋 硬件要求

### Apollo-0.5B

- **最低要求**: 4GB RAM, 2GB VRAM
- **推荐配置**: 8GB RAM, 4GB+ VRAM
- **GPU**: 支持 CUDA 的 NVIDIA GPU（可选）

### BiomedCLIP-PubMedBERT_256-vit_base_patch16_224

- **最低要求**: 4GB RAM
- **推荐配置**: 8GB RAM
- **GPU**: 可选，CPU 也可正常运行

### whisper-tiny

- **最低要求**: 2GB RAM
- **推荐配置**: 4GB RAM
- **GPU**: 可选，CPU 也可正常运行

### 其他模型

- **最低要求**: 2GB RAM
- **推荐配置**: 4GB RAM
- **GPU**: 可选，CPU 也可正常运行

## 📞 技术支持

如果遇到问题，请检查：

1. 模型文件完整性
2. 配置文件路径
3. 系统资源使用情况
4. 依赖包版本

### 定期维护

```bash
# 每月运行一次模型检查
python model_config_reader.py
python check_project_models.py
```

### 添加新模型

1. 将模型文件放入 `codes/aimodels/` 目录
2. 运行 `python model_config_reader.py` 更新配置
3. 运行 `python check_project_models.py` 验证

---

## 📋 技术实施历史记录

### 模型统一管理完成报告

#### 完成的任务

1. **全项目模型使用情况搜索** - 搜索了整个项目中所有使用模型的地方
2. **创建统一模型管理器** - 实现了模型的自动下载、检查和配置更新功能
3. **创建模型配置读取器** - 提供了统一的模型信息获取接口
4. **更新所有模型加载逻辑** - 更新了 5 个核心文件的模型加载逻辑
5. **替换硬编码模型引用** - 将所有硬编码的模型引用替换为配置文件读取
6. **模型下载和检查** - 检查了本地模型文件的存在性并自动下载缺失文件

#### 技术实现

- **统一模型配置文件**: 使用 JSON 格式统一管理所有模型配置
- **模型配置读取器接口**: 提供统一的模型信息获取方法
- **自动维护**: 自动检查模型文件完整性、自动下载缺失文件、自动更新配置文件
- **向后兼容**: 保持原有 API 接口不变，提供回退机制

#### 更新统计

- **核心代码文件**: 5 个
- **配置文件**: 4 个
- **新增管理文件**: 2 个
- **硬编码引用**: 全部替换为配置文件读取

### 文件合并完成报告

#### 合并操作

将`unified_model_manager.py`的所有功能合并到`model_config_reader.py`中：

**新增功能**:

- 模型下载管理: `download_model()`, `ensure_models_available()`
- 模型状态检查: `check_model_exists()`, `list_models()`
- 配置文件更新: `update_all_configs()`, `_update_rag_config()`, `_update_vector_config()`
- 代码替换: `replace_text2vec_references()`
- 命令行接口: `main()` 函数支持多种操作

**命令行接口**:

```bash
# 列出所有模型
python model_config_reader.py --action list

# 检查特定模型
python model_config_reader.py --action check --model "BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"

# 下载模型
python model_config_reader.py --action download --model "Qwen2-0.5B-Medical-MLX"

# 确保所有核心模型可用
python model_config_reader.py --action ensure

# 更新所有配置文件
python model_config_reader.py --action update
```

### 项目模型使用检查报告

#### 检查结果

- **总计检查文件数**: 36 个
- **使用本地模型**: 3 个文件
- **需要更新**: 33 个文件
- **本地化率**: 8.3%

#### 主要发现

1. **Python 文件**: 大部分仍使用硬编码的模型路径
2. **配置文件**: 部分已更新为本地路径，部分仍需更新
3. **脚本文件**: 启动脚本中的模型路径需要更新
4. **文档文件**: 大量文档中的模型引用需要更新

#### 修复建议

1. **使用模型管理器自动更新**:

   ```python
   from model_manager import ModelManager
   manager = ModelManager()
   manager.update_config_files(use_local_models=True)
   ```

2. **手动更新配置文件中的模型路径**

3. **确保本地模型文件完整且可访问**

### 系统演进历程

#### 第一阶段: 基础模型部署

- 部署了基础的医疗大语言模型和向量化模型
- 建立了基本的模型管理机制

#### 第二阶段: 统一管理

- 创建了统一的模型配置管理系统
- 实现了自动化的模型检查和下载功能
- 建立了完整的模型管理工具链

#### 第三阶段: 优化整合

- 合并了重复的管理工具
- 优化了配置文件结构
- 完善了文档体系

#### 当前状态

- **模型管理**: ✅ 完全统一化
- **配置管理**: ✅ 自动化更新
- **文档体系**: ✅ 完整规范
- **本地化率**: ✅ 100%本地模型优先

## 📈 性能优化

### 1. 模型加载优化

- 使用半精度浮点数 (float16) 减少内存使用
- 启用模型并行处理
- 使用模型缓存避免重复加载

### 2. 推理优化

- 使用批处理提高吞吐量
- 启用 GPU 加速
- 使用量化模型减少计算量

### 3. 存储优化

- 定期清理缓存文件
- 使用模型压缩技术
- 优化模型存储结构

## 🔒 安全考虑

### 1. 模型安全

- 定期更新模型版本
- 验证模型文件完整性
- 使用数字签名验证模型来源

### 2. 数据安全

- 加密存储敏感数据
- 限制模型访问权限
- 定期备份重要数据

### 3. 隐私保护

- 本地处理敏感数据
- 避免将数据发送到外部服务
- 遵守数据保护法规

---

**更新时间**: 2025 年 1 月 17 日  
**版本**: 3.0.0  
**状态**: ✅ 就绪  
**维护者**: 智诊通系统开发团队
