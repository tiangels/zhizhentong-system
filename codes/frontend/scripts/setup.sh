#!/bin/bash

# 智诊通前端项目设置脚本
# 用于初始化项目环境和依赖

set -e

echo "🚀 开始设置智诊通前端项目..."

# 检查Node.js版本
echo "📋 检查Node.js版本..."
NODE_VERSION=$(node --version)
echo "当前Node.js版本: $NODE_VERSION"

# 检查npm版本
echo "📋 检查npm版本..."
NPM_VERSION=$(npm --version)
echo "当前npm版本: $NPM_VERSION"

# 安装依赖
echo "📦 安装项目依赖..."
npm install

# 复制环境变量文件
echo "⚙️  设置环境变量..."
if [ ! -f .env ]; then
  cp env.example .env
  echo "✅ 已创建.env文件，请根据需要修改配置"
else
  echo "ℹ️  .env文件已存在，跳过创建"
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p src/assets/images
mkdir -p src/assets/icons
mkdir -p src/components/common
mkdir -p src/components/chat
mkdir -p src/components/input
mkdir -p src/components/layout
mkdir -p src/views/auth
mkdir -p src/views/chat
mkdir -p src/views/profile
mkdir -p src/views/settings
mkdir -p src/stores
mkdir -p src/services/api
mkdir -p src/router
mkdir -p src/plugins
mkdir -p src/types

# 检查Docker环境
echo "🐳 检查Docker环境..."
if command -v docker &> /dev/null; then
  DOCKER_VERSION=$(docker --version)
  echo "Docker版本: $DOCKER_VERSION"
  
  if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo "Docker Compose版本: $COMPOSE_VERSION"
  else
    echo "⚠️  Docker Compose未安装"
  fi
else
  echo "⚠️  Docker未安装，将无法使用容器化部署"
fi

# 生成类型声明文件
echo "🔧 生成类型声明文件..."
npm run type-check

echo "✅ 项目设置完成！"
echo ""
echo "📝 下一步操作："
echo "1. 修改.env文件中的配置"
echo "2. 添加favicon.ico和logo.png到public目录"
echo "3. 运行 'npm run dev' 启动开发服务器"
echo "4. 访问 http://localhost:3000 查看应用"
echo ""
echo "🔧 常用命令："
echo "  npm run dev      - 启动开发服务器"
echo "  npm run build    - 构建生产版本"
echo "  npm run preview  - 预览生产版本"
echo "  npm run lint     - 代码检查"
echo "  npm run format   - 代码格式化"
echo ""
echo "🐳 Docker命令："
echo "  docker-compose up -d    - 启动所有服务"
echo "  docker-compose down     - 停止所有服务"
echo "  docker-compose logs     - 查看日志"
