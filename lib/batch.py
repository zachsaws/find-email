"""
Batch processing for email finding.

Supports CSV input/output and result caching.
"""

import csv
import json
import os
from pathlib import Path
from typing import Optional


class ResultCache:
    """
    Cache verified email results.

    Stores in ~/.find-email-cache.json
    Format: {
        "email@example.com": {
            "valid": true,
            "confidence": "high",
            "verified_at": "2024-01-01T00:00:00",
            "methods": {...}
        }
    }
    """

    def __init__(self, cache_path: str = None):
        home = os.path.expanduser("~")
        self.cache_path = cache_path or os.path.join(home, ".find-email-cache.json")
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

    def get(self, email: str) -> Optional[dict]:
        """Get cached result for an email."""
        return self._cache.get(email.lower())

    def set(self, email: str, result: dict):
        """Cache a verification result."""
        import datetime
        self._cache[email.lower()] = {
            "valid": result.get("valid", False),
            "confidence": result.get("confidence", "none"),
            "verified_at": datetime.datetime.now().isoformat(),
            "methods": result.get("methods", {})
        }
        self._save()

    def clear(self, email: str = None):
        """Clear cache for specific email or all."""
        if email:
            self._cache.pop(email.lower(), None)
        else:
            self._cache = {}
        self._save()

    def size(self) -> int:
        """Return number of cached entries."""
        return len(self._cache)


def read_csv_input(csv_path: str) -> list[dict]:
    """
    Read CSV file with person information.

    Expected columns:
    - name: Person's name (required)
    - domain: Company domain (required)
    - first_name: English first name (optional)
    - last_name: English last name (optional)
    - duplicate: "true" or "false" (optional)
    - linkedin: LinkedIn profile URL (optional)

    Returns list of dicts with person info.
    """
    people = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            person = {
                "name": row.get("name", "").strip(),
                "domain": row.get("domain", "").strip(),
                "english_first": row.get("first_name", "").strip() or None,
                "english_last": row.get("last_name", "").strip() or None,
                "has_duplicate": row.get("duplicate", "").lower() == "true",
                "linkedin": row.get("linkedin", "").strip() or None,
            }
            if person["name"] and person["domain"]:
                people.append(person)
    return people


def write_csv_output(results: list[dict], csv_path: str):
    """
    Write results to CSV file.

    Columns: name, domain, email, valid, confidence, pattern, methods
    """
    if not results:
        return

    fieldnames = ["name", "domain", "email", "valid", "confidence", "pattern", "methods"]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            row = {
                "name": r.get("name", ""),
                "domain": r.get("domain", ""),
                "email": r.get("email", ""),
                "valid": str(r.get("valid", "")),
                "confidence": r.get("confidence", ""),
                "pattern": r.get("pattern", ""),
                "methods": json.dumps(r.get("methods", {}), ensure_ascii=False)
            }
            writer.writerow(row)


def write_json_output(results: list[dict], json_path: str):
    """Write results to JSON file."""
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)