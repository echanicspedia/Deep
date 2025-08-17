"""
DependencyConfusionFinder - main orchestrator
"""
import argparse
import json
import os
from typing import Dict, List

from .github_fetcher import GitHubFetcher
from .js_parser import extract_packages_from_js
from .registry_checker import RegistryChecker
from .utils import (
    normalize_repo_url,
    is_relative_import,
)

NODE_PACKAGE_FIELDS = ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies"]


class DependencyConfusionFinder:
    def __init__(self, github_token: str = None, verbose: bool = False):
        self.github_token = github_token
        self.verbose = verbose
        self.gh_fetcher = GitHubFetcher(token=github_token)
        self.registry = RegistryChecker()

    def _log(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def analyze(self, repo_url: str, js_file_path: str) -> List[str]:
        """
        Main analysis. Returns list of vulnerable dependencies formatted 'package@version'
        """
        owner_repo = normalize_repo_url(repo_url)
        self._log("Normalized repo:", owner_repo)

        # Fetch repo files
        try:
            repo_files = self.gh_fetcher.fetch_repo_root_files(owner_repo)
        except Exception as e:
            raise RuntimeError("Failed to fetch repository files: {}".format(e))

        self._log("Fetched files from repo:", list(repo_files.keys()))

        package_json = {}
        package_lock = {}
        if "package.json" in repo_files:
            package_json = self.gh_fetcher.parse_package_json(repo_files["package.json"]) or {}
        if "package-lock.json" in repo_files:
            try:
                package_lock = json.loads(repo_files["package-lock.json"]) or {}
            except Exception:
                package_lock = {}

        # Gather declared dependencies (name -> version)
        declared_deps: Dict[str, str] = {}
        for field in NODE_PACKAGE_FIELDS:
            deps = package_json.get(field, {}) or {}
            for k, v in deps.items():
                declared_deps[k] = v

        # Add versions from package-lock if available (more accurate)
        lock_deps = {}
        if "dependencies" in package_lock and isinstance(package_lock["dependencies"], dict):
            for k, v in package_lock["dependencies"].items():
                ver = v.get("version")
                if ver:
                    lock_deps[k] = ver

        # Parse local JS file
        if not os.path.exists(js_file_path):
            raise FileNotFoundError("JS file not found: {}".format(js_file_path))
        with open(js_file_path, "r", encoding="utf-8") as f:
            js_source = f.read()

        packages_in_js = extract_packages_from_js(js_source)
        self._log("Packages referenced in JS:", packages_in_js)

        # Merge packages found in JS and declared in package.json
        all_candidates = set(packages_in_js) | set(declared_deps.keys())
        self._log("Combined candidate packages:", all_candidates)

        vulnerable = []

        for pkg in sorted(all_candidates):
            # Skip if pkg is relative or empty (shouldn't be)
            if is_relative_import(pkg):
                continue
            # Determine best-known version
            version = None
            if pkg in lock_deps:
                version = lock_deps[pkg]
            elif pkg in declared_deps:
                version = declared_deps[pkg]
            # Query npm
            exists, latest = self.registry.npm_package_exists(pkg)
            self._log("Registry check for {}: exists={}, latest={}".format(pkg, exists, latest))
            if not exists:
                vstr = version or "unknown"
                vulnerable.append("{}@{}".format(pkg, vstr))
            # else: package exists on npm -> skip (not vulnerable)
        return vulnerable

def main():
    parser = argparse.ArgumentParser(description="DependencyConfusionFinder - detect dependency confusion candidates")
    parser.add_argument("repo", help="GitHub repository URL (e.g., https://github.com/owner/repo)")
    parser.add_argument("jsfile", help="Local JavaScript file to analyze (e.g., script.js)")
    parser.add_argument("--token", "-t", help="GitHub token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    finder = DependencyConfusionFinder(github_token=(args.token or os.getenv("GITHUB_TOKEN")), verbose=args.verbose)
    try:
        vulnerable = finder.analyze(args.repo, args.jsfile)
    except Exception as e:
        print("ERROR: {}".format(e))
        raise SystemExit(2)

    # Output only vulnerable dependencies unless verbose
    for entry in vulnerable:
        print(entry)

if __name__ == "__main__":
    main()
