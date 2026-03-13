#!/usr/bin/env python3
"""Pack remote txt content into CSV content column.

Input CSV columns: file,url
Output CSV columns: file,url,content

Usage:
    python pack_csv_content.py --input fileURL_20260312_052330.csv --output packed.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
import urllib.request
from typing import Dict, List


def decode_bytes(data: bytes) -> str:
    encodings = ("utf-8", "gb18030")
    for enc in encodings:
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def fetch_text(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "DataViewerPacker/1.0",
            "Accept": "text/plain,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
    return decode_bytes(body).replace("\ufeff", "")


def is_text_row(file_name: str) -> bool:
    return file_name.lower().endswith(".txt")


def pack_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    packed: List[Dict[str, str]] = []

    total = len(rows)
    for idx, row in enumerate(rows, start=1):
        file_name = (row.get("file") or "").strip()
        url = (row.get("url") or "").strip()

        content = ""
        if file_name and url and is_text_row(file_name):
            try:
                content = fetch_text(url)
                print(f"[{idx}/{total}] OK TXT: {file_name}")
            except Exception as exc:  # noqa: BLE001
                content = f"[FETCH_ERROR] {exc}"
                print(f"[{idx}/{total}] ERR TXT: {file_name} -> {exc}", file=sys.stderr)
        else:
            print(f"[{idx}/{total}] SKIP   : {file_name}")

        packed.append(
            {
                "file": file_name,
                "url": url,
                "content": content,
            }
        )

    return packed


def main() -> int:
    parser = argparse.ArgumentParser(description="Pack remote txt content into CSV")
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", required=True, help="Output CSV path")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV header is missing")

        names = [x.strip().lower() for x in reader.fieldnames]
        if "file" not in names or "url" not in names:
            raise ValueError("Input CSV must contain file,url headers")

        rows = list(reader)

    packed_rows = pack_rows(rows)

    with open(args.output, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "url", "content"])
        writer.writeheader()
        writer.writerows(packed_rows)

    print(f"\nDone. Wrote: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
