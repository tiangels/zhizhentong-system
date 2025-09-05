#!/usr/bin/env python3
"""
快速查看医疗对话数据的工具
使用方法: python quick_view.py [行数] [列名]
"""

import pandas as pd
import sys
import os

def quick_view(n_rows=10, columns=None):
    """快速查看数据"""
    csv_file = "/Users/tiangels/AI/llm_learning_project/zhi_zhen_tong_system/datas/medical_knowledge/processed_medical_dialogues_optimized.csv"
    
    if not os.path.exists(csv_file):
        print(f"文件不存在: {csv_file}")
        return
    
    print(f"正在读取文件: {csv_file}")
    print(f"显示前 {n_rows} 行数据\n")
    
    try:
        # 读取数据
        df = pd.read_csv(csv_file, encoding='utf-8', low_memory=False)
        print(f"数据形状: {df.shape}")
        print(f"列名: {list(df.columns)}\n")
        
        # 选择要显示的列
        if columns:
            available_cols = [col for col in columns if col in df.columns]
            if not available_cols:
                print(f"指定的列 {columns} 不存在")
                print(f"可用列: {list(df.columns)}")
                return
            display_df = df[available_cols].head(n_rows)
        else:
            display_df = df.head(n_rows)
        
        # 显示数据
        for i in range(len(display_df)):
            print(f"{'='*60}")
            print(f"第 {i+1} 行数据")
            print(f"{'='*60}")
            
            row = display_df.iloc[i]
            for col in display_df.columns:
                value = str(row[col])
                if value == 'nan':
                    value = '无数据'
                elif len(value) > 300:
                    value = value[:300] + "..."
                
                print(f"\n{col}:")
                print(f"  {value}")
            print()
        
        # 显示统计信息
        print(f"{'='*60}")
        print("数据统计信息")
        print(f"{'='*60}")
        print(f"总行数: {len(df):,}")
        print(f"总列数: {len(df.columns)}")
        
        # 显示缺失值统计
        print(f"\n缺失值统计:")
        missing_stats = df.isnull().sum()
        for col, missing_count in missing_stats.items():
            if missing_count > 0:
                print(f"  {col}: {missing_count:,} ({missing_count/len(df)*100:.2f}%)")
        
        # 显示对话统计
        if 'dialogue_content' in df.columns:
            dialogue_lengths = df['dialogue_content'].str.len()
            print(f"\n对话内容长度统计:")
            print(f"  平均长度: {dialogue_lengths.mean():.2f} 字符")
            print(f"  最短长度: {dialogue_lengths.min()} 字符")
            print(f"  最长长度: {dialogue_lengths.max()} 字符")
        
        if 'qa_pairs' in df.columns:
            qa_counts = df['qa_pairs'].apply(
                lambda x: len(str(x).split(' | ')) if pd.notna(x) and str(x).strip() else 0
            )
            print(f"\n问答对统计:")
            print(f"  平均问答对数: {qa_counts.mean():.2f}")
            print(f"  最多问答对数: {qa_counts.max()}")
            print(f"  最少问答对数: {qa_counts.min()}")
        
    except Exception as e:
        print(f"读取文件时出错: {e}")

def main():
    """主函数"""
    # 解析命令行参数
    n_rows = 10
    columns = None
    
    if len(sys.argv) > 1:
        try:
            n_rows = int(sys.argv[1])
        except ValueError:
            print("行数必须是整数")
            return
    
    if len(sys.argv) > 2:
        columns = sys.argv[2:]
    
    # 显示数据
    quick_view(n_rows, columns)

if __name__ == "__main__":
    main()
