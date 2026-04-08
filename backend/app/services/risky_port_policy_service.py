"""
Load global risky port policy and apply it to rule security analysis.
"""
from __future__ import annotations

from typing import Any, Dict, List, TYPE_CHECKING

from sqlalchemy.orm import Session

from app.utils.port_formatter import parse_postgres_port_multirange_to_ranges

if TYPE_CHECKING:
    from app.models.risky_port_policy import RiskyPortPolicyEntry


def list_enabled_entries(db: Session) -> List[RiskyPortPolicyEntry]:
    from app.models.risky_port_policy import RiskyPortPolicyEntry as Entry

    return (
        db.query(Entry)
        .filter(Entry.enabled.is_(True))
        .order_by(Entry.sort_order.asc(), Entry.id.asc())
        .all()
    )


def _protocol_matches(rule_protocol: str, entry_protocol: str) -> bool:
    r = (rule_protocol or "tcp").lower().strip()
    e = (entry_protocol or "tcp").lower().strip()
    if e == "both":
        return True
    return r == e


def _ranges_overlap(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return max(a[0], b[0]) <= min(a[1], b[1])


def collect_matching_policy_entries(
    services: List[Dict[str, Any]],
    entries: List[RiskyPortPolicyEntry],
) -> Dict[int, RiskyPortPolicyEntry]:
    """Return map policy_id -> entry for policies matched by any service on protocol and port overlap."""
    matched: Dict[int, RiskyPortPolicyEntry] = {}
    for svc in services:
        proto = str(svc.get("protocol", "tcp"))
        raw = str(svc.get("port_ranges", ""))
        rule_ranges = parse_postgres_port_multirange_to_ranges(raw)
        for entry in entries:
            if not _protocol_matches(proto, entry.protocol):
                continue
            policy_range = (entry.port_start, entry.port_end)
            for rr in rule_ranges:
                if _ranges_overlap(rr, policy_range):
                    matched[entry.id] = entry
                    break
    return matched


def _default_recommendation(entry: RiskyPortPolicyEntry) -> str:
    pr = entry.protocol.upper()
    if entry.port_start == entry.port_end:
        ports = str(entry.port_start)
    else:
        ports = f"{entry.port_start}-{entry.port_end}"
    return f"Restricted service ({entry.label}): {pr} {ports}"


def apply_risky_port_policy_to_analysis(
    analysis: Dict[str, Any],
    services: List[Dict[str, Any]],
    entries: List[RiskyPortPolicyEntry],
    *,
    rich_issues: bool = False,
) -> None:
    """
    Mutate analysis dict: append recommendations/issues and adjust security_score (delta style).

    Both FAR rule detail and request security analysis use security_score as a value that
    decreases with penalties (FAR path uses a negative accumulator until final normalization).

    Scoring (deterministic):
    - severity info: recommendations only.
    - severity warning: one issue for all warning-tier matches, -5 once per rule.
    - severity high: one issue per matched high-tier policy row, -10 per distinct row, total high penalty capped at -25.
    """
    if not entries or not services:
        return

    matched = collect_matching_policy_entries(services, entries)
    if not matched:
        return

    rec_seen: set[str] = set()
    ordered = sorted(matched.values(), key=lambda e: (e.sort_order, e.id))

    for entry in ordered:
        text = (entry.recommendation or "").strip() or _default_recommendation(entry)
        if text not in rec_seen:
            analysis["recommendations"].append(text)
            rec_seen.add(text)

    high_entries = [e for e in ordered if e.severity == "high"]
    warning_entries = [e for e in ordered if e.severity == "warning"]

    impact_text = "May violate organization port restrictions"

    for entry in high_entries:
        desc = (entry.recommendation or "").strip() or _default_recommendation(entry)
        issue: Dict[str, Any] = {
            "type": "risky_port",
            "severity": "high",
            "description": desc,
        }
        if rich_issues:
            issue["impact"] = impact_text
        analysis["issues"].append(issue)

    if high_entries:
        high_penalty = min(25, 10 * len(high_entries))
        analysis["security_score"] -= high_penalty

    if warning_entries:
        labels = ", ".join(e.label for e in warning_entries)
        desc = f"Rule matches restricted port policies (warning): {labels}"
        issue_w: Dict[str, Any] = {
            "type": "risky_port",
            "severity": "medium",
            "description": desc,
        }
        if rich_issues:
            issue_w["impact"] = impact_text
        analysis["issues"].append(issue_w)
        analysis["security_score"] -= 5
