from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from locad_ad_simulator import EVALUATOR_VERSION, __version__
from locad_ad_simulator.ad.asset_loader import load_ad
from locad_ad_simulator.ad.ad_fingerprint import fingerprint_ad
from locad_ad_simulator.ad.claim_extractor import extract_ad_claims
from locad_ad_simulator.config import load_yaml, repo_root_from, write_json
from locad_ad_simulator.core.run_context import create_run_context
from locad_ad_simulator.evaluators.buying_committee import simulate_buying_committee
from locad_ad_simulator.evaluators.chatgpt_baseline import generic_chatgpt_baseline, differential_value
from locad_ad_simulator.evaluators.evidence_linter import lint_ad_evidence
from locad_ad_simulator.evaluators.localization import evaluate_localization
from locad_ad_simulator.evaluators.persona_reaction import evaluate_persona_reactions
from locad_ad_simulator.evaluators.proof_gap import evaluate_proof_gaps
from locad_ad_simulator.evaluators.trust_risk import evaluate_trust_risk
from locad_ad_simulator.ingest.benchmark_loader import load_benchmarks
from locad_ad_simulator.ingest.brand_loader import load_brand_context
from locad_ad_simulator.ingest.icp_compiler import compile_icp_files
from locad_ad_simulator.ingest.icp_loader import load_icp_atoms
from locad_ad_simulator.ingest.rules_loader import load_rules
from locad_ad_simulator.market.market_loader import load_market_context, VALID_MARKETS
from locad_ad_simulator.market.persona_scorer import score_buyer_personas
from locad_ad_simulator.market.market_report import build_market_fit_summary
from locad_ad_simulator.panels.panel_builder import build_panel
from locad_ad_simulator.reporting.json_report import write_json_report
from locad_ad_simulator.reporting.markdown_report import write_markdown_report
from locad_ad_simulator.reporting.pr_comment import write_pr_comment
from locad_ad_simulator.scoring.aggregate import aggregate_persona_results
from locad_ad_simulator.scoring.benchmark_compare import compare_to_benchmarks
from locad_ad_simulator.scoring.calibration import rebuild_benchmark_bands
from locad_ad_simulator.scoring.gates import decide_gate


def compile_icps_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile raw ICP JSON files into normalized atoms.")
    parser.add_argument("--raw-dir", default="data/icp/raw")
    parser.add_argument("--out-dir", default="data/icp/compiled")
    args = parser.parse_args(argv)
    root = repo_root_from()
    result = compile_icp_files(root / args.raw_dir, root / args.out_dir)
    print(f"Compiled {result['total_atoms']} ICP atoms -> {result['atoms_path']}")
    return 0


def validate_ad_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an ad against Locad ICP panels.")
    parser.add_argument("--image", help="Path to ad image", default=None)
    parser.add_argument("--copy", help="Path to ad copy .txt", required=True)
    parser.add_argument("--panel", default="usa_gcc_balanced")
    parser.add_argument("--panel-size", type=int, default=None)
    parser.add_argument("--gate", default="standard")
    parser.add_argument("--mode", choices=["all", "persona", "evidence", "committee", "baseline"], default="all")
    parser.add_argument("--output-root", default="runs")
    parser.add_argument("--reports-root", default="reports")
    parser.add_argument("--ci", action="store_true", help="Exit non-zero for WEAK/NO-GO")
    parser.add_argument(
        "--market",
        choices=VALID_MARKETS,
        default=None,
        help="Market to validate against: usa, gcc_uae, gcc_ksa. Loads market-specific ICPs, gate thresholds, and persona scoring.",
    )
    args = parser.parse_args(argv)
    root = repo_root_from()
    report = run_validation(
        repo_root=root,
        image_path=Path(args.image) if args.image else None,
        copy_path=Path(args.copy),
        panel_name=args.panel,
        gate_name=args.gate,
        mode=args.mode,
        panel_size=args.panel_size,
        output_root=args.output_root,
        reports_root=args.reports_root,
        market=getattr(args, "market", None),
    )
    print_summary(report)
    return int(report["gate_decision"]["exit_code"]) if args.ci else 0


