# TopClanker Ranking Sources & Methodology

## Data Quality Standards

We only source rankings from:
- Peer-reviewed benchmarks (MMLU, GSM8K, HumanEval, GPQA)
- Trusted leaderboards: LMSYS Chatbot Arena, Hugging Face Open LLM Leaderboard
- Company official announcements with benchmark data

## Primary Sources

### Benchmark Tests
| Benchmark | Source | URL |
|-----------|--------|-----|
| MMLU | Hugging Face | https://huggingface.co/leaderboards |
| GSM8K | OpenAI/Stanford | https://github.com/openai/grade-school-math |
| HumanEval | OpenAI | https://github.com/openai/human-eval |
| GPQA | AI21 Labs | https://github.com/AI21Labs/GPQA |
| SWE-Bench | Princeton | https://swe-bench.github.io |

### Leaderboards
| Leaderboard | Source | URL |
|-------------|--------|-----|
| Chatbot Arena | LMSYS | https://chat.lmsys.org |
| Open LLM Leaderboard | Hugging Face | https://huggingface.co/spaces/open-llm-leaderboard |
| Artificial Analysis | Artificial Analysis | https://artificialanalysis.ai |

### Model Documentation (for verification)
- Anthropic: https://www.anthropic.com
- OpenAI: https://openai.com
- Google DeepMind: https://deepmind.google
- Meta AI: https://ai.meta.com
- DeepSeek: https://github.com/deepseek-ai
- Mistral: https://mistral.ai
- Qwen: https://github.com/QwenLM

## Ranking Criteria

### Score Calculation
1. Primary: Benchmark average (MMLU 40%, domain-specific 40%, Chatbot Arena 20%)
2. Adjust for: Context window, pricing, privacy
3. Subjective: "No bullshit" factor (real-world usability)

### Update Schedule
- Check sources weekly
- Full ranking update bi-weekly
- Hotfix for major releases

## Verification Process

Before publishing:
1. [ ] Cross-reference at least 2 sources
2. [ ] Verify with official model documentation
3. [ ] Check date of benchmark data (must be < 3 months old)
4. [ ] Note any caveats or limitations

## Known Limitations

- Some "benchmark" scores are self-reported by companies
- Benchmarks don't capture all use cases
- Real-world performance may vary

## Last Updated
2026-02-19
