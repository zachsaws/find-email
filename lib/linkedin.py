"""
LinkedIn profile scraper for email finding.

Extracts name, company, job title from LinkedIn public profiles.
Sometimes email appears in profile page metadata.
"""

import re
import json
import urllib.request
import urllib.error
from typing import Optional


class LinkedInScraper:
    """
    Scrape LinkedIn public profiles for person information.

    Note: LinkedIn has anti-scraping measures. Use responsibly.
    This is for personal/professional use cases only.
    """

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    def scrape_profile(self, profile_url: str) -> dict:
        """
        Scrape a LinkedIn profile URL.

        Args:
            profile_url: LinkedIn profile URL (e.g., https://www.linkedin.com/in/johndoe)

        Returns dict with:
            - success: bool
            - name: str or None
            - first_name: str or None
            - last_name: str or None
            - company: str or None
            - job_title: str or None
            - profile_url: str
            - email: str or None (sometimes in page metadata)
            - raw_data: dict (all extracted data)
        """
        try:
            req = urllib.request.Request(profile_url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            return self._parse_profile_html(html, profile_url)
        except urllib.error.HTTPError as e:
            return {
                "success": False,
                "name": None,
                "first_name": None,
                "last_name": None,
                "company": None,
                "job_title": None,
                "profile_url": profile_url,
                "email": None,
                "raw_data": {},
                "error": f"HTTP {e.code}"
            }
        except Exception as e:
            return {
                "success": False,
                "name": None,
                "first_name": None,
                "last_name": None,
                "company": None,
                "job_title": None,
                "profile_url": profile_url,
                "email": None,
                "raw_data": {},
                "error": str(e)
            }

    def _parse_profile_html(self, html: str, profile_url: str) -> dict:
        """Parse LinkedIn profile HTML to extract information."""
        result = {
            "success": False,
            "name": None,
            "first_name": None,
            "last_name": None,
            "company": None,
            "job_title": None,
            "profile_url": profile_url,
            "email": None,
            "raw_data": {}
        }

        # Extract name from various patterns
        name_patterns = [
            r'"name":"([^"]+)"',
            r'class="profile-entity-lockup__name[^>]*>([^<]+)<',
            r'<h1[^>]*class="[^"]*top-card[^"]*headline[^"]*[^>]*>([^<]+)<',
            r'"fullName":"([^"]+)"',
            r'<title>([^|]+)\| LinkedIn</title>',
        ]

        for pattern in name_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                result["name"] = match.group(1).strip()
                # Try to split into first/last
                parts = result["name"].split()
                if len(parts) >= 2:
                    result["first_name"] = parts[0]
                    result["last_name"] = parts[-1]
                elif len(parts) == 1:
                    result["first_name"] = parts[0]
                break

        # Extract job title
        title_patterns = [
            r'"headline":"([^"]+)"',
            r'class="[^"]*top-card[^"]*subtitle[^"]*[^>]*>([^<]+)<',
            r'<h2[^>]*class="[^"]*headline[^"]*[^>]*>([^<]+)<',
        ]

        for pattern in title_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                result["job_title"] = match.group(1).strip()
                break

        # Extract company (from experience section or other patterns)
        company_patterns = [
            r'"companyName":"([^"]+)"',
            r'class="[^"]*experience[^"]*[^>]*>\s*<[^>]*>[^<]*<span[^>]*>([^<]+)<',
            r'class="[^"]*company[^"]*[^>]*>([^<]+)<',
        ]

        for pattern in company_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if company and len(company) > 1:
                    result["company"] = company
                    break

        # Try to extract email from page metadata
        # LinkedIn sometimes includes email in og:email meta tag or structured data
        email_patterns = [
            r'"email":"([^"]+)"',
            r'og:email"[^>]*content="([^"]+)"',
            r'"contactEmail":"([^"]+)"',
        ]

        for pattern in email_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                email = match.group(1).strip()
                if "@" in email and "." in email.split("@")[1]:
                    result["email"] = email
                    break

        # Extract LinkedIn profile ID
        profile_id_match = re.search(r'voyagerProfileDashEntityUrn"[^>]*"urn:li:fs_normalized_profile:([^"]+)"', html)
        if profile_id_match:
            result["raw_data"]["profile_id"] = profile_id_match.group(1)

        result["success"] = result["name"] is not None
        return result

    def extract_company_domain(self, company_name: str) -> Optional[str]:
        """
        Guess company domain from company name.

        This is a simple heuristic - in production you'd use a company database.

        Returns guessed domain or None.
        """
        if not company_name:
            return None

        # Clean company name
        company_lower = company_name.lower().strip()

        # Remove common suffixes
        for suffix in [" inc", " inc.", " llc", " ltd", " ltd.", " corporation", " corp"]:
            if company_lower.endswith(suffix):
                company_lower = company_lower[: -len(suffix)].strip()

        # Replace spaces/special chars with nothing
        domain_candidate = re.sub(r'[^a-z0-9]', '', company_lower)

        # Common TLDs to try
        tlds = ["com", "io", "co", "net"]

        for tld in tlds:
            domain = f"{domain_candidate}.{tld}"
            # Don't return obviously fake domains
            if len(domain_candidate) >= 3 and not domain.startswith("company."):
                return domain

        return None


def scrape_linkedin_profile(profile_url: str) -> dict:
    """Convenience function to scrape a LinkedIn profile."""
    scraper = LinkedInScraper()
    return scraper.scrape_profile(profile_url)


def extract_company_domain(company_name: str) -> Optional[str]:
    """Convenience function to guess company domain."""
    scraper = LinkedInScraper()
    return scraper.extract_company_domain(company_name)