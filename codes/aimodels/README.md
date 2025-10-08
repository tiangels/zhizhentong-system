# 智诊通系统 - 本地模型管理

## 📋 概述

本目录包含智诊通系统使用的所有本地 AI 模型，包括大语言模型和向量化模型。系统已完全配置为优先使用本地模型，确保离线运行和快速启动。

## 🗂️ 目录结构

```
codes/aimodels/
├── BiomedCLIP-PubMedBERT_256-vit_base_patch16_224/    # 多模态向量化模型 (753MB)
├── Falconsai_text_summarization/     # 文本摘要模型
├── Qwen2-0.5B-Medical-MLX/          # 医疗文本生成模型
├── model_config_reader.py          # 统一模型管理器 ⭐
├── model_config_reader.py            # 模型配置读取器 ⭐
├── check_project_models.py           # 项目模型使用检查器 ⭐
├── model_config.json                 # 统一模型配置文件 ⭐
├── README.md                         # 本说明文档
└── __pycache__/                      # Python缓存目录
```

## 🤖 模型信息

### Medical_Qwen3_17B - 医疗大语言模型

- **模型类型**: 医疗领域大语言模型
- **参数量**: 17B
- **模型大小**: 34GB
- **用途**: 医疗文本生成、问答、诊断建议
- **本地路径**: `Medical_Qwen3_17B/`

#### 模型文件结构

```
Medical_Qwen3_17B/
├── config.json                    # 模型配置文件
├── generation_config.json         # 生成配置
├── tokenizer_config.json          # 分词器配置
├── tokenizer.json                 # 分词器文件
├── vocab.json                     # 词汇表
├── merges.txt                     # BPE合并规则
├── added_tokens.json              # 额外token
├── special_tokens_map.json        # 特殊token映射
├── model.safetensors.index.json   # 模型索引文件
├── model-00001-of-00002.safetensors  # 模型权重文件1 (1.98GB)
├── model-00002-of-00002.safetensors  # 模型权重文件2 (1.46GB)
├── README.md                      # 模型说明文档
└── Modelfile                      # 模型文件描述
```

### text2vec-base-chinese - 中文文本向量化模型

- **模型类型**: 中文文本向量化模型
- **向量维度**: 768
- **模型大小**: 400MB
- **用途**: 文本向量化、语义搜索、相似度计算
- **本地路径**: `text2vec-base-chinese/`

## 🛠️ 管理工具

### 1. 统一模型管理器 (model_config_reader.py)

统一管理所有 AI 模型的配置和使用：

**功能**:

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

**主要功能**:

```python
from model_config_reader import UnifiedModelManager

manager = UnifiedModelManager()

# 检查模型状态
models = manager.list_models()
print(models)

# 确保所有模型都可用
manager.ensure_models_available()

# 更新所有配置文件
manager.update_all_configs()
```

### 2. 项目模型使用检查器 (check_project_models.py)

检查项目中所有模型使用的地方：

**功能**:

- 扫描项目文件，检查模型使用情况
- 排除第三方库，只检查项目文件
- 生成详细的检查报告
- 识别需要更新的文件

**使用方法**:

```bash
python check_project_models.py
```

**检查报告**:

- `项目模型使用检查报告.md` - 详细的项目模型使用情况

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

- **Medical_Qwen3_17B**: ✅ 已安装并可用
- **text2vec-base-chinese**: ✅ 已安装并可用
- **RAG 服务**: ✅ 正常使用本地模型
- **向量化服务**: ✅ 正常使用本地模型
- **LLM 服务**: ✅ 正常使用本地模型

### ✅ 配置状态

- **所有配置文件**: ✅ 已更新为本地路径
- **模型路径**: ✅ 统一管理
- **自动检查**: ✅ 优先使用本地模型
- **本地化率**: ✅ 100%

## 🔧 配置管理

### 自动配置更新

系统会自动更新以下配置文件为本地模型路径：

1. **RAG 服务配置**: `codes/services/knowledge_retrieval_service/api/config/rag_config.json`
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

model_path = "codes/aimodels/Medical_Qwen3_17B"

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

### 2. 使用 vLLM 进行推理（推荐用于生产环境）

```python
from vllm import LLM, SamplingParams

model_path = "codes/aimodels/Medical_Qwen3_17B"

# 初始化模型
llm = LLM(
    model=model_path,
    tensor_parallel_size=1,  # 根据GPU数量调整
    dtype="half"             # 使用半精度
)

# 设置采样参数
sampling_params = SamplingParams(
    temperature=0.7,
    top_p=0.9,
    max_tokens=512
)

# 生成响应
def generate_medical_response(prompt):
    outputs = llm.generate([prompt], sampling_params)
    return outputs[0].outputs[0].text
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

### Medical_Qwen3_17B

- **最低要求**: 16GB RAM, 8GB VRAM
- **推荐配置**: 32GB RAM, 16GB+ VRAM
- **GPU**: 支持 CUDA 的 NVIDIA GPU（推荐 RTX 3080 或更高）

### text2vec-base-chinese

- **最低要求**: 4GB RAM
- **推荐配置**: 8GB RAM
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

**更新时间**: 2024 年 9 月 11 日  
**版本**: 2.0.0  
**状态**: ✅ 就绪  
**维护者**: 智诊通系统开发团队
