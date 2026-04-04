#!/usr/bin/env python3
"""
Generate synthetic firewall rule CSVs from reference templates, topology, and
the asset manifest produced by generate_assets.py.

Scenarios: clean, security_audit, all_facts, cross_zone, scale.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from models import NetworkTopology, load_reference_yaml, make_rng

# Default matches backend/app/core/facts_config.py (FACTS_MAX_TUPLE_ESTIMATE_CAP).
DEFAULT_TUPLE_CAP = 1_000_000_000

CSV_FIELDNAMES = ("source", "destination", "service", "action", "direction")

CLEAN_CATEGORIES = frozenset(
    {"web_tier", "app_data", "infrastructure", "management", "mail"}
)
CROSS_ZONE_CATEGORIES = frozenset({"cross_zone"})
SECURITY_AUDIT_CATEGORIES = frozenset({"security_audit"})
FACTS_MATRIX_CATEGORIES = frozenset({"facts_matrix"})


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def _default_output_dir() -> Path:
    return _script_dir().parent / "generated" / "firewall_rules"


def map_direction(yaml_direction: str) -> str:
    """Map plan/YAML wording to csv_ingestion_service accepted values."""
    d = (yaml_direction or "").strip().lower()
    if d == "egress":
        return "outbound"
    if d == "ingress":
        return "inbound"
    return d


def load_asset_manifest(path: Path) -> Dict[str, List[str]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    raw = data.get("allocated_ips_by_vlan") or {}
    return {str(k): [str(ip) for ip in v] for k, v in raw.items()}


class ManifestResolver:
    """Resolve YAML selectors to endpoint strings using manifest + topology."""

    def __init__(self, topology: NetworkTopology, allocated_ips_by_vlan: Mapping[str, Sequence[str]]):
        self.topology = topology
        self.allocated: Dict[str, List[str]] = {k: list(v) for k, v in allocated_ips_by_vlan.items()}
        self._zone_vlan_keys: Dict[str, List[str]] = {}
        for v in topology.vlans:
            self._zone_vlan_keys.setdefault(v.zone, []).append(v.key)

    def all_manifest_ips(self) -> List[str]:
        out: List[str] = []
        for ips in self.allocated.values():
            out.extend(ips)
        return out

    def ips_on_vlan(self, vlan_key: str) -> List[str]:
        return list(self.allocated.get(vlan_key, []))

    def ips_in_zone(self, zone: str) -> List[str]:
        keys = self._zone_vlan_keys.get(zone, [])
        ips: List[str] = []
        for k in keys:
            ips.extend(self.allocated.get(k, []))
        return ips

    def pick_many(
        self,
        pool: Sequence[str],
        n: int,
        rng,
        *,
        unique: bool = True,
    ) -> List[str]:
        if n <= 0:
            return []
        if not pool:
            return []
        if unique and n <= len(pool):
            return rng.sample(list(pool), n)
        if unique:
            base = list(pool)
            rng.shuffle(base)
            out = base[:]
            while len(out) < n:
                out.append(rng.choice(pool))
            return out[:n]
        return [rng.choice(pool) for _ in range(n)]

    def resolve(
        self,
        selector: Mapping[str, Any],
        rng,
        *,
        source_resolved: Optional[Sequence[str]] = None,
    ) -> List[str]:
        kind = str(selector.get("kind", ""))
        if kind == "zone":
            zone = str(selector["zone"])
            ips = self.ips_in_zone(zone)
            return self.pick_many(ips, 1, rng, unique=True)

        if kind == "vlan_key":
            vk = str(selector["vlan_key"])
            ips = self.ips_on_vlan(vk)
            return self.pick_many(ips, 1, rng, unique=True)

        if kind == "cidr_literal":
            return [str(selector["cidr"])]

        if kind == "vlan_subnet":
            vk = str(selector["vlan_key"])
            return [self.topology.get_vlan(vk).subnet]

        if kind == "same_as_source":
            if source_resolved is None:
                raise ValueError("same_as_source requires source_resolved")
            return list(source_resolved)

        if kind == "multi_zone":
            zones = [str(z) for z in selector["zones"]]
            count = int(selector["count"])
            pool: List[str] = []
            for z in zones:
                pool.extend(self.ips_in_zone(z))
            return self.pick_many(pool, count, rng, unique=True)

        if kind == "multi_vlan":
            keys = [str(k) for k in selector["vlan_keys"]]
            per = int(selector["count_per_key"])
            picked: List[str] = []
            for vk in keys:
                ips = self.ips_on_vlan(vk)
                picked.extend(self.pick_many(ips, per, rng, unique=True))
            return picked

        raise ValueError(f"Unknown selector kind: {kind!r}")


def _services_from_template(tpl: Mapping[str, Any]) -> List[str]:
    if "services" in tpl and tpl["services"] is not None:
        return [str(s) for s in tpl["services"]]
    if "services_template" in tpl and tpl["services_template"] is not None:
        return [str(s) for s in tpl["services_template"]]
    return []


def _format_endpoint_field(parts: Sequence[str]) -> str:
    return ", ".join(parts)


def _format_service_field(services: Sequence[str]) -> str:
    return ", ".join(services)


def row_from_template(
    tpl: Mapping[str, Any],
    resolver: ManifestResolver,
    rng,
    *,
    source_override: Optional[Sequence[str]] = None,
    dest_override: Optional[Sequence[str]] = None,
    services_override: Optional[Sequence[str]] = None,
) -> Dict[str, str]:
    src = list(source_override) if source_override is not None else resolver.resolve(tpl["source_selector"], rng)
    dst = (
        list(dest_override)
        if dest_override is not None
        else resolver.resolve(tpl["dest_selector"], rng, source_resolved=src)
    )
    svcs = list(services_override) if services_override is not None else _services_from_template(tpl)
    if not src or not dst or not svcs:
        raise ValueError(f"Template {tpl.get('id')!r} resolved to empty src/dst/service")
    action = str(tpl.get("action") or "allow")
    direction = map_direction(str(tpl.get("direction") or "outbound"))
    return {
        "source": _format_endpoint_field(src),
        "destination": _format_endpoint_field(dst),
        "service": _format_service_field(svcs),
        "action": action,
        "direction": direction,
    }


def _templates_by_category(data: Mapping[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {}
    for tpl in data.get("templates") or []:
        if not isinstance(tpl, dict):
            continue
        cat = str(tpl.get("category") or "unknown")
        out.setdefault(cat, []).append(tpl)
    return out


def _write_csv(path: Path, rows: Sequence[Mapping[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(CSV_FIELDNAMES), quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in CSV_FIELDNAMES})


def _dedupe_row_key(r: Mapping[str, str]) -> Tuple[str, str, str]:
    return (r["source"], r["destination"], r["service"])


def _expand_rows_unique(
    templates: Sequence[Mapping[str, Any]],
    resolver: ManifestResolver,
    rng,
    target_count: int,
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    seen: Set[Tuple[str, str, str]] = set()
    guard = 0
    while len(rows) < target_count and guard < target_count * 50:
        guard += 1
        tpl = rng.choice(list(templates))
        try:
            row = row_from_template(tpl, resolver, rng)
        except ValueError:
            continue
        k = _dedupe_row_key(row)
        if k in seen:
            continue
        seen.add(k)
        rows.append(row)
    return rows


def _expansion_capped_row(resolver: ManifestResolver, rng, cap: int) -> Dict[str, str]:
    """
    One rule with tuple_estimate = n_src * n_dst * n_services > cap.
    Repeats addresses in the CSV field so ingestion creates one row per token.
    """
    pool = resolver.all_manifest_ips()
    if not pool:
        raise ValueError("Manifest has no IPs; cannot build expansion_capped rule")

    n_src = 4000
    n_dst = 4000
    n_svc = max(2, (cap // (n_src * n_dst)) + 2)

    src_parts = [rng.choice(pool) for _ in range(n_src)]
    dst_parts = [rng.choice(pool) for _ in range(n_dst)]
    services = [f"tcp/{8000 + i}" for i in range(n_svc)]

    return {
        "source": _format_endpoint_field(src_parts),
        "destination": _format_endpoint_field(dst_parts),
        "service": _format_service_field(services),
        "action": "allow",
        "direction": "outbound",
    }


def generate_clean(
    by_cat: Dict[str, List[Dict[str, Any]]],
    resolver: ManifestResolver,
    rng,
    target: int = 30,
) -> List[Dict[str, str]]:
    templates: List[Dict[str, Any]] = []
    for c in CLEAN_CATEGORIES:
        templates.extend(by_cat.get(c, []))
    if not templates:
        raise ValueError("No templates for clean scenario")
    return _expand_rows_unique(templates, resolver, rng, target)


def generate_security_audit(
    by_cat: Dict[str, List[Dict[str, Any]]],
    resolver: ManifestResolver,
    rng,
    target: int = 100,
) -> List[Dict[str, str]]:
    templates = list(by_cat.get("security_audit", []))
    if not templates:
        raise ValueError("No security_audit templates")
    rows = _expand_rows_unique(templates, resolver, rng, target)
    # Ensure risky literals remain; duplicates only affect manifest-backed picks.
    return rows


def generate_all_facts(
    by_cat: Dict[str, List[Dict[str, Any]]],
    resolver: ManifestResolver,
    rng,
    cap: int,
    target_min: int = 50,
) -> List[Dict[str, str]]:
    """Cover facts-oriented templates, tuple stress, expansion_capped, then pad toward target_min."""
    rows: List[Dict[str, str]] = []
    seen: Set[Tuple[str, str, str]] = set()

    def add_row(r: Dict[str, str], *, dedupe: bool = True) -> None:
        k = _dedupe_row_key(r)
        if dedupe and k in seen:
            return
        seen.add(k)
        rows.append(r)

    skip_in_loop = frozenset({"stress_expansion_capped", "stress_high_tuple_grid"})
    for cat in ("security_audit", "facts_matrix"):
        for tpl in by_cat.get(cat, []):
            tid = str(tpl.get("id", ""))
            if tid in skip_in_loop:
                continue
            try:
                add_row(row_from_template(tpl, resolver, rng))
            except ValueError:
                continue

    # Dedicated high-tuple row (10 x 10 x 5) from stress_high_tuple_grid semantics
    high_tpl = next((t for t in by_cat.get("facts_matrix", []) if t.get("id") == "stress_high_tuple_grid"), None)
    if high_tpl:
        src = resolver.resolve(high_tpl["source_selector"], rng)
        dst = resolver.resolve(high_tpl["dest_selector"], rng)
        svcs = _services_from_template(high_tpl)
        if len(src) >= 10 and len(dst) >= 10 and len(svcs) >= 5:
            add_row(
                row_from_template(
                    high_tpl,
                    resolver,
                    rng,
                    source_override=src[:10],
                    dest_override=dst[:10],
                    services_override=svcs[:5],
                ),
            )

    try:
        add_row(_expansion_capped_row(resolver, rng, cap))
    except ValueError:
        pass

    # Pad with legitimate traffic so the file is usable as a medium-sized fixture (~50 rows).
    need = max(0, target_min - len(rows))
    if need:
        clean_tpls: List[Dict[str, Any]] = []
        for c in CLEAN_CATEGORIES:
            clean_tpls.extend(by_cat.get(c, []))
        guard = 0
        while len(rows) < target_min and guard < need * 80 and clean_tpls:
            guard += 1
            tpl = rng.choice(clean_tpls)
            try:
                add_row(row_from_template(tpl, resolver, rng), dedupe=True)
            except ValueError:
                continue

    return rows


def generate_cross_zone(
    by_cat: Dict[str, List[Dict[str, Any]]],
    resolver: ManifestResolver,
    rng,
    target: int = 80,
) -> List[Dict[str, str]]:
    templates = list(by_cat.get("cross_zone", []))
    if not templates:
        raise ValueError("No cross_zone templates")
    return _expand_rows_unique(templates, resolver, rng, target)


def generate_scale(
    by_cat: Dict[str, List[Dict[str, Any]]],
    resolver: ManifestResolver,
    rng,
    target: int = 2000,
) -> List[Dict[str, str]]:
    pool_tpls: List[Dict[str, Any]] = []
    for c in CLEAN_CATEGORIES | CROSS_ZONE_CATEGORIES:
        pool_tpls.extend(by_cat.get(c, []))
    if not pool_tpls:
        raise ValueError("No templates for scale scenario")

    rows: List[Dict[str, str]] = []
    seen: Set[Tuple[str, str, str]] = set()
    attempts = 0
    while len(rows) < target and attempts < target * 30:
        attempts += 1
        tpl = rng.choice(pool_tpls)
        try:
            # Multi-IP fields: re-resolve with wider picks where selectors are zone/vlan.
            src_sel = tpl.get("source_selector") or {}
            dst_sel = tpl.get("dest_selector") or {}
            kind_s = str(src_sel.get("kind", ""))
            kind_d = str(dst_sel.get("kind", ""))

            src = resolver.resolve(src_sel, rng)
            dst = resolver.resolve(dst_sel, rng, source_resolved=src)

            if kind_s in ("zone", "vlan_key"):
                pool = (
                    resolver.ips_in_zone(str(src_sel["zone"]))
                    if kind_s == "zone"
                    else resolver.ips_on_vlan(str(src_sel["vlan_key"]))
                )
                n = rng.randint(2, min(5, max(2, len(pool))))
                src = resolver.pick_many(pool, n, rng, unique=True) or src

            if kind_d in ("zone", "vlan_key"):
                pool = (
                    resolver.ips_in_zone(str(dst_sel["zone"]))
                    if kind_d == "zone"
                    else resolver.ips_on_vlan(str(dst_sel["vlan_key"]))
                )
                n = rng.randint(2, min(5, max(2, len(pool))))
                dst = resolver.pick_many(pool, n, rng, unique=True) or dst

            svcs = _services_from_template(tpl)
            if not svcs:
                continue
            row = {
                "source": _format_endpoint_field(src),
                "destination": _format_endpoint_field(dst),
                "service": _format_service_field(svcs),
                "action": str(tpl.get("action") or "allow"),
                "direction": map_direction(str(tpl.get("direction") or "outbound")),
            }
            k = _dedupe_row_key(row)
            if k in seen:
                continue
            seen.add(k)
            rows.append(row)
        except (ValueError, KeyError):
            continue

    return rows


SCENARIO_OUTPUT = {
    "clean": "rules_clean.csv",
    "security_audit": "rules_security_audit.csv",
    "all_facts": "rules_all_facts.csv",
    "cross_zone": "rules_cross_zone.csv",
    "scale": "rules_scale.csv",
}


def generate(
    scenario: str,
    *,
    seed: int,
    manifest_path: Path,
    output_dir: Path,
    tuple_cap: int = DEFAULT_TUPLE_CAP,
) -> Path:
    if scenario not in SCENARIO_OUTPUT:
        raise ValueError(f"Unknown scenario {scenario!r}; expected one of {sorted(SCENARIO_OUTPUT)}")

    topology = NetworkTopology.from_reference("network_topology")
    manifest = load_asset_manifest(manifest_path)
    resolver = ManifestResolver(topology, manifest)
    rng = make_rng(seed)

    patterns = load_reference_yaml("firewall_patterns")
    by_cat = _templates_by_category(patterns)

    if scenario == "clean":
        rows = generate_clean(by_cat, resolver, rng)
    elif scenario == "security_audit":
        rows = generate_security_audit(by_cat, resolver, rng)
    elif scenario == "all_facts":
        rows = generate_all_facts(by_cat, resolver, rng, tuple_cap)
    elif scenario == "cross_zone":
        rows = generate_cross_zone(by_cat, resolver, rng)
    else:
        rows = generate_scale(by_cat, resolver, rng)

    out_path = output_dir / SCENARIO_OUTPUT[scenario]
    _write_csv(out_path, rows)
    return out_path


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate firewall rule CSV fixtures.")
    p.add_argument(
        "--scenario",
        required=True,
        choices=sorted(SCENARIO_OUTPUT.keys()),
        help="Which rule set to emit",
    )
    p.add_argument("--seed", type=int, default=42, help="RNG seed (default: 42)")
    p.add_argument(
        "--asset-manifest",
        type=Path,
        required=True,
        help="Path to asset_registry_*_manifest.json from generate_assets.py",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory (default: tests/testdata_generation/generated/firewall_rules)",
    )
    p.add_argument(
        "--tuple-cap",
        type=int,
        default=DEFAULT_TUPLE_CAP,
        help=f"Tuple estimate cap for expansion_capped row (default: {DEFAULT_TUPLE_CAP})",
    )
    return p.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    out_dir = args.output if args.output is not None else _default_output_dir()
    try:
        path = generate(
            args.scenario,
            seed=args.seed,
            manifest_path=args.asset_manifest.resolve(),
            output_dir=out_dir.resolve(),
            tuple_cap=args.tuple_cap,
        )
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
