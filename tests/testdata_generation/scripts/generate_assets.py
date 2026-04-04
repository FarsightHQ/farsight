#!/usr/bin/env python3
"""
Generate synthetic asset registry CSVs plus a VLAN→IP manifest for firewall rule generation.

Reads reference/network_topology.yaml and reference/asset_profiles.yaml.
"""

from __future__ import annotations

import argparse
import csv
import ipaddress
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from models import (
    AssetRecord,
    NetworkTopology,
    hostname_generator,
    load_reference_yaml,
    make_rng,
    pick_weighted,
)

SIZE_COUNTS = {"small": 50, "medium": 500, "large": 5000}

ENV_SLUGS = {
    "Production": "prod",
    "Staging": "stg",
    "UAT": "uat",
    "Development": "dev",
    "DR": "dr",
}

SITE_SLUGS = {
    "dc_east": "east",
    "dc_west": "west",
    "branch_eu": "eu",
}


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def _default_output_dir() -> Path:
    return _script_dir().parent / "generated" / "assets"


def _role_counts(total: int, roles: Mapping[str, Any], rng) -> Dict[str, int]:
    """Proportional allocation by selection_weight; exact sum to total."""
    items = [(name, int(cfg["selection_weight"])) for name, cfg in roles.items()]
    if not items:
        raise ValueError("asset_profiles.yaml: no roles defined")
    wsum = sum(w for _, w in items)
    if wsum <= 0:
        raise ValueError("asset_profiles.yaml: role selection_weight sum must be positive")
    counts: Dict[str, int] = {}
    frac_heap: List[Tuple[float, str]] = []
    assigned = 0
    for name, w in items:
        exact = (total * w) / wsum
        base = int(exact)
        counts[name] = base
        assigned += base
        frac_heap.append((exact - base, name))
    frac_heap.sort(key=lambda x: -x[0])
    remainder = total - assigned
    for j in range(remainder):
        counts[frac_heap[j][1]] += 1
    return counts


def _pick_app_version(role: Mapping[str, Any], rng) -> Optional[str]:
    pool = role.get("app_version_pool")
    if pool:
        return str(pick_weighted(pool, rng)["value"])
    v = role.get("app_version")
    if v is None or v == "null":
        return None
    return str(v)


def _pick_db_version(role: Mapping[str, Any], rng) -> Optional[str]:
    pool = role.get("db_version_pool")
    if pool:
        return str(pick_weighted(pool, rng)["value"])
    v = role.get("db_version")
    if v is None or v == "null":
        return None
    return str(v)


def _pick_compliance_tags(
    role: Mapping[str, Any],
    compliance_pools: Mapping[str, Any],
    rng,
) -> Optional[List[str]]:
    prob = float(role.get("compliance_tag_pick_probability", 0))
    if rng.random() >= prob:
        return None
    ref = str(role.get("compliance_tag_pool_ref", "default"))
    pool = compliance_pools.get(ref) or compliance_pools.get("default")
    if not pool:
        return None
    choice = pick_weighted(pool, rng)
    tags = choice.get("tags")
    if not tags:
        return None
    return [str(t) for t in tags]


def _int_in_range(rng, low: int, high: int) -> int:
    return rng.randint(int(low), int(high))


def _topology_total_host_capacity(topology: NetworkTopology) -> int:
    """Sum of usable host addresses across all VLAN subnets (each IP used at most once)."""
    total = 0
    for v in topology.vlans:
        net = ipaddress.IPv4Network(v.subnet, strict=False)
        gw = ipaddress.IPv4Address(v.gateway)
        total += sum(1 for h in net.hosts() if h != gw)
    return total


def _allocate_in_allowed_vlans(
    topology: NetworkTopology,
    allowed_keys: Sequence[str],
    rng,
    role_name: str,
) -> Tuple[Any, str]:
    """
    Pick a VLAN from allowed_keys with room left, allocating the next host IP.

    Tries keys in random order so large asset counts can spread across subnets.
    """
    order = list(allowed_keys)
    rng.shuffle(order)
    last_err: Optional[RuntimeError] = None
    for vk in order:
        try:
            return topology.allocate_next_ip(vk), vk
        except RuntimeError as e:
            last_err = e
    raise RuntimeError(
        f"No free IPv4 addresses left in any allowed VLAN for role {role_name!r} "
        f"(tried {list(allowed_keys)})"
    ) from last_err


