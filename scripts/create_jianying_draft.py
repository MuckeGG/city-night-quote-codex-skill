#!/usr/bin/env python3
"""Create an editable Jianying draft from a city-night content package."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any


VOICE_TRACK = "01 连续旁白（请在本轨执行文本朗读）"
SUBTITLE_TRACK = "02 屏幕字幕（不要在本轨配音）"
BGM_TRACK = "03 舒缓BGM（请在剪映添加）"
VIDEO_TRACK = "画面"
CHIYUN_LI_BOLD_RESOURCE_ID = "7587347429331176750"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--drafts-dir", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def load_package(package_dir: Path) -> tuple[dict[str, Any], str]:
    timeline_path = package_dir / "timeline.json"
    narration_path = package_dir / "narration.txt"
    if not timeline_path.exists():
        raise FileNotFoundError(f"缺少时间轴：{timeline_path}")
    if not narration_path.exists():
        raise FileNotFoundError(f"缺少旁白：{narration_path}")
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    narration = narration_path.read_text(encoding="utf-8").strip()
    if not narration:
        raise ValueError("旁白为空")
    if not timeline.get("items"):
        raise ValueError("时间轴没有镜头")
    return timeline, narration


def copy_assets(package_dir: Path, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    asset_dir = package_dir / "jianying_assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    copied: list[dict[str, Any]] = []
    for item in items:
        source = Path(str(item["image_path"]))
        if not source.is_absolute():
            source = package_dir / source
        if not source.exists():
            raise FileNotFoundError(f"镜头 {item.get('shot_id')} 缺少图片：{source}")
        target = asset_dir / f"shot-{int(item['shot_id']):02d}{source.suffix.lower()}"
        if not target.exists() or target.stat().st_mtime_ns < source.stat().st_mtime_ns:
            shutil.copy2(source, target)
        copied.append({**item, "image_path": str(target.resolve())})
    return copied


def merge_video_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for item in items:
        if merged and merged[-1]["shot_id"] == item["shot_id"]:
            merged[-1]["end"] = item["end"]
            merged[-1]["text"] = f"{merged[-1]['text']}{item['text']}"
        else:
            merged.append(dict(item))
    return merged


def seconds_range(item: dict[str, Any]) -> tuple[str, str]:
    start_ms = round(float(item["start"]) * 1000)
    end_ms = round(float(item["end"]) * 1000)
    start = f"{start_ms / 1000:.3f}s"
    duration = f"{max(1, end_ms - start_ms) / 1000:.3f}s"
    return start, duration


def create_draft(
    package_dir: Path,
    drafts_dir: Path,
    title: str,
    replace: bool,
) -> dict[str, Any]:
    try:
        import pyJianYingDraft as draft
    except ImportError as exc:
        raise RuntimeError(
            "缺少 pyJianYingDraft==0.3.0；请先安装该固定版本"
        ) from exc

    timeline, narration_text = load_package(package_dir)
    copied = copy_assets(package_dir, list(timeline["items"]))
    drafts_dir.mkdir(parents=True, exist_ok=True)
    folder = draft.DraftFolder(str(drafts_dir))
    script = folder.create_draft(title, 1080, 1920, allow_replace=replace)
    script.append_tracks(
        [
            draft.TrackSpec(draft.TrackType.video, VIDEO_TRACK),
            draft.TrackSpec(draft.TrackType.text, VOICE_TRACK),
            draft.TrackSpec(draft.TrackType.text, SUBTITLE_TRACK),
            draft.TrackSpec(draft.TrackType.audio, BGM_TRACK),
        ]
    )

    for item in merge_video_items(copied):
        start, duration = seconds_range(item)
        segment = draft.VideoSegment(
            str(item["image_path"]),
            draft.trange(start, duration),
        )
        segment.add_keyframe(draft.KeyframeProperty.uniform_scale, "0s", 1.0)
        segment.add_keyframe(draft.KeyframeProperty.uniform_scale, duration, 1.04)
        motion = str(item.get("motion", ""))
        if "横移" in motion or "平移" in motion:
            segment.add_keyframe(draft.KeyframeProperty.position_x, "0s", -0.025)
            segment.add_keyframe(draft.KeyframeProperty.position_x, duration, 0.025)
        script.add_segment(segment, VIDEO_TRACK)

    for item in copied:
        start, duration = seconds_range(item)
        caption = draft.TextSegment(
            str(item["text"]),
            draft.trange(start, duration),
            style=draft.TextStyle(
                size=6.0,
                color=(1.0, 1.0, 1.0),
                align=1,
                auto_wrapping=True,
                max_line_width=0.82,
            ),
            clip_settings=draft.ClipSettings(transform_y=-0.72),
            shadow=draft.TextShadow(
                color=(0.0, 0.0, 0.0),
                alpha=0.9,
                diffuse=15.0,
                distance=5.0,
                angle=-45.0,
            ),
        )
        caption.font = SimpleNamespace(resource_id=CHIYUN_LI_BOLD_RESOURCE_ID)
        script.add_segment(caption, SUBTITLE_TRACK)

    narration = draft.TextSegment(
        narration_text,
        draft.trange("0s", f"{float(timeline['duration']):.3f}s"),
        style=draft.TextStyle(size=1.0, alpha=0.0, align=1),
        clip_settings=draft.ClipSettings(alpha=0.0),
    )
    script.add_segment(narration, VOICE_TRACK)
    script.save()

    manifest = {
        "status": "created",
        "title": title,
        "draft_path": str((drafts_dir / title).resolve()),
        "package_dir": str(package_dir.resolve()),
        "width": 1080,
        "height": 1920,
        "duration": float(timeline["duration"]),
        "video_segments": len(merge_video_items(copied)),
        "subtitle_segments": len(copied),
        "tracks": [VIDEO_TRACK, VOICE_TRACK, SUBTITLE_TRACK, BGM_TRACK],
        "instruction": "在01连续旁白轨执行文本朗读；在03舒缓BGM轨添加剪映内授权音乐。",
    }
    manifest_path = package_dir / "jianying_draft.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    args = parse_args()
    package_dir = args.package_dir.resolve()
    result = create_draft(
        package_dir,
        args.drafts_dir.expanduser().resolve(),
        args.title,
        args.replace,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
