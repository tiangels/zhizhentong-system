import os
import re
from this import d
import pandas as pd
import jieba
from tqdm import tqdm

# 设置中文字体显示
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]

class MedicalTextPreprocessor:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.output_file = os.path.join(os.path.dirname(data_dir), "processed_medical_dialogues.csv")
        self.all_dialogues = []

    def load_data(self):
        """加载所有年份的医疗对话数据"""
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".txt") and filename[:4].isdigit():
                file_path = os.path.join(self.data_dir, filename)
                print(f"加载文件: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.parse_dialogues(content)
        print(f"共加载 {len(self.all_dialogues)} 条对话数据")

    def parse_dialogues(self, content):
        """解析对话内容，提取结构化信息"""
        # 分割不同的对话记录
        dialogues = re.split(r'id=\d+', content)
        for dialog in dialogues[1:]:  # 跳过第一个空字符串
            dialog_id = re.search(r'id=(\d+)', dialog)
            if dialog_id:
                dialog_id = dialog_id.group(1)
            else:
                dialog_id = "unknown"

            # 提取医生科室
            doctor_faculty = re.search(r'Doctor faculty\n(.*?)\n', dialog)
            doctor_faculty = doctor_faculty.group(1).strip() if doctor_faculty else ""

            # 提取疾病信息
            disease = re.search(r'疾病：\s*(.*?)\n', dialog)
            disease = disease.group(1).strip() if disease else ""

            # 提取病情描述
            description = re.search(r'病情描述：\s*(.*?)\n希望获得的帮助', dialog, re.DOTALL)
            if not description:
                description = re.search(r'病情描述：\s*(.*?)\n过敏史', dialog, re.DOTALL)
            description = description.group(1).strip() if description else ""

            # 提取希望获得的帮助
            help_required = re.search(r'希望获得的帮助：\s*(.*?)\n', dialog, re.DOTALL)
            help_required = help_required.group(1).strip() if help_required else ""

            # 提取既往病史
            medical_history = re.search(r'既往病史：\s*(.*?)\n', dialog)
            medical_history = medical_history.group(1).strip() if medical_history else ""

            # 提取诊断结果
            diagnosis = re.search(r'病情摘要及初步印象：\s*(.*?)\n', dialog)
            if not diagnosis:
                diagnosis = re.search(r'Diagnosis and suggestions\n病情摘要及初步印象：\s*(.*?)\n', dialog)
            diagnosis = diagnosis.group(1).strip() if diagnosis else ""

            # 提取医生建议
            suggestions = re.search(r'总结建议：\s*(.*?)\n', dialog)
            if not suggestions:
                suggestions = re.search(r'Diagnosis and suggestions\n总结建议：\s*(.*?)\n', dialog)
            suggestions = suggestions.group(1).strip() if suggestions else ""

            # 添加到对话列表
            self.all_dialogues.append({
                'id': dialog_id,
                'doctor_faculty': doctor_faculty,
                'disease': disease,
                'description': description,
                'help_required': help_required,
                'medical_history': medical_history,
                'diagnosis': diagnosis,
                'suggestions': suggestions
            })

    def clean_data(self):
        """清洗数据：去除重复、处理缺失值等"""
        df = pd.DataFrame(self.all_dialogues)

        # 去除重复记录
        initial_count = len(df)
        df = df.drop_duplicates()
        print(f"去除重复记录: {initial_count} -> {len(df)}")

        # 处理缺失值
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            if missing_count > 0:
                print(f"{col} 缺失值数量: {missing_count}")
                df[col] = df[col].fillna("")

        # 过滤无效记录（如果所有关键字段都为空）
        key_columns = ['disease', 'description', 'diagnosis']
        df['is_valid'] = df[key_columns].apply(lambda x: any(x), axis=1)
        df = df[df['is_valid']]
        df = df.drop('is_valid', axis=1)
        print(f"过滤无效记录后: {len(df)}")

        self.df = df

    def text_enhancement(self):
        """文本增强：分词、实体识别等"""
        # 中文分词处理
        print("进行中文分词处理...")
        for col in ['description', 'diagnosis', 'suggestions']:
            self.df[f'{col}_tokens'] = self.df[col].apply(
                lambda x: ' '.join(jieba.cut(x)) if x else ""
            )

        # 这里可以添加更多文本增强操作，如实体识别、情感分析等

    def save_results(self):
        """保存处理后的结果"""
        self.df.to_csv(self.output_file, index=False, encoding='utf-8')
        print(f"处理结果已保存至: {self.output_file}")

    def visualize_data(self):
        """可视化数据分布"""
        # 科室分布
        plt.figure(figsize=(12, 6))
        top_faculties = self.df['doctor_faculty'].value_counts().head(10)
        top_faculties.plot(kind='bar')
        plt.title('Top 10 医生科室分布')
        plt.xlabel('科室')
        plt.ylabel('数量')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(os.path.dirname(self.data_dir), "faculty_distribution.png"))
        print("科室分布图表已保存")

        # 疾病分布
        plt.figure(figsize=(12, 6))
        top_diseases = self.df['disease'].value_counts().head(10)
        top_diseases.plot(kind='bar')
        plt.title('Top 10 疾病分布')
        plt.xlabel('疾病')
        plt.ylabel('数量')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(os.path.dirname(self.data_dir), "disease_distribution.png"))
        print("疾病分布图表已保存")

    def run(self):
        """运行预处理流程"""
        print("开始医疗对话文本数据预处理...")
        self.load_data()
        self.clean_data()
        self.text_enhancement()
        self.save_results()
        self.visualize_data()
        print("文本数据预处理完成!")

if __name__ == "__main__":
    # 设置数据目录
    print(11111111)
    print(os.path.abspath(__file__))
    print(os.path.dirname)

    # 修改为加载 datas/medical_knowledge/2010.txt
    # 直接使用绝对路径
    data_dir = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge"
    print(data_dir)
    print(22222222)
    # 创建预处理实例并运行
    preprocessor = MedicalTextPreprocessor(data_dir)
    preprocessor.run()