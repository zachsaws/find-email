"""
Email verification using multiple methods.
"""

import hashlib
import socket
import time
import smtplib
import dns.resolver
import dns.reversename
import dns.query
import dns.zone
from typing import Optional, List, Dict
import urllib.request
import urllib.error


class EmailVerifier:
    """Multi-method email verifier."""

    def __init__(self):
        self.mx_cache = {}
        self.smtp_timeout = 10
        self.dnsbl_cache = {}
        self.server_type_cache = {}

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

        # DNSBL blacklist check
        dnsbl_result = self._check_dnsbl_blacklist(domain)
        result['methods']['dnsbl'] = dnsbl_result
        if dnsbl_result:
            result['reason'] = 'Domain blacklisted in DNSBL'
            result['confidence'] = 'low'
            return result

        # Corporate mail server detection
        server_type = self._detect_mail_server_type(domain)
        result['methods']['server_type'] = server_type

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

    def _check_dnsbl_blacklist(self, domain: str) -> bool:
        """Check if domain is blacklisted in DNSBL."""
        if domain in self.dnsbl_cache:
            return self.dnsbl_cache[domain]

        # Common DNSBL servers
        dnsbl_servers = [
            'zen.spamhaus.org',
            'bl.spamcop.net',
            'dnsbl.sorbs.net'
        ]

        try:
            # Get domain IP (for A record domains)
            try:
                ip = socket.gethostbyname(domain)
                ip_parts = ip.split('.')
                reversed_ip = '.'.join(reversed(ip_parts))

                for dnsbl in dnsbl_servers:
                    try:
                        query = f"{reversed_ip}.{dnsbl}"
                        dns.resolver.resolve(query, 'A')
                        self.dnsbl_cache[domain] = True
                        return True
                    except:
                        continue
            except:
                # Domain doesn't resolve to IP, check domain-based DNSBL
                for dnsbl in dnsbl_servers:
                    try:
                        query = f"{domain}.{dnsbl}"
                        dns.resolver.resolve(query, 'A')
                        self.dnsbl_cache[domain] = True
                        return True
                    except:
                        continue

            self.dnsbl_cache[domain] = False
            return False
        except Exception:
            self.dnsbl_cache[domain] = False
            return False

    def _detect_mail_server_type(self, domain: str) -> str:
        """Detect type of mail server (corporate, shared, etc.)."""
        if domain in self.server_type_cache:
            return self.server_type_cache[domain]

        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_hosts = [str(record.exchange).rstrip('.') for record in mx_records]

            # Corporate mail server indicators
            corporate_indicators = [
                'mail.', 'smtp.', 'mx.', 'mailserver.',
                'outlook.', 'exchange.', 'office365.',
                'google.', 'gmail.', 'googlemail.',
                'zoho.', 'yahoo.', 'hotmail.'
            ]

            # Check MX host patterns
            for mx_host in mx_hosts:
                mx_host_lower = mx_host.lower()

                # Known corporate services
                if any(indicator in mx_host_lower for indicator in ['google.', 'gmail.', 'googlemail.']):
                    self.server_type_cache[domain] = 'google_workspace'
                    return 'google_workspace'

                if any(indicator in mx_host_lower for indicator in ['outlook.', 'exchange.', 'office365.', 'microsoft.']):
                    self.server_type_cache[domain] = 'microsoft_365'
                    return 'microsoft_365'

                if any(indicator in mx_host_lower for indicator in ['zoho.']):
                    self.server_type_cache[domain] = 'zoho_mail'
                    return 'zoho_mail'

                # Corporate pattern (subdomain of main domain)
                if domain.lower() in mx_host_lower and mx_host.count('.') > domain.count('.'):
                    self.server_type_cache[domain] = 'corporate_custom'
                    return 'corporate_custom'

            # Default to generic
            self.server_type_cache[domain] = 'generic'
            return 'generic'

        except Exception:
            self.server_type_cache[domain] = 'unknown'
            return 'unknown'

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
        Enhanced SMTP verification with retry logic and timeout optimization.

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
            # Sort by priority
            mx_records = sorted(mx_records, key=lambda x: x.preference)
            mx_hosts = [str(r.exchange).rstrip('.') for r in mx_records]
        except Exception:
            return 'timeout'

        # Check for catch-all first with enhanced detection
        if self._is_catchall_enhanced(mx_hosts, domain):
            return 'catchall'

        # Try SMTP verification on each MX with retry logic
        for mx_host in mx_hosts:
            result = self._try_smtp_enhanced(mx_host, email, domain)
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

    def _is_catchall_enhanced(self, mx_hosts: list, domain: str) -> bool:
        """Enhanced catch-all detection with multiple test addresses."""
        test_addresses = [
            f"nonexistent_{int(time.time()) % 10000}@{domain}",
            f"test_invalid_{hash(domain) % 1000}@{domain}",
            f"definitely_not_real_{domain.replace('.', '_')}@{domain}"
        ]

        accepted_count = 0
        total_tests = 0

        for test_email in test_addresses:
            for mx_host in mx_hosts:
                if total_tests >= 6:  # Limit tests to avoid long delays
                    break

                try:
                    server = smtplib.SMTP(mx_host, timeout=self.smtp_timeout)
                    server.ehlo()

                    # Try STARTTLS if available
                    try:
                        if server.has_extn('STARTTLS'):
                            server.starttls()
                            server.ehlo()
                    except Exception:
                        pass

                    server.mail('test@example.com')
                    response = server.rcpt(test_email)
                    code = response[0]
                    server.quit()

                    total_tests += 1
                    if code == 250:
                        accepted_count += 1
                    elif code == 550:
                        # Definitely not catch-all
                        return False

                except Exception:
                    continue

        # If most test addresses are accepted, likely catch-all
        if total_tests > 0 and accepted_count / total_tests > 0.7:
            return True

        return False

    def _try_smtp_enhanced(self, mx_host: str, email: str, domain: str) -> str:
        """Enhanced SMTP verification with retry logic and port fallback."""
        # Try different ports in order of preference
        ports = [587, 465, 25]

        for attempt in range(3):  # Retry up to 3 times
            for port in ports:
                try:
                    if port == 465:
                        # SSL connection
                        server = smtplib.SMTP_SSL(mx_host, port, timeout=self.smtp_timeout)
                    else:
                        server = smtplib.SMTP(mx_host, port, timeout=self.smtp_timeout)

                    server.ehlo()

                    # Try STARTTLS if available (except for SSL port)
                    try:
                        if port != 465 and server.has_extn('STARTTLS'):
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
                    elif code == 451:
                        # Greylisting - wait and retry
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        # Other codes - continue to next port
                        continue

                except smtplib.SMTPServerDisconnected:
                    continue
                except smtplib.SMTPConnectError:
                    continue
                except smtplib.SMTPRecipientsRefused:
                    return 'invalid'
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