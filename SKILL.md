# Find Email Skill

Given a person's name and company domain, find and verify their possible email addresses.

## Usage

```
用户：找一个邮箱
助手：好的，请提供以下信息：
- 姓名（中文或英文）：张三
- 公司域名：company.com
- （可选）英文名：David

助手将输出猜测的邮箱列表和验证状态。
```

## Core Workflow

### Phase 1: Generate Email Candidates

Generate 50+ email format variants from a name:

1. **Chinese name processing** (e.g., "张三" → zhangsan, zhang.san, etc.)
2. **English name variants** (e.g., "David Zhang" → david.zhang, d.zhang, etc.)
3. **Number suffixes for duplicates** (e.g., zhangsan01, zhangsan02)
4. **Year suffixes** (e.g., zhangsan1990, zhangsan90)
5. **Department/counter formats** (e.g., zhang.san.it, zhangsan2)

### Phase 2: Verify Candidates

For each candidate, run through verification pipeline:

1. **Syntax check** - Valid email format
2. **MX record check** - Domain can receive email
3. **HTTP verification** (parallel):
   - Gravatar check (md5 hash → gravatar.com avatar exists)
   - GitHub public email search (commits API)
4. **SMTP verification** (if HTTP failed):
   - Detect catch-all domains first
   - Try ports: 587 → 465 → 25
   - Retry with exponential backoff (greylisting handling)

### Phase 3: Confidence Scoring

Score each email:
- **High (>85%)**: Multiple verifications passed (e.g., SMTP + Gravatar)
- **Medium (60-85%)**: One strong verification (e.g., SMTP passes, or Gravatar matches)
- **Low (30-60%)**: Pattern match only, unverified
- **Rejected**: Syntax invalid or domain doesn't exist

## Technical Details

### Email Format Patterns

The skill uses a comprehensive pattern library including:

- `{first}.{last}` - david.zhang
- `{first}{last}` - davidzhang
- `{f}{last}` - dzhang
- `{f}.{last}` - d.zhang
- `{first}_{last}` - david_zhang
- Chinese: `{pinyin_first}{pinyin_last}` - zhangsan
- With numbers: `{first}{last}01` - davidzhang01
- With year: `{first}{last}85` - davidzhang85

### Chinese Name Handling

1. Convert Chinese characters to pinyin (using pypinyin or similar)
2. Generate all common pinyin format variants
3. Handle surname-first vs given-name-first conventions
4. Generate duplicate-safe formats with 01/02 suffixes

### Verification Methods

| Method | Accuracy | Speed | Port Dependencies |
|--------|----------|-------|-------------------|
| Gravatar | ~30% coverage | Fast | None |
| GitHub | ~20% (tech users) | Medium | None |
| SMTP | ~95% if works | Slow | Port 25/587/465 |
| MX check | 100% | Fast | None |

### Catch-All Detection

Before trusting SMTP results, detect if domain accepts all mail:
1. Send RCPT TO to random invalid address
2. If accepts → catch-all (unreliable verification)
3. If rejects → individual verification works

## File Structure

```
find-email/
├── SKILL.md           # This file
├── README.md          # Detailed documentation
├── config/
│   └── patterns.json  # Email format patterns
├── lib/
│   ├── generator.py   # Email candidate generation
│   ├── verifier.py    # Multi-method verification
│   ├── chinese.py     # Chinese name → pinyin
│   └── scorer.py      # Confidence scoring
└── test/
    └── test_email.py  # Test cases
```

## Examples

### Example 1: Basic Chinese name

**Input**:
- Name: 张伟
- Domain: tencent.com

**Output**:
```
Candidates for 张伟 @ tencent.com:

✅ zhang.wei@tencent.com (High confidence)
   - SMTP: verified
   - Pattern: first.last format

⚠️ zhangwei@tencent.com (Medium confidence)
   - Gravatar: match found
   - Pattern: full pinyin

❌ zhangwei01@tencent.com (Low confidence)
   - No verification
   - Pattern: duplicate format
```

### Example 2: English name with domain knowledge

**Input**:
- Name: Daniel Zhang
- Domain: alibaba.com
- Company pattern learned: firstname.lastname

**Output**:
```
Candidates for Daniel Zhang @ alibaba.com:

✅ daniel.zhang@alibaba.com (High confidence)
   - SMTP: verified
   - Learned pattern: firstname.lastname
   - English name confirmed

✅ d.zhang@alibaba.com (Medium confidence)
   - Gravatar: match found
```

### Example 3: Duplicate handling

**Input**:
- Name: 张伟
- Domain: company.com
- Evidence: Two "张伟" in company

**Output**:
```
Candidates for 张伟 @ company.com:

✅ zhang.wei@company.com (High confidence)
   - SMTP: verified
   - No duplicate suffix needed

✅ zhang.wei01@company.com (Medium confidence)
   - SMTP: verified
   - Format indicates duplicate handling

⚠️ zhang.wei02@company.com (Low confidence)
   - Pattern: second duplicate
   - Unverified
```

## Allowed Tools

- Read, Write, Edit, Glob, Grep - File operations
- Bash - Running Python scripts, installing packages
- WebFetch - Checking external APIs (Gravatar, GitHub)

## Notes

- SMTP verification often fails due to port 25 blocking by ISPs. Use HTTP-based methods (Gravatar, GitHub) as primary when available.
- For Chinese corporate emails, prefer pinyin-based formats over English name formats unless company is known to use English names.
- Always check for catch-all domains before trusting SMTP "accept" results.
- Rate limit GitHub API to avoid being blocked (max 60 requests/hour for unauthenticated).