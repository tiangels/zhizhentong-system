#!/usr/bin/env conda run -n nlp python
"""
检查项目中的模型使用情况，排除第三方库
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple

class ProjectModelChecker:
    """项目模型检查器"""
    
    def __init__(self, project_root: str = None):
        """
        初始化检查器
        
        Args:
            project_root: 项目根目录
        """
        if project_root is None:
            # 获取项目根目录
            self.project_root = Path(__file__).parent.parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # 需要排除的目录
        self.exclude_dirs = {
            "venv", "__pycache__", ".git", "node_modules", 
            ".venv", "site-packages", ".pytest_cache"
        }
        
        # 需要检查的目录
        self.check_dirs = {
            "codes/backend/app",
            "codes/services", 
            "codes/ai_models",
            "codes/frontend/src"
        }
        
        # 模型相关的关键词和模式
        self.model_patterns = {
            "llm_models": [
                r"Qwen2-0.5B-Medical-MLX",
                r"microsoft/DialoGPT",
                r"AutoModelForCausalLM",
                r"AutoTokenizer"
            ],
            "embedding_models": [
                r"text2vec-base-chinese",
                r"shibing624/text2vec-base-chinese",
                r"SentenceTransformer",
                r"clip-ViT-B-32"
            ]
        }
        
        # 本地模型路径
        self.local_model_paths = {
            "Qwen2-0.5B-Medical-MLX": str(self.project_root / "codes/ai_models/llm_models/Qwen2-0.5B-Medical-MLX"),
            "text2vec-base-chinese": str(self.project_root / "codes/ai_models/llm_models/text2vec-base-chinese")
        }
    
    def should_check_file(self, file_path: Path) -> bool:
        """
        判断是否应该检查该文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否应该检查
        """
        # 检查是否在排除目录中
        for part in file_path.parts:
            if part in self.exclude_dirs:
                return False
        
        # 检查是否在需要检查的目录中
        relative_path = file_path.relative_to(self.project_root)
        for check_dir in self.check_dirs:
            if str(relative_path).startswith(check_dir):
                return True
        
        return False
    
    def check_file(self, file_path: Path) -> Dict:
        """
        检查单个文件中的模型使用情况
        
        Args:
            file_path: 文件路径
            
        Returns:
            检查结果
        """
        result = {
            "file_path": str(file_path.relative_to(self.project_root)),
            "model_usage": [],
            "needs_update": False,
            "is_local": False
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                # 检查各种模型模式
                for model_type, patterns in self.model_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, line):
                            usage_info = {
                                "line": line_num,
                                "content": line.strip(),
                                "pattern": pattern,
                                "model_type": model_type
                            }
                            
                            # 检查是否使用本地路径
                            is_local = any(local_path in line for local_path in self.local_model_paths.values())
                            usage_info["is_local"] = is_local
                            
                            if not is_local and "microsoft/DialoGPT" in line:
                                result["needs_update"] = True
                            
                            result["model_usage"].append(usage_info)
            
            # 检查是否主要使用本地模型
            local_count = sum(1 for usage in result["model_usage"] if usage["is_local"])
            total_count = len(result["model_usage"])
            result["is_local"] = local_count > 0 and local_count >= total_count * 0.5
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def check_all_files(self) -> Dict[str, List[Dict]]:
        """
        检查所有相关文件
        
        Returns:
            检查结果
        """
        results = {
            "python_files": [],
            "config_files": [],
            "script_files": [],
            "documentation": []
        }
        
        # 遍历项目文件
        for file_path in self.project_root.rglob("*"):
            if not file_path.is_file():
                continue
            
            if not self.should_check_file(file_path):
                continue
            
            # 只检查特定类型的文件
            if file_path.suffix not in ['.py', '.json', '.sh', '.md']:
                continue
            
            result = self.check_file(file_path)
            
            # 只保留有模型使用的文件
            if result["model_usage"]:
                file_type = self._get_file_type(file_path)
                results[file_type].append(result)
        
        return results
    
    def _get_file_type(self, file_path: Path) -> str:
        """
        获取文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件类型
        """
        if file_path.suffix == '.py':
            return "python_files"
        elif file_path.suffix == '.json':
            return "config_files"
        elif file_path.suffix == '.sh':
            return "script_files"
        else:
            return "documentation"
    
    def generate_report(self) -> str:
        """
        生成检查报告
        
        Returns:
            报告内容
        """
        results = self.check_all_files()
        
        report = """# 智诊通系统项目模型使用检查报告

## 📋 检查概述

本报告检查了智诊通系统项目中所有模型使用的地方，确保优先使用本地模型。

## 🔍 检查结果

"""
        
        total_files = sum(len(files) for files in results.values())
        report += f"**总计检查文件数**: {total_files}\n\n"
        
        # 统计信息
        needs_update_count = 0
        local_count = 0
        
        for file_type, files in results.items():
            if not files:
                continue
                
            report += f"### {file_type.replace('_', ' ').title()}\n\n"
            
            for file_info in files:
                if file_info.get("needs_update"):
                    needs_update_count += 1
                if file_info.get("is_local"):
                    local_count += 1
                
                status = "✅ 本地模型" if file_info.get("is_local") else "⚠️ 需要更新"
                if file_info.get("needs_update"):
                    status = "❌ 需要更新"
                
                report += f"#### {file_info['file_path']}\n"
                report += f"**状态**: {status}\n\n"
                
                for usage in file_info['model_usage']:
                    local_indicator = "🏠" if usage["is_local"] else "🌐"
                    report += f"- {local_indicator} **第{usage['line']}行**: `{usage['content']}`\n"
                    report += f"  - 类型: {usage['model_type']}\n"
                    report += f"  - 模式: `{usage['pattern']}`\n"
                
                if file_info.get("error"):
                    report += f"⚠️ **错误**: {file_info['error']}\n"
                
                report += "\n"
        
        # 添加统计信息
        report += f"""## 📊 统计信息

- **总文件数**: {total_files}
- **使用本地模型**: {local_count}
- **需要更新**: {needs_update_count}
- **本地化率**: {(local_count/total_files*100):.1f}% (如果total_files > 0)

## 💡 建议

### 1. 优先使用本地模型
- 确保所有配置文件中的模型路径指向本地模型
- 避免在运行时下载模型，提高启动速度

### 2. 统一模型管理
- 使用 `model_manager.py` 统一管理模型路径
- 定期运行模型管理器更新配置文件

### 3. 检查清单
- [ ] 所有Python文件使用本地模型路径
- [ ] 配置文件中的模型路径正确
- [ ] 启动脚本检查本地模型存在性
- [ ] 文档中的模型路径信息准确

## 🔧 修复建议

如果发现需要更新的文件，请：

1. 使用模型管理器自动更新：
   ```python
   from model_manager import ModelManager
   manager = ModelManager()
   manager.update_config_files(use_local_models=True)
   ```

2. 手动更新配置文件中的模型路径

3. 确保本地模型文件完整且可访问

---
**检查时间**: 2024年9月11日  
**检查工具**: ProjectModelChecker  
**状态**: ✅ 完成
"""
        
        return report
    
    def save_report(self, output_path: str = None) -> bool:
        """
        保存检查报告
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            是否成功保存
        """
        try:
            if output_path is None:
                output_path = self.project_root / "codes/ai_models/llm_models/项目模型使用检查报告.md"
            
            report_content = self.generate_report()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"检查报告已保存到: {output_path}")
            return True
            
        except Exception as e:
            print(f"保存检查报告失败: {e}")
            return False


def main():
    """主函数"""
    print("🔍 智诊通系统项目模型使用检查器")
    print("=" * 50)
    
    # 创建检查器
    checker = ProjectModelChecker()
    
    # 生成并保存报告
    print("正在检查项目模型使用情况...")
    if checker.save_report():
        print("✅ 检查报告生成成功")
    else:
        print("❌ 检查报告生成失败")
    
    print("\n🎉 项目模型使用检查完成！")


if __name__ == "__main__":
    main()