def generate_assets(
    count: int,
    seed: int,
    topology: NetworkTopology,
    profiles: Mapping[str, Any],
) -> Tuple[List[AssetRecord], Dict[str, Any]]:
    rng = make_rng(seed)
    roles_raw = profiles.get("roles") or {}
    if not isinstance(roles_raw, dict):
        raise TypeError("asset_profiles.yaml: 'roles' must be a mapping")

    env_dist = profiles.get("environment_distribution") or []
    avail_by_env = profiles.get("availability_by_environment") or {}
    dmz_mz_by_zone = profiles.get("dmz_mz_by_zone") or {}
    compliance_pools = profiles.get("compliance_tag_pools") or {}

    counts = _role_counts(count, roles_raw, rng)
    seq_by_role: Dict[str, int] = {name: 0 for name in roles_raw}
    itam_seq_by_role: Dict[str, int] = {name: 0 for name in roles_raw}

    rows: List[AssetRecord] = []

    for role_name, n in counts.items():
        role = roles_raw[role_name]
        for _ in range(n):
            seq_by_role[role_name] += 1
            itam_seq_by_role[role_name] += 1
            seq = seq_by_role[role_name]
            itam_n = itam_seq_by_role[role_name]

            env_choice = pick_weighted(env_dist, rng)
            environment = str(env_choice["environment"])
            env_slug = ENV_SLUGS.get(environment, environment.lower().replace(" ", ""))

            allowed = role.get("allowed_vlan_keys") or []
            if not allowed:
                raise ValueError(f"role {role_name!r} has empty allowed_vlan_keys")
            allowed_str = [str(x) for x in allowed]
            ip, vlan_key = _allocate_in_allowed_vlans(topology, allowed_str, rng, role_name)
            vr = topology.get_vlan(vlan_key)

            site_placeholder = SITE_SLUGS.get(vr.location, vr.location.replace("_", ""))

            host_pattern = str(role["hostname_pattern"])
            if "{site}" in host_pattern:
                hn = hostname_generator(host_pattern, site=site_placeholder, seq=seq)
            else:
                hn = hostname_generator(host_pattern, env_slug=env_slug, seq=seq)

            vm_pattern = str(role["vm_display_name_pattern"])
            if "{site}" in vm_pattern:
                vm_dn = hostname_generator(vm_pattern, site=site_placeholder, seq=seq)
            else:
                vm_dn = hostname_generator(vm_pattern, env_slug=env_slug, seq=seq)

            os_pick = pick_weighted(role["os_choices"], rng)
            os_name = str(os_pick["os_name"])
            os_version = str(os_pick["os_version"])

            lo, hi = role["vcpu_range"]
            vcpu = _int_in_range(rng, lo, hi)
            mlo, mhi = role["memory_gb_range"]
            mem_gb = _int_in_range(rng, mlo, mhi)
            memory = f"{mem_gb} GB"

            prefix = str(role.get("itam_id_prefix") or "ITAM")
            itm_id = f"{prefix}-{itam_n:06d}"

            tool_pick = pick_weighted(role["tool_update_pool"], rng)
            tool_update = str(tool_pick["value"])

            availability = str(avail_by_env.get(environment, "Medium"))
            dmz_mz = str(dmz_mz_by_zone.get(vr.zone, "Internal"))

            confidentiality = str(role.get("confidentiality", "Internal"))
            integrity = str(role.get("integrity", "Medium"))

            compliance = _pick_compliance_tags(role, compliance_pools, rng)

            record = AssetRecord(
                ip_address=str(ip),
                segment=vr.segment,
                subnet=vr.subnet,
                gateway=vr.gateway,
                vlan=str(vr.vlan_id),
                os_name=os_name,
                os_version=os_version,
                app_version=_pick_app_version(role, rng),
                db_version=_pick_db_version(role, rng),
                vcpu=vcpu,
                memory=memory,
                hostname=hn,
                vm_display_name=vm_dn,
                environment=environment,
                location=topology.location_display_name(vr.location),
                availability=availability,
                itm_id=itm_id,
                tool_update=tool_update,
                dmz_mz=dmz_mz,
                confidentiality=confidentiality,
                integrity=integrity,
                compliance_tags=compliance,
            )
            rows.append(record)

    rng.shuffle(rows)

    manifest: Dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "asset_count": len(rows),
        "allocated_ips_by_vlan": topology.manifest_allocated_by_vlan(),
    }
    return rows, manifest


def _write_csv(path: Path, records: Sequence[AssetRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = list(AssetRecord.CSV_HEADERS)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        w.writeheader()
        for r in records:
            w.writerow(r.to_csv_row())


def _write_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Generate asset registry CSV and IP manifest.")
    p.add_argument(
        "--size",
        choices=tuple(SIZE_COUNTS),
        required=True,
        help="Preset row count: small=50, medium=500, large=5000",
    )
    p.add_argument("--seed", type=int, default=42, help="RNG seed for reproducible output")
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory (default: tests/testdata_generation/generated/assets/)",
    )
    args = p.parse_args(list(argv) if argv is not None else None)

    out_dir = args.output if args.output is not None else _default_output_dir()
    out_dir = out_dir.resolve()

    count = SIZE_COUNTS[args.size]
    topo = NetworkTopology.from_reference("network_topology")
    profiles = load_reference_yaml("asset_profiles")

    cap = _topology_total_host_capacity(topo)
    if count > cap:
        print(
            f"error: --size {args.size} requests {count} assets but the reference topology "
            f"only has {cap} assignable host IPv4 addresses. Expand subnets in "
            f"reference/network_topology.yaml or pick a smaller size.",
            file=sys.stderr,
        )
        return 1

    records, manifest = generate_assets(count, args.seed, topo, profiles)

    csv_path = out_dir / f"asset_registry_{args.size}.csv"
    man_path = out_dir / f"asset_registry_{args.size}_manifest.json"

    _write_csv(csv_path, records)
    _write_manifest(man_path, manifest)

    print(f"Wrote {len(records)} rows to {csv_path}")
    print(f"Wrote manifest to {man_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
