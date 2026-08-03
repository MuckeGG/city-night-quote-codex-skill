#!/usr/bin/env python3
"""Validate the final files emitted by the city-night quote workflow."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


TIME_RE = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$")


def parse_time(value: str) -> float:
    match = TIME_RE.match(value.strip())
    if not match:
        raise ValueError(f"invalid SRT time: {value}")
    hours, minutes, seconds, milliseconds = map(int, match.groups())
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000


def validate_srt(path: Path) -> list[str]:
    errors: list[str] = []
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    blocks = []
    current: list[str] = []
    for line in lines + [""]:
        if line.strip():
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    previous_end = -1.0
    for expected_index, block in enumerate(blocks, start=1):
        if len(block) < 3:
            errors.append(f"SRT block {expected_index} is incomplete")
            continue
        try:
            if int(block[0]) != expected_index:
                errors.append(f"SRT index {block[0]} is not {expected_index}")
            start_text, end_text = block[1].split(" --> ", 1)
            start, end = parse_time(start_text), parse_time(end_text)
            if end <= start:
                errors.append(f"SRT block {expected_index} has non-positive duration")
            if start < previous_end - 0.01:
                errors.append(f"SRT block {expected_index} overlaps the previous block")
            previous_end = end
        except (ValueError, IndexError) as exc:
            errors.append(f"SRT block {expected_index}: {exc}")
        if any(len(text) > 24 for text in block[2:]):
            errors.append(f"SRT block {expected_index} has a line longer than 24 characters")
    return errors


def validate_csv(path: Path) -> list[str]:
    required = {"shot_id", "start", "end", "image_path", "voice_text", "caption", "motion"}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            return [f"timeline.csv is missing columns: {sorted(required - set(reader.fieldnames or []))}"]
        rows = list(reader)
    errors: list[str] = []
    previous = -1.0
    for index, row in enumerate(rows, start=1):
        try:
            start, end = float(row["start"]), float(row["end"])
            if end <= start or start < previous - 0.01:
                errors.append(f"timeline row {index} has invalid or overlapping times")
            previous = end
        except ValueError:
            errors.append(f"timeline row {index} has invalid numeric times")
        if not row["voice_text"].strip():
            errors.append(f"timeline row {index} has empty voice_text")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("--min-assets", type=int, default=1)
    args = parser.parse_args()
    root = args.package_dir
    required = [
        "brief.md",
        "script.md",
        "narration.txt",
        "storyboard.md",
        "image-prompts.md",
        "subtitles.srt",
        "timeline.csv",
        "timeline.json",
        "source-ledger.csv",
        "capcut_handoff.md",
    ]
    errors = [f"missing file: {name}" for name in required if not (root / name).is_file()]
    assets = [p for p in (root / "assets").glob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}] if (root / "assets").is_dir() else []
    if len(assets) < args.min_assets:
        errors.append(f"expected at least {args.min_assets} image assets, found {len(assets)}")
    if (root / "subtitles.srt").is_file():
        errors.extend(validate_srt(root / "subtitles.srt"))
    if (root / "timeline.csv").is_file():
        errors.extend(validate_csv(root / "timeline.csv"))
    if (root / "source-ledger.csv").is_file():
        with (root / "source-ledger.csv").open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            errors.append("source-ledger.csv has no source rows")
        for row in rows:
            if not row.get("source_name") or not row.get("usage_mode"):
                errors.append("source-ledger.csv has a row without source_name or usage_mode")
    disclosure_files = [root / "capcut_handoff.md", root / "publish-copy.md"]
    if not any(path.is_file() and "AI生成" in path.read_text(encoding="utf-8") for path in disclosure_files):
        errors.append("missing AI-generated content disclosure")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: {root} ({len(assets)} image assets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
