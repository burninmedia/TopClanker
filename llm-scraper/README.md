# llm-scraper

Weekly pipeline that scrapes public LLM benchmark leaderboards, normalizes the
results into a canonical dataset, diffs against the previous snapshot, and
opens a PR with the update.

## Pipeline stages

```
run.py
  ├── archive data/master.json → data/archive/master_YYYY-MM-DD.json
  ├── scrapers/hf_leaderboard.run_scraper()  → data/raw/hf_leaderboard.json
  ├── scrapers/lmsys_arena.run_scraper()     → data/raw/lmsys_arena.json
  ├── normalize.normalize()                  → updates data/master.json
  │                                             + appends data/needs_review.json
  ├── diff.compute_diff()                    → data/weekly_diff.json
  └── writes .pipeline_exit_code / .pipeline_summary / .needs_review_new
     at the repo root for the GitHub Actions workflow to consume
```

Exit codes:

| Code | Meaning                                                       |
|------|---------------------------------------------------------------|
| `0`  | Success. All scraped model names resolved to canonical IDs.   |
| `2`  | Success, but new unknown model names landed in `needs_review.json`. |
| `1`  | Hard failure. Workflow aborts.                                |

## Benchmark types (apples-to-apples)

Every benchmark in `data/benchmarks.json` carries a `benchmark_type` field so
the site can group scores by capability category. HF Open LLM Leaderboard v1
was retired upstream; the pipeline now targets v2:

| Benchmark    | benchmark_type          |
|--------------|-------------------------|
| `ifeval`     | `instruction_following` |
| `bbh`        | `reasoning`             |
| `math_lvl5`  | `math`                  |
| `gpqa`       | `knowledge`             |
| `musr`       | `reasoning`             |
| `mmlu_pro`   | `knowledge`             |
| `lmsys_elo`  | `human_preference`      |

`normalize.py` copies this `benchmark_type` onto every score entry in
`data/master.json`, and `diff.py` includes it on every per-benchmark change in
`data/weekly_diff.json`, so consumers never need to do a join to compare
"apples to apples" (e.g. sort only `knowledge` benchmarks, or only
`human_preference` scores).

Example score entry in `master.json`:

```json
"mmlu_pro": {
  "score": 66.3,
  "source": "hf_leaderboard",
  "benchmark_type": "knowledge",
  "recorded_at": "2025-01-12T00:00:00Z"
}
```

## First-time setup (one-time manual steps)

These are things the repo owner must do once in the GitHub UI. They are
**not** automated by any workflow.

### 1. Enable auto-merge

**Settings → General → Pull Requests → enable "Allow auto-merge"**

This is what lets the weekly workflow squash-merge clean runs without a
human in the loop.

### 2. Protect `main`

**Settings → Branches → Add protection rule for `main`:**

- Require a pull request before merging: **ON**
- Require approvals: **OFF** (this is a solo project; flip this on if you
  add collaborators)
- Require status checks to pass: **ON**
  - After the workflow has run once, add **`scrape`** as a required check.

### 3. Netlify rebuild trigger

There are two possibilities. Pick the one that matches your layout.

**A. TopClanker site lives in a SEPARATE repo from this scraper:**

1. Netlify → Site settings → Build hooks → **create a hook** → copy the URL.
2. In this repo: Settings → Secrets and variables → Actions → add a secret
   named `NETLIFY_BUILD_HOOK` with that URL as the value.
3. Append this step to `.github/workflows/scrape.yml` after the auto-merge
   step:

   ```yaml
   - name: Trigger Netlify rebuild
     if: steps.exitcode.outputs.code == '0'
     run: curl -X POST "${{ secrets.NETLIFY_BUILD_HOOK }}"
   ```

**B. TopClanker site is in the SAME repo as this scraper:**

Nothing to do — Netlify already rebuilds on every push to `main`, and the
weekly workflow pushes to `main` via the auto-merged PR.

### 4. Repository layout

The workflow file lives at the repo root (`.github/workflows/scrape.yml`) —
that is the only location GitHub Actions actually discovers workflows from.
The scraper code and data all live under `llm-scraper/`, and the workflow
uses `defaults.run.working-directory: llm-scraper` so every shell step
executes inside that subdirectory. This means the relative paths you see in
the YAML (`data/...`, `.pipeline_*`, `python run.py`) all resolve against
`llm-scraper/` at runtime.

