Check the health of all source fetchers by running each one and reporting results.

For each fetcher module in `agents/fetcher/sources/`:
1. Import and call `fetch()`
2. Record: items returned, any errors, response time

Present a summary table:
| Source | Status | Items | Notes |
|--------|--------|-------|-------|

Flag any sources returning 0 items or throwing errors. Suggest fixes for broken sources.
