# Find Email Skill - Data Sources Integration 功能文档

## 迭代C：扩展数据源集成 ✅ 已完成

### 新增功能

#### 1. 企业信息API集成
- **天眼查 (TianYanCha)** - 中国工商信息查询API
- **企查查 (QiChaCha)** - 中国企业信息查询API
- **功能**：查询企业工商信息、联系人、邮箱等

#### 2. 社交媒体数据源
- **GitHub** - 开源代码托管平台
- **Stack Overflow** - 开发者问答社区
- **功能**：查找技术人员公开信息、邮箱、项目经历

#### 3. 公开数据库查询
- **技术社区数据** - GitHub、Stack Overflow等
- **企业公开信息** - 工商注册信息、联系方式
- **功能**：多源数据聚合，提高查找成功率

#### 4. 智能数据集成
- **自动数据合并** - 合并多个数据源结果
- **置信度排序** - 基于数据源可靠性排序
- **去重处理** - 智能识别重复记录

#### 5. 配置管理
- **灵活的API密钥管理** - 支持文件和环境变量配置
- **数据源开关** - 可启用/禁用特定数据源
- **速率限制** - 避免API调用限制

### 使用示例

#### 基本数据源搜索
```bash
# 启用数据源集成
python3 find_email.py "张伟" "tencent.com" --data-sources

# 深度数据增强
python3 find_email.py "张伟" "tencent.com" --enrich

# 列出可用数据源
python3 find_email.py --list-sources

# 创建配置文件
python3 find_email.py --setup-config
```

#### 批量处理
```bash
# 批量搜索并启用数据源
python3 find_email.py --batch input.csv --data-sources --output-csv results.csv
```

#### 配置管理
```bash
# 创建示例配置
python3 find_email.py --setup-config

# 然后编辑 ~/.find_email/api_keys.json 添加API密钥
```

### 核心组件

#### DataSourceIntegrator 类
```python
class DataSourceIntegrator:
    def initialize_sources(self):
        """初始化所有配置的数据源"""

    def search_person(self, name, company=None, domain=None):
        """跨数据源搜索人员"""

    def search_company(self, company, domain=None):
        """搜索企业信息"""

    def enrich_email_search(self, name, domain):
        """增强邮箱搜索"""
```

#### 数据源基类
```python
class BaseDataSource:
    def search_person(self, name, company=None, domain=None):
        """搜索人员"""

    def search_company(self, company, domain=None):
        """搜索企业"""

class GitHubSource(BaseDataSource):
    """GitHub数据源"""

class TianYanChaSource(BaseDataSource):
    """天眼查数据源"""
```

#### 配置管理
```python
class ConfigManager:
    def get_api_key(self, service):
        """获取API密钥"""

    def is_data_source_enabled(self, source):
        """检查数据源是否启用"""

    def get_enabled_data_sources(self):
        """获取启用的数据源列表"""
```

### 数据源详情

#### 天眼查 (TianYanCha)
- **功能**：中国企业工商信息查询
- **数据**：企业基本信息、联系方式、高管信息
- **API限制**：需要API密钥，速率限制2秒/次
- **使用场景**：查找中国企业高管联系方式

#### 企查查 (QiChaCha)
- **功能**：中国企业信息查询
- **数据**：企业注册信息、电话、邮箱、地址
- **API限制**：需要API密钥，速率限制2秒/次
- **使用场景**：企业背景调查和联系方式获取

#### GitHub
- **功能**：开源开发者信息查询
- **数据**：用户名、公司、公开邮箱、项目经历
- **API限制**：公开API 1秒/次，认证API更高限制
- **使用场景**：技术人员背景调查和技能评估

#### Stack Overflow
- **功能**：开发者社区信息查询
- **数据**：用户名、声誉、技能标签、地理位置
- **API限制**：需要API密钥，1秒/次
- **使用场景**：开发者技能评估和背景了解

### 配置文件格式

#### API密钥配置 (api_keys.json)
```json
{
  "tianyancha": "your_tianyancha_api_key_here",
  "qichacha": "your_qichacha_api_key_here",
  "github": "your_github_personal_access_token",
  "stackoverflow": "your_stackexchange_api_key",
  "hunterio": "your_hunterio_api_key",
  "zerointel": "your_zerointel_api_key",
  "apollo": "your_apollo_api_key"
}
```

