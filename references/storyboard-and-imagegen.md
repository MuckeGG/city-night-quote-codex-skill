# 分镜与 image-gen 规范

## 25–35秒默认节奏

| 段落 | 建议时长 | 作用 |
|---|---:|---|
| 城市钩子 | 0–2秒 | 立即说出城市或地标 |
| 夜景建立 | 2–6秒 | 建立归属感和氛围 |
| 金句主体 | 6–22秒 | 连续朗读短摘录 |
| 原创收束 | 22–30秒 | 将金句落到本地生活 |
| 转发出口 | 30–35秒 | 送给家人、朋友或同城的人 |

## 分镜字段

每个镜头必须包含：

`shot_id, narration, duration, scene, camera, emotion, image_prompt, negative_prompt, motion_prompt`

描述顺序使用：`主体 → 动作 → 环境互动 → 景别/构图 → 镜头运动 → 光线/色彩 → 约束`。

## image-gen 提示词模板

```text
Use case: photorealistic-natural
Asset type: vertical short-video keyframe, 9:16
Primary request: [本地城市/地标]的夜景情绪画面
Scene/backdrop: [季节、时间、天气、城市空间]
Subject: [地标主体或街道主体]
Composition/framing: [大远景/中景/特写]，[三分法/引导线/留白]
Camera: [35mm或50mm视角]，缓慢推近或横移的静态关键帧构图
Lighting/mood: [暖色灯光、雨后反光、安静、治愈、克制]
Color palette: [低饱和蓝紫/暖金/青灰]
Text (verbatim): ""
Constraints: no readable text, no subtitles, no logo, no watermark, no news graphics, no fake live-reporting cues, preserve recognizable landmark structure
Avoid: distorted architecture, extra towers, impossible roads, duplicated vehicles, deformed people, oversaturated cyberpunk, text artifacts
```

不在生图提示词里加入金句文字；字幕和来源信息由 Codex/剪映后期完成。
