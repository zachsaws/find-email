"""
Email verification using multiple methods.
"""

import hashlib
import socket
import time
import smtplib
from typing import Optional
import urllib.request
import urllib.error


class EmailVerifier:
    """Multi-method email verifier."""

    def __init__(self):
        self.mx_cache = {}
        self.smtp_timeout = 10

    def verify(self, email: str) -> dict:
        """
        Verify an email using multiple methods.

        Returns dict with:
        - valid: bool
        - methods: dict of method → result
        - confidence: 'high', 'medium', 'low', 'none'
        - reason: str
        """
        result = {
            'email': email,
            'valid': False,
            'methods': {},
            'confidence': 'none',
            'reason': ''
        }

        # Syntax check
        if not self._check_syntax(email):
            result['reason'] = 'Invalid email syntax'
            return result

        domain = email.split('@')[1]

        # MX record check
        mx_exists = self._check_mx(domain)
        result['methods']['mx'] = mx_exists
        if not mx_exists:
            result['reason'] = 'No MX records - domain cannot receive email'
            return result

        # HTTP-based checks (parallel)
        gravatar_result = self._check_gravatar(email)
        result['methods']['gravatar'] = gravatar_result

        github_result = self._check_github(email)
        result['methods']['github'] = github_result

        # If any HTTP check passed, consider valid
        if gravatar_result or github_result:
            result['valid'] = True
            result['confidence'] = 'medium'
            result['reason'] = 'Verified via HTTP method'
            return result

        # SMTP check as fallback
        smtp_result = self._smtp_verify(email, domain)
        result['methods']['smtp'] = smtp_result

        if smtp_result == 'valid':
            result['valid'] = True
            result['confidence'] = 'high'
            result['reason'] = 'SMTP verification passed'
        elif smtp_result == 'invalid':
            result['reason'] = 'SMTP mailbox not found'
        elif smtp_result == 'catchall':
            result['valid'] = True
            result['confidence'] = 'low'
            result['reason'] = 'Catch-all domain - verification uncertain'
        else:
            result['reason'] = 'SMTP verification timeout'

        return result

    def _check_syntax(self, email: str) -> bool:
        """Basic email syntax check."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _check_mx(self, domain: str) -> bool:
        """Check if domain has MX records."""
        if domain in self.mx_cache:
            return self.mx_cache[domain]

        try:
            import dns.resolver
            mx_records = dns.resolver.resolve(domain, 'MX')
            result = len(mx_records) > 0
        except Exception:
            result = False

        self.mx_cache[domain] = result
        return result

    def _check_gravatar(self, email: str) -> bool:
        """
        Check if email has a Gravatar.

        Uses MD5 hash of email to check gravatar.com avatar.
        Returns True if avatar found (email likely exists).
        """
        email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
        url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=5)
            return response.status == 200
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False
            # Other error - can't confirm
            return False
        except Exception:
            return False

    def _check_github(self, email: str) -> bool:
        """
        Check if email appears in public GitHub commits.

        This is a simplified version - in production you'd use the GitHub API.
        """
        # GitHub search API has rate limits, so we do a simple web search
        # In practice, you'd want to use the GitHub CLI or API with authentication
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

    def _smtp_verify(self, email: str, domain: str) -> str:
        """
        Verify email via SMTP.

        Returns:
        - 'valid': Email exists
        - 'invalid': Email doesn't exist
        - 'catchall': Domain accepts all emails
        - 'timeout': Could not verify
        """
        # Get MX records
        try:
            import dns.resolver
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_hosts = [str(r.exchange).rstrip('.') for r in mx_records]
        except Exception:
            return 'timeout'

        # Check for catch-all first
        if self._is_catchall(mx_hosts, domain):
            return 'catchall'

        # Try SMTP verification on each MX
        for mx_host in mx_hosts:
            result = self._try_smtp(mx_host, email)
            if result in ['valid', 'invalid']:
                return result

        return 'timeout'

    def _is_catchall(self, mx_hosts: list, domain: str) -> bool:
        """Detect if domain is catch-all (accepts all email)."""
        test_addresses = [
            f"nonexistent_{time.time()}@{domain}",
            f"test_{hash(time.time())}@{domain}"
        ]

        accepted = 0
        for test_email in test_addresses:
            for mx_host in mx_hosts:
                try:
                    server = smtplib.SMTP(mx_host, 25, timeout=self.smtp_timeout)
                    server.helo()
                    server.mail('test@example.com')
                    response = server.rcpt(test_email)
                    code = response[0]
                    server.quit()

                    if code == 250:
                        accepted += 1
                    break  # Move to next test email
                except Exception:
                    continue

        # If both invalid addresses accepted, it's catch-all
        return accepted >= 2

    def _try_smtp(self, mx_host: str, email: str) -> str:
        """Try to verify email via SMTP to a specific MX host."""
        ports = [587, 465, 25]

        for port in ports:
            try:
                server = smtplib.SMTP(mx_host, port, timeout=self.smtp_timeout)
                server.ehlo()

                # Start TLS if available
                if port == 587:
                    try:
                        server.starttls()
                        server.ehlo()
                    except Exception:
                        pass

                server.mail('verify@example.com')
                response = server.rcpt(email)
                code = response[0]
                server.quit()

                if code == 250:
                    return 'valid'
                elif code == 550:
                    return 'invalid'
                else:
                    # Other code (like 451 greylisting) - retry
                    continue

            except smtplib.SMTPServerDisconnected:
                continue
            except smtplib.SMTPConnectError:
                continue
            except Exception:
                continue

        return 'timeout'

    def verify_batch(self, emails: list[str]) -> list[dict]:
        """Verify multiple emails."""
        results = []
        for email in emails:
            results.append(self.verify(email))
        return results


def quick_verify_gravatar(email: str) -> bool:
    """Quick Gravatar-only verification."""
    verifier = EmailVerifier()
    return verifier._check_gravatar(email)


def quick_verify_mx(domain: str) -> bool:
    """Quick MX record check."""
    verifier = EmailVerifier()
    return verifier._check_mx(domain)