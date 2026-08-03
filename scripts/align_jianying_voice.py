#!/usr/bin/env python3
"""Build a real-audio timeline from one continuous Jianying text reading."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


AUDIO_SUFFIXES = {".aac", ".m4a", ".mp3", ".wav"}


def find_single_reading(source_draft: Path) -> Path:
    reading_dir = source_draft / "textReading"
    if not reading_dir.is_dir():
        raise FileNotFoundError(
            f"草稿里没有 textReading：{reading_dir}。请先在剪映中对整段旁白执行一次朗读。"
        )
    files = sorted(
        path
        for path in reading_dir.iterdir()
        if path.is_file() and path.suffix.lower() in AUDIO_SUFFIXES
    )
    if len(files) != 1:
        raise RuntimeError(
            f"应当只有 1 段完整旁白音频，实际检测到 {len(files)} 段。"
            "这通常说明误选了短字幕逐条朗读；请使用‘连续旁白’草稿重新生成一次。"
        )
    return files[0]


def audio_duration_seconds(path: Path) -> float:
    try:
        import pyJianYingDraft as draft
    except ImportError as exc:
        raise RuntimeError(
            "缺少 pyJianYingDraft==0.3.0，无法读取剪映旁白的真实时长。"
        ) from exc
    duration = draft.AudioMaterial(str(path)).duration / 1_000_000
    if duration <= 0:
        raise ValueError(f"音频时长无效：{path}")
    return duration


def retime_timeline(timeline: dict[str, Any], duration: float) -> dict[str, Any]:
    old_duration = float(timeline.get("duration", 0))
    items = timeline.get("items", [])
    if old_duration <= 0 or not items:
        raise ValueError("原始 timeline.json 缺少有效 duration/items")
    scale = duration / old_duration
    aligned_items: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        aligned = dict(item)
        aligned["start"] = round(float(item["start"]) * scale, 6)
        aligned["end"] = (
            round(duration, 6)
            if index == len(items) - 1
            else round(float(item["end"]) * scale, 6)
        )
        aligned_items.append(aligned)
    return {
        **timeline,
        "duration": round(duration, 6),
        "items": aligned_items,
        "timing_source": "jianying_single_continuous_reading",
        "caption_timing": "generate_in_jianying_from_complete_audio",
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def align(
    package_dir: Path,
    source_draft: Path,
    output_timeline: Path | None = None,
    audio_output: Path | None = None,
) -> dict[str, Any]:
    timeline_path = package_dir / "timeline.json"
    if not timeline_path.exists():
        raise FileNotFoundError(f"缺少原始时间轴：{timeline_path}")
    source_audio = find_single_reading(source_draft)
    duration = audio_duration_seconds(source_audio)
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    aligned = retime_timeline(timeline, duration)

    output_timeline = output_timeline or package_dir / "timeline-aligned.json"
    audio_output = audio_output or package_dir / (
        f"audio/complete-narration{source_audio.suffix.lower()}"
    )
    output_timeline.parent.mkdir(parents=True, exist_ok=True)
    audio_output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_audio, audio_output)
    output_timeline.write_text(
        json.dumps(aligned, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = {
        "status": "aligned",
        "method": "single_continuous_jianying_reading",
        "source_draft": str(source_draft.resolve()),
        "source_audio": str(source_audio.resolve()),
        "audio_output": str(audio_output.resolve()),
        "audio_duration_seconds": round(duration, 6),
        "source_timeline_duration_seconds": float(timeline["duration"]),
        "timeline_output": str(output_timeline.resolve()),
        "audio_sha256": sha256(audio_output),
        "subtitle_sync": (
            "最终草稿中对完整旁白音频执行剪映‘识别字幕/歌词’，"
            "字幕时间以真实语音识别结果为准。"
        ),
    }
    report_path = package_dir / "audio-alignment-report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--source-draft", type=Path, required=True)
    parser.add_argument("--output-timeline", type=Path)
    parser.add_argument("--audio-output", type=Path)
    args = parser.parse_args()
    result = align(
        args.package_dir.expanduser().resolve(),
        args.source_draft.expanduser().resolve(),
        args.output_timeline.expanduser().resolve() if args.output_timeline else None,
        args.audio_output.expanduser().resolve() if args.audio_output else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
