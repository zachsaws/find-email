"""
Email verification API providers.

Supports:
- Hunter.io (https://hunter.io)
- ZeroIntel (https://zerointel.com)
- Apollo (https://apollo.io)
"""

import json
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import Optional


class BaseProvider(ABC):
    """Base class for email verification API providers."""

    name: str = "base"

    @abstractmethod
    def verify(self, email: str, **kwargs) -> dict:
        """
        Verify an email using the provider's API.

        Returns dict with:
        - success: bool
        - valid: bool
        - confidence: 'high', 'medium', 'low', 'none'
        - reason: str
        - methods: dict (provider-specific details)
        """
        pass

    def _request(self, url: str, headers: dict = None) -> Optional[dict]:
        """Make HTTP request and return JSON response."""
        try:
            req = urllib.request.Request(url, headers=headers or {})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}", "body": e.read().decode()}
        except Exception as e:
            return {"error": str(e)}


class HunterioProvider(BaseProvider):
    """Hunter.io email finder and verifier."""

    name = "hunterio"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or self._load_api_key("HUNTER_API_KEY")

    def verify(self, email: str, **kwargs) -> dict:
        """Verify email via Hunter.io API."""
        url = f"https://api.hunter.io/v2/email-checker?email={email}&api_key={self.api_key}"

        data = self._request(url)
        if data is None or "error" in data:
            return {
                "success": False,
                "valid": False,
                "confidence": "none",
                "reason": data.get("error", "Request failed") if data else "No response",
                "methods": {"hunterio": None}
            }

        # Hunter.io response structure
        # {"data": {"status": "valid", "score": 85, ...}}
        result = data.get("data", {})
        status = result.get("status", "unknown")

        confidence_map = {
            "valid": "high",
            "risky": "medium",
            "invalid": "none",
            "unknown": "low"
        }

        return {
            "success": True,
            "valid": status == "valid",
            "confidence": confidence_map.get(status, "low"),
            "reason": f"Hunter.io: {status} (score: {result.get('score', 'N/A')})",
            "methods": {
                "hunterio": {
                    "status": status,
                    "score": result.get("score", 0),
                    "email": result.get("email", email),
                    "type": result.get("type", "unknown")  # personal / professional
                }
            }
        }

    def find(self, first_name: str, last_name: str, domain: str, **kwargs) -> dict:
        """
        Find email by name and domain via Hunter.io API.

        Returns dict with:
        - success: bool
        - email: str or None
        - confidence: str
        - reason: str
        """
        url = f"https://api.hunter.io/v2/email-finder?domain={domain}&first_name={first_name}&last_name={last_name}&api_key={self.api_key}"

        data = self._request(url)
        if data is None or "error" in data:
            return {
                "success": False,
                "email": None,
                "confidence": "none",
                "reason": data.get("error", "Request failed") if data else "No response",
                "methods": {"hunterio": None}
            }

        result = data.get("data", {})
        email = result.get("email")

        if email:
            return {
                "success": True,
                "email": email,
                "confidence": "high",
                "reason": f"Hunter.io found: {email} (score: {result.get('score', 'N/A')})",
                "methods": {
                    "hunterio": {
                        "email": email,
                        "score": result.get("score", 0),
                        "position": result.get("position", ""),
                        "company": result.get("company", "")
                    }
                }
            }
        else:
            return {
                "success": False,
                "email": None,
                "confidence": "none",
                "reason": result.get("error", {}).get("message", "No email found"),
                "methods": {"hunterio": None}
            }

    @staticmethod
    def _load_api_key(env_var: str) -> Optional[str]:
        import os
        return os.environ.get(env_var)


class ZeroIntelProvider(BaseProvider):
    """ZeroIntel email verification API."""

    name = "zerointel"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or self._load_api_key("ZEROINTEL_API_KEY")

    def verify(self, email: str, **kwargs) -> dict:
        """Verify email via ZeroIntel API."""
        url = f"https://zerointel.com/api/v1/verify?email={email}&key={self.api_key}"

        data = self._request(url)
        if data is None or "error" in data:
            return {
                "success": False,
                "valid": False,
                "confidence": "none",
                "reason": data.get("error", "Request failed") if data else "No response",
                "methods": {"zerointel": None}
            }

        # ZeroIntel response: {"status": "valid", "score": 85, ...}
        status = data.get("status", "unknown")
        score = data.get("score", 0)

        if status == "valid" and score >= 80:
            confidence = "high"
        elif status == "valid" and score >= 50:
            confidence = "medium"
        elif status == "valid":
            confidence = "low"
        else:
            confidence = "none"

        return {
            "success": True,
            "valid": status == "valid",
            "confidence": confidence,
            "reason": f"ZeroIntel: {status} (score: {score})",
            "methods": {
                "zerointel": {
                    "status": status,
                    "score": score,
                    "disposable": data.get("disposable", False),
                    "role": data.get("role", False)
                }
            }
        }

    @staticmethod
    def _load_api_key(env_var: str) -> Optional[str]:
        import os
        return os.environ.get(env_var)