def run_validation(repo_root: Path, image_path: Path | None, copy_path: Path | None, panel_name: str, gate_name: str, mode: str = "all", panel_size: int | None = None, output_root: str = "runs", reports_root: str = "reports", copy_text: str | None = None, ad_id: str | None = None, market: str | None = None) -> dict[str, Any]:
    if copy_path is not None and not copy_path.is_absolute():
        copy_path = repo_root / copy_path
    if image_path is not None and not image_path.is_absolute():
        image_path = repo_root / image_path
    ad = load_ad(copy_path=copy_path, copy_text=copy_text, image_path=image_path, ad_id=ad_id)
    fingerprint = fingerprint_ad(ad.copy_text, ad.image_path)
    ctx = create_run_context(repo_root, ad.ad_id, panel_name, gate_name, EVALUATOR_VERSION, mode)

    # Snapshot inputs
    (ctx.run_dir / "input_snapshot" / "ad_copy.txt").write_text(ad.copy_text, encoding="utf-8")
    if ad.image_path and ad.image_path.exists():
        shutil.copy2(ad.image_path, ctx.run_dir / "input_snapshot" / ad.image_path.name)

    # ── market-aware ICP loading ────────────────────────────────────────────
    market_ctx: dict[str, Any] | None = None
    if market:
        market_ctx = load_market_context(market, repo_root, gate_name)
        atoms = market_ctx["atoms"]
    else:
        atoms = load_icp_atoms(repo_root / "data/icp/compiled", repo_root / "data/icp/raw", auto_compile=True)

    panel_bundle = build_panel(atoms, repo_root / "configs/panels" / f"{panel_name}.yaml", override_size=panel_size)
    panel = panel_bundle["panel"]
    coverage = panel_bundle["coverage"]
    brand = load_brand_context(repo_root / "data/brand")
    rules = load_rules(repo_root / "data/rules")
    benchmarks = load_benchmarks(repo_root / "data/benchmarks")

    ad_claims = extract_ad_claims(ad.copy_text)
    evidence = lint_ad_evidence(ad.copy_text, panel, brand, rules)
    persona_results = evaluate_persona_reactions(ad.copy_text, panel, evidence)
    scorecard = aggregate_persona_results(persona_results)
    localization = evaluate_localization(ad.copy_text, rules, panel)
    trust_risk = evaluate_trust_risk(evidence)
    proof_gaps = evaluate_proof_gaps(evidence, panel)
    committee = simulate_buying_committee(ad.copy_text, panel, evidence, scorecard)
    baseline = generic_chatgpt_baseline(ad.copy_text)
    diff = differential_value(baseline, evidence, coverage, committee)
    benchmark = compare_to_benchmarks(scorecard, benchmarks)
    gate = decide_gate(scorecard, evidence, repo_root / "configs/gates" / f"{gate_name}.yaml")

    # ── buyer persona scoring (parallel layer) ──────────────────────────────
    buyer_persona_scores: dict[str, Any] = {}
    market_fit: dict[str, Any] = {}
    if market and market_ctx is not None:
        buyer_persona_scores = score_buyer_personas(ad.copy_text, repo_root)
        market_fit = build_market_fit_summary(market_ctx, buyer_persona_scores, gate, scorecard, ad.copy_text)

    report: dict[str, Any] = {
        "meta": {
            "run_id": ctx.run_id,
            "repo_version": __version__,
            "evaluator_version": EVALUATOR_VERSION,
            "mode": mode,
            "panel": panel_name,
            "gate": gate_name,
            "market": market,
            "ad_id": ad.ad_id,
            "ad_fingerprint": fingerprint,
            "ad_image": str(ad.image_path) if ad.image_path else None,
            "ad_copy_file": str(ad.copy_path) if ad.copy_path else None,
        },
        "coverage": coverage,
        "ad_claims": ad_claims,
        "icp_alignment": evidence,
        "persona_results": persona_results,
        "localization": localization,
        "trust_risk": trust_risk,
        "proof_gaps": proof_gaps,
        "committee_simulation": committee,
        "chatgpt_baseline": baseline,
        "differential_value": diff,
        "benchmark_comparison": benchmark,
        "final_scorecard": scorecard,
        "gate_decision": gate,
        "buyer_persona_scores": buyer_persona_scores,
        "market_fit": market_fit,
        "next_actions": _next_actions(evidence, gate, committee, market_fit),
    }

    write_json(ctx.run_dir / "parsed" / "panel.json", {"panel": panel, "coverage": coverage})
    write_json(ctx.run_dir / "parsed" / "evidence_linter.json", evidence)
    write_json(ctx.run_dir / "parsed" / "scorecard.json", scorecard)
    if market_fit:
        write_json(ctx.run_dir / "parsed" / "market_fit.json", market_fit)
    write_json_report(report, ctx.run_dir / "final" / "report.json")
    write_markdown_report(report, ctx.run_dir / "final" / "report.md")
    write_pr_comment(report, ctx.run_dir / "final" / "pr_comment.md")

    # ── run history log (Suggestion C) ─────────────────────────────────────
    _append_run_history(repo_root, report)

    reports_dir = repo_root / reports_root
    reports_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ctx.run_dir / "final" / "report.md", reports_dir / "latest.md")
    shutil.copy2(ctx.run_dir / "final" / "report.json", reports_dir / "latest.json")
    return report


