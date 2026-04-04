"""
Spot-checks for tests/testdata_generation/generated CSVs.

- Asset registries: rows map via AssetRegistryService._map_csv_row_to_asset and satisfy AssetRegistryCreate.
- Firewall rules: CSVValidationService file/structure/row-count checks pass.
- Error fixtures: expected validation or row-parse failures (aligned with actual backend behavior).
"""
from __future__ import annotations

import csv
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.schemas.asset_registry import AssetRegistryCreate
from app.services.asset_registry_service import AssetRegistryService
from app.services.csv_ingestion_service import CsvIngestionService
from app.services.csv_validation_service import CSVValidationService
from app.utils.csv_errors import CSVColumnError, CSVFileError, CSVValidationError

REPO_ROOT = BACKEND_ROOT.parent
GENERATED = REPO_ROOT / "tests" / "testdata_generation" / "generated"
ASSETS_DIR = GENERATED / "assets"
FIREWALL_DIR = GENERATED / "firewall_rules"
ERR_DIR = GENERATED / "error_scenarios"


def _asset_row_indices(n: int) -> list[int]:
    if n <= 200:
        return list(range(n))
    base = {0, 1, 2, n // 4, n // 2, (3 * n) // 4, n - 3, n - 2, n - 1}
    base.update(range(min(n, 50)))
    return sorted(base)


class TestGeneratedAssetRegistryCSV(unittest.TestCase):
    def test_small_medium_large_map_and_validate(self) -> None:
        for name in (
            "asset_registry_small.csv",
            "asset_registry_medium.csv",
            "asset_registry_large.csv",
        ):
            path = ASSETS_DIR / name
            self.assertTrue(path.is_file(), f"Missing generated asset file: {path}")
            df = pd.read_csv(path)
            self.assertGreater(len(df), 0, f"{name} has no rows")
            for i in _asset_row_indices(len(df)):
                row = df.iloc[i]
                mapped = AssetRegistryService._map_csv_row_to_asset(row)
                self.assertTrue(
                    mapped.get("ip_address"),
                    f"{name} row {i}: expected ip_address after mapping",
                )
                AssetRegistryCreate(created_by="testdata_verify", **mapped)


class TestGeneratedFirewallRulesCSV(unittest.TestCase):
    def test_all_rules_csv_pass_csv_validation_service(self) -> None:
        for path in sorted(FIREWALL_DIR.glob("rules_*.csv")):
            raw = path.read_bytes()
            decoded, _meta = CSVValidationService.validate_file_structure(raw)
            _fieldnames, _cm = CSVValidationService.validate_csv_structure(decoded)
            row_count = CSVValidationService.validate_row_count(decoded)
            self.assertGreater(
                row_count,
                0,
                f"{path.name}: expected at least one data row",
            )


class TestGeneratedErrorScenarioCSVs(unittest.TestCase):
    def test_valid_sample_passes_validation_pipeline(self) -> None:
        path = ERR_DIR / "valid_sample.csv"
        raw = path.read_bytes()
        decoded, _ = CSVValidationService.validate_file_structure(raw)
        CSVValidationService.validate_csv_structure(decoded)
        n = CSVValidationService.validate_row_count(decoded)
        self.assertEqual(n, 5)

    def test_empty_file_raises_csv_file_error(self) -> None:
        raw = (ERR_DIR / "empty_file.csv").read_bytes()
        with self.assertRaises(CSVFileError) as ctx:
            CSVValidationService.validate_file_structure(raw)
        self.assertIn("empty", ctx.exception.message.lower())

    def test_wrong_columns_raises_csv_column_error(self) -> None:
        decoded = (ERR_DIR / "wrong_columns.csv").read_text(encoding="utf-8")
        with self.assertRaises(CSVColumnError) as ctx:
            CSVValidationService.validate_csv_structure(decoded)
        self.assertIn("Missing required columns", ctx.exception.message)

    def test_duplicate_columns_raises_csv_column_error(self) -> None:
        decoded = (ERR_DIR / "duplicate_columns.csv").read_text(encoding="utf-8")
        with self.assertRaises(CSVColumnError) as ctx:
            CSVValidationService.validate_csv_structure(decoded)
        self.assertIn("Duplicate", ctx.exception.message)

    def test_no_header_raises_csv_validation_error(self) -> None:
        decoded = (ERR_DIR / "no_header.csv").read_text(encoding="utf-8")
        with self.assertRaises(CSVValidationError) as ctx:
            CSVValidationService.validate_csv_structure(decoded)
        self.assertIn("header", ctx.exception.message.lower())

    def test_header_only_raises_csv_validation_error(self) -> None:
        decoded = (ERR_DIR / "header_only.csv").read_text(encoding="utf-8")
        CSVValidationService.validate_csv_structure(decoded)
        with self.assertRaises(CSVValidationError) as ctx:
            CSVValidationService.validate_row_count(decoded)
        self.assertIn("no data rows", ctx.exception.message.lower())

    def test_missing_source_raises_csv_column_error(self) -> None:
        decoded = (ERR_DIR / "missing_source.csv").read_text(encoding="utf-8")
        with self.assertRaises(CSVColumnError) as ctx:
            CSVValidationService.validate_csv_structure(decoded)

    def test_missing_multiple_raises_csv_column_error(self) -> None:
        decoded = (ERR_DIR / "missing_multiple.csv").read_text(encoding="utf-8")
        with self.assertRaises(CSVColumnError) as ctx:
            CSVValidationService.validate_csv_structure(decoded)

    def test_not_a_csv_txt_raises_csv_column_error(self) -> None:
        raw = (ERR_DIR / "not_a_csv.txt").read_bytes()
        decoded, _ = CSVValidationService.validate_file_structure(raw)
        with self.assertRaises(CSVColumnError) as ctx:
            CSVValidationService.validate_csv_structure(decoded)
        self.assertIn("Missing required columns", ctx.exception.message)

    def test_corrupted_utf8_not_strict_utf8(self) -> None:
        raw = (ERR_DIR / "corrupted_utf8.csv").read_bytes()
        with self.assertRaises(UnicodeDecodeError):
            raw.decode("utf-8")

    def test_empty_fields_rows_fail_parse(self) -> None:
        svc = CsvIngestionService(MagicMock())
        decoded = (ERR_DIR / "empty_fields.csv").read_text(encoding="utf-8")
        _, cm = CSVValidationService.validate_csv_structure(decoded)
        reader = csv.DictReader(io.StringIO(decoded))
        rows = list(reader)
        with self.assertRaises(ValueError):
            svc._parse_csv_row(rows[0], cm)
        with self.assertRaises(ValueError):
            svc._parse_csv_row(rows[3], cm)

    def test_invalid_ips_rows_fail_parse(self) -> None:
        svc = CsvIngestionService(MagicMock())
        decoded = (ERR_DIR / "invalid_ips.csv").read_text(encoding="utf-8")
        _, cm = CSVValidationService.validate_csv_structure(decoded)
        reader = csv.DictReader(io.StringIO(decoded))
        rows = list(reader)
        with self.assertRaises(ValueError) as ctx:
            svc._parse_csv_row(rows[0], cm)
        self.assertIn("source", ctx.exception.args[0].lower())
        with self.assertRaises(ValueError):
            svc._parse_csv_row(rows[1], cm)

    def test_invalid_ports_rows_fail_parse(self) -> None:
        svc = CsvIngestionService(MagicMock())
        decoded = (ERR_DIR / "invalid_ports.csv").read_text(encoding="utf-8")
        _, cm = CSVValidationService.validate_csv_structure(decoded)
        reader = csv.DictReader(io.StringIO(decoded))
        rows = list(reader)
        with self.assertRaises(ValueError) as ctx:
            svc._parse_csv_row(rows[0], cm)
        self.assertIn("service", ctx.exception.args[0].lower())

    def test_malformed_csv_structure_valid_but_fields_corrupted(self) -> None:
        """Python's csv module accepts the fixture; quoted newlines leak into cell values."""
        decoded = (ERR_DIR / "malformed.csv").read_text(encoding="utf-8")
        CSVValidationService.validate_csv_structure(decoded)
        reader = csv.DictReader(io.StringIO(decoded))
        rows = list(reader)
        self.assertTrue(rows)
        self.assertTrue(
            any("\n" in (v or "") for v in rows[0].values()),
            "Expected malformed quoting to surface as embedded newlines in parsed fields",
        )


if __name__ == "__main__":
    unittest.main()
