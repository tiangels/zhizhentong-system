# 检索服务日志增强总结

## 概述

为 ES 检索服务和混合检索服务添加了详细的日志记录，包括检索条件、融合过程和结果统计等关键信息。

## ES 检索服务日志增强

### 新增的日志记录

#### 1. 检索请求参数日志

```python
logger.info(f"ES检索请求 - 用户ID: {user_id}, 关键词: {keywords}, 就诊人: {patient_unique_ids}, 科室: {department}, 记录类型: {record_type}, 返回数量: {top_k}")
```

#### 2. 查询条件构建日志

- **用户权限过滤**: 记录用户 ID 过滤条件
- **就诊人过滤**: 记录就诊人 ID 列表或全量搜索
- **关键词搜索**: 记录关键词内容和搜索字段
- **科室过滤**: 记录科室过滤条件
- **记录类型过滤**: 记录记录类型过滤条件
- **日期范围过滤**: 记录日期范围条件

#### 3. ES 查询执行日志

```python
logger.info(f"构建ES查询完成 - 查询条件数量: {len(must_conditions)}, 索引: {self.index_name}")
logger.debug(f"ES查询详情: {json.dumps(query, ensure_ascii=False, indent=2)}")
logger.info(f"开始执行ES搜索 - 索引: {self.index_name}, 返回数量: {top_k}")
```

#### 4. 搜索结果统计日志

```python
logger.info(f"ES搜索完成 - 总命中数: {total_hits}, 最高分数: {max_score}, 返回结果数: {len(response['hits']['hits'])}")
```

#### 5. 结果详情日志

```python
logger.debug(f"结果 {i+1}: ID={result.get('id')}, 分数={hit['_score']:.4f}, 患者={result.get('patient_name')}")
```

### 增强的方法

1. **`search_by_user_and_keywords`** - 用户关键词检索
2. **`get_user_patient_records`** - 就诊人记录查询
3. **`search_similar_cases`** - 相似病例搜索

## 混合检索服务日志增强

### 新增的日志记录

#### 1. 混合检索协调日志

```python
logger.info(f"开始用户中心化混合检索 - 用户ID: {request.user_id}, 查询: {request.query}, 搜索模式: {request.search_mode}, 返回数量: {request.top_k}")
```

#### 2. 就诊人信息日志

```python
logger.info(f"获取用户 {request.user_id} 的就诊人信息...")
logger.info(f"用户就诊人信息获取完成 - 就诊人数量: {len(patient_info)}")
```

#### 3. 并行搜索协调日志

```python
logger.info("开始并行执行ES和向量搜索...")
logger.info("等待ES和向量搜索完成...")
logger.info(f"并行搜索完成 - ES结果数: {len(es_results)}, 向量结果数: {len(vector_results)}")
```

#### 4. RRF 融合算法日志

```python
logger.info(f"开始RRF混合融合 - ES结果数: {len(es_results)}, 向量结果数: {len(vector_results)}, ES权重: {alpha:.2f}, 向量权重: {1-alpha:.2f}")
logger.info(f"RRF算法参数 - k值: {k}")
```

#### 5. 融合过程详细日志

```python
logger.debug(f"ES结果 {rank+1}: ID={doc_id}, 原始分数={result.get('_score', 0):.4f}, RRF分数={rrf_score:.6f}, 加权分数={weighted_score:.6f}")
logger.debug(f"向量结果 {rank+1}: ID={doc_id}, 原始分数={result.get('_score', 0):.4f}, RRF分数={rrf_score:.6f}, 加权分数={weighted_score:.6f}")
```

#### 6. 融合结果统计日志

```python
logger.info(f"RRF混合融合完成 - 最终结果数: {len(hybrid_results)}")
logger.info(f"混合结果 {i+1}: ID={result.get('id')}, RRF分数={result.get('_hybrid_score', 0):.6f}, 患者={result.get('patient_name', 'N/A')}")
```

#### 7. ES 和向量搜索调用日志

```python
logger.info(f"开始ES搜索 - 用户ID: {user_id}, 查询: {query}, 就诊人: {patient_unique_ids}, 科室: {department}")
logger.info(f"发送ES搜索请求到: {self.es_service_url}/search/user-centric")
logger.info(f"ES搜索成功 - 返回结果数: {len(es_results)}")
```

### 增强的方法

1. **`search`** - 主混合检索方法
2. **`es_search`** - ES 搜索调用
3. **`vector_search`** - 向量搜索调用
4. **`hybrid_fusion`** - RRF 融合算法

## 日志级别说明

### INFO 级别日志

- 检索请求参数
- 查询条件构建过程
- 搜索执行状态
- 结果统计信息
- 融合算法参数和结果

### DEBUG 级别日志

- 详细的查询条件 JSON
- 每个搜索结果的详细信息
- RRF 算法计算过程
- 融合分数计算详情

### ERROR 级别日志