def _next_actions(evidence: dict[str, Any], gate: dict[str, Any], committee: dict[str, Any], market_fit: dict[str, Any] | None = None) -> list[str]:
    actions = []
    if gate["verdict"] != "GO":
        actions.append("Revise the creative before media launch; use the missing-proof and rule-violation list as the brief.")
    for gap in evidence.get("missing_proof", [])[:3]:
        actions.append(f"Add proof: {gap}")
    if evidence.get("recommended_rewrite"):
        actions.append(f"Rewrite direction: {evidence['recommended_rewrite']}")
    for asset in committee.get("best_followup_assets", [])[:2]:
        actions.append(f"Prepare follow-up asset: {asset}")
    # Market-aware next actions
    if market_fit:
        for gap in market_fit.get("proof_gap_analysis", {}).get("missing", [])[:2]:
            actions.append(f"Market proof gap: {gap}")
        rewrite = market_fit.get("rewrite_recommendation", "")
        if rewrite:
            first_line = rewrite.split("\n")[0]
            actions.append(f"Rewrite for {market_fit.get('market_context_header', {}).get('market_label', 'market')}: {first_line}")
        if market_fit.get("ramadan_check", {}).get("flag"):
            actions.append("Add Ramadan/Eid peak-season messaging to pass GCC localization gate.")
        mismatches = market_fit.get("marketplace_mismatch", {}).get("mismatches", [])
        if mismatches:
            actions.append(f"Remove irrelevant marketplace references: {', '.join(mismatches)}")
    return actions or ["Ad passes current gates; test against live traffic and capture reviewer/campaign feedback."]


def _append_run_history(repo_root: Path, report: dict[str, Any]) -> None:
    """Append a one-line summary to runs/history.csv after every validation run."""
    import csv
    from datetime import datetime
    history_path = repo_root / "runs" / "history.csv"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not history_path.exists() or history_path.stat().st_size == 0
    meta = report.get("meta", {})
    scorecard = report.get("final_scorecard", {})
    gate = report.get("gate_decision", {})
    market_fit = report.get("market_fit", {})
    top_blocker = market_fit.get("weakest_persona", "") if market_fit else ""
    row = {
        "run_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "market": meta.get("market") or "all",
        "ad_name": meta.get("ad_id", "unknown"),
        "overall_score": scorecard.get("avg_overall", ""),
        "go_rate": f"{round(scorecard.get('go_rate', 0) * 100)}%",
        "verdict": gate.get("verdict", ""),
        "top_blocker_persona": top_blocker,
    }
    with history_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def print_summary(report: dict[str, Any]) -> None:
    gate = report["gate_decision"]
    score = report["final_scorecard"]
    market = report["meta"].get("market")
    market_fit = report.get("market_fit", {})
    print("Locad Ad Simulator")
    print(f"Run:      {report['meta']['run_id']}")
    if market:
        market_label = market_fit.get("market_context_header", {}).get("market_label", market)
        icp_count = market_fit.get("market_context_header", {}).get("icp_count", "?")
        print(f"Market:   {market_label} ({icp_count} ICPs)")
    print(f"Panel:    {report['meta']['panel']} ({report['coverage']['panel_size']} ICPs)")
    print(f"Verdict:  {gate['verdict']} — {gate['reason']}")
    print(f"Overall:  {score['avg_overall']} / 10")
    print(f"GO rate:  {round(score.get('go_rate', 0) * 100)}%")
    if market_fit:
        mgate = market_fit.get("market_gate", {}).get("details", {})
        print(f"Market gate: {mgate.get('verdict', '—')}")
        strongest = market_fit.get("strongest_persona", "")
        weakest = market_fit.get("weakest_persona", "")
        if strongest:
            print(f"Best persona match: {strongest}  |  Critical blocker: {weakest}")
    print(f"Report:   runs/{report['meta']['run_id']}/final/report.md")


