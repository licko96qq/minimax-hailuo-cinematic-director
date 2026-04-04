# Soundtrack Playbook

## 目标

把三段式 Hailuo 视频从“无声审片预览”升级为“带配乐成片”，同时保持：

- 原无声版不被覆盖
- 配乐先审核再生成
- 音乐生成与混音可重复执行
- 每次经验都能回写进 skill 与交接文档

## 当前已验证策略

### 1. MiniMax 音乐接口需要 `lyrics`

实测结论：

- `POST /v1/music_generation` 在当前环境下会报：
  `invalid params, lyrics is required`
- 因此，不能只传 `prompt`

### 2. 纯配乐最佳兼容策略

当前最稳妥的做法不是传真实歌词，而是传“结构占位歌词”：

```text
[Intro]
 
[Development]
 
[Outro]
```

配合强约束 prompt：

- 无歌词
- 无人声
- 不要主唱
- 不要吟唱
- 电影配乐

这样既满足接口要求，也尽量把结果压向纯背景音乐。

## 工作流

1. `plan_story_package.py`
   产出 `music_plan` 和 `music-plan.md`
2. `audit_soundtrack_plan.py`
   先审核叙事契合度、时长结构、生成可行性、混音可行性
3. `generate_minimax_music.py`
   调用 MiniMax 音乐生成
4. `mix_sequence_soundtrack.py`
   把音乐混入无声预览片，输出新的带配乐版
5. `review_soundtrack_fit.py`
   复盘音画适配是否可交付

## 输出约定

- 无声预览片保留在：
  `review/sequence-preview.mp4`
- 带配乐成片单独输出到：
  `soundtrack/final-with-music.mp4`

不要覆盖无声审片版。

## 审核标准

### 配乐审核

- 叙事契合度
- 时间结构契合度
- 生成可行性
- 混音可行性

### 音画复盘

- 叙事契合度
- 时长契合度
- 交付完整性
- 风险信号

## 混音经验

- 默认音乐音量：`0.27 ~ 0.30`
- 默认淡入：`0.7 ~ 0.9s`
- 默认淡出：`1.5 ~ 1.7s`
- 默认策略：
  音乐短则循环，音乐长则裁切到视频长度

## 版本管理要求

- 所有新能力必须同时更新：
  - `SKILL.md`
  - 交接手册
  - 对应脚本
  - 至少一个真实 run 的产物
- 修改后同步一份到：
  `~/.codex/skills/minimax-hailuo-cinematic-director/`
