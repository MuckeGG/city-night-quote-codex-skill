# 剪映草稿生成规范

## 实现原则

- 使用 `pyJianYingDraft==0.3.0` 直接生成草稿文件，不通过剪映界面逐张导入或手工排列。
- 草稿为1080×1920竖屏，图片按 `timeline.json` 的时间点放置。
- 相邻且 `shot_id` 相同的字幕条目合并为一个画面段；字幕仍逐条保留。
- 画面默认添加1.00到1.04的缓慢推近；时间轴标注横移时添加轻微水平关键帧。
- 连续旁白作为一条不可见文本片段放在 `01 连续旁白（请在本轨执行文本朗读）`。
- 屏幕字幕放在 `02 屏幕字幕（不要在本轨配音）`。
- 建立空的 `03 舒缓BGM（请在剪映添加）` 音频轨，不自动下载或添加未经授权音乐。

## 依赖

先检查固定版本：

```bash
python3 -c "import pyJianYingDraft"
```

缺失时安装到临时或用户可写目录，并通过 `PYTHONPATH` 调用：

```bash
python3 -m pip install --target /tmp/city-night-draft-deps pyJianYingDraft==0.3.0
```

不要升级到未验证版本后直接生成草稿。

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

## 创建命令

```bash
PYTHONPATH=/tmp/city-night-draft-deps python3 scripts/create_jianying_draft.py \
  --package-dir /absolute/path/to/outputs/city-date-slug \
  --drafts-dir "/absolute/path/to/com.lveditor.draft" \
  --title "城市夜读｜标题"
```

默认不覆盖同名草稿。只有用户明确要求替换时才添加 `--replace`。

## 验证

1. 检查草稿目录包含 `draft_content.json` 和 `draft_meta_info.json`。
2. 检查 `draft_content.json` 的 `duration`、`canvas_config`、轨道名称和片段数量。
3. 本机安装剪映时，确认首页出现指定草稿标题即可。无需打开草稿逐轨手工编辑。
4. 告知用户只需进入草稿，在01轨执行文本朗读，并在03轨添加授权BGM。
