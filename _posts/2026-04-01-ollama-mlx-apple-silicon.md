---
title: "Ollama 0.19 Just Made Apple Silicon Real for Local AI — Here's the Actual Data"
date: 2026-04-01
author: TopClanker Team
description: Ollama 0.19 dropped with MLX support baked in, and the numbers are not what the skeptics expected. On an M5 Pro, the preview hits 1,851 tokens per second on prefill and 134 tokens per second on decode running Qwen3.5-35B-A3B with int4 quantization. That's not a prototype. That's a workstation.
tags: [ollama, apple-silicon, mlx, local-ai, qwen, nvidia]
layout: post
---

Ollama 0.19 dropped March 29, 2026 with MLX support baked in, and the numbers are not what the skeptics expected. On an M5 Pro, the preview hits **1,851 tokens per second** on prefill and **134 tokens per second** on decode running Qwen3.5-35B-A3B with int4 quantization. That's not a prototype. That's a workstation.

If you've been running local AI on an RTX 3090 or 4090 and quietly laughing at Mac users, this post is for you — because the laugh is getting harder to justify.

## What's New: MLX and Unified Memory

Ollama's new preview rebuilds the Apple Silicon stack on top of Apple's MLX framework, which was designed specifically to exploit the unified memory architecture in M-series chips. Unified memory means the GPU, CPU, and Neural Engine all share the same physical RAM — no VRAM bottleneck, no PCIe transfer latency. A 70B parameter model doesn't need a 24 GB VRAM chunk carved out. It just needs 32+ GB of unified memory, full stop.

The speedup is substantial. Ollama's own benchmarks comparing the new MLX path to their previous implementation on the same Qwen3.5-35B-A3B model show roughly an order of magnitude improvement in prefill throughput on M5-series hardware. Decode performance — the tokens-per-second you actually read — lands at 134 t/s on the new Neural Accelerators.

The catch: you need a Mac with **32GB of unified memory minimum**. M5-series Neural Accelerators compound the gains further, but the MLX backend helps all Apple Silicon chips. An M4 Max with 128 GB unified RAM already runs 70B models at 12 tokens per second — fast enough for real-time streaming, not a slideshow.

## The Numbers That Actually Matter

Here's how Apple Silicon stacks up against the reigning NVIDIA champion, the RTX 4090, on local AI workloads:

| Hardware | Model Size | Tokens/sec | Notes |
|---|---|---|---|
| M5 Pro (MLX, int4) | 35B | 134 t/s decode | Ollama 0.19 preview, Qwen3.5-35B-A3B |
| M5 Pro (MLX) | 35B | 1,851 t/s prefill | Same model, first-token speed |
| M4 Max (unified) | 70B | ~12 t/s | DeepSeek-R1, fits in unified RAM |
| RTX 4090 (24 GB) | 8B | ~145 t/s | Best for compact models |
| RTX 4090 (24 GB) | 32B | limited | Can't load 70B without quantization |

The RTX 4090 wins decisively on small models — 145 t/s for an 8B model is genuinely fast. But it stops there. The 24 GB VRAM ceiling means you can't load a 70B model at all without aggressive quantization that kills quality. Apple's unified memory sidesteps this entirely. The M4 Max running 70B DeepSeek-R1 at 12 t/s isn't faster in raw throughput, but it's running a model that's roughly 9× more capable than what the 4090 can load at all.

This is the Apple Silicon argument that actually holds water in 2026: not "Macs are faster," but "Macs can run models that NVIDIA consumer cards physically cannot."

## What Changed: Ollama's Ecosystem Hits Escape Velocity

Ollama's growth alone tells you local AI is no longer a hobby. Monthly downloads went from **100,000 in Q1 2023 to 52 million in Q1 2026** — a 520× increase. Hugging Face now hosts **135,000 GGUF-formatted models** optimized for local inference, up from 200 three years ago. The llama.cpp project, which underpins most of this stack, crossed 73,000 GitHub stars.

