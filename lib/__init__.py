"""
Find Email Skill - Find and verify email addresses from names.
"""

from .generator import generate_candidates, generate_from_known_pattern
from .verifier import EmailVerifier, quick_verify_gravatar, quick_verify_mx
from .scorer import ConfidenceScorer, format_candidate_list
from .chinese import chinese_to_pinyin, parse_name, is_chinese_name
from .api_providers import HunterioProvider, ZeroIntelProvider, ApolloProvider
from .pattern_learner import PatternLearner, PatternCache

__all__ = [
    'generate_candidates',
    'generate_from_known_pattern',
    'EmailVerifier',
    'quick_verify_gravatar',
    'quick_verify_mx',
    'ConfidenceScorer',
    'format_candidate_list',
    'chinese_to_pinyin',
    'parse_name',
    'is_chinese_name',
    'HunterioProvider',
    'ZeroIntelProvider',
    'ApolloProvider',
    'PatternLearner',
    'PatternCache'
]