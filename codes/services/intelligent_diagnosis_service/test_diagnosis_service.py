#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能诊断服务测试脚本
"""

import os
import sys
import json
import requests
import argparse
import time
from pathlib import Path

# 添加项目根目录到路径
current_file = Path(__file__)
project_root = current_file.parent.parent.parent  # 回到codes目录
sys.path.insert(0, str(project_root))

# 添加common模块到路径
common_dir = project_root / "common"
sys.path.insert(0, str(common_dir))

from common.log_config import setup_logging, get_logger
setup_logging("diagnosis_service")
logger = get_logger(__name__)


def test_health_check(base_url: str):
    """测试健康检查接口"""
    try:
        logger.info("测试健康检查接口...")
        response = requests.get(f"{base_url}/diagnosis/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ 健康检查通过: {data['status']}")
            return True
        else:
            logger.error(f"❌ 健康检查失败: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 健康检查异常: {e}")
        return False


def test_service_info(base_url: str):
    """测试服务信息接口"""
    try:
        logger.info("测试服务信息接口...")
        response = requests.get(f"{base_url}/diagnosis/info", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ 服务信息获取成功: {data['service_name']} v{data['service_version']}")
            return True
        else:
            logger.error(f"❌ 服务信息获取失败: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 服务信息获取异常: {e}")
        return False


def test_summarize(base_url: str):
    """测试文本摘要接口"""
    try:
        logger.info("测试文本摘要接口...")
        
        test_data = {
            "text": "患者：医生，我最近总是感觉胸闷，特别是晚上睡觉的时候，有时候还会出汗。医生：请问您这种症状持续多长时间了？有没有其他伴随症状？患者：大概有半个月了，有时候还会感觉心跳很快，特别是活动后。",
            "max_length": 100,
            "retrieval_content": "根据《中国心血管病报告》，胸闷、心悸、出汗等症状可能与冠心病、心律失常等疾病相关。"
        }
        
        response = requests.post(
            f"{base_url}/diagnosis/summarize",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                logger.info(f"✅ 文本摘要成功: {data['summary']}")
                return True
            else:
                logger.error(f"❌ 文本摘要失败: {data['error']}")
                return False
        else:
            logger.error(f"❌ 文本摘要请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 文本摘要异常: {e}")
        return False


def test_generate_diagnosis(base_url: str):
    """测试生成诊断建议接口"""
    try:
        logger.info("测试生成诊断建议接口...")
        
        test_data = {
            "query": "我最近经常感到胸痛，这是什么原因？",
            "context": "胸痛可能由多种原因引起，包括心血管疾病、肺部疾病、消化系统疾病等。需要根据具体症状和检查结果进行诊断。",
            "response_type": "diagnosis",
            "enable_summary": True
        }
        
        response = requests.post(
            f"{base_url}/diagnosis/generate",
            json=test_data,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                logger.info(f"✅ 诊断建议生成成功: {data['diagnosis_response'][:100]}...")
                return True
            else:
                logger.error(f"❌ 诊断建议生成失败: {data['error']}")
                return False
        else:
            logger.error(f"❌ 诊断建议请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 诊断建议生成异常: {e}")
        return False


def test_stream_diagnosis(base_url: str):
    """测试流式诊断接口"""
    try:
        logger.info("测试流式诊断接口...")
        
        test_data = {
            "query": "我最近经常感到胸痛，这是什么原因？",
            "context": "胸痛可能由多种原因引起，包括心血管疾病、肺部疾病、消化系统疾病等。需要根据具体症状和检查结果进行诊断。",
            "response_type": "diagnosis",
            "enable_summary": True
        }
        
        response = requests.post(
            f"{base_url}/diagnosis/stream",
            json=test_data,
            stream=True,
            timeout=60
        )
        
        if response.status_code == 200:
            logger.info("✅ 流式诊断开始:")
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    chunk_count += 1
                    logger.info(f"  收到第{chunk_count}个数据块")
                    if chunk_count >= 5:  # 只显示前5个块
                        logger.info("  ...")
                        break
            
            logger.info("✅ 流式诊断测试完成")
            return True
        else:
            logger.error(f"❌ 流式诊断请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 流式诊断异常: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试智能诊断服务")
    parser.add_argument("--url", default="http://localhost:8003", help="服务URL")
    parser.add_argument("--test", choices=["all", "health", "info", "summarize", "generate", "stream"], 
                       default="all", help="测试类型")
    
    args = parser.parse_args()
    
    base_url = args.url.rstrip('/')
    
    logger.info("=" * 60)
    logger.info("🧪 开始测试智诊通智能诊断服务")
    logger.info("=" * 60)
    logger.info(f"服务URL: {base_url}")
    logger.info(f"测试类型: {args.test}")
    logger.info("=" * 60)
    
    # 等待服务启动
    logger.info("等待服务启动...")
    time.sleep(2)
    
    test_results = []
    
    if args.test in ["all", "health"]:
        test_results.append(("健康检查", test_health_check(base_url)))
    
    if args.test in ["all", "info"]:
        test_results.append(("服务信息", test_service_info(base_url)))
    
    if args.test in ["all", "summarize"]:
        test_results.append(("文本摘要", test_summarize(base_url)))
    
    if args.test in ["all", "generate"]:
        test_results.append(("生成诊断", test_generate_diagnosis(base_url)))
    
    if args.test in ["all", "stream"]:
        test_results.append(("流式诊断", test_stream_diagnosis(base_url)))
    
    # 输出测试结果
    logger.info("=" * 60)
    logger.info("📊 测试结果汇总")
    logger.info("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info("=" * 60)
    logger.info(f"测试完成: {passed}/{total} 通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！智能诊断服务运行正常")
        return 0
    else:
        logger.error("⚠️ 部分测试失败，请检查服务状态")
        return 1


if __name__ == "__main__":
    sys.exit(main())
