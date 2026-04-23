"""
AI-powered pattern learning for email generation.

Uses machine learning and pattern analysis to:
1. Learn from historical successful email verifications
2. Predict company-specific email patterns
3. Generate smarter email candidates
"""

import json
import re
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import defaultdict, Counter
from datetime import datetime


class AIPatternLearner:
    """AI-powered pattern learning for email generation."""

    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or str(Path(__file__).parent.parent / 'data')
        self.history_file = Path(self.data_dir) / 'email_history.json'
        self.pattern_cache_file = Path(self.data_dir) / 'learned_patterns.json'

        # Create data directory if not exists
        os.makedirs(self.data_dir, exist_ok=True)

        # Load existing data
        self.history = self._load_history()
        self.learned_patterns = self._load_learned_patterns()

        # Pattern weights based on historical success
        self.pattern_weights = defaultdict(float)
        self.company_patterns = defaultdict(list)

    def _load_history(self) -> List[Dict]:
        """Load email verification history."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _load_learned_patterns(self) -> Dict:
        """Load learned patterns cache."""
        if self.pattern_cache_file.exists():
            try:
                with open(self.pattern_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_history(self):
        """Save email verification history."""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def _save_learned_patterns(self):
        """Save learned patterns cache."""
        with open(self.pattern_cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.learned_patterns, f, ensure_ascii=False, indent=2)

    def record_verification(self, name: str, domain: str, email: str,
                          pattern: str, is_valid: bool, confidence: str):
        """Record an email verification result for learning."""
        record = {
            'timestamp': datetime.now().isoformat(),
            'name': name,
            'domain': domain,
            'email': email,
            'pattern': pattern,
            'is_valid': is_valid,
            'confidence': confidence
        }

        self.history.append(record)

        # Keep only recent history (last 1000 records)
        if len(self.history) > 1000:
            self.history = self.history[-1000:]

        self._save_history()

        # Update pattern weights
        self._update_pattern_weights()

    def _update_pattern_weights(self):
        """Update pattern weights based on historical success rate."""
        pattern_stats = defaultdict(lambda: {'success': 0, 'total': 0})

        for record in self.history:
            pattern = record['pattern']
            pattern_stats[pattern]['total'] += 1
            if record['is_valid']:
                pattern_stats[pattern]['success'] += 1

        # Calculate success rate for each pattern
        for pattern, stats in pattern_stats.items():
            if stats['total'] > 0:
                success_rate = stats['success'] / stats['total']
                # Weight by sample size (more data = more confidence)
                weight = success_rate * min(1.0, stats['total'] / 10)  # Cap at 10 samples
                self.pattern_weights[pattern] = weight

    def learn_company_pattern(self, domain: str, known_emails: List[str],
                            names: List[str]) -> Dict[str, float]:
        """Learn email patterns for a specific company."""
        if len(known_emails) < 2:
            return {}  # Need at least 2 examples

        patterns_found = []

        for email, name in zip(known_emails, names):
            pattern = self._extract_pattern(email, name)
            if pattern:
                patterns_found.append(pattern)

        # Count pattern frequency
        pattern_counts = Counter(patterns_found)
        total = len(patterns_found)

        # Calculate pattern confidence
        company_patterns = {}
        for pattern, count in pattern_counts.items():
            confidence = count / total
            company_patterns[pattern] = confidence

        # Cache learned patterns
        self.learned_patterns[domain] = {
            'patterns': company_patterns,
            'sample_size': len(known_emails),
            'last_updated': datetime.now().isoformat()
        }

        self._save_learned_patterns()
        return company_patterns

    def _extract_pattern(self, email: str, name: str) -> Optional[str]:
        """Extract email pattern from email and name."""
        try:
            local_part = email.split('@')[0].lower()

            # Try to match with common patterns
            patterns = [
                (r'^([a-z])\.([a-z]+)$', '{f}.{last}'),
                (r'^([a-z]+)\.([a-z]+)$', '{first}.{last}'),
                (r'^([a-z])([a-z]+)$', '{f}{last}'),
                (r'^([a-z]+)([a-z]+)$', '{first}{last}'),
                (r'^([a-z])_([a-z]+)$', '{f}_{last}'),
                (r'^([a-z]+)_([a-z]+)$', '{first}_{last}'),
                (r'^([a-z])-([a-z]+)$', '{f}-{last}'),
                (r'^([a-z]+)-([a-z]+)$', '{first}-{last}'),
                (r'^([a-z])\.([a-z])$', '{f}.{l}'),
                (r'^([a-z])([a-z])$', '{f}{l}'),
                (r'^([a-z]+)\.([a-z])$', '{first}.{l}'),
                (r'^([a-z]+)([a-z])$', '{first}{l}'),
            ]

            for regex, pattern in patterns:
                match = re.match(regex, local_part)
                if match:
                    return pattern

            return None
        except Exception:
            return None

    def get_company_patterns(self, domain: str) -> Dict[str, float]:
        """Get learned patterns for a company."""
        return self.learned_patterns.get(domain, {}).get('patterns', {})

    def generate_smart_candidates(self, name: str, domain: str,
                                 base_candidates: List[Dict]) -> List[Dict]:
        """Generate smart candidates using learned patterns."""
        # Get company-specific patterns
        company_patterns = self.get_company_patterns(domain)

        if not company_patterns:
            # Try parent domain (e.g., sub.company.com -> company.com)
            parent_domain = '.'.join(domain.split('.')[-2:])
            company_patterns = self.get_company_patterns(parent_domain)

        # Re-rank candidates based on learned patterns
        enhanced_candidates = []

        for candidate in base_candidates:
            email = candidate['email']
            pattern = candidate.get('pattern', '')
            priority = candidate.get('priority', 3)

            # Boost priority if pattern matches company pattern
            pattern_confidence = company_patterns.get(pattern, 0)
            if pattern_confidence > 0:
                # Reduce priority number (higher priority)
                priority = max(1, priority - int(pattern_confidence * 2))

            # Apply global pattern weights
            global_weight = self.pattern_weights.get(pattern, 0)
            if global_weight > 0:
                priority = max(1, priority - int(global_weight * 1.5))

            enhanced_candidate = candidate.copy()
            enhanced_candidate['priority'] = priority
            enhanced_candidate['pattern_confidence'] = pattern_confidence
            enhanced_candidate['global_weight'] = global_weight

            enhanced_candidates.append(enhanced_candidate)

        # Sort by enhanced priority
        enhanced_candidates.sort(key=lambda x: x['priority'])

        return enhanced_candidates

    def suggest_new_patterns(self, name: str, domain: str) -> List[str]:
        """Suggest new email patterns based on AI analysis."""
        suggestions = []

        # Analyze name structure
        if any('一' <= c <= '鿿' for c in name):  # Chinese characters
            # For Chinese names, suggest pinyin-based patterns
            from .chinese import chinese_to_pinyin
            pinyin_data = chinese_to_pinyin(name)

            if pinyin_data:
                # Generate variations based on successful Chinese patterns
                suggestions.extend([
                    f"{pinyin_data['full']}{{{'year'}}}",
                    f"{pinyin_data['initial']}{{{'year'}}}",
                    f"{pinyin_data['surname']}.{pinyin_data['given']}{{{'year'}}}"
                ])

        # Analyze domain for patterns
        domain_parts = domain.split('.')
        if len(domain_parts) > 2:
            # Subdomain - might indicate department structure
            subdomain = domain_parts[0]
            suggestions.append(f"{{first}}.{{last}}.{subdomain}")

        return suggestions

    def get_learning_stats(self) -> Dict:
        """Get statistics about the learning progress."""
        return {
            'total_records': len(self.history),
            'learned_companies': len(self.learned_patterns),
            'pattern_weights_count': len(self.pattern_weights),
            'most_successful_patterns': sorted(
                self.pattern_weights.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }