#!/usr/bin/env python3
"""
Find Email Skill - Data Sources Integration 演示

展示迭代C新增的外部数据源集成功能：
- 企业信息API集成（天眼查、企查查）
- 社交媒体数据源（GitHub、Stack Overflow）
- 公开数据库查询
- 自定义数据源支持
"""

import sys
import json
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.data_sources import DataSourceIntegrator, GitHubSource, StackOverflowSource
from lib.config_manager import ConfigManager

def demo_data_sources():
    print("🌐 Find Email Skill - Data Sources Integration 演示")
    print("=" * 70)

    # Initialize configuration
    config_manager = ConfigManager()
    print("📋 配置管理:")
    print(f"  配置文件目录: {config_manager.config_dir}")
    print(f"  启用的数据源: {', '.join(config_manager.get_enabled_data_sources())}")

    # Initialize data integrator
    integrator = DataSourceIntegrator()
    integrator.initialize_sources()

    print(f"\n🔌 已启用的数据源 ({len(integrator.sources)}):")
    for name, source in integrator.sources.items():
        print(f"  ✅ {name}: {source.__class__.__name__}")

    # Test cases
    test_cases = [
        {
            'name': '张伟',
            'company': '腾讯',
            'domain': 'tencent.com',
            'description': '中文企业高管搜索'
        },
        {
            'name': 'John Smith',
            'company': 'Microsoft',
            'domain': 'microsoft.com',
            'description': '英文技术专家搜索'
        },
        {
            'name': 'Linus Torvalds',
            'company': 'Linux Foundation',
            'domain': 'linux.org',
            'description': '开源社区领袖搜索'
        }
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n🔍 测试案例 {i}: {case['description']}")
        print("-" * 50)
        print(f"  姓名: {case['name']}")
        print(f"  公司: {case['company']}")
        print(f"  域名: {case['domain']}")

        # Search for person
        print(f"\n  👤 人员搜索:")
        person_results = integrator.search_person(
            case['name'], case['company'], case['domain']
        )

        if person_results:
            for j, result in enumerate(person_results[:3], 1):  # Show top 3
                print(f"    {j}. {result.get('name', 'N/A')}")
                if result.get('company'):
                    print(f"       公司: {result['company']}")
                if result.get('position'):
                    print(f"       职位: {result['position']}")
                if result.get('email'):
                    print(f"       邮箱: {result['email']}")
                if result.get('login'):
                    print(f"       用户名: {result['login']}")
                print(f"       来源: {result['source']} (置信度: {result.get('confidence', 0):.2f})")
                print()
        else:
            print("    ❌ 未找到相关记录")

        # Search for company
        print(f"  🏢 企业搜索:")
        company_results = integrator.search_company(
            case['company'], case['domain']
        )

        if company_results:
            for j, result in enumerate(company_results[:2], 1):  # Show top 2
                print(f"    {j}. {result.get('name', 'N/A')}")
                if result.get('website'):
                    print(f"       网站: {result['website']}")
                if result.get('email'):
                    print(f"       邮箱: {result['email']}")
                if result.get('phone'):
                    print(f"       电话: {result['phone']}")
                if result.get('address'):
                    print(f"       地址: {result['address']}")
                print(f"       来源: {result['source']} (置信度: {result.get('confidence', 0):.2f})")
                print()
        else:
            print("    ❌ 未找到相关企业记录")

        # Enrichment example
        print(f"  🎯 搜索增强:")
        enrichment = integrator.enrich_email_search(case['name'], case['domain'])

        if enrichment['suggested_emails']:
            print(f"    发现的邮箱 ({len(enrichment['suggested_emails'])}):")
            for email_info in enrichment['suggested_emails'][:3]:
                print(f"      📧 {email_info['email']} "
                      f"({email_info['source']}, 置信度: {email_info['confidence']:.2f})")
        else:
            print("    📧 未发现直接邮箱")

        print(f"    置信度提升: +{enrichment['confidence_boost']:.2f}")

    # Demonstrate GitHub source specifically
    print(f"\n🐙 GitHub 数据源演示")
    print("-" * 50)

    github = GitHubSource()
    github_results = github.search_person("John Doe", "Tech Corp")

    print(f"GitHub 搜索示例 (John Doe):")
    if github_results:
        for result in github_results[:2]:
            print(f"  👤 {result.get('name')}")
            print(f"     用户名: {result.get('login')}")
            print(f"     公司: {result.get('company')}")
            print(f"     公开仓库: {result.get('public_repos')}")
            print()
    else:
        print("  模拟数据: 需要GitHub API密钥才能获取真实数据")

    # Configuration demo
    print(f"\n⚙️ 配置管理演示")
    print("-" * 50)

    # Create sample configs
    sample_config = config_manager.create_sample_config()
    sample_keys = config_manager.create_sample_api_keys()

    print(f"📁 示例配置文件已创建:")
    print(f"  配置: {sample_config}")
    print(f"  API密钥: {sample_keys}")

    print(f"\n🔧 配置选项:")
    print(f"  数据源开关: 可启用/禁用特定数据源")
    print(f"  速率限制: 控制API调用频率")
    print(f"  API密钥: 支持文件配置和环境变量")

    # Performance considerations
    print(f"\n⚡ 性能考虑")
    print("-" * 50)
    print("  ✅ 速率限制: 避免API限制")
    print("  ✅ 错误处理: 优雅处理API错误")
    print("  ✅ 并行查询: 多个数据源并发查询")
    print("  ✅ 结果缓存: 避免重复查询")

    print(f"\n🔒 隐私和安全")
    print("-" * 50)
    print("  ✅ API密钥加密存储")
    print("  ✅ 仅查询公开数据")
    print("  ✅ 遵守各平台使用条款")
    print("  ✅ 可配置的数据源开关")

    print("\n" + "=" * 70)
    print("🎓 数据源集成功能总结:")
    print("  ✅ 企业信息API - 天眼查、企查查等工商信息")
    print("  ✅ 社交媒体数据 - GitHub、Stack Overflow等平台")
    print("  ✅ 公开数据库 - 技术社区和开源项目")
    print("  ✅ 智能集成 - 自动合并和排序多源数据")
    print("  ✅ 配置管理 - 灵活的API密钥和设置管理")
    print("\n📚 详细文档请查看: DATA_SOURCES.md")

if __name__ == "__main__":
    demo_data_sources()