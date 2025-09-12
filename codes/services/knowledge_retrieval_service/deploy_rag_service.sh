#!/bin/bash

# RAG检索增强系统部署脚本

set -e  # 遇到错误立即退出

echo "🚀 开始部署RAG检索增强系统..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查Docker是否安装
check_docker() {
    print_info "检查Docker环境..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    print_success "Docker环境检查通过"
}

# 检查端口是否被占用
check_ports() {
    print_info "检查端口占用情况..."
    
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        print_warning "端口8000已被占用"
        read -p "是否要停止占用端口的进程？(y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            lsof -ti:8000 | xargs kill -9
            print_success "已停止占用端口8000的进程"
        else
            print_error "请手动停止占用端口8000的进程后重试"
            exit 1
        fi
    fi
    
    if lsof -Pi :80 -sTCP:LISTEN -t >/dev/null ; then
        print_warning "端口80已被占用"
        read -p "是否要停止占用端口的进程？(y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            lsof -ti:80 | xargs kill -9
            print_success "已停止占用端口80的进程"
        else
            print_error "请手动停止占用端口80的进程后重试"
            exit 1
        fi
    fi
    
    print_success "端口检查完成"
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    mkdir -p data logs models
    print_success "目录创建完成"
}

# 构建Docker镜像
build_image() {
    print_info "构建Docker镜像..."
    docker-compose build --no-cache
    print_success "Docker镜像构建完成"
}

# 启动服务
start_services() {
    print_info "启动RAG服务..."
    docker-compose up -d
    print_success "RAG服务启动完成"
}

# 等待服务就绪
wait_for_service() {
    print_info "等待服务就绪..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            print_success "服务已就绪"
            return 0
        fi
        
        print_info "等待服务启动... ($attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    print_error "服务启动超时"
    return 1
}

# 运行健康检查
health_check() {
    print_info "运行健康检查..."
    
    # 检查服务状态
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "服务健康检查通过"
    else
        print_error "服务健康检查失败"
        return 1
    fi
    
    # 检查API文档
    if curl -f http://localhost:8000/docs >/dev/null 2>&1; then
        print_success "API文档可访问"
    else
        print_warning "API文档不可访问"
    fi
    
    # 运行快速测试
    print_info "运行快速功能测试..."
    if /opt/anaconda3/bin/conda run -n nlp python quick_test.py >/dev/null 2>&1; then
        print_success "功能测试通过"
    else
        print_warning "功能测试失败，但服务仍在运行"
    fi
}

# 显示部署信息
show_deployment_info() {
    print_success "RAG检索增强系统部署完成！"
    echo
    echo "📋 服务信息:"
    echo "   🌐 服务地址: http://localhost:8000"
    echo "   📖 API文档: http://localhost:8000/docs"
    echo "   🔍 健康检查: http://localhost:8000/health"
    echo "   📊 统计信息: http://localhost:8000/stats"
    echo
    echo "📋 管理命令:"
    echo "   查看日志: docker-compose logs -f rag-service"
    echo "   停止服务: docker-compose down"
    echo "   重启服务: docker-compose restart"
    echo "   查看状态: docker-compose ps"
    echo
    echo "📋 测试命令:"
    echo "   快速测试: /opt/anaconda3/bin/conda run -n nlp python quick_test.py"
    echo "   完整测试: /opt/anaconda3/bin/conda run -n nlp python test_complete_rag_flow.py"
    echo "   演示脚本: /opt/anaconda3/bin/conda run -n nlp python demo_rag_system.py"
    echo
    echo "🎉 部署完成！现在可以使用RAG服务了。"
}

# 清理函数
cleanup() {
    print_info "清理临时文件..."
    # 这里可以添加清理逻辑
    print_success "清理完成"
}

# 主函数
main() {
    echo "============================================================"
    echo "🎯 RAG检索增强系统部署脚本"
    echo "============================================================"
    
    # 设置错误处理
    trap cleanup EXIT
    
    # 检查环境
    check_docker
    check_ports
    
    # 准备部署
    create_directories
    
    # 构建和启动
    build_image
    start_services
    
    # 等待服务就绪
    if ! wait_for_service; then
        print_error "服务启动失败"
        exit 1
    fi
    
    # 健康检查
    health_check
    
    # 显示部署信息
    show_deployment_info
}

# 如果直接运行脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
