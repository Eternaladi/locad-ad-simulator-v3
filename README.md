# Locad Ad Simulator v2

A schema-first ad validation engine for Locad ICPs. It turns raw ICP sheets into coverage-based synthetic panels, then validates ads with traceable evidence: ICP pain points, Locad value props, do/don't rules, proof gaps, localization risk, buying-committee objections, benchmarks, and CI gates.

This repo is deliberately **not** just "ask 10 personas what they think." The goal is to answer: _which specific Locad ICPs does this ad serve, which pain/value pairs does it activate, what proof is missing, and what would block a real buying committee from moving forward?_

## What changed from v1

- `personas/` moved to `data/icp/raw/` because the source of truth is structured ICP data, not hand-written persona roleplay.
- The old `scripts/validate.py` was split into a package under `src/locad_ad_simulator/`.
- The ICP schema mismatch is fixed: the compiler reads `meta + icps` files and writes normalized `icp_atoms.jsonl`.
- Added configurable coverage panels, evidence linter, generic ChatGPT baseline, buying committee simulation, benchmark comparison, report traceability, and CI gates.
- Added deterministic offline scoring so the repo works locally without an API key. LLM prompts/clients are scaffolded for later model-backed evaluation.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/compile_icps.py
python scripts/validate_ad.py \
  --image inputs/ads/sample_locad_ad.png \
  --copy inputs/ads/sample_locad_ad_copy.txt \
  --panel usa_gcc_balanced \
  --mode all
```

The command writes a traceable run under `runs/` and copies the latest human-readable report to `reports/latest.md`.

## Main CLI commands

```bash
# Compile raw ICP files into normalized atoms
python scripts/compile_icps.py

# Validate one creative
python scripts/validate_ad.py \
  --image inputs/ads/sample_locad_ad.png \
  --copy inputs/ads/sample_locad_ad_copy.txt \
  --panel usa_gcc_balanced \
  --gate standard \
  --mode all

# Compare multiple variants
python scripts/validate_batch.py --batch inputs/batches/sample_ab_test.yaml

# Run generic ChatGPT-style baseline only
python scripts/run_baseline.py --copy inputs/ads/sample_locad_ad_copy.txt

# Run buying committee simulation only
python scripts/run_committee_sim.py \
  --copy inputs/ads/sample_locad_ad_copy.txt \
  --panel committee_default

# Rebuild benchmark bands from ad history
python scripts/calibrate_scores.py
```

## Repo structure

```txt
configs/                  Runtime config, gates, panels, report templates
data/icp/raw/             Raw ICP JSON files from the original repo
data/icp/compiled/        Generated ICP atoms, axes, and coverage matrix
data/brand/               Locad positioning, proof points, competitors, restricted claims
data/rules/               Do/don't, claim, localization, and risk rules
src/locad_ad_simulator/   Package logic
evals/                    Evaluator regression tests and version tracking
runs/                     Per-run trace artifacts
reports/                  Curated/latest reports
scripts/                  Thin wrappers around the package CLI
docs/                     Architecture, scoring, schemas, improvement loop
```

## Why this beats a generic ChatGPT prompt

A generic ChatGPT prompt can produce reactions. This repo produces a reproducible decision artifact:

1. **Coverage:** which ICP axes were actually tested.
2. **Evidence:** which ICP rows, pain points, value props, and do/don't rules support the critique.
3. **Committee simulation:** how founder, ops, finance, marketplace, growth, and CX stakeholders would object.
4. **Benchmarking:** how the creative compares with prior Locad ads and human/campaign labels.
5. **Improvement loop:** reviewer and outcome feedback can improve prompts, panel sampling, and gates without drifting blindly.

## Current implementation status

Implemented now:

- ICP compiler for the uploaded `meta + icps` schema
- Coverage-based panel builder
- Deterministic persona reaction evaluator
- Evidence-grounded ad linter
- Trust/proof/localization risk checks
- Buying committee simulation
- Generic ChatGPT baseline comparator
- Benchmark comparison scaffolding
- JSON, Markdown, and PR comment reports
- CI workflows and pytest tests

Scaffolded for later:

- Real LLM-backed reactions using Anthropic/OpenAI clients
- Human/campaign outcome feedback ingestion
- Champion/challenger evaluator promotion
- Richer calibration once real historical outcomes exist

## CI behavior

Use `--ci` to make validation exit with gate codes:

| Verdict | Exit code | Meaning |
|---|---:|---|
| GO | 0 | Safe to proceed |
| WEAK | 1 | Review before launch |
| NO-GO | 2 | Block launch |

Without `--ci`, the local CLI always exits 0 after writing reports.
