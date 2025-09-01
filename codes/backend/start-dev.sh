#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 启动智诊通系统开发环境...${NC}"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3未安装，请先安装Python3${NC}"
    exit 1
fi

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}⚠️  建议使用虚拟环境${NC}"
    echo -e "${YELLOW}💡 创建虚拟环境: python3 -m venv venv${NC}"
    echo -e "${YELLOW}💡 激活虚拟环境: source venv/bin/activate${NC}"
    echo ""
fi

# 安装依赖
echo -e "${YELLOW}📦 安装Python依赖...${NC}"
pip install -r requirements.txt

# 创建必要的目录
echo -e "${YELLOW}📁 创建必要目录...${NC}"
mkdir -p logs uploads

# 检查数据库文件
if [ ! -f "zhizhentong.db" ]; then
    echo -e "${YELLOW}🔄 初始化数据库...${NC}"
    python3 create_tables.py
fi

# 启动后端服务
echo -e "${YELLOW}🚀 启动后端API服务...${NC}"
echo -e "${GREEN}✅ 服务将在 http://localhost:8000 启动${NC}"
echo -e "${GREEN}✅ API文档: http://localhost:8000/docs${NC}"
echo ""

# 启动服务
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
