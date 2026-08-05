# city-night-quote-codex-skill

用 Codex 自动完成“城市夜景 + 官方来源短摘录 + 字幕 + 可编辑剪映草稿”的短视频工作流。

Codex 负责来源核对、脚本、分镜、ImageGen 生图、字幕和时间轴；剪映负责文本朗读与授权 BGM。生成器直接创建草稿，不需要逐张导入、手工排列。

## 工作流

```text
城市与主题
  → 核对官方来源
  → 旁白与分镜
  → ImageGen 逐镜生图
  → 初版 SRT 与画面时间轴
  → 创建“整段朗读”首稿
  → 剪映一次性朗读完整文稿
  → 读取真实音频时长并创建音画同步版
  → 剪映从完整音频识别字幕 + 添加授权 BGM
  → 自动生成视频号发布文案 + 5个话题
```

设计参考了 [today-dungeon-studio](https://github.com/MuckeGG/today-dungeon-studio) 的阶段化创作流程，以及 [Hamburgerai 的 Codex 视频制作复盘](https://x.com/Hamburgerai/status/2083419087246664038) 中三条经验：数据和构建器分离、系统差异显式处理、验收最终交付物而不是中间文件。

## Windows / macOS 支持

| 项目 | Windows | macOS |
|---|---|---|
| 默认草稿目录 | `%LOCALAPPDATA%\JianyingPro\User Data\Projects\com.lveditor.draft` | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft` |
| 旧版草稿入口 | `draft_content.json` | 不推荐 |
| 当前草稿入口 | `draft_info.json` | `draft_info.json` |
| 自动判断 | 读取本机最近的有效草稿；没有样本时兼容旧版 | 固定使用当前格式 |
| 素材位置 | 草稿内部 `assets/` | 草稿内部 `assets/`，避免 macOS 文件权限导致素材离线 |

生成器支持两层选择：

- `--platform auto|windows|macos`：默认识别当前操作系统。
- `--draft-format auto|modern|legacy`：`modern` 写入 `draft_info.json`，`legacy` 写入 `draft_content.json`。

若 Windows 剪映升级后仍误判，可显式添加 `--draft-format modern`。若使用旧版 Windows 剪映，可添加 `--draft-format legacy`。

## 安装为 Codex Skill

### macOS

```bash
git clone https://github.com/MuckeGG/city-night-quote-codex-skill.git \
  ~/.codex/skills/city-night-quote-codex-skill
cd ~/.codex/skills/city-night-quote-codex-skill
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Windows PowerShell

```powershell
git clone https://github.com/MuckeGG/city-night-quote-codex-skill.git `
  "$env:USERPROFILE\.codex\skills\city-night-quote-codex-skill"
cd "$env:USERPROFILE\.codex\skills\city-night-quote-codex-skill"
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

安装后重启 Codex，然后直接说：

> 使用 city-night-quote-codex-skill，生成一集广州城市夜读，并直接创建剪映草稿。

## 音画同步的两阶段草稿

前提是内容包已经包含 `timeline.json`、`narration.txt` 和镜头图片。

第一阶段只生成一条完整旁白文本，不创建短字幕轨。因此在剪映中不会再误选七条短字幕、生成七段断续配音。

### 1. 创建整段朗读首稿

```bash
python scripts/create_jianying_draft.py \
  --package-dir /absolute/path/to/outputs/guangzhou-episode \
  --phase voice \
  --title "广州夜读｜灯火照见认真生活的人"
```

Windows PowerShell 使用相同参数，只需改为 Windows 路径和续行符。

打开首稿，只选中 `01 连续旁白（整段朗读一次）`，选择音色后执行一次“文本朗读”。不要创建短字幕配音。

### 2. 读取真实配音并创建最终草稿

```bash
python scripts/align_jianying_voice.py \
  --package-dir /absolute/path/to/outputs/guangzhou-episode \
  --source-draft "/absolute/path/to/剪映草稿/广州夜读｜灯火照见认真生活的人"

python scripts/create_jianying_draft.py \
  --package-dir /absolute/path/to/outputs/guangzhou-episode \
  --phase final \
  --timeline-file /absolute/path/to/outputs/guangzhou-episode/timeline-aligned.json \
  --audio-file /absolute/path/to/outputs/guangzhou-episode/audio/complete-narration.wav \
  --title "广州夜读｜音画同步版"
```

打开“音画同步版”，对 `01 完整旁白（已按真实时长）` 执行“识别字幕/歌词”。字幕时间由真实语音识别生成，比按字数估算更准确，也不破坏整段朗读的连贯性。

音频扩展名以 `audio-alignment-report.json` 的 `audio_output` 为准：不同剪映版本可能输出 WAV 或 MP3，脚本会保留真实格式。

### Windows PowerShell 示例

```powershell
python scripts/create_jianying_draft.py `
  --package-dir "C:\absolute\path\to\outputs\guangzhou-episode" `
  --phase voice `
  --title "广州夜读｜灯火照见认真生活的人"
```

草稿目录会自动识别。若剪映使用了自定义目录，增加 `--drafts-dir`。

默认不覆盖同名草稿。只有确认要替换时才使用 `--replace`。

## 验收标准

“首页出现标题”不等于草稿有效。每次生成后至少检查：

1. 草稿入口文件能解析，轨道数、时长和画面段正确。
2. 剪映能真正进入编辑时间线，不能出现“草稿已损坏”。
3. 点击画面片段后预览区能显示图片，不能出现“暂无访问权限”或“链接媒体”。
4. 朗读首稿的 `textReading` 中只有一个音频；最终草稿只有一条完整旁白音频。
5. 最终字幕由完整音频识别生成，播放抽查时文字切换与声音一致。
6. 内容包包含可直接发布的 `publish-copy.md`，正文注明AI生成画面，结尾恰好有5个视频号话题。

## 视频号发布文案

最终草稿验收后，Codex 会自动生成 `publish-copy.md`，无需再次提醒。固定格式为：

```markdown
# 视频号发布文案

## 正文

一句本地城市或地标情绪钩子。

2–4句承接视频主题，并自然邀请转发或送给某人。

画面为AI生成。

## 话题（固定5个）

#城市 #地标 #城市夜读 #情绪主题 #目标人群
```

话题必须恰好5个，优先覆盖城市、地标、栏目、情绪和目标人群；不写“必火”“十万播放”等无法保证的表述。

## 音色建议

- 默认：`云泽大叔`。温和、可信、有生活阅历，适合城市夜读和中老年用户，但不会过分像官方新闻播音。
- 更克制、更有文化感：`自然纪录片`。
- 更柔和、偏陪伴感：`真人播客女`。

不建议使用“真人新闻主播”等强官方感音色，以免让原创栏目看起来像官方媒体配音或背书。剪映音色名称可能随版本变化；找不到同名音色时，选择“自然、舒缓、普通话清晰”的通用声音。

## 常见问题

### 首页有标题，但打开显示“草稿已损坏”

通常是入口文件名与剪映版本不匹配。当前剪映使用 `draft_info.json`；旧流程固定写 `draft_content.json`。重新生成并显式指定 `--draft-format modern`。

### 打开后图片显示“暂无访问权限”

旧草稿引用了 `Documents` 等外部目录，macOS 剪映没有访问权限。新版生成器会把图片复制到草稿内部 `assets/`，请重新生成，不要手工重新链接五张图片。

### 更换电脑后能直接打开旧草稿吗

Skill 代码可以通过 GitHub 重新安装；单集草稿仍包含本机绝对路径，不建议把 macOS 草稿文件夹原样复制到 Windows。更换系统后用同一个内容包重新运行生成器，它会按新系统重写素材路径和草稿入口。

### 为什么配音和 BGM 不自动生成

这是刻意保留的交付边界：旁白在剪映执行“文本朗读”，BGM 使用剪映内授权音乐，避免伪造官方播音员声音和不明版权音乐。

### 为什么检测到“应当只有 1 段，实际有多段”

说明在旧草稿中对短字幕逐条执行了朗读。多段配音不仅有停顿，还会让估算字幕逐渐漂移。删除该首稿并重新运行 `--phase voice`，只对唯一的完整旁白文本执行一次朗读。

## 内容与版权

- 官方媒体内容只使用经过核对的短摘录，并保留来源记录；商业化前优先改为原创转述或取得授权。
- 不生成人民日报、央视新闻的 Logo、台标、仿官方新闻包装或播音员克隆音色。
- AI 城市画面应按平台规则标注，不能冒充实时航拍、实时天气或新闻现场。
- BGM 使用剪映平台授权或明确可商用音乐。
