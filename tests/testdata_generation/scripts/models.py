"""
Shared types and helpers for test data generation scripts.

Loads reference YAML under tests/testdata_generation/reference/, models network
VLANs/subnets, allocates non-colliding host IPs, and provides weighted picking
and hostname templating. Generators should construct a dedicated random.Random
per run (see make_rng) for reproducible output.
"""

from __future__ import annotations

import ipaddress
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Mapping, Optional, Sequence, Tuple, Union

import yaml

# --- Paths -----------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
REFERENCE_DIR = SCRIPT_DIR.parent / "reference"


def reference_dir() -> Path:
    """Directory containing network_topology.yaml, asset_profiles.yaml, etc."""
    return REFERENCE_DIR


def load_reference_yaml(name: str) -> Dict[str, Any]:
    """
    Load a YAML file from the reference directory.

    `name` is the stem only, e.g. ``"network_topology"`` or ``"asset_profiles"``.
    """
    stem = name[:-5] if name.endswith(".yaml") else name
    path = REFERENCE_DIR / f"{stem}.yaml"
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Reference {stem}.yaml must parse to a mapping, got {type(data)}")
    return data


def load_yaml(path: Union[str, Path]) -> Dict[str, Any]:
    """Load an arbitrary YAML path (must be a mapping at the top level)."""
    p = Path(path)
    with p.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{p} must parse to a mapping, got {type(data)}")
    return data


# --- Random / weighting ----------------------------------------------------


def make_rng(seed: Optional[int] = None) -> random.Random:
    """Return an isolated RNG. Prefer this in generators so `--seed` is local and testable."""
    return random.Random(seed)


def set_global_seed(seed: int) -> None:
    """Seed the module-level `random` (for code paths that use `random.*` directly)."""
    random.seed(seed)


def pick_weighted(
    choices: Sequence[Mapping[str, Any]],
    rng: random.Random,
    *,
    weight_key: str = "weight",
) -> Mapping[str, Any]:
    """
    Pick one mapping from `choices` using integer or float weights.

    Weights must be non-negative; at least one choice must have weight > 0.
    """
    if not choices:
        raise ValueError("pick_weighted: empty choices")
    weights: List[float] = []
    for c in choices:
        w = float(c.get(weight_key, 0))
        if w < 0:
            raise ValueError(f"pick_weighted: negative weight {w!r} in {c!r}")
        weights.append(w)
    total = sum(weights)
    if total <= 0:
        raise ValueError("pick_weighted: total weight must be positive")
    r = rng.uniform(0, total)
    acc = 0.0
    for c, w in zip(choices, weights):
        acc += w
        if r <= acc:
            return c
    return choices[-1]


def hostname_from_pattern(pattern: str, **placeholders: Any) -> str:
    """
    Fill a hostname or display-name pattern using ``str.format`` rules.

    Example: ``hostname_from_pattern("web-{env_slug}-{seq:02d}", env_slug="prod", seq=3)``
    -> ``web-prod-03``.
    """
    return pattern.format(**placeholders)


# Alias expected by the test data generation plan.
hostname_generator = hostname_from_pattern


# --- Network topology ------------------------------------------------------


@dataclass(frozen=True)
class VlanRecord:
    """One VLAN entry from network_topology.yaml."""

    key: str
    vlan_id: int
    name: str
    zone: str
    location: str
    subnet: str
    gateway: str
    segment: str
    description: str


def _parse_vlan_row(row: Mapping[str, Any]) -> VlanRecord:
    return VlanRecord(
        key=str(row["key"]),
        vlan_id=int(row["vlan_id"]),
        name=str(row["name"]),
        zone=str(row["zone"]),
        location=str(row["location"]),
        subnet=str(row["subnet"]),
        gateway=str(row["gateway"]),
        segment=str(row["segment"]),
        description=str(row.get("description") or ""),
    )


