"""
Email candidate generation from name and domain.
"""

import json
import re
from pathlib import Path
from typing import Optional
from .chinese import chinese_to_pinyin, parse_name, generate_pinyin_formats


def load_patterns() -> dict:
    """Load email format patterns from config."""
    config_path = Path(__file__).parent.parent / 'config' / 'patterns.json'
    with open(config_path) as f:
        return json.load(f)


def generate_candidates(
    name: str,
    domain: str,
    english_first: Optional[str] = None,
    english_last: Optional[str] = None,
    has_duplicate: bool = False,
    department: Optional[str] = None
) -> list[dict]:
    """
    Generate email candidates from a name and domain.

    Args:
        name: Person's name (Chinese or English)
        domain: Company domain (e.g., "tencent.com")
        english_first: Optional English first name
        english_last: Optional English last name
        has_duplicate: Whether this person might share a name with others
        department: Optional department for departmental emails

    Returns:
        List of candidate dicts with keys:
        - email: email address string
        - pattern: description of the pattern used
        - priority: int (1=most likely)
    """
    patterns = load_patterns()
    candidates = []

    # Parse the name
    name_data = parse_name(name)
    is_chinese = name_data['is_chinese']

    # Determine first/last name for pattern substitution
    if english_first and english_last:
        first = english_first.lower()
        last = english_last.lower()
        pinyin_data = None
    elif is_chinese:
        pinyin_data = name_data['pinyin']
        first = pinyin_data['surname']  # For pattern purposes, use surname as "first"
        last = pinyin_data['given']
    else:
        parts = name.lower().split()
        first = parts[0] if parts else ''
        last = parts[-1] if len(parts) > 1 else ''
        pinyin_data = None

    f = first[0] if first else ''
    l = last[0] if last else ''

    # Generate from patterns
    pattern_list = patterns.get('patterns', [])
    chinese_patterns_list = patterns.get('chinese_patterns', [])
    duplicate_suffixes = patterns.get('duplicate_suffixes', ['01', '02', '1', '2'])
    year_suffixes = patterns.get('year_suffixes', {})

    # Handle department suffix
    dept = department or 'it'

    for i, pattern in enumerate(pattern_list):
        email = pattern
        email = email.replace('{first}', first)
        email = email.replace('{last}', last)
        email = email.replace('{f}', f)
        email = email.replace('{l}', l)

        # English name variants
        if english_first:
            email = email.replace('{english_first}', english_first.lower())
        if english_last:
            email = email.replace('{english_last}', english_last.lower())

        # Department
        email = email.replace('{dept}', dept)

        # Year suffixes
        if '{year}' in email:
            for year in year_suffixes.get('full', ['1990', '1995', '2000']):
                candidates.append({
                    'email': email.replace('{year}', year),
                    'pattern': f"{pattern} with year {year}",
                    'priority': 3
                })
            continue
        if '{year2}' in email:
            for year in year_suffixes.get('short', ['90', '95', '00']):
                candidates.append({
                    'email': email.replace('{year2}', year),
                    'pattern': f"{pattern} with short year {year}",
                    'priority': 3
                })
            continue

        # For duplicate suffixes, only add if has_duplicate
        if '{last}' in pattern and ('01' in pattern or '1' in pattern or 'a' in pattern):
            # These patterns already have duplicate handling built in
            pass

        candidates.append({
            'email': f"{email}@{domain}",
            'pattern': pattern,
            'priority': 1 if i < 5 else 2  # First 5 patterns are most likely
        })

    # Add Chinese-specific patterns
    if is_chinese and pinyin_data:
        pinyin_formats = generate_pinyin_formats(pinyin_data)
        for pf in pinyin_formats:
            email = f"{pf}@{domain}"
            if email not in [c['email'] for c in candidates]:
                candidates.append({
                    'email': email,
                    'pattern': 'chinese pinyin variant',
                    'priority': 2
                })

    # Add duplicate-safe variants if needed
    if has_duplicate:
        for suffix in duplicate_suffixes[:4]:
            # Add zhang.wei01@domain.com style
            base = f"{first}.{last}" if first and last else first
            candidates.append({
                'email': f"{base}{suffix}@{domain}",
                'pattern': f"duplicate suffix {suffix}",
                'priority': 3
            })

    # Deduplicate and limit
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c['email'] not in seen:
            seen.add(c['email'])
            unique_candidates.append(c)

    return unique_candidates[:50]  # Limit to 50 candidates


def generate_from_known_pattern(
    name: str,
    domain: str,
    pattern_format: str,
    has_duplicate: bool = False
) -> list[dict]:
    """
    Generate emails using a learned company-specific pattern.

    Args:
        name: Person's name
        domain: Company domain
        pattern_format: Learned pattern like "firstname.lastname" or "flast"
        has_duplicate: Whether to add duplicate suffixes

    Returns:
        List of candidate emails
    """
    name_data = parse_name(name)
    pinyin_data = name_data['pinyin'] if name_data['is_chinese'] else None

    candidates = []

    # Map pattern_format to actual emails
    if pinyin_data:
        surname = pinyin_data['surname']
        given = pinyin_data['given']
        full = pinyin_data['full']

        if pattern_format == 'firstname.lastname':
            candidates.append(f"{surname}.{given}@{domain}")
            candidates.append(f"{surname}{given}@{domain}")
        elif pattern_format == 'flast':
            candidates.append(f"{surname[0]}{given}@{domain}")
        elif pattern_format == 'firstlast':
            candidates.append(f"{surname}{given}@{domain}")
        elif pattern_format == 'last.first':
            candidates.append(f"{given}.{surname}@{domain}")

        if has_duplicate:
            for suffix in ['01', '02']:
                candidates.append(f"{surname}.{given}{suffix}@{domain}")
    else:
        parts = name.lower().split()
        first = parts[0] if parts else ''
        last = parts[-1] if len(parts) > 1 else ''

        if pattern_format == 'firstname.lastname':
            candidates.append(f"{first}.{last}@{domain}")
        elif pattern_format == 'flast':
            candidates.append(f"{first[0]}{last}@{domain}")

    return [{'email': c, 'pattern': f"learned: {pattern_format}", 'priority': 1} for c in candidates]


def clean_email_local_part(email: str) -> str:
    """Clean email local part for display."""
    local = email.split('@')[0]
    # Remove obvious bad characters
    local = re.sub(r'[^a-z0-9._\-]', '', local.lower())
    return local