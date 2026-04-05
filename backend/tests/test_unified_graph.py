"""Tests for unified endpoint graph and CIDR asset resolution."""
from unittest.mock import MagicMock

from app.services.graph_service import GraphService
from app.utils.ip_formatter import extract_base_ip_from_cidr


def test_extract_base_ip_from_cidr():
    assert extract_base_ip_from_cidr("10.100.0.8/32") == "10.100.0.8"
    assert extract_base_ip_from_cidr("10.100.0.0/21") == "10.100.0.0"
    assert extract_base_ip_from_cidr("192.168.1.5") == "192.168.1.5"
    assert extract_base_ip_from_cidr("") == ""


def test_unified_graph_dedupes_nodes_and_merges_edges():
    mock_asset = MagicMock()
    mock_asset.get_asset_for_network_cidr.return_value = None
    mock_asset.create_node_tooltip = MagicMock(side_effect=lambda c, a, t: f"{t}:{c}")

    gs = GraphService(mock_asset)

    rule_data = [
        {
            "rule_id": 1,
            "rule_name": "Rule 1",
            "sources": [{"network_cidr": "10.0.0.1/32"}],
            "destinations": [{"network_cidr": "10.0.0.2/32"}],
            "services": [{"protocol": "tcp", "port_ranges": "{[443,443]}"}],
        },
        {
            "rule_id": 2,
            "rule_name": "Rule 2",
            "sources": [{"network_cidr": "10.0.0.1/32"}],
            "destinations": [{"network_cidr": "10.0.0.2/32"}],
            "services": [{"protocol": "tcp", "port_ranges": "{[80,80]}"}],
        },
    ]

    out = gs.create_unified_endpoint_graph(rule_data)

    assert len(out["nodes"]) == 2
    cidr_set = {n["network_cidr"] for n in out["nodes"]}
    assert cidr_set == {"10.0.0.1/32", "10.0.0.2/32"}

    assert len(out["links"]) == 1
    link = out["links"][0]
    assert link["rule_ids"] == [1, 2]
    assert len(link["services"]) == 2
    protos = {s["protocol"] for s in link["services"]}
    assert protos == {"tcp"}


def test_unified_graph_skips_self_loop():
    mock_asset = MagicMock()
    mock_asset.get_asset_for_network_cidr.return_value = None
    mock_asset.create_node_tooltip = MagicMock(side_effect=lambda c, a, t: f"{t}:{c}")

    gs = GraphService(mock_asset)
    out = gs.create_unified_endpoint_graph(
        [
            {
                "rule_id": 1,
                "sources": [{"network_cidr": "10.0.0.1/32"}],
                "destinations": [{"network_cidr": "10.0.0.1/32"}],
                "services": [],
            }
        ]
    )
    assert len(out["nodes"]) == 1
    assert out["links"] == []


def test_get_asset_for_network_cidr_uses_base_ip():
    from app.services.asset_service import AssetService

    mock_db = MagicMock()
    svc = AssetService(mock_db)
    svc.get_asset_by_ip = MagicMock(return_value={"ip_address": "10.1.1.1", "segment": "S1"})

    result = svc.get_asset_for_network_cidr("10.1.1.1/24")
    assert result is not None
    assert result["segment"] == "S1"
    svc.get_asset_by_ip.assert_called_once_with("10.1.1.1")
