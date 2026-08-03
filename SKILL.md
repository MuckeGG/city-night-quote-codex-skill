---
name: city-night-quote-codex-skill
description: Create reusable city-night quote videos with verified official-source excerpts, local landmark image-gen assets, subtitles, timelines, publishing copy, and directly generated editable Jianying drafts. Use when the user asks for a city-night quote video, local landmark motivational content, official-media quote adaptation, Jianying/CapCut-ready drafts or subtitles, or a repeatable AI short-video workflow.
---

# 城市夜读短视频制作

将“官方来源金句 + 本地城市夜景/地标 + 剪映配音 + Codex字幕”生成内容包和可编辑剪映草稿。默认制作25–35秒竖屏视频；若用户指定时长，以用户指定值为准。

## 交付边界

- 在 Codex 中完成选题、来源核对、脚本、分镜、图片提示词、image-gen生图、字幕、时间轴和发布文案。
- 默认直接写入剪映草稿目录，创建9:16可编辑草稿。草稿必须含画面轨、连续旁白文本轨、屏幕字幕轨和空BGM轨。
- 将配音和BGM留在剪映：连续旁白轨供用户执行文本朗读，BGM轨供用户添加剪映内授权音乐。不要在 Codex 中伪造剪映配音。
- 使用内置 `image_gen` 生成位图素材；每个关键镜头单独生成并保存到当前内容包的 `assets/` 目录。不要改用外部API或自行编写图片生成客户端。
- 不生成冒充人民日报、央视新闻或播音员的Logo、台标、声音、新闻包装或官方背书。

## 工作流

按以下阶段顺序执行，并在每个阶段保留可编辑产物：

1. **定位**：锁定一座城市、一个地标、一个情绪主题和转发对象。输出 `brief.md`。
2. **来源**：优先使用人民日报、央视新闻等官方页面。记录来源URL、标题、日期、作者、原文摘录和使用方式，输出 `source-ledger.csv`。无法核对来源时，向用户索要原文或链接，不要猜写金句。
3. **大纲**：用“地标钩子→金句→本地情绪解释→送给某人”的四拍结构。25–35秒通常安排4–6个画面段落。
4. **旁白**：写一段适合剪映连续文本朗读的完整中文旁白。开头2秒出现城市/地标，金句只朗读短摘录，结尾使用原创收束。输出 `script.md` 和 `narration.txt`。
5. **分镜**：为每段旁白固定 `shot_id`、画面内容、景别、机位、动作、光线、情绪和时长。分镜中的旁白原文不可改写、遗漏、合并或调换。输出 `storyboard.md` 和机器可读的 `shots.json`。
6. **图片提示词**：为每个镜头写完整的中文 image-gen prompt，包含主体、动作、环境、镜头、构图、光线、色调、竖屏画幅和负面约束。输出 `image-prompts.md`。
7. **image-gen**：调用内置 `image_gen`，逐镜头生成图片。保持同一城市、地标特征、季节、时间段和视觉风格一致；避免图片出现文字、字幕、Logo、水印或伪造的实时新闻信息。生成后检查并把最终图片保存到 `assets/shot-XX.png`。
8. **字幕与时间轴**：使用 `scripts/build_subtitles.py` 根据旁白和目标时长生成初版 `subtitles.srt`、`timeline.csv` 和 `timeline.json`。字幕按自然句意分段，不按每个镜头机械断句。
9. **剪映草稿**：读取 `references/jianying-draft.md`，运行 `scripts/create_jianying_draft.py`，将草稿直接写入本机剪映草稿目录。不要通过界面逐张导入和手工剪辑。输出 `jianying_draft.json`，并保留 `capcut_handoff.md` 作为人工交接备份。
10. **验收**：运行 `scripts/validate_content_package.py`，再检查草稿的画布为1080×1920、总时长正确、视频段数量等于去重后的 `shot_id` 数、字幕段数量等于时间轴条目数。若本机装有剪映，确认首页能看到草稿标题；不要为了验证而手工重建时间线。

## 固定输出结构

```text
outputs/<city>-<date>-<slug>/
├── brief.md
├── script.md
├── narration.txt
├── storyboard.md
├── shots.json
├── image-prompts.md
├── subtitles.srt
├── timeline.csv
├── timeline.json
├── source-ledger.csv
├── publish-copy.md
├── capcut_handoff.md
├── jianying_draft.json
├── jianying_assets/
└── assets/
```

## 内容与来源规则

- “来自官方媒体”不等于自动获得商业转载授权。前期可做短摘录并明确出处；挂书链接或接广告后，优先使用授权原文或原创转述。
- 不整篇抓取、整段朗读或搬运原视频；不把事实新闻加工成未经核实的新闻报道。
- 生成的城市画面必须标注“AI生成画面”或使用平台提供的AI标识；不把AI想象图描述为真实航拍、实时天气或真实现场。
- BGM由用户在剪映中选择平台授权或可商用音乐。旁白优先，BGM不得覆盖人声。
- 养生书、健康商品和商家广告不得使用疾病治疗、保证效果或虚假本地事实表述。

## 何时需要用户确认

- 用户只给了媒体名称，没有给出可核对的文章或金句：先搜索官方来源；仍无法核对时暂停来源阶段。
- 用户要求原文商业朗读但没有授权：改为短摘录/原创转述，并明确风险。
- 用户要求生成真实人物、官方播音员声音、官方Logo或仿真新闻画面：拒绝该部分，改为通用旁白和原创栏目包装。
- 用户指定的地标需要参考图才能保持准确外观：先请求用户提供图片或明确允许使用公开参考图，再生成。

## 资源

- 读取 `references/workflow-source-map.md` 了解迁移自 today-dungeon-studio 的阶段、数据对象和真实音频校准思路。
- 读取 `references/storyboard-and-imagegen.md` 生成城市夜景分镜和 image-gen 提示词。
- 读取 `references/source-and-rights.md` 处理官方来源、短摘录、商业化和AI标识。
- 读取 `references/jianying-draft.md` 直接创建和验证可编辑剪映草稿。
- 读取 `references/capcut-handoff.md` 生成剪映交接包和可选的真实音频校准输入。
