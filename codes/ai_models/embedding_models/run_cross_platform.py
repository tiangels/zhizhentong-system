#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智诊通系统 - 数据预处理统一启动脚本 (跨平台兼容)
支持 Windows, macOS, Linux
"""

import os
import sys
import subprocess
import platform
import argparse
import time
from pathlib import Path

class CrossPlatformRunner:
    def __init__(self):
        self.system = platform.system().lower()
        self.script_dir = Path(__file__).parent
        self.python_cmd = self._get_python_command()
        
    def _get_python_command(self):
        """获取Python命令，兼容不同平台"""
        commands = ['python3', 'python']
        for cmd in commands:
            try:
                result = subprocess.run([cmd, '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return cmd
            except FileNotFoundError:
                continue
        return 'python'  # 默认回退
    
    def install_dependencies(self, requirements_file):
        """安装依赖库"""
        print(f"安装依赖库: {requirements_file}")
        
        # 使用国内镜像源
        mirrors = [
            'https://pypi.tuna.tsinghua.edu.cn/simple',
            'https://mirrors.aliyun.com/pypi/simple',
            'https://pypi.mirrors.ustc.edu.cn/simple'
        ]
        
        for mirror in mirrors:
            try:
                cmd = [self.python_cmd, '-m', 'pip', 'install', 
                       '-r', str(requirements_file), '-i', mirror]
                result = subprocess.run(cmd, check=True, 
                                      capture_output=True, text=True)
                print(f"依赖安装成功，使用镜像: {mirror}")
                return True
            except subprocess.CalledProcessError as e:
                print(f"镜像 {mirror} 安装失败: {e.stderr}")
                continue
        
        print("所有镜像源均安装失败，请检查网络连接")
        return False
    
    def run_script(self, script_path, cwd=None):
        """运行Python脚本"""
        if not cwd:
            cwd = self.script_dir
            
        cmd = [self.python_cmd, str(script_path)]
        print(f"运行脚本: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, cwd=cwd, check=True, 
                                  capture_output=True, text=True)
            print(f"脚本执行成功: {script_path}")
            if result.stdout:
                print("输出:", result.stdout[-500:])  # 显示最后500字符
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"脚本执行失败: {script_path}")
            print(f"错误输出: {e.stderr}")
            return None
    
    def check_data_directories(self):
        """检查数据目录是否存在"""
        required_dirs = [
            'Medical-Dialogue-Dataset-Chinese',
            'VQA_data',
            'processed_vqa_data'
        ]
        
        missing_dirs = []
        for dir_name in required_dirs:
            dir_path = self.script_dir / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)
        
        if missing_dirs:
            print(f"警告: 缺少以下数据目录: {missing_dirs}")
            return False
        return True
    
    def create_shell_script(self):
        """创建Shell脚本 (适用于macOS/Linux)"""
        shell_script = """#!/bin/bash

echo "智诊通词向量模型处理脚本"
echo "检测到操作系统: $(uname -s)"

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

# 安装依赖
echo "安装依赖..."
$PYTHON_CMD -m pip install -r processed_vqa_data/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 运行预处理
echo "运行文本预处理..."
$PYTHON_CMD processed_vqa_data/text_preprocessing.py

echo "运行图像预处理..."
$PYTHON_CMD processed_vqa_data/image_text_preprocessing.py

# 构建向量数据库
echo "构建向量数据库..."
$PYTHON_CMD -m pip install -r vector_database/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
$PYTHON_CMD vector_database/build_vector_database.py

