# AGENTS.md — Rankings Data

**Who:** Oracle (research), Cypher (updating)

## Guardrails

1. **Data source:** Edit `src/data.json` directly
   - Use real benchmark scores when available
   - Source each change in commit message

2. **Weekly update process:**
   - Check model releases (OpenAI, Anthropic, Google, DeepSeek)
   - Verify benchmark claims before adding
   - Update `lastUpdated` field

3. **Ranking rules:**
   - 1-10 scale based on benchmarks + agentic capability
   - Include both closed + open models
   - Keep descriptions factual, under 200 chars

4. **No breaking builds:**
   - Always run `npm run build` after changes
   - Verify rankings render on homepage

## Process
1. Research → Update `src/data.json`
2. Commit with sources → PR to staging
3. Preview → Verify homepage loads
4. Merge to main
