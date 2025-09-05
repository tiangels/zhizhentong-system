import pandas as pd
import os
import argparse

class MedicalDataAnalyzer:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.df = None
        
    def load_data(self):
        """加载数据"""
        print(f"正在加载数据: {self.csv_file}")
        try:
            self.df = pd.read_csv(self.csv_file, encoding='utf-8', low_memory=False)
            print(f"数据加载成功！形状: {self.df.shape}")
            return True
        except Exception as e:
            print(f"加载数据失败: {e}")
            return False
    
    def show_basic_info(self):
        """显示基本信息"""
        if self.df is None:
            print("请先加载数据")
            return
            
        print("\n=== 数据基本信息 ===")
        print(f"总行数: {len(self.df):,}")
        print(f"总列数: {len(self.df.columns)}")
        print(f"内存使用: {self.df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        
        print(f"\n列名:")
        for i, col in enumerate(self.df.columns, 1):
            print(f"  {i:2d}. {col}")
    
    def show_sample_data(self, n_rows=5, columns=None):
        """显示样本数据"""
        if self.df is None:
            print("请先加载数据")
            return
            
        print(f"\n=== 前 {n_rows} 行数据 ===")
        
        if columns:
            # 只显示指定列
            available_cols = [col for col in columns if col in self.df.columns]
            if not available_cols:
                print(f"指定的列 {columns} 不存在")
                return
            display_df = self.df[available_cols].head(n_rows)
        else:
            display_df = self.df.head(n_rows)
        
        for i in range(len(display_df)):
            print(f"\n--- 第 {i+1} 行 ---")
            row = display_df.iloc[i]
            for col in display_df.columns:
                value = str(row[col])
                if len(value) > 150:
                    value = value[:150] + "..."
                print(f"{col}: {value}")
    
    def analyze_columns(self):
        """分析各列的数据质量"""
        if self.df is None:
            print("请先加载数据")
            return
            
        print("\n=== 列数据质量分析 ===")
        
        analysis_data = []
        for col in self.df.columns:
            col_data = self.df[col]
            analysis_data.append({
                '列名': col,
                '数据类型': str(col_data.dtype),
                '非空值数量': col_data.notna().sum(),
                '缺失值数量': col_data.isna().sum(),
                '缺失值比例': f"{col_data.isna().sum() / len(col_data) * 100:.2f}%",
                '唯一值数量': col_data.nunique(),
                '重复值数量': len(col_data) - col_data.nunique()
            })
        
        analysis_df = pd.DataFrame(analysis_data)
        print(analysis_df.to_string(index=False))
    
    def analyze_dialogues(self):
        """分析对话数据"""
        if self.df is None:
            print("请先加载数据")
            return
            
        print("\n=== 对话数据分析 ===")
        
        # 对话长度分析
        if 'dialogue_content' in self.df.columns:
            dialogue_lengths = self.df['dialogue_content'].str.len()
            print(f"对话内容长度统计:")
            print(f"  平均长度: {dialogue_lengths.mean():.2f} 字符")
            print(f"  中位数长度: {dialogue_lengths.median():.2f} 字符")
            print(f"  最短长度: {dialogue_lengths.min()} 字符")
            print(f"  最长长度: {dialogue_lengths.max()} 字符")
            print(f"  标准差: {dialogue_lengths.std():.2f}")
        
        # 问答对分析
        if 'qa_pairs' in self.df.columns:
            qa_counts = self.df['qa_pairs'].apply(
                lambda x: len(str(x).split(' | ')) if pd.notna(x) and str(x).strip() else 0
            )
            print(f"\n问答对统计:")
            print(f"  平均问答对数: {qa_counts.mean():.2f}")
            print(f"  中位数问答对数: {qa_counts.median():.2f}")
            print(f"  最多问答对数: {qa_counts.max()}")
            print(f"  最少问答对数: {qa_counts.min()}")
            print(f"  标准差: {qa_counts.std():.2f}")
            
            # 问答对分布
            print(f"\n问答对数量分布:")
            qa_distribution = qa_counts.value_counts().sort_index()
            for count, freq in qa_distribution.head(10).items():
                print(f"  {count} 个问答对: {freq:,} 条记录")
    
    def analyze_medical_info(self):
        """分析医疗信息"""
        if self.df is None:
            print("请先加载数据")
            return
            
        print("\n=== 医疗信息分析 ===")
        
        # 科室分析
        if 'doctor_faculty' in self.df.columns:
            print(f"医生科室统计:")
            print(f"  总科室数: {self.df['doctor_faculty'].nunique()}")
            print(f"  最常见的10个科室:")
            top_faculties = self.df['doctor_faculty'].value_counts().head(10)
            for faculty, count in top_faculties.items():
                print(f"    {faculty}: {count:,}")
        
        # 疾病分析
        if 'disease' in self.df.columns:
            print(f"\n疾病统计:")
            print(f"  总疾病数: {self.df['disease'].nunique()}")
            print(f"  最常见的10种疾病:")
            top_diseases = self.df['disease'].value_counts().head(10)
            for disease, count in top_diseases.items():
                print(f"    {disease}: {count:,}")
    
    def search_data(self, keyword, column=None, limit=10):
        """搜索包含关键词的数据"""
        if self.df is None:
            print("请先加载数据")
            return
            
        print(f"\n=== 搜索关键词: '{keyword}' ===")
        
        if column and column in self.df.columns:
            # 在指定列中搜索
            mask = self.df[column].str.contains(keyword, case=False, na=False)
            results = self.df[mask].head(limit)
            print(f"在列 '{column}' 中找到 {mask.sum()} 条匹配记录，显示前 {len(results)} 条:")
        else:
            # 在所有文本列中搜索
            text_columns = self.df.select_dtypes(include=['object']).columns
            mask = pd.Series([False] * len(self.df))
            for col in text_columns:
                mask |= self.df[col].str.contains(keyword, case=False, na=False)
            results = self.df[mask].head(limit)
            print(f"在所有文本列中找到 {mask.sum()} 条匹配记录，显示前 {len(results)} 条:")
        
        for i, (idx, row) in enumerate(results.iterrows(), 1):
            print(f"\n--- 匹配记录 {i} (ID: {row.get('id', 'N/A')}) ---")
            for col in ['id', 'doctor_faculty', 'disease', 'description', 'dialogue_content']:
                if col in row:
                    value = str(row[col])
                    if len(value) > 200:
                        value = value[:200] + "..."
                    print(f"{col}: {value}")
    
    def export_sample(self, n_rows=100, output_file=None):
        """导出样本数据"""
        if self.df is None:
            print("请先加载数据")
            return
            
        if output_file is None:
            output_file = f"sample_data_{n_rows}_rows.csv"
        
        sample_df = self.df.head(n_rows)
        sample_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"已导出 {n_rows} 行样本数据到: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='医疗对话数据分析工具')
    parser.add_argument('--file', '-f', required=True, help='CSV文件路径')
    parser.add_argument('--rows', '-r', type=int, default=5, help='显示的行数')
    parser.add_argument('--columns', '-c', nargs='+', help='要显示的列名')
    parser.add_argument('--search', '-s', help='搜索关键词')
    parser.add_argument('--search-column', help='搜索的列名')
    parser.add_argument('--export', '-e', type=int, help='导出样本数据行数')
    parser.add_argument('--export-file', help='导出文件名')
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not os.path.exists(args.file):
        print(f"文件不存在: {args.file}")
        return
    
    # 创建分析器
    analyzer = MedicalDataAnalyzer(args.file)
    
    # 加载数据
    if not analyzer.load_data():
        return
    
    # 显示基本信息
    analyzer.show_basic_info()
    
    # 显示样本数据
    analyzer.show_sample_data(args.rows, args.columns)
    
    # 分析列数据质量
    analyzer.analyze_columns()
    
    # 分析对话数据
    analyzer.analyze_dialogues()
    
    # 分析医疗信息
    analyzer.analyze_medical_info()
    
    # 搜索功能
    if args.search:
        analyzer.search_data(args.search, args.search_column)
    
    # 导出样本数据
    if args.export:
        analyzer.export_sample(args.export, args.export_file)

if __name__ == "__main__":
    # 如果没有命令行参数，使用默认设置
    import sys
    if len(sys.argv) == 1:
        # 默认分析
        csv_file = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/processed_medical_dialogues_optimized.csv"
        analyzer = MedicalDataAnalyzer(csv_file)
        if analyzer.load_data():
            analyzer.show_basic_info()
            analyzer.show_sample_data(5)
            analyzer.analyze_columns()
            analyzer.analyze_dialogues()
            analyzer.analyze_medical_info()
    else:
        main()