NVFP4 support in Ollama 0.19 also deserves attention. NVIDIA's new NVFP4 format reduces memory bandwidth and storage requirements without the quality hit that aggressive quantization traditionally carries. Combined with improved cache handling across conversations, this makes coding agent workflows — think Claude Code, OpenCode, Codex — significantly more responsive.

## Where Apple Still Falls Short

Let's not get carried away. The M5 Pro at 134 t/s decode on a 35B model is impressive, but:

- **RTX 4090 still leads for small models.** At 145 t/s for 8B, NVIDIA's consumer cards remain the better choice if you're running Phi-4, Qwen 3.5 7B, or similar compact models.
- **32 GB minimum is a real gate.** Most Mac users — and most MacBooks — don't have 32 GB of unified memory. This is a desktop story, not a laptop story for heavy workloads.
- **M5-series required for peak gains.** Older M-chips benefit from MLX but won't hit 1,851 t/s prefill. The Neural Accelerators are M5-exclusive.
- **Frontier models still outpace.** GPT-4o and Claude 3.5 Sonnet still outperform every open-weight model on complex reasoning by 5–15% on standard benchmarks. Local AI closes the gap significantly for most tasks, but if you're doing the hardest reasoning work, cloud is still measurably better.
- **Multimodal still favors cloud.** Vision tasks on local models lag significantly behind OpenAI and Google's offerings.

## Practical Guidance: Is This Worth It for You?

**Yes — if you're in one of these situations:**

- You already own an M4 Max or M5-series Mac with 64+ GB unified RAM and you're doing serious coding or agentic work. Running Claude Code or OpenClaw locally with Qwen3.5-35B now gets you genuinely fast response times with zero per-token cost.
- Privacy is non-negotiable. Local inference means your prompts never leave your machine. For sensitive codebases, compliance work, or anything under HIPAA/GDPR, this is architecturally cleaner than any cloud API.
- You're running 50,000+ requests per day. At that volume, cloud API costs hit $2,250/month from OpenAI. Your Mac Studio costs about $139/month amortized over 36 months, plus $15 in electricity.

**Probably not — if:**

- You have an M1/M2 MacBook with 16 GB. The experience will be underwhelming.
- Your workflow demands frontier model quality on hard reasoning tasks. You're still going to pay for Claude or GPT-4o for the 10–15% of requests that truly need it.
- You're running an RTX 4090 today and mainly doing 8B–32B models. NVIDIA still wins at that tier.

## The Take

Ollama 0.19 with MLX doesn't make Apple Silicon the best choice for every local AI workload. The RTX 4090 still dominates on compact models, the 32 GB unified memory floor is a real gate, and M5-series hardware isn't in everyone's hands yet.

But the narrative that "Macs are bad for local AI" needs updating. The unified memory architecture gives Apple a structural advantage that NVIDIA's consumer VRAM model literally cannot match — and now that advantage is fully accessible through Ollama. For developers running 70B-class models on existing M4 Max hardware, or anyone who can wait for M5-series Mac Studio, the question isn't whether local AI works on Mac. It's whether you can afford not to use it.

The preview is live at [ollama.com/download](https://ollama.com/download). You'll need 0.19 and a model pulled with the NVFP4 tag. Try `ollama run qwen3.5:35b-a3b-coding-nvfp4` and see what your Mac actually feels like with 1,851 tokens waiting on the first word.

---
*Sources: [Ollama Blog / MLX](https://ollama.com/blog/mlx) (March 29, 2026), [Ars Technica](https://arstechnica.com/apple/2026/03/running-local-models-on-macs-gets-faster-with-ollamas-mlx-support/), [9to5Mac](https://9to5mac.com/2026/03/31/ollama-adopts-mlx-for-faster-ai-performance-on-apple-silicon-macs/), [DEV Community / Pooya Golchian](https://dev.to/pooyagolchian/local-ai-in-2026-running-production-llms-on-your-own-hardware-with-ollama-54d0)*
