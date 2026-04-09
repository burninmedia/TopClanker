---
layout: post
title: "I Replaced My Local LLM With Half the Parameters — and Got Better Results"
date: 2026-04-13
tags: [ai, local-llm, benchmarking, optimization]
---

The assumption in local AI is straightforward: bigger is better. More parameters means more capability. A 70B model outperforms a 35B model the same way a V8 outperforms a four-cylinder. End of story.

Except the V8 burns twice as much fuel, requires premium everything, and still leaves you stranded when you forgot to check the oil.

New testing from XDA Developers this week puts that assumption in a different light. A practitioner ran the same workload — coding tasks, document synthesis, reasoning — on a 35B-class model versus a 70B they were previously running. The smaller model won. Not by a little. By enough to make them switch permanently.

The explanation isn't complicated. It turns out that "parameter count" was always a proxy for capability, not capability itself. And we've been optimizing for the proxy.

---

## What's Actually Going On

The testing wasn't a single synthetic benchmark. It was real workload analysis — the kind you can only do when you actually use the thing for a week instead of reading the leaderboard.

A few things that mattered more than parameter count in practice:

**Quantization quality** — a well-quantized 35B running at 4-bit precision can outperform a poorly-optimized 70B running at 8-bit. The quantization method, the calibration data, the tooling — these matter more than the raw model size.

**Context window utilization** — larger models eat context for breakfast. A 70B model at 128K context is burning compute on every token just to maintain the conversation state. A 35B model optimized for the same context window is doing the same job with less overhead.

**Task-specific fine-tuning** — the 35B in this test was a code-specialized variant. The 70B was a generalist. On coding tasks, specialization beats scale. This shouldn't surprise anyone who's been paying attention to the open-weight ecosystem, but it keeps getting lost in the "bigger = better" framing.

---

## The Benchmark Problem

This is where TopClanker has to be honest about a gap in our own coverage. Most of our rankings are benchmark-driven — SWE-bench, HumanEval, MMLU. These are useful for establishing what's possible, but they don't tell you what runs well on the hardware you actually have.

A model that scores 85% on a benchmark but runs at 40 tokens/second on an RTX 4090 is doing less real work than a model that scores 78% and runs at 95 tokens/second. Throughput is a capability metric. We just haven't been treating it like one.

The XDA practitioner's result — switching from a 70B to a 35B and getting "better results" — is probably measuring something closer to effective throughput than raw benchmark score.

---

## What This Means for Model Selection

Three things worth internalizing:

1. **Test on your hardware, not the leaderboard.** The gap between benchmark performance and real-world performance can be large. If you have an RTX 4090 or an M3 Max, run the actual models you're evaluating before committing.

2. **Specialization beats scale for specific domains.** Code, math, instruction-following — domain-specific fine-tunes at smaller sizes are winning against generalists at larger sizes. Qwen3.5-32B for coding, for instance, has been consistently competitive with models twice its size.

3. **Quantization is a capability multiplier, not a compromise.** Done right, 4-bit quantization on a well-calibrated model loses less than you'd expect — sometimes nothing measurable on practical tasks. The "half the parameters, better results" story is partly a quantization story.

The parameter arms race is real, but the local AI community has been quietly winning a different race: the one where "good enough at 35B" beats "great at 70B" because the great model never finishes loading.

---

**Sources:**
- [I Replaced My Local LLM With Half Its Size and Got Better Results — XDA Developers](https://www.xda-developers.com/replaced-local-llm-with-smaller-model-better-results/)
