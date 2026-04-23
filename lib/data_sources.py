"""
External data sources integration for email finding.

Integrates with:
- Business information APIs (TianYanCha, QiChaCha)
- Social media platforms (LinkedIn, Weibo)
- Public databases (GitHub, Stack Overflow)
- Custom data sources
"""

import json
import urllib.request
import urllib.error
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from pathlib import Path


class BaseDataSource(ABC):
    """Base class for external data sources."""

    name: str = "base"
    rate_limit: float = 1.0  # seconds between requests

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.last_request = 0

    def _rate_limit(self):
        """Enforce rate limiting."""
        now = time.time()
        elapsed = now - self.last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request = time.time()

    def _request(self, url: str, headers: dict = None, params: dict = None) -> Optional[dict]:
        """Make HTTP request and return JSON response."""
        self._rate_limit()

        try:
            # Add params to URL
            if params:
                from urllib.parse import urlencode
                url += '?' + urlencode(params)

            req = urllib.request.Request(url, headers=headers or {})
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}", "body": e.read().decode()}
        except Exception as e:
            return {"error": str(e)}

    @abstractmethod
    def search_person(self, name: str, company: str = None, domain: str = None) -> List[Dict]:
        """Search for a person across this data source."""
        pass

    @abstractmethod
    def search_company(self, company: str, domain: str = None) -> List[Dict]:
        """Search for company information."""
        pass


class TianYanChaSource(BaseDataSource):
    """TianYanCha (天眼查) business information API."""

    name = "tianyancha"
    rate_limit = 2.0  # Conservative rate limit

    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.base_url = "https://api.tianyancha.com"

    def search_person(self, name: str, company: str = None, domain: str = None) -> List[Dict]:
        """Search for person in TianYanCha."""
        if not self.api_key:
            return []

        results = []

        # Search for person as key person in companies
        endpoint = f"{self.base_url}/v3/search/person.json"
        params = {
            "keyword": name,
            "pageSize": 10,
            "apiKey": self.api_key
        }

        response = self._request(endpoint, params=params)
        if response and not response.get('error'):
            for person in response.get('result', {}).get('personList', []):
                results.append({
                    'source': self.name,
                    'type': 'person',
                    'name': person.get('name'),
                    'company': person.get('companyName'),
                    'position': person.get('position'),
                    'confidence': 0.7
                })

        return results

    def search_company(self, company: str, domain: str = None) -> List[Dict]:
        """Search for company in TianYanCha."""
        if not self.api_key:
            return []

        results = []

        endpoint = f"{self.base_url}/v3/search/company.json"
        params = {
            "keyword": company,
            "pageSize": 10,
            "apiKey": self.api_key
        }

        response = self._request(endpoint, params=params)
        if response and not response.get('error'):
            for comp in response.get('result', {}).get('companyList', []):
                results.append({
                    'source': self.name,
                    'type': 'company',
                    'name': comp.get('name'),
                    'credit_code': comp.get('creditCode'),
                    'phone': comp.get('phone'),
                    'email': comp.get('email'),
                    'website': comp.get('website'),
                    'address': comp.get('regLocation'),
                    'confidence': 0.8
                })

        return results


class QiChaChaSource(BaseDataSource):
    """QiChaCha (企查查) business information API."""

    name = "qichacha"
    rate_limit = 2.0

    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.base_url = "https://api.qichacha.com"

    def search_person(self, name: str, company: str = None, domain: str = None) -> List[Dict]:
        """Search for person in QiChaCha."""
        if not self.api_key:
            return []

        results = []

        endpoint = f"{self.base_url}/api/person/search"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        params = {
            "keyword": name,
            "page": 1,
            "size": 10
        }

        response = self._request(endpoint, headers=headers, params=params)
        if response and not response.get('error'):
            for person in response.get('data', {}).get('items', []):
                results.append({
                    'source': self.name,
                    'type': 'person',
                    'name': person.get('name'),
                    'company': person.get('company'),
                    'position': person.get('position'),
                    'confidence': 0.7
                })

        return results

    def search_company(self, company: str, domain: str = None) -> List[Dict]:
        """Search for company in QiChaCha."""
        if not self.api_key:
            return []

        results = []

        endpoint = f"{self.base_url}/api/company/search"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        params = {
            "keyword": company,
            "page": 1,
            "size": 10
        }

        response = self._request(endpoint, headers=headers, params=params)
        if response and not response.get('error'):
            for comp in response.get('data', {}).get('items', []):
                results.append({
                    'source': self.name,
                    'type': 'company',
                    'name': comp.get('name'),
                    'phone': comp.get('phone'),
                    'email': comp.get('email'),
                    'website': comp.get('website'),
                    'address': comp.get('address'),
                    'confidence': 0.8
                })

        return results


