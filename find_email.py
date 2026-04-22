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
            except Exception as e:
                c['verification'] = {'email': c['email'], 'error': str(e)}

    # Format output
    if args.output == 'json':
        print(json.dumps(candidates, indent=2, ensure_ascii=False))
    else:
        print(f"Email candidates for {args.name} @ {args.domain}\n")
        print(format_candidate_list(candidates, scorer))
        print(f"\nTotal candidates: {len(candidates)}")


if __name__ == '__main__':
    main()