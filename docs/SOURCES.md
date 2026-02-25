# Source Registry

Machine-readable source definitions. Claude Code: populate this during implementation.
The fetcher agent should load source definitions from here or from `shared/config.py`.

## Format

Each source entry:

```yaml
- id: github_wan_video
  name: Wan-Video (Alibaba)
  category: models
  method: atom_feed
  url: https://github.com/Wan-AI/Wan-Video/releases.atom
  frequency: daily
  enabled: true
  keywords_filter: []  # empty = no filter needed
  notes: "Primary Wan2.x release tracking"
```

## Sources

TODO: Populate during implementation using data from SOURCE_EXPLORATION.md.
