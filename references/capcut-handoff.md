# 剪映交接规范

## 导入顺序

1. 新建9:16项目，按 `timeline.csv` 导入 `assets/shot-XX.png`。
2. 设置每张图片的时长；需要运动感时使用剪映的轻微推近、横移或关键帧。
3. 将 `narration.txt` 作为一整段文本，在剪映中完成文本朗读。不要按每条短字幕分别朗读，避免断气和音色跳变。
4. 优先对完整旁白音频执行剪映“识别字幕/歌词”，让字幕时间来自真实配音；`subtitles.srt` 仅作为文字核对和应急导入文件。
5. 添加剪映内可商用或平台授权BGM；BGM低于旁白，不覆盖人声。
6. 在开头或发布设置中添加AI生成标识，并保留来源说明。

## 推荐精确校准

直接读取朗读首稿的单条音频并建立真实时长时间轴：

```bash
python3 scripts/align_jianying_voice.py \
  --package-dir /absolute/path/to/content-package \
  --source-draft /absolute/path/to/voice-draft
```

脚本会拒绝多个 `textReading` 文件，因为那代表短字幕被逐条朗读。最终字幕由剪映从完整旁白音频识别生成；Codex 的初版SRT不再冒充精确字幕。
