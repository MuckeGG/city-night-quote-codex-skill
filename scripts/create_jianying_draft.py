#!/usr/bin/env python3
"""Create an editable Jianying draft from a city-night content package."""

from __future__ import annotations

import argparse
import json
import os
import platform as platform_module
import shutil
import time
import uuid
from pathlib import Path
from typing import Any


VOICE_TRACK = "01 连续旁白（整段朗读一次）"
ALIGNED_AUDIO_TRACK = "01 完整旁白（已按真实时长）"
BGM_TRACK = "03 舒缓BGM（最后添加）"
VIDEO_TRACK = "画面"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--drafts-dir", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument(
        "--phase",
        choices=("voice", "final"),
        default="voice",
        help="voice=只生成一条长旁白；final=写入真实旁白音频",
    )
    parser.add_argument(
        "--timeline-file",
        type=Path,
        help="可选时间轴；默认使用内容包 timeline.json",
    )
    parser.add_argument(
        "--audio-file",
        type=Path,
        help="final 阶段必填：剪映生成的完整旁白音频",
    )
    parser.add_argument(
        "--platform",
        choices=("auto", "windows", "macos"),
        default="auto",
        help="目标系统；auto 使用当前系统",
    )
    parser.add_argument(
        "--draft-format",
        choices=("auto", "modern", "legacy"),
        default="auto",
        help="modern=draft_info.json，legacy=draft_content.json",
    )
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def resolve_platform(requested: str) -> str:
    if requested != "auto":
        return requested
    current = platform_module.system().lower()
    if current == "darwin":
        return "macos"
    if current == "windows":
        return "windows"
    raise RuntimeError(f"不支持自动识别的系统：{platform_module.system()}")


def default_drafts_dir(target_platform: str) -> Path:
    if target_platform == "macos":
        return Path.home() / "Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("Windows 环境缺少 LOCALAPPDATA，请显式传入 --drafts-dir")
    return Path(local_app_data) / "JianyingPro/User Data/Projects/com.lveditor.draft"


def resolve_draft_format(
    drafts_dir: Path,
    target_platform: str,
    requested: str,
) -> str:
    if requested != "auto":
        return requested

    if target_platform == "macos":
        return "modern"

    samples: list[tuple[int, str]] = []
    if drafts_dir.exists():
        for child in drafts_dir.iterdir():
            if not child.is_dir():
                continue
            modern = child / "draft_info.json"
            legacy = child / "draft_content.json"
            if modern.exists():
                samples.append((modern.stat().st_mtime_ns, "modern"))
            elif legacy.exists():
                samples.append((legacy.stat().st_mtime_ns, "legacy"))
    if samples:
        return max(samples)[1]

    # Current macOS Jianying uses draft_info.json. Keep the historical Windows
    # default for users who still run the older Jianying version used by the
    # original today-dungeon-studio workflow.
    return "legacy"


def validate_title(title: str, target_platform: str) -> None:
    if not title.strip():
        raise ValueError("草稿标题不能为空")
    forbidden = '<>:"/\\|?*' if target_platform == "windows" else "/:"
    found = sorted({char for char in title if char in forbidden})
    if found:
        raise ValueError(f"草稿标题含系统不允许的字符：{''.join(found)}")


def load_package(
    package_dir: Path,
    timeline_file: Path | None = None,
) -> tuple[dict[str, Any], str]:
    timeline_path = timeline_file or package_dir / "timeline.json"
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


