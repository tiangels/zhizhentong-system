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

# 导入字体配置模块
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config'))
from font_config import configure_chinese_font

# 配置中文字体
configure_chinese_font()

try:
    from .base_processor import BaseDataProcessor
except ImportError:
    from base_processor import BaseDataProcessor

class MedicalImageTextPreprocessor(BaseDataProcessor):
    """医疗图文数据预处理器
    功能：
    1. 图像数据清洗和预处理
    2. 文本数据清洗和预处理
    3. 生成供文档切分使用的JSON格式数据
    
    注意：不包含文档切分和向量化功能，只负责数据预处理
    """
    
    def __init__(self, data_dir):
        # 设置输出目录
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
        output_dir = os.path.join(project_root, "datas", "medical_knowledge", "image_text_data", "processed")
        super().__init__(data_dir, output_dir, "MedicalImageTextPreprocessor")
        
        self.data_dir = data_dir
        self.images_dir = os.path.join(data_dir, "chestX-rays", "images")
        self.reports_file = os.path.join(data_dir, "chestX-rays", "indiana_reports.csv")

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

        # 生成供文档切分使用的JSON格式数据
        self._save_json_data()
    
    def _save_json_data(self):
        """生成供文档切分使用的JSON格式数据"""
        try:
            # 准备JSON数据
            json_data = []
            for idx, row in self.reports_df.iterrows():
                # 合并findings和impression作为文本内容
                text_content = ""
                if 'findings' in row and pd.notna(row['findings']):
                    text_content += f"检查结果: {row['findings']}\n"
                if 'impression' in row and pd.notna(row['impression']):
                    text_content += f"诊断印象: {row['impression']}\n"
                if 'MeSH' in row and pd.notna(row['MeSH']):
                    text_content += f"MeSH术语: {row['MeSH']}\n"
                if 'Problems' in row and pd.notna(row['Problems']):
                    text_content += f"问题描述: {row['Problems']}\n"
                
                # 1. 调用基类的文本清洗功能，保留医学符号
                cleaned_result = self.clean_text(text_content.strip())
                
                # 2. 调用数据脱敏功能
                desensitized_result = self.desensitize_text(cleaned_result['cleaned_text'])
                
                # 3. 创建结构化输出
                metadata = {
                    'file_name': row['image'],
                    'file_path': f"image_text_data/raw/chestX-rays/images/{row['image']}",
                    'data_type': 'image_text',
                    'image_type': 'chest_xray',
                    'uid': row['uid'],
                    'age': row.get('age', ''),
                    'gender': row.get('gender', ''),
                    'view_position': row.get('view_position', ''),
                    'original_findings': row.get('findings', ''),
                    'original_impression': row.get('impression', ''),
                    'quality_score': cleaned_result['quality_score'],
                    'medical_terms_count': cleaned_result['medical_terms_count'],
                    'sensitive_info': desensitized_result['sensitive_info'],
                    'has_sensitive_data': desensitized_result['has_sensitive_data']
                }
                
                structured_doc = self.create_structured_output(
                    desensitized_result['desensitized_text'], 
                    metadata
                )
                
                json_data.append(structured_doc)
            
            # 保存为JSON格式
            import json
            json_path = os.path.join(self.output_dir, 'image_text_documents.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"✅ 图文JSON数据文件已保存: {json_path}")
            
        except Exception as e:
            self.logger.error(f"❌ 图文JSON数据文件保存失败: {e}")

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
        try:
            self.log_processing_step("步骤1: 加载报告数据", f"从文件加载: {self.reports_file}")
            self.load_reports()
            self.logger.info(f"报告数据加载完成，共 {len(self.reports_df)} 条")
            
            # 在数据加载后记录开始日志
            self.log_processing_start("医疗图文数据", len(self.reports_df))
            
            self.log_processing_step("步骤2: 清洗报告文本", "清理文本内容和进行分词处理")
            self.clean_reports()
            self.logger.info("报告文本清洗完成")
            
            self.log_processing_step("步骤3: 处理图像数据", "加载和预处理图像文件")
            self.process_images()
            self.logger.info(f"图像数据处理完成，有效图文对: {len(self.reports_df)}")

            # 检查是否有有效数据
            if len(self.reports_df) == 0:
                self.logger.error("❌ 没有找到有效的图文数据。预处理终止。")
                return

            self.log_processing_step("步骤4: 保存处理后的数据", "保存图文数据到文件")
            self.save_processed_data()
            self.logger.info("数据保存完成")
            
            self.log_processing_step("步骤5: 生成样本可视化", "创建样本图像展示")
            self.visualize_samples()
            self.logger.info("样本可视化完成")
            
            self.log_processing_complete("医疗图文数据", len(self.reports_df), len(self.reports_df))
            self.logger.info("📄 图文数据预处理完成，JSON文件已保存供文档切分使用")
            
        except Exception as e:
            self.logger.error(f"❌ 图文数据预处理失败: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    # 设置数据目录 - 指向实际的原始数据目录
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
    data_dir = os.path.join(project_root, "datas", "medical_knowledge", "image_text_data", "raw")

    # 创建预处理实例并运行
    preprocessor = MedicalImageTextPreprocessor(data_dir)
    preprocessor.run()