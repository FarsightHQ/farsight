"""CSV asset mapping: sparse rows must not imply clearing unset fields."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.asset_registry_service import AssetRegistryService


class TestSparseCsvRowMapping(unittest.TestCase):
    def test_ip_only_row_has_only_ip_key(self) -> None:
        row = pd.Series({"ip": "10.0.0.5"})
        mapped = AssetRegistryService._map_csv_row_to_asset(row)
        self.assertEqual(mapped, {"ip_address": "10.0.0.5"})

    def test_ip_and_hostname_includes_both(self) -> None:
        row = pd.Series({"ip_address": "10.0.0.1", "hostname": "web-01"})
        mapped = AssetRegistryService._map_csv_row_to_asset(row)
        self.assertEqual(mapped["ip_address"], "10.0.0.1")
        self.assertEqual(mapped["hostname"], "web-01")
        self.assertNotIn("segment", mapped)

    def test_empty_hostname_cell_omits_hostname(self) -> None:
        row = pd.Series({"ip": "10.0.0.2", "hostname": ""})
        mapped = AssetRegistryService._map_csv_row_to_asset(row)
        self.assertEqual(mapped, {"ip_address": "10.0.0.2"})


if __name__ == "__main__":
    unittest.main()
