# Windows / macOS 剪映草稿生成规范

## 实现原则

- 使用 `pyJianYingDraft==0.3.0` 构建时间线，不通过剪映界面逐张导入或手工排列。
- Windows 与 macOS 共用同一时间线构建器，入口文件由系统与剪映版本决定：当前格式为 `draft_info.json`，旧格式为 `draft_content.json`。
- 所有图片复制到草稿内部 `assets/` 后再写入时间线，避免 macOS 沙盒权限和跨目录移动造成素材离线。
- 草稿为1080×1920竖屏，图片按 `timeline.json` 的时间点放置。
- 相邻且 `shot_id` 相同的字幕条目合并为一个画面段；字幕仍逐条保留。
- 画面默认添加1.00到1.04的缓慢推近；时间轴标注横移时添加轻微水平关键帧。
- 连续旁白作为一条不可见文本片段放在 `01 连续旁白（请在本轨执行文本朗读）`。
- 屏幕字幕放在 `02 屏幕字幕（不要在本轨配音）`。
- 建立空的 `03 舒缓BGM（请在剪映添加）` 音频轨，不自动下载或添加未经授权音乐。

## 依赖与安装

先检查固定版本：

```bash
python3 -c "import pyJianYingDraft"
```

缺失时安装到临时或用户可写目录，并通过 `PYTHONPATH` 调用：

```bash
python3 -m pip install -r requirements.txt
```

不要升级到未验证版本后直接生成草稿。Windows 可将 `python3` 换成 `py -3`。

## 草稿目录

macOS 常用目录：

```text
/Users/<user>/Movies/JianyingPro/User Data/Projects/com.lveditor.draft
```

Windows 常用目录：

```text
C:\Users\<user>\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft
```

若目录不存在，先在剪映设置中查看草稿保存位置，不要猜测或写入其他用户目录。

## 自动兼容规则

- `--platform auto`：根据当前系统选择 Windows 或 macOS；这是默认值。
- macOS 自动使用 `draft_info.json`。
- Windows 自动读取最近的本机有效草稿：存在 `draft_info.json` 时使用当前格式，只有 `draft_content.json` 时使用旧格式；没有样本时保持原项目的旧版默认。
- 可用 `--draft-format modern` 或 `--draft-format legacy` 显式覆盖。
- 未传 `--drafts-dir` 时使用当前系统默认目录；剪映自定义过目录时必须显式传入。

## 创建命令

```bash
python3 scripts/create_jianying_draft.py \
  --package-dir /absolute/path/to/outputs/city-date-slug \
  --title "城市夜读｜标题"
```

默认不覆盖同名草稿。只有用户明确要求替换时才添加 `--replace`。

## 验证

1. 检查草稿目录包含 `draft_meta_info.json`，并按格式包含 `draft_info.json` 或 `draft_content.json`。
2. 检查入口文件的 `duration`、`canvas_config`、轨道名称和片段数量。
3. 确认视频素材路径都位于当前草稿的 `assets/`，且文件存在。
4. 本机安装剪映时，必须打开草稿进入时间线；首页出现标题不能证明草稿有效。
5. 点击一个画面片段，确认预览区出现图片，且没有“草稿已损坏”“暂无访问权限”或“链接媒体”提示。
6. 告知用户只需在01轨执行文本朗读，并在03轨添加授权BGM。
