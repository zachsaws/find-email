#!/usr/bin/env python3
"""
Find Email Skill - 增强功能演示

展示迭代A新增的增强验证功能：
- DNSBL黑名单检查
- 企业邮箱识别
- 增强SMTP验证
- 改进的置信度评分
"""

import sys
import time
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.generator import generate_candidates
from lib.verifier import EmailVerifier
from lib.scorer import ConfidenceScorer

def demo_enhanced_features():
    print("🔍 Find Email Skill - 增强功能演示")
    print("=" * 60)

    # Test cases
    test_cases = [
        ("张伟", "gmail.com", "Google Workspace邮箱"),
        ("test", "example.com", "普通域名测试"),
        ("admin", "spamdomain.com", "黑名单域名测试")
    ]

    verifier = EmailVerifier()
    scorer = ConfidenceScorer()

    for name, domain, description in test_cases:
        print(f"\n📧 测试案例: {name} @ {domain} ({description})")
        print("-" * 50)

        # Generate candidates
        candidates = generate_candidates(name, domain, has_duplicate=False)[:5]  # 限制显示数量

        for candidate in candidates:
            email = candidate['email']
            print(f"\n🔍 验证邮箱: {email}")

            # Verify with enhanced methods
            verification = verifier.verify(email)

            # Display verification methods
            methods = verification.get('methods', {})
            print(f"  验证方法结果:")
            for method, result in methods.items():
                if method == 'dnsbl':
                    status = "❌ 黑名单" if result else "✅ 清洁"
                elif method == 'server_type':
                    status = f"🏢 {result}" if result else "❓ 未知"
                elif method == 'mx':
                    status = "✅ 有MX记录" if result else "❌ 无MX记录"
                elif method == 'gravatar':
                    status = "✅ 有头像" if result else "❌ 无头像"
                elif method == 'github':
                    status = "✅ GitHub匹配" if result else "❌ 无匹配"
                elif method == 'smtp':
                    status = f"📧 {result}" if result else "❌ 无SMTP"
                else:
                    status = str(result)
                print(f"    {method}: {status}")

            # Score and display
            scored = scorer.score(verification, candidate.get('priority', 2))
            print(f"  置信度: {scored['score']}% ({scored['level']})")
            print(f"  因素: {', '.join(scored['factors'])}")

            time.sleep(0.5)  # 演示间隔

    print("\n" + "=" * 60)
    print("🎯 增强功能总结:")
    print("  ✅ DNSBL黑名单检查 - 过滤垃圾邮件域名")
    print("  ✅ 企业邮箱识别 - 智能识别主流企业邮箱服务")
    print("  ✅ 增强SMTP验证 - 多端口重试，更可靠")
    print("  ✅ 改进置信度评分 - 综合考虑多种因素")
    print("\n📚 详细文档请查看: ENHANCEMENTS.md")

if __name__ == "__main__":
    demo_enhanced_features()