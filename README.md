# MiniMax Hailuo Cinematic Director

一个面向 `MiniMax-Hailuo-2.3` 的电影级三段式视频导演型 Skill，版本见 [VERSION](VERSION)。

它的目标不是简单调 API，而是把整条链路固化成可复用流程：

- 先做三段式故事规划
- 再做分镜与提示词审核
- 再生成视频
- 再做成片复盘
- 需要时再补 MiniMax 配乐、混音与音画适配复盘

## 项目亮点

- 三段式电影叙事 `story package` 规划
- 强制“连续但不重复”的镜头差异约束
- 中文审核摘要与中文成片复盘
- MiniMax `music-2.5` 配乐规划、审核、生成与混音
- 默认保留无声版，同时单独导出带配乐版
- 精选案例可直接在仓库中查看和下载

## 精选案例

### Storm Lighthouse Rescue

![Storm Lighthouse Rescue](examples/storm-lighthouse-rescue-20260405/cover.jpg)

- 带配乐成片：[final-with-music.mp4](examples/storm-lighthouse-rescue-20260405/final-with-music.mp4)
- 分镜：[storyboard.md](examples/storm-lighthouse-rescue-20260405/storyboard.md)
- 提示词：[prompts.md](examples/storm-lighthouse-rescue-20260405/prompts.md)
- 配乐规划：[music-plan.md](examples/storm-lighthouse-rescue-20260405/music-plan.md)
- 视频审核：[audit-summary.md](examples/storm-lighthouse-rescue-20260405/audit-summary.md)
- 配乐审核：[soundtrack-audit-summary.md](examples/storm-lighthouse-rescue-20260405/soundtrack-audit-summary.md)
- 音画复盘：[soundtrack-review-summary.md](examples/storm-lighthouse-rescue-20260405/soundtrack-review-summary.md)

### Iceland Continuation

![Iceland Continuation](examples/iceland-continuation-20260404/cover.jpg)

- 无声预览片：[sequence-preview.mp4](examples/iceland-continuation-20260404/sequence-preview.mp4)
- 分镜：[storyboard.md](examples/iceland-continuation-20260404/storyboard.md)
- 提示词：[prompts.md](examples/iceland-continuation-20260404/prompts.md)
- 规划审核：[audit-summary.md](examples/iceland-continuation-20260404/audit-summary.md)
- 成片复盘：[review-summary.md](examples/iceland-continuation-20260404/review-summary.md)

## 核心流程

1. 用 `plan_story_package.py` 生成三段式故事包。
2. 用 `audit_story_package.py` 审核故事、连续性、镜头差异和提示词质量。
3. 用 `run_story_sequence.py` 生成视频并自动跑成片复盘。
4. 需要音乐时，用 `run_soundtrack_pipeline.py` 做配乐审核、音乐生成、混音和音画适配复盘。

## 目录结构

- `SKILL.md`
  Skill 主说明
- `scripts/`
  规划、审核、生成、复盘、配乐、混音脚本
- `references/`
  镜头语言、连续性、配乐经验文档
- `assets/`
  预设 brief 与模板
- `examples/`
  精选示例与最终演示成片
- `output/`
  运行时产物目录，默认不纳入版本控制

## 环境要求

- Python 3
- `ffmpeg` / `ffprobe`
- MiniMax API key，通过环境变量提供

支持的环境变量：

- `MINIMAX_API_KEY`
- `MINIMAX_API_KEY_MAX`
- `MINIMAX_API_KEY_PRO`
- 可选：`MINIMAX_BASE_URL`

不要把密钥写进仓库。

## 快速开始

```bash
python3 scripts/plan_story_package.py \
  --preset storm-lighthouse-rescue \
  --output-dir output/runs/storm-lighthouse-rescue

python3 scripts/audit_story_package.py \
  --story-package output/runs/storm-lighthouse-rescue/story-package.json \
  --report output/runs/storm-lighthouse-rescue/audit-report.json \
  --markdown output/runs/storm-lighthouse-rescue/audit-summary.md

python3 scripts/run_story_sequence.py \
  --story-package output/runs/storm-lighthouse-rescue/story-package.json \
  --output-dir output/runs/storm-lighthouse-rescue/generated \
  --execute \
  --with-soundtrack
```

如果只想在已有无声预览片基础上补配乐：

```bash
python3 scripts/run_soundtrack_pipeline.py \
  --story-package output/runs/storm-lighthouse-rescue/story-package.json \
  --sequence-preview output/runs/storm-lighthouse-rescue/review/sequence-preview.mp4 \
  --output-dir output/runs/storm-lighthouse-rescue/soundtrack \
  --execute
```

## 版本管理

- 当前版本：`0.1.0`
- 版本变更记录见 [CHANGELOG.md](CHANGELOG.md)
- 推荐使用语义化版本 tag，如 `v0.1.0`

## GitHub 收录策略

- 上传可复用脚本、说明、参考资料
- 不上传 `output/` 下的中间产物
- 不上传任何 API key、`.env`、下载签名或临时缓存
- 精选示例放在 `examples/`，只保留可交付 demo 与摘要
