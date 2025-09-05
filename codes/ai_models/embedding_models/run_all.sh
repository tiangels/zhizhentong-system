#!/bin/bash

echo "智诊通词向量模型处理脚本"
echo "检测到操作系统: $(uname -s)"
echo "开始时间: $(date)"

# 检查Python环境
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "错误: 未找到Python环境"
    exit 1
fi

echo "使用Python命令: $PYTHON_CMD"

# 检查数据目录
echo "检查数据目录..."
if [ ! -d "Medical-Dialogue-Dataset-Chinese" ]; then
    echo "警告: Medical-Dialogue-Dataset-Chinese 目录不存在"
fi

if [ ! -d "VQA_data" ]; then
    echo "警告: VQA_data 目录不存在"
fi

# 安装依赖
echo "安装依赖..."
if [ -f "processed_vqa_data/requirements.txt" ]; then
    $PYTHON_CMD -m pip install -r processed_vqa_data/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if [ $? -ne 0 ]; then
        echo "依赖安装失败，尝试使用默认源..."
        $PYTHON_CMD -m pip install -r processed_vqa_data/requirements.txt
    fi
else
    echo "警告: requirements.txt 文件不存在"
fi

# 运行文本预处理
echo "运行文本预处理..."
if [ -f "processed_vqa_data/text_preprocessing.py" ]; then
    $PYTHON_CMD processed_vqa_data/text_preprocessing.py
    if [ $? -eq 0 ]; then
        echo "文本预处理完成"
    else
        echo "文本预处理失败"
        exit 1
    fi
else
    echo "警告: text_preprocessing.py 文件不存在"
fi

# 运行图像预处理
echo "运行图像预处理..."
if [ -f "processed_vqa_data/image_text_preprocessing.py" ]; then
    $PYTHON_CMD processed_vqa_data/image_text_preprocessing.py
    if [ $? -eq 0 ]; then
        echo "图像预处理完成"
    else
        echo "图像预处理失败"
        exit 1
    fi
else
    echo "警告: image_text_preprocessing.py 文件不存在"
fi

# 构建向量数据库
echo "构建向量数据库..."
if [ -f "vector_database/requirements.txt" ]; then
    $PYTHON_CMD -m pip install -r vector_database/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if [ $? -ne 0 ]; then
        echo "向量数据库依赖安装失败，尝试使用默认源..."
        $PYTHON_CMD -m pip install -r vector_database/requirements.txt
    fi
fi

if [ -f "vector_database/build_vector_database.py" ]; then
    $PYTHON_CMD vector_database/build_vector_database.py
    if [ $? -eq 0 ]; then
        echo "向量数据库构建完成"
    else
        echo "向量数据库构建失败"
        exit 1
    fi
else
    echo "警告: build_vector_database.py 文件不存在"
fi

echo "处理完成!"
echo "结束时间: $(date)"

# 运行测试
echo "运行检索测试..."
if [ -f "test_retrieval.py" ]; then
    $PYTHON_CMD test_retrieval.py
else
    echo "测试脚本不存在，跳过测试"
fi

echo "智诊通词向量模型处理脚本"
echo "检测到操作系统: $(uname -s)"
echo "开始时间: $(date)"

# 检查Python环境
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "错误: 未找到Python环境"
    exit 1
fi

echo "使用Python命令: $PYTHON_CMD"

# 检查数据目录
echo "检查数据目录..."
if [ ! -d "Medical-Dialogue-Dataset-Chinese" ]; then
    echo "警告: Medical-Dialogue-Dataset-Chinese 目录不存在"
fi

if [ ! -d "VQA_data" ]; then
    echo "警告: VQA_data 目录不存在"
fi

# 安装依赖
echo "安装依赖..."
if [ -f "processed_vqa_data/requirements.txt" ]; then
    $PYTHON_CMD -m pip install -r processed_vqa_data/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if [ $? -ne 0 ]; then
        echo "依赖安装失败，尝试使用默认源..."
        $PYTHON_CMD -m pip install -r processed_vqa_data/requirements.txt
    fi
else
    echo "警告: requirements.txt 文件不存在"
fi

# 运行文本预处理
echo "运行文本预处理..."
if [ -f "processed_vqa_data/text_preprocessing.py" ]; then
    $PYTHON_CMD processed_vqa_data/text_preprocessing.py
    if [ $? -eq 0 ]; then
        echo "文本预处理完成"
    else
        echo "文本预处理失败"
        exit 1
    fi
else
    echo "警告: text_preprocessing.py 文件不存在"
fi

# 运行图像预处理
echo "运行图像预处理..."
if [ -f "processed_vqa_data/image_text_preprocessing.py" ]; then
    $PYTHON_CMD processed_vqa_data/image_text_preprocessing.py
    if [ $? -eq 0 ]; then
        echo "图像预处理完成"
    else
        echo "图像预处理失败"
        exit 1
    fi
else
    echo "警告: image_text_preprocessing.py 文件不存在"
fi

# 构建向量数据库
echo "构建向量数据库..."
if [ -f "vector_database/requirements.txt" ]; then
    $PYTHON_CMD -m pip install -r vector_database/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if [ $? -ne 0 ]; then
        echo "向量数据库依赖安装失败，尝试使用默认源..."
        $PYTHON_CMD -m pip install -r vector_database/requirements.txt
    fi
fi

if [ -f "vector_database/build_vector_database.py" ]; then
    $PYTHON_CMD vector_database/build_vector_database.py
    if [ $? -eq 0 ]; then
        echo "向量数据库构建完成"
    else
        echo "向量数据库构建失败"
        exit 1
    fi
else
    echo "警告: build_vector_database.py 文件不存在"
fi

echo "处理完成!"
echo "结束时间: $(date)"

# 运行测试
echo "运行检索测试..."
if [ -f "test_retrieval.py" ]; then
    $PYTHON_CMD test_retrieval.py
else
    echo "测试脚本不存在，跳过测试"
fi




