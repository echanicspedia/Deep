````markdown
```markdown
# DependencyConfusionFinder

DependencyConfusionFinder is a Python 3.8+ command-line tool to detect potential dependency confusion vulnerabilities in JavaScript projects. It combines ideas from existing tools (Confuser, Confused, DepFuzzer, Dependency Combobulator) into a single modular scanner that:

- Extracts package names from a provided JavaScript file (imports / require calls).
- Fetches repository dependency files (package.json, package-lock.json, yarn.lock, pnpm-lock.yaml) from a GitHub repository.
- Checks package names against the public npm registry to identify package names that are not published (and therefore potentially hijackable).
- Outputs only vulnerable dependencies in the concise format `package@version` (or `package@unknown` if version not resolvable).

This tool prioritizes low false positives by:
- Ignoring relative imports and Node core modules.
- Treating network/registry errors conservatively (avoids marking as vulnerable if registry status is unknown).
- Cross-referencing package.json and package-lock.json for version data.

## Features

- Modular Python package (PyGithub, requests, esprima).
- CLI with single-line output per vulnerable dependency.
- Verbose mode for diagnostics and debugging.
- Extensible architecture to add other registries (PyPI, RubyGems) in future.

## Requirements

- Python 3.8+
- pip packages:
  - PyGithub
  - requests
  - esprima

Install dependencies:
```bash
python -m pip install -r requirements.txt
```

Example requirements.txt:
```
PyGithub>=1.59
requests>=2.25
esprima>=4.0
```

## Usage

Basic:
```bash
python -m dependency_confusion_finder.main https://github.com/owner/repo ./script.js
```

With GitHub token (recommended to avoid rate limits):
```bash
GITHUB_TOKEN=ghp_... python -m dependency_confusion_finder.main https://github.com/owner/repo ./script.js
# or
python -m dependency_confusion_finder.main https://github.com/owner/repo ./script.js --token ghp_...
```

Verbose diagnostics:
```bash
python -m dependency_confusion_finder.main https://github.com/owner/repo ./script.js --verbose
```

Output: Each vulnerable dependency on a new line in `package@version` format (only vulnerable ones printed).

## Example

Given `script.js`:
```js
const secret = require('internal-private-package');
import '@myorg/unfinished';
const fs = require('fs'); // core module ignored
```

And a GitHub repo whose package.json declares:
```json
{
  "dependencies": {
    "internal-private-package": "^1.0.0"
  }
}
```

Running the tool prints:
```
internal-private-package@^1.0.0
@myorg/unfinished@unknown
```

## Error handling

- Invalid repo URL -> error
- Missing JS file -> error
- GitHub API rate limit or permission errors surface meaningful messages. Provide a `GITHUB_TOKEN` to mitigate.
- Network/registry errors: treated conservatively (assumed non-vulnerable to reduce false positives).

## Testing strategy

1. Unit tests for:
   - JS parser: ensure imports, requires (static) and scoped packages are parsed.
   - Utils: normalize_repo_url, get_base_package_name, filter logic.
   - Registry checker: mock requests responses (200, 404, 500) to validate behavior.

2. Integration tests:
   - Create a set of small GitHub test repositories (public) and local JS files:
     - Repo A: declares `private-package` in package.json but not published -> should be flagged.
     - Repo B: uses `lodash` in JS -> should not be flagged.
     - Repo C: imports relative modules -> ignored.

3. Benchmarking against existing tools:
   - Select corpus of repos that previous tools were evaluated against.
   - Run Confuser, Confused, DepFuzzer, Dependency Combobulator and this tool.
   - Compute precision/recall based on a ground-truth annotated dataset.

## Limitations & Future Work

- Root-level files only; monorepos and workspaces improvement planned.
- Yarn/pnpm lock parsing can be added.
- Optional aggressive mode can be added for red-team use.

## License

MIT
````
