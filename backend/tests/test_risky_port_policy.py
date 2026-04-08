"""Tests for global risky port policy parsing and matching."""
from types import SimpleNamespace
import pytest

from app.utils.port_formatter import parse_postgres_port_multirange_to_ranges
from app.services.risky_port_policy_service import (
    apply_risky_port_policy_to_analysis,
    collect_matching_policy_entries,
)


def test_parse_multirange_single_and_range():
    assert parse_postgres_port_multirange_to_ranges("{[22,22]}") == [(22, 22)]
    assert parse_postgres_port_multirange_to_ranges("{[8001,8010]}") == [(8001, 8010)]
    assert parse_postgres_port_multirange_to_ranges("{[80,80],[443,443]}") == [
        (80, 80),
        (443, 443),
    ]


def test_parse_multirange_empty_and_malformed():
    assert parse_postgres_port_multirange_to_ranges("{}") == []
    assert parse_postgres_port_multirange_to_ranges("") == []
    assert parse_postgres_port_multirange_to_ranges("not-a-range") == []


def test_no_false_positive_port_2222_for_ssh_22():
    entries = [
        SimpleNamespace(
            id=1,
            protocol="tcp",
            port_start=22,
            port_end=22,
            label="SSH",
            recommendation=None,
            severity="info",
            enabled=True,
            sort_order=0,
        )
    ]
    services = [{"protocol": "tcp", "port_ranges": "{[2222,2222]}"}]
    assert collect_matching_policy_entries(services, entries) == {}


def test_overlap_matches_ssh_22():
    entries = [
        SimpleNamespace(
            id=1,
            protocol="tcp",
            port_start=22,
            port_end=22,
            label="SSH",
            recommendation=None,
            severity="info",
            enabled=True,
            sort_order=0,
        )
    ]
    services = [{"protocol": "tcp", "port_ranges": "{[22,22]}"}]
    m = collect_matching_policy_entries(services, entries)
    assert 1 in m and m[1].label == "SSH"


def test_protocol_both_matches_udp():
    entries = [
        SimpleNamespace(
            id=2,
            protocol="both",
            port_start=69,
            port_end=69,
            label="TFTP",
            recommendation=None,
            severity="high",
            enabled=True,
            sort_order=0,
        )
    ]
    services = [{"protocol": "udp", "port_ranges": "{[69,69]}"}]
    assert 2 in collect_matching_policy_entries(services, entries)


def test_apply_high_severity_penalty_capped():
    analysis = {"security_score": 100, "risk_level": "low", "issues": [], "recommendations": []}
    entries = [
        SimpleNamespace(
            id=i,
            protocol="tcp",
            port_start=1000 + i,
            port_end=1000 + i,
            label=f"P{i}",
            recommendation=None,
            severity="high",
            enabled=True,
            sort_order=i,
        )
        for i in range(1, 5)
    ]
    services = [{"protocol": "tcp", "port_ranges": "{[1001,1004]}"}]
    apply_risky_port_policy_to_analysis(analysis, services, entries, rich_issues=False)
    # 4 high rows: 10 each capped at 25
    assert analysis["security_score"] == 75
    assert len([x for x in analysis["issues"] if x["type"] == "risky_port"]) == 4


def test_apply_warning_once_per_rule():
    analysis = {"security_score": 100, "issues": [], "recommendations": []}
    entries = [
        SimpleNamespace(
            id=1,
            protocol="tcp",
            port_start=80,
            port_end=80,
            label="A",
            recommendation=None,
            severity="warning",
            enabled=True,
            sort_order=0,
        ),
        SimpleNamespace(
            id=2,
            protocol="tcp",
            port_start=443,
            port_end=443,
            label="B",
            recommendation=None,
            severity="warning",
            enabled=True,
            sort_order=1,
        ),
    ]
    services = [{"protocol": "tcp", "port_ranges": "{[80,80],[443,443]}"}]
    apply_risky_port_policy_to_analysis(analysis, services, entries, rich_issues=False)
    warning_issues = [i for i in analysis["issues"] if i["severity"] == "medium"]
    assert len(warning_issues) == 1
    assert analysis["security_score"] == 95
