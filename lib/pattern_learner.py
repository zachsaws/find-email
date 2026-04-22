"""
LLM-based email pattern learner.

Uses MiniMax API to analyze a company's email format from known email samples.
"""

import os
import json
import re
from typing import Optional


class PatternLearner:
    """
    Learn company email format patterns using LLM.

    Given a domain and one or more known email addresses from that domain,
    the LLM can infer the company's email format convention.
    """

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.environ.get("MINIMAX_API_KEY")
        self.base_url = base_url or os.environ.get(
            "MINIMAX_BASE_URL",
            "https://api.minimax.chat/v1"
        )

    def learn_from_emails(self, domain: str, known_emails: list[str]) -> dict:
        """
        Analyze known emails to infer the company's email format.

        Args:
            domain: Company domain (e.g., "tencent.com")
            known_emails: List of known email addresses from this domain

        Returns dict with:
            - success: bool
            - pattern: str (e.g., "firstname.lastname", "flast", etc.)
            - confidence: 'high', 'medium', 'low'
            - examples: list of generated example emails
            - reasoning: str (LLM's explanation)
        """
        if not self.api_key:
            return {
                "success": False,
                "pattern": None,
                "confidence": "none",
                "examples": [],
                "reasoning": "No MiniMax API key found (set MINIMAX_API_KEY env var)"
            }

        if not known_emails:
            return {
                "success": False,
                "pattern": None,
                "confidence": "none",
                "examples": [],
                "reasoning": "No known emails provided"
            }

        # Extract local parts (everything before @)
        local_parts = []
        for email in known_emails:
            local = email.split("@")[0] if "@" in email else email
            local_parts.append(local.lower())

        # Build prompt for LLM
        prompt = self._build_analysis_prompt(domain, local_parts)

        try:
            result = self._call_llm(prompt)
            return result
        except Exception as e:
            return {
                "success": False,
                "pattern": None,
                "confidence": "none",
                "examples": [],
                "reasoning": f"LLM call failed: {str(e)}"
            }

    def _build_analysis_prompt(self, domain: str, local_parts: list[str]) -> str:
        """Build the analysis prompt for the LLM."""
        examples = "\n".join([f"  - {p}@{domain}" for p in local_parts])

        return f"""分析以下公司邮箱格式，推断其邮件命名规则。

公司域名: {domain}

已知邮箱示例:
{examples}

请分析并返回以下格式的JSON（不带markdown代码块）:
{{
  "pattern": "推断出的格式模式，如 firstname.lastname, flast, firstname_last, fl 等",
  "confidence": "推断置信度: high, medium, 或 low",
  "reasoning": "推断理由，简短说明为什么认为是这个格式",
  "examples": ["基于此格式生成的示例邮箱，3-5个"]
}}

常见格式参考:
- firstname.lastname: zhang.wei
- firstname: zhangwei
- flast: zwei (zhang.wei 的首字母+zhang -> zwei)
- firstname_last: zhang_wei
- f.last: z.wei
- firstname.l: zhang.wei

注意：如果邮箱是中文拼音格式（如zhangwei），通常意味着公司使用firstname格式；
如果邮箱包含姓名字母缩写（如zwei），通常是flast格式。"""

    def _call_llm(self, prompt: str) -> dict:
        """Call MiniMax API to analyze email patterns."""
        import urllib.request
        import urllib.error

        url = f"{self.base_url}/text/chatcompletion_v2"

        payload = json.dumps({
            "model": "MiniMax-Text-01",
            "messages": [
                {"role": "system", "content": "你是一个邮箱格式分析专家。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }).encode()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise Exception(f"API Error {e.code}: {error_body}")

        # Parse response
        try:
            content = data["choices"][0]["message"]["content"]

            # Try to extract JSON from the response
            # The LLM might wrap it in ```json or just return raw JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Try parsing the whole content as JSON
                result = json.loads(content)

            return {
                "success": True,
                "pattern": result.get("pattern", "unknown"),
                "confidence": result.get("confidence", "low"),
                "reasoning": result.get("reasoning", ""),
                "examples": result.get("examples", [])
            }
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            return {
                "success": False,
                "pattern": None,
                "confidence": "none",
                "examples": [],
                "reasoning": f"Failed to parse LLM response: {str(e)}. Raw: {content[:200] if content else 'empty'}"
            }


class PatternCache:
    """
    Local cache for learned company email patterns.

    Stores patterns in ~/.find-email-patterns.json
    """

    def __init__(self, cache_path: str = None):
        import os
        home = os.path.expanduser("~")
        self.cache_path = cache_path or os.path.join(home, ".find-email-patterns.json")
        self._cache = self._load()

    def _load(self) -> dict:
        """Load cache from disk."""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path) as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        """Save cache to disk."""
        try:
            with open(self.cache_path, "w") as f:
                json.dump(self._cache, f, indent=2)
        except Exception:
            pass

    def get(self, domain: str) -> Optional[dict]:
        """Get cached pattern for domain."""
        return self._cache.get(domain)

    def set(self, domain: str, pattern_data: dict):
        """Cache a pattern for domain."""
        self._cache[domain] = pattern_data
        self._save()

    def clear(self, domain: str = None):
        """Clear cache for specific domain or all."""
        if domain:
            self._cache.pop(domain, None)
        else:
            self._cache = {}
        self._save()