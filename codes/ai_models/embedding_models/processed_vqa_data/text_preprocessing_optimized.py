import os
import re
import pandas as pd
import jieba
from tqdm import tqdm
import gc

# 设置中文字体显示
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]

class MedicalTextPreprocessor:
    def __init__(self, data_file):
        self.data_file = data_file
        self.output_file = os.path.join(os.path.dirname(data_file), "processed_medical_dialogues_optimized.csv")
        self.all_dialogues = []

    def load_data(self):
        """加载医疗对话数据"""
        print(f"加载文件: {self.data_file}")
        with open(self.data_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.parse_dialogues(content)
        print(f"共加载 {len(self.all_dialogues)} 条对话数据")

    def parse_dialogues(self, content):
        """解析对话内容，提取结构化信息"""
        # 按 id= 分割不同的对话记录
        dialogues = re.split(r'\nid=', content)
        
        for i, dialog in enumerate(tqdm(dialogues, desc="解析对话")):
            if i == 0:
                # 第一个记录没有 id= 前缀，需要特殊处理
                if not dialog.strip():
                    continue
                dialog_id = "0"
            else:
                # 提取对话ID
                id_match = re.match(r'(\d+)', dialog)
                dialog_id = id_match.group(1) if id_match else str(i)

            # 提取医生科室
            doctor_faculty = self.extract_field(dialog, r'Doctor faculty\n(.*?)\n')
            
            # 提取疾病信息
            disease = self.extract_field(dialog, r'疾病：\s*(.*?)\s*内容：')
            
            # 提取病情描述
            description = self.extract_field(dialog, r'Description\n(.*?)\n\nDialogue', re.DOTALL)
            if not description:
                # 如果没有Description字段，尝试从其他位置提取
                description = self.extract_field(dialog, r'病情描述.*?：\s*(.*?)\n', re.DOTALL)
            
            # 提取对话内容
            dialogue_content = self.extract_field(dialog, r'Dialogue\n(.*?)(?=\nid=|\Z)', re.DOTALL)
            
            # 解析对话中的问答对
            qa_pairs = self.parse_qa_pairs(dialogue_content)
            
            # 提取其他字段
            help_required = self.extract_field(dialog, r'希望获得的帮助.*?：\s*(.*?)\n', re.DOTALL)
            medical_history = self.extract_field(dialog, r'既往病史.*?：\s*(.*?)\n', re.DOTALL)
            diagnosis = self.extract_field(dialog, r'病情摘要及初步印象.*?：\s*(.*?)\n', re.DOTALL)
            suggestions = self.extract_field(dialog, r'总结建议.*?：\s*(.*?)\n', re.DOTALL)

            # 添加到对话列表
            self.all_dialogues.append({
                'id': dialog_id,
                'doctor_faculty': doctor_faculty,
                'disease': disease,
                'description': description,
                'dialogue_content': dialogue_content,
                'qa_pairs': qa_pairs,
                'help_required': help_required,
                'medical_history': medical_history,
                'diagnosis': diagnosis,
                'suggestions': suggestions
            })

    def extract_field(self, text, pattern, flags=0):
        """提取字段内容"""
        match = re.search(pattern, text, flags)
        if match:
            result = match.group(1).strip()
            # 清理多余的空白字符
            result = re.sub(r'\s+', ' ', result)
            return result
        return ""

    def parse_qa_pairs(self, dialogue_content):
        """解析对话中的问答对"""
        if not dialogue_content:
            return []
        
        qa_pairs = []
        # 按"病人："和"医生："分割对话
        parts = re.split(r'(病人：|医生：)', dialogue_content)
        
        current_speaker = None
        current_content = ""
        
        for part in parts:
            if part == "病人：" or part == "医生：":
                if current_speaker and current_content.strip():
                    qa_pairs.append({
                        'speaker': current_speaker,
                        'content': current_content.strip()
                    })
                current_speaker = "患者" if part == "病人：" else "医生"
                current_content = ""
            else:
                current_content += part
        
        # 添加最后一个对话
        if current_speaker and current_content.strip():
            qa_pairs.append({
                'speaker': current_speaker,
                'content': current_content.strip()
            })
        
        return qa_pairs

    def clean_data(self):
        """清洗数据：去除重复、处理缺失值等"""
        df = pd.DataFrame(self.all_dialogues)

        # 去除重复记录
        initial_count = len(df)
        df = df.drop_duplicates(subset=['id'])
        print(f"去除重复记录: {initial_count} -> {len(df)}")

        # 处理缺失值
        for col in df.columns:
            if col != 'qa_pairs':  # qa_pairs是列表，不需要fillna
                missing_count = df[col].isnull().sum()
                if missing_count > 0:
                    print(f"{col} 缺失值数量: {missing_count}")
                    df[col] = df[col].fillna("")

        # 过滤无效记录（如果所有关键字段都为空）
        key_columns = ['disease', 'description', 'dialogue_content']
        df['is_valid'] = df[key_columns].apply(lambda x: any(str(val).strip() for val in x), axis=1)
        df = df[df['is_valid']]
        df = df.drop('is_valid', axis=1)
        print(f"过滤无效记录后: {len(df)}")

        self.df = df

    def text_enhancement(self):
        """文本增强：分词、实体识别等（优化版本）"""
        print("进行中文分词处理（优化版本）...")
        
        # 只对主要字段进行分词，减少处理量
        text_columns = ['description', 'dialogue_content']
        
        for col in text_columns:
            if col in self.df.columns:
                print(f"正在处理 {col} 字段...")
                # 分批处理，避免内存问题
                batch_size = 10000
                total_rows = len(self.df)
                
                tokens_list = []
                for i in tqdm(range(0, total_rows, batch_size), desc=f"分词处理 {col}"):
                    batch = self.df[col].iloc[i:i+batch_size]
                    batch_tokens = batch.apply(
                        lambda x: ' '.join(jieba.cut(str(x))) if x and str(x).strip() else ""
                    )
                    tokens_list.extend(batch_tokens.tolist())
                    
                    # 强制垃圾回收
                    gc.collect()
                
                self.df[f'{col}_tokens'] = tokens_list
                print(f"{col} 字段分词完成")

    def save_results(self):
        """保存处理后的结果"""
        print("保存处理结果...")
        # 将qa_pairs转换为字符串以便保存到CSV
        df_to_save = self.df.copy()
        df_to_save['qa_pairs'] = df_to_save['qa_pairs'].apply(
            lambda x: ' | '.join([f"{pair['speaker']}: {pair['content']}" for pair in x]) if x else ""
        )
        
        df_to_save.to_csv(self.output_file, index=False, encoding='utf-8')
        print(f"处理结果已保存至: {self.output_file}")

    def analyze_qa_pairs(self):
        """分析问答对统计信息"""
        print("分析问答对统计信息...")
        total_qa_pairs = 0
        patient_questions = 0
        doctor_answers = 0
        
        for qa_list in tqdm(self.df['qa_pairs'], desc="分析问答对"):
            if qa_list:
                total_qa_pairs += len(qa_list)
                for qa in qa_list:
                    if qa['speaker'] == '患者':
                        patient_questions += 1
                    elif qa['speaker'] == '医生':
                        doctor_answers += 1
        
        print(f"\n=== 对话分析统计 ===")
        print(f"总问答对数量: {total_qa_pairs}")
        print(f"患者问题数量: {patient_questions}")
        print(f"医生回答数量: {doctor_answers}")
        print(f"平均每个对话的问答对数: {total_qa_pairs / len(self.df):.2f}")

    def run(self):
        """运行预处理流程"""
        print("开始医疗对话文本数据预处理（优化版）...")
        self.load_data()
        self.clean_data()
        self.text_enhancement()
        self.analyze_qa_pairs()
        self.save_results()
        print("文本数据预处理完成!")

if __name__ == "__main__":
    # 设置数据文件路径
    data_file = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/2010.txt"
    
    # 创建预处理实例并运行
    preprocessor = MedicalTextPreprocessor(data_file)
    preprocessor.run()
