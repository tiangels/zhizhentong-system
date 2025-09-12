#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 启动智诊通系统开发环境...${NC}"
echo ""

# 初始化conda环境
echo -e "${YELLOW}🔄 初始化conda环境...${NC}"

# 尝试多种conda路径
CONDA_PATHS=(
    "$HOME/miniconda3/etc/profile.d/conda.sh"
    "$HOME/anaconda3/etc/profile.d/conda.sh"
    "/opt/miniconda3/etc/profile.d/conda.sh"
    "/opt/anaconda3/etc/profile.d/conda.sh"
    "/usr/local/miniconda3/etc/profile.d/conda.sh"
    "/usr/local/anaconda3/etc/profile.d/conda.sh"
)

CONDA_INIT_FOUND=false
for conda_path in "${CONDA_PATHS[@]}"; do
    if [ -f "$conda_path" ]; then
        source "$conda_path"
        CONDA_INIT_FOUND=true
        echo -e "${GREEN}✅ conda环境初始化成功${NC}"
        break
    fi
done

if [ "$CONDA_INIT_FOUND" = false ]; then
    echo -e "${YELLOW}⚠️  conda未找到，将使用系统Python环境${NC}"
fi

# 检查Python环境
if ! command -v /opt/anaconda3/bin/conda run -n nlp python &> /dev/null; then
    echo -e "${RED}❌ Python3未安装，请先安装Python3${NC}"
    exit 1
fi

# 尝试激活conda环境
if command -v /opt/anaconda3/bin/conda &> /dev/null; then
    if /opt/anaconda3/bin/conda info --envs | grep -q "nlp"; then
        echo -e "${GREEN}✅ 找到conda环境 'nlp'，正在激活...${NC}"
        /opt/anaconda3/bin/conda activate nlp
        echo -e "${GREEN}✅ conda环境已激活${NC}"
    else
        echo -e "${YELLOW}⚠️  conda环境 'nlp' 不存在${NC}"
        echo -e "${YELLOW}💡 创建conda环境: /opt/anaconda3/bin/conda create -n nlp python=3.9${NC}"
        echo -e "${YELLOW}💡 然后激活: /opt/anaconda3/bin/conda activate nlp${NC}"
        echo ""
    fi
else
    echo -e "${YELLOW}⚠️  conda未找到，使用系统Python环境${NC}"
fi

# 安装依赖
echo -e "${YELLOW}📦 安装Python依赖...${NC}"
/opt/anaconda3/bin/conda run -n nlp python -m pip install -r requirements.txt

# 创建必要的目录
echo -e "${YELLOW}📁 创建必要目录...${NC}"
mkdir -p logs uploads

# 检查数据库文件
if [ ! -f "zhizhentong.db" ]; then
    echo -e "${YELLOW}🔄 初始化数据库...${NC}"
    /opt/anaconda3/bin/conda run -n nlp python create_tables.py
fi

# 启动后端服务
echo -e "${YELLOW}🚀 启动后端API服务...${NC}"
echo -e "${GREEN}✅ 服务将在 http://localhost:8000 启动${NC}"
echo -e "${GREEN}✅ API文档: http://localhost:8000/docs${NC}"
echo ""

# 启动服务
/opt/anaconda3/bin/conda run -n nlp python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
