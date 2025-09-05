# 多模态智能医生问诊系统 - 向量数据库构建工具

此工具用于将处理后的医疗数据转换为本地向量数据库，以便在后续的RAG（检索增强生成）应用中使用。

## 功能特点
- 加载处理后的文本报告和图像数据
- 使用中文预训练嵌入模型将文本转换为向量
- 构建并持久化向量数据库
- 支持处理全部数据、训练集和测试集

## 文件结构
```
vector_database/
├── build_vector_database.py  # 主程序脚本
├── requirements.txt          # 依赖库列表
├── run_build_vector_db.ps1   # PowerShell运行脚本
├── run_build_vector_db.bat   # 批处理文件（可能存在编码问题）
├── run_simple.bat            # 简单批处理文件
├── run_vector_db.py          # Python运行脚本（推荐使用）
└── README.md                 # 使用说明
```

##### 使用步骤

### 推荐方法：使用Python脚本
1. 双击运行`run_vector_db.py`文件
2. 按照提示操作
3. 如果安装依赖失败，脚本会提供具体错误信息和解决方案

### 备选方法：使用简单批处理文件
1. 双击运行`run_simple.bat`文件
2. 按照提示操作

### 备选方法：使用PowerShell脚本
1. 打开PowerShell
2. 进入向量数据库目录：
   ```
   cd d:\Consultation system\processed_vqa_data\vector_database
   ```
3. 运行脚本：
   ```
   .\run_build_vector_db.ps1
   ```

### 备选方法：手动运行
1. 确保已安装所需依赖：
   ```
   cd d:\Consultation system\processed_vqa_data\vector_database
   pip install -r requirements.txt
   ```

2. 运行脚本构建向量数据库：
   ```
   python build_vector_database.py
   ```

### 注意：批处理文件使用
如果您想使用批处理文件(`run_build_vector_db.bat`)，可能会遇到编码问题。如果出现乱码，请按照以下步骤手动创建一个新的批处理文件：

1. 打开记事本
2. 复制`run_build_vector_db.bat`文件的内容
3. 点击"文件"->"另存为"
4. 在"保存类型"中选择"所有文件"
5. 文件名输入`run_build_vector_db.bat`
6. 编码选择"ANSI"（非常重要）
7. 点击"保存"
8. 双击新创建的批处理文件运行

3. 构建完成后，向量库将存储在 `./chroma_db` 目录中

## 代码说明

### 核心功能
- `load_data()`: 加载处理后的文本和图像数据
- `init_vector_db()`: 初始化向量数据库和嵌入模型
- `prepare_documents()`: 准备文档数据用于向量存储
- `add_documents_to_db()`: 批量添加文档到向量数据库
- `main()`: 主函数，按顺序执行上述功能

### 配置项
可在 `Config` 类中修改以下配置：
- 数据路径：指定处理后的数据文件位置
- 向量数据库配置：
  - `VECTOR_DB_PATH`：向量数据库存储路径
  - `EMBEDDING_MODEL`：使用的中文嵌入模型，默认为 `shibing624/text2vec-base-chinese`
  - `LOCAL_MODEL_PATH`：本地模型路径，设置后将使用离线模式
  - `PROXY`：代理服务器地址，用于解决网络连接问题
  - `BATCH_SIZE`：批量处理大小
  - `DOWNLOAD_TIMEOUT`：下载模型的超时时间
  - `MAX_RETRIES`：下载模型的最大重试次数

## 注意事项
1. 确保处理后的数据文件存在于指定路径
2. 首次运行会下载嵌入模型，可能需要一些时间
3. 向量数据库会存储在 `./chroma_db` 目录，下次运行会覆盖现有数据库
4. 对于大型数据集，可能需要调整 `BATCH_SIZE` 以避免内存问题
5. 代码假设处理后的数据中包含 'findings', 'impression', 'findings_tokens' 和 'impression_tokens' 字段

## 常见问题解决

### 1. 缺少Microsoft Visual C++ 14.0或更高版本
错误提示示例：`error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/`

解决方案：
1. 安装Microsoft C++ Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. 或尝试安装预编译的chroma-hnswlib轮文件
3. 或使用conda环境安装依赖: `conda install -c conda-forge chromadb`

### 2. 安装过程中用户中断
错误提示示例：`安装依赖失败: 用户中断了命令执行`

解决方案：
1. 重新运行脚本
2. 或手动安装依赖: 打开命令提示符，进入vector_database目录，执行以下命令:
   `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

### 3. 无法下载模型
如果安装依赖时出现类似以下错误：
```
error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/
```
这是因为安装chroma-hnswlib需要C++编译工具。解决方案：
1. 安装Microsoft C++ Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. 或尝试安装预编译的chroma-hnswlib轮文件
3. 或使用conda环境安装依赖: conda install -c conda-forge chromadb

### 2. 无法下载模型
```如果遇到无法连接到Hugging Face Hub下载模型的问题，可以尝试以下解决方法：

#### 方法1: 设置代理
在 `Config` 类中设置代理服务器：
```python
PROXY = "http://127.0.0.1:7890"  # 根据您的实际代理设置修改
```

#### 方法2: 使用本地模型
1. 提前下载模型到本地
2. 在 `Config` 类中设置本地模型路径：
```python
LOCAL_MODEL_PATH = "/path/to/local/model"  # 替换为您的本地模型路径
```

## 潜在改进点
1. 添加数据验证和清洗功能
2. 实现更复杂的文档分割策略
3. 增加增量更新向量数据库的功能
4. 添加更多的错误处理和日志记录

## 依赖库版本
- langchain==0.1.16
- chromadb==0.4.24
- pandas==2.2.1
- numpy==1.26.4
- tqdm==4.66.2
- transformers==4.38.2
- sentence-transformers==2.6.1