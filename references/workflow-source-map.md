# 源流程迁移图

参考 `MuckeGG/today-dungeon-studio` v0.3.0 的公开仓库界面和已登录可读的私有仓库文件，保留其流程思想，不复制源代码或素材。

## 保留的设计

源项目把创作拆成有序阶段：`positioning → outline → script → storyboard → prompts → images → voice → timeline → jianying`。每个阶段有状态、可回看、可单独重跑；提示词采用“全局规则 + 阶段导演指令”，并保留历史版本。

源项目的数据对象可映射为：

- `Positioning` → `brief.md`
- `StoryOutline` → `outline.md`
- `ScriptResult` → `narration.txt`、`script.md`
- `Scene` / `Storyboard` → `shots.json`、`storyboard.md`
- `ImageVersion` → `assets/` 与 `manifest.json`
- `TimelineItem` / `Timeline` → `timeline.json`、`timeline.csv`、`subtitles.srt`

## 本 Skill 的替换

- 源项目支持多个API生图服务；本 Skill 只使用 Codex 内置 `image_gen`，一镜头一调用，最终文件落到内容包 `assets/`。
- 源项目使用剪映文本朗读，不在工作台内生成本地配音；本 Skill 保留这一边界。
- 源项目 v0.3.0 的真实音频校准思路保留为可选输入：用户在剪映完成配音后，可提供 `timings.json`，再生成精确字幕和图片时间轴。
- 源项目的长旁白连续性规则迁移为：先输出一份完整 `narration.txt`，字幕只是该旁白的分段呈现。

## 不迁移的内容

- Windows启动器、FastAPI服务、桌面UI、数据库、Windows凭据管理器和剪映草稿私有目录。
- 源项目的现实冲突故事模板；本 Skill 的主体改为本地城市夜景、地标和官方来源金句。
