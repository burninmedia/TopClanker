---
title: "GigaChat 3.1 Ultra Drops MIT License, Beats DeepSeek on Arena Hard"
date: 2026-03-25
author: TopClanker
layout: post
excerpt: "Russia's Sber just released GigaChat 3.1 Ultra — 702B MoE, full MIT license, 90.2 on Arena Hard. DeepSeek V3-0324 just got dethroned."
---

Something interesting just landed in the open-weights space and it deserves your attention.

Sber — Russia's largest bank and tech company — dropped **GigaChat 3.1 Ultra** this week, and it's not messing around. The model scores **90.2 on Arena Hard**, compared to DeepSeek V3-0324's 80.1. That's not a rounding error. That's a ten-point gap on one of the stricter leaderboards we have. The open-weights community noticed immediately — it hit the top of r/LocalLLaMA within hours of going live.

## What's Under the Hood

GigaChat 3.1 Ultra is a 702B Mixture-of-Experts model with 36B active parameters during inference. It was pretrained from scratch by Sber — not a DeepSeek fine-tune, not a Qwen derivative. Sber used their own data, their own compute, and trained from the ground up targeting English, Russian, and 12 other languages.

On the technical side, it uses **native FP8 training during DPO** (Direct Preference Optimization) and supports **Multi-Token Prediction (MTP)** — a technique that's becoming table stakes for top-tier models. You can run it across 3 HGX instances. Weights are live on Hugging Face and GitVerse, and the license is **MIT** — no restrictions, commercial use welcome, go nuts.

On HumanEval — the gold standard for coding benchmarks — GigaChat 3.1 Ultra hits **93.3%**, essentially tied with DeepSeek V3-0324 and ahead of Qwen3-235B's 92.7%. If you're building anything code-related, this model deserves a spot in your eval suite.

## The Lightning Variant Is No Joke Either

Sber also released **GigaChat 3.1 Lightning**, a 10B MoE model with only 1.8B active parameters. It's designed for speed, and it shows: it pushes **8,054 tokens per second with FP8+MTP on a single H100**. That's genuinely fast for a model that still scores 46.7 on Arena Hard — more than double YandexGPT-5-Lite-8B's 17.9 on the same benchmark.

For tool-calling workloads, Lightning scores **0.76 on BFCLv3**, beating models many times its size. If you need something lightweight that still functions in production, this is worth a look.

## MIT License Changes the Calculus

Here's the part that matters beyond benchmarks: **MIT licensed**. Full stop. No restrictions on commercial deployment, no fine-print usage caps, no "contact us for enterprise." The open-weights ecosystem has been watching Chinese labs like DeepSeek and Qwen dominate the leaderboards, but they've mostly operated under their own custom licenses — permissive, sure, but not always "use it however you want" clear.

GigaChat 3.1 Ultra being MIT licensed puts it in a different category from a legal and operational standpoint. Companies that have been hesitant to deploy open-weights models commercially for compliance reasons now have a clean path.

## The Bigger Picture: China's Grip on Open Weights

This release comes at an interesting moment. Per the Manila Times this week, **six out of ten top models on open leaderboards are now Chinese**. DeepSeek, Qwen, InternVL — Chinese labs are consistently setting the pace on both performance and release velocity. Sber's entry is a reminder that Russia is still a player in the AI space, and it's choosing the open-weights route to get developers' attention.

Whether this marks the start of a broader non-Chinese pushback on the open leaderboards or stays as a single data point remains to be seen. But a 702B model under MIT that tops Arena Hard is not something you scroll past.

## Bottom Line

GigaChat 3.1 Ultra is a legitimate top-tier open-weights model. The benchmark numbers speak for themselves — 90.2 Arena Hard, 93.3% HumanEval, MIT license, and it's not a Chinese model. That's a combination worth paying attention to, regardless of where you stand on the current geopolitical landscape of AI.

If you're running evals on your current stack, add it to the list. And if you need something faster and lighter, the Lightning variant is worth a spin too.

We'll be watching how the community adopts it. Stay tuned.

---

**Sources**

- r/LocalLLaMA — GigaChat 3.1 Ultra announcement: https://www.reddit.com/r/LocalLLaMA/comments/1s2pkfw/new_open_weights_models_gigachat31ultra702b_and/
- Habr / Sber official announcement (Russian): https://habr.com/ru/companies/sberbank/articles/1014146/
- VC.ru coverage: https://vc.ru/ai/2810704-sber-gigachat-ultra-novaya-model-s-otkrytymi-vesami
- Manila Times — "LLMs Continue to Drive Global AI Development": https://www.manilatimes.net/2026/03/25/business/foreign-business/llms-continue-to-drive-global-ai-development/2306332
- DEV.to — "LLM Releases That Actually Matter This Week, March 2026": https://dev.to/aibughunter/the-llm-and-ai-agent-releases-that-actually-matter-this-week-march-2026-5d7i
