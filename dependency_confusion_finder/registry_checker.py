"""
Registry checker for npm.
Checks whether a package exists on the public npm registry and fetches latest version.
"""
import requests
from typing import Tuple, Optional

NPM_REGISTRY_URL = "https://registry.npmjs.org/"

class RegistryChecker:
    def __init__(self, timeout: float = 5.0, session: requests.Session = None):
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "DependencyConfusionFinder/0.1 (+https://github.com/)"})

    def npm_package_exists(self, package_name: str) -> Tuple[bool, Optional[str]]:
        """
        Returns (exists_on_npm, latest_version_or_none)
        Behavior:
          - 200: return (True, latest_version_if_available_or_None)
          - 404: return (False, None)
          - other network or server errors: return (True, None) to avoid false positives
        """
        url_name = package_name
        try:
            resp = self.session.get(NPM_REGISTRY_URL + url_name, timeout=self.timeout)
        except requests.RequestException:
            # Network error: treat conservatively as "unknown" => assume exists to avoid false positives
            return True, None

        if resp.status_code == 200:
            try:
                data = resp.json()
                latest = None
                dist_tags = data.get("dist-tags", {})
                latest = dist_tags.get("latest")
                if not latest:
                    versions = data.get("versions", {})
                    if versions:
                        latest = sorted(versions.keys())[-1]
                return True, latest
            except Exception:
                return True, None
        elif resp.status_code == 404:
            return False, None
        else:
            # 429, 5xx, etc. treat as unknown to avoid false positives
            return True, None
