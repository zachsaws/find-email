# Find Email - 智能邮件查找工具

通过姓名和公司域名，快速猜测并验证可能的企业邮箱地址。

## 核心能力

| 功能 | 说明 |
|------|------|
| **50+ 格式候选** | 覆盖中文拼音、英文名、重名后缀、年份后缀等所有常见格式 |
| **多方法验证** | Gravatar + GitHub + SMTP 三重验证，只返回高置信度结果 |
| **中文名字优化** | pypinyin 转拼音 + 100+ 常见姓氏映射，无惧生僻字 |
| **重名自动处理** | 张伟01 / 张伟02 格式，避免同名混淆 |

## 安装

```bash
pip3 install pypinyin dnspython
git clone https://github.com/zachsaws/find-email.git
cd find-email
```

## 快速开始

```bash
# 中文名字
python3 find_email.py "张伟" tencent.com

# 英文名字
python3 find_email.py "David Zhang" alibaba.com --english

# 仅生成候选，不验证（速度更快）
python3 find_email.py "张伟" tencent.com --no-verify

# 已知公司邮件格式
python3 find_email.py "张伟" tencent.com --pattern firstname.lastname

# 可能存在重名
python3 find_email.py "张伟" tencent.com --has-duplicate

# JSON 输出（便于程序调用）
python3 find_email.py "张伟" tencent.com --output json
```

## 输出示例

```
Email candidates for 张伟 @ tencent.com

✅ zhang.wei@tencent.com (85% - SMTP verified, common format)
⚠️ david.zhang@alibaba.com (60% - Gravatar match)
❌ zhang.wei01@tencent.com (0% - no MX records)

Total candidates: 50
```

## 技术原理

### 候选生成（50+ 格式）

```
基础格式:     first.last / firstlast / flast / f.last / first_last / first-last
中文拼音:     zhang.wei / zhangwei / wei.zhang / zwei / zwe
重名后缀:     zhang.wei01 / zhangwei1 / zhang.wei.1
年份后缀:     zhang.wei1990 / zhang.wei90
部门格式:     zhang.wei@dept.company.com
```

### 验证流程

```
1. 语法检查        → 过滤无效格式
2. MX 记录检查     → 确认域名可收邮件
3. Gravatar 检查  → MD5 哈希 → gravatar.com 头像查询
4. GitHub 搜索    → 公开 commit 中是否使用此邮箱
5. SMTP 验证      → 连接邮件服务器确认邮箱存在
```

### 置信度等级

| 等级 | 分值 | 依据 |
|------|------|------|
| ✅ 高 | >85% | SMTP 验证通过 或 多重 HTTP 验证 |
| ⚠️ 中 | 60-85% | Gravatar/GitHub 任一匹配 |
| ⚠️ 低 | 30-60% | 仅模式匹配，无验证 |
| ❌ 无 | <30% | 验证失败或域名异常 |

### 关键技术细节

**中文名字处理**：
- pypinyin 库转换汉字 → 拼音（自动处理多音字）
- 100+ 常见姓氏人工映射（如 张 → zhang，不是 zhangsan）
- 生成全格式变体：`zhang.wei` / `zhangwei` / `wei.zhang` / `zwei`

**Catch-all 检测**：
- 部分企业邮件服务器接受所有发往该域名的邮件（catch-all）
- 验证前先向 `random@domain.com` 测试，确认真实性

**SMTP 端口自适应**：
- 自动尝试 587 → 465 → 25 三个常用端口
- 跳过被 ISP 封堵的 25 端口，避免长时间等待

## 项目结构

```
find-email/
├── SKILL.md              # Claude Code Skill 定义
├── README.md              # 本文档
├── CLAUDE.md              # 开发说明
├── config/
│   └── patterns.json     # 50+ 邮件格式模式库
├── lib/
│   ├── __init__.py
│   ├── chinese.py         # 中文 → 拼音转换
│   ├── generator.py       # 候选生成引擎
│   ├── verifier.py        # 三重验证（Gravatar/SMTP/GitHub）
│   └── scorer.py          # 置信度评分
├── find_email.py          # CLI 入口
└── test/
    └── test_email.py      # 测试套件
```

## 测试

```bash
python3 test/test_email.py
```

## 适用场景

- **销售/BD**：快速找到目标企业联系人邮箱
- **招聘/猎头**：查找目标公司候选人联系方式
- **安全研究**：企业信息收集（OSINT）
- **AI 应用**：作为 MCP tool 嵌入其他 AI agent

## 局限性

- Gmail / QQ 等个人邮箱域名无法预测（需要其他数据源）
- SMTP 验证在部分网络环境下可能较慢（25 端口常被封）
- Gravatar 覆盖率约 30%（技术人群），非技术人群可能漏检

## License

MIT