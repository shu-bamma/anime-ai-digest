Test a single source fetcher in isolation by calling its `fetch()` function directly.

Run this Python snippet, replacing the source name with $ARGUMENTS (e.g., `github_releases`, `civitai`, `arxiv`):

```
python -c "
from agents.fetcher.sources.$ARGUMENTS import fetch
items = fetch()
print(f'Fetched {len(items)} items')
for item in items[:3]:
    print(f'  - [{item.get(\"source_category\")}] {item.get(\"title\", \"\")}')
    print(f'    {item.get(\"url\", \"\")}')
"
```

Report: number of items returned, any errors logged, and show the first 3 items with title/url/category.
