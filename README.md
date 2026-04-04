# MiniMax Hailuo Cinematic Director

一个面向 `MiniMax-Hailuo-2.3` 的电影级三段式视频导演型 Skill。

它的目标不是简单调 API，而是把这条链路固化成可复用流程：

- 先做三段式故事规划
- 再做分镜与提示词审核
- 再生成视频
- 再做成片复盘
- 需要时再补 MiniMax 配乐、混音与音画适配复盘

## 当前能力

- 三段式电影叙事 story package 规划
- 连续但不重复的镜头设计
- 中文审核摘要
- 生成后镜头差异复盘
- MiniMax `music-2.5` 配乐规划与审核
- 保留无声版，同时单独导出带配乐成片

## 目录

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

`output/` 是运行时产物目录，默认不纳入版本控制。

## 环境变量

通过环境变量提供 MiniMax 鉴权，不要把密钥写进仓库：

- `MINIMAX_API_KEY`
- `MINIMAX_API_KEY_MAX`
- `MINIMAX_API_KEY_PRO`
- 可选：`MINIMAX_BASE_URL`

## 典型流程

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

## GitHub 收录策略

- 上传可复用脚本、说明、参考资料
- 不上传 `output/` 下的中间产物
- 不上传任何 API key、`.env`、下载签名或临时缓存
- 精选示例放在 `examples/`，只保留最新可交付 demo 与摘要

## 当前精选示例

- 风暴灯塔三段式带配乐成片：
  `examples/storm-lighthouse-rescue-20260405/final-with-music.mp4`

