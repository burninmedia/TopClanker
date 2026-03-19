---
title: "The Settings That Actually Matter: A Local LLM Tuning Guide"
date: 2026-03-19
author: TopClanker
description: "Default settings suck. Here's how to fix them. Temperature, min-p, and context length — the three knobs that actually move the needle for local LLMs."
tags: [local-llm, tuning, lm-studio, ollama, parameters]
---

Default settings suck. Here's how to fix them.

You downloaded LM Studio. You pulled a model. You typed your first prompt — and got back something bland, repetitive, or just… wrong. So you assume the model is the problem.

It's not. It's the settings.

Most people run local LLMs on defaults — and defaults are designed to be safe, not good. They're tuned to avoid controversy, avoid creativity, avoid making anyone think too hard. That's fine for a general-purpose chatbot. It's terrible for actually getting work done.

Three settings matter. Temperature, min-p, and context length. Master these, and your local LLM transforms.

## Temperature — Creativity vs Accuracy

Temperature controls how random the model's output is. Low temperature (0.0–0.3) means the model picks the most statistically likely next token every time. High temperature (0.7–1.0+) means it throws in surprises.

Here's the practical breakdown:

- **0.0–0.2**: Factual Q&A, code generation, summarization. You want precision.
- **0.3–0.5**: General conversation. The default most people use.
- **0.6–0.8**: Creative writing, brainstorming, roleplay. You want variety.
- **0.9+**: Chaos. Fun for experimentation, useless for work.

The counterintuitive part? **Lower is not always better.** At 0.0, models repeat themselves. They'll loop on the same phrase, gravitate toward generic outputs, and sound like a middle manager writing mission statements.

For code? Stay at 0.0–0.2. For writing? Try 0.4–0.6. The sweet spot for most practical work sits around 0.3–0.4 — enough variety to avoid repetition, enough focus to stay on topic.

In LM Studio, you'll find this under **Chat Settings → Temperature**. In Ollama, it's `temperature: 0.4` in your Modelfile.

## Min-p — The Modern Alternative

Here's something most guides don't tell you: **temperature is outdated.**

Min-p (minimum probability) is a newer sampling method that's rapidly becoming the standard. Instead of controlling randomness directly, it controls *which tokens are even considered*.

Min-p works like this: take the highest-probability token. Say it's 80% likely. With min-p set to 0.05, the model only considers tokens with at least 5% of that probability (4%+). Tokens below that threshold get filtered out completely.

Why this matters:

- **Min-p = 0.05** (default in many UIs): Filters out garbage, keeps decent options
- **Min-p = 0.1**: Aggressive filtering — only the best tokens get through
- **Min-p = 0.0**: Same as disabling it entirely

Combine min-p with temperature for best results. A common setup:

- Temperature: 0.4
- Min-p: 0.1

This gives you focused, high-quality output without the repetitive droning that happens at low temperature alone. It's the combo most power users land on.

Check if your UI supports it — LM Studio does under **Advanced Parameters**. Ollama supports it in the `min_p` field.

## Context Length — Memory Management

Context length is how many tokens the model "remembers" in a single conversation. A 4K context means ~3,000 words. 8K is ~6,000 words. 32K? ~24,000 words — enough for an entire novel.

Here's the catch: **longer context = more RAM = slower generation.**

Every token in context gets processed. If you're generating at 30 tokens/second with 4K context, dropping to 32K context might cut that to 8 tokens/second — depending on your hardware.

The practical framework:

- **4K–8K**: Chat, quick questions, code snippets. Fasts
- **8K–16K**: Document analysis, multi-file codebases, sustained conversation
- **16K–32K**: Large document review, research, long-form writing
- **32K+**: Only if your hardware can handle it (24GB+ unified memory, or dedicated GPU)

For most local setups, **8K is the sweet spot**. It fits most PDFs, handles multi-turn conversation, and doesn't kill your speed.

But here's the setting people miss: **sliding context.** Some UIs support this — when context fills up, it slides the oldest tokens out rather than starting a fresh conversation. LM Studio has this option. It lets you have long-running conversations without the memory explosion.

In LM Studio: **Settings → Context → Sliding Window** (if available). In Ollama: set `num_ctx` in your Modelfile.

## Why These Settings Matter More Than You Think

These aren't minor tweaks. They're fundamental levers that change *what your model is.*

Temperature determines whether your LLM is a library reference or a creative partner. Min-p determines whether it filters noise or chases outliers. Context length determines whether it's a quick chatbot or a research assistant.

The default "safe" settings exist because they work for the widest range of use cases — which means they work great for *no* specific use case. They're the model's training wheels. Taking them off is what makes local LLMs actually useful.

Most people bounce off local AI because they never touch these settings. They get bland output, assume the model sucks, and go back to ChatGPT. That's a shame. The model is the same. The settings are what make the difference.

## Quick Reference

| Setting | Low Value | High Value | Recommended |
|---------|-----------|------------|-------------|
| Temperature | Precise, repetitive | Creative, chaotic | 0.3–0.4 |
| Min-p | More random choices | Only top picks | 0.05–0.1 |
| Context | Fast, less memory | Slow, more memory | 8K default |

## Start Here

Don't overthink it. Pick one thing to change:

1. Set temperature to 0.4 and actually notice the difference
2. Enable min-p at 0.1 and watch output quality improve
3. Bump context to 8K and load a longer document

Default settings exist for a reason. They keep you safe. But safe isn't what you want when you're trying to get something done.

---

**Sources:**

[1] LM Studio (2026). "Configuration Settings." lmstudio.ai/docs.

[2] Ollama (2026). "Modelfile Reference." github.com/ollama/ollama.

[3] Together AI (2024). "Understanding Min-P Sampling." together.ai/blog/min-p-sampling.

[4] Anthropic (2025). "Prompt Engineering Guide." docs.anthropic.com/en/docs/prompt-engineering.
