#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import time

def run_command(command, cwd=None):
    """运行命令并返回输出和退出码"""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout, result.stderr, result.returncode
    except KeyboardInterrupt:
        return '', '用户中断了命令执行', 1
    except Exception as e:
        return '', str(e), 1

def main():
    # 检查是否在正确的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(os.path.join(current_dir, 'build_vector_database.py')):
        print("错误: 请在vector_database目录下运行此脚本")
        input("按Enter键继续...")
        sys.exit(1)

    # 安装依赖
    print("安装依赖...")
    # 定义国内源列表
    chinese_mirrors = [
        'https://pypi.tuna.tsinghua.edu.cn/simple',
        'https://mirrors.aliyun.com/pypi/simple',
        'https://pypi.mirrors.ustc.edu.cn/simple',
        'https://pypi.hustunique.com/simple'
    ]

    # 尝试使用默认源安装
    print("尝试使用默认源安装依赖...")
    stdout, stderr, exit_code = run_command(
        ['pip', 'install', '-r', 'requirements.txt'],
        cwd=current_dir
    )

    # 如果默认源安装失败，尝试使用国内源
    mirror_index = 0
    while exit_code != 0 and mirror_index < len(chinese_mirrors):
        mirror = chinese_mirrors[mirror_index]
        print(f"默认源安装失败，尝试使用国内源 {mirror}...")
        stdout, stderr, exit_code = run_command(
            ['pip', 'install', '-r', 'requirements.txt', '-i', mirror],
            cwd=current_dir
        )
        mirror_index += 1

    if exit_code != 0:
        print(f"安装依赖失败: {stderr}")
        # 检测是否是用户中断
        if "用户中断了命令执行" in stderr:
            print("""
错误原因分析: 安装过程被用户中断。
解决方案:
1. 重新运行脚本
2. 或手动安装依赖: 打开命令提示符，进入vector_database目录，执行以下命令:
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
""")
        # 检测是否是缺少C++编译工具的错误
        elif "Microsoft Visual C++ 14.0 or greater is required" in stderr:
            print("""
错误原因分析: 缺少Microsoft Visual C++ 14.0或更高版本，无法编译chroma-hnswlib。
解决方案:
1. 安装Microsoft C++ Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. 或尝试安装预编译的chroma-hnswlib轮文件
3. 或使用conda环境安装依赖: conda install -c conda-forge chromadb
""")
        # 检测是否是SSL错误
        elif "SSL" in stderr or "SSLError" in stderr:
            print("""
错误原因分析: 网络连接问题，可能是SSL证书错误或网络不稳定。
解决方案:
1. 检查网络连接
2. 手动安装依赖: 打开命令提示符，进入vector_database目录，执行以下命令:
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
3. 或尝试使用其他国内源
""")
        # 检测是否是版本找不到的错误
        elif "No matching distribution found" in stderr:
            print("""
错误原因分析: 无法找到指定版本的依赖包。
解决方案:
1. 手动修改requirements.txt文件，放宽版本约束
2. 手动安装依赖: 打开命令提示符，进入vector_database目录，执行以下命令:
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
""")
        else:
            print("""
错误原因分析: 安装依赖时出现未知错误。
解决方案:
1. 手动安装依赖: 打开命令提示符，进入vector_database目录，执行以下命令:
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
""")
        input("按Enter键继续...")
        sys.exit(1)
    print(stdout)

    # 运行脚本
    print("开始构建向量数据库...")
    stdout, stderr, exit_code = run_command(
        ['python', 'build_vector_database.py'],
        cwd=current_dir
    )
    print(stdout)
    if exit_code != 0:
        print(f"向量数据库构建失败: {stderr}")
    else:
        print("向量数据库构建成功！")
        print("数据库存储位置: ./chroma_db")

    input("按Enter键继续...")
if __name__ == '__main__':
    main()