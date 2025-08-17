"""
GitHub fetching utilities using PyGithub.
Fetches package.json and lock files from a repository root.
"""
import json
import os
from typing import Dict, Optional
from github import Github, GithubException

DEFAULT_FILES = [
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
]


class GitHubFetcher:
    def __init__(self, token: Optional[str] = None):
        """
        token: GitHub token optional (env GITHUB_TOKEN recommended)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.gh = Github(self.token) if self.token else Github()  # unauthenticated allowed (rate-limited)

    def fetch_repo_root_files(self, owner_repo: str) -> Dict[str, str]:
        """
        Attempt to fetch usual dependency-related files from the repo root.
        Returns dict filename -> file content (string). Missing files are omitted.
        Raises GithubException on major failures.
        """
        try:
            repo = self.gh.get_repo(owner_repo)
        except GithubException as e:
            raise e

        contents = {}
        for fname in DEFAULT_FILES:
            try:
                file_content = repo.get_contents(fname)
                contents[fname] = file_content.decoded_content.decode("utf-8", errors="replace")
            except GithubException as e:
                # file not found -> ignore; other errors bubble up
                if getattr(e, "status", None) == 404:
                    continue
                else:
                    raise e
        return contents

    @staticmethod
    def parse_package_json(content: str) -> Dict:
        try:
            return json.loads(content)
        except Exception:
            return {}
