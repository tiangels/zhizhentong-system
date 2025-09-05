import os
import argparse
from huggingface_hub import snapshot_download

def download_model(model_name="shibing624/text2vec-base-chinese", local_dir=None):
    """
    从Hugging Face下载模型到本地目录
    
    参数:
    model_name: 模型名称，默认为"shibing624/text2vec-base-chinese"
    local_dir: 本地目录，默认为当前目录下的models文件夹
    """
    # 如果未指定本地目录，则使用当前目录下的models文件夹
    if local_dir is None:
        local_dir = os.path.join(os.getcwd(), "models", model_name.split("/")[-1])
        os.makedirs(local_dir, exist_ok=True)
    
    print(f"开始下载模型 '{model_name}' 到目录 '{local_dir}'...")
    try:
        # 只下载必要的模型文件，排除大型的ONNX和OpenVINO文件
        snapshot_download(
            model_name,
            local_dir=local_dir,
            ignore_patterns=[
                "*.onnx",  # 排除ONNX模型文件
                "openvino/*",  # 排除OpenVINO相关文件
                "logs.txt"  # 排除日志文件
            ],
            max_workers=4,  # 限制并发下载数量
            resume_download=True  # 支持断点续传
        )
        print(f"模型 '{model_name}' 下载完成！")
        print(f"模型存储位置: {local_dir}")
    except Exception as e:
        print(f"下载模型时出错: {e}")
        print("请检查网络连接或代理设置。")
        return False
    return True

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="从Hugging Face下载模型到本地")
    parser.add_argument("--model", type=str, default="shibing624/text2vec-base-chinese",
                        help="模型名称，默认为'shibing624/text2vec-base-chinese'")
    parser.add_argument("--dir", type=str, default=None,
                        help="本地目录，默认为当前目录下的models文件夹")
    args = parser.parse_args()
    
    # 下载模型
    download_model(args.model, args.dir)