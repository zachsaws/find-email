#!/usr/bin/env python3
"""
Find email from name - CLI tool.

Usage:
    python find_email.py "张伟" tencent.com
    python find_email.py "David Zhang" alibaba.com --english
    python find_email.py "张伟" company.com --has-duplicate
"""

import sys
import json
import argparse
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.generator import generate_candidates, generate_from_known_pattern
from lib.api_providers import EmailVerifier
from lib.scorer import ConfidenceScorer, format_candidate_list
from lib.chinese import chinese_to_pinyin, is_chinese_name
from lib.api_providers import HunterioProvider, ZeroIntelProvider, ApolloProvider
from lib.pattern_learner import PatternLearner, PatternCache
from lib.linkedin import scrape_linkedin_profile
from lib.batch import ResultCache, read_csv_input, write_csv_output
from lib.fast_verifier import FastVerifier
from lib.ai_pattern_learner import AIPatternLearner
from lib.history_analyzer import HistoryAnalyzer
from lib.data_sources import DataSourceIntegrator
from lib.config_manager import ConfigManager


def main():
    parser = argparse.ArgumentParser(description='Find email from name and domain')
    parser.add_argument('name', nargs='?', help='Person name (Chinese or English)')
    parser.add_argument('domain', nargs='?', help='Company domain (e.g., tencent.com)')
    parser.add_argument('--english-first', help='English first name')
    parser.add_argument('--english-last', help='English last name')
    parser.add_argument('--has-duplicate', action='store_true', help='Name may have duplicates')
    parser.add_argument('--department', help='Department for departmental emails')
    parser.add_argument('--pattern', help='Known company email pattern (e.g., firstname.lastname)')
    parser.add_argument('--verify', action='store_true', default=True, help='Verify candidates')
    parser.add_argument('--no-verify', action='store_false', dest='verify', help='Skip verification')
    parser.add_argument('--output', choices=['text', 'json'], default='text', help='Output format')
    parser.add_argument('--provider', choices=['hunterio', 'zerointel', 'apollo'], help='Email verification API provider')
    parser.add_argument('--api-key', help='API key for the verification provider')
    parser.add_argument('--learn-from', help='Learn pattern from a known email at this domain (e.g., john@company.com)')
    parser.add_argument('--cache-patterns', action='store_true', default=True, help='Cache learned patterns (default: true)')
    parser.add_argument('--no-cache', action='store_true', help='Disable pattern cache')
    parser.add_argument('--linkedin', help='LinkedIn profile URL to scrape for info')
    parser.add_argument('--batch', help='CSV file with multiple people to process')
    parser.add_argument('--output-csv', help='Output CSV file for batch results')
    parser.add_argument('--cache-verify', action='store_true', default=True, help='Cache verification results (default: true)')
    parser.add_argument('--clear-cache', action='store_true', help='Clear verification cache')
    parser.add_argument('--fast', action='store_true', help='Fast mode - skip slow SMTP verification')
    parser.add_argument('--ai-learn', action='store_true', help='Enable AI pattern learning')
    parser.add_argument('--analyze-history', action='store_true', help='Analyze historical data and show insights')
    parser.add_argument('--learn-from-history', action='store_true', help='Learn patterns from historical verification data')
    parser.add_argument('--data-sources', action='store_true', help='Enable external data source integration')
    parser.add_argument('--enrich', action='store_true', help='Enrich search with external data sources')
    parser.add_argument('--list-sources', action='store_true', help='List available data sources')
    parser.add_argument('--setup-config', action='store_true', help='Create sample configuration files')

    args = parser.parse_args()

    # Batch processing mode (Route D)
    if args.batch:
        print(f"[Batch] Reading from {args.batch}...")
        result_cache = ResultCache() if args.cache_verify and not args.clear_cache else None

        if args.clear_cache:
            result_cache.clear() if result_cache else None
            print("[Batch] Cache cleared.")

        people = read_csv_input(args.batch)
        print(f"[Batch] Processing {len(people)} people...\n")

        all_results = []
        for i, person in enumerate(people):
            print(f"[{i+1}/{len(people)}] {person['name']} @ {person['domain']}...")
            candidates = generate_candidates(
                person['name'],
                person['domain'],
                english_first=person.get('english_first'),
                english_last=person.get('english_last'),
                has_duplicate=person.get('has_duplicate', False)
            )

            verifier = EmailVerifier(provider=args.provider, api_key=args.api_key)

            # Check cache first
            if result_cache:
                for c in candidates:
                    cached = result_cache.get(c['email'])
                    if cached:
                        c['verification'] = cached
                        print(f"  [Cache hit] {c['email']}")

            # Verify uncached
            if args.verify:
                for c in candidates:
                    if not result_cache or not result_cache.get(c['email']):
                        try:
                            verification = verifier.verify(c['email'])
                            c['verification'] = verification
                            if result_cache:
                                result_cache.set(c['email'], verification)
                        except Exception as e:
                            c['verification'] = {'email': c['email'], 'error': str(e)}

            # Get best result
            scored = []
            for c in candidates:
                verification = c.get('verification', {})
                if verification:
                    scored_c = scorer.score(verification, c.get('priority', 2))
                    scored_c['email'] = c['email']
                    scored_c['pattern'] = c['pattern']
                    scored.append(scored_c)
                else:
                    # Unverified - use priority as score
                    scored.append({
                        'email': c['email'],
                        'score': (3 - c.get('priority', 2)) * 10,  # priority 1 = 20, 2 = 10, 3 = 0
                        'level': 'none',
                        'factors': ['unverified'],
                        'pattern': c.get('pattern', '')
                    })

            scored.sort(key=lambda x: x['score'], reverse=True)
            best = scored[0] if scored else None

            if best:
                print(f"  Best: {best['email']} ({best['score']}% - {best['level']})")
                all_results.append({
                    'name': person['name'],
                    'domain': person['domain'],
                    'email': best['email'],
                    'valid': best['score'] >= 60,
                    'confidence': best['level'],
                    'pattern': best.get('pattern', ''),
                    'methods': best.get('factors', [])
                })
            else:
                print(f"  No candidates found")
                all_results.append({
                    'name': person['name'],
                    'domain': person['domain'],
                    'email': None,
                    'valid': False,
                    'confidence': 'none',
                    'pattern': '',
                    'methods': []
                })

        if args.output_csv:
            write_csv_output(all_results, args.output_csv)
            print(f"\n[Batch] Results saved to {args.output_csv}")
        else:
            print(f"\n[Batch] Results:")
            for r in all_results:
                print(f"  {r['name']} @ {r['domain']}: {r['email']} ({r['confidence']})")

        if result_cache:
            print(f"\n[Batch] Cache size: {result_cache.size()} entries")
        return

    # LinkedIn profile scraping (Route C)
    if args.linkedin:
        print(f"[LinkedIn] Scraping {args.linkedin}...")
        profile = scrape_linkedin_profile(args.linkedin)

        if profile['success']:
            print(f"[LinkedIn] Name: {profile.get('name', 'N/A')}")
            if profile.get('first_name'):
                print(f"[LinkedIn] First: {profile['first_name']}, Last: {profile.get('last_name', 'N/A')}")
            if profile.get('job_title'):
                print(f"[LinkedIn] Title: {profile['job_title']}")
            if profile.get('company'):
                print(f"[LinkedIn] Company: {profile['company']}")
            if profile.get('email'):
                print(f"[LinkedIn] Email found: {profile['email']}")

            # Use scraped info to override args
            if profile.get('first_name') and not args.english_first:
                args.english_first = profile['first_name']
            if profile.get('last_name') and not args.english_last:
                args.english_last = profile['last_name']
            if profile.get('company') and not args.domain:
                # Try to guess domain from company name
                from lib.linkedin import extract_company_domain
                guessed_domain = extract_company_domain(profile['company'])
                if guessed_domain:
                    print(f"[LinkedIn] Guessed domain: {guessed_domain}")
                    args.domain = guessed_domain
        else:
            print(f"[LinkedIn] Failed: {profile.get('error', 'Unknown error')}")
            print("[LinkedIn] Continuing with provided info...\n")

    # Pattern learning (Route B)
    learned_pattern = None
    if args.learn_from:
        cache = PatternCache() if not args.no_cache else None
        cached = cache.get(args.domain) if cache else None

        if cached:
            print(f"[Pattern cache] Found: {cached.get('pattern', 'unknown')}")
            learned_pattern = cached.get('pattern')
        else:
            print(f"[Pattern learning] Analyzing {args.learn_from}...")
            learner = PatternLearner()
            result = learner.learn_from_emails(args.domain, [args.learn_from])

            if result['success']:
                print(f"[Pattern learning] Detected: {result['pattern']} (confidence: {result['confidence']})")
                print(f"[Pattern learning] Reasoning: {result['reasoning']}")
                if result.get('examples'):
                    print(f"[Pattern learning] Examples: {', '.join(result['examples'][:3])}")

                learned_pattern = result['pattern']
                if cache and learned_pattern:
                    cache.set(args.domain, result)
            else:
                print(f"[Pattern learning] Failed: {result['reasoning']}")

        if learned_pattern:
            print(f"[Pattern learning] Using learned pattern: {learned_pattern}\n")

    # Configuration setup
    if args.setup_config:
        print("[Configuration] Creating sample configuration files...")
        config_manager = ConfigManager()

        sample_config = config_manager.create_sample_config()
        sample_keys = config_manager.create_sample_api_keys()

        print(f"📁 Sample config created: {sample_config}")
        print(f"🔑 Sample API keys created: {sample_keys}")
        print("\n📋 Next steps:")
        print("  1. Edit the API keys file with your actual keys")
        print("  2. Or set environment variables (e.g., TIANYANCHA_API_KEY)")
        print("  3. Run with --data-sources to enable external data integration")

        return

    # List available data sources
    if args.list_sources:
        print("[Data Sources] Available data sources:")
        config_manager = ConfigManager()
        enabled_sources = config_manager.get_enabled_data_sources()

        sources_info = {
            'tianyancha': '天眼查 - Chinese business information API',
            'qichacha': '企查查 - Chinese business information API',
            'github': 'GitHub - Public code repository data',
            'stackoverflow': 'Stack Overflow - Developer Q&A platform'
        }

        for source in enabled_sources:
            description = sources_info.get(source, source)
            status = "✅ Enabled" if config_manager.is_data_source_enabled(source) else "❌ Disabled"
            print(f"  {source}: {description} {status}")

        return

    # AI Pattern Learning - History Analysis
    if args.analyze_history:
        print("[AI Learning] Analyzing historical verification data...")
        analyzer = HistoryAnalyzer()

        # Copy sample data if no history exists
        if not Path(analyzer.history_file).exists():
            import shutil
            sample_file = Path(__file__).parent / 'data' / 'sample_history.json'
            if sample_file.exists():
                shutil.copy(sample_file, analyzer.history_file)
                print("[AI Learning] Using sample history data for demonstration")

        insights = analyzer.generate_insights()

        print("\n[AI Learning] Insights from history:")
        for insight in insights['insights']:
            print(f"  • {insight}")

        print("\n[AI Learning] Recommendations:")
        for rec in insights['recommendations']:
            print(f"  📋 {rec}")

        return  # Exit after analysis

    # AI Pattern Learning for candidate generation
    if args.ai_learn or args.learn_from_history:
        if not args.name or not args.domain:
            print("Error: --ai-learn requires name and domain arguments")
            return

        print("[AI Learning] Initializing AI pattern learner...")
        ai_learner = AIPatternLearner()

        if args.learn_from_history:
            print("[AI Learning] Learning from historical data...")
            # This will be used to enhance the candidates later

        if args.ai_learn:
            print("[AI Learning] Enhancing candidates with learned patterns...")

    # Data Source Integration
    enrichment_data = None
    if args.data_sources or args.enrich:
        if not args.name or not args.domain:
            print("Error: --data-sources requires name and domain arguments")
            return

        print("[Data Sources] Initializing external data sources...")
        config_manager = ConfigManager()
        data_integrator = DataSourceIntegrator()
        data_integrator.initialize_sources()

        if args.enrich:
            print("[Data Sources] Enriching search with external data...")
            enrichment_data = data_integrator.enrich_email_search(args.name, args.domain)

            if enrichment_data['person_data']:
                print(f"[Data Sources] Found {len(enrichment_data['person_data'])} person records")
                for person in enrichment_data['person_data'][:3]:  # Show top 3
                    print(f"  👤 {person.get('name')} @ {person.get('company')} "
                          f"({person.get('source')}, confidence: {person.get('confidence', 0):.2f})")

            if enrichment_data['company_data']:
                print(f"[Data Sources] Found {len(enrichment_data['company_data'])} company records")
                for company in enrichment_data['company_data'][:3]:  # Show top 3
                    print(f"  🏢 {company.get('name')} "
                          f"({company.get('source')}, confidence: {company.get('confidence', 0):.2f})")

            if enrichment_data['suggested_emails']:
                print(f"[Data Sources] Found {len(enrichation_data['suggested_emails'])} suggested emails")
                for email_info in enrichment_data['suggested_emails'][:5]:  # Show top 5
                    print(f"  📧 {email_info['email']} "
                          f"({email_info['source']}, confidence: {email_info['confidence']:.2f})")

    # Generate candidates
    if args.pattern or learned_pattern:
        pattern_to_use = args.pattern or learned_pattern
        print(f"Using pattern: {pattern_to_use}")
        candidates = generate_from_known_pattern(
            args.name, args.domain, pattern_to_use, args.has_duplicate
        )
    else:
        candidates = generate_candidates(
            args.name,
            args.domain,
            english_first=args.english_first,
            english_last=args.english_last,
            has_duplicate=args.has_duplicate,
            department=args.department
        )

    # Apply AI learning if enabled
    if args.ai_learn and 'ai_learner' in locals():
        candidates = ai_learner.generate_smart_candidates(args.name, args.domain, candidates)
        print(f"[AI Learning] Re-ranked {len(candidates)} candidates based on learned patterns")

    # Apply data source enrichment if available
    if enrichment_data and args.enrich:
        # Add suggested emails from data sources to candidates
        for email_info in enrichment_data['suggested_emails']:
            # Check if this email is already in candidates
            existing = any(c['email'] == email_info['email'] for c in candidates)
            if not existing:
                candidates.insert(0, {
                    'email': email_info['email'],
                    'pattern': 'external_source',
                    'priority': 1,  # High priority for externally found emails
                    'source': email_info['source'],
                    'confidence': email_info['confidence']
                })
        print(f"[Data Sources] Added external emails to candidate list")

    # Verify if requested
    if args.fast:
        print("[Fast mode] Using quick verification (no SMTP)...")
        verifier = FastVerifier()
    else:
        verifier = EmailVerifier(provider=args.provider, api_key=args.api_key)
    scorer = ConfidenceScorer()

    # Try API provider direct lookup first (more reliable than candidate generation)
    # Skip in fast mode (API lookup not supported by FastVerifier)
    if args.provider and not args.fast:
        name_parts = args.name.split()
        first_name = args.english_first or (name_parts[0] if name_parts else '')
        last_name = args.english_last or (name_parts[-1] if len(name_parts) > 1 else '')

        if first_name and last_name:
            api_result = verifier.find_email(first_name, last_name, args.domain)
            if api_result['success']:
                print(f"API provider ({args.provider}) found: {api_result['email']}")
                print(f"Confidence: {api_result['confidence']}")
                print(f"Reason: {api_result['reason']}\n")

    if args.verify:
        for c in candidates[:20]:  # Verify first 20 to save time
            try:
                verification = verifier.verify(c['email'])
                c['verification'] = verification

                # Record verification for AI learning
                if args.ai_learn and 'ai_learner' in locals():
                    is_valid = verification.get('valid', False)
                    confidence = verification.get('confidence', 'none')
                    ai_learner.record_verification(
                        args.name, args.domain, c['email'],
                        c.get('pattern', ''), is_valid, confidence
                    )

            except Exception as e:
                c['verification'] = {'email': c['email'], 'error': str(e)}

    # Format output
    if args.output == 'json':
        print(json.dumps(candidates, indent=2, ensure_ascii=False))
    else:
        print(f"Email candidates for {args.name} @ {args.domain}\n")
        print(format_candidate_list(candidates, scorer))
        print(f"\nTotal candidates: {len(candidates)}")

        # Show AI learning stats if enabled
        if args.ai_learn and 'ai_learner' in locals():
            stats = ai_learner.get_learning_stats()
            print(f"\n[AI Learning Stats]")
            print(f"  📊 Total records: {stats['total_records']}")
            print(f"  🏢 Learned companies: {stats['learned_companies']}")
            print(f"  🎯 Pattern weights: {stats['pattern_weights_count']}")

            if stats['most_successful_patterns']:
                print(f"  🏆 Top patterns:")
                for pattern, weight in stats['most_successful_patterns']:
                    print(f"     {pattern}: {weight:.2f}")


if __name__ == '__main__':
    main()