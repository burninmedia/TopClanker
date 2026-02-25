# TopClanker Ranking Sources

This document tracks sites and sources we use for LLM rankings. We don't cite these in blog posts — we use them to build our own data store with real-world numbers.

## Cloud LLM Rankings

| Site | URL | What's Useful |
|------|-----|---------------|
| LLM Stats | https://llm-stats.com/ | Comprehensive leaderboards, pricing, context windows |
| Artificial Analysis | https://artificialanalysis.ai/leaderboards/models | 100+ models, intelligence/price/speed metrics |
| Onyx AI | https://www.onyx.app/llm-leaderboard | Coding, reasoning, math, agentic benchmarks |
| Open Source LLM Leaderboard (Onyx) | https://www.onyx.app/open-llm-leaderboard | Open source models, SWE-bench, LiveCodeBench |
| VERTU | https://vertu.com/lifestyle/open-source-llm-leaderboard-2026-rankings-benchmarks-the-best-models-right-now/ | MMLU, MMLU-Pro, HumanEval, SWE-bench, GPQA, MATH |
| Klu AI | https://klu.ai/llm-leaderboard | Model comparisons, pricing |
| LiveBench | https://livebench.ai/ | Live, continuously updated benchmarks |
| SEAL (Scale AI) | https://scale.com/leaderboard | Expert-driven evaluations |

## Local/GPU LLM Rankings

| Site | URL | What's Useful |
|------|-----|---------------|
| Hardware Corner | https://www.hardware-corner.net/gpu-ranking-local-llm/ | GPU rankings for LLM inference, token/sec by model/GPU |
| Local AI Master | https://localaimaster.com/blog/best-gpus-for-ai-2025 | GPU benchmarks, cost-to-speed ratio |
| LocalLLM.in | https://localllm.in/blog/best-gpus-llm-inference-2025 | GPU benchmarks, Q4_K_M performance |
| Best GPUs for AI | https://www.bestgpusforai.com/ | 3090 vs 4090 comparisons, inference stacks |
| Puget Systems | https://www.pugetsystems.com/labs/articles/llm-inference-consumer-gpu-performance/ | Consumer GPU inference benchmarks |
| LLM Token Generation Simulator | https://kamilstanuch.github.io/LLM-token-generation-simulator/ | Interactive speed simulator |

## Community Benchmarks (Reddit)

| Source | URL | What's Useful |
|--------|-----|---------------|
| r/LocalLLaMA Benchmarks | https://www.reddit.com/r/LocalLLaMA/ | Real-world user benchmarks, RTX 3090/4090/5090 tests |
| vLLM Benchmarks | GitHub: XiongjieDai/GPU-Benchmarks-on-LLM-Inference | Quantitative GPU benchmarks |

## Key Benchmarks We Track

- **MMLU / MMLU-Pro**: General knowledge
- **HumanEval**: Code generation
- **SWE-bench Verified**: Real-world software engineering
- **LiveCodeBench**: Coding competition
- **GPQA**: Graduate-level QA
- **MATH-500**: Math reasoning
- **IFEval**: Instruction following
- **Chatbot Arena**: Human preference

## Update Cadence

- Cloud models: Weekly checks
- GPU benchmarks: Monthly
- Reddit community: Ongoing monitoring

## Notes

- Prioritize real-world tests over model developer papers
- Cross-reference benchmark claims with multiple sources
- Note the date — fast-moving space, prefer recent data
- Track inference engine (vLLM, llama.cpp, TensorRT-LLM) — speeds vary significantly
