# Scoring model

Current dimensions:

- relevance
- pain_resonance
- value_prop_alignment
- trust
- clarity
- cta_pull
- localization_fit
- proof_sufficiency

The current implementation uses deterministic heuristics based on token overlap, proof signals, CTA clarity, localization terms, and rule violations. This is intentionally conservative: do not claim CTR or conversion prediction until calibrated against campaign outcomes.