## Local development

```bash
cd llm-scraper
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the whole pipeline
python run.py

# Or run a single scraper and inspect its output
python -m scrapers.hf_leaderboard
cat data/raw/hf_leaderboard.json | head
```

`data/raw/` and `data/archive/` are gitignored; they're regenerated on every
run. The three tracked data artifacts are:

- `data/master.json` — the full, cumulative canonical dataset (never shrinks).
- `data/weekly_diff.json` — site-facing summary of what changed this week.
- `data/needs_review.json` — human review queue of unknown model names.

## Testing

The pipeline ships with a pytest suite covering normalize, diff, the
orchestrator, scraper helpers, and registry-data integrity. None of the
tests touch the network — `run.py` is exercised against monkeypatched
in-memory scrapers, and every test gets its own isolated temp data tree
via the `scenario` fixture in `tests/conftest.py`.

```bash
cd llm-scraper
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests/ -v
```

What's covered:

| Suite                | What it pins down                                                  |
|----------------------|---------------------------------------------------------------------|
| `test_data.py`       | benchmarks.json and models.json schemas; alias uniqueness across models |
| `test_scrapers.py`   | Pure helpers: score coercion, column-name → benchmark mapping, CSV column picking |
| `test_normalize.py`  | Alias resolution, `benchmark_type` propagation, authoritative-source rule, `needs_review` dedup |
| `test_diff.py`       | Added/updated/removed detection, latest-archive selection, deltas, `benchmark_type` carry-through |
| `test_run.py`        | Exit codes (0/2), archive skip-on-empty, archive re-run protection, temp file format, scraper soft-failure handling |

Roughly 45 tests; the whole suite runs in well under a second.

## Manually adding a model alias

When the weekly PR is labeled `needs-review`, it means the scraper found a
raw model name that didn't match any alias in `data/models.json`. To resolve
one:

1. Open `data/needs_review.json` and pick a `raw_name`.
2. In `data/models.json`, find the canonical model entry it belongs to (or
   add a new one if the model isn't in the registry yet).
3. Add the raw name — and any sensible variants (dated pins, HuggingFace-style
   `org/model` paths, short names) — to that entry's `aliases` array.
4. Remove the entry from `data/needs_review.json` manually.
5. Commit both files and push. On the next run, the name will resolve to the
   correct `canonical_id` and its scores will appear in `master.json`.

Example: if `Qwen2.5-72B-Instruct` appears in `needs_review.json`, add a new
entry to `models.json`:

```json
"qwen/qwen2.5-72b": {
  "canonical_id": "qwen2.5-72b",
  "display_name": "Qwen2.5 72B",
  "provider": "Alibaba",
  "aliases": [
    "qwen2.5-72b",
    "Qwen2.5 72B",
    "Qwen/Qwen2.5-72B",
    "Qwen/Qwen2.5-72B-Instruct",
    "Qwen2.5-72B-Instruct"
  ]
}
```

## What to do when a `needs-review` PR is opened

The weekly workflow opens a PR with one of two label configurations:

- `automated, data-update` — clean run. If you've enabled auto-merge, it will
  merge itself once the `scrape` check passes. You don't have to do anything.
- `automated, data-update, needs-review` — there are new unknown model names.
  The PR body lists them under **"New model names flagged for review"**.
  **Do not merge this PR yet.** Instead:

  1. Check out the PR branch locally.
  2. For each flagged name, follow the "Manually adding a model alias" steps
     above (edit `data/models.json` to absorb the alias, then remove the entry
     from `data/needs_review.json`).
  3. Commit to the same PR branch and push. (Optional) re-run `python run.py`
     locally to verify the names now resolve and the score lands in
     `master.json`.
  4. Merge the PR manually.

If an unknown name is actually junk (e.g. a duplicate listing, a test model,
a renamed repo you don't care about), you can just delete it from
`needs_review.json` without adding it to `models.json`. It will re-appear on
the next run if the source still reports it, so the durable fix is usually
to add an alias.
