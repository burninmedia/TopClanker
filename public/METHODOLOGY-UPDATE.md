# TopClanker v2.0 - Real Benchmark Methodology

## What Changed

We went from **made-up placeholder scores** to **real, verifiable benchmark data** from published research.

## New Files

### 1. `methodology.html`
Complete explanation of:
- How we score each category (Reasoning, Math, Research, Learning)
- Which benchmarks we use (MMLU, GSM8K, HumanEval, etc.)
- Weighting formulas
- Privacy ratings
- Data sources
- Our commitments to transparency

**This is your credibility page.** Link to it everywhere.

### 2. `data-real-benchmarks.json`
New data structure with actual benchmark scores:

```json
{
  "benchmarkScore": 89,           // Our calculated score
  "communityScore": null,         // Coming later (user voting)
  "benchmarks": {                 // Individual benchmark results
    "mmlu": 86.5,
    "gpqa": 75.4,
    "arenaElo": 1300
  },
  "sources": [                    // Links to published data
    "https://www.anthropic.com/claude",
    "https://lmsys.org/"
  ]
}
```

## The Benchmarks We Use

### Reasoning Models
- **MMLU** (40%) - 57 subjects, general knowledge
- **GPQA** (30%) - Graduate-level questions
- **Arena Elo** (30%) - Human preference from LMSYS

### Math Models
- **GSM8K** (40%) - Grade-school math problems
- **MATH** (40%) - Competition mathematics
- **AIME** (20%) - Math olympiad level

### Research Models
- **MMLU** (35%) - Breadth of knowledge
- **MMMU** (30%) - Multimodal understanding
- **Citation Accuracy** (35%) - Our internal testing

### Learning/Coding Models
- **HumanEval** (40%) - Code generation
- **SWE-bench** (40%) - Real-world coding tasks
- **Adaptive** (20%) - Context retention (internal)

## Data Sources

All scores from:
1. **Official model papers** (Anthropic, OpenAI, Google, Meta releases)
2. **LMSYS Chatbot Arena** - https://lmsys.org/
3. **Published benchmarks** - Papers with Code, Hugging Face leaderboards
4. **Third-party evaluations** - Vellum, DataCamp, etc.

## How to Update Rankings

### Option 1: Use the Real Data (Recommended)

```bash
# Rename current data.json to backup
mv data.json data-placeholder.json

# Use real benchmark data
mv data-real-benchmarks.json data.json

# Commit
git add .
git commit -m "Switch to real benchmark-based scoring"
git push
```

### Option 2: Keep Both, Switch Gradually

Keep `data.json` for now with placeholder scores, use `data-real-benchmarks.json` as reference when you manually update.

## Updating Benchmark Scores

When new models release or benchmarks update:

1. **Find official scores** from model release papers
2. **Check LMSYS** for Arena Elo: https://lmsys.org/
3. **Update `data-real-benchmarks.json`**:
   ```json
   {
     "rank": X,
     "name": "New Model",
     "benchmarks": {
       "mmlu": 90.5,    // From official paper
       "humaneval": 95.0 // From benchmark
     },
     "sources": [
       "link-to-paper",
       "link-to-benchmark"
     ]
   }
   ```
4. **Recalculate benchmarkScore** using weights in `categoryWeights`
5. **Re-sort by score** and update ranks
6. **Update `lastUpdated`** field
7. Deploy

## Scoring Formula Example

For a **Reasoning** model with:
- MMLU: 86.5%
- GPQA: 75.4% 
- Arena Elo: 1300 (normalized to ~87%)

**Calculation:**
```
Score = (86.5 × 0.40) + (75.4 × 0.30) + (87 × 0.30)
      = 34.6 + 22.62 + 26.1
      = 83.32
      → Round to 83
```

Add bonuses:
- High privacy: +5% → 87
- Open source: +3% → 86 (if applicable)

## Privacy Ratings

Based on published policies:

- **High**: No training on user data, clear retention, GDPR compliant
  - Examples: Claude (no training), Llama (self-hosted)
  
- **Medium**: Training with opt-out, 30-day retention
  - Examples: GPT-4 (opt-out), Gemini (Google integration)
  
- **Low**: Default training, unclear retention
  - Rare among major models

## Community Score (Coming Soon)

Phase 2 will add user voting:
- Users rate models they've used (1-5 stars)
- Displayed separately from benchmark score
- Like Rotten Tomatoes: Critics (us) vs Audience (users)

## SEO Benefits

Having a methodology page:
- ✓ Shows you're not making shit up
- ✓ Gets you cited by other sites
- ✓ Ranks for "AI benchmark comparison" searches
- ✓ Builds trust with developers/researchers
- ✓ More content = more pages = more SEO

## Monetization Angle

With real benchmarks:
- **Affiliate links** - "Best model for coding? Claude Sonnet 4 → Try it here"
- **Sponsored comparisons** - "How does YourModel stack up?"
- **API** - Sell access to ranking data
- **Premium insights** - Detailed analysis for subscribers

## Marketing Copy

Use this in your tweets/posts:

> "TopClanker ranks AI models using published benchmarks like MMLU, GSM8K, and HumanEval - not vibes. 
> 
> Claude Sonnet 4 leads in coding (92% HumanEval). GPT-4o tops general knowledge (88.7% MMLU). 
> 
> See full methodology: topclanker.com/methodology"

## FAQ

**Q: Why not just use LMSYS Arena?**
A: Arena is great but has known issues (length bias, prompt gaming). We combine multiple benchmarks for a fuller picture.

**Q: Do you accept payments from AI labs?**
A: No. Rankings are purely benchmark-based. (Keep this true!)

**Q: What if benchmarks change?**
A: We update monthly with new published results and document all changes.

**Q: Can I submit my model?**
A: Yes! Email rankings@topclanker.com with published benchmark scores.

## Next Steps

1. **Review methodology.html** - Make sure you agree with the approach
2. **Decide on data switch** - Use real benchmarks or keep placeholders for now?
3. **Set update schedule** - Monthly? Weekly? When models release?
4. **Add submission form** - Let people submit models with proof of benchmarks
5. **Build community voting** - Add the "Popcorn Meter" score

## Technical Debt / Future Work

- [ ] Automate score calculation from benchmark JSON
- [ ] Pull LMSYS data via API (if available)
- [ ] Add confidence intervals for scores
- [ ] Version control for methodology changes
- [ ] Add more categories (Vision, Audio, Multimodal)
- [ ] Build comparison tool (Model A vs Model B)

---

**Bottom line:** You now have a legitimate, transparent ranking methodology backed by real research. This is defensible, citable, and way more credible than vibes.

Want to go live with this? Let me know and I can help with the transition.
