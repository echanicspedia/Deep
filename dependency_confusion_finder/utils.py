"""
Utility helpers for DependencyConfusionFinder
"""
import re
from urllib.parse import urlparse

NODE_CORE_MODULES = {
    "assert", "buffer", "child_process", "cluster", "console", "constants",
    "crypto", "dgram", "dns", "domain", "events", "fs", "http", "https",
    "http2", "inspector", "module", "net", "os", "path", "perf_hooks",
    "process", "punycode", "querystring", "readline", "repl", "stream",
    "string_decoder", "tls", "tty", "url", "util", "v8", "vm", "zlib"
}

def _remove_suffix(text: str, suffix: str) -> str:
    if text.endswith(suffix):
        return text[:-len(suffix)]
    return text

def normalize_repo_url(url: str):
    """
    Normalize GitHub repo URL to owner/repo.
    Accepts:
      - https://github.com/owner/repo
      - git@github.com:owner/repo.git
      - https://github.com/owner/repo.git
    Returns 'owner/repo' or raises ValueError.
    """
    if url.startswith("git@"):
        # git@github.com:owner/repo.git
        try:
            path = url.split(":", 1)[1]
        except IndexError:
            raise ValueError("Invalid git@ URL")
        path = _remove_suffix(path, ".git")
        if path.count("/") != 1:
            raise ValueError("Could not parse owner/repo from URL")
        return path
    parsed = urlparse(url)
    if parsed.netloc not in ("github.com", "www.github.com"):
        raise ValueError("Only GitHub URLs are supported in this version")
    path = parsed.path.lstrip("/")
    path = _remove_suffix(path, ".git").rstrip("/")
    parts = path.split("/")
    if len(parts) < 2:
        raise ValueError("Repository URL must include owner and repo")
    return "/".join(parts[:2])

def is_relative_import(specifier: str) -> bool:
    return isinstance(specifier, str) and (specifier.startswith(".") or specifier.startswith("/"))

def get_base_package_name(specifier: str) -> str:
    """
    Given an import/require specifier, extract the base package name.
    Examples:
      lodash -> lodash
      lodash/fp -> lodash
      @org/pkg -> @org/pkg
      @org/pkg/sub -> @org/pkg
    """
    if not isinstance(specifier, str):
        return specifier
    if specifier.startswith("@"):
        parts = specifier.split("/")
        if len(parts) >= 2:
            return "{}/{}".format(parts[0], parts[1])
        return specifier
    return specifier.split("/")[0]

def looks_like_package(specifier: str) -> bool:
    """
    Return True if the import specifier looks like an external package.
    """
    if not specifier or not isinstance(specifier, str):
        return False
    if is_relative_import(specifier):
        return False
    if specifier in NODE_CORE_MODULES:
        return False
    # Discard URL imports or protocol (http:, git+, etc.)
    if ":" in specifier and not specifier.startswith("@"):
        return False
    # Accept scoped and unscoped packages; basic sanity check
    # Allow things like @scope/name or name/subpath
    if re.match(r"^@?[^@\s/][^@\s]*(/[^@\s/][^@\s]*)?", specifier):
        return True
    return False
