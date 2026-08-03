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
- 源项目 v0.3.0 的“两次生成”闭环已迁移：先让剪映生成真实 `textReading` 音频，再按音频真实时长重建画面时间轴和音画同步版草稿。
- 本 Skill 进一步限制首稿只能有一条完整旁白文本，并验证 `textReading/` 恰好只有一个文件，从结构上避免短字幕逐条朗读造成断气、重叠和漂移。
- 源项目使用语音转写取得短字幕时间；本 Skill 在最终草稿中直接调用剪映对完整旁白音频“识别字幕/歌词”，时间点同样来自真实语音，同时保留整段朗读的自然连贯性。

## 不迁移的内容

- Windows启动器、FastAPI服务、桌面UI、数据库和Windows凭据管理器。
- 源项目的现实冲突故事模板；本 Skill 的主体改为本地城市夜景、地标和官方来源金句。
