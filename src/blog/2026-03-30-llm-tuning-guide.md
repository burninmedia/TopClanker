---
title: "The Settings That Actually Matter: A Local LLM Tuning Guide"
date: 2026-03-30
author: TopClanker Team
tags: [guides, local-llm, tuning]
layout: post
---

Stop touching everything. Most Local LLM settings exist for a reason, but only a handful actually determine whether your output is good or garbage. Here's what actually matters in 2026.

<!--more-->

If you've ever fallen down a rabbit hole of Local LLM settings and emerged two hours later with nothing to show for it — you're not alone. The problem isn't a lack of options. It's knowing which ones move the needle and which ones are just there to make you feel like you're piloting a spaceship.

This guide cuts through that. Four settings. That's it. Get these right and your模型的 outputs will improve noticeably. The rest is noise.

---

## 1. Temperature — But You're Probably Using It Wrong

Temperature scales the logits (raw probability scores) before the model picks its next token. Below 1.0 makes the model favor its most confident guess. Above 1.0 spreads probability more evenly across less likely tokens.

Simple, right? Most people stop there. They don't.

**The order of operations matters.** Temperature gets applied *first*, before top-k, top-p, or min-p filtering. This means high temperature doesn't just add randomness — it reshapes *which tokens survive the filtering step at all*. A confident model at temp 0.8 still behaves pretty locked-in. An uncertain model at temp 0.8 goes everywhere.

**The actual defaults by task:**

| Task | Temperature |
|---|---|
| Factual extraction, classification | 0.0 – 0.2 |
| Code generation | 0.1 – 0.4 |
| Code review | 0.1 – 0.2 |
| Summarization, analysis | 0.3 – 0.5 |
| Conversational chat | 0.5 – 0.7 |
| Creative writing, brainstorming | 0.7 – 1.0 |

**One gotcha that bites people:** Temperature 0 gives you greedy decoding (always pick the most probable token), but some models produce repetition artifacts at exactly 0. If you're going for deterministic output, use 0.1 as your safe default.

**The counterintuitive finding:** Low temperature on multi-step reasoning can actually *hurt* performance. When a model hits a reasoning step where multiple valid paths exist, greedy decoding forces one path and sticks with it — even if it's wrong. Research on math and logic benchmarks shows temperature around 0.5–0.7 improves final accuracy because the reasoning process benefits from a little exploration. If your math model is giving you confident wrong answers, try bumping the temp up before you assume it's a model problem.

---

## 2. Min-P — The 2026 Replacement for Top-P

Here's what most tuning guides still get wrong: they treat top-p as the default sampling method. In 2026, that's outdated.

**What top-p does:** Consider the smallest set of tokens whose combined probability exceeds threshold P. Top-p 0.9 means "keep tokens until they add up to 90% probability." The problem: the candidate pool size can swing wildly — sometimes 5 tokens, sometimes 500 — and it doesn't care whether the model is confident or not.

**What min-p does:** Sets a minimum probability threshold *relative to the top token*. If min-p = 0.1 and the top token has 50% probability, only tokens with ≥5% probability make the cut. When the model is confident (top token at 90%), the pool tightens automatically. When it's uncertain (top token at 20%), it relaxes. It adapts to model confidence rather than imposing a fixed cutoff.

**Why it's gained traction in 2026:**
- Supported in Ollama, llama.cpp, and LM Studio
- Makes temperature more predictable — you can push higher temps without the output going off the rails
- Particularly valuable for creative tasks where top-p breaks down at elevated temperatures

**Practical range:** 0.05 – 0.1

**Typical 2026 pairing:** temperature 0.7, min-p 0.05, top-k 20, top-p 1.0. This is close to Qwen3.5's official guidance for general tasks.

**If your tool supports min-p, replace your top-p habit with it.** You'll get more consistent temperature behavior, especially at higher values.

---

## 3. Context Length — The Silent Output Killer

This one doesn't affect output *quality* the way temperature does. It affects output *completeness* — and it fails silently.

Context length (often called `num_ctx` in Ollama) controls how many tokens the model can see at once: system prompt, conversation history, and current response all count toward that limit.

**The gotcha:** Exceed the limit and the model just... loses access to the start of your conversation. No error. No warning. The model keeps generating as if nothing happened, and you're left with a response that ignores everything you said ten minutes ago.

**Ollama's old default was 2048 tokens.** For quick Q&A that's fine. For document ingestion, multi-turn debugging, or anything requiring real working memory, it's not. A 2048-token context is roughly 1000 words. That's not enough for a long code file or a detailed conversation.

**VRAM cost is real.** KV cache scales linearly with context length. For an 8B model at FP16, every 4K extra tokens costs roughly 0.5–1 GB of VRAM. At 32K context, you might be spending more VRAM on the KV cache than on the model weights themselves.

**The quadratic attention tax:** Attention computation scales with the *square* of sequence length. Doubling context from 8K to 16K more than doubles both VRAM usage *and* time-per-token. A 32K context can feel noticeably sluggish compared to 8K.

**The practical recommendation:** Set context as high as your VRAM allows, then enable KV cache quantization (see below) to stretch it. For a 12GB GPU running an 8B model, 16K is usually the sweet spot.

**How to check if you're hitting the limit:** If your model starts ignoring earlier parts of the conversation or giving answers that don't make sense given the full context, the first thing to check is whether you've exceeded the context window. Bump `num_ctx` up and try again before you blame the model.

---

