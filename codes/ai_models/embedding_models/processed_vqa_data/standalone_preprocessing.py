import os
import sys
import pandas as pd
import cv2
import numpy as np
import torch
from torchvision import transforms
from tqdm import tqdm
import shutil

# 定义常量
DATA_DIR = 'd:\\Consultation system\\VQA_data\\ChestX-rays'
REPORTS_PATH = os.path.join(DATA_DIR, 'indiana_reports.csv')
IMAGES_DIR = os.path.join(DATA_DIR, 'images', 'images_normalized')
OUTPUT_DIR = 'd:\\Consultation system\\processed_vqa_data'
IMAGE_SIZE = (224, 224)

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 定义图像变换
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# 读取报告数据
print(f"读取报告文件: {REPORTS_PATH}")
reports_df = pd.read_csv(REPORTS_PATH)
print(f"报告数量: {len(reports_df)}")
print("前5行报告:")
print(reports_df.head())

# 检查图像目录
print(f"图像目录: {IMAGES_DIR}")
if not os.path.exists(IMAGES_DIR):
    print(f"错误: 图像目录不存在 {IMAGES_DIR}")
    sys.exit(1)

# 列出图像目录中的文件
try:
    files = os.listdir(IMAGES_DIR)
    print(f"图像文件数量: {len(files)}")
    print("前10个图像文件:")
    print(files[:10])
except Exception as e:
    print(f"无法列出图像目录中的文件: {str(e)}")
    sys.exit(1)

# 创建图像文件名到路径的映射
image_file_map = {}
for file_name in files:
    # 提取文件名中的数字部分（假设格式为 {number}_IM-...）
    parts = file_name.split('_')
    if len(parts) > 0 and parts[0].isdigit():
        number = parts[0]
        if number not in image_file_map:
            image_file_map[number] = os.path.join(IMAGES_DIR, file_name)

print(f"已建立 {len(image_file_map)} 个图像文件映射")

# 处理图像和报告
processed_images = []
valid_reports = []
matched_count = 0

for idx, row in tqdm(reports_df.iterrows(), total=len(reports_df)):
    uid = str(row['uid'])
    report_text = row['Problems'] if 'Problems' in row else row['MeSH']

    # 查找匹配的图像
    image_path = None
    if uid in image_file_map:
        image_path = image_file_map[uid]
        matched_count += 1
    else:
        # 尝试查找包含uid的文件名
        for file_name in files:
            if uid in file_name:
                image_path = os.path.join(IMAGES_DIR, file_name)
                matched_count += 1
                break

    if image_path and os.path.exists(image_path):
        # 加载和处理图像
        try:
            image = cv2.imread(image_path)
            if image is not None:
                # 转换为RGB
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                # 应用变换
                processed_image = transform(image)
                processed_images.append(processed_image.numpy())
                valid_reports.append(row)
                if idx < 5:  # 只打印前5个匹配结果
                    print(f"找到匹配: uid={uid}, 图像路径={image_path}")
            else:
                print(f"警告: 无法加载图像 {image_path}")
        except Exception as e:
            print(f"处理图像 {image_path} 时出错: {str(e)}")
    else:
        print(f"警告: 未找到uid为 {uid} 的图像文件")

print(f"匹配成功的数量: {matched_count}")
print(f"有效图文对数量: {len(valid_reports)}")

# 保存处理后的数据
if len(valid_reports) > 0:
    valid_reports_df = pd.DataFrame(valid_reports)
    processed_images_np = np.array(processed_images)

    # 保存报告
    reports_output_path = os.path.join(OUTPUT_DIR, 'processed_reports.csv')
    valid_reports_df.to_csv(reports_output_path, index=False)
    print(f"已保存处理后的报告到: {reports_output_path}")

    # 保存图像
    images_output_path = os.path.join(OUTPUT_DIR, 'processed_images.npy')
    np.save(images_output_path, processed_images_np)
    print(f"已保存处理后的图像到: {images_output_path}")

    # 划分训练集和测试集
    from sklearn.model_selection import train_test_split
    try:
        train_reports, test_reports, train_images, test_images = train_test_split(
            valid_reports_df, processed_images_np, test_size=0.2, random_state=42
        )

        # 保存训练集和测试集
        train_reports.to_csv(os.path.join(OUTPUT_DIR, 'train_reports.csv'), index=False)
        test_reports.to_csv(os.path.join(OUTPUT_DIR, 'test_reports.csv'), index=False)
        np.save(os.path.join(OUTPUT_DIR, 'train_images.npy'), train_images)
        np.save(os.path.join(OUTPUT_DIR, 'test_images.npy'), test_images)

        print(f"训练集大小: {len(train_reports)}")
        print(f"测试集大小: {len(test_reports)}")
    except Exception as e:
        print(f"划分训练集和测试集时出错: {str(e)}")
else:
    print("没有找到有效图文对，无法保存处理后的数据")

print("预处理完成")