def copy_assets(
    package_dir: Path,
    items: list[dict[str, Any]],
    asset_dir: Path,
) -> list[dict[str, Any]]:
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
    target_platform: str,
    draft_format: str,
    phase: str,
    timeline_file: Path | None = None,
    audio_file: Path | None = None,
) -> dict[str, Any]:
    try:
        import pyJianYingDraft as draft
    except ImportError as exc:
        raise RuntimeError(
            "缺少 pyJianYingDraft==0.3.0；请先安装该固定版本"
        ) from exc

    timeline, narration_text = load_package(package_dir, timeline_file)
    if phase == "final" and (audio_file is None or not audio_file.exists()):
        raise FileNotFoundError("final 阶段缺少 --audio-file 完整旁白音频")
    drafts_dir.mkdir(parents=True, exist_ok=True)
    folder = draft.DraftFolder(str(drafts_dir))
    script = folder.create_draft(title, 1080, 1920, allow_replace=replace)
    draft_path = drafts_dir / title
    copied = copy_assets(
        package_dir,
        list(timeline["items"]),
        draft_path / "assets",
    )
    content_filename = (
        "draft_info.json" if draft_format == "modern" else "draft_content.json"
    )
    # pyJianYingDraft 0.3.0 always chooses draft_content.json. Override only
    # the save target so the same timeline builder works on both draft formats.
    script.save_path = str(draft_path / content_filename)
    tracks = [draft.TrackSpec(draft.TrackType.video, VIDEO_TRACK)]
    track_names_in_order = [VIDEO_TRACK]
    if phase == "voice":
        tracks.append(draft.TrackSpec(draft.TrackType.text, VOICE_TRACK))
        track_names_in_order.append(VOICE_TRACK)
    else:
        tracks.append(draft.TrackSpec(draft.TrackType.audio, ALIGNED_AUDIO_TRACK))
        track_names_in_order.append(ALIGNED_AUDIO_TRACK)
    tracks.append(draft.TrackSpec(draft.TrackType.audio, BGM_TRACK))
    track_names_in_order.append(BGM_TRACK)
    script.append_tracks(tracks)

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

    if phase == "voice":
        # Intentionally keep only one narration text segment. Short caption
        # segments are deferred so Jianying cannot accidentally create seven
        # overlapping TTS clips from the subtitle track.
        narration = draft.TextSegment(
            narration_text,
            draft.trange("0s", f"{float(timeline['duration']):.3f}s"),
            style=draft.TextStyle(size=1.0, alpha=0.0, align=1),
            clip_settings=draft.ClipSettings(alpha=0.0),
        )
        script.add_segment(narration, VOICE_TRACK)
    else:
        assert audio_file is not None
        audio_target = (
            draft_path / "assets" / f"complete-narration{audio_file.suffix.lower()}"
        )
        shutil.copy2(audio_file, audio_target)
        audio = draft.AudioSegment(
            str(audio_target.resolve()),
            draft.trange("0s", f"{float(timeline['duration']):.3f}s"),
        )
        script.add_segment(audio, ALIGNED_AUDIO_TRACK)
    script.save()

    meta_path = draft_path / "draft_meta_info.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.update(
        {
            "draft_id": str(uuid.uuid4()).upper(),
            "draft_name": title,
            "draft_fold_path": str(draft_path.resolve()),
            "draft_root_path": str(drafts_dir.resolve()),
            "tm_duration": round(float(timeline["duration"]) * 1_000_000),
        }
    )
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    now = int(time.time())
    (draft_path / "draft_settings").write_text(
        "[General]\n"
        f"draft_create_time={now}\n"
        f"draft_last_edit_time={now}\n"
        "real_edit_keys=1\n"
        "real_edit_seconds=0\n",
        encoding="utf-8",
    )
    (draft_path / "key_value.json").write_text("{}\n", encoding="utf-8")

    content_path = draft_path / content_filename
    content = json.loads(content_path.read_text(encoding="utf-8"))
    tracks = content.get("tracks", [])
    track_names = {track.get("name") for track in tracks}
    required_tracks = {VIDEO_TRACK, BGM_TRACK}
    required_tracks.add(VOICE_TRACK if phase == "voice" else ALIGNED_AUDIO_TRACK)
    if not required_tracks.issubset(track_names):
        missing = sorted(required_tracks - track_names)
        raise RuntimeError(f"草稿结构校验失败，缺少轨道：{missing}")

    manifest = {
        "status": "created",
        "title": title,
        "draft_path": str(draft_path.resolve()),
        "platform": target_platform,
        "draft_format": draft_format,
        "content_file": content_filename,
        "phase": phase,
        "package_dir": str(package_dir.resolve()),
        "width": 1080,
        "height": 1920,
        "duration": float(timeline["duration"]),
        "video_segments": len(merge_video_items(copied)),
        "subtitle_segments": 0,
        "tracks": track_names_in_order,
        "validation": {
            "json_structure": "passed",
            "jianying_open": "pending",
        },
        "instruction": (
            "只选中01连续旁白，选择推荐音色后整段朗读一次；不要生成短字幕配音。"
            if phase == "voice"
            else "完整旁白已写入；打开草稿后对01音频执行识别字幕，再添加授权BGM。"
        ),
    }
    manifest_path = package_dir / "jianying_draft.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    args = parse_args()
    target_platform = resolve_platform(args.platform)
    validate_title(args.title, target_platform)
    package_dir = args.package_dir.resolve()
    drafts_dir = (
        args.drafts_dir.expanduser().resolve()
        if args.drafts_dir
        else default_drafts_dir(target_platform).resolve()
    )
    draft_format = resolve_draft_format(
        drafts_dir,
        target_platform,
        args.draft_format,
    )
    result = create_draft(
        package_dir,
        drafts_dir,
        args.title,
        args.replace,
        target_platform,
        draft_format,
        args.phase,
        args.timeline_file.expanduser().resolve() if args.timeline_file else None,
        args.audio_file.expanduser().resolve() if args.audio_file else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
