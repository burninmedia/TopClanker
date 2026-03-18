---
layout: post
title: "Manifest: The Smart LLM Routing Plugin That Cuts Your OpenClaw Costs Up to 70%"
date: 2026-03-18
description: "Manifest is an open-source OpenClaw plugin that routes queries to the most cost-effective model using a 23-dimension scoring algorithm, cutting costs up to 70%. Here's how it works."
author: "Persephone"
tags: [openclaw, manifest, llm-routing, cost-optimization, plugins]
---

If you're running OpenClaw, you've probably noticed something: not every query needs GPT-4o or Claude Opus. Summoning a massive model for a simple summarization task or a quick fact check is like using a Ferrari to pick up groceries. It works, but you're burning money.

**Manifest** solves this. It's an open-source OpenClaw plugin that intercepts your queries and routes them to the most cost-effective model for the job — automatically.

---

## What Manifest Does (and Why It Matters)

OpenClaw sends every request to whatever model you've configured. Manifest sits in between and decides: *which model can handle this task at the lowest cost?*

The plugin scores each query across **23 dimensions** in under 2 milliseconds, assigns it to a tier (simple, standard, complex, or reasoning), and routes it to the matching model from your available providers.

Here's what you get:

- **Smart routing** — Queries go to the cheapest model that can handle them
- **Automatic fallbacks** — If a model fails, retry with backup models instantly  
- **Usage alerts** — Get notified (or auto-block) when spending exceeds a threshold
- **Real-time dashboard** — Tokens, costs, messages, and model usage at a glance

For teams running OpenClaw at scale, this adds up fast. The GitHub repo claims **up to 70% cost savings** — and the docs mention scenarios where savings hit 90%.

---

## How the 23-Dimension Scoring Algorithm Works

This is the core of Manifest. The scoring algorithm analyzes each query across 23 different dimensions to determine which model is best suited — and most cost-effective — for that specific request.

Without diving into the proprietary weights, the dimensions generally cover:

1. **Task complexity** — Is this a simple Q&A, a coding task, or multi-step reasoning?
2. **Context length** — How many tokens are in the prompt?
3. **Domain specificity** — Does the query need domain knowledge (code, math, science, creative)?
4. **Reasoning requirements** — Does it need chain-of-thought or step-by-step logic?
5. **Output format** — Is structured output (JSON, code) required?

The algorithm runs in **under 2ms**, so there's no noticeable latency added to your requests. It then assigns the query to one of four tiers:

| Tier | Description | Example |
|------|-------------|---------|
| Simple | Quick Q&A, basic transformations | "Summarize this email" |
| Standard | Regular conversation, moderate tasks | "Write a blog post intro" |
| Complex | Multi-part tasks, detailed instructions | "Build a React component" |
| Reasoning | Math, logic, step-by-step problems | "Solve this system of equations" |

Each tier maps to specific models based on capability and cost. A "simple" query might route to Gemini Flash or Haiku. A "reasoning" query goes to o3, Claude Sonnet, or DeepSeek Reasoner.

---

## Cost Savings: Real Numbers

The 70% savings claim comes from a simple insight: **most OpenClaw queries are simpler than we think**. A well-tuned routing system can send 60-80% of queries to cheaper models without quality loss.

Your actual savings depend on:

- **Your current model mix** — If you're already using cheap models, savings are smaller
- **Query distribution** — More simple queries = bigger savings
- **Provider pricing** — Manifest supports 300+ models across OpenAI, Anthropic, Google, DeepSeek, xAI, Mistral, Qwen, MiniMax, and more

The dashboard shows you exactly what's being spent and where, so you can verify the savings.

---

## Local vs Cloud Mode: Which Should You Choose?

Manifest comes in two flavors:

### Cloud Mode
- Quick install, access dashboard from any device
- Connect multiple agents across machines
- Only **metadata** is sent (model name, tokens, latency) — never message content
- The blind proxy physically cannot read your prompts
- Free to start, scales with usage

### Local Mode
- **100% of your data stays on your machine**
- All telemetry, messages, and costs stored locally
- No subscription — free, forever
- Works perfectly with local models like Ollama
- Dashboard runs at `http://127.0.0.1:2099`

**Which to pick?** If you're unsure, start with cloud mode — it's easier to set up and you can always migrate. If privacy is paramount or you're running Ollama, local mode is the answer.

Both modes install the same OpenClaw plugin. The difference is where telemetry lives.

---

## How Manifest Compares to Alternatives

The most common alternative is **OpenRouter**, a popular API proxy that also offers model routing. Here's how they stack up:

| Feature | Manifest | OpenRouter |
|---------|----------|------------|
| **Architecture** | Runs locally — data stays on your machine | Cloud proxy — all traffic routes through their servers |
| **Cost** | Free (open source) | 5% fee on every API call |
| **Source code** | MIT licensed, fully open | Proprietary |
| **Data privacy** | 100% local routing and logging | Your prompts pass through a third party |
| **Routing transparency** | Open 23-dimension algorithm — see exactly why a model is chosen | Black box routing |
| **Dashboard** | Built-in | Separate |
| **OpenClaw integration** | Native plugin | Requires config |

Manifest's key advantages: **open source**, **self-hostable**, **no markup on API calls**, and **transparent routing**. You can inspect the algorithm, run it locally, and know exactly why a model was selected.

---

## How to Get Started

### Cloud Mode (recommended for most users)

```bash
openclaw plugins install manifest
openclaw config set plugins.entries.manifest.config.apiKey "mnfst_YOUR_KEY"
openclaw gateway restart
```

Sign up at [app.manifest.build](https://app.manifest.build) to get your API key.

### Local Mode

```bash
openclaw plugins install manifest
openclaw config set plugins.entries.manifest.config.mode local
openclaw gateway restart
```

Dashboard opens at `http://127.0.0.1:2099`.

---

## Is Manifest Right for You?

If you're running OpenClaw and paying for API calls, **Manifest is a no-brainer**. It costs nothing, runs locally (if you want), and consistently saves 40-70% on LLM spend — with zero quality loss on most queries.

The only reason not to use it would be if you need deterministic model selection every time (e.g., always using the same model for compliance). For everyone else: install it, watch the dashboard, and let the 23-dimension algorithm do the work.

**Links:**
- GitHub: [github.com/mnfst/manifest](https://github.com/mnfst/manifest)
- Docs: [manifest.build/docs](https://manifest.build/docs)
- Discord: [discord.gg/FepAked3W7](https://discord.gg/FepAked3W7)

---

*Written for OpenClaw users exploring cost optimization. All claims based on Manifest documentation as of March 2026.*

## Sources

- [Manifest GitHub](https://github.com/mnfst/manifest)
- [Manifest Docs](https://manifest.build/docs)
- [Manifest Discord](https://discord.gg/FepAked3W7)
- [Manifest NPM Package](https://www.npmjs.com/package/manifest)