class NetworkTopology:
    """
    Parsed network_topology.yaml: VLAN lookup, zone grouping, sequential IP
    allocation within each subnet (excluding network, broadcast, and gateway).
    """

    def __init__(self, data: Mapping[str, Any]):
        self._raw: Dict[str, Any] = dict(data)
        self.locations: Dict[str, Any] = dict(self._raw.get("locations") or {})
        self.zones: Dict[str, Any] = dict(self._raw.get("zones") or {})
        vlans_raw = self._raw.get("vlans") or []
        self.vlans: Tuple[VlanRecord, ...] = tuple(_parse_vlan_row(v) for v in vlans_raw)
        self._by_key: Dict[str, VlanRecord] = {v.key: v for v in self.vlans}
        self._by_zone: Dict[str, List[VlanRecord]] = {}
        for v in self.vlans:
            self._by_zone.setdefault(v.zone, []).append(v)
        # Per-VLAN ordered host list and cursor (lazy)
        self._host_lists: Dict[str, List[ipaddress.IPv4Address]] = {}
        self._next_idx: Dict[str, int] = {}
        self._allocated: Dict[str, List[ipaddress.IPv4Address]] = {k: [] for k in self._by_key}

    @classmethod
    def from_reference(cls, stem: str = "network_topology") -> NetworkTopology:
        return cls(load_reference_yaml(stem))

    def get_vlan(self, vlan_key: str) -> VlanRecord:
        if vlan_key not in self._by_key:
            raise KeyError(f"Unknown VLAN key: {vlan_key!r}")
        return self._by_key[vlan_key]

    def vlans_in_zone(self, zone: str) -> List[VlanRecord]:
        return list(self._by_zone.get(zone, []))

    def vlan_keys_in_zone(self, zone: str) -> List[str]:
        return [v.key for v in self.vlans_in_zone(zone)]

    def location_display_name(self, location_key: str) -> str:
        loc = self.locations.get(location_key)
        if isinstance(loc, dict) and "display_name" in loc:
            return str(loc["display_name"])
        return location_key

    def subnet_network(self, vlan_key: str) -> ipaddress.IPv4Network:
        vr = self.get_vlan(vlan_key)
        return ipaddress.IPv4Network(vr.subnet, strict=False)

    def _build_host_list(self, vlan_key: str) -> List[ipaddress.IPv4Address]:
        vr = self.get_vlan(vlan_key)
        net = ipaddress.IPv4Network(vr.subnet, strict=False)
        gw = ipaddress.IPv4Address(vr.gateway)
        # For typical prefixes, .hosts() omits network and broadcast addresses.
        return [h for h in net.hosts() if h != gw]

    def _ensure_hosts(self, vlan_key: str) -> None:
        if vlan_key not in self._host_lists:
            self._host_lists[vlan_key] = self._build_host_list(vlan_key)
            self._next_idx[vlan_key] = 0

    def allocate_next_ip(self, vlan_key: str) -> ipaddress.IPv4Address:
        """
        Return the next unused host IP in the VLAN subnet.

        Raises RuntimeError if the subnet is exhausted.
        """
        self._ensure_hosts(vlan_key)
        hosts = self._host_lists[vlan_key]
        idx = self._next_idx[vlan_key]
        if idx >= len(hosts):
            raise RuntimeError(f"No free IPv4 addresses left in VLAN {vlan_key!r} ({self.get_vlan(vlan_key).subnet})")
        ip = hosts[idx]
        self._next_idx[vlan_key] = idx + 1
        self._allocated[vlan_key].append(ip)
        return ip

    def allocated_ips(self, vlan_key: Optional[str] = None) -> List[ipaddress.IPv4Address]:
        """All IPs allocated so far, optionally restricted to one VLAN key."""
        if vlan_key is not None:
            return list(self._allocated.get(vlan_key, []))
        out: List[ipaddress.IPv4Address] = []
        for ips in self._allocated.values():
            out.extend(ips)
        return out

    def manifest_allocated_by_vlan(self) -> Dict[str, List[str]]:
        """JSON-serializable map of VLAN key -> list of allocated IP strings."""
        return {k: [str(ip) for ip in ips] for k, ips in self._allocated.items() if ips}


# --- Asset / firewall records ----------------------------------------------


@dataclass
class AssetRecord:
    """
    Fields aligned with AssetRegistryService._map_csv_row_to_asset / CSV upload.

    CSV writers can map these snake_case fields to the human-readable headers
    expected by the backend (e.g. os_name -> "OS").
    """

    ip_address: Optional[str] = None
    segment: Optional[str] = None
    subnet: Optional[str] = None
    gateway: Optional[str] = None
    vlan: Optional[str] = None
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    db_version: Optional[str] = None
    vcpu: Optional[int] = None
    memory: Optional[str] = None
    hostname: Optional[str] = None
    vm_display_name: Optional[str] = None
    environment: Optional[str] = None
    location: Optional[str] = None
    availability: Optional[str] = None
    itm_id: Optional[str] = None
    tool_update: Optional[str] = None
    dmz_mz: Optional[str] = None
    confidentiality: Optional[str] = None
    integrity: Optional[str] = None
    compliance_tags: Optional[List[str]] = None
    extended_properties: Optional[Dict[str, str]] = None

    # Order matches common export header row used by generators.
    CSV_HEADERS: ClassVar[Tuple[str, ...]] = (
        "IP Address",
        "Segment",
        "Subnet",
        "Gateway",
        "VLAN",
        "OS",
        "OS Version",
        "App Version",
        "DB Version",
        "vCPU",
        "Memory",
        "Hostname",
        "VM Display Name - VMware",
        "Env",
        "Location",
        "Availability",
        "ITAM ID",
        "Tool_Update",
        "DMZ/MZ",
        "Confidentially",
        "Integrity",
        "Compliance",
    )

    def to_csv_row(self) -> Dict[str, str]:
        """Map to CSV column names (string values; blanks for missing)."""
        def s(x: Any) -> str:
            if x is None:
                return ""
            if isinstance(x, list):
                return ", ".join(str(i) for i in x)
            return str(x)

        return {
            "IP Address": s(self.ip_address),
            "Segment": s(self.segment),
            "Subnet": s(self.subnet),
            "Gateway": s(self.gateway),
            "VLAN": s(self.vlan),
            "OS": s(self.os_name),
            "OS Version": s(self.os_version),
            "App Version": s(self.app_version),
            "DB Version": s(self.db_version),
            "vCPU": s(self.vcpu),
            "Memory": s(self.memory),
            "Hostname": s(self.hostname),
            "VM Display Name - VMware": s(self.vm_display_name),
            "Env": s(self.environment),
            "Location": s(self.location),
            "Availability": s(self.availability),
            "ITAM ID": s(self.itm_id),
            "Tool_Update": s(self.tool_update),
            "DMZ/MZ": s(self.dmz_mz),
            "Confidentially": s(self.confidentiality),
            "Integrity": s(self.integrity),
            "Compliance": s(self.compliance_tags) if self.compliance_tags else "",
        }


@dataclass
class FirewallRule:
    """One firewall rule row: required triple plus optional policy columns."""

    source: str
    destination: str
    service: str
    action: Optional[str] = None
    direction: Optional[str] = None
