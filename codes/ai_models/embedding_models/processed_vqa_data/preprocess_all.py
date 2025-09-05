import os
import sys
import argparse
import subprocess
import time

def run_command(command, cwd=None):
    """运行命令并返回输出"""
    print(f"运行命令: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"命令成功完成: {' '.join(command)}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {' '.join(command)}")
        print(f"错误输出: {e.stderr}")
        sys.exit(1)

def install_dependencies(requirements_file):
    """安装依赖库"""
    print(f"安装依赖库: {requirements_file}")
    run_command([sys.executable, "-m", "pip", "install", "-r", requirements_file])

def main():
    parser = argparse.ArgumentParser(description="多模态智能医生问诊系统数据预处理")
    parser.add_argument("--install", action="store_true", help="安装依赖库")
    parser.add_argument("--text-only", action="store_true", help="仅处理文本数据")
    parser.add_argument("--image-text-only", action="store_true", help="仅处理图文数据")
    args = parser.parse_args()

    # 获取当前脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 安装依赖
    if args.install:
        install_dependencies(os.path.join(script_dir, "requirements.txt"))
        print("依赖库安装完成!")

    # 运行文本数据预处理
    if not args.image_text_only:
        print("开始处理文本数据...")
        start_time = time.time()
        run_command([sys.executable, os.path.join(script_dir, "text_preprocessing.py")], cwd=script_dir)
        end_time = time.time()
        print(f"文本数据预处理完成，耗时: {end_time - start_time:.2f} 秒")

    # 运行图文数据预处理
    if not args.text_only:
        print("开始处理图文数据...")
        start_time = time.time()
        try:
            # 检查图像目录是否存在
            image_dir = os.path.join(script_dir, "VQA_data", "ChestX-rays", "images", "images_normalized")
            if not os.path.exists(image_dir):
                print(f"警告: 图像目录不存在: {image_dir}")
                # 尝试创建目录
                os.makedirs(image_dir, exist_ok=True)
                print(f"已尝试创建图像目录: {image_dir}")

            # 运行预处理脚本
            script_path = os.path.join(script_dir, "image_text_preprocessing.py")
            result = subprocess.run(
                [sys.executable, script_path],
                cwd=script_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            print(f"脚本输出: {result.stdout}")
            if result.returncode != 0:
                print(f"脚本执行失败，错误输出: {result.stderr}")
            else:
                print("图文数据预处理脚本成功执行")

        except Exception as e:
            print(f"处理图文数据时发生错误: {str(e)}")

        end_time = time.time()
        print(f"图文数据预处理完成，耗时: {end_time - start_time:.2f} 秒")

    print("所有数据预处理完成!")

if __name__ == "__main__":
    main()