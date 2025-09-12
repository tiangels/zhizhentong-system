import os
import re
import pandas as pd
import jieba
import json
from tqdm import tqdm
import numpy as np

# 设置中文字体显示
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]

class OptimizedMedicalTextPreprocessor:
    def __init__(self, raw_data_dir, output_dir):
        self.raw_data_dir = raw_data_dir
        self.output_dir = output_dir
        self.dialogue_data = []
        self.vqa_data = []
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "test_data"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "training_data"), exist_ok=True)

    def load_dialogue_data(self, sample_size=10):
        """加载中文医疗对话数据，只取前sample_size条进行测试"""
        dialogue_dir = os.path.join(self.raw_data_dir, "dialogue", "Medical-Dialogue-Dataset-Chinese")
        
        if not os.path.exists(dialogue_dir):
            print(f"对话数据目录不存在: {dialogue_dir}")
            return
            
        print(f"加载对话数据，限制样本数量: {sample_size}")
        
        for filename in os.listdir(dialogue_dir):
            if filename.endswith(".txt") and filename[:4].isdigit():
                file_path = os.path.join(dialogue_dir, filename)
                print(f"处理文件: {filename}")
                
                # 尝试不同的编码方式
                content = None
                for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        print(f"成功使用 {encoding} 编码读取文件")
                        break
                    except UnicodeDecodeError:
                        continue
                
                if content is None:
                    print(f"无法读取文件 {filename}，跳过")
                    continue
                
                dialogues = self.parse_dialogues(content, sample_size)
                self.dialogue_data.extend(dialogues)
                    
                # 如果已经达到样本数量限制，停止处理
                if len(self.dialogue_data) >= sample_size:
                    break
                    
        # 限制到指定数量
        self.dialogue_data = self.dialogue_data[:sample_size]
        print(f"共加载 {len(self.dialogue_data)} 条对话数据")

    def parse_dialogues(self, content, max_count):
        """解析对话内容，提取结构化信息"""
        dialogues = []
        
        # 分割不同的对话记录
        dialog_sections = re.split(r'id=\d+', content)
        
        for i, dialog in enumerate(dialog_sections[1:], 1):  # 跳过第一个空字符串
            if len(dialogues) >= max_count:
                break
                
            # 提取对话ID
            dialog_id_match = re.search(r'id=(\d+)', dialog)
            dialog_id = dialog_id_match.group(1) if dialog_id_match else f"unknown_{i}"

            # 提取医生科室
            doctor_faculty = self.extract_field(dialog, r'Doctor faculty\n(.*?)\n')

            # 提取疾病信息 - 修改正则表达式
            disease = self.extract_field(dialog, r'疾病：\s*(.*?)\n')
            if not disease:
                # 尝试其他可能的格式
                disease = self.extract_field(dialog, r'Description\n疾病：\s*(.*?)\n')

            # 提取病情描述 - 修改正则表达式
            description = self.extract_field(dialog, r'内容：病情描述.*?：\s*(.*?)\n', re.DOTALL)
            if not description:
                description = self.extract_field(dialog, r'Description\n.*?病情描述.*?：\s*(.*?)\n', re.DOTALL)

            # 提取希望获得的帮助
            help_required = self.extract_field(dialog, r'想得到怎样的帮助.*?：\s*(.*?)\n', re.DOTALL)
            if not help_required:
                help_required = self.extract_field(dialog, r'想得到怎样的帮助.*?：\s*(.*?)\n', re.DOTALL)

            # 提取既往病史
            medical_history = self.extract_field(dialog, r'曾经治疗情况和效果.*?：\s*(.*?)\n', re.DOTALL)

            # 提取诊断结果
            diagnosis = self.extract_field(dialog, r'病情摘要及初步印象.*?：\s*(.*?)\n', re.DOTALL)
            if not diagnosis:
                diagnosis = self.extract_field(dialog, r'Diagnosis and suggestions\n病情摘要及初步印象.*?：\s*(.*?)\n', re.DOTALL)

            # 提取医生建议
            suggestions = self.extract_field(dialog, r'总结建议.*?：\s*(.*?)\n', re.DOTALL)
            if not suggestions:
                suggestions = self.extract_field(dialog, r'Diagnosis and suggestions\n总结建议.*?：\s*(.*?)\n', re.DOTALL)

            # 提取对话内容
            dialogue_content = self.extract_dialogue_content(dialog)

            # 添加到对话列表
            dialogues.append({
                'id': dialog_id,
                'doctor_faculty': doctor_faculty,
                'disease': disease,
                'description': description,
                'help_required': help_required,
                'medical_history': medical_history,
                'diagnosis': diagnosis,
                'suggestions': suggestions,
                'dialogue_content': dialogue_content
            })

        return dialogues

    def extract_field(self, text, pattern, flags=0):
        """提取字段内容的辅助函数"""
        match = re.search(pattern, text, flags)
        if match:
            result = match.group(1).strip()
            # 清理文本，移除多余的空白字符
            result = re.sub(r'\s+', ' ', result)
            return result
        return ""

    def extract_dialogue_content(self, dialog):
        """提取对话内容"""
        # 查找对话部分
        dialogue_match = re.search(r'Dialogue\n(.*?)(?=\nid=|\Z)', dialog, re.DOTALL)
        if dialogue_match:
            dialogue_text = dialogue_match.group(1).strip()
            # 清理对话内容，分离患者和医生的对话
            lines = dialogue_text.split('\n')
            cleaned_dialogue = []
            for line in lines:
                line = line.strip()
                if line and ('病人：' in line or '医生：' in line):
                    cleaned_dialogue.append(line)
            return '\n'.join(cleaned_dialogue)
        return ""

    def load_vqa_data(self, sample_size=10):
        """加载VQA数据，只取前sample_size条进行测试"""
        vqa_dir = os.path.join(self.raw_data_dir, "vqa", "VQA_data")
        
        if not os.path.exists(vqa_dir):
            print(f"VQA数据目录不存在: {vqa_dir}")
            return
            
        print(f"加载VQA数据，限制样本数量: {sample_size}")
        
        # 这里可以根据实际的VQA数据格式进行加载
        # 暂时创建一个示例结构
        for i in range(min(sample_size, 10)):
            self.vqa_data.append({
                'id': f"vqa_{i}",
                'question': f"示例问题 {i}",
                'answer': f"示例答案 {i}",
                'image_path': f"image_{i}.jpg"
            })

    def clean_and_enhance_data(self):
        """清洗和增强数据"""
        print("清洗和增强数据...")
        
        # 处理对话数据
        if self.dialogue_data:
            dialogue_df = pd.DataFrame(self.dialogue_data)
            
            # 去除重复记录
            initial_count = len(dialogue_df)
            dialogue_df = dialogue_df.drop_duplicates()
            print(f"对话数据去重: {initial_count} -> {len(dialogue_df)}")

            # 处理缺失值
            for col in dialogue_df.columns:
                dialogue_df[col] = dialogue_df[col].fillna("")

            # 中文分词处理
            print("进行中文分词处理...")
            text_columns = ['description', 'diagnosis', 'suggestions', 'dialogue_content']
            for col in text_columns:
                if col in dialogue_df.columns:
                    dialogue_df[f'{col}_tokens'] = dialogue_df[col].apply(
                        lambda x: ' '.join(jieba.cut(x)) if x and x.strip() else ""
                    )

            self.dialogue_df = dialogue_df

        # 处理VQA数据
        if self.vqa_data:
            vqa_df = pd.DataFrame(self.vqa_data)
            
            # 处理缺失值
            for col in vqa_df.columns:
                vqa_df[col] = vqa_df[col].fillna("")

            self.vqa_df = vqa_df

    def save_data(self):
        """保存处理后的数据，确保CSV文件格式正确"""
        print("保存处理后的数据...")
        
        # 保存对话数据
        if hasattr(self, 'dialogue_df'):
            # 分割训练集和测试集 (80% 训练, 20% 测试)
            total_dialogue = len(self.dialogue_df)
            train_size = int(total_dialogue * 0.8)
            
            train_dialogue = self.dialogue_df[:train_size]
            test_dialogue = self.dialogue_df[train_size:]
            
            # 保存到指定目录
            train_path = os.path.join(self.output_dir, "training_data", "dialogue_train.csv")
            test_path = os.path.join(self.output_dir, "test_data", "dialogue_test.csv")
            
            # 确保没有多余的逗号 - 使用index=False避免行号
            train_dialogue.to_csv(train_path, index=False, encoding='utf-8')
            test_dialogue.to_csv(test_path, index=False, encoding='utf-8')
            
            print(f"对话数据已保存:")
            print(f"  训练集: {train_path} ({len(train_dialogue)} 条)")
            print(f"  测试集: {test_path} ({len(test_dialogue)} 条)")

        # 保存VQA数据
        if hasattr(self, 'vqa_df'):
            total_vqa = len(self.vqa_df)
            train_size = int(total_vqa * 0.8)
            
            train_vqa = self.vqa_df[:train_size]
            test_vqa = self.vqa_df[train_size:]
            
            train_path = os.path.join(self.output_dir, "training_data", "vqa_train.csv")
            test_path = os.path.join(self.output_dir, "test_data", "vqa_test.csv")
            
            train_vqa.to_csv(train_path, index=False, encoding='utf-8')
            test_vqa.to_csv(test_path, index=False, encoding='utf-8')
            
            print(f"VQA数据已保存:")
            print(f"  训练集: {train_path} ({len(train_vqa)} 条)")
            print(f"  测试集: {test_path} ({len(test_vqa)} 条)")

    def create_data_summary(self):
        """创建数据摘要"""
        summary = {
            "dialogue_data": {
                "total_count": len(self.dialogue_data) if self.dialogue_data else 0,
                "columns": list(self.dialogue_df.columns) if hasattr(self, 'dialogue_df') else []
            },
            "vqa_data": {
                "total_count": len(self.vqa_data) if self.vqa_data else 0,
                "columns": list(self.vqa_df.columns) if hasattr(self, 'vqa_df') else []
            }
        }
        
        summary_path = os.path.join(self.output_dir, "data_summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"数据摘要已保存: {summary_path}")

    def run(self, sample_size=10):
        """运行预处理流程"""
        print("开始优化的医疗文本数据预处理...")
        print(f"样本数量限制: {sample_size}")
        
        # 加载数据
        self.load_dialogue_data(sample_size)
        self.load_vqa_data(sample_size)
        
        # 清洗和增强
        self.clean_and_enhance_data()
        
        # 保存数据
        self.save_data()
        
        # 创建摘要
        self.create_data_summary()
        
        print("文本数据预处理完成!")
    
    def process_texts(self, texts):
        """
        处理文本列表，返回向量化结果
        
        Args:
            texts: 文本列表
            
        Returns:
            处理后的文本向量数组
        """
        import numpy as np
        from sentence_transformers import SentenceTransformer
        
        # 初始化模型
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # 处理文本
        processed_texts = []
        for text in texts:
            # 简单的文本清洗
            cleaned_text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', str(text))
            processed_texts.append(cleaned_text)
        
        # 生成向量
        vectors = model.encode(processed_texts)
        
        return vectors

if __name__ == "__main__":
    # 设置路径
    raw_data_dir = "raw_datas"
    output_dir = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge"
    
    # 创建预处理实例并运行
    preprocessor = OptimizedMedicalTextPreprocessor(raw_data_dir, output_dir)
    preprocessor.run(sample_size=10)  # 只处理10条数据用于测试
