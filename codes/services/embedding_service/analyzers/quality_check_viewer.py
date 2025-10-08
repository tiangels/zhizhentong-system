#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
质量检查结果查看器
用于查看向量化过程中各环节的质量检查结果
支持数据统计和图表展示
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 导入字体配置模块
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config'))
try:
    from font_config import configure_chinese_font
    configure_chinese_font()
except ImportError:
    print("警告: 字体配置模块未找到，图表可能无法正确显示中文")

class QualityCheckViewer:
    """质量检查结果查看器"""
    
    def __init__(self, data_dir: str, log_dir: str = None):
        """
        初始化质量检查结果查看器
        
        Args:
            data_dir: 数据目录路径
            log_dir: 日志目录路径
        """
        self.data_dir = Path(data_dir)
        self.log_dir = Path(log_dir) if log_dir else self.data_dir.parent / "logs"
        self.logger = self._setup_logging()
        
        # 质量检查结果存储
        self.quality_stats = {}
        self.quality_reports = {}
        self.vectorization_stats = {}
        
        # 创建输出目录
        self.output_dir = self.data_dir / "quality_reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _setup_logging(self) -> logging.Logger:
        """设置日志 - 使用统一的日志系统"""
        import sys
        from pathlib import Path
        
        # 添加common模块到路径
        current_file = Path(__file__)
        common_dir = current_file.parent.parent.parent.parent / "common"
        sys.path.insert(0, str(common_dir))
        
        from log_config import setup_service_logging
        
        # 使用统一的日志管理器
        return setup_service_logging("quality_check_analysis")
    
    def load_quality_stats(self, stats_file: str = None) -> Dict:
        """
        加载质量检查统计数据
        
        Args:
            stats_file: 统计文件路径
            
        Returns:
            质量统计数据
        """
        if stats_file is None:
            stats_file = self.data_dir / "quality_stats.json"
        
        if not Path(stats_file).exists():
            self.logger.warning(f"质量统计文件不存在: {stats_file}")
            return {}
        
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                self.quality_stats = json.load(f)
            self.logger.info(f"成功加载质量统计数据: {stats_file}")
            return self.quality_stats
        except Exception as e:
            self.logger.error(f"加载质量统计数据失败: {e}")
            return {}
    
    def load_vectorization_logs(self, log_file: str = None) -> Dict:
        """
        从向量化日志中提取质量检查信息
        
        Args:
            log_file: 日志文件路径
            
        Returns:
            向量化过程中的质量检查信息
        """
        if log_file is None:
            log_file = self.log_dir / "multimodal_builder.log"
        
        if not Path(log_file).exists():
            self.logger.warning(f"向量化日志文件不存在: {log_file}")
            return {}
        
        try:
            quality_info = {
                'total_documents': 0,
                'valid_documents': 0,
                'invalid_documents': 0,
                'empty_documents': 0,
                'short_documents': 0,
                'quality_checks': [],
                'processing_stages': []
            }
            
            # 首先尝试从质量统计数据中获取向量化信息
            if self.quality_stats:
                overall_stats = self.quality_stats.get('overall_stats', {})
                # 从质量统计数据中推导向量化统计信息
                total_texts = overall_stats.get('total_texts', 0)
                final_passed = overall_stats.get('final_passed', 0)
                
                quality_info['total_documents'] = total_texts
                quality_info['valid_documents'] = final_passed
                quality_info['invalid_documents'] = total_texts - final_passed
                quality_info['empty_documents'] = 0
                quality_info['short_documents'] = 0
                
                self.logger.info(f"从质量统计数据中提取向量化信息: 总文档={total_texts}, 有效={final_passed}")
            
            # 如果日志文件存在，尝试从中提取额外信息
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    # 提取质量检查信息
                    if "质量检查" in line or "quality" in line.lower():
                        quality_info['quality_checks'].append(line.strip())
                    
                    # 提取处理阶段信息
                    if "处理片段" in line or "处理完成" in line:
                        quality_info['processing_stages'].append(line.strip())
                    
                    # 提取统计信息（如果日志中有更详细的信息，会覆盖从质量统计数据中获取的信息）
                    if "总文档数" in line:
                        try:
                            quality_info['total_documents'] = int(line.split("总文档数:")[1].split()[0])
                        except:
                            pass
                    elif "有效文档数" in line:
                        try:
                            quality_info['valid_documents'] = int(line.split("有效文档数:")[1].split()[0])
                        except:
                            pass
                    elif "无效文档数" in line:
                        try:
                            quality_info['invalid_documents'] = int(line.split("无效文档数:")[1].split()[0])
                        except:
                            pass
                    elif "空文档数" in line:
                        try:
                            quality_info['empty_documents'] = int(line.split("空文档数:")[1].split()[0])
                        except:
                            pass
                    elif "短文档数" in line:
                        try:
                            quality_info['short_documents'] = int(line.split("短文档数:")[1].split()[0])
                        except:
                            pass
            
            self.vectorization_stats = quality_info
            self.logger.info(f"成功从日志中提取质量检查信息")
            return quality_info
            
        except Exception as e:
            self.logger.error(f"从日志中提取质量检查信息失败: {e}")
            return {}
    
    def create_quality_overview_chart(self) -> str:
        """
        创建质量检查概览图表
        
        Returns:
            图表文件路径
        """
        if not self.quality_stats and not self.vectorization_stats:
            self.logger.warning("没有质量检查数据可显示")
            return None
        
        # 准备数据
        if self.vectorization_stats:
            total = self.vectorization_stats.get('total_documents', 0)
            valid = self.vectorization_stats.get('valid_documents', 0)
            invalid = self.vectorization_stats.get('invalid_documents', 0)
            empty = self.vectorization_stats.get('empty_documents', 0)
            short = self.vectorization_stats.get('short_documents', 0)
        else:
            # 修复数据结构解析 - 从嵌套结构中获取数据
            overall_stats = self.quality_stats.get('overall_stats', {})
            total = overall_stats.get('total_texts', 0)
            valid = overall_stats.get('final_passed', 0)
            invalid = total - valid
            empty = 0
            short = 0
        
        if total == 0:
            self.logger.warning("没有文档数据可显示")
            return None
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 左图：文档质量分布饼图
        labels = ['有效文档', '无效文档', '空文档', '短文档']
        sizes = [valid, invalid, empty, short]
        colors = ['#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']
        
        # 过滤掉0值
        non_zero_data = [(label, size, color) for label, size, color in zip(labels, sizes, colors) if size > 0]
        if non_zero_data:
            labels_filtered, sizes_filtered, colors_filtered = zip(*non_zero_data)
            
            ax1.pie(sizes_filtered, labels=labels_filtered, colors=colors_filtered, autopct='%1.1f%%', startangle=90)
            ax1.set_title('文档质量分布', fontsize=14, fontweight='bold')
        
        # 右图：质量检查通过率柱状图
        if self.quality_stats:
            # 修复数据结构解析 - 从嵌套结构中获取数据
            overall_stats = self.quality_stats.get('overall_stats', {})
            stages = ['完整性检查', '唯一性检查', '相关性检查', '向量化检查']
            pass_rates = [
                overall_stats.get('completeness_passed', 0) / total * 100 if total > 0 else 0,
                overall_stats.get('uniqueness_passed', 0) / total * 100 if total > 0 else 0,
                overall_stats.get('relevance_passed', 0) / total * 100 if total > 0 else 0,
                overall_stats.get('vectorization_passed', 0) / total * 100 if total > 0 else 0
            ]
            
            bars = ax2.bar(stages, pass_rates, color=['#3498db', '#e67e22', '#9b59b6', '#1abc9c'])
            ax2.set_title('各阶段质量检查通过率', fontsize=14, fontweight='bold')
            ax2.set_ylabel('通过率 (%)')
            ax2.set_ylim(0, 100)
            
            # 在柱子上显示数值
            for bar, rate in zip(bars, pass_rates):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{rate:.1f}%', ha='center', va='bottom')
            
            plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        # 保存图表
        chart_path = self.output_dir / "quality_overview.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"质量概览图表已保存: {chart_path}")
        return str(chart_path)
    
    def create_filter_reasons_chart(self) -> str:
        """
        创建过滤原因分析图表
        
        Returns:
            图表文件路径
        """
        if not self.quality_stats:
            self.logger.warning("没有质量检查统计数据可显示")
            return None
        
        # 修复数据结构解析 - 从嵌套结构中获取数据
        overall_stats = self.quality_stats.get('overall_stats', {})
        filtered_reasons = overall_stats.get('filtered_reasons', {})
        if not filtered_reasons:
            self.logger.info("没有过滤原因数据可显示（所有文档都通过了质量检查）")
            return None
        
        # 准备数据
        reasons = list(filtered_reasons.keys())
        counts = list(filtered_reasons.values())
        
        if not reasons:
            return None
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 左图：过滤原因柱状图
        bars = ax1.barh(reasons, counts, color='#e74c3c')
        ax1.set_title('文档过滤原因分析', fontsize=14, fontweight='bold')
        ax1.set_xlabel('过滤数量')
        
        # 在柱子上显示数值
        for bar, count in zip(bars, counts):
            width = bar.get_width()
            ax1.text(width + 0.1, bar.get_y() + bar.get_height()/2,
                    f'{count}', ha='left', va='center')
        
        # 右图：过滤原因饼图
        ax2.pie(counts, labels=reasons, autopct='%1.1f%%', startangle=90)
        ax2.set_title('过滤原因分布', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # 保存图表
        chart_path = self.output_dir / "filter_reasons.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"过滤原因分析图表已保存: {chart_path}")
        return str(chart_path)
    
    def create_processing_timeline_chart(self) -> str:
        """
        创建处理时间线图表
        
        Returns:
            图表文件路径
        """
        if not self.vectorization_stats or not self.vectorization_stats.get('processing_stages'):
            self.logger.info("没有处理阶段数据可显示（处理阶段信息未记录）")
            return None
        
        # 分析处理阶段
        stages = []
        stage_counts = defaultdict(int)
        
        for stage in self.vectorization_stats['processing_stages']:
            if "处理片段" in stage:
                stages.append("文档处理")
                stage_counts["文档处理"] += 1
            elif "处理完成" in stage:
                stages.append("处理完成")
                stage_counts["处理完成"] += 1
        
        if not stages:
            return None
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 处理阶段分布
        stage_names = list(stage_counts.keys())
        stage_values = list(stage_counts.values())
        
        bars = ax.bar(stage_names, stage_values, color=['#3498db', '#2ecc71'])
        ax.set_title('处理阶段分布', fontsize=14, fontweight='bold')
        ax.set_ylabel('处理数量')
        
        # 在柱子上显示数值
        for bar, value in zip(bars, stage_values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{value}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        # 保存图表
        chart_path = self.output_dir / "processing_timeline.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"处理时间线图表已保存: {chart_path}")
        return str(chart_path)
    
    def create_quality_trend_chart(self) -> str:
        """
        创建质量趋势图表
        
        Returns:
            图表文件路径
        """
        if not self.quality_stats:
            self.logger.warning("没有质量检查统计数据可显示")
            return None
        
        # 准备数据
        # 修复数据结构解析 - 从嵌套结构中获取数据
        overall_stats = self.quality_stats.get('overall_stats', {})
        stages = ['完整性', '唯一性', '相关性', '向量化']
        pass_counts = [
            overall_stats.get('completeness_passed', 0),
            overall_stats.get('uniqueness_passed', 0),
            overall_stats.get('relevance_passed', 0),
            overall_stats.get('vectorization_passed', 0)
        ]
        
        total = overall_stats.get('total_texts', 0)
        if total == 0:
            return None
        
        # 计算累积通过率
        cumulative_rates = []
        for count in pass_counts:
            rate = count / total * 100
            cumulative_rates.append(rate)
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 左图：各阶段通过数量
        bars = ax1.bar(stages, pass_counts, color=['#3498db', '#e67e22', '#9b59b6', '#1abc9c'])
        ax1.set_title('各阶段通过数量', fontsize=14, fontweight='bold')
        ax1.set_ylabel('通过数量')
        
        # 在柱子上显示数值
        for bar, count in zip(bars, pass_counts):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{count}', ha='center', va='bottom')
        
        # 右图：累积通过率趋势
        ax2.plot(stages, cumulative_rates, marker='o', linewidth=2, markersize=8, color='#e74c3c')
        ax2.set_title('累积通过率趋势', fontsize=14, fontweight='bold')
        ax2.set_ylabel('通过率 (%)')
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.3)
        
        # 在点上显示数值
        for stage, rate in zip(stages, cumulative_rates):
            ax2.text(stage, rate + 2, f'{rate:.1f}%', ha='center', va='bottom')
        
        plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
        plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        # 保存图表
        chart_path = self.output_dir / "quality_trend.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"质量趋势图表已保存: {chart_path}")
        return str(chart_path)
    
    def generate_quality_report(self) -> str:
        """
        生成质量检查报告
        
        Returns:
            报告文件路径
        """
        report = {
            "report_info": {
                "generated_at": datetime.now().isoformat(),
                "data_dir": str(self.data_dir),
                "output_dir": str(self.output_dir)
            },
            "quality_statistics": self.quality_stats,
            "vectorization_statistics": self.vectorization_stats,
            "summary": self._generate_summary()
        }
        
        # 保存报告
        report_path = self.output_dir / "quality_check_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"质量检查报告已保存: {report_path}")
        return str(report_path)
    
    def _generate_summary(self) -> Dict:
        """生成质量检查摘要"""
        summary = {
            "overview": {},
            "quality_metrics": {},
            "recommendations": []
        }
        
        # 概览信息
        if self.vectorization_stats:
            total = self.vectorization_stats.get('total_documents', 0)
            valid = self.vectorization_stats.get('valid_documents', 0)
            invalid = self.vectorization_stats.get('invalid_documents', 0)
            
            summary["overview"] = {
                "total_documents": total,
                "valid_documents": valid,
                "invalid_documents": invalid,
                "success_rate": f"{valid/total*100:.2f}%" if total > 0 else "0%"
            }
        
        # 质量指标
        if self.quality_stats:
            # 修复数据结构解析 - 从嵌套结构中获取数据
            overall_stats = self.quality_stats.get('overall_stats', {})
            total = overall_stats.get('total_texts', 0)
            if total > 0:
                summary["quality_metrics"] = {
                    "completeness_rate": f"{overall_stats.get('completeness_passed', 0)/total*100:.2f}%",
                    "uniqueness_rate": f"{overall_stats.get('uniqueness_passed', 0)/total*100:.2f}%",
                    "relevance_rate": f"{overall_stats.get('relevance_passed', 0)/total*100:.2f}%",
                    "vectorization_rate": f"{overall_stats.get('vectorization_passed', 0)/total*100:.2f}%",
                    "final_pass_rate": f"{overall_stats.get('final_passed', 0)/total*100:.2f}%"
                }
        
        # 建议
        if self.quality_stats:
            # 修复数据结构解析 - 从嵌套结构中获取数据
            overall_stats = self.quality_stats.get('overall_stats', {})
            filtered_reasons = overall_stats.get('filtered_reasons', {})
            if filtered_reasons:
                top_reason = max(filtered_reasons.items(), key=lambda x: x[1])
                summary["recommendations"].append(f"主要过滤原因: {top_reason[0]} ({top_reason[1]}次)")
                
                if "文本过短" in filtered_reasons:
                    summary["recommendations"].append("建议调整最小文本长度阈值")
                if "重复文本" in filtered_reasons:
                    summary["recommendations"].append("建议检查数据源，避免重复数据")
                if "包含无关关键词" in filtered_reasons:
                    summary["recommendations"].append("建议更新无关关键词列表")
        
        return summary
    
    def create_html_report(self) -> str:
        """
        创建HTML格式的质量检查报告
        
        Returns:
            HTML报告文件路径
        """
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>质量检查报告</title>
            <style>
                body {{
                    font-family: 'Microsoft YaHei', Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2c3e50;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .section {{
                    margin-bottom: 30px;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }}
                .section h2 {{
                    color: #34495e;
                    margin-top: 0;
                }}
                .metric {{
                    display: inline-block;
                    margin: 10px;
                    padding: 15px;
                    background-color: #ecf0f1;
                    border-radius: 5px;
                    text-align: center;
                    min-width: 120px;
                }}
                .metric-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .metric-label {{
                    font-size: 14px;
                    color: #7f8c8d;
                }}
                .chart-container {{
                    text-align: center;
                    margin: 20px 0;
                }}
                .chart-container img {{
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }}
                .recommendations {{
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 5px;
                    padding: 15px;
                }}
                .recommendations h3 {{
                    color: #856404;
                    margin-top: 0;
                }}
                .recommendations ul {{
                    margin: 10px 0;
                    padding-left: 20px;
                }}
                .recommendations li {{
                    margin: 5px 0;
                    color: #856404;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>质量检查报告</h1>
                <p style="text-align: center; color: #7f8c8d;">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <div class="section">
                    <h2>📊 质量概览</h2>
                    <div class="chart-container">
                        <img src="quality_overview.png" alt="质量概览图表">
                    </div>
                </div>
                
                <div class="section">
                    <h2>🔍 过滤原因分析</h2>
                    <div class="chart-container">
                        <img src="filter_reasons.png" alt="过滤原因分析图表">
                    </div>
                </div>
                
                <div class="section">
                    <h2>📈 质量趋势</h2>
                    <div class="chart-container">
                        <img src="quality_trend.png" alt="质量趋势图表">
                    </div>
                </div>
                
                <div class="section">
                    <h2>⏱️ 处理时间线</h2>
                    <div class="chart-container">
                        <img src="processing_timeline.png" alt="处理时间线图表">
                    </div>
                </div>
                
                <div class="section">
                    <h2>💡 建议</h2>
                    <div class="recommendations">
                        <h3>优化建议</h3>
                        <ul>
                            <li>定期检查数据源质量，确保输入数据的完整性</li>
                            <li>根据过滤原因调整质量检查参数</li>
                            <li>监控各阶段通过率，及时发现问题</li>
                            <li>建立数据质量监控机制</li>
                        </ul>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        html_path = self.output_dir / "quality_check_report.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"HTML质量检查报告已保存: {html_path}")
        return str(html_path)
    
    def run_quality_analysis(self, stats_file: str = None, log_file: str = None) -> Dict:
        """
        运行完整的质量分析
        
        Args:
            stats_file: 统计文件路径
            log_file: 日志文件路径
            
        Returns:
            分析结果
        """
        self.logger.info("开始质量检查结果分析...")
        
        # 加载数据
        self.load_quality_stats(stats_file)
        self.load_vectorization_logs(log_file)
        
        # 创建图表
        charts = {}
        charts['overview'] = self.create_quality_overview_chart()
        charts['filter_reasons'] = self.create_filter_reasons_chart()
        charts['quality_trend'] = self.create_quality_trend_chart()
        charts['processing_timeline'] = self.create_processing_timeline_chart()
        
        # 生成报告
        json_report = self.generate_quality_report()
        html_report = self.create_html_report()
        
        # 返回结果
        result = {
            "charts": charts,
            "reports": {
                "json": json_report,
                "html": html_report
            },
            "quality_stats": self.quality_stats,
            "vectorization_stats": self.vectorization_stats
        }
        
        self.logger.info("质量检查结果分析完成!")
        return result


def main():
    """主函数示例"""
    # 设置路径
    data_dir = "medical_knowledge"
    log_dir = "logs"
    
    # 创建查看器
    viewer = QualityCheckViewer(data_dir, log_dir)
    
    # 运行质量分析
    result = viewer.run_quality_analysis()
    
    # 打印结果
    print("\n=== 质量检查结果分析 ===")
    print(f"图表文件: {result['charts']}")
    print(f"报告文件: {result['reports']}")
    
    if result['quality_stats']:
        print(f"质量统计数据: {result['quality_stats']}")
    
    if result['vectorization_stats']:
        print(f"向量化统计数据: {result['vectorization_stats']}")


if __name__ == "__main__":
    main()
