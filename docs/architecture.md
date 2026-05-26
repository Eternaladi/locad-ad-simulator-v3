# Architecture

The repo is built around five layers:

1. **ICP source of truth** — raw `meta + icps` files are compiled into normalized ICP atoms.
2. **Coverage panels** — panel configs select ICP atoms by measured axis coverage, not random persona lists.
3. **Evaluators** — persona reactions, evidence linter, trust/proof/localization checks, buying committee, and baseline comparator.
4. **Scoring and gates** — aggregate dimensions, benchmark comparison, and CI-friendly GO/WEAK/NO-GO decisions.
5. **Improvement loop** — reviewer/campaign feedback and holdout evals support future champion/challenger evaluator upgrades.

Every final recommendation should trace to at least one of: ICP ID, pain point, Locad value prop, do/don't rule, proof point, benchmark, or committee objection.
