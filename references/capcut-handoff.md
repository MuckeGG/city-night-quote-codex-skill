# 剪映交接规范

## 导入顺序

1. 新建9:16项目，按 `timeline.csv` 导入 `assets/shot-XX.png`。
2. 设置每张图片的时长；需要运动感时使用剪映的轻微推近、横移或关键帧。
3. 将 `narration.txt` 作为一整段文本，在剪映中完成文本朗读。不要按每条短字幕分别朗读，避免断气和音色跳变。
4. 导入 `subtitles.srt`，根据真实配音做最后一次人工校准。
5. 添加剪映内可商用或平台授权BGM；BGM低于旁白，不覆盖人声。
6. 在开头或发布设置中添加AI生成标识，并保留来源说明。

## 可选精确校准

若用户能从剪映导出旁白音频并取得分段时间，可建立：

```json
[
  {"id": 1, "start": 0.0, "end": 3.8, "text": "完整旁白片段"}
]
```

保存为 `timings.json` 后运行：

```bash
python3 scripts/build_subtitles.py \
  --input narration.txt \
  --output-dir . \
  --timings timings.json
```

这会用真实时间替换估算时间，重新输出精确SRT和图片时间轴。没有真实时间时，使用目标时长和字数比例生成初版，不声称已经完成音频级校准。