def validate_batch_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a batch/A-B test YAML.")
    parser.add_argument("--batch", required=True)
    parser.add_argument("--ci", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root_from()
    data = load_yaml(root / args.batch if not Path(args.batch).is_absolute() else Path(args.batch))
    reports = []
    for variant in data.get("variants", []):
        report = run_validation(
            repo_root=root,
            image_path=Path(variant["image"]) if variant.get("image") else None,
            copy_path=Path(variant["copy"]) if variant.get("copy") else None,
            copy_text=variant.get("copy_text"),
            ad_id=variant.get("id"),
            panel_name=data.get("panel", "usa_gcc_balanced"),
            gate_name=data.get("gate", "standard"),
            mode="all",
        )
        reports.append(report)
    best = max(reports, key=lambda r: r.get("final_scorecard", {}).get("avg_overall", 0)) if reports else None
    if best:
        print(f"Best variant: {best['meta']['ad_id']} ({best['final_scorecard']['avg_overall']}/10)")
    worst_exit = max(r["gate_decision"]["exit_code"] for r in reports) if reports else 2
    return worst_exit if args.ci else 0


def run_baseline_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run generic ChatGPT-style baseline only.")
    parser.add_argument("--copy", required=True)
    args = parser.parse_args(argv)
    root = repo_root_from()
    copy_path = Path(args.copy)
    if not copy_path.is_absolute():
        copy_path = root / copy_path
    result = generic_chatgpt_baseline(copy_path.read_text(encoding="utf-8"))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def run_committee_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run buying committee simulation only.")
    parser.add_argument("--copy", required=True)
    parser.add_argument("--panel", default="committee_default")
    args = parser.parse_args(argv)
    root = repo_root_from()
    copy_path = root / args.copy if not Path(args.copy).is_absolute() else Path(args.copy)
    atoms = load_icp_atoms(root / "data/icp/compiled", root / "data/icp/raw", auto_compile=True)
    panel_bundle = build_panel(atoms, root / "configs/panels" / f"{args.panel}.yaml")
    brand = load_brand_context(root / "data/brand")
    rules = load_rules(root / "data/rules")
    copy_text = copy_path.read_text(encoding="utf-8")
    lint = lint_ad_evidence(copy_text, panel_bundle["panel"], brand, rules)
    result = simulate_buying_committee(copy_text, panel_bundle["panel"], lint)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def calibrate_scores_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rebuild benchmark bands from ad history.")
    parser.add_argument("--history", default="data/benchmarks/ad_history.csv")
    parser.add_argument("--output", default="data/benchmarks/benchmark_bands.yaml")
    args = parser.parse_args(argv)
    root = repo_root_from()
    result = rebuild_benchmark_bands(root / args.history, root / args.output)
    print(json.dumps(result, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Locad Ad Simulator")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("compile-icps")
    sub.add_parser("validate-ad")
    sub.add_parser("validate-batch")
    sub.add_parser("run-baseline")
    sub.add_parser("run-committee")
    sub.add_parser("calibrate-scores")
    ns, rest = parser.parse_known_args(argv)
    if ns.command == "compile-icps":
        return compile_icps_cli(rest)
    if ns.command == "validate-ad":
        return validate_ad_cli(rest)
    if ns.command == "validate-batch":
        return validate_batch_cli(rest)
    if ns.command == "run-baseline":
        return run_baseline_cli(rest)
    if ns.command == "run-committee":
        return run_committee_cli(rest)
    if ns.command == "calibrate-scores":
        return calibrate_scores_cli(rest)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
