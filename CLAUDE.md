# Find Email Skill

通过姓名和公司域名查找、验证邮件地址。

## 项目结构

```
find-email/
├── SKILL.md              # 技能定义文件
├── CLAUDE.md             # 本文件
├── config/
│   └── patterns.json     # 50+ 邮件格式模式库
├── lib/
│   ├── __init__.py       # 包导出
│   ├── chinese.py        # 中文名字转拼音
│   ├── generator.py      # 邮件候选生成
│   ├── scorer.py         # 置信度评分
│   └── verifier.py       # 多方法验证（Gravatar/SMTP/GitHub）
├── find_email.py         # CLI 工具
└── test/
    └── test_email.py     # 测试套件
```

## 依赖

```bash
pip3 install pypinyin dnspython
```

## 测试

```bash
python3 test/test_email.py
python3 find_email.py "张伟" tencent.com
python3 find_email.py "David Zhang" alibaba.com --english
```

## 验证命令

```bash
# 无验证模式（快速生成候选）
python3 find_email.py "张伟" tencent.com --no-verify

# JSON 输出
python3 find_email.py "张伟" tencent.com --output json

# 已知公司邮件格式模式
python3 find_email.py "张伟" tencent.com --pattern firstname.lastname

# 可能存在重名
python3 find_email.py "张伟" tencent.com --has-duplicate
```

## 核心模块

| 模块 | 职责 |
|------|------|
| `chinese.py` | 中文名字转拼音（pypinyin + 100+ 姓氏映射） |
| `generator.py` | 生成 50+ 邮件格式候选 |
| `verifier.py` | Gravatar / SMTP / GitHub 多方法验证 |
| `scorer.py` | 置信度评分（高>85% / 中60-85% / 低30-60%） |

## 邮件格式模式

- **英文名字**: first.last, firstlast, flast, f.last, first_last, first-last
- **中文拼音**: zhang.wei, zhangwei, wei.zhang, zw, zwang
- **重名后缀**: zhang.wei01, zhangwei1, zhang.wei.1
- **年份后缀**: zhangwei1990, zhangwei90
- **部门邮箱**: first.last@dept.company.com