class GitHubSource(BaseDataSource):
    """GitHub public data source."""

    name = "github"
    rate_limit = 1.0

    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.base_url = "https://api.github.com"

    def search_person(self, name: str, company: str = None, domain: str = None) -> List[Dict]:
        """Search for person on GitHub."""
        results = []

        # Search users by name
        endpoint = f"{self.base_url}/search/users"
        params = {
            "q": f"fullname:{name}",
            "per_page": 10
        }

        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.api_key:
            headers["Authorization"] = f"token {self.api_key}"

        response = self._request(endpoint, headers=headers, params=params)
        if response and not response.get('error'):
            for user in response.get('items', []):
                # Get user details
                user_details = self._get_user_details(user['login'], headers)
                if user_details:
                    results.append({
                        'source': self.name,
                        'type': 'person',
                        'name': user_details.get('name'),
                        'login': user_details.get('login'),
                        'company': user_details.get('company'),
                        'email': user_details.get('email'),
                        'blog': user_details.get('blog'),
                        'location': user_details.get('location'),
                        'public_repos': user_details.get('public_repos'),
                        'confidence': 0.6
                    })

        return results

    def _get_user_details(self, username: str, headers: dict) -> Optional[Dict]:
        """Get detailed user information from GitHub."""
        endpoint = f"{self.base_url}/users/{username}"
        response = self._request(endpoint, headers=headers)
        return response if response and not response.get('error') else None

    def search_company(self, company: str, domain: str = None) -> List[Dict]:
        """Search for company on GitHub."""
        results = []

        # Search organizations
        endpoint = f"{self.base_url}/search/users"
        params = {
            "q": f"org:{company}",
            "per_page": 10
        }

        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.api_key:
            headers["Authorization"] = f"token {self.api_key}"

        response = self._request(endpoint, headers=headers, params=params)
        if response and not response.get('error'):
            for org in response.get('items', []):
                if org.get('type') == 'Organization':
                    org_details = self._get_user_details(org['login'], headers)
                    if org_details:
                        results.append({
                            'source': self.name,
                            'type': 'company',
                            'name': org_details.get('name'),
                            'login': org_details.get('login'),
                            'blog': org_details.get('blog'),
                            'location': org_details.get('location'),
                            'public_repos': org_details.get('public_repos'),
                            'confidence': 0.7
                        })

        return results


class StackOverflowSource(BaseDataSource):
    """Stack Overflow public data source."""

    name = "stackoverflow"
    rate_limit = 1.0

    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.base_url = "https://api.stackexchange.com/2.3"

    def search_person(self, name: str, company: str = None, domain: str = None) -> List[Dict]:
        """Search for person on Stack Overflow."""
        results = []

        endpoint = f"{self.base_url}/users"
        params = {
            "inname": name,
            "site": "stackoverflow",
            "pagesize": 10
        }

        if self.api_key:
            params["key"] = self.api_key

        response = self._request(endpoint, params=params)
        if response and not response.get('error'):
            for user in response.get('items', []):
                results.append({
                    'source': self.name,
                    'type': 'person',
                    'name': user.get('display_name'),
                    'user_id': user.get('user_id'),
                    'reputation': user.get('reputation'),
                    'location': user.get('location'),
                    'confidence': 0.5
                })

        return results

    def search_company(self, company: str, domain: str = None) -> List[Dict]:
        """Search for company on Stack Overflow."""
        # Stack Overflow doesn't have company pages like GitHub
        # We can search for users who mention the company
        return []


class DataSourceIntegrator:
    """Integrates multiple data sources for comprehensive search."""

    def __init__(self, config_file: str = None):
        self.sources = {}
        self.config = self._load_config(config_file)

    def _load_config(self, config_file: str = None) -> Dict:
        """Load data source configuration."""
        default_config = {
            'tianyancha': {'api_key': None, 'enabled': True},
            'qichacha': {'api_key': None, 'enabled': True},
            'github': {'api_key': None, 'enabled': True},
            'stackoverflow': {'api_key': None, 'enabled': True}
        }

        if config_file and Path(config_file).exists():
            try:
                with open(config_file) as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    for key, value in user_config.items():
                        if key in default_config:
                            default_config[key].update(value)
            except Exception:
                pass

        return default_config

    def add_source(self, source: BaseDataSource):
        """Add a data source."""
        self.sources[source.name] = source

    def initialize_sources(self):
        """Initialize all configured data sources."""
        # TianYanCha
        if self.config['tianyancha']['enabled']:
            tianyancha = TianYanChaSource(self.config['tianyancha']['api_key'])
            self.add_source(tianyancha)

        # QiChaCha
        if self.config['qichacha']['enabled']:
            qichacha = QiChaChaSource(self.config['qichacha']['api_key'])
            self.add_source(qichacha)

        # GitHub
        if self.config['github']['enabled']:
            github = GitHubSource(self.config['github']['api_key'])
            self.add_source(github)

        # Stack Overflow
        if self.config['stackoverflow']['enabled']:
            so = StackOverflowSource(self.config['stackoverflow']['api_key'])
            self.add_source(so)

    def search_person(self, name: str, company: str = None, domain: str = None) -> List[Dict]:
        """Search for person across all data sources."""
        results = []

        for source_name, source in self.sources.items():
            try:
                source_results = source.search_person(name, company, domain)
                results.extend(source_results)
            except Exception as e:
                print(f"Error searching {source_name}: {e}")

        # Sort by confidence
        results.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        return results

    def search_company(self, company: str, domain: str = None) -> List[Dict]:
        """Search for company across all data sources."""
        results = []

        for source_name, source in self.sources.items():
            try:
                source_results = source.search_company(company, domain)
                results.extend(source_results)
            except Exception as e:
                print(f"Error searching {source_name}: {e}")

        # Sort by confidence
        results.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        return results

    def enrich_email_search(self, name: str, domain: str) -> Dict:
        """Enrich email search with external data."""
        company_name = domain.split('.')[0] if domain else None

        # Search for person and company
        person_results = self.search_person(name, company_name, domain)
        company_results = self.search_company(company_name, domain)

        # Extract useful information
        enrichment = {
            'person_data': person_results,
            'company_data': company_results,
            'suggested_emails': [],
            'confidence_boost': 0
        }

        # Extract emails from results
        for result in person_results + company_results:
            if result.get('email') and '@' in result['email']:
                enrichment['suggested_emails'].append({
                    'email': result['email'],
                    'source': result.get('source'),
                    'confidence': result.get('confidence', 0)
                })

        # Boost confidence if we found relevant data
        if person_results:
            enrichment['confidence_boost'] += 0.2
        if company_results:
            enrichment['confidence_boost'] += 0.1

        return enrichment