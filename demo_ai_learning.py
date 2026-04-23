#!/usr/bin/env python3
"""
Find Email Skill - AI Learning 演示

展示迭代B新增的AI驱动模式学习功能：
- 历史数据分析
- 智能模式学习
- 公司特定模式识别
- 置信度优化
"""

import sys
import json
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.ai_pattern_learner import AIPatternLearner
from lib.history_analyzer import HistoryAnalyzer

def demo_ai_learning():
    print("🤖 Find Email Skill - AI Learning 演示")
    print("=" * 60)

    # Initialize components
    analyzer = HistoryAnalyzer()
    learner = AIPatternLearner()

    # Ensure we have sample data
    if not analyzer.history_file.exists():
        import shutil
        sample_file = Path(__file__).parent / 'data' / 'sample_history.json'
        if sample_file.exists():
            shutil.copy(sample_file, analyzer.history_file)
            print("📊 加载示例历史数据...")

    print("\n🔍 历史数据分析")
    print("-" * 30)

    # Pattern success rate analysis
    pattern_analysis = analyzer.analyze_pattern_success_rate()
    print("📈 模式成功率分析:")
    if pattern_analysis:
        for pattern, stats in sorted(pattern_analysis.items(),
                                   key=lambda x: x[1]['success_rate'],
                                   reverse=True):
            print(f"  {pattern}: {stats['success_rate']:.1%} "
                  f"({stats['success_count']}/{stats['total_count']})")
    else:
        print("  暂无历史数据")

    # Company pattern analysis
    company_analysis = analyzer.analyze_company_patterns()
    print(f"\n🏢 公司模式分析:")
    if company_analysis:
        for domain, analysis in company_analysis.items():
            print(f"  {domain}:")
            print(f"    记录数: {analysis['total_records']}")
            if analysis['successful_patterns']:
                print(f"    成功模式: {', '.join(analysis['successful_patterns'])}")
            if analysis['most_common_pattern']:
                print(f"    最常用: {analysis['most_common_pattern']}")
    else:
        print("  暂无公司数据")

    # Name pattern analysis
    name_analysis = analyzer.analyze_name_patterns()
    print(f"\n👤 姓名类型分析:")
    for name_type, analysis in name_analysis.items():
        if analysis['group_size'] > 0:
            print(f"  {name_type}: {analysis['group_size']} 条记录")
            if analysis['top_patterns']:
                top_pattern = analysis['top_patterns'][0]
                print(f"    最佳模式: {top_pattern[0]} "
                      f"(成功率: {top_pattern[1]['success_rate']:.1%})")

    # Generate insights
    insights = analyzer.generate_insights()
    print(f"\n💡 智能洞察:")
    for insight in insights['insights']:
        print(f"  • {insight}")

    print(f"\n🎯 推荐建议:")
    for rec in insights['recommendations']:
        print(f"  📋 {rec}")

    # Demonstrate pattern learning
    print(f"\n🧠 AI模式学习演示")
    print("-" * 30)

    # Learn company patterns
    test_domains = ['tencent.com', 'microsoft.com', 'google.com']

    for domain in test_domains:
        if domain in company_analysis:
            print(f"\n🏢 学习 {domain} 的模式:")

            # Simulate learning from known emails
            known_emails = []
            names = []

            # Get some sample data from history
            history = analyzer.load_history()
            domain_records = [r for r in history if r.get('domain') == domain]

            if len(domain_records) >= 2:
                for record in domain_records[:3]:
                    if record.get('is_valid'):
                        known_emails.append(record['email'])
                        names.append(record['name'])

                if len(known_emails) >= 2:
                    learned_patterns = learner.learn_company_pattern(
                        domain, known_emails, names
                    )

                    print(f"  已知邮箱: {', '.join(known_emails)}")
                    print(f"  学习到的模式:")
                    for pattern, confidence in learned_patterns.items():
                        print(f"    {pattern}: {confidence:.1%} 置信度")

    # Demonstrate smart candidate generation
    print(f"\n🎯 智能候选生成演示")
    print("-" * 30)

    # Import generator for demo
    from lib.generator import generate_candidates

    test_cases = [
        ("张伟", "tencent.com"),
        ("John Smith", "microsoft.com"),
        ("李娜", "alibaba.com")
    ]

    for name, domain in test_cases:
        print(f"\n🔍 {name} @ {domain}:")

        # Generate base candidates
        base_candidates = generate_candidates(name, domain, has_duplicate=False)[:5]

        # Apply AI learning
        smart_candidates = learner.generate_smart_candidates(
            name, domain, base_candidates
        )

        print("  基础候选 → AI优化候选:")
        for i, (base, smart) in enumerate(zip(base_candidates, smart_candidates)):
            priority_change = smart['priority'] - base.get('priority', 3)
            change_symbol = "⬆️" if priority_change < 0 else "⬇️" if priority_change > 0 else "➡️"

            print(f"    {i+1}. {base['email']}")
            print(f"       优先级: {base.get('priority', 3)} → {smart['priority']} {change_symbol}")

            if smart.get('pattern_confidence', 0) > 0:
                print(f"       🎯 模式置信度: {smart['pattern_confidence']:.2f}")

    print("\n" + "=" * 60)
    print("🎓 AI Learning 功能总结:")
    print("  ✅ 历史数据分析 - 从验证历史中学习成功模式")
    print("  ✅ 公司模式识别 - 自动学习特定公司的邮箱规则")
    print("  ✅ 智能候选排序 - 基于学习结果优化候选优先级")
    print("  ✅ 实时学习 - 每次验证都改进模式库")
    print("\n📚 详细文档请查看: AI_LEARNING.md")

if __name__ == "__main__":
    demo_ai_learning()