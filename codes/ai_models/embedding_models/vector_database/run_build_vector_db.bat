@echo off

REM 向量数据库构建脚本

REM 检查是否在正确的目录
if not exist build_vector_database.py (
    echo 错误: 请在vector_database目录下运行此批处理文件
    pause
    exit /b 1
)

REM 安装依赖
if exist requirements.txt (
    echo 安装依赖...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo 安装依赖失败，请检查网络连接
        pause
        exit /b 1
    )
)

REM 运行脚本
 echo 开始构建向量数据库...
 python build_vector_database.py

REM 检查脚本执行结果
if %ERRORLEVEL% EQU 0 (
    echo 向量数据库构建成功！
    echo 数据库存储位置: .\chroma_db
) else (
    echo 向量数据库构建失败，请查看上面的错误信息
)

pause
