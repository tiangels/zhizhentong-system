#!/bin/bash

# 知识检索系统部署脚本

set -e  # 遇到错误立即退出

echo "🚀 开始部署知识检索系统..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统环境
check_environment() {
    log_info "检查系统环境..."
    
    # 检查Python版本
    if ! command -v /opt/anaconda3/bin/conda run -n nlp python &> /dev/null; then
        log_error "Python3 未安装，请先安装Python3"
        exit 1
    fi
    
    python_version=$(/opt/anaconda3/bin/conda run -n nlp python --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ $(echo "$python_version < 3.8" | bc -l) -eq 1 ]]; then
        log_error "Python版本过低，需要3.8+，当前版本: $python_version"
        exit 1
    fi
    
    log_success "Python版本检查通过: $python_version"
    
    # 检查pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 未安装，请先安装pip3"
        exit 1
    fi
    
    log_success "pip3 检查通过"
}

# 安装依赖
install_dependencies() {
    log_info "安装Python依赖包..."
    
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
        log_success "依赖包安装完成"
    else
        log_warning "requirements.txt 不存在，跳过依赖安装"
    fi
}

# 检查模型文件
check_models() {
    log_info "检查模型文件..."
    
    # 检查LLM模型
    llm_model_path="../../aimodels/Qwen2-0.5B-Medical-MLX"
    if [ -d "$llm_model_path" ]; then
        log_success "LLM模型路径存在: $llm_model_path"
    else
        log_warning "LLM模型路径不存在: $llm_model_path"
        log_warning "请确保Qwen2-0.5B-Medical-MLX模型已下载到正确位置"
    fi
    
    # 检查向量化模型（会自动下载）
    log_info "向量化模型将在首次运行时自动下载"
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    mkdir -p logs
    mkdir -p data
    mkdir -p data/vectors
    mkdir -p data/documents
    
    log_success "目录创建完成"
}

# 设置权限
set_permissions() {
    log_info "设置文件权限..."
    
    chmod +x quick_start.sh
    chmod +x deploy.sh
    
    # 设置Python文件权限
    find . -name "*.py" -exec chmod 644 {} \;
    
    log_success "权限设置完成"
}

# 运行测试
run_tests() {
    log_info "运行系统测试..."
    
    if [ -f "test_retrieval_service.py" ]; then
        /opt/anaconda3/bin/conda run -n nlp python test_retrieval_service.py
        log_success "测试完成"
    else
        log_warning "测试文件不存在，跳过测试"
    fi
}

# 启动服务
start_service() {
    log_info "启动知识检索服务..."
    
    # 检查端口是否被占用
    if lsof -Pi :8002 -sTCP:LISTEN -t >/dev/null ; then
        log_warning "端口8002已被占用，尝试停止现有服务..."
        pkill -f "start_retrieval_service.py" || true
        sleep 2
    fi
    
    # 启动服务
    nohup /opt/anaconda3/bin/conda run -n nlp python start_retrieval_service.py --host 0.0.0.0 --port 8002 > logs/retrieval_service.log 2>&1 &
    
    # 等待服务启动
    sleep 5
    
    # 检查服务状态
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        log_success "知识检索服务启动成功！"
        log_info "服务地址: http://localhost:8000"
        log_info "API文档: http://localhost:8000/docs"
        log_info "健康检查: http://localhost:8000/health"
        log_info "日志文件: logs/retrieval_service.log"
    else
        log_error "知识检索服务启动失败，请检查日志: logs/retrieval_service.log"
        exit 1
    fi
}

# 显示使用说明
show_usage() {
    echo ""
    echo "🎉 知识检索系统部署完成！"
    echo ""
    echo "📖 使用说明:"
    echo "  1. 查看API文档: http://localhost:8000/docs"
    echo "  2. 健康检查: http://localhost:8000/health"
    echo "  3. 查看日志: tail -f logs/retrieval_service.log"
    echo "  4. 停止服务: pkill -f start_retrieval_service.py"
    echo ""
    echo "🧪 测试命令:"
    echo "  /opt/anaconda3/bin/conda run -n nlp python test_retrieval_service.py"
    echo ""
    echo "🔧 管理命令:"
    echo "  ./quick_start.sh  # 快速启动"
    echo "  ./deploy.sh       # 重新部署"
    echo ""
}

# 主函数
main() {
    echo "=========================================="
    echo "    知识检索系统部署脚本"
    echo "=========================================="
    echo ""
    
    check_environment
    install_dependencies
    check_models
    create_directories
    set_permissions
    run_tests
    start_service
    show_usage
    
    echo "✅ 部署完成！"
}

# 执行主函数
main "$@"
