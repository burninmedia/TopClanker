# TopClanker — Team Guide

How to manage the site: adding blog posts, updating rankings, and understanding how everything gets built and deployed.

---

## Table of Contents

1. [How the site works (quick overview)](#how-the-site-works)
2. [Writing a new blog post](#writing-a-new-blog-post)
3. [Updating the LLM rankings](#updating-the-llm-rankings)
4. [How builds and deploys work](#how-builds-and-deploys-work)
5. [File structure reference](#file-structure-reference)
6. [What not to do](#what-not-to-do)

---

## How the site works

TopClanker now uses **Eleventy**, a static site generator. Instead of hand-editing HTML files for every page, you edit simple source files and Eleventy compiles them into the final site.

- **Source files** live in `src/`
- **Built output** goes to `_site/` (auto-generated, never edit directly)
- **Netlify** runs the build automatically on every push and deploys `_site/`

The nav, footer, colors, fonts, and page structure are defined once in shared layout files. Every page automatically gets the same look — you never have to think about styling when writing content.

---

## Writing a new blog post

### Step 1 — Create the file

Create a new `.md` file inside `src/blog/`. Name it using the date and a short slug:

```
src/blog/2026-03-20-your-post-title-here.md
```

Use the format `YYYY-MM-DD-slug.md`. The date controls where the post appears in the listing (newest first). The slug becomes the URL: `/blog/2026-03-20-your-post-title-here/`.

### Step 2 — Add the frontmatter

Every post starts with a frontmatter block between two sets of `---`. Copy this template exactly:

```markdown
---
layout: post
title: "Your Post Title Goes Here"
date: 2026-03-20
description: "One or two sentences for SEO. This appears in Google results and social shares."
author: "TopClanker"
tags: [ai, open-source]
---

Your content starts here.
```

| Field | Required | Notes |
|-------|----------|-------|
| `layout` | **Yes** | Always `post` — do not change this |
| `title` | **Yes** | Shown as the page heading and in the blog listing |
| `date` | **Yes** | Format: `YYYY-MM-DD` — controls sort order |
| `description` | **Yes** | Used for SEO meta description and social sharing |
| `author` | No | Displayed under the title. Use `"TopClanker"` or your name |
| `tags` | No | Array of strings. Not currently displayed, but useful for future filtering |

### Step 3 — Write the content

Everything below the closing `---` is your post. Use standard Markdown:

```markdown
---
layout: post
title: "GPT-6 Just Dropped — Here's What Actually Matters"
date: 2026-04-01
description: "OpenAI released GPT-6 today. We cut through the hype and tell you what changed."
author: "TopClanker"
tags: [openai, gpt, benchmarks]
---

OpenAI dropped GPT-6 this morning and the internet lost its mind. Here's what's actually different.

## The benchmark numbers

| Benchmark | GPT-5 | GPT-6 |
|-----------|-------|-------|
| MMLU      | 88%   | 93%   |
| HumanEval | 90%   | 95%   |

## Should you switch?

If you're doing heavy coding tasks, yes. For everything else, the difference is marginal...
```

**Markdown cheat sheet:**

```
## Heading 2
### Heading 3

**bold text**
*italic text*

- bullet list item
- another item

1. numbered list
2. second item

[link text](https://example.com)

| Column 1 | Column 2 |
|----------|----------|
| value    | value    |
```

### Step 4 — Push and it's live

```bash
git add src/blog/2026-03-20-your-post-title-here.md
git commit -m "Add blog post: your post title here"
git push origin staging
```

Netlify picks up the push, runs the build (about 1–2 minutes), and the post is live. The home page "Recent Posts" section and the `/blog/` listing both update automatically — no other files to touch.

---

## Updating the LLM rankings

All rankings data lives in one file: **`src/data.json`**

Open it, make your changes, commit, and push. The rankings table updates on next deploy.

### Adding a new model

Find the `"agents"` array in `src/data.json` and add a new entry. Here's the full structure:

```json
{
  "rank": 3,
  "name": "GPT-6",
  "category": "reasoning",
  "type": "closed",
  "privacy": "medium",
  "score": 99,
  "benchmarkScore": 91,
  "link": "https://openai.com",
  "description": "One sentence description of what makes this model notable.",
  "benchmarks": {
    "mmlu": 93,
    "humaneval": 95,
    "gsm8k": 97
  }
}
```

**Field reference:**

| Field | Type | Values / Notes |
|-------|------|----------------|
| `rank` | number | Displayed rank position. Also update other entries if ranks shift. |
| `name` | string | Model name as displayed on site |
| `category` | string | `"reasoning"`, `"coding"`, `"research"`, `"math"`, `"learning"`, `"general"` |
| `type` | string | `"closed"` (API/cloud only) or `"open-source"` (weights available) |
| `privacy` | string | `"high"`, `"medium"`, `"low"` — how private is your data when using it? |
| `score` | number | Overall TopClanker score, 1–100. Controls ranking order. |
| `benchmarkScore` | number | Average across key benchmarks shown in the table |
| `link` | string | Official model/product URL |
| `description` | string | Short one-liner shown in the table |
| `benchmarks` | object | Key/value pairs of benchmark name → score (number, percentage without %) |

**Common benchmark keys:**

| Key | What it measures |
|-----|-----------------|
| `mmlu` | General knowledge (Massive Multitask Language Understanding) |
| `humaneval` | Coding ability |
| `gsm8k` | Math word problems |
| `gpqa` | Graduate-level science questions |
| `swebench` | Real-world software engineering tasks |
| `math` | Competition math |
| `aime` | High school math olympiad |
| `arenaElo` | Chatbot Arena ELO rating (community head-to-head voting) |

You don't need every benchmark — just include the ones you have reliable data for.

### Updating an existing model's rank or score

Find the model in `src/data.json`, edit the values, and update the `rank` field and any other entries whose ranks shifted.

Also update the `"lastUpdated"` field at the top of the file:

```json
{
  "lastUpdated": "2026-04-01",
  "agents": [...]
}
```

### Adding a local/open-source model

After adding the model to `src/data.json` with `"type": "open-source"`, you also need to add its name to the local model list in **`src/app.js`**. Search for `isLocalModel` and add the model name to the array:

```js
// Find this in src/app.js:
const localModels = [
  'Llama 3.3 70B',
  'DeepSeek V3',
  'Qwen 2.5 Ultra',
  // ... add your new model name here, exactly as in data.json:
  'GLM-5',
];
```

This is what makes the "Local Only" and Apple Silicon filters work correctly.

### Removing a model

Delete its entry from the `"agents"` array in `src/data.json`, and update the `rank` values of remaining models.

---

## How builds and deploys work

```
You push to GitHub
        ↓
Netlify detects the push
        ↓
Netlify runs: npm run build
  (Tailwind CSS → output.css, then Eleventy → _site/)
        ↓
Netlify deploys _site/ to topclanker.com (or preview URL for PRs)
        ↓
GitHub Actions waits 60 seconds for Netlify to finish
        ↓
GitHub Actions pings Google and Bing with the sitemap URL
  so search engines re-index the updated content
```

### Branch workflow

| Branch | What it does |
|--------|-------------|
| `staging` | Deploys to the staging preview of topclanker.com |
| `master` | Deploys to production (live topclanker.com) |
| Any PR branch | Gets its own Netlify deploy preview URL for review |

For most updates, the workflow is:
1. Create a branch or work directly on `staging`
2. Push → review on the Netlify preview URL
3. Open a PR and merge to `master` when ready

### The sitemap is automatic

`sitemap.xml` is generated by Eleventy at build time from `src/sitemap.njk`. It always includes:
- All static pages (home, methodology, privacy, blog index)
- Every markdown blog post with its actual publish date as `<lastmod>`

You never need to manually edit the sitemap. Every deploy keeps it current.

### Running the site locally

```bash
# First time only:
npm install

# Start local dev server (auto-reloads on save):
npm run watch

# Open http://localhost:8080
```

To do a full production build locally:
```bash
npm run build
# Output is in _site/
```

---

## File structure reference

```
src/
├── _data/
│   └── site.js              ← Site name, URL, year (rarely needs changing)
│
├── _includes/
│   └── layouts/
│       ├── base.njk         ← Shared shell: <head>, nav, footer, AdSense
│       └── post.njk         ← Blog post layout (extends base)
│
├── blog/
│   ├── index.njk            ← Blog listing page (do not edit often)
│   ├── *.md                 ← ✅ New blog posts go here
│   └── *.html               ← Legacy posts (preserved, do not add new ones)
│
├── app.js                   ← Rankings filter/sort logic + isLocalModel() list
├── data.json                ← ✅ LLM rankings data — edit this to update rankings
├── index.njk                ← Home page template
├── methodology.njk          ← Methodology page
├── privacy.njk              ← Privacy policy
├── sitemap.njk              ← Generates sitemap.xml at build time (do not edit)
├── style.css                ← Custom styles (beyond Tailwind)
└── robots.txt               ← SEO robots rules
```

---

## What not to do

**Do not create new `.html` files in `src/blog/`.**
The old HTML blog posts are kept for backwards compatibility, but they each contain their own full HTML with inconsistent styling. Any new post written as raw HTML will look different from the rest of the site. Always use Markdown.

**Do not edit files in `_site/`.**
This folder is auto-generated on every build and gets completely replaced. Any changes you make there will be lost on the next deploy.

**Do not edit `src/output.css`.**
This is generated by Tailwind from `src/input.css`. Edit `src/input.css` if you need custom CSS, but in practice you rarely need to — use Tailwind utility classes in the template files instead.

**Do not change `"layout": "post"` in blog post frontmatter.**
This is what connects the post to the shared styling. Remove it and the post will render without the nav, footer, or any site styling.
