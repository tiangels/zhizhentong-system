#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智诊通系统 - 环境验证脚本
检查所有必要的组件是否正确安装和配置
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python版本过低: {version.major}.{version.minor}.{version.micro}")
        print("   需要Python 3.8或更高版本")
        return False

def check_required_packages():
    """检查必要的Python包"""
    print("\n📦 检查Python包...")
    
    required_packages = [
        'numpy', 'pandas', 'torch', 'transformers', 
        'langchain', 'chromadb', 'sentence_transformers',
        'jieba', 'PIL', 'tqdm'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n缺少以下包: {', '.join(missing_packages)}")
        print("请运行: pip install -r processed_vqa_data/requirements.txt")
        return False
    
    return True

def check_data_directories():
    """检查数据目录"""
    print("\n📁 检查数据目录...")
    
    required_dirs = [
        'Medical-Dialogue-Dataset-Chinese',
        'VQA_data',
        'processed_vqa_data',
        'vector_database',
        'models'
    ]
    
    missing_dirs = []
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            file_count = len(list(dir_path.rglob('*')))
            print(f"✅ {dir_name} ({file_count} 个文件)")
        else:
            print(f"❌ {dir_name} - 目录不存在")
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"\n缺少以下目录: {', '.join(missing_dirs)}")
        return False
    
    return True

def check_script_files():
    """检查脚本文件"""
    print("\n🔧 检查脚本文件...")
    
    required_scripts = [
        'run_cross_platform.py',
        'run_all.sh',
        'test_retrieval.py',
        'processed_vqa_data/text_preprocessing.py',
        'processed_vqa_data/image_text_preprocessing.py',
        'vector_database/build_vector_database.py'
    ]
    
    missing_scripts = []
    
    for script in required_scripts:
        script_path = Path(script)
        if script_path.exists():
            # 检查执行权限
            if script.endswith('.py') or script.endswith('.sh'):
                if os.access(script_path, os.X_OK):
                    print(f"✅ {script} (可执行)")
                else:
                    print(f"⚠️  {script} (存在但无执行权限)")
            else:
                print(f"✅ {script}")
        else:
            print(f"❌ {script} - 文件不存在")
            missing_scripts.append(script)
    
    if missing_scripts:
        print(f"\n缺少以下脚本: {', '.join(missing_scripts)}")
        return False
    
    return True

def check_model_files():
    """检查模型文件"""
    print("\n🤖 检查模型文件...")
    
    model_path = Path('models/text2vec-base-chinese')
    if model_path.exists():
        config_file = model_path / 'config.json'
        if config_file.exists():
            print("✅ text2vec-base-chinese 模型文件存在")
            return True
        else:
            print("⚠️  模型目录存在但config.json缺失")
            return False
    else:
        print("❌ text2vec-base-chinese 模型目录不存在")
        print("   模型将在首次运行时自动下载")
        return True  # 不算错误，会自动下载

def check_vector_database():
    """检查向量数据库"""
    print("\n🗄️  检查向量数据库...")
    
    db_path = Path('vector_database/chroma_db')
    if db_path.exists():
        # 检查数据库文件
        db_files = list(db_path.rglob('*'))
        if db_files:
            print(f"✅ 向量数据库存在 ({len(db_files)} 个文件)")
            return True
        else:
            print("⚠️  向量数据库目录存在但为空")
            return False
    else:
        print("❌ 向量数据库不存在")
        print("   需要运行数据预处理和向量数据库构建")
        return False

def check_processed_data():
    """检查处理后的数据"""
    print("\n📊 检查处理后的数据...")
    
    processed_files = [
        'processed_vqa_data/processed_medical_dialogues.csv',
        'processed_vqa_data/processed_reports.csv',
        'processed_vqa_data/processed_images.npy'
    ]
    
    existing_files = []
    for file_path in processed_files:
        if Path(file_path).exists():
            existing_files.append(file_path)
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - 不存在")
    
    if existing_files:
        print(f"\n已处理的数据文件: {len(existing_files)}/{len(processed_files)}")
        return len(existing_files) >= 1  # 至少有一个文件存在
    else:
        print("   需要运行数据预处理脚本")
        return False

