# Self-improvement loop

The repo should not self-improve using synthetic feedback alone. A safe loop is:

1. Validate ad.
2. Reviewer marks useful/wrong/missing context.
3. Campaign outcome labels are added after launch.
4. Candidate evaluator changes are tested on holdout ads.
5. Champion/challenger report is reviewed.
6. Only then update `EVALUATOR_VERSION`.

This prevents prompt drift and overfitting to the LLM judge.