## KV Cache Quantization — The Setting You're Not Using (But Should)

This one doesn't appear in most tuning guides, and it's the one with the most impact for consumer GPU users.

**What it does:** Compresses the KV cache — the data structure that stores attention keys and values for every token in context. It's separate from model weights, and it grows linearly with context length.

**Why it's the most underrated setting for 2026:**
- Q8_0 (8-bit): halves KV cache VRAM usage, ~0.002–0.05 perplexity increase (basically imperceptible)
- Q4_0 (4-bit): quarter of the original size, ~0.2–0.25 perplexity increase (noticeable on precision tasks like coding)
- Q8 keys + Q4 values: a middle-ground compromise

**If you're running 16K–32K context on a 12GB GPU, this is often the difference between fitting the model entirely in VRAM and hitting swap.**

**How to enable it:**
- Ollama: `OLLAMA_KV_CACHE_TYPE` environment variable
- llama.cpp: `--cache-type-k` and `--cache-type-v` flags (you can quantize K and V separately for fine control)

This is a genuine leverage point for anyone running local models on consumer hardware. It doesn't make the model dumber — it makes the context window *work*.

---

## 4. Repetition Penalty — The Fix for the "Loop of Death"

You know the problem: the model gets going and just... keeps going. Repeating the same phrase. The same idea. The same word, eventually. This is where repetition penalty lives.

**What it does:** Multiplies logits of recently-seen tokens by a penalty factor greater than 1.0, reducing their probability. The model avoids repeating itself.

**The sweet spot:** 1.05 – 1.15

**Where it breaks:** Go above 1.2 and the model starts avoiding common words entirely. "The" becomes a liability. "Is" gets axed. Output starts reading like someone using a thesaurus to avoid repetition — technically not repeating, but worse than if it had.

**How it interacts with other settings:** Repetition penalties (and presence/frequency penalties) are applied *before* top-k, top-p, and min-p filtering. The model deprioritizes repeated tokens first, then redistributes probability. This means you can't fully fix a repetition problem by cranking the penalty — you may also need to adjust temperature or sampling parameters.

**Tip:** If you're seeing repetition but don't want to push the penalty too high, lowering temperature slightly can help. Low temperature + moderate repetition penalty usually handles loops better than either alone at an extreme.

---

## What Not to Touch

Some settings exist, are commonly discussed, but are either redundant or dangerous in common combinations:

**Top-p at low values (0.3–0.5) with high temperature.** This flattens the probability distribution while sampling from a narrow nucleus. You get weird repetitive randomness — the worst of both worlds. If you're using high temperature, leave top-p at 1.0 and let min-p handle filtering.

**Frequency penalty as a default.** It scales penalty proportionally to token count — a word used 10 times gets penalized more than one used twice. This is for long-form generation where certain words naturally recur. For short responses or code, leave it at 0.

**Mirostat as a default.** Mirostat (modes 1 and 2) dynamically adjusts sampling to maintain target perplexity. It's genuinely useful for long-form article generation where consistent quality matters across 1000+ tokens. For short responses, creative tasks, or tool-calling, it adds complexity without benefit. Don't reach for it unless you have a specific long-form problem.

**`--reasoning-budget 0` on reasoning models.** This is a new llama.cpp feature (merged March 2026) that enforces a hard token limit on thinking tokens. Setting it to 0 restricts via the sampler — which can cause erratic behavior on models that try to open a second reasoning block. If you want to disable reasoning, use the model's built-in instruct mode, not a zero budget hack.

**Top-k as your primary filtering method.** Top-k applies a fixed cutoff regardless of model confidence. If the model is 95% sure, top-k 40 still lets in unlikely candidates. If it's uncertain, top-k 40 might cut off perfectly reasonable options. It's fine as a secondary constraint with min-p = 0.0, but don't use it alone.

---

## The Quick Reference

| Setting | What It Does | The Practical Range | Warning |
|---|---|---|---|
| Temperature | Scales probability distribution | 0.1 (factual) – 1.0 (creative) | Don't go to 0 on some models |
| Min-p | Dynamic confidence-aware filtering | 0.05 – 0.1 | Replaces top-p for most use cases |
| Context length | Working memory window | As high as VRAM allows | Check this before blaming the model for "forgetting" |
| KV cache quantization | Compresses attention cache | Q8_0 (quality) – Q4_0 (max space) | Biggest impact per complexity for consumer GPUs |
| Repetition penalty | Reduces token recycling | 1.05 – 1.15 | Don't go above 1.2 or output gets weird |

---

## Sources

- XDA Developers, "8 local LLM settings most people never touch that fixed my worst AI problems," March 9, 2026
- LocalAIops.com, "Advanced LLM Parameter Tuning for Production Workloads," February 2026
- Unprompted Mind, "Temperature and Top-P Explained," March 2026
- Reddit r/LocalLLaMA, Qwen3.5 settings discussion threads, March 2026
- Reddit r/LocalLLaMA, "Llama.cpp now with a true reasoning budget," March 2026
- aiproductivity.ai, "Llama.cpp Adds Reasoning Budget Controls," March 11, 2026
- Shuyo blog, "Adding Reasoning Budget to vLLM," March 26, 2026
- Sebastian Raschka, LLM Architecture Gallery, updated March 27, 2026
- SitePoint, "Ollama vs vLLM Benchmarks," March 2026
- Alibaba Cloud, Qwen3.5 Official Model Documentation and GitHub Repository, March 2026