#### 主配置 (config.json)
```json
{
  "data_sources": {
    "tianyancha": {
      "enabled": true,
      "rate_limit": 2.0
    },
    "qichacha": {
      "enabled": true,
      "rate_limit": 2.0
    },
    "github": {
      "enabled": true,
      "rate_limit": 1.0
    },
    "stackoverflow": {
      "enabled": true,
      "rate_limit": 1.0
    }
  },
  "verification": {
    "dnsbl_check": true,
    "smtp_timeout": 10,
    "max_retries": 3
  },
  "ai_learning": {
    "enabled": true,
    "history_limit": 1000,
    "auto_learn": true
  }
}
```

### 数据模型

#### 人员搜索结果
```json
{
  "source": "github",
  "type": "person",
  "name": "John Smith",
  "login": "johnsmith",
  "company": "Microsoft",
  "email": "john.smith@microsoft.com",
  "blog": "https://johnsmith.dev",
  "location": "Seattle, WA",
  "public_repos": 42,
  "confidence": 0.7
}
```

#### 企业搜索结果
```json
{
  "source": "tianyancha",
  "type": "company",
  "name": "腾讯科技",
  "credit_code": "91440300708461136T",
  "phone": "0755-86013388",
  "email": "contact@tencent.com",
  "website": "https://www.tencent.com",
  "address": "深圳市南山区",
  "confidence": 0.8
}
```

### 增强功能

#### 智能数据合并
```python
# 自动合并多个数据源的结果
enrichment = integrator.enrich_email_search(name, domain)
# 返回包含建议邮箱和置信度提升的数据
```

#### 置信度计算
- **数据源权重**：不同数据源有不同的基础权重
- **数据质量**：完整度、准确性影响最终置信度
- **交叉验证**：多个数据源确认同一信息时提升置信度

#### 错误处理
- **API错误**：优雅处理API调用失败
- **网络超时**：合理超时设置和重试机制
- **数据解析**：处理不同API的响应格式差异

### 性能优化

#### 速率限制
- **自动限流**：遵守各API的速率限制
- **并发控制**：并行请求多个数据源
- **缓存机制**：避免重复查询相同信息

#### 数据缓存
- **结果缓存**：缓存查询结果减少API调用
- **配置缓存**：缓存配置信息提高启动速度
- **历史记录**：保存搜索历史用于AI学习

### 安全考虑

#### API密钥管理
- **加密存储**：API密钥本地加密存储
- **环境变量**：支持通过环境变量配置密钥
- **权限控制**：最小权限原则使用API

#### 隐私保护
- **公开数据**：仅查询公开可用信息
- **数据最小化**：只收集必要信息
- **使用条款**：遵守各平台使用条款

### 测试结果

数据源集成功能已通过完整测试：
- ✅ 天眼查API集成
- ✅ 企查查API集成  
- ✅ GitHub数据查询
- ✅ Stack Overflow集成
- ✅ 配置管理系统
- ✅ 智能数据合并
- ✅ 错误处理机制
- ✅ 性能优化

### 使用场景

#### 销售/BD场景
- **场景**：寻找目标企业决策者联系方式
- **优势**：结合工商信息和技术社区数据
- **使用**：`--enrich` 模式获取全面信息

#### 招聘/猎头场景
- **场景**：查找候选人背景信息
- **优势**：GitHub等技术社区数据验证技能
- **使用**：`--data-sources` 搜索技术背景

#### 安全研究场景
- **场景**：企业信息收集和OSINT
- **优势**：多源数据交叉验证提高准确性
- **使用**：组合使用多个数据源

#### 市场研究场景
- **场景**：竞争对手分析和行业研究
- **优势**：企业工商信息提供组织架构
- **使用**：批量处理模式分析多个目标

### 最佳实践

1. **API密钥安全**：妥善保管API密钥，不要提交到版本控制
2. **合理使用**：遵守各平台使用条款，避免过度请求
3. **数据验证**：多渠道验证重要联系信息的准确性
4. **隐私尊重**：仅用于合法合规的商业用途
5. **错误处理**：准备好处理API限制和网络错误

### 下一步计划

完成迭代C后，接下来的开发重点：
1. **用户体验优化** - Web界面和RESTful API
2. **高级AI功能** - 深度学习模式识别
3. **更多数据源** - 微博、LinkedIn等社交媒体
4. **企业部署** - Docker容器化和集群支持

---

*文档更新时间：2026-04-23*
*版本：v1.3.0*