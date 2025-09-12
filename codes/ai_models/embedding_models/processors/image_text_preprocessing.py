import os
import cv2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import jieba
from tqdm import tqdm
from sklearn.model_selection import train_test_split
import torch
from torchvision import transforms

# 设置中文字体显示
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]

class MedicalImageTextPreprocessor:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.images_dir = os.path.join(data_dir, "chestX-rays", "images")
        self.reports_file = os.path.join(data_dir, "chestX-rays", "indiana_reports.csv")
        self.output_dir = os.path.join("/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge", "image_text_data", "processed")
        os.makedirs(self.output_dir, exist_ok=True)

        # 图像预处理参数
        self.image_size = (224, 224)
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize(self.image_size),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def load_reports(self):
        """加载报告数据"""
        print(f"加载报告数据: {self.reports_file}")
        self.reports_df = pd.read_csv(self.reports_file)
        print(f"共加载 {len(self.reports_df)} 条报告数据")
        return self.reports_df

    def clean_reports(self):
        """清洗报告文本"""
        print("清洗报告文本...")
        # 去除缺失值
        self.reports_df = self.reports_df.dropna(subset=['image', 'findings', 'impression'])
        print(f"去除缺失值后: {len(self.reports_df)}")

        # 去除特殊字符
        for col in ['findings', 'impression', 'MeSH', 'Problems']:
            if col in self.reports_df.columns:
                self.reports_df[col] = self.reports_df[col].str.replace('[^\w\s\u4e00-\u9fa5]', '', regex=True)

        # 中文分词
        print("对报告文本进行分词...")
        for col in ['findings', 'impression']:
            self.reports_df[f'{col}_tokens'] = self.reports_df[col].apply(
                lambda x: ' '.join(jieba.cut(x)) if isinstance(x, str) else ""
            )

    def process_images(self):
        """处理图像数据"""
        print("处理图像数据...")
        processed_images = []
        valid_indices = []

        # 检查图像目录是否存在
        print(f"图像目录: {self.images_dir}")
        if not os.path.exists(self.images_dir):
            print(f"错误: 图像目录不存在 {self.images_dir}")
            return

        # 列出图像目录中的前10个文件，用于调试
        try:
            files = os.listdir(self.images_dir)
            print(f"图像目录中的文件数量: {len(files)}")
            if len(files) > 0:
                print(f"前10个文件: {files[:10]}")
        except Exception as e:
            print(f"无法列出图像目录中的文件: {str(e)}")

        # 创建一个图像文件名到路径的映射，以便快速查找
        image_file_map = {}
        for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']:
            for file_name in files:
                if file_name.lower().endswith(ext):
                    # 提取文件名中的数字部分（假设格式为 {number}_IM-...）
                    parts = file_name.split('_')
                    if len(parts) > 0 and parts[0].isdigit():
                        number = parts[0]
                        if number not in image_file_map:
                            image_file_map[number] = os.path.join(self.images_dir, file_name)

        print(f"已建立 {len(image_file_map)} 个图像文件映射")

        valid_rows = []
        for idx, row in tqdm(self.reports_df.iterrows(), total=len(self.reports_df)):
            uid = str(row['uid'])
            print(f"尝试查找uid为 {uid} 的图像")

            # 首先尝试直接匹配uid
            if uid in image_file_map:
                image_path = image_file_map[uid]
                print(f"找到匹配的图像: {image_path}")
            else:
                # 如果没有直接匹配，尝试查找包含uid的文件名
                image_path = None
                for file_name in files:
                    if uid in file_name:
                        image_path = os.path.join(self.images_dir, file_name)
                        print(f"找到包含uid的图像: {image_path}")
                        break

            if image_path and os.path.exists(image_path):
                # 加载图像
                image = cv2.imread(image_path)
                if image is not None:
                    # 转换为RGB
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    # 应用预处理
                    processed_image = self.transform(image)
                    processed_images.append(processed_image.numpy())
                    valid_rows.append(row)
                    print(f"成功加载并处理图像: {image_path}")
                else:
                    print(f"警告: 无法加载图像 {image_path}")
            else:
                print(f"警告: 未找到uid为 {uid} 的图像文件")

        # 只保留有有效图像的报告
        if valid_rows:
            self.reports_df = pd.DataFrame(valid_rows).reset_index(drop=True)
        else:
            self.reports_df = pd.DataFrame()
        self.processed_images = np.array(processed_images) if processed_images else np.array([])
        print(f"有效图文对数量: {len(self.reports_df)}")

    def save_processed_data(self):
        """保存处理后的数据"""
        # 检查是否有有效数据
        if len(self.reports_df) == 0:
            print("警告: 没有有效的图文数据可保存")
            return

        # 保存处理后的报告
        reports_output = os.path.join(self.output_dir, "processed_reports.csv")
        self.reports_df.to_csv(reports_output, index=False, encoding='utf-8')
        print(f"处理后的报告已保存至: {reports_output}")

        # 保存处理后的图像（作为numpy数组）
        images_output = os.path.join(self.output_dir, "processed_images.npy")
        np.save(images_output, self.processed_images)
        print(f"处理后的图像已保存至: {images_output}")

        # 划分训练集、验证集和测试集
        train_df, temp_df = train_test_split(self.reports_df, test_size=0.3, random_state=42)
        val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42)

        # 保存数据集划分
        train_df.to_csv(os.path.join(self.output_dir, "train_reports.csv"), index=False, encoding='utf-8')
        val_df.to_csv(os.path.join(self.output_dir, "val_reports.csv"), index=False, encoding='utf-8')
        test_df.to_csv(os.path.join(self.output_dir, "test_reports.csv"), index=False, encoding='utf-8')
        print("数据集划分已完成并保存")

    def visualize_samples(self, num_samples=5):
        """可视化处理后的样本"""
        plt.figure(figsize=(15, 10))
        sample_indices = np.random.choice(len(self.reports_df), min(num_samples, len(self.reports_df)), replace=False)

        for i, idx in enumerate(sample_indices):
            plt.subplot(2, num_samples, i+1)
            # 显示原始图像
            image_name = self.reports_df.iloc[idx]['image']
            image_path = None
            for ext in ['.png', '.jpg', '.jpeg']:
                temp_path = os.path.join(self.images_dir, image_name + ext)
                if os.path.exists(temp_path):
                    image_path = temp_path
                    break

            if image_path:
                image = cv2.imread(image_path)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                plt.imshow(image)
                plt.title(f"原始图像: {image_name}")
                plt.axis('off')

            # 显示处理后的图像
            plt.subplot(2, num_samples, i+1+num_samples)
            processed_image = self.processed_images[idx].transpose(1, 2, 0)
            # 反归一化以便显示
            mean = np.array([0.485, 0.456, 0.406])
            std = np.array([0.229, 0.224, 0.225])
            processed_image = std * processed_image + mean
            processed_image = np.clip(processed_image, 0, 1)
            plt.imshow(processed_image)
            plt.title(f"处理后图像")
            plt.axis('off')

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "sample_images.png"))
        print("样本图像已保存")

    def run(self):
        """运行预处理流程"""
        print("开始医疗图文数据预处理...")
        self.load_reports()
        self.clean_reports()
        self.process_images()

        # 检查是否有有效数据
        if len(self.reports_df) == 0:
            print("错误: 没有找到有效的图文数据。预处理终止。")
            return

        self.save_processed_data()
        self.visualize_samples()
        print("图文数据预处理完成!")

if __name__ == "__main__":
    # 设置数据目录 - 指向实际的原始数据目录
    data_dir = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/image_text_data/raw"

    # 创建预处理实例并运行
    preprocessor = MedicalImageTextPreprocessor(data_dir)
    preprocessor.run()