import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import jieba
import json

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False

class MedicalDataAnalyzer:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.dialogue_data = None
        self.vqa_data = None
        
    def load_data(self):
        """加载所有数据文件"""
        print("加载数据文件...")
        
        # 加载对话数据
        dialogue_train_path = os.path.join(self.data_dir, "training_data", "dialogue_train.csv")
        dialogue_test_path = os.path.join(self.data_dir, "test_data", "dialogue_test.csv")
        
        if os.path.exists(dialogue_train_path):
            self.dialogue_train = pd.read_csv(dialogue_train_path)
            print(f"对话训练数据: {len(self.dialogue_train)} 条")
        else:
            print("对话训练数据文件不存在")
            
        if os.path.exists(dialogue_test_path):
            self.dialogue_test = pd.read_csv(dialogue_test_path)
            print(f"对话测试数据: {len(self.dialogue_test)} 条")
        else:
            print("对话测试数据文件不存在")
            
        # 加载VQA数据
        vqa_train_path = os.path.join(self.data_dir, "training_data", "vqa_train.csv")
        vqa_test_path = os.path.join(self.data_dir, "test_data", "vqa_test.csv")
        
        if os.path.exists(vqa_train_path):
            self.vqa_train = pd.read_csv(vqa_train_path)
            print(f"VQA训练数据: {len(self.vqa_train)} 条")
        else:
            print("VQA训练数据文件不存在")
            
        if os.path.exists(vqa_test_path):
            self.vqa_test = pd.read_csv(vqa_test_path)
            print(f"VQA测试数据: {len(self.vqa_test)} 条")
        else:
            print("VQA测试数据文件不存在")

    def analyze_dialogue_data(self):
        """分析对话数据"""
        if not hasattr(self, 'dialogue_train'):
            print("没有对话数据可分析")
            return
            
        print("\n=== 对话数据分析 ===")
        
        # 基本统计信息
        print(f"训练集大小: {len(self.dialogue_train)}")
        if hasattr(self, 'dialogue_test'):
            print(f"测试集大小: {len(self.dialogue_test)}")
        
        # 科室分布
        if 'doctor_faculty' in self.dialogue_train.columns:
            faculty_counts = self.dialogue_train['doctor_faculty'].value_counts()
            print(f"\n科室分布 (前10):")
            print(faculty_counts.head(10))
            
            # 可视化科室分布
            plt.figure(figsize=(12, 6))
            faculty_counts.head(10).plot(kind='bar')
            plt.title('医生科室分布 (前10)')
            plt.xlabel('科室')
            plt.ylabel('数量')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(self.data_dir, 'faculty_distribution.png'))
            plt.close()
            print("科室分布图已保存")
        
        # 疾病分布
        if 'disease' in self.dialogue_train.columns:
            disease_counts = self.dialogue_train['disease'].value_counts()
            print(f"\n疾病分布 (前10):")
            print(disease_counts.head(10))
            
            # 可视化疾病分布
            plt.figure(figsize=(12, 6))
            disease_counts.head(10).plot(kind='bar')
            plt.title('疾病分布 (前10)')
            plt.xlabel('疾病')
            plt.ylabel('数量')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(self.data_dir, 'disease_distribution.png'))
            plt.close()
            print("疾病分布图已保存")
        
        # 文本长度分析 - 修复错误
        text_columns = ['description', 'diagnosis', 'suggestions', 'dialogue_content']
        for col in text_columns:
            if col in self.dialogue_train.columns:
                # 确保列是字符串类型
                if self.dialogue_train[col].dtype == 'object':
                    # 过滤掉空值并转换为字符串
                    non_null_data = self.dialogue_train[col].dropna().astype(str)
                    if len(non_null_data) > 0:
                        lengths = non_null_data.str.len()
                        print(f"\n{col} 文本长度统计:")
                        print(f"  平均长度: {lengths.mean():.2f}")
                        print(f"  中位数长度: {lengths.median():.2f}")
                        print(f"  最大长度: {lengths.max()}")
                        print(f"  最小长度: {lengths.min()}")
                    else:
                        print(f"\n{col}: 没有有效数据")
                else:
                    print(f"\n{col}: 数据类型不是字符串，跳过长度分析")

    def analyze_vqa_data(self):
        """分析VQA数据"""
        if not hasattr(self, 'vqa_train'):
            print("没有VQA数据可分析")
            return
            
        print("\n=== VQA数据分析 ===")
        
        # 基本统计信息
        print(f"训练集大小: {len(self.vqa_train)}")
        if hasattr(self, 'vqa_test'):
            print(f"测试集大小: {len(self.vqa_test)}")
        
        # 问题长度分析
        if 'question' in self.vqa_train.columns:
            question_lengths = self.vqa_train['question'].str.len()
            print(f"\n问题长度统计:")
            print(f"  平均长度: {question_lengths.mean():.2f}")
            print(f"  中位数长度: {question_lengths.median():.2f}")
            print(f"  最大长度: {question_lengths.max()}")
            print(f"  最小长度: {question_lengths.min()}")
        
        # 答案长度分析
        if 'answer' in self.vqa_train.columns:
            answer_lengths = self.vqa_train['answer'].str.len()
            print(f"\n答案长度统计:")
            print(f"  平均长度: {answer_lengths.mean():.2f}")
            print(f"  中位数长度: {answer_lengths.median():.2f}")
            print(f"  最大长度: {answer_lengths.max()}")
            print(f"  最小长度: {answer_lengths.min()}")

    def analyze_text_quality(self):
        """分析文本质量"""
        print("\n=== 文本质量分析 ===")
        
        if hasattr(self, 'dialogue_train'):
            # 检查缺失值
            print("对话数据缺失值统计:")
            missing_data = self.dialogue_train.isnull().sum()
            for col, missing_count in missing_data.items():
                if missing_count > 0:
                    print(f"  {col}: {missing_count} ({missing_count/len(self.dialogue_train)*100:.2f}%)")
            
            # 检查空字符串
            print("\n空字符串统计:")
            for col in self.dialogue_train.columns:
                if self.dialogue_train[col].dtype == 'object':
                    empty_count = (self.dialogue_train[col] == '').sum()
                    if empty_count > 0:
                        print(f"  {col}: {empty_count} ({empty_count/len(self.dialogue_train)*100:.2f}%)")

    def generate_word_cloud(self):
        """生成词云"""
        try:
            from wordcloud import WordCloud
            print("\n=== 生成词云 ===")
            
            if hasattr(self, 'dialogue_train') and 'dialogue_content' in self.dialogue_train.columns:
                # 合并所有对话内容
                all_text = ' '.join(self.dialogue_train['dialogue_content'].dropna().astype(str))
                
                if all_text.strip():
                    # 中文分词
                    words = jieba.cut(all_text)
                    word_list = ' '.join(words)
                    
                    # 生成词云
                    wordcloud = WordCloud(
                        font_path='simhei.ttf',  # 需要中文字体文件
                        width=800,
                        height=400,
                        background_color='white',
                        max_words=100
                    ).generate(word_list)
                    
                    plt.figure(figsize=(10, 5))
                    plt.imshow(wordcloud, interpolation='bilinear')
                    plt.axis('off')
                    plt.title('对话内容词云')
                    plt.tight_layout()
                    plt.savefig(os.path.join(self.data_dir, 'wordcloud.png'))
                    plt.close()
                    print("词云图已保存")
                else:
                    print("没有足够的对话内容生成词云")
        except ImportError:
            print("需要安装wordcloud库来生成词云: pip install wordcloud")

    def create_summary_report(self):
        """创建分析摘要报告"""
        report = {
            "data_overview": {
                "dialogue_train_size": len(self.dialogue_train) if hasattr(self, 'dialogue_train') else 0,
                "dialogue_test_size": len(self.dialogue_test) if hasattr(self, 'dialogue_test') else 0,
                "vqa_train_size": len(self.vqa_train) if hasattr(self, 'vqa_train') else 0,
                "vqa_test_size": len(self.vqa_test) if hasattr(self, 'vqa_test') else 0
            },
            "analysis_timestamp": pd.Timestamp.now().isoformat()
        }
        
        # 保存报告
        report_path = os.path.join(self.data_dir, 'analysis_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n分析报告已保存: {report_path}")

    def run_analysis(self):
        """运行完整的数据分析"""
        print("开始医疗数据分析...")
        
        # 加载数据
        self.load_data()
        
        # 分析对话数据
        self.analyze_dialogue_data()
        
        # 分析VQA数据
        self.analyze_vqa_data()
        
        # 分析文本质量
        self.analyze_text_quality()
        
        # 生成词云
        self.generate_word_cloud()
        
        # 创建摘要报告
        self.create_summary_report()
        
        print("\n数据分析完成!")

if __name__ == "__main__":
    # 设置数据目录
    data_dir = "medical_knowledge"
    
    # 创建分析器并运行
    analyzer = MedicalDataAnalyzer(data_dir)
    analyzer.run_analysis()