def run_quick_test():
    """运行快速测试"""
    print("\n🧪 运行快速测试...")
    
    try:
        # 测试导入关键模块
        from langchain_community.embeddings import HuggingFaceEmbeddings
        print("✅ LangChain导入成功")
        
        # 测试模型加载
        embeddings = HuggingFaceEmbeddings(
            model_name="shibing624/text2vec-base-chinese",
            model_kwargs={"device": "cpu"}
        )
        print("✅ 嵌入模型加载成功")
        
        # 测试向量化
        test_text = "胸痛患者的诊断"
        vector = embeddings.embed_query(test_text)
        print(f"✅ 文本向量化成功 (维度: {len(vector)})")
        
        return True
        
    except Exception as e:
        print(f"❌ 快速测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🔍 智诊通词向量模型环境验证")
    print("=" * 50)
    
    checks = [
        ("Python版本", check_python_version),
        ("Python包", check_required_packages),
        ("数据目录", check_data_directories),
        ("脚本文件", check_script_files),
        ("模型文件", check_model_files),
        ("向量数据库", check_vector_database),
        ("处理后数据", check_processed_data),
        ("快速测试", run_quick_test)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name}检查出错: {e}")
            results.append((name, False))
    
    # 输出总结
    print("\n" + "=" * 50)
    print("📋 验证结果总结")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 项检查通过")
    
    if passed == total:
        print("\n🎉 所有检查都通过了！系统已准备就绪。")
        print("\n下一步:")
        print("1. 运行数据预处理: python3 run_cross_platform.py --all")
        print("2. 测试检索功能: python3 test_retrieval.py")
        print("3. 集成到智诊通系统: 参考 INTEGRATION_GUIDE.md")
    elif passed >= total * 0.7:
        print("\n⚠️  大部分检查通过，系统基本可用。")
        print("请解决失败的检查项以获得最佳体验。")
    else:
        print("\n❌ 多项检查失败，请先解决环境问题。")
        print("建议:")
        print("1. 安装缺失的Python包")
        print("2. 检查数据目录结构")
        print("3. 运行数据预处理脚本")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
