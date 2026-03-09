# TopClanker Quick Reference

## Files You'll Edit Most

```
data-real-benchmarks.json  ← Add/update model scores here
methodology.html           ← Tweak methodology if needed
index.html                 ← Homepage content
```

## Adding a New Model

1. **Get benchmark scores** from official papers or LMSYS
   - Example sources:
     - https://lmsys.org/ (Arena Elo)
     - Model release papers
     - https://paperswithcode.com/

2. **Add to data-real-benchmarks.json**:
```json
{
  "rank": 13,
  "name": "New Model Name",
  "category": "reasoning",  // or math, research, learning
  "type": "open-source",    // or closed
  "privacy": "high",        // high, medium, low
  "benchmarkScore": 0,      // Calculate this
  "communityScore": null,
  "link": "https://model-site.com",
  "description": "Brief description",
  "benchmarks": {
    "mmlu": 85.0,          // Get from paper
    "gpqa": 70.0,          // Get from paper
    "arenaElo": 1250       // Get from LMSYS
  },
  "sources": [
    "https://link-to-paper.com",
    "https://lmsys.org/"
  ]
}
```

3. **Calculate score**:
```bash
python3 calculate_scores.py
```

4. **Update benchmarkScore** field with calculated value

5. **Re-sort by score** and update ranks

6. **Deploy**: `git add . && git commit -m "Add New Model" && git push`

## Score Calculation (Manual)

For **Reasoning** model:
```
Score = (MMLU × 0.40) + (GPQA × 0.30) + (normalized_Elo × 0.30)

Elo normalization: ((Elo - 1150) / 200) × 100
```

**Bonuses:**
- High privacy: × 1.05
- Open source: × 1.03

## Common Tasks

### Update Existing Model Score
1. Find model in `data-real-benchmarks.json`
2. Update benchmark values
3. Run `python3 calculate_scores.py`
4. Update `benchmarkScore` field
5. Update `lastUpdated` at top of file
6. Deploy

### Change Category Weights
1. Edit weights in `data-real-benchmarks.json` under `categoryWeights`
2. Run `python3 calculate_scores.py` to recalculate all scores
3. Update all `benchmarkScore` fields
4. Update methodology.html to reflect new weights
5. Deploy

### Add New Benchmark
1. Update methodology.html with benchmark description
2. Add to `categoryWeights` in data file
3. Add benchmark scores to models
4. Update `benchmarkDefinitions`
5. Update calculate_scores.py to handle new benchmark
6. Deploy

## Data Sources Quick Links

- **LMSYS Chatbot Arena**: https://lmsys.org/
- **Hugging Face Leaderboard**: https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard
- **Papers with Code**: https://paperswithcode.com/
- **Claude benchmarks**: https://www.anthropic.com/claude
- **GPT-4 benchmarks**: https://openai.com/research/gpt-4
- **Gemini benchmarks**: https://deepmind.google/technologies/gemini/
- **Llama benchmarks**: https://ai.meta.com/llama/

## Quick Deploys

```bash
# Standard update
git add .
git commit -m "Update rankings"
git push

# Update just data
git add data-real-benchmarks.json
git commit -m "Update model scores"
git push

# Methodology change
git add methodology.html data-real-benchmarks.json
git commit -m "Update methodology and recalculate scores"
git push
```

## Score Ranges

- **90-100**: Elite (top 3 models globally)
- **80-89**: Excellent (top tier)
- **70-79**: Very good (competitive)
- **60-69**: Good (capable)
- **<60**: Needs improvement or specialized use case

## Category Breakdown

**Reasoning**: General intelligence, problem-solving
- Best for: Analysis, decision-making, complex queries

**Math**: Numerical computation, logic
- Best for: Calculations, proofs, quantitative analysis

**Research**: Knowledge synthesis, citations
- Best for: Reports, literature reviews, fact-checking

**Learning**: Code generation, adaptation
- Best for: Programming, debugging, iterative tasks

## Privacy Ratings

**High (✓):**
- No training on user data
- Clear retention policies
- GDPR compliant
- Example: Claude, self-hosted Llama

**Medium (○):**
- Training with opt-out
- 30-day retention
- Example: GPT-4, Gemini

**Low (✗):**
- Default training
- Unclear policies
- Rare among major models

## Emergency: Revert Changes

```bash
# See recent commits
git log --oneline

# Revert to previous commit
git revert HEAD

# Or go back to specific commit
git reset --hard COMMIT_HASH
git push --force
```

On Netlify: Deploys tab → Click previous deploy → "Publish deploy"

## Support Contacts

- **Methodology questions**: methodology@topclanker.com
- **Model submissions**: rankings@topclanker.com
- **General**: hello@topclanker.com

## Remember

✓ Always link to sources
✓ Update `lastUpdated` when changing data
✓ Run calculate_scores.py before committing
✓ Test locally before pushing
✓ Keep methodology.html in sync with data

---

**Pro tip**: Bookmark this file. It has everything you need for quick updates.
