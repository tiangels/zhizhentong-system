import pandas as pd
import os

def inspect_medical_data(csv_file, n_rows=10):
    """
    检查医疗对话数据文件
    
    Args:
        csv_file: CSV文件路径
        n_rows: 要显示的行数
    """
    print(f"正在读取文件: {csv_file}")
    print(f"显示前 {n_rows} 行数据\n")
    
    # 读取CSV文件
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
        print(f"文件读取成功！")
        print(f"数据形状: {df.shape}")
        print(f"列名: {list(df.columns)}\n")
        
        # 显示基本信息
        print("=== 数据基本信息 ===")
        print(f"总行数: {len(df)}")
        print(f"总列数: {len(df.columns)}")
        print()
        
        # 显示前n行数据
        print(f"=== 前 {n_rows} 行数据预览 ===")
        for i in range(min(n_rows, len(df))):
            print(f"\n--- 第 {i+1} 行 ---")
            row = df.iloc[i]
            for col in df.columns:
                value = str(row[col])
                # 如果内容太长，截断显示
                if len(value) > 100:
                    value = value[:100] + "..."
                print(f"{col}: {value}")
        
        # 显示数据类型和缺失值统计
        print(f"\n=== 数据类型和缺失值统计 ===")
        info_df = pd.DataFrame({
            '列名': df.columns,
            '数据类型': df.dtypes,
            '缺失值数量': df.isnull().sum(),
            '缺失值比例': (df.isnull().sum() / len(df) * 100).round(2)
        })
        print(info_df.to_string(index=False))
        
        # 显示一些统计信息
        print(f"\n=== 数据统计信息 ===")
        if 'doctor_faculty' in df.columns:
            print(f"医生科室数量: {df['doctor_faculty'].nunique()}")
            print(f"最常见的5个科室:")
            print(df['doctor_faculty'].value_counts().head().to_string())
        
        if 'disease' in df.columns:
            print(f"\n疾病类型数量: {df['disease'].nunique()}")
            print(f"最常见的5种疾病:")
            print(df['disease'].value_counts().head().to_string())
        
        # 检查对话内容长度
        if 'dialogue_content' in df.columns:
            dialogue_lengths = df['dialogue_content'].str.len()
            print(f"\n对话内容长度统计:")
            print(f"平均长度: {dialogue_lengths.mean():.2f} 字符")
            print(f"最短长度: {dialogue_lengths.min()} 字符")
            print(f"最长长度: {dialogue_lengths.max()} 字符")
        
        # 检查问答对统计
        if 'qa_pairs' in df.columns:
            qa_counts = df['qa_pairs'].apply(lambda x: len(str(x).split(' | ')) if pd.notna(x) and str(x).strip() else 0)
            print(f"\n问答对统计:")
            print(f"平均问答对数: {qa_counts.mean():.2f}")
            print(f"最多问答对数: {qa_counts.max()}")
            print(f"最少问答对数: {qa_counts.min()}")
        
        return df
        
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None

def show_sample_dialogues(df, n_samples=3):
    """显示样本对话内容"""
    print(f"\n=== 样本对话内容展示 ===")
    
    for i in range(min(n_samples, len(df))):
        print(f"\n--- 样本 {i+1} ---")
        row = df.iloc[i]
        
        print(f"ID: {row.get('id', 'N/A')}")
        print(f"科室: {row.get('doctor_faculty', 'N/A')}")
        print(f"疾病: {row.get('disease', 'N/A')}")
        print(f"病情描述: {str(row.get('description', 'N/A'))[:200]}...")
        
        if 'qa_pairs' in row and pd.notna(row['qa_pairs']):
            print(f"问答对:")
            qa_pairs = str(row['qa_pairs']).split(' | ')
            for j, qa in enumerate(qa_pairs[:5]):  # 只显示前5个问答对
                print(f"  {j+1}. {qa}")
            if len(qa_pairs) > 5:
                print(f"  ... 还有 {len(qa_pairs) - 5} 个问答对")

if __name__ == "__main__":
    # 设置文件路径
    csv_file = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/processed_medical_dialogues_optimized.csv"
    
    # 检查文件是否存在
    if not os.path.exists(csv_file):
        print(f"文件不存在: {csv_file}")
        print("请确认文件路径是否正确")
    else:
        # 检查数据
        df = inspect_medical_data(csv_file, n_rows=5)
        
        if df is not None:
            # 显示样本对话
            show_sample_dialogues(df, n_samples=2)
