# city-night-quote-codex-skill

用 Codex 自动完成“城市夜景 + 官方来源短摘录 + 字幕 + 可编辑剪映草稿”的短视频工作流。

Codex 负责来源核对、脚本、分镜、ImageGen 生图、字幕和时间轴；剪映负责文本朗读与授权 BGM。生成器直接创建草稿，不需要逐张导入、手工排列。

## 工作流

```text
城市与主题
  → 核对官方来源
  → 旁白与分镜
  → ImageGen 逐镜生图
  → SRT 与时间轴
  → 自动创建剪映草稿
  → 在剪映中打开验收
  → 文本朗读 + 授权 BGM
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

## 单独创建草稿

前提是内容包已经包含 `timeline.json`、`narration.txt` 和镜头图片。

### macOS

```bash
python scripts/create_jianying_draft.py \
  --package-dir /absolute/path/to/outputs/guangzhou-episode \
  --title "广州夜读｜灯火照见认真生活的人"
```

### Windows PowerShell

```powershell
python scripts/create_jianying_draft.py `
  --package-dir "C:\absolute\path\to\outputs\guangzhou-episode" `
  --title "广州夜读｜灯火照见认真生活的人"
```

草稿目录会自动识别。若剪映使用了自定义目录，增加 `--drafts-dir`。

默认不覆盖同名草稿。只有确认要替换时才使用 `--replace`。

## 验收标准

“首页出现标题”不等于草稿有效。每次生成后至少检查：

1. 草稿入口文件能解析，轨道数、时长、画面段和字幕段正确。
2. 剪映能真正进入编辑时间线，不能出现“草稿已损坏”。
3. 点击画面片段后预览区能显示图片，不能出现“暂无访问权限”或“链接媒体”。
4. 旁白文本轨完整，字幕轨和画面轨时间正确。

当前 macOS 实机验证：1080×1920、32 秒、5 个画面段、7 条字幕，能进入时间线并显示草稿内图片。

## 常见问题

### 首页有标题，但打开显示“草稿已损坏”

通常是入口文件名与剪映版本不匹配。当前剪映使用 `draft_info.json`；旧流程固定写 `draft_content.json`。重新生成并显式指定 `--draft-format modern`。

### 打开后图片显示“暂无访问权限”

旧草稿引用了 `Documents` 等外部目录，macOS 剪映没有访问权限。新版生成器会把图片复制到草稿内部 `assets/`，请重新生成，不要手工重新链接五张图片。

### 更换电脑后能直接打开旧草稿吗

Skill 代码可以通过 GitHub 重新安装；单集草稿仍包含本机绝对路径，不建议把 macOS 草稿文件夹原样复制到 Windows。更换系统后用同一个内容包重新运行生成器，它会按新系统重写素材路径和草稿入口。

### 为什么配音和 BGM 不自动生成

这是刻意保留的交付边界：旁白在剪映执行“文本朗读”，BGM 使用剪映内授权音乐，避免伪造官方播音员声音和不明版权音乐。

## 内容与版权

- 官方媒体内容只使用经过核对的短摘录，并保留来源记录；商业化前优先改为原创转述或取得授权。
- 不生成人民日报、央视新闻的 Logo、台标、仿官方新闻包装或播音员克隆音色。
- AI 城市画面应按平台规则标注，不能冒充实时航拍、实时天气或新闻现场。
- BGM 使用剪映平台授权或明确可商用音乐。

