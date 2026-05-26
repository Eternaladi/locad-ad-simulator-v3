from __future__ import annotations

from typing import Any


def render_persona(atom: dict[str, Any]) -> str:
    pains = "\n".join(f"- {p}" for p in atom.get("top_pain_points", []))
    values = "\n".join(f"- {v}" for v in atom.get("locad_value_propositions", []))
    objections = "\n".join(f"- {o}" for o in atom.get("likely_objections", []))
    return f"""ICP {atom.get('icp_id')} — {atom.get('persona')}
Region: {atom.get('region')}
Decision maker: {atom.get('decision_maker_title')} in {atom.get('hq_location')}
Category: {atom.get('product_category')}
Channels: {', '.join(atom.get('sales_channels', []))}
Primary marketplace: {atom.get('primary_marketplace')}
Revenue stage: {atom.get('revenue_stage')}

Pain points:
{pains}

Relevant Locad value props:
{values}

Likely objections:
{objections}
""".strip()