- 搜索失败信息
- 服务调用异常
- 融合算法异常

## 日志输出示例

### ES 检索服务日志示例

```
2024-01-15 10:30:15 INFO ES检索请求 - 用户ID: user_123, 关键词: ['头痛', '发热'], 就诊人: ['PATIENT_001'], 科室: 神经内科, 记录类型: None, 返回数量: 10
2024-01-15 10:30:15 INFO 添加用户权限过滤条件 - 用户ID: user_123
2024-01-15 10:30:15 INFO 添加就诊人过滤条件 - 就诊人ID: ['PATIENT_001']
2024-01-15 10:30:15 INFO 添加关键词搜索条件 - 关键词: 头痛 发热
2024-01-15 10:30:15 INFO 添加科室过滤条件 - 科室: 神经内科
2024-01-15 10:30:15 INFO 构建ES查询完成 - 查询条件数量: 4, 索引: medical_records_enhanced
2024-01-15 10:30:15 INFO 开始执行ES搜索 - 索引: medical_records_enhanced, 返回数量: 10
2024-01-15 10:30:15 INFO ES搜索完成 - 总命中数: 15, 最高分数: 2.3456, 返回结果数: 10
2024-01-15 10:30:15 INFO 用户 user_123 检索到 10 条记录
```

### 混合检索服务日志示例

```
2024-01-15 10:30:20 INFO 开始用户中心化混合检索 - 用户ID: user_123, 查询: 头痛症状, 搜索模式: hybrid, 返回数量: 10
2024-01-15 10:30:20 INFO 获取用户 user_123 的就诊人信息...
2024-01-15 10:30:20 INFO 用户就诊人信息获取完成 - 就诊人数量: 2
2024-01-15 10:30:20 INFO 使用指定就诊人: ['PATIENT_001']
2024-01-15 10:30:20 INFO 开始并行执行ES和向量搜索...
2024-01-15 10:30:20 INFO 开始ES搜索 - 用户ID: user_123, 查询: 头痛症状, 就诊人: ['PATIENT_001'], 科室: None
2024-01-15 10:30:20 INFO 开始向量搜索 - 用户ID: user_123, 查询: 头痛症状, 就诊人: ['PATIENT_001']
2024-01-15 10:30:20 INFO 发送ES搜索请求到: http://localhost:8004/search/user-centric
2024-01-15 10:30:20 INFO 发送向量搜索请求到: http://localhost:8005/search/user-centric
2024-01-15 10:30:21 INFO ES搜索成功 - 返回结果数: 8
2024-01-15 10:30:21 INFO 向量搜索成功 - 返回结果数: 6
2024-01-15 10:30:21 INFO 并行搜索完成 - ES结果数: 8, 向量结果数: 6
2024-01-15 10:30:21 INFO 使用混合模式，开始RRF融合...
2024-01-15 10:30:21 INFO 开始RRF混合融合 - ES结果数: 8, 向量结果数: 6, ES权重: 0.60, 向量权重: 0.40
2024-01-15 10:30:21 INFO RRF算法参数 - k值: 60
2024-01-15 10:30:21 INFO 处理ES检索结果...
2024-01-15 10:30:21 INFO 处理向量检索结果...
2024-01-15 10:30:21 INFO RRF分数计算完成 - 唯一文档数: 12
2024-01-15 10:30:21 INFO RRF混合融合完成 - 最终结果数: 12
2024-01-15 10:30:21 INFO 混合结果 1: ID=doc_001, RRF分数=0.016667, 患者=张三
2024-01-15 10:30:21 INFO 用户中心化混合检索完成 - 总耗时: 1.234秒, 最终结果数: 12
```

## 日志配置建议

### 生产环境

- INFO 级别：记录关键检索过程和结果统计
- ERROR 级别：记录所有错误和异常

### 开发/调试环境

- DEBUG 级别：记录详细的查询条件和计算过程
- INFO 级别：记录检索流程和结果
- ERROR 级别：记录错误信息

## 监控和告警

基于新增的日志，可以设置以下监控指标：

1. **检索性能监控**

   - 检索响应时间
   - 检索成功率
   - 结果数量统计

2. **融合算法监控**

   - RRF 融合成功率
   - 融合结果质量
   - 权重配置效果

3. **服务健康监控**

   - ES 服务调用成功率
   - 向量服务调用成功率
   - 服务响应时间

4. **业务指标监控**
   - 用户检索频率
   - 检索结果相关性
   - 就诊人数据访问模式

## 总结

通过添加详细的日志记录，现在可以：

1. **完整追踪检索过程** - 从请求参数到最终结果
2. **监控融合算法性能** - RRF 算法计算过程和结果
3. **诊断检索问题** - 快速定位检索失败原因
4. **优化检索性能** - 基于日志数据优化检索策略
5. **业务分析** - 分析用户检索行为和结果质量

这些日志增强将大大提高系统的可观测性和可维护性。
