# AGENTS.md — Blog Posts

**Who:** Persephone (writing), Oracle (research), Cypher (publishing)

## Guardrails

1. **Always use frontmatter template:**
```yaml
---
layout: post
title: "Title"
date: 2026-03-18
description: "Description under 160 chars"
author: "Persephone"
tags: [tag1, tag2]
---
```

2. **Preview before commit:**
   - Run `npm run build` and check `_site/blog/` output
   - Verify header/nav renders correctly
   - Check mobile layout

3. **No breaking builds:**
   - Posts go to `src/blog/` (NOT `_posts/`)
   - Must pass `npm run build` without errors

4. **Quality:**
   - Include sources at bottom
   - Proofread for grammar
   - SEO: title + description in frontmatter

## Process
1. Research → Write → Save to `src/blog/`
2. Commit to feature branch → PR to staging
3. Preview builds → Verify formatting
4. Merge to main → Auto-posts to Twitter/Reddit
