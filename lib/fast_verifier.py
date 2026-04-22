"""
Fast email verification methods.

Optimized for speed - skips slow SMTP verification.
"""

import hashlib
import concurrent.futures
import dns.resolver
import smtplib
import urllib.request
import urllib.error
from typing import List


class FastVerifier:
    """
    Fast email verifier - skips slow SMTP verification.

    Uses only:
    - MX record check
    - Gravatar check
    - Quick GitHub check
    """

    def __init__(self):
        self.mx_cache = {}

    def verify(self, email: str) -> dict:
        """
        Fast verification - no SMTP.

        Returns dict with:
        - valid: bool
        - methods: dict
        - confidence: 'high', 'medium', 'low', 'none'
        - reason: str
        """
        import re

        result = {
            'email': email,
            'valid': False,
            'methods': {},
            'confidence': 'none',
            'reason': ''
        }

        # Syntax check
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            result['reason'] = 'Invalid email syntax'
            return result

        domain = email.split('@')[1]

        # MX record check
        mx_exists = self._check_mx(domain)
        result['methods']['mx'] = mx_exists
        if not mx_exists:
            result['reason'] = 'No MX records'
            return result

        # Gravatar check (fast)
        gravatar = self._check_gravatar(email)
        result['methods']['gravatar'] = gravatar

        # GitHub check (fast, limited)
        github = self._check_github(email)
        result['methods']['github'] = github

        if gravatar or github:
            result['valid'] = True
            result['confidence'] = 'medium'
            result['reason'] = 'Verified via HTTP method'
        else:
            result['confidence'] = 'low'
            result['reason'] = 'MX only - no SMTP verification'

        return result

    def verify_batch(self, emails: List[str], max_workers: int = 5) -> List[dict]:
        """
        Verify multiple emails in parallel.

        Args:
            emails: List of email addresses
            max_workers: Max parallel threads

        Returns:
            List of verification results
        """
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_email = {executor.submit(self.verify, email): email for email in emails}
            for future in concurrent.futures.as_completed(future_to_email):
                email = future_to_email[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        'email': email,
                        'valid': False,
                        'methods': {},
                        'confidence': 'none',
                        'reason': f'Error: {str(e)}'
                    })

        return results

    def verify_with_early_stop(
        self, emails: List[str], target_confidence: str = 'high', max_workers: int = 5
    ) -> List[dict]:
        """
        Verify emails with early termination when high confidence reached.

        Args:
            emails: List of email addresses
            target_confidence: 'high' or 'medium'
            max_workers: Max parallel threads

        Returns:
            List of verification results (partial if early stop)
        """
        results = [None] * len(emails)
        remaining_indices = list(range(len(emails)))

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {}

            while remaining_indices:
                # Submit all remaining
                for idx in remaining_indices:
                    future = executor.submit(self.verify, emails[idx])
                    future_to_idx[future] = idx

                remaining_indices = []

                # Wait for at least one to complete
                for future in concurrent.futures.as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    result = future.result()
                    results[idx] = result

                    # Check if we can stop early
                    if result['confidence'] == 'high':
                        # Cancel all remaining
                        for f in future_to_idx:
                            f.cancel()
                        # Fill remaining with "skipped"
                        for i in range(len(results)):
                            if results[i] is None:
                                results[i] = {
                                    'email': emails[i],
                                    'valid': False,
                                    'methods': {},
                                    'confidence': 'skipped',
                                    'reason': 'Early termination - high confidence found'
                                }
                        return results

                    remaining_indices.append(idx)
                    future_to_idx.pop(future)

                # If we get here with no remaining, break
                if not remaining_indices:
                    break

        # Fill any remaining None entries
        for i in range(len(results)):
            if results[i] is None:
                results[i] = {
                    'email': emails[i],
                    'valid': False,
                    'methods': {},
                    'confidence': 'none',
                    'reason': 'Verification failed'
                }

        return results

    def _check_mx(self, domain: str) -> bool:
        """Check if domain has MX records."""
        if domain in self.mx_cache:
            return self.mx_cache[domain]

        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            result = len(mx_records) > 0
        except Exception:
            result = False

        self.mx_cache[domain] = result
        return result

    def _check_gravatar(self, email: str) -> bool:
        """Check if email has a Gravatar."""
        email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
        url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=5)
            return response.status == 200
        except urllib.error.HTTPError as e:
            return e.code == 404
        except Exception:
            return False

    def _check_github(self, email: str) -> bool:
        """Check if email appears in public GitHub commits."""
        try:
            url = f"https://api.github.com/search/commits?q={email}+in:email"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'EmailFinder',
                'Accept': 'application/vnd.github.cloak-preview+json'
            })
            response = urllib.request.urlopen(req, timeout=5)
            data = response.read()
            import json
            result = json.loads(data)
            return result.get('total_count', 0) > 0
        except Exception:
            return False