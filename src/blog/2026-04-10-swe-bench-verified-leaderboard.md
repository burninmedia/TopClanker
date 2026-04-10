---
layout: post
title: "The SWE-bench Verified Leaderboard Has a New King — And Nobody Can Run It Locally"
date: 2026-04-10
tags: [ai, benchmarks, swe-bench, claude, gpt, local-llm]
---

The SWE-bench Verified leaderboard — the benchmark that most directly measures whether a model can actually fix real software bugs in production codebases — updated today with results that recalibrate what's possible.

Claude Mythos Preview: **93.9%**. GPT-5.3 Codex: **85%**. Claude Opus 4.5: **80.9%**.

For context: six months ago, 70% on SWE-bench Verified was frontier. 93.9% is a different capability tier entirely.

---

## What SWE-bench Verified Actually Measures

SWE-bench is not a trivia benchmark. It's a dataset of real GitHub issues from popular Python repositories — Django, pytest, matplotlib, scikit-learn — paired with ground-truth patches. To score, a model has to generate a fix that actually applies cleanly to the repository.

Verified means human-verified: every patch is checked by a human to confirm it's the correct solution, not just a plausible one that passes the test harness.

This is the benchmark that matters for coding agents. If you're building a tool that writes or modifies code autonomously, SWE-bench Verified is the closest proxy for "will this actually work in my codebase."

---

## The Numbers in Context

| Model | SWE-bench Verified | Notes |
|---|---|---|
| Claude Mythos Preview | **93.9%** | Closed preview only |
| GPT-5.3 Codex | **85%** | API access |
| Claude Opus 4.5 | **80.9%** | API access |
| GPT-5.4 | ~74.9% | API access |
| GLM-5.1 | ~58.4% | Open weights |
| Qwen 3.6 Plus | ~49% | Open weights |

The gap between the top closed models and the best open weights is now roughly 35 percentage points. That's not a small gap — it's a structural difference in deployment model, not just benchmark optimization.

---

## The Deployment Reality

Here's the part the leaderboard doesn't tell you:

**Claude Mythos Preview** at 93.9% is only available through Anthropic's controlled partner program. You cannot access it via API today. You cannot download the weights. You cannot run it locally.

**GPT-5.3 Codex** at 85% is available via OpenAI's API — but at GPT-5 pricing, which is not cheap.

The models that are actually available to run locally — GLM-5.1, Qwen 3.6 Plus, Gemma 4 — are 35+ points behind on this benchmark.

This is the gap between "best for coding agents" and "best for coding agents you can actually deploy."

---

## Why the Gap Matters for Local AI

For the TopClanker audience, the SWE-bench leaderboard tells a uncomfortable story: the models that perform best on real coding tasks are the ones you have the least control over.

A 93.9% SWE-bench score from a closed preview model doesn't help you if:
- The model goes offline when Anthropic changes their partner criteria
- The API pricing makes autonomous coding agents economically impractical
- You need immutable audit trails that can't be altered by the model provider

For production coding agents, the question isn't just "what scores highest" — it's "what scores highest on the infrastructure I can actually run, afford, and audit."

The open-weight models are improving faster than the closed ones. But on SWE-bench Verified specifically, the gap is real and it's not closing in the next quarter.

---

**Sources:**
- [SWE-bench Verified Leaderboard — BenchLM.ai](https://benchlm.ai/benchmarks/sweVerified)
- [LLM Updates April 2026 — LLM Stats](https://llm-stats.com/llm-updates)