class ApolloProvider(BaseProvider):
    """Apollo.io email enrichment API."""

    name = "apollo"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or self._load_api_key("APOLLO_API_KEY")

    def verify(self, email: str, **kwargs) -> dict:
        """Verify email via Apollo.io API."""
        url = "https://api.apollo.io/v1/email/verify"
        payload = json.dumps({"email": email}).encode()
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.api_key
        }

        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            return {
                "success": False,
                "valid": False,
                "confidence": "none",
                "reason": str(e),
                "methods": {"apollo": None}
            }

        # Apollo response: {"result": "valid", "email": "...", "score": 85}
        result = data.get("result", "unknown")
        score = data.get("score", 0) or 0

        if result == "valid" and score >= 80:
            confidence = "high"
        elif result == "valid":
            confidence = "medium"
        else:
            confidence = "none"

        return {
            "success": True,
            "valid": result == "valid",
            "confidence": confidence,
            "reason": f"Apollo: {result} (score: {score})",
            "methods": {
                "apollo": {
                    "result": result,
                    "score": score,
                    "email": email
                }
            }
        }

    def enrich(self, first_name: str, last_name: str, domain: str, **kwargs) -> dict:
        """
        Enrich person with Apollo.io API (find email).

        Returns dict with:
        - success: bool
        - email: str or None
        - confidence: str
        - reason: str
        """
        url = "https://api.apollo.io/v1/people/search"
        payload = json.dumps({
            "api_key": self.api_key,
            "first_name": first_name,
            "last_name": last_name,
            "organization_domain": domain
        }).encode()
        headers = {"Content-Type": "application/json"}

        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            return {
                "success": False,
                "email": None,
                "confidence": "none",
                "reason": str(e),
                "methods": {"apollo": None}
            }

        people = data.get("people", [])
        if people:
            first_person = people[0]
            email = first_person.get("email")
            if email:
                return {
                    "success": True,
                    "email": email,
                    "confidence": "high",
                    "reason": f"Apollo found via enrichment",
                    "methods": {
                        "apollo": {
                            "email": email,
                            "name": f"{first_name} {last_name}",
                            "title": first_person.get("title", ""),
                            "organization": first_person.get("organization_name", "")
                        }
                    }
                }

        return {
            "success": False,
            "email": None,
            "confidence": "none",
            "reason": "No email found via Apollo enrichment",
            "methods": {"apollo": None}
        }

    @staticmethod
    def _load_api_key(env_var: str) -> Optional[str]:
        import os
        return os.environ.get(env_var)


class EmailVerifier:
    """
    Multi-source email verifier with API provider support.

    Combines:
    - Local verification (Gravatar, GitHub, SMTP)
    - External API providers (Hunter.io, ZeroIntel, Apollo)
    """

    def __init__(self, provider: str = None, api_key: str = None):
        """
        Initialize verifier.

        Args:
            provider: 'hunterio', 'zerointel', 'apollo', or None (local only)
            api_key: API key for the provider
        """
        self.local_verifier = _LocalVerifier()
        self.api_provider = self._init_provider(provider, api_key)

    def _init_provider(self, provider: str, api_key: str):
        """Initialize the API provider if specified."""
        if provider == "hunterio":
            return HunterioProvider(api_key)
        elif provider == "zerointel":
            return ZeroIntelProvider(api_key)
        elif provider == "apollo":
            return ApolloProvider(api_key)
        return None

    def verify(self, email: str) -> dict:
        """
        Verify email using all available methods.

        Priority:
        1. API provider (if configured)
        2. Local verification (Gravatar -> GitHub -> SMTP)

        Returns dict with:
        - valid: bool
        - confidence: 'high', 'medium', 'low', 'none'
        - reason: str
        - methods: dict of all methods checked
        """
        result = {
            "email": email,
            "valid": False,
            "confidence": "none",
            "reason": "",
            "methods": {}
        }

        # Try API provider first (most reliable)
        if self.api_provider:
            api_result = self.api_provider.verify(email)
            result["methods"][self.api_provider.name] = api_result["methods"].get(
                self.api_provider.name
            )

            if api_result["success"]:
                result["valid"] = api_result["valid"]
                result["confidence"] = api_result["confidence"]
                result["reason"] = api_result["reason"]
                if api_result["valid"]:
                    return result

        # Fall back to local verification
        local_result = self.local_verifier.verify(email)
        result["methods"].update(local_result["methods"])

        if local_result["valid"]:
            result["valid"] = True
            result["confidence"] = local_result["confidence"]
            result["reason"] = local_result["reason"]
        elif not result["reason"]:
            result["reason"] = local_result["reason"]

        return result

    def find_email(
        self, first_name: str, last_name: str, domain: str, **kwargs
    ) -> dict:
        """
        Find email by name and domain using API provider.

        Only works if API provider is configured and supports find/enrich.

        Returns dict with:
        - success: bool
        - email: str or None
        - confidence: str
        - reason: str
        """
        if not self.api_provider:
            return {
                "success": False,
                "email": None,
                "confidence": "none",
                "reason": "No API provider configured",
                "methods": {}
            }

        if isinstance(self.api_provider, HunterioProvider):
            return self.api_provider.find(first_name, last_name, domain, **kwargs)
        elif isinstance(self.api_provider, ApolloProvider):
            return self.api_provider.enrich(first_name, last_name, domain, **kwargs)
        else:
            return {
                "success": False,
                "email": None,
                "confidence": "none",
                "reason": f"{self.api_provider.name} does not support find/enrich",
                "methods": {}
            }


