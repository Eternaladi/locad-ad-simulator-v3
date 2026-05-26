from __future__ import annotations

from typing import Any


def committee_interaction_graph(internal_objections: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = [{"id": o["role"], "stance": o.get("stance")} for o in internal_objections]
    edges = []
    role_order = [o["role"] for o in internal_objections]
    for a, b in zip(role_order, role_order[1:]):
        edges.append({"from": a, "to": b, "interaction": "forwards concern"})
    return {"nodes": nodes, "edges": edges}
