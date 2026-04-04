# Music Plan

- Model: music-2.5
- Mode: instrumental-score
- Vocal policy: no-vocals
- Goal: 为暴风灯塔救援三段短片生成一条连续的电影悬疑配乐。
- Duration strategy: 先生成一条较长纯配乐，再按最终成片长度裁切并混音。
- Target video duration: 18.0s
- Overall arc: 从风暴危险建立，到海上搏斗升级，再到接近安全的脆弱收束。
- Palette: 低沉弦乐、稀疏铜管、紧张脉冲、冷感音垫，结尾带微弱暖色和弦，但不彻底明亮。

## Cue Sheet

### shot-01 — The Beacon

- Start: 0.0s
- End: 6.0s
- Story function: setup
- Music function: 风暴与目标建立
- Energy: 低到中

### shot-02 — Through the Breakers

- Start: 6.0s
- End: 12.0s
- Story function: escalation
- Music function: 张力推进与海上搏斗
- Energy: 中到高

### shot-03 — At the Edge of Safety

- Start: 12.0s
- End: 18.0s
- Story function: payoff
- Music function: 脆弱安全感与情绪收束
- Energy: 中到低

## Chinese Music Prompt

无歌词、无人声、纯电影配乐。为一条暴风海岸灯塔救援三段式短片创作连续背景音乐。第一段建立危险海况和远处灯塔目标，用低沉、压迫、带海雾感的电影配乐质感；第二段明显加强推进与搏斗感，可以有更清晰的节奏脉冲与弦乐驱动，表现救援船冲破浪头；第三段不要继续冲锋，而是转为接近安全后的脆弱收束，保留风雨余波与一点温暖希望。整体必须像电影配乐，不要流行歌曲，不要主唱，不要人声吟唱，不要广告片节奏。

## English Music Prompt

Instrumental only, no vocals, no singing. Compose a cinematic suspense-rescue score for a three-shot storm lighthouse sequence. Shot one establishes danger, distance, and the beacon through low strings, cold atmosphere, and restrained pressure. Shot two increases propulsion with stronger pulse and maritime struggle. Shot three shifts into fragile relief and hard-won safety while preserving storm residue and a faint warm harmonic lift. Feature-film underscore, not a pop song, not trailer braam spam, not commercial ad music.

## Mix Plan

- Music volume: 0.3
- Fade in: 0.7s
- Fade out: 1.7s
- Loop strategy: loop_if_short_trim_if_long
- Trim to video: true
