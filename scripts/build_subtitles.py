#!/usr/bin/env python3
"""Build an editable SRT and CapCut-friendly image timeline from narration."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Segment:
    index: int
    start: float
    end: float
    text: str
    shot_id: int
    image_path: str
    motion: str


def clean_text(value: str) -> str:
    return re.sub(r"\s+", "", value).strip()


def chunks(text: str, max_chars: int) -> list[str]:
    text = clean_text(text)
    if len(text) <= max_chars:
        return [text] if text else []
    pieces: list[str] = []
    while len(text) > max_chars:
        cut = max_chars
        for i in range(max_chars, max(0, max_chars - 6), -1):
            if text[i - 1] in "，。！？；：、,!?;:":
                cut = i
                break
        pieces.append(text[:cut])
        text = text[cut:]
    if text:
        if pieces and len(text) <= 2 and all(char in "，。！？；：、,!?;:" for char in text):
            pieces[-1] += text
        else:
            pieces.append(text)
    return pieces


def split_sentences(text: str) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    parts = re.findall(r"[^。！？!?；;\n]+[。！？!?；;]?", text)
    return [part for part in parts if clean_text(part)]


def format_srt_time(seconds: float) -> str:
    milliseconds = max(0, int(round(seconds * 1000)))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    seconds_value, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds_value:02d},{milliseconds:03d}"


def read_timing_segments(path: Path, max_chars: int) -> list[Segment]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        raw = raw.get("segments", raw.get("items", []))
    result: list[Segment] = []
    index = 1
    for item in raw:
        start = float(item["start"])
        end = float(item["end"])
        text = clean_text(str(item["text"]))
        parts = chunks(text, max_chars)
        total_chars = max(1, sum(len(part) for part in parts))
        cursor = start
        for part in parts:
            part_duration = (end - start) * len(part) / total_chars
            result.append(
                Segment(
                    index=index,
                    start=cursor,
                    end=cursor + part_duration,
                    text=part,
                    shot_id=int(item.get("shot_id", index)),
                    image_path=str(item.get("image_path", f"assets/shot-{int(item.get('shot_id', index)):02d}.png")),
                    motion=str(item.get("motion", "缓慢推近")),
                )
            )
            cursor += part_duration
            index += 1
    return result


def read_shots(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        raw = raw.get("scenes", raw.get("shots", []))
    return list(raw)


def estimate_segments(
    narration: str,
    target_duration: float | None,
    chars_per_second: float,
    max_chars: int,
    shots: list[dict] | None,
) -> list[Segment]:
    if shots:
        units = []
        for shot in shots:
            text = clean_text(str(shot.get("narration", shot.get("text", ""))))
            units.append(
                {
                    "shot_id": int(shot.get("shot_id", len(units) + 1)),
                    "text": text,
                    "duration": float(shot.get("duration", 0) or 0),
                    "image_path": str(shot.get("image_path", f"assets/shot-{int(shot.get('shot_id', len(units) + 1)):02d}.png")),
                    "motion": str(shot.get("motion_prompt", shot.get("motion", "缓慢推近"))),
                }
            )
    else:
        units = [
            {
                "shot_id": i,
                "text": sentence,
                "duration": 0,
                "image_path": f"assets/shot-{i:02d}.png",
                "motion": "缓慢推近",
            }
            for i, sentence in enumerate(split_sentences(narration), start=1)
        ]

    expanded: list[dict] = []
    for unit in units:
        pieces = chunks(unit["text"], max_chars)
        for piece in pieces:
            expanded.append({**unit, "text": piece})
    if not expanded:
        return []

    base_durations = [
        max(0.8, len(item["text"]) / max(chars_per_second, 0.1) + 0.15)
        for item in expanded
    ]
    if any(item["duration"] for item in expanded):
        shot_totals: dict[int, float] = {}
        for item in expanded:
            shot_totals[item["shot_id"]] = shot_totals.get(item["shot_id"], 0) + item["duration"]
        shot_piece_counts: dict[int, int] = {}
        for item in expanded:
            shot_piece_counts[item["shot_id"]] = shot_piece_counts.get(item["shot_id"], 0) + 1
        base_durations = [shot_totals[item["shot_id"]] / shot_piece_counts[item["shot_id"]] for item in expanded]
    total = sum(base_durations)
    scale = (target_duration / total) if target_duration and total else 1.0
    result: list[Segment] = []
    cursor = 0.0
    for index, (item, base) in enumerate(zip(expanded, base_durations), start=1):
        end = cursor + base * scale
        result.append(
            Segment(
                index=index,
                start=cursor,
                end=end,
                text=item["text"],
                shot_id=item["shot_id"],
                image_path=item["image_path"],
                motion=item["motion"],
            )
        )
        cursor = end
    return result


def write_outputs(output_dir: Path, segments: list[Segment]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    srt_lines: list[str] = []
    for segment in segments:
        srt_lines.extend(
            [
                str(segment.index),
                f"{format_srt_time(segment.start)} --> {format_srt_time(segment.end)}",
                segment.text,
                "",
            ]
        )
    (output_dir / "subtitles.srt").write_text("\n".join(srt_lines), encoding="utf-8")

    with (output_dir / "timeline.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["shot_id", "start", "end", "image_path", "voice_text", "caption", "motion"],
        )
        writer.writeheader()
        for segment in segments:
            writer.writerow(
                {
                    "shot_id": segment.shot_id,
                    "start": f"{segment.start:.3f}",
                    "end": f"{segment.end:.3f}",
                    "image_path": segment.image_path,
                    "voice_text": segment.text,
                    "caption": segment.text,
                    "motion": segment.motion,
                }
            )
    (output_dir / "timeline.json").write_text(
        json.dumps({"duration": segments[-1].end if segments else 0, "items": [asdict(s) for s in segments]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path, help="narration.txt path")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--duration", type=float, default=None)
    parser.add_argument("--chars-per-second", type=float, default=4.8)
    parser.add_argument("--max-line-chars", type=int, default=18)
    parser.add_argument("--shots", type=Path, default=None)
    parser.add_argument("--timings", type=Path, default=None, help="JSON with start/end/text segments")
    args = parser.parse_args()

    narration = args.input.read_text(encoding="utf-8")
    if args.timings:
        segments = read_timing_segments(args.timings, args.max_line_chars)
    else:
        shots = read_shots(args.shots) if args.shots else None
        segments = estimate_segments(
            narration,
            args.duration,
            args.chars_per_second,
            args.max_line_chars,
            shots,
        )
    if not segments:
        raise SystemExit("narration contains no usable text")
    write_outputs(args.output_dir, segments)
    print(json.dumps({"segments": len(segments), "duration": round(segments[-1].end, 3)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