class _LocalVerifier:
    """
    Local-only email verifier (Gravatar + GitHub + SMTP).

    This was the original EmailVerifier logic, now separated for clarity.
    """

    def __init__(self):
        self.mx_cache = {}
        self.smtp_timeout = 10

    def verify(self, email: str) -> dict:
        """Verify email using local methods only."""
        result = {
            "email": email,
            "valid": False,
            "methods": {},
            "confidence": "none",
            "reason": ""
        }

        # Syntax check
        if not self._check_syntax(email):
            result["reason"] = "Invalid email syntax"
            return result

        domain = email.split("@")[1]

        # MX record check
        mx_exists = self._check_mx(domain)
        result["methods"]["mx"] = mx_exists
        if not mx_exists:
            result["reason"] = "No MX records - domain cannot receive email"
            return result

        # HTTP-based checks
        gravatar_result = self._check_gravatar(email)
        result["methods"]["gravatar"] = gravatar_result

        github_result = self._check_github(email)
        result["methods"]["github"] = github_result

        if gravatar_result or github_result:
            result["valid"] = True
            result["confidence"] = "medium"
            result["reason"] = "Verified via HTTP method"
            return result

        # SMTP check
        smtp_result = self._smtp_verify(email, domain)
        result["methods"]["smtp"] = smtp_result

        if smtp_result == "valid":
            result["valid"] = True
            result["confidence"] = "high"
            result["reason"] = "SMTP verification passed"
        elif smtp_result == "invalid":
            result["reason"] = "SMTP mailbox not found"
        elif smtp_result == "catchall":
            result["valid"] = True
            result["confidence"] = "low"
            result["reason"] = "Catch-all domain - verification uncertain"
        else:
            result["reason"] = "SMTP verification timeout"

        return result

    def _check_syntax(self, email: str) -> bool:
        import re
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def _check_mx(self, domain: str) -> bool:
        if domain in self.mx_cache:
            return self.mx_cache[domain]

        try:
            import dns.resolver
            mx_records = dns.resolver.resolve(domain, "MX")
            result = len(mx_records) > 0
        except Exception:
            result = False

        self.mx_cache[domain] = result
        return result

    def _check_gravatar(self, email: str) -> bool:
        email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
        url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            response = urllib.request.urlopen(req, timeout=5)
            return response.status == 200
        except urllib.error.HTTPError as e:
            return e.code == 404
        except Exception:
            return False

    def _check_github(self, email: str) -> bool:
        try:
            url = f"https://api.github.com/search/commits?q={email}+in:email"
            req = urllib.request.Request(url, headers={
                "User-Agent": "EmailFinder",
                "Accept": "application/vnd.github.cloak-preview+json"
            })
            response = urllib.request.urlopen(req, timeout=5)
            data = json.loads(response.read())
            return data.get("total_count", 0) > 0
        except Exception:
            return False

    def _smtp_verify(self, email: str, domain: str) -> str:
        try:
            import dns.resolver
            mx_records = dns.resolver.resolve(domain, "MX")
            mx_hosts = [str(r.exchange).rstrip(".") for r in mx_records]
        except Exception:
            return "timeout"

        if self._is_catchall(mx_hosts, domain):
            return "catchall"

        for mx_host in mx_hosts:
            result = self._try_smtp(mx_host, email)
            if result in ["valid", "invalid"]:
                return result

        return "timeout"

    def _is_catchall(self, mx_hosts: list, domain: str) -> bool:
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
                    server.mail("test@example.com")
                    response = server.rcpt(test_email)
                    code = response[0]
                    server.quit()
                    if code == 250:
                        accepted += 1
                    break
                except Exception:
                    continue

        return accepted >= 2

    def _try_smtp(self, mx_host: str, email: str) -> str:
        ports = [587, 465, 25]

        for port in ports:
            try:
                server = smtplib.SMTP(mx_host, port, timeout=self.smtp_timeout)
                server.ehlo()

                if port == 587:
                    try:
                        server.starttls()
                        server.ehlo()
                    except Exception:
                        pass

                server.mail("verify@example.com")
                response = server.rcpt(email)
                code = response[0]
                server.quit()

                if code == 250:
                    return "valid"
                elif code == 550:
                    return "invalid"
                else:
                    continue

            except smtplib.SMTPServerDisconnected:
                continue
            except smtplib.SMTPConnectError:
                continue
            except Exception:
                continue

        return "timeout"


# Convenience functions for quick access
def quick_verify_gravatar(email: str) -> bool:
    verifier = _LocalVerifier()
    return verifier._check_gravatar(email)


def quick_verify_mx(domain: str) -> bool:
    verifier = _LocalVerifier()
    return verifier._check_mx(domain)