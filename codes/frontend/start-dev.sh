#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 启动智诊通前端系统...${NC}"
echo ""

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js未安装，请先安装Node.js${NC}"
    exit 1
fi

# 检查npm环境
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm未安装，请先安装npm${NC}"
    exit 1
fi

# 检查Node.js版本
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo -e "${RED}❌ Node.js版本过低，需要16.0.0或更高版本${NC}"
    echo -e "${YELLOW}当前版本: $(node -v)${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Node.js版本: $(node -v)${NC}"
echo -e "${GREEN}✅ npm版本: $(npm -v)${NC}"

# 检查依赖是否已安装
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 安装依赖包...${NC}"
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 依赖安装失败${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
else
    echo -e "${GREEN}✅ 依赖已安装${NC}"
fi

# 检查环境配置文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  未找到.env文件，将使用默认配置${NC}"
    echo -e "${YELLOW}💡 可以复制env.example为.env并修改配置${NC}"
    echo ""
fi

# 启动开发服务器
echo -e "${YELLOW}🚀 启动开发服务器...${NC}"
echo -e "${GREEN}✅ 前端将在 http://localhost:8080 启动${NC}"
echo -e "${GREEN}✅ 后端API: http://localhost:8000${NC}"
echo -e "${GREEN}✅ API文档: http://localhost:8000/docs${NC}"
echo ""

# 启动服务
npm run dev
