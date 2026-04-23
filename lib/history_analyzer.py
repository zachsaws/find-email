"""
History analysis for email pattern learning.

Analyzes historical email verification data to:
1. Identify successful patterns
2. Detect company-specific conventions
3. Optimize candidate generation
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta


class HistoryAnalyzer:
    """Analyze historical email verification data."""

    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or str(Path(__file__).parent.parent / 'data')
        self.history_file = Path(self.data_dir) / 'email_history.json'

    def load_history(self) -> List[Dict]:
        """Load verification history."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def analyze_pattern_success_rate(self, days: int = 30) -> Dict[str, Dict]:
        """Analyze success rate of different email patterns."""
        history = self.load_history()

        # Filter recent history
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_history = [
            h for h in history
            if datetime.fromisoformat(h['timestamp']) > cutoff_date
        ]

        pattern_stats = defaultdict(lambda: {'success': 0, 'total': 0})

        for record in recent_history:
            pattern = record.get('pattern', 'unknown')
            pattern_stats[pattern]['total'] += 1

            if record.get('is_valid', False):
                pattern_stats[pattern]['success'] += 1

        # Calculate success rates
        result = {}
        for pattern, stats in pattern_stats.items():
            if stats['total'] > 0:
                success_rate = stats['success'] / stats['total']
                result[pattern] = {
                    'success_rate': success_rate,
                    'success_count': stats['success'],
                    'total_count': stats['total'],
                    'confidence': min(1.0, stats['total'] / 10)  # Sample size confidence
                }

        return result

    def analyze_company_patterns(self, min_samples: int = 3) -> Dict[str, Dict]:
        """Analyze patterns by company domain."""
        history = self.load_history()

        # Group by domain
        domain_data = defaultdict(list)
        for record in history:
            domain = record.get('domain', '')
            domain_data[domain].append(record)

        result = {}
        for domain, records in domain_data.items():
            if len(records) < min_samples:
                continue

            # Analyze patterns for this domain
            pattern_counts = Counter()
            valid_patterns = set()

            for record in records:
                pattern = record.get('pattern', 'unknown')
                pattern_counts[pattern] += 1

                if record.get('is_valid', False):
                    valid_patterns.add(pattern)

            # Calculate domain-specific pattern preferences
            total_records = len(records)
            domain_patterns = {}

            for pattern, count in pattern_counts.items():
                frequency = count / total_records
                is_valid = pattern in valid_patterns

                domain_patterns[pattern] = {
                    'frequency': frequency,
                    'count': count,
                    'is_valid': is_valid,
                    'score': frequency * (1.5 if is_valid else 0.5)
                }

            result[domain] = {
                'total_records': total_records,
                'patterns': domain_patterns,
                'most_common_pattern': pattern_counts.most_common(1)[0][0] if pattern_counts else None,
                'successful_patterns': list(valid_patterns)
            }

        return result

    def analyze_name_patterns(self) -> Dict[str, Dict]:
        """Analyze patterns based on name characteristics."""
        history = self.load_history()

        # Group by name characteristics
        chinese_names = []
        english_names = []
        mixed_names = []

        for record in history:
            name = record.get('name', '')

            # Detect name type
            has_chinese = any('一' <= c <= '鿿' for c in name)
            has_english = any(c.isalpha() and ord(c) < 128 for c in name)

            if has_chinese and has_english:
                mixed_names.append(record)
            elif has_chinese:
                chinese_names.append(record)
            elif has_english:
                english_names.append(record)

        def analyze_group(records: List[Dict], group_name: str) -> Dict:
            pattern_stats = defaultdict(lambda: {'success': 0, 'total': 0})

            for record in records:
                pattern = record.get('pattern', 'unknown')
                pattern_stats[pattern]['total'] += 1

                if record.get('is_valid', False):
                    pattern_stats[pattern]['success'] += 1

            result = {}
            for pattern, stats in pattern_stats.items():
                if stats['total'] > 0:
                    success_rate = stats['success'] / stats['total']
                    result[pattern] = {
                        'success_rate': success_rate,
                        'count': stats['total']
                    }

            return {
                'group_size': len(records),
                'patterns': result,
                'top_patterns': sorted(
                    result.items(),
                    key=lambda x: x[1]['success_rate'],
                    reverse=True
                )[:5]
            }

        return {
            'chinese_names': analyze_group(chinese_names, 'chinese'),
            'english_names': analyze_group(english_names, 'english'),
            'mixed_names': analyze_group(mixed_names, 'mixed')
        }

    def detect_trends(self, days: int = 90) -> Dict[str, List]:
        """Detect trends in email verification success."""
        history = self.load_history()

        # Group by time periods
        period_data = defaultdict(list)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        for record in history:
            timestamp = datetime.fromisoformat(record['timestamp'])
            if start_date <= timestamp <= end_date:
                # Group by week
                week_start = timestamp - timedelta(days=timestamp.weekday())
                period_data[week_start.strftime('%Y-%m-%d')].append(record)

        # Analyze trends
        trends = {
            'success_rate_over_time': [],
            'pattern_popularity': defaultdict(list),
            'domain_activity': defaultdict(list)
        }

        for period, records in sorted(period_data.items()):
            if not records:
                continue

            # Success rate
            valid_count = sum(1 for r in records if r.get('is_valid', False))
            success_rate = valid_count / len(records)

            trends['success_rate_over_time'].append({
                'period': period,
                'success_rate': success_rate,
                'total_tests': len(records)
            })

            # Pattern popularity
            pattern_counts = Counter(r.get('pattern', 'unknown') for r in records)
            for pattern, count in pattern_counts.items():
                trends['pattern_popularity'][pattern].append({
                    'period': period,
                    'count': count
                })

            # Domain activity
            domain_counts = Counter(r.get('domain', 'unknown') for r in records)
            for domain, count in domain_counts.items():
                trends['domain_activity'][domain].append({
                    'period': period,
                    'count': count
                })

        return trends

    def generate_insights(self) -> Dict[str, List[str]]:
        """Generate actionable insights from historical data."""
        insights = []

        # Analyze recent patterns
        pattern_analysis = self.analyze_pattern_success_rate(days=30)

        if pattern_analysis:
            best_pattern = max(pattern_analysis.items(), key=lambda x: x[1]['success_rate'])
            insights.append(
                f"最佳模式: {best_pattern[0]} (成功率: {best_pattern[1]['success_rate']:.1%})"
            )

            worst_pattern = min(pattern_analysis.items(), key=lambda x: x[1]['success_rate'])
            insights.append(
                f"需要改进: {worst_pattern[0]} (成功率: {worst_pattern[1]['success_rate']:.1%})"
            )

        # Analyze company patterns
        company_analysis = self.analyze_company_patterns()

        if company_analysis:
            most_consistent = max(company_analysis.items(),
                                key=lambda x: len(x[1]['successful_patterns']))
            insights.append(
                f"最一致的公司: {most_consistent[0]} "
                f"({len(most_consistent[1]['successful_patterns'])} 个成功模式)"
            )

        # Analyze name patterns
        name_analysis = self.analyze_name_patterns()

        if name_analysis['chinese_names']['group_size'] > 0:
            top_chinese = name_analysis['chinese_names']['top_patterns'][0]
            insights.append(
                f"中文姓名最佳模式: {top_chinese[0]} (成功率: {top_chinese[1]['success_rate']:.1%})"
            )

        if name_analysis['english_names']['group_size'] > 0:
            top_english = name_analysis['english_names']['top_patterns'][0]
            insights.append(
                f"英文姓名最佳模式: {top_english[0]} (成功率: {top_english[1]['success_rate']:.1%})"
            )

        return {
            'insights': insights,
            'recommendations': self._generate_recommendations(
                pattern_analysis, company_analysis, name_analysis
            )
        }

    def _generate_recommendations(self, pattern_analysis: Dict,
                                company_analysis: Dict,
                                name_analysis: Dict) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        # Pattern-based recommendations
        if pattern_analysis:
            high_success = [p for p, s in pattern_analysis.items()
                          if s['success_rate'] > 0.7 and s['total_count'] >= 5]

            if high_success:
                recommendations.append(
                    f"优先使用高成功率模式: {', '.join(high_success[:3])}"
                )

        # Company-based recommendations
        if company_analysis:
            recommendations.append(
                "为常用公司建立模式缓存以提高准确性"
            )

        # Name-based recommendations
        if name_analysis['chinese_names']['group_size'] > 10:
            recommendations.append(
                "中文姓名数据充足，建议优化拼音转换算法"
            )

        return recommendations

    def export_analysis_report(self, output_file: str = None) -> str:
        """Export comprehensive analysis report."""
        if not output_file:
            output_file = Path(self.data_dir) / 'analysis_report.json'

        report = {
            'generated_at': datetime.now().isoformat(),
            'pattern_analysis': self.analyze_pattern_success_rate(),
            'company_analysis': self.analyze_company_patterns(),
            'name_analysis': self.analyze_name_patterns(),
            'trends': self.detect_trends(),
            'insights': self.generate_insights()
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return str(output_file)