echo "处理完成!"
"""
        
        script_path = self.script_dir / "run_all.sh"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(shell_script)
        
        # 设置执行权限 (仅在Unix系统上)
        if self.system in ['linux', 'darwin']:
            os.chmod(script_path, 0o755)
        
        print(f"已创建Shell脚本: {script_path}")

def main():
    parser = argparse.ArgumentParser(
        description="智诊通系统数据预处理统一启动脚本"
    )
    parser.add_argument("--install-deps", action="store_true", 
                       help="安装依赖库")
    parser.add_argument("--text-only", action="store_true", 
                       help="仅处理文本数据")
    parser.add_argument("--image-only", action="store_true", 
                       help="仅处理图像数据")
    parser.add_argument("--build-vector-db", action="store_true", 
                       help="构建向量数据库")
    parser.add_argument("--all", action="store_true", 
                       help="执行完整流程")
    parser.add_argument("--create-shell", action="store_true", 
                       help="创建Shell脚本")
    
    args = parser.parse_args()
    runner = CrossPlatformRunner()
    
    print(f"检测到操作系统: {platform.system()}")
    print(f"Python命令: {runner.python_cmd}")
    
    # 创建Shell脚本
    if args.create_shell:
        runner.create_shell_script()
        return
    
    # 检查数据目录
    if not runner.check_data_directories():
        print("请确保数据目录存在后再运行")
        return
    
    # 安装依赖
    if args.install_deps or args.all:
        requirements_file = runner.script_dir / "processed_vqa_data" / "requirements.txt"
        if not runner.install_dependencies(requirements_file):
            return
    
    # 处理文本数据
    if args.text_only or args.all:
        print("\n=== 开始处理文本数据 ===")
        script_path = runner.script_dir / "processed_vqa_data" / "text_preprocessing.py"
        result = runner.run_script(script_path)
        if result is None:
            print("文本处理失败，停止执行")
            return
    
    # 处理图像数据
    if args.image_only or args.all:
        print("\n=== 开始处理图像数据 ===")
        script_path = runner.script_dir / "processed_vqa_data" / "image_text_preprocessing.py"
        result = runner.run_script(script_path)
        if result is None:
            print("图像处理失败，停止执行")
            return
    
    # 构建向量数据库
    if args.build_vector_db or args.all:
        print("\n=== 开始构建向量数据库 ===")
        # 先安装向量数据库依赖
        vdb_requirements = runner.script_dir / "vector_database" / "requirements.txt"
        if vdb_requirements.exists():
            if not runner.install_dependencies(vdb_requirements):
                print("向量数据库依赖安装失败，停止执行")
                return
        
        # 运行向量数据库构建脚本
        script_path = runner.script_dir / "vector_database" / "build_vector_database.py"
        result = runner.run_script(script_path)
        if result is None:
            print("向量数据库构建失败")
            return
    
    print("\n=== 处理完成 ===")

if __name__ == "__main__":
    main()
# -*- coding: utf-8 -*-
"""
智诊通系统 - 数据预处理统一启动脚本 (跨平台兼容)
支持 Windows, macOS, Linux
"""

import os
import sys
import subprocess
import platform
import argparse
import time
from pathlib import Path

class CrossPlatformRunner:
    def __init__(self):
        self.system = platform.system().lower()
        self.script_dir = Path(__file__).parent
        self.python_cmd = self._get_python_command()
        
    def _get_python_command(self):
        """获取Python命令，兼容不同平台"""
        commands = ['python3', 'python']
        for cmd in commands:
            try:
                result = subprocess.run([cmd, '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return cmd
            except FileNotFoundError:
                continue
        return 'python'  # 默认回退
    
    def install_dependencies(self, requirements_file):
        """安装依赖库"""
        print(f"安装依赖库: {requirements_file}")
        
        # 使用国内镜像源
        mirrors = [
            'https://pypi.tuna.tsinghua.edu.cn/simple',
            'https://mirrors.aliyun.com/pypi/simple',
            'https://pypi.mirrors.ustc.edu.cn/simple'
        ]
        
        for mirror in mirrors:
            try:
                cmd = [self.python_cmd, '-m', 'pip', 'install', 
                       '-r', str(requirements_file), '-i', mirror]
                result = subprocess.run(cmd, check=True, 
                                      capture_output=True, text=True)
                print(f"依赖安装成功，使用镜像: {mirror}")
                return True
            except subprocess.CalledProcessError as e:
                print(f"镜像 {mirror} 安装失败: {e.stderr}")
                continue
        
        print("所有镜像源均安装失败，请检查网络连接")
        return False
    
    def run_script(self, script_path, cwd=None):
        """运行Python脚本"""
        if not cwd:
            cwd = self.script_dir
            
        cmd = [self.python_cmd, str(script_path)]
        print(f"运行脚本: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, cwd=cwd, check=True, 
                                  capture_output=True, text=True)
            print(f"脚本执行成功: {script_path}")
            if result.stdout:
                print("输出:", result.stdout[-500:])  # 显示最后500字符
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"脚本执行失败: {script_path}")
            print(f"错误输出: {e.stderr}")
            return None
    
    def check_data_directories(self):
        """检查数据目录是否存在"""
        required_dirs = [
            'Medical-Dialogue-Dataset-Chinese',
            'VQA_data',
            'processed_vqa_data'
        ]
        
        missing_dirs = []
        for dir_name in required_dirs:
            dir_path = self.script_dir / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)
        
        if missing_dirs:
            print(f"警告: 缺少以下数据目录: {missing_dirs}")
            return False
        return True
    
    def create_shell_script(self):
        """创建Shell脚本 (适用于macOS/Linux)"""
        shell_script = """#!/bin/bash

echo "智诊通词向量模型处理脚本"
echo "检测到操作系统: $(uname -s)"

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

# 安装依赖
echo "安装依赖..."
$PYTHON_CMD -m pip install -r processed_vqa_data/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 运行预处理
echo "运行文本预处理..."
$PYTHON_CMD processed_vqa_data/text_preprocessing.py

echo "运行图像预处理..."
$PYTHON_CMD processed_vqa_data/image_text_preprocessing.py

# 构建向量数据库
echo "构建向量数据库..."
$PYTHON_CMD -m pip install -r vector_database/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
$PYTHON_CMD vector_database/build_vector_database.py

echo "处理完成!"
"""
        
        script_path = self.script_dir / "run_all.sh"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(shell_script)
        
        # 设置执行权限 (仅在Unix系统上)
        if self.system in ['linux', 'darwin']:
            os.chmod(script_path, 0o755)
        
        print(f"已创建Shell脚本: {script_path}")

def main():
    parser = argparse.ArgumentParser(
        description="智诊通系统数据预处理统一启动脚本"
    )
    parser.add_argument("--install-deps", action="store_true", 
                       help="安装依赖库")
    parser.add_argument("--text-only", action="store_true", 
                       help="仅处理文本数据")
    parser.add_argument("--image-only", action="store_true", 
                       help="仅处理图像数据")
    parser.add_argument("--build-vector-db", action="store_true", 
                       help="构建向量数据库")
    parser.add_argument("--all", action="store_true", 
                       help="执行完整流程")
    parser.add_argument("--create-shell", action="store_true", 
                       help="创建Shell脚本")
    
    args = parser.parse_args()
    runner = CrossPlatformRunner()
    
    print(f"检测到操作系统: {platform.system()}")
    print(f"Python命令: {runner.python_cmd}")
    
    # 创建Shell脚本
    if args.create_shell:
        runner.create_shell_script()
        return
    
    # 检查数据目录
    if not runner.check_data_directories():
        print("请确保数据目录存在后再运行")
        return
    
    # 安装依赖
    if args.install_deps or args.all:
        requirements_file = runner.script_dir / "processed_vqa_data" / "requirements.txt"
        if not runner.install_dependencies(requirements_file):
            return
    
    # 处理文本数据
    if args.text_only or args.all:
        print("\n=== 开始处理文本数据 ===")
        script_path = runner.script_dir / "processed_vqa_data" / "text_preprocessing.py"
        result = runner.run_script(script_path)
        if result is None:
            print("文本处理失败，停止执行")
            return
    
    # 处理图像数据
    if args.image_only or args.all:
        print("\n=== 开始处理图像数据 ===")
        script_path = runner.script_dir / "processed_vqa_data" / "image_text_preprocessing.py"
        result = runner.run_script(script_path)
        if result is None:
            print("图像处理失败，停止执行")
            return
    
    # 构建向量数据库
    if args.build_vector_db or args.all:
        print("\n=== 开始构建向量数据库 ===")
        # 先安装向量数据库依赖
        vdb_requirements = runner.script_dir / "vector_database" / "requirements.txt"
        if vdb_requirements.exists():
            if not runner.install_dependencies(vdb_requirements):
                print("向量数据库依赖安装失败，停止执行")
                return
        
        # 运行向量数据库构建脚本
        script_path = runner.script_dir / "vector_database" / "build_vector_database.py"
        result = runner.run_script(script_path)
        if result is None:
            print("向量数据库构建失败")
            return
    
    print("\n=== 处理完成 ===")

if __name__ == "__main__":
    main()




