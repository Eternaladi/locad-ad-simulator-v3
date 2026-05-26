from __future__ import annotations


def propose_prompt_mutations(feedback_notes: list[str]) -> list[str]:
    return [
        "Add stricter proof requirements for cost/speed claims.",
        "Force every critique to cite an ICP ID and field.",
        "Separate GCC premium-SKU objections from generic GCC growth objections.",
    ] if feedback_notes else []
