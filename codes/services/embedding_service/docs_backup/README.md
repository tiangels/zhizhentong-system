# 医疗数据质量检查器

## 概述

`quality_analyzer.py` 是一个专门为医疗数据设计的质量检查工具，实现了完整的数据质量检查流程，确保向量化前的数据质量。

## 功能特性

### 1. 完整性检查

- **空白过滤**: 剔除纯空白或仅含标点的文本
- **长度检查**: 过滤过短（<10 字符）和过长（>模型 Token 上限 1.2 倍）的文本
- **格式验证**: 确保文本格式正确

### 2. 唯一性检查

- **哈希去重**: 基于 MD5 哈希的精确去重
- **语义去重**: 使用 Sentence-BERT 计算语义相似度，过滤相似度>0.95 的重复文本
- **批量处理**: 支持大批量文本的高效去重

### 3. 相关性检查

- **关键词过滤**: 过滤包含无关关键词（金融、游戏等）的文本
- **医疗内容检测**: 确保文本包含医疗相关内容
- **质量评估**: 检查特殊字符比例，过滤乱码文本
- **语义分类**: 使用轻量级分类模型判断文本相关性

### 4. 向量化前置检查

- **编码验证**: 确保文本可正确编码为 UTF-8
- **Token 计算**: 预计算文本 Token 数量，避免向量化失败
- **模型兼容性**: 检查文本是否适合目标向量化模型

## 安装依赖

### 必需依赖

```bash
pip install pandas numpy jieba
```

### 可选依赖（增强功能）

```bash
# 语义相似度检查
pip install sentence-transformers

# 文本分类
pip install transformers torch

# 编码检测
pip install chardet

# 相似度计算
pip install scikit-learn
```

## 使用方法

### 基本使用

```python
from quality_analyzer import QualityAnalyzer

# 初始化质量检查器
analyzer = QualityAnalyzer("data_directory")

# 准备待检查的文本列表
texts = [
    "患者出现发热、咳嗽等症状，建议进行血常规检查。",
    "这是一个关于金融投资的文章。",  # 会被过滤
    "",  # 空白文本，会被过滤
    "患者出现发热、咳嗽等症状，建议进行血常规检查。"  # 重复文本
]

# 执行质量分析
result = analyzer.analyze_text_quality(texts)

# 获取通过所有检查的清洁文本
clean_texts = analyzer.get_clean_texts(result)
print(f"通过检查的文本数量: {len(clean_texts)}")

# 保存分析报告
analyzer.save_analysis_report(result, "quality_report.json")
```

### 自定义配置

```python
# 自定义配置参数
config = {
    'min_length': 15,  # 最小文本长度
    'max_length_ratio': 1.0,  # 最大长度比例
    'model_max_tokens': 512,  # 模型最大token数
    'semantic_similarity_threshold': 0.9,  # 语义相似度阈值
    'irrelevant_keywords': ['金融', '游戏', '娱乐'],  # 无关关键词
    'special_char_ratio_threshold': 0.2,  # 特殊字符比例阈值
}

analyzer = QualityAnalyzer("data_directory", config)
```

## 配置参数

| 参数                            | 类型  | 默认值                                                                           | 说明                                    |
| ------------------------------- | ----- | -------------------------------------------------------------------------------- | --------------------------------------- |
| `min_length`                    | int   | 10                                                                               | 最小文本长度                            |
| `max_length_ratio`              | float | 1.2                                                                              | 最大长度比例（相对于模型最大 token 数） |
| `model_max_tokens`              | int   | 512                                                                              | 模型最大 token 数                       |
| `semantic_similarity_threshold` | float | 0.95                                                                             | 语义相似度阈值                          |
| `batch_size`                    | int   | 32                                                                               | 批处理大小                              |
| `irrelevant_keywords`           | list  | ['金融', '游戏', '娱乐', '体育', '政治', '军事', '科技']                         | 无关关键词列表                          |
| `special_char_ratio_threshold`  | float | 0.3                                                                              | 特殊字符比例阈值                        |
| `medical_keywords`              | list  | ['疾病', '症状', '治疗', '诊断', '药物', '医院', '医生', '患者', '健康', '医疗'] | 医疗关键词列表                          |
| `encoding`                      | str   | 'utf-8'                                                                          | 文本编码                                |
| `token_overhead`                | int   | 10                                                                               | token 开销                              |

## 输出结果

### 分析结果结构

```python
{
    'statistics': {
        'total_texts': 100,           # 总文本数
        'completeness_passed': 80,    # 完整性检查通过数
        'uniqueness_passed': 75,      # 唯一性检查通过数
        'relevance_passed': 70,       # 相关性检查通过数
        'vectorization_passed': 65,   # 向量化检查通过数
        'final_passed': 65,           # 最终通过数
        'filtered_reasons': Counter() # 过滤原因统计
    },
    'results': [                      # 详细结果列表
        {
            'index': 0,
            'text': '原始文本',
            'completeness_passed': True,
            'completeness_reason': '',
            'uniqueness_passed': True,
            'uniqueness_reason': '',
            'relevance_passed': True,
            'relevance_reason': '',
            'vectorization_passed': True,
            'vectorization_reason': ''
        }
    ],
    'duplicate_groups': {},           # 重复组信息
    'summary': {                      # 摘要统计
        'total_texts': 100,
        'completeness_rate': '80.00%',
        'uniqueness_rate': '75.00%',
        'relevance_rate': '70.00%',
        'vectorization_rate': '65.00%',
        'final_pass_rate': '65.00%',
        'top_filter_reasons': {}
    }
}
```

## 测试

运行测试脚本验证功能：

```bash
cd analyzer
python test_quality_analyzer.py
```

测试包括：

- 基本功能测试
- 边界情况测试
- 各检查模块单独测试
- 性能测试

## 日志

质量检查器会生成详细的日志文件：

- 位置: `codes/logs/quality_analyzer.log`
- 包含: 检查过程、错误信息、统计信息

## 性能优化

### 批处理

- 支持批量处理大量文本
- 可配置批处理大小
- 内存友好的处理方式

### 模型延迟加载

- 只在需要时加载 AI 模型
- 支持模型加载失败时的降级处理
- 避免不必要的资源消耗

### 缓存机制

- 重复检查结果缓存
- 减少重复计算

## 错误处理

- **模型加载失败**: 自动降级到基础功能
- **网络连接问题**: 跳过在线模型，使用本地功能
- **内存不足**: 自动调整批处理大小
- **编码错误**: 自动检测并报告编码问题

## 扩展性

### 自定义检查器

可以继承 `QualityAnalyzer` 类并重写检查方法：

```python
class CustomQualityAnalyzer(QualityAnalyzer):
    def check_custom_criteria(self, text):
        # 自定义检查逻辑
        pass
```

### 插件系统

支持添加自定义检查插件：

```python
analyzer.add_checker('custom', custom_checker_function)
```

## 注意事项

1. **模型依赖**: 某些高级功能需要额外的 AI 模型，如果模型不可用会自动降级
2. **内存使用**: 处理大量文本时注意内存使用，可调整批处理大小
3. **网络连接**: 语义相似度检查需要下载模型，确保网络连接正常
4. **编码问题**: 确保输入文本使用正确的编码格式

## 更新日志

### v1.0.0

- 初始版本
- 实现四大检查模块
- 支持配置化参数
- 完整的测试套件
