# Music Plan

- Model: music-2.5
- Mode: instrumental-score
- Vocal policy: no-vocals
- Goal: 为云海邮差三段短片规划一条轻冒险、可爱、电影级的连续配乐。
- Duration strategy: 先生成一条略长的纯配乐，再按最终无声 preview 时长裁切并保留尾部淡出。
- Target video duration: 18.0s
- Overall arc: 第一段建立晨曦云海世界与出发感，第二段明显推进追逐张力，第三段转为温暖发光的送达收束。
- Palette: 轻盈木管、柔和弦乐、微弱钟琴、温暖竖琴点缀、少量推进性打击，不做人声，不做流行副歌。

## Cue Sheet

### shot-01 — Morning Route

- Start: 0.0s
- End: 6.0s
- Story function: setup
- Music function: 晨曦世界建立与出发感
- Energy: 低到中

### shot-02 — Catch the Star

- Start: 6.0s
- End: 12.0s
- Story function: escalation
- Music function: 轻冒险推进与追逐兴奋
- Energy: 中

### shot-03 — First Delivery Light

- Start: 12.0s
- End: 18.0s
- Story function: payoff
- Music function: 温暖发光的送达收束
- Energy: 中到低

## Chinese Music Prompt

无歌词、无人声、纯电影配乐。为一条晨曦云海邮差三段式动漫短片创作连续背景音乐。第一段要有轻盈出发感、梦幻天空感和清晨苏醒感；第二段加入更明确但不过分激烈的推进节奏，表现见习少女邮差追逐逃跑星屑包裹的轻冒险兴奋；第三段转为温暖、发光、带一点释然与成就感的收束。整体要像高质量动画电影配乐，柔和自然，不要流行歌曲结构，不要主唱，不要电子舞曲感。

## English Music Prompt

Instrumental only, no vocals, no singing. Compose a cinematic animation-style score for a three-shot sunrise cloud-mail story. Shot one should feel airy, hopeful, and softly wondrous as the cloud-rail world wakes up. Shot two should add clear forward momentum and playful adventure as a trainee postgirl chases a runaway starlight parcel. Shot three should resolve into warm glowing delivery payoff and gentle accomplishment. Use refined film-score orchestration with light woodwinds, soft strings, subtle bells, and restrained rhythmic lift. Avoid pop-song structure, avoid lead vocals, avoid EDM energy.

## Mix Plan

- Music volume: 0.26
- Fade in: 0.9s
- Fade out: 1.8s
- Loop strategy: loop_if_short_trim_if_long
- Trim to video: true
