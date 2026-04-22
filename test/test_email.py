#!/usr/bin/env python3
"""Test email finder skill."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.chinese import chinese_to_pinyin, is_chinese_name, parse_name
from lib.generator import generate_candidates
from lib.verifier import EmailVerifier
from lib.scorer import ConfidenceScorer


def test_chinese_conversion():
    """Test Chinese name to pinyin conversion."""
    print("=== Chinese Name Conversion Test ===")

    test_names = ['张伟', '李明', '王芳', '刘洋']

    for name in test_names:
        result = chinese_to_pinyin(name)
        print(f"\n{name} → {result}")

        # Test format generation
        formats = []
        surname = result['surname']
        given = result['given']
        formats.append(f"{surname}.{given}")  # zhang.wei
        formats.append(f"{surname}{given}")    # zhangwei
        formats.append(f"{surname[0]}{given}") # zwang
        formats.append(f"{given}.{surname}")    # wei.zhang
        print(f"  Formats: {formats}")


def test_generator():
    """Test email candidate generation."""
    print("\n=== Email Generator Test ===")

    # Test Chinese name
    candidates = generate_candidates('张伟', 'tencent.com')
    print(f"\nGenerated {len(candidates)} candidates for 张伟 @ tencent.com")
    for c in candidates[:10]:
        print(f"  - {c['email']} (pattern: {c['pattern']})")

    # Test English name
    candidates = generate_candidates('David Zhang', 'alibaba.com',
                                     english_first='David', english_last='Zhang')
    print(f"\nGenerated {len(candidates)} candidates for David Zhang @ alibaba.com")
    for c in candidates[:5]:
        print(f"  - {c['email']} (pattern: {c['pattern']})")


def test_verifier():
    """Test email verification."""
    print("\n=== Email Verifier Test ===")

    verifier = EmailVerifier()

    # Test a few emails
    test_emails = [
        'david.zhang@alibaba.com',
        'test@example.com',
    ]

    for email in test_emails:
        try:
            result = verifier.verify(email)
            print(f"\n{email}:")
            print(f"  Valid: {result['valid']}")
            print(f"  Confidence: {result['confidence']}")
            print(f"  Reason: {result['reason']}")
            print(f"  Methods: {result['methods']}")
        except Exception as e:
            print(f"\n{email}: Error - {e}")


def test_scorer():
    """Test confidence scoring."""
    print("\n=== Confidence Scorer Test ===")

    scorer = ConfidenceScorer()

    test_result = {
        'email': 'test@example.com',
        'valid': True,
        'methods': {
            'gravatar': True,
            'mx': True,
            'smtp': None
        }
    }

    scored = scorer.score(test_result, pattern_priority=1)
    print(f"\nTest result: {scored}")
    print(f"Formatted: {scorer.format_result(scored)}")


def test_is_chinese():
    """Test Chinese name detection."""
    print("\n=== Chinese Detection Test ===")

    test_names = ['张伟', 'David Zhang', '张三丰', 'John Smith']
    for name in test_names:
        print(f"{name}: is_chinese = {is_chinese_name(name)}")


if __name__ == '__main__':
    print("Find Email Skill - Test Suite\n")

    test_is_chinese()
    test_chinese_conversion()
    test_generator()
    test_verifier()
    test_scorer()

    print("\n=== All tests complete ===")