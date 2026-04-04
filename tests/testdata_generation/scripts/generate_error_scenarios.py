#!/usr/bin/env python3
"""
Generate negative-test CSV fixtures for CSVValidationService and ingestion row parsing.

Writes into tests/testdata_generation/generated/error_scenarios/ by default.
See tests/testdata_generation/README.md (if present) for how these map to validation errors.

No third-party dependencies (stdlib only).
"""

from __future__ import annotations

import argparse
from pathlib import Path


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def _default_output_dir() -> Path:
    return _script_dir().parent / "generated" / "error_scenarios"


def _write_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    path.write_text(content, encoding=encoding, newline="\n")


def _write_bytes(path: Path, content: bytes) -> None:
    path.write_bytes(content)


def generate_all(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Baseline: passes structure + row-count checks; ingestion should succeed for these rows.
    _write_text(
        output_dir / "valid_sample.csv",
        """source,destination,service,action,direction
10.0.0.1,10.0.0.2,tcp/80,allow,inbound
10.0.0.3,10.0.0.4,tcp/443,allow,outbound
192.168.1.1,192.168.1.2,udp/53,allow,inbound
10.1.0.0/24,10.2.0.0/24,tcp/22-25,deny,bidirectional
172.16.0.1,172.16.0.2,icmp,allow,inbound
""",
    )

    # CSVFileError: empty file (validate_file_structure)
    _write_bytes(output_dir / "empty_file.csv", b"")

    # CSVColumnError: missing required logical columns
    _write_text(
        output_dir / "wrong_columns.csv",
        """col1,col2,col3
10.0.0.1,10.0.0.2,tcp/80
10.0.0.3,10.0.0.4,tcp/443
192.168.1.1,192.168.1.2,udp/53
""",
    )

    # CSVColumnError: duplicate headers (case-insensitive)
    _write_text(
        output_dir / "duplicate_columns.csv",
        """source,destination,service,Source
10.0.0.1,10.0.0.2,tcp/80,10.0.0.3
""",
    )

    # CSVValidationError: no header row (csv.DictReader.fieldnames is empty)
    _write_text(output_dir / "no_header.csv", "\n")

    # Row-level: empty required fields after trim (ingestion / CSVRowError / skipped semantics)
    _write_text(
        output_dir / "empty_fields.csv",
        """source,destination,service
,10.0.0.2,tcp/80
10.0.0.1,,tcp/443
10.0.0.3,10.0.0.4,
,,
10.0.0.5,10.0.0.6,tcp/80
""",
    )

    # Row-level: endpoints fail normalize_ip_address → no valid endpoints
    _write_text(
        output_dir / "invalid_ips.csv",
        """source,destination,service
999.999.999.999,10.0.0.2,tcp/80
10.0.0.1,256.256.256.256,tcp/443
abc.def,10.0.0.4,udp/53
10.0.0.5,10.0.0.6,tcp/80
""",
    )

    # Row-level: invalid port specs (normalize_port_ranges / out of range)
    _write_text(
        output_dir / "invalid_ports.csv",
        """source,destination,service
10.0.0.1,10.0.0.2,tcp/99999
10.0.0.3,10.0.0.4,tcp/-1
192.168.1.1,192.168.1.2,udp/65536
10.0.0.5,10.0.0.6,tcp/abc
10.0.0.7,10.0.0.8,tcp/70000-80000
""",
    )

    # CSVColumnError: destination+service present but no source (or alias)
    _write_text(
        output_dir / "missing_source.csv",
        """destination,service
10.0.0.2,tcp/80
10.0.0.4,tcp/443
""",
    )

    # CSVColumnError: missing both source and destination
    _write_text(
        output_dir / "missing_multiple.csv",
        """service,action
tcp/80,allow
tcp/443,deny
""",
    )

    # CSVValidationError: csv.Error while parsing structure
    _write_text(
        output_dir / "malformed.csv",
        """source,destination,service
"10.0.0.1,10.0.0.2,tcp/80
"10.0.0.3","10.0.0.4","tcp/443
192.168.1.1,192.168.1.2,"udp/53
""",
    )

    # CSVEncodingError: UTF-8 decode fails on full buffer
    good = "source,destination,service\n10.0.0.1,10.0.0.2,tcp/80\n".encode("utf-8")
    _write_bytes(output_dir / "corrupted_utf8.csv", good + b"\xff\xfe\x00")

    # Plain text (upload layer may reject before CSVValidationService)
    _write_text(
        output_dir / "not_a_csv.txt",
        """This is not a CSV file.
It is intentionally plain text for negative tests.
""",
    )

    # CSVValidationError: header only, no data rows (validate_row_count)
    _write_text(
        output_dir / "header_only.csv",
        "source,destination,service,action,direction\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"Output directory (default: {_default_output_dir()})",
    )
    args = parser.parse_args()
    out = args.output.resolve() if args.output else _default_output_dir()
    generate_all(out)
    print(f"Wrote error scenario fixtures to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
