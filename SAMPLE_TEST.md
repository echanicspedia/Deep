````markdown
```markdown
# Sample test: Demonstration of DependencyConfusionFinder

This sample demonstrates running DependencyConfusionFinder locally with a small JS file.

1. Create a sample JS file `example/script.js`:

```js
// example/script.js
const secret = require('internal-private-package');
import express from 'express';
import localmod from './lib/localmod';
const scoped = require('@myorg/notpublished');
```

2. Optional: create a sample `package.json` in a GitHub test repo that declares `internal-private-package` as dependency.

For demonstration using a real public GitHub repo:
- Suppose you have a repo at `https://github.com/youruser/testrepo` with a `package.json` that lists `internal-private-package`.

3. Run (ensure GITHUB_TOKEN env var set to avoid rate limit):
```bash
GITHUB_TOKEN=ghp_xxx python -m dependency_confusion_finder.main https://github.com/youruser/testrepo example/script.js
```

Expected output (example):
```
internal-private-package@^1.2.3
@myorg/notpublished@unknown
```

Notes:
- `express` is published on npm -> not listed.
- `./lib/localmod` is a relative import -> ignored.
- If a package is in `package-lock.json`, version from the lockfile will be preferred.
```
````
