# PowerShell脚本，用于运行向量数据库构建

# 检查是否在正确的目录
if (-not (Test-Path -Path ".\build_vector_database.py")) {
    Write-Host "错误: 请在vector_database目录下运行此脚本"
    Read-Host -Prompt "按Enter键继续..."
    exit 1
}

# 安装依赖
if (Test-Path -Path ".\requirements.txt") {
    Write-Host "安装依赖..."
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "安装依赖失败，请检查网络连接"
        Read-Host -Prompt "按Enter键继续..."
        exit 1
    }
}

# 运行脚本
Write-Host "开始构建向量数据库..."
python build_vector_database.py

# 检查脚本执行结果
if ($LASTEXITCODE -eq 0) {
    Write-Host "向量数据库构建成功！"
    Write-Host "数据库存储位置: .\chroma_db"
} else {
    Write-Host "向量数据库构建失败，请查看上面的错误信息"
}

Read-Host -Prompt "按Enter键继续..."
