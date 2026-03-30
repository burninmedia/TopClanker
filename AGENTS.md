# AGENTS.md — TopClanker

**Who:** The Team

## Directories

| Folder | Purpose | Agent |
|--------|---------|-------|
| `src/blog/` | Blog posts | Persephone |
| `src/` | Rankings data, homepage | Oracle/Cypher |
| `scripts/` | Automation | Cypher |

## Golden Rules

1. **Never break the build** — always run `npm run build` before committing
2. **Preview first** — check deploy preview before merging PRs
3. **Staging → Main** — all changes go through staging
4. **Sources required** — any data claims need sources cited

## Blog Post Checklist
- [ ] `layout: post` in frontmatter
- [ ] Goes to `src/blog/` (NOT `_posts/`)
- [ ] Passes build
- [ ] Has sources at bottom

## Rankings Checklist
- [ ] Updated `lastUpdated` in data.json
- [ ] Benchmarks sourced
- [ ] Passes build
- [ ] Homepage renders correctly
