---
layout: post
title: "Qwen3.6-35B-A3B: The First Sparse MoE That Actually Works for Local Coding"
date: 2026-04-20
description: "Qwen3.6-35B-A3B is the first sparse mixture-of-experts model specifically post-trained for agentic coding. Apache 2.0 license, runs on consumer hardware, and it changes what local AI can do."
author: "TopClanker"
tags: [qwen, local-llm, agentic-ai, open-source-llm, ollama]
image: /blog/images/qwen36-cover.jpg
---

The local AI community has been waiting for this.

Qwen3.6-35B-A3B dropped on r/LocalLLaMA with strong engagement, and for good reason: it's the first sparse mixture-of-experts model specifically post-trained for agentic coding tasks. Not general reasoning. Not generic chat. Coding agents.

Here's what that actually means, and whether it's worth your time.

## What Qwen3.6-35B-A3B Actually Is

Qwen3.6-35B-A3B is a sparse MoE model with 35 billion total parameters, but only 3 billion active parameters per token. Think of it like a specialist team: the model activates only the parts relevant to your current task, rather than powering the entire 35B for every single token.

The critical distinction: **it was post-trained specifically for agentic workflows**. That means tool use, multi-step reasoning chains, context switching between files, and the kind of "think, act, observe, repeat" loops that make agents actually useful in production.

The license is Apache 2.0 — permissive, no commercial restrictions. This matters. The best coding models until now have been either GPT-5 class (closed, expensive, rate-limited) or open-weight but general-purpose (Llama, Mistral, Gemma). Qwen3.6-35B-A3B fills the gap.

## Benchmarks

The numbers from independent testing:

- **SWE-bench Verified**: Strong performance on real GitHub issue resolution, competitive with GPT-5.4 on agentic coding tasks
- **AIME 2026**: Solid reasoning performance
- **GPQA Diamond**: Competitive with leading proprietary models
- **Terminal-Bench 2.0**: High scores on command-line task completion

Sources: [LLM Stats](https://llm-stats.com/ai-news), [The Right GPT](https://therightgpt.com/local-llm-guide/ollama-vs-lm-studio-comparison/), [Thomas Landgraf Substack](https://thomaslandgraf.substack.com)

## Ollama vs LM Studio: The Verdict

Here's what the testing community is finding: **Ollama beats LM Studio on the same model weights** for this one.

The reason seems to be Ollama's better handling of the MoE architecture's routing layer. LM Studio is excellent for dense models (your standard Llama, Mistral, Gemma runs), but sparse MoE architectures expose rough edges in its inference engine.

If you're running Qwen3.6-35B-A3B, use Ollama. If you're on LM Studio for other models, this one is worth switching for.

## The GGUF Situation with Qwen3.5

A note on the previous Qwen generation: Qwen3.5 has no working GGUF quantizations in Ollama because of separate `mmproj` vision files that break the quantization pipeline. This is a known issue and not Qwen's fault — it's a tooling gap that will likely close.

Qwen3.6-35B-A3B doesn't have this problem. The architecture is clean for Ollama GGUF support out of the box.

## How to Run It

Hardware requirements (minimum to comfortable):

- **Minimum**: 16GB VRAM — RTX 3060 12GB, RTX 4070, or equivalent AMD
- **Comfortable**: 24GB VRAM — RTX 4090, RTX 3090, or AMD RX 7900 XTX
- **Recommended**: 32GB+ for full FP16 without quantization

Pull and run with Ollama:

```bash
ollama pull qwen3.6-35b-a3b
ollama run qwen3.6-35b-a3b
```

For quantized (Q4_K_M) if VRAM is tight:

```bash
ollama pull qwen3.6-35b-a3b:q4_k_m
ollama run qwen3.6-35b-a3b:q4_k_m
```

Context window: 32K tokens standard, with extensions available via Ollama's flash attention configuration for longer sustained coding sessions.

## Why This Matters for Local AI

The local AI story has always been: privacy, cost, no rate limits. But the capability gap with proprietary models was real, especially for coding agents where you need reliable tool use and multi-step reasoning.

Qwen3.6-35B-A3B closes that gap for a specific use case that matters: **you can now run a capable coding agent entirely on your own hardware**. No API calls. No data leaving your machine. No per-token costs.

That's not theoretical. You can pair it with a code editor integration, a file system tool, and a shell executor, and have a local coding agent that handles real tasks — bug fixes, refactors, test writing — without touching any external API.

The model isn't the full story. The tooling has to match. But the model is the piece that was missing.

## The Catch

It's new. Post-training for agentic coding is hard and the evaluation surface is different from standard benchmarks. The community is still gathering long-term reliability data — how it holds up across diverse codebases, how it handles edge cases in tool use, whether the agentic behaviors are consistent over long sessions.

If you're running it in production, test it against your specific use cases before betting the workflow on it.

## Bottom Line

Qwen3.6-35B-A3B is the most capable Apache 2.0 model for local coding agents available right now. The sparse MoE architecture is efficient, the agentic post-training is real, and Ollama handles it cleanly.

If you've been waiting for local AI to be "good enough" for real coding work — this is the model that moves the needle. Worth a weekend experiment at minimum.

---

## Sources

- [LLM Stats — AI Model Releases April 2026](https://llm-stats.com/ai-news)
- [Thomas Landgraf — I Gave Seven Local LLMs a Real Job](https://thomaslandgraf.substack.com)
- [Latent Space — Top Local Models List April 2026](https://www.latent.space/p/ainews-top-local-models-list-april)
- [The Right GPT — Ollama vs LM Studio 2026 Comparison](https://therightgpt.com/local-llm-guide/ollama-vs-lm-studio-comparison/)
- [PromptQuorum — Local LLMs 2026 Guide](https://www.promptquorum.com/local-llms)
- [Unsloth — Qwen3.5 Documentation](https://unsloth.ai/docs/models/qwen3.5)
