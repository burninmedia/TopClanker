---
title: "OpenAI Deep Research Retires, Apple M5 Pro/Max Redefines Local AI"
date: 2026-03-26
author: TopClanker
description: OpenAI deprecates legacy deep research on March 26, 2026. Meanwhile Apple M5 Pro/Max delivers 6.7x LLM throughput vs M1 Max and Kimi K2.5 dominates open-source leaderboards.
tags: [openai, apple-silicon, local-llm, kimi, llm-benchmarks]
---

# OpenAI Retires Legacy Deep Research Today — And Apple Just Made Local AI Obscenely Fast

*March 26, 2026 is a red-letter day for AI tooling. Here's what matters.*

---

Today marks a small but significant end of an era: **OpenAI is retiring its legacy deep research mode** on Thursday, March 26, 2026. If you've been using the old deep research interface, this is your heads-up — it's being replaced by something cleaner, faster, and presumably more capable. The legacy version disappears today; if you're still relying on it, migrate now or get cut off.

This drops on the same day Apple announced its M5 Pro and M5 Max chips, and the numbers are... aggressive. Let's dig into both.

## OpenAI's Legacy Deep Research: Gone Today

If you've been using OpenAI's deep research feature, you've probably noticed it felt slower and less refined than the newer modes. OpenAI apparently noticed too. According to Releasebot's March 2026 update tracker, the legacy deep research mode gets removed today — Thursday, March 26, 2026.

What this means in practice: if you have workflows built around the old deep research endpoint, audit them before end of day. The replacement is the newer agentic research mode, which OpenAI has been gradually rolling out over the past few months. It's a cleaner experience, better citations, and faster iteration on complex research tasks.

For developers: check the OpenAI API changelog for migration paths. Legacy users are being pushed to the updated endpoints, which reportedly handle multi-step research tasks more reliably.

---

## Apple M5 Pro/Max: The Local AI Chip You Actually Want

Apple doesn't typically dominate AI benchmark conversations, but the M5 Pro and M5 Max announcements deserve attention. The performance claims are substantial:

**LLM Prompt Processing (M5 Max vs. predecessors):**
- **6.7× faster** than M1 Max
- **4× faster** than M4 Max

**AI Image Generation:**
- **8× faster** than M1 Pro/Max
- **3.8× faster** than M4 Max

The M5 Pro delivers up to 4× AI performance versus M4 Pro, and the M5 Max pushes that to 4× versus M4 Max. For developers running local models via LM Studio, Ollama, or anything else on Apple Silicon, these gains are meaningful. A 4× throughput improvement on LLM inference alone changes what's feasible on laptop hardware.

Apple's Neural Accelerators in the GPU cores are doing the heavy lifting here, and the unified memory architecture continues to offer advantages for on-device AI that discrete GPU setups can't match at this efficiency level. The 24-hour battery life claim means you can run meaningful local inference workloads all day without hunting for an outlet.

For the local AI crowd specifically: if you've been holding off on running 70B+ models on your MacBook because throughput felt sluggish, the M5 Max numbers suggest that calculus has changed.

---

## Open Source LLM Rankings: The Big Picture

While this news was dropping, the Onyx Open LLM Leaderboard updated with fresh data. Here's what matters from the current standings:

**Top Open Source Models — Key Benchmarks**

| Model | MMLU-Pro | GPQA | IFEval | LiveCodeBench | Chatbot Arena |
|-------|----------|------|--------|---------------|---------------|
| Kimi K2.5 | 87.1 | 87.6 | 94.0 | **99.0** | 1438 |
| GLM-4.7 | 84.3 | 85.7 | 88.0 | 84.9 | 1441 |
| GLM-5 | 70.4 | 86.0 | 88.0 | 52.0 | 1454 |
| DeepSeek R1 | 84.0 | 71.5 | 83.3 | 65.9 | 1398 |
| DeepSeek V3.2 | 85.0 | 79.9 | N/A | 74.1 | 1423 |
| GPT-oss 120B | 90.0 | 80.9 | N/A | 60.0 | 1355 |
| MiniMax M2.5 | 76.5 | 85.2 | 87.5 | 65.0 | 1404 |
| Qwen 3.5 | 87.8 | 88.4 | 92.6 | 83.6 | 1450 |

A few notes on the data:

**Kimi K2.5** continues to dominate LiveCodeBench with a 99.0 score — essentially perfect on the benchmark. The GPQA reasoning score of 87.6 puts it competitive with the best open-source models available. If you're evaluating models for coding tasks, Kimi K2.5 is hard to argue against at its price point.

**GLM-5** shows an interesting quirk: it leads on Chatbot Arena (1454) but scores notably lower on LiveCodeBench (52.0). This is a reminder that benchmark总分 don't tell the whole story — the use case matters enormously. A model that excels at general chat may not be your pick for code generation.

**GPT-oss 120B** leads on MMLU-Pro at 90.0, suggesting strong general knowledge capabilities. The lower LiveCodeBench score (60.0) is worth noting if code generation is a priority.

The Chinese model dominance on open leaderboards continues — DeepSeek, Kimi, GLM, MiniMax, Qwen, and Xiaomi all appear in these rankings. The Manila Times noted this week that six out of ten top models on open leaderboards are now Chinese in origin. That's a meaningful shift from 18 months ago.

---

## What This Week Tells Us

Three things are happening simultaneously:

1. **Proprietary AI is iterating fast** — OpenAI retiring legacy features after months shows the pace of change at the frontier labs. What was canonical six months ago is being deprecated.

2. **Local AI hardware is catching up** — Apple's M5 numbers suggest the efficiency gap between on-device and cloud inference is narrowing. Running large models locally is increasingly viable for real workloads.

3. **Open-source leadership is consolidating** — The top of the open leaderboard is dominated by a shrinking set of teams (DeepSeek, Kimi, GLM, Qwen), and the benchmark gaps between them and proprietary models are often within noise.

For builders: the tools are getting better on every axis. Local inference, cloud APIs, open weights, proprietary frontier models — the choice is increasingly about your specific constraints rather than which option is definitively better.

---

*Sources: OpenAI Release Notes (releasebot.io, March 2026), Apple Newsroom (March 3, 2026), Onyx Open LLM Leaderboard (updated March 24, 2026), Manila Times (March 25, 2026)*
