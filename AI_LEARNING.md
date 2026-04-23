# Find Email Skill - AI Learning 功能文档

## 迭代B：智能模式学习 ✅ 已完成

### 新增功能

#### 1. 历史数据分析
- **功能**：分析历史邮箱验证数据，识别成功模式
- **数据源**：自动记录每次验证结果
- **分析维度**：
  - 模式成功率统计
  - 公司特定模式
  - 姓名类型分析（中文/英文）
  - 趋势分析

#### 2. AI模式学习
- **功能**：基于机器学习自动学习邮箱模式
- **学习能力**：
  - 从成功验证中学习有效模式
  - 识别公司特定的邮箱命名规则
  - 动态调整模式权重
  - 实时学习新的验证结果

#### 3. 智能候选生成
- **功能**：基于学习结果优化候选邮箱排序
- **优化策略**：
  - 高成功率模式优先
  - 公司特定模式加权
  - 历史成功率影响排序
  - 动态优先级调整

#### 4. 实时洞察
- **功能**：提供数据驱动的洞察和建议
- **洞察类型**：
  - 最佳实践推荐
  - 模式优化建议
  - 公司模式识别
  - 成功率趋势分析

### 使用示例

#### 基本AI学习
```bash
# 启用AI学习模式
python3 find_email.py "张伟" "company.com" --ai-learn

# 分析历史数据
python3 find_email.py --analyze-history

# 从历史中学习模式
python3 find_email.py "张伟" "company.com" --learn-from-history
```

#### 批量处理与学习
```bash
# 批量处理并记录学习数据
python3 find_email.py --batch input.csv --ai-learn

# 导出分析报告
python3 -c "
from lib.history_analyzer import HistoryAnalyzer
analyzer = HistoryAnalyzer()
analyzer.export_analysis_report('email_analysis.json')
"
```

### 核心组件

#### AIPatternLearner 类
```python
class AIPatternLearner:
    def record_verification(self, name, domain, email, pattern, is_valid, confidence):
        """记录验证结果用于学习"""

    def learn_company_pattern(self, domain, known_emails, names):
        """学习公司特定模式"""

    def generate_smart_candidates(self, name, domain, base_candidates):
        """生成智能候选邮箱"""

    def get_learning_stats(self):
        """获取学习统计"""
```

#### HistoryAnalyzer 类
```python
class HistoryAnalyzer:
    def analyze_pattern_success_rate(self, days=30):
        """分析模式成功率"""

    def analyze_company_patterns(self, min_samples=3):
        """分析公司模式"""

    def analyze_name_patterns(self):
        """分析姓名类型模式"""

    def generate_insights(self):
        """生成智能洞察"""

    def export_analysis_report(self, output_file):
        """导出分析报告"""
```

### 数据模型

#### 验证历史记录
```json
{
  "timestamp": "2026-04-20T10:00:00",
  "name": "张伟",
  "domain": "tencent.com",
  "email": "zhang.wei@tencent.com",
  "pattern": "{first}.{last}",
  "is_valid": true,
  "confidence": "high"
}
```

#### 学习到的公司模式
```json
{
  "tencent.com": {
    "patterns": {
      "{first}.{last}": 1.0,
      "{first}{last}": 0.0
    },
    "sample_size": 5,
    "last_updated": "2026-04-20T10:00:00"
  }
}
```

### 学习算法

#### 模式权重计算
```python
# 基于成功率和样本量计算权重
weight = success_rate * min(1.0, total_samples / 10)
```

#### 公司模式学习
```python
# 从已知邮箱中提取模式
pattern = extract_pattern(email, name)
# 计算模式频率和置信度
confidence = pattern_frequency / total_patterns
```

#### 候选排序优化
```python
# 综合多个因素调整优先级
final_priority = base_priority - pattern_confidence * 2 - global_weight * 1.5
```

### 性能优化

#### 数据管理
- **历史记录限制**：只保留最近1000条记录
- **模式缓存**：缓存学习到的公司模式
- **增量学习**：新数据不影响已有学习结果

#### 分析效率
- **快速分析**：基于聚合数据的快速分析
- **批量处理**：支持批量历史数据分析
- **报告导出**：一键导出完整分析报告

### 测试结果

AI学习功能已通过完整测试：
- ✅ 历史数据加载和分析
- ✅ 模式成功率统计
- ✅ 公司模式学习
- ✅ 智能候选生成
- ✅ 实时学习更新
- ✅ 洞察生成和推荐

### 使用场景

#### 销售/BD场景
- **场景**：快速找到目标企业联系人
- **优势**：学习行业特定模式，提高成功率
- **使用**：`--ai-learn` 模式批量处理

#### 招聘/猎头场景
- **场景**：查找候选人联系方式
- **优势**：学习公司邮箱规则，精准定位
- **使用**：`--analyze-history` 分析目标公司

#### 安全研究场景
- **场景**：企业信息收集（OSINT）
- **优势**：智能模式识别，减少无效尝试
- **使用**：`--learn-from-history` 持续优化

### 最佳实践

1. **持续使用**：越多的验证数据，AI学习效果越好
2. **定期分析**：使用 `--analyze-history` 定期查看洞察
3. **公司学习**：对常用公司使用 `--ai-learn` 学习特定模式
4. **批量处理**：大量数据时使用批量模式提高效率

### 下一步计划

完成迭代B后，接下来的开发重点：
1. **迭代C：扩展数据源集成** - 集成企业信息API、社交媒体数据
2. **用户体验优化** - Web界面和API服务
3. **高级AI功能** - 深度学习模式识别、预测模型

---

*文档更新时间：2026-04-23*
*版本：v1.2.0*