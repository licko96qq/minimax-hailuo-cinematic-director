# Changelog

## Unreleased

- 固化 `MiniMax-Hailuo-2.3` 与 `MiniMax-Hailuo-2.3-Fast` 双模式说明，不再把 `Fast` 误当作普通 `t2v`
- 新增 `cloud-postgirl-runaway-star` 与 `cloud-postgirl-runaway-star-fast` 预设资产
- 新增 `generate_minimax_images.py`，支持 `Fast` 模式先批量产出 anchor still 候选
- 新增 `run_soundtrack_candidates.py`，支持多候选配乐的自动审核、混音、复盘、选优和提升
- `generate_hailuo_video.py` / `minimax_common.py` 现按真实文件头识别首帧图 MIME，规避“JPEG 内容误存为 .png”导致的 Fast 首帧上传失败
- README 补充 `Fast` anchor workflow、多候选配乐和未来 roadmap
- 新增 `examples/cloud-postgirl-runaway-star-fast-20260405`，正式收录云端邮差 Fast 案例、成片、预览、审核与配乐候选结果

## v0.1.0 - 2026-04-05

- 新增三段式视频规划、审核、生成、复盘完整链路
- 新增中文审核摘要与中文成片复盘
- 新增 `storm-lighthouse-rescue` 三段式示例
- 新增 `iceland-continuation` 精选示例目录
- 新增 MiniMax 配乐规划、配乐审核、音乐生成、混音成片、音画适配复盘
- 固化“保留无声版，单独导出带配乐版”的交付规则
- 固化 MiniMax 音乐接口需要 `lyrics` 时的“结构占位歌词”兼容策略
- 新增 GitHub 友好的 README、精选案例目录和版本文件
