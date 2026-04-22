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


def main():
    parser = argparse.ArgumentParser(description='Find email from name and domain')
    parser.add_argument('name', help='Person name (Chinese or English)')
    parser.add_argument('domain', help='Company domain (e.g., tencent.com)')
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

    args = parser.parse_args()

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
    verifier = EmailVerifier(provider=args.provider, api_key=args.api_key)
    scorer = ConfidenceScorer()

    # Try API provider direct lookup first (more reliable than candidate generation)
    if args.provider:
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