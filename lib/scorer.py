"""
Confidence scoring for email candidates.
"""

from typing import Optional


class ConfidenceScorer:
    """Calculate confidence scores for email candidates."""

    def __init__(self):
        # Weights for different verification methods
        self.weights = {
            'smtp': 0.95,       # SMTP verification is most reliable
            'gravatar': 0.60,   # Gravatar has ~60% coverage among tech users
            'github': 0.50,     # GitHub commit email is reliable but low coverage
            'mx_only': 0.30,   # MX only means domain exists but not specific email
            'pattern': 0.20    # Pattern match alone is weak
        }

    def score(self, verification_result: dict, pattern_priority: int = 2) -> dict:
        """
        Calculate confidence score from verification result.

        Args:
            verification_result: Result from EmailVerifier.verify()
            pattern_priority: 1-3, how likely the pattern is (1=most likely)

        Returns:
            dict with:
            - score: 0-100
            - level: 'high', 'medium', 'low', 'none'
            - factors: list of contributing factors
        """
        score = 0
        factors = []
        methods = verification_result.get('methods', {})

        # Base score from pattern priority
        if pattern_priority == 1:
            score += 20
            factors.append('common format pattern')
        elif pattern_priority == 2:
            score += 10
            factors.append('less common pattern')
        else:
            score += 5
            factors.append('rare pattern')

        # Add verification method scores
        if verification_result.get('valid'):
            if methods.get('smtp') == 'valid':
                score += 80
                factors.append('SMTP verified')
            elif methods.get('smtp') == 'catchall':
                score += 30
                factors.append('catchall domain (unreliable)')
            elif methods.get('gravatar'):
                score += 50
                factors.append('Gravatar match')
            elif methods.get('github'):
                score += 40
                factors.append('GitHub commit match')
            elif methods.get('mx'):
                score += 20
                factors.append('domain has MX records')

            # Enhanced verification bonuses
            server_type = methods.get('server_type')
            if server_type in ['google_workspace', 'microsoft_365']:
                score += 15
                factors.append(f'known enterprise mail service ({server_type})')
            elif server_type == 'corporate_custom':
                score += 10
                factors.append('custom corporate mail server')

            # DNSBL penalty
            if methods.get('dnsbl'):
                score = max(0, score - 40)
                factors.append('domain blacklisted')
        else:
            if methods.get('smtp') == 'invalid':
                score = 0
                factors.append('SMTP mailbox not found')
            elif not methods.get('mx'):
                score = 0
                factors.append('no MX records')
            elif methods.get('dnsbl'):
                score = 0
                factors.append('domain blacklisted')

        # Determine level
        if score >= 85:
            level = 'high'
        elif score >= 60:
            level = 'medium'
        elif score >= 30:
            level = 'low'
        else:
            level = 'none'

        return {
            'score': min(100, score),
            'level': level,
            'factors': factors,
            'email': verification_result.get('email')
        }

    def format_result(self, scored_result: dict) -> str:
        """Format scored result for display."""
        level = scored_result['level']
        email = scored_result['email']
        score = scored_result['score']
        factors = scored_result['factors']

        if level == 'high':
            icon = '✅'
        elif level == 'medium':
            icon = '⚠️'
        elif level == 'low':
            icon = '⚠️'
        else:
            icon = '❌'

        factor_str = ', '.join(factors) if factors else 'no verification'
        return f"{icon} {email} ({score}% - {factor_str})"


def format_candidate_list(candidates: list[dict], scorer: ConfidenceScorer) -> str:
    """
    Format a list of email candidates for display.

    Each candidate should have 'email', 'pattern', 'verification' keys.
    """
    lines = []

    # Sort by confidence score
    scored = []
    for c in candidates:
        verification = c.get('verification', {})
        if verification:
            scored_c = scorer.score(verification, c.get('priority', 2))
            scored_c['email'] = c['email']
            scored_c['pattern'] = c['pattern']
            scored.append(scored_c)
        else:
            scored.append({
                'email': c['email'],
                'score': 0,
                'level': 'none',
                'factors': ['unverified'],
                'pattern': c.get('pattern', '')
            })

    scored.sort(key=lambda x: x['score'], reverse=True)

    for s in scored:
        line = scorer.format_result(s)
        lines.append(line)

    return '\n'.join(lines)


def emoji_for_level(level: str) -> str:
    """Get emoji for confidence level."""
    return {
        'high': '✅',
        'medium': '⚠️',
        'low': '⚠️',
        'none': '❌'
    }.get(level, '❌')