# -*- coding: utf-8 -*-
"""
智诊通系统 - 环境验证脚本
检查所有必要的组件是否正确安装和配置
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python版本过低: {version.major}.{version.minor}.{version.micro}")
        print("   需要Python 3.8或更高版本")
        return False

def check_required_packages():
    """检查必要的Python包"""
    print("\n📦 检查Python包...")
    
    required_packages = [
        'numpy', 'pandas', 'torch', 'transformers', 
        'langchain', 'chromadb', 'sentence_transformers',
        'jieba', 'PIL', 'tqdm'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n缺少以下包: {', '.join(missing_packages)}")
        print("请运行: pip install -r processed_vqa_data/requirements.txt")
        return False
    
    return True

def check_data_directories():
    """检查数据目录"""
    print("\n📁 检查数据目录...")
    
    required_dirs = [
        'Medical-Dialogue-Dataset-Chinese',
        'VQA_data',
        'processed_vqa_data',
        'vector_database',
        'models'
    ]
    
    missing_dirs = []
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            file_count = len(list(dir_path.rglob('*')))
            print(f"✅ {dir_name} ({file_count} 个文件)")
        else:
            print(f"❌ {dir_name} - 目录不存在")
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"\n缺少以下目录: {', '.join(missing_dirs)}")
        return False
    
    return True

def check_script_files():
    """检查脚本文件"""
    print("\n🔧 检查脚本文件...")
    
    required_scripts = [
        'run_cross_platform.py',
        'run_all.sh',
        'test_retrieval.py',
        'processed_vqa_data/text_preprocessing.py',
        'processed_vqa_data/image_text_preprocessing.py',
        'vector_database/build_vector_database.py'
    ]
    
    missing_scripts = []
    
    for script in required_scripts:
        script_path = Path(script)
        if script_path.exists():
            # 检查执行权限
            if script.endswith('.py') or script.endswith('.sh'):
                if os.access(script_path, os.X_OK):
                    print(f"✅ {script} (可执行)")
                else:
                    print(f"⚠️  {script} (存在但无执行权限)")
            else:
                print(f"✅ {script}")
        else:
            print(f"❌ {script} - 文件不存在")
            missing_scripts.append(script)
    
    if missing_scripts:
        print(f"\n缺少以下脚本: {', '.join(missing_scripts)}")
        return False
    
    return True

def check_model_files():
    """检查模型文件"""
    print("\n🤖 检查模型文件...")
    
    model_path = Path('models/text2vec-base-chinese')
    if model_path.exists():
        config_file = model_path / 'config.json'
        if config_file.exists():
            print("✅ text2vec-base-chinese 模型文件存在")
            return True
        else:
            print("⚠️  模型目录存在但config.json缺失")
            return False
    else:
        print("❌ text2vec-base-chinese 模型目录不存在")
        print("   模型将在首次运行时自动下载")
        return True  # 不算错误，会自动下载

def check_vector_database():
    """检查向量数据库"""
    print("\n🗄️  检查向量数据库...")
    
    db_path = Path('vector_database/chroma_db')
    if db_path.exists():
        # 检查数据库文件
        db_files = list(db_path.rglob('*'))
        if db_files:
            print(f"✅ 向量数据库存在 ({len(db_files)} 个文件)")
            return True
        else:
            print("⚠️  向量数据库目录存在但为空")
            return False
    else:
        print("❌ 向量数据库不存在")
        print("   需要运行数据预处理和向量数据库构建")
        return False

def check_processed_data():
    """检查处理后的数据"""
    print("\n📊 检查处理后的数据...")
    
    processed_files = [
        'processed_vqa_data/processed_medical_dialogues.csv',
        'processed_vqa_data/processed_reports.csv',
        'processed_vqa_data/processed_images.npy'
    ]
    
    existing_files = []
    for file_path in processed_files:
        if Path(file_path).exists():
            existing_files.append(file_path)
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - 不存在")
    
    if existing_files:
        print(f"\n已处理的数据文件: {len(existing_files)}/{len(processed_files)}")
        return len(existing_files) >= 1  # 至少有一个文件存在
    else:
        print("   需要运行数据预处理脚本")
        return False

def run_quick_test():
    """运行快速测试"""
    print("\n🧪 运行快速测试...")
    
    try:
        # 测试导入关键模块
        from langchain_community.embeddings import HuggingFaceEmbeddings
        print("✅ LangChain导入成功")
        
        # 测试模型加载
        embeddings = HuggingFaceEmbeddings(
            model_name="shibing624/text2vec-base-chinese",
            model_kwargs={"device": "cpu"}
        )
        print("✅ 嵌入模型加载成功")
        
        # 测试向量化
        test_text = "胸痛患者的诊断"
        vector = embeddings.embed_query(test_text)
        print(f"✅ 文本向量化成功 (维度: {len(vector)})")
        
        return True
        
    except Exception as e:
        print(f"❌ 快速测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🔍 智诊通词向量模型环境验证")
    print("=" * 50)
    
    checks = [
        ("Python版本", check_python_version),
        ("Python包", check_required_packages),
        ("数据目录", check_data_directories),
        ("脚本文件", check_script_files),
        ("模型文件", check_model_files),
        ("向量数据库", check_vector_database),
        ("处理后数据", check_processed_data),
        ("快速测试", run_quick_test)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name}检查出错: {e}")
            results.append((name, False))
    
    # 输出总结
    print("\n" + "=" * 50)
    print("📋 验证结果总结")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 项检查通过")
    
    if passed == total:
        print("\n🎉 所有检查都通过了！系统已准备就绪。")
        print("\n下一步:")
        print("1. 运行数据预处理: python3 run_cross_platform.py --all")
        print("2. 测试检索功能: python3 test_retrieval.py")
        print("3. 集成到智诊通系统: 参考 INTEGRATION_GUIDE.md")
    elif passed >= total * 0.7:
        print("\n⚠️  大部分检查通过，系统基本可用。")
        print("请解决失败的检查项以获得最佳体验。")
    else:
        print("\n❌ 多项检查失败，请先解决环境问题。")
        print("建议:")
        print("1. 安装缺失的Python包")
        print("2. 检查数据目录结构")
        print("3. 运行数据预处理脚本")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)




