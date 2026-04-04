#!/usr/bin/env python3

import argparse
import datetime as dt
import json
import pathlib

from minimax_common import read_json, slugify, write_json, write_text


def shot_dict(
    shot_id,
    title,
    dramatic_purpose,
    story_beat,
    primary_subject,
    new_information,
    camera_height,
    framing,
    camera_movement,
    continuity_anchors,
    difference_axes,
    must_not_repeat,
    prompt_zh,
    prompt_en,
    model,
    duration,
    resolution,
    prompt_optimizer,
    input_mode="t2v",
    first_frame_image=None,
    anchor_from=None,
    frame_position=None,
    frame_offset_seconds=None,
    status=None,
    video_path=None,
    tags=None,
):
    payload = {
        "shot_id": shot_id,
        "title": title,
        "dramatic_purpose": dramatic_purpose,
        "story_beat": story_beat,
        "primary_subject": primary_subject,
        "new_information": new_information,
        "camera_height": camera_height,
        "framing": framing,
        "camera_movement": camera_movement,
        "continuity_anchors": continuity_anchors,
        "difference_axes": difference_axes,
        "must_not_repeat": must_not_repeat,
        "prompt_zh": prompt_zh,
        "prompt_en": prompt_en,
        "model": model,
        "duration": duration,
        "resolution": resolution,
        "prompt_optimizer": prompt_optimizer,
        "tags": tags or [],
    }
    if input_mode:
        payload["input_mode"] = input_mode
    if first_frame_image:
        payload["first_frame_image"] = first_frame_image
    if anchor_from:
        payload["anchor_from"] = anchor_from
    if frame_position:
        payload["frame_position"] = frame_position
    if frame_offset_seconds is not None:
        payload["frame_offset_seconds"] = frame_offset_seconds
    if status:
        payload["status"] = status
    if video_path:
        payload["video_path"] = video_path
    return payload


def total_duration_seconds(shots):
    return round(
        sum(float(shot.get("duration", 0) or 0) for shot in shots),
        3,
    )


def instrumental_placeholder_lyrics():
    return "[Intro]\n \n[Development]\n \n[Outro]\n "


def generic_music_plan(topic, shots):
    total_duration = total_duration_seconds(shots)
    return {
        "model": "music-2.5",
        "mode": "instrumental-score",
        "vocal_policy": "no-vocals",
        "goal": "为三段式短片生成一条连续的电影配乐，并在后期按成片时长裁切。",
        "duration_strategy": "先生成一条较长音乐，再按最终视频时长裁切并淡出。",
        "target_video_duration_seconds": total_duration,
        "overall_arc": "第一段建立氛围，第二段推动张力，第三段做情绪收束。",
        "palette": "电影配乐质感，控制层次与动态，不做人声主唱，不做流行歌曲结构。",
        "prompt_zh": (
            f"无歌词、无人声、纯电影配乐。围绕“{topic}”创作一条适合三段式短片的连续背景音乐。"
            "第一段建立世界和氛围，第二段明显提升张力与推进感，第三段转向收束、回望或情绪落点。"
            "要求电影级质感、层次清晰、可用于高质感短片，不要流行歌唱，不要主唱，不要口语采样。"
        ),
        "prompt_en": (
            f"Instrumental only, no vocals, no singing. Compose a cinematic underscore for a three-shot short film about {topic}. "
            "Structure the cue as setup, escalation, and payoff. Keep it filmic, emotionally legible, and suitable for trimming under a short sequence. "
            "Avoid pop-song structure, avoid lead vocals, avoid obvious commercial jingle energy."
        ),
        "lyrics": instrumental_placeholder_lyrics(),
        "cue_sheet": [
            {
                "shot_id": shot["shot_id"],
                "title": shot["title"],
                "start_seconds": round(index * float(shot.get("duration", 0) or 0), 3),
                "end_seconds": round((index + 1) * float(shot.get("duration", 0) or 0), 3),
                "story_function": shot["dramatic_purpose"],
                "music_function": {
                    "shot-01": "氛围建立",
                    "shot-02": "张力推进",
                    "shot-03": "情绪收束",
                }.get(shot["shot_id"], "叙事承接"),
                "energy": {
                    "shot-01": "低到中",
                    "shot-02": "中到高",
                    "shot-03": "中到低",
                }.get(shot["shot_id"], "中"),
            }
            for index, shot in enumerate(shots)
        ],
        "mix_plan": {
            "music_volume": 0.28,
            "fade_in_seconds": 0.8,
            "fade_out_seconds": 1.5,
            "loop_strategy": "loop_if_short_trim_if_long",
            "trim_to_video": True,
        },
        "audit_targets": {
            "required_total_score": 80,
            "required_narrative_fit": 22,
            "required_mix_feasibility": 16,
        },
    }


def iceland_music_plan(shots):
    total_duration = total_duration_seconds(shots)
    return {
        "model": "music-2.5",
        "mode": "instrumental-score",
        "vocal_policy": "no-vocals",
        "goal": "为冰岛冰川河流三段短片生成一条自然史诗感的连续配乐。",
        "duration_strategy": "先生成一条较长纯配乐，再按最终三段拼接时长裁切。",
        "target_video_duration_seconds": total_duration,
        "overall_arc": "从敬畏的自然建立，进入发现线索，再落到人与地貌关系的情绪收束。",
        "palette": "冷感弦乐、空气质感、极简脉冲、微弱低频，不要人声，不要流行主旋律。",
        "prompt_zh": (
            "无歌词、无人声、纯电影配乐。为一条冰岛冰川河流三段式短片创作自然史诗感背景音乐。"
            "开头要有冰冷、广阔、敬畏感；中段加入轻微脉冲和更明确的推进，表现发现人类痕迹的时刻；"
            "结尾转为克制、孤独、带一点希望的收束。整体像国家地理纪录片与电影配乐之间的质感，"
            "不要流行歌曲，不要主唱，不要过度煽情。"
        ),
        "prompt_en": (
            "Instrumental only, no vocals, no singing. Compose a cinematic natural-history score for an Iceland glacier-river three-shot sequence. "
            "Begin with cold awe and open landscape scale, add subtle pulse and narrative tension in the middle as evidence of passage is discovered, "
            "then resolve into restrained solitude and witness-scale payoff. Premium documentary-meets-feature-film tone, no pop-song structure."
        ),
        "lyrics": instrumental_placeholder_lyrics(),
        "cue_sheet": [
            {
                "shot_id": "shot-01",
                "title": "The River",
                "start_seconds": 0.0,
                "end_seconds": round(float(shots[0].get("duration", 0) or 0), 3),
                "story_function": "setup",
                "music_function": "广阔自然建立",
                "energy": "低到中",
            },
            {
                "shot_id": "shot-02",
                "title": "Evidence of Passage",
                "start_seconds": round(float(shots[0].get("duration", 0) or 0), 3),
                "end_seconds": round(float(shots[0].get("duration", 0) or 0) + float(shots[1].get("duration", 0) or 0), 3),
                "story_function": "escalation",
                "music_function": "轻微张力推进",
                "energy": "中",
            },
            {
                "shot_id": "shot-03",
                "title": "Witness at the Edge",
                "start_seconds": round(total_duration - float(shots[2].get("duration", 0) or 0), 3),
                "end_seconds": total_duration,
                "story_function": "payoff",
                "music_function": "克制收束",
                "energy": "中到低",
            },
        ],
        "mix_plan": {
            "music_volume": 0.27,
            "fade_in_seconds": 0.9,
            "fade_out_seconds": 1.6,
            "loop_strategy": "loop_if_short_trim_if_long",
            "trim_to_video": True,
        },
        "audit_targets": {
            "required_total_score": 80,
            "required_narrative_fit": 22,
            "required_mix_feasibility": 16,
        },
    }


def lighthouse_music_plan(shots):
    total_duration = total_duration_seconds(shots)
    shot_duration = float(shots[0].get("duration", 0) or 0)
    return {
        "model": "music-2.5",
        "mode": "instrumental-score",
        "vocal_policy": "no-vocals",
        "goal": "为暴风灯塔救援三段短片生成一条连续的电影悬疑配乐。",
        "duration_strategy": "先生成一条较长纯配乐，再按最终成片长度裁切并混音。",
        "target_video_duration_seconds": total_duration,
        "overall_arc": "从风暴危险建立，到海上搏斗升级，再到接近安全的脆弱收束。",
        "palette": "低沉弦乐、稀疏铜管、紧张脉冲、冷感音垫，结尾带微弱暖色和弦，但不彻底明亮。",
        "prompt_zh": (
            "无歌词、无人声、纯电影配乐。为一条暴风海岸灯塔救援三段式短片创作连续背景音乐。"
            "第一段建立危险海况和远处灯塔目标，用低沉、压迫、带海雾感的电影配乐质感；"
            "第二段明显加强推进与搏斗感，可以有更清晰的节奏脉冲与弦乐驱动，表现救援船冲破浪头；"
            "第三段不要继续冲锋，而是转为接近安全后的脆弱收束，保留风雨余波与一点温暖希望。"
            "整体必须像电影配乐，不要流行歌曲，不要主唱，不要人声吟唱，不要广告片节奏。"
        ),
        "prompt_en": (
            "Instrumental only, no vocals, no singing. Compose a cinematic suspense-rescue score for a three-shot storm lighthouse sequence. "
            "Shot one establishes danger, distance, and the beacon through low strings, cold atmosphere, and restrained pressure. "
            "Shot two increases propulsion with stronger pulse and maritime struggle. "
            "Shot three shifts into fragile relief and hard-won safety while preserving storm residue and a faint warm harmonic lift. "
            "Feature-film underscore, not a pop song, not trailer braam spam, not commercial ad music."
        ),
        "lyrics": instrumental_placeholder_lyrics(),
        "cue_sheet": [
            {
                "shot_id": "shot-01",
                "title": "The Beacon",
                "start_seconds": 0.0,
                "end_seconds": round(shot_duration, 3),
                "story_function": "setup",
                "music_function": "风暴与目标建立",
                "energy": "低到中",
            },
            {
                "shot_id": "shot-02",
                "title": "Through the Breakers",
                "start_seconds": round(shot_duration, 3),
                "end_seconds": round(shot_duration * 2, 3),
                "story_function": "escalation",
                "music_function": "张力推进与海上搏斗",
                "energy": "中到高",
            },
            {
                "shot_id": "shot-03",
                "title": "At the Edge of Safety",
                "start_seconds": round(shot_duration * 2, 3),
                "end_seconds": total_duration,
                "story_function": "payoff",
                "music_function": "脆弱安全感与情绪收束",
                "energy": "中到低",
            },
        ],
        "mix_plan": {
            "music_volume": 0.3,
            "fade_in_seconds": 0.7,
            "fade_out_seconds": 1.7,
            "loop_strategy": "loop_if_short_trim_if_long",
            "trim_to_video": True,
        },
        "audit_targets": {
            "required_total_score": 80,
            "required_narrative_fit": 22,
            "required_mix_feasibility": 16,
        },
    }


def cloud_postgirl_music_plan(shots):
    total_duration = total_duration_seconds(shots)
    shot_duration = float(shots[0].get("duration", 0) or 0)
    return {
        "model": "music-2.5",
        "mode": "instrumental-score",
        "vocal_policy": "no-vocals",
        "goal": "为云海邮差三段短片规划一条轻冒险、可爱、电影级的连续配乐。",
        "duration_strategy": "先生成一条略长的纯配乐，再按最终无声 preview 时长裁切并保留尾部淡出。",
        "target_video_duration_seconds": total_duration,
        "overall_arc": "第一段建立晨曦云海世界与出发感，第二段明显推进追逐张力，第三段转为温暖发光的送达收束。",
        "palette": "轻盈木管、柔和弦乐、微弱钟琴、温暖竖琴点缀、少量推进性打击，不做人声，不做流行副歌。",
        "prompt_zh": (
            "无歌词、无人声、纯电影配乐。为一条晨曦云海邮差三段式动漫短片创作连续背景音乐。"
            "第一段要有轻盈出发感、梦幻天空感和清晨苏醒感；第二段加入更明确但不过分激烈的推进节奏，"
            "表现见习少女邮差追逐逃跑星屑包裹的轻冒险兴奋；第三段转为温暖、发光、带一点释然与成就感的收束。"
            "整体要像高质量动画电影配乐，柔和自然，不要流行歌曲结构，不要主唱，不要电子舞曲感。"
        ),
        "prompt_en": (
            "Instrumental only, no vocals, no singing. Compose a cinematic animation-style score for a three-shot sunrise cloud-mail story. "
            "Shot one should feel airy, hopeful, and softly wondrous as the cloud-rail world wakes up. "
            "Shot two should add clear forward momentum and playful adventure as a trainee postgirl chases a runaway starlight parcel. "
            "Shot three should resolve into warm glowing delivery payoff and gentle accomplishment. "
            "Use refined film-score orchestration with light woodwinds, soft strings, subtle bells, and restrained rhythmic lift. "
            "Avoid pop-song structure, avoid lead vocals, avoid EDM energy."
        ),
        "lyrics": instrumental_placeholder_lyrics(),
        "cue_sheet": [
            {
                "shot_id": "shot-01",
                "title": "Morning Route",
                "start_seconds": 0.0,
                "end_seconds": round(shot_duration, 3),
                "story_function": "setup",
                "music_function": "晨曦世界建立与出发感",
                "energy": "低到中",
            },
            {
                "shot_id": "shot-02",
                "title": "Catch the Star",
                "start_seconds": round(shot_duration, 3),
                "end_seconds": round(shot_duration * 2, 3),
                "story_function": "escalation",
                "music_function": "轻冒险推进与追逐兴奋",
                "energy": "中",
            },
            {
                "shot_id": "shot-03",
                "title": "First Delivery Light",
                "start_seconds": round(shot_duration * 2, 3),
                "end_seconds": total_duration,
                "story_function": "payoff",
                "music_function": "温暖发光的送达收束",
                "energy": "中到低",
            },
        ],
        "mix_plan": {
            "music_volume": 0.26,
            "fade_in_seconds": 0.9,
            "fade_out_seconds": 1.8,
            "loop_strategy": "loop_if_short_trim_if_long",
            "trim_to_video": True,
        },
        "audit_targets": {
            "required_total_score": 80,
            "required_narrative_fit": 22,
            "required_mix_feasibility": 16,
        },
    }


def build_generic_package(args):
    topic = args.topic.strip()
    project_slug = slugify(topic)
    defaults = {
        "model": args.model,
        "duration": args.duration,
        "resolution": args.resolution,
        "prompt_optimizer": args.prompt_optimizer,
    }

    continuity_spine = {
        "world": f"The same cinematic world built around {topic}.",
        "light": "Maintain one coherent light logic and time-of-day feel.",
        "emotion": "Escalate toward a clear emotional payoff instead of repeating a mood board.",
        "cause_effect": "Each shot should reveal new information caused by the previous shot.",
    }

    shots = []
    if args.existing_shot_video:
        shots.append(
            shot_dict(
                "shot-01",
                "Existing Shot",
                "setup",
                "world-establishment",
                "the existing cinematic opening image",
                "the world is already established by the provided clip",
                "locked-from-reference",
                "existing",
                "locked",
                ["existing opening clip"],
                ["reference clip"],
                [],
                "沿用用户提供的开场镜头作为既定第一段。",
                "Existing reference shot carried forward as the locked opening shot.",
                args.model,
                args.duration,
                args.resolution,
                args.prompt_optimizer,
                input_mode=None,
                status="existing",
                video_path=str(pathlib.Path(args.existing_shot_video).resolve()),
                tags=[project_slug, "setup", "existing"],
            )
        )
        next_shots = [
            shot_dict(
                "shot-02",
                "Escalation",
                "escalation",
                "discovery",
                "a new clue or human trace inside the same world",
                "a concrete narrative clue appears",
                "low-to-mid",
                "medium-wide",
                "descending or lateral tracking",
                ["same geography", "same light logic", "same palette"],
                ["lower camera height", "tighter framing", "new story clue"],
                ["repeat the same establishing view", "stay purely scenic without a clue"],
                f"延续同一世界，但第二段必须更低、更近，并带出新的叙事线索，主题是{topic}。",
                f"A cinematic continuation of {topic}. Keep the same world, but move lower and closer into the dramatic center. Introduce a concrete new clue or human trace, use a tighter medium-wide composition, and make the second shot clearly different from the opening establishing image.",
                args.model,
                args.duration,
                args.resolution,
                args.prompt_optimizer,
                input_mode="i2v",
                anchor_from="shot-01",
                frame_position="end",
                frame_offset_seconds=0.12,
                tags=[project_slug, "escalation", "distinct"],
            ),
            shot_dict(
                "shot-03",
                "Payoff",
                "payoff",
                "revelation",
                "the emotional point of view or final meaning of the sequence",
                "a final revealing image with emotional closure",
                "very-high or ground-distant",
                "extreme-wide or witness composition",
                "lift reveal or restrained static witness shot",
                ["same world", "same light logic", "same emotional objective"],
                ["new composition", "new emotional function", "new subject emphasis"],
                ["repeat shot-02 framing", "remain in the same camera band as shot-02"],
                f"第三段必须是与第二段明显不同的收束镜头，主题仍然是{topic}，但镜头功能应转为情绪收束和意义揭示。",
                f"A cinematic payoff shot for {topic}. Stay in the same world and emotional chain, but switch to a clearly different final composition with a new cinematic function: reveal meaning, scale, or point of view. This shot must not look like another version of shot two. Use a new framing scale and a new emotional image.",
                args.model,
                args.duration,
                args.resolution,
                args.prompt_optimizer,
                input_mode="t2v",
                tags=[project_slug, "payoff", "distinct"],
            ),
        ]
    else:
        next_shots = [
            shot_dict(
                "shot-01",
                "Setup",
                "setup",
                "world-establishment",
                "the environment as the primary subject",
                "the viewer understands the world and visual promise",
                "high",
                "wide-establishing",
                "one clean opening move",
                ["world", "light", "emotional objective"],
                ["world setup"],
                [],
                f"第一段是{topic}的建立镜头，负责建立世界与尺度。",
                f"A cinematic setup shot for {topic}. Establish the world, scale, and visual promise with one clean opening move.",
                args.model,
                args.duration,
                args.resolution,
                args.prompt_optimizer,
                input_mode="t2v",
                tags=[project_slug, "setup"],
            ),
            shot_dict(
                "shot-02",
                "Escalation",
                "escalation",
                "discovery",
                "a more specific subject inside the world",
                "a new clue, threat, or trace appears",
                "mid or low",
                "medium-wide",
                "closer tracking or descent",
                ["same world", "same light", "same emotional objective"],
                ["lower camera height", "new subject emphasis", "new beat"],
                ["repeat the setup framing", "stay purely atmospheric"],
                f"第二段在{topic}的同一世界中推进故事，必须比第一段更具体、更靠近叙事中心。",
                f"A cinematic escalation shot for {topic}. Stay in the same world, but move lower or closer, introduce a concrete new clue, and make the second shot clearly different from the setup.",
                args.model,
                args.duration,
                args.resolution,
                args.prompt_optimizer,
                input_mode="t2v",
                tags=[project_slug, "escalation"],
            ),
            shot_dict(
                "shot-03",
                "Payoff",
                "payoff",
                "revelation",
                "the final emotional image",
                "the sequence resolves into a memorable cinematic conclusion",
                "very-high or ground-distant",
                "extreme-wide or witness",
                "revealing lift or calm payoff frame",
                ["same world", "same light", "same emotional objective"],
                ["new composition", "new emotional function", "payoff beat"],
                ["repeat shot-02 framing", "behave like another middle shot"],
                f"第三段是{topic}的真正收束镜头，必须比第二段更有结论感，并且视觉上明显不同。",
                f"A cinematic payoff shot for {topic}. End the three-shot sequence with a clearly different image and a conclusive emotional function. It must not look like another middle shot.",
                args.model,
                args.duration,
                args.resolution,
                args.prompt_optimizer,
                input_mode="t2v",
                tags=[project_slug, "payoff"],
            ),
        ]

    shots.extend(next_shots)

    package = {
        "project": project_slug,
        "topic": topic,
        "language": "zh-CN",
        "treatment": args.treatment,
        "defaults": defaults,
        "continuity_spine": continuity_spine,
        "audit_targets": {
            "required_total_score": 80,
            "required_distinctness_score": 24,
            "min_adjacent_difference_axes": 3,
        },
        "tags": [project_slug, "cinematic", "multi-shot", "hailuo-2.3"],
        "shots": shots,
    }
    package["music_plan"] = generic_music_plan(topic, shots)
    return package


def build_iceland_package(args):
    preset = read_json(pathlib.Path(__file__).resolve().parents[1] / "assets" / "iceland-continuation-brief.json")
    existing_video = str(pathlib.Path(args.existing_shot_video).resolve())
    defaults = preset["defaults"]
    package = {
        "project": preset["project"],
        "topic": preset["topic"],
        "language": "zh-CN",
        "treatment": preset["treatment"],
        "defaults": defaults,
        "continuity_spine": {
            "world": "The same Iceland glacier-river system, black sand, ice-blue water, and volcanic terrain.",
            "light": "The same cold early-morning sunlight and drifting mist.",
            "emotion": "A progression from awe to discovery to witness-scale payoff.",
            "cause_effect": "Shot 2 discovers evidence of passage. Shot 3 reveals who or what that evidence belongs to, without breaking realism.",
        },
        "audit_targets": {
            "required_total_score": 85,
            "required_distinctness_score": 26,
            "min_adjacent_difference_axes": 3,
        },
        "tags": preset["tags"],
        "shots": [
            shot_dict(
                "shot-01",
                "The River",
                "setup",
                "world-establishment",
                "the glacier river as a monumental living landscape",
                "the Icelandic world is established",
                "high-aerial",
                "wide-establishing",
                "forward aerial glide",
                ["black-sand river geometry", "ice-blue water", "dawn light", "mist"],
                ["existing reference shot"],
                [],
                "沿用已有的冰岛冰川河开场镜头。",
                "Existing reference shot carried forward as the locked opening image.",
                defaults["model"],
                defaults["duration"],
                defaults["resolution"],
                defaults["prompt_optimizer"],
                input_mode=None,
                status="existing",
                video_path=existing_video,
                tags=["iceland", "setup", "existing"],
            ),
            shot_dict(
                "shot-02",
                "Evidence of Passage",
                "escalation",
                "discovery",
                "human traces emerging inside the natural landscape",
                "the viewer discovers that someone has passed through this place",
                "low-aerial",
                "medium-wide tracking",
                "banking descent along the riverbank",
                ["same river system", "same dawn light", "same black sand", "same mist"],
                ["lower camera height", "tighter framing", "new human evidence", "sideways motion"],
                ["repeat the top-down river composition", "stay only as a scenic landscape shot"],
                "第二段必须明显不同于第一段：镜头压低并贴近黑沙河岸，从高空建立镜头进入更有叙事线索的中近距离跟拍。画面重点从宏观河流转到河岸上的轮胎印、临时信标、废弃勘察标记等人类经过痕迹，自然景观依旧主导，但故事开始发生。",
                "A cinematic continuation of the same Iceland glacier river world. This second shot must be clearly different from the opening aerial setup. Drop to a much lower altitude and track diagonally along the black-sand riverbank with a banking descent [推进]. The primary subject is no longer the full river geometry, but newly discovered traces of human passage inside the landscape: crisp tire marks pressed into wet volcanic sand, a small amber expedition beacon, and a weathered survey marker near the water. The river still rushes past in the frame, dawn light still glints across the ice, and mist moves through the canyon, but the narrative function is now discovery, not establishment. Photorealistic, premium natural-history cinematography, realistic motion, no fantasy elements.",
                defaults["model"],
                defaults["duration"],
                defaults["resolution"],
                defaults["prompt_optimizer"],
                input_mode="i2v",
                anchor_from="shot-01",
                frame_position="end",
                frame_offset_seconds=0.12,
                tags=["iceland", "escalation", "discovery", "human-trace", "distinct"],
            ),
            shot_dict(
                "shot-03",
                "Witness at the Edge",
                "payoff",
                "revelation",
                "an anonymous witness facing the full scale of the world",
                "the traces resolve into a tiny human presence and emotional meaning",
                "ground-ridge",
                "extreme-wide witness composition",
                "restrained hold with slight environmental motion",
                ["same Icelandic world", "same dawn light", "same black sand and glacier palette"],
                ["new subject emphasis", "new composition", "new emotional function", "switch away from anchor lock"],
                ["repeat shot-02 tracking angle", "look like another discovery shot"],
                "第三段不能再是第二段的变体。它必须变成一个明确的收束镜头：从远处黑沙山脊或海口附近的高地望向同一片冰川河世界，画面中第一次出现极小的匿名背影或停驻车辆，人物不露正脸，只作为尺度感和情绪锚点。这个镜头的任务不是继续找线索，而是让整段故事得到意义上的落点。",
                "A cinematic payoff shot in the same Iceland glacier-river world, but with a clearly different visual function from shot two. From a distant black-sand ridge above the river mouth and glacier plain, frame an extreme-wide witness composition. A tiny anonymous back-facing explorer or a parked expedition vehicle appears in the foreground as a scale anchor, never a visible face. The glacier river and surrounding volcanic landscape stretch outward into a broader final view, while the dawn light remains cold and coherent. This is no longer a discovery shot. It is the emotional payoff: awe, solitude, and the realization of human smallness against the landscape. Photorealistic, restrained, natural-history feature-film realism, premium composition, minimal but meaningful motion.",
                defaults["model"],
                defaults["duration"],
                defaults["resolution"],
                defaults["prompt_optimizer"],
                input_mode="t2v",
                tags=["iceland", "payoff", "witness", "anonymous-human", "distinct"],
            ),
        ],
    }
    package["music_plan"] = iceland_music_plan(package["shots"])
    return package


def build_lighthouse_package(args):
    preset = read_json(pathlib.Path(__file__).resolve().parents[1] / "assets" / "storm-lighthouse-rescue-brief.json")
    defaults = preset["defaults"]
    package = {
        "project": preset["project"],
        "topic": preset["topic"],
        "language": "zh-CN",
        "treatment": preset["treatment"],
        "defaults": defaults,
        "continuity_spine": {
            "world": "The same storm-lashed Atlantic-style rocky coast, isolated lighthouse, black sea, and rain-heavy sky.",
            "light": "The same blue-hour storm light, intermittent warm lighthouse beam, and cold wet reflections.",
            "emotion": "A progression from danger, to struggle, to hard-won refuge.",
            "cause_effect": "Shot 1 establishes the danger and the distant rescue target. Shot 2 shows the boat fighting toward the lighthouse. Shot 3 reveals arrival and emotional release at the edge of safety.",
        },
        "audit_targets": {
            "required_total_score": 85,
            "required_distinctness_score": 26,
            "min_adjacent_difference_axes": 3,
        },
        "tags": preset["tags"],
        "shots": [
            shot_dict(
                "shot-01",
                "The Beacon",
                "setup",
                "world-establishment",
                "an isolated lighthouse on a black rocky coast with a tiny rescue boat in the distance",
                "the viewer understands the storm, the destination, and the human scale of danger",
                "high-aerial",
                "wide-establishing",
                "slow aerial drift toward the lighthouse",
                ["same lighthouse", "same storm", "same blue-hour light", "same rescue boat"],
                ["world setup", "aerial scale"],
                [],
                "第一段是建立镜头：暴风中的海岸、孤立灯塔和远处极小的救援船构成完整世界。重点是危险、距离和尺度感，让观众知道这是一场必须到达灯塔的海上救援故事。",
                "A cinematic opening shot at stormy blue hour on a wild Atlantic-style rocky coast. A tall isolated lighthouse stands on black cliffs above violent dark water, its warm beam cutting through rain and sea mist. Far offshore, a tiny rescue boat fights through the storm toward the lighthouse, barely visible against the waves. The camera begins high above the coast and slowly drifts toward the beacon [推进], establishing danger, distance, and scale. Photorealistic, premium feature-film realism, dramatic wet textures, realistic waves and spray, no fantasy elements.",
                defaults["model"],
                defaults["duration"],
                defaults["resolution"],
                defaults["prompt_optimizer"],
                input_mode="t2v",
                tags=["lighthouse", "storm", "setup", "rescue", "distinct"],
            ),
            shot_dict(
                "shot-02",
                "Through the Breakers",
                "escalation",
                "struggle",
                "the rescue boat as it fights through the breakers beneath the looming lighthouse",
                "the viewer now feels the physical difficulty of reaching shore",
                "water-level-low",
                "medium-wide tracking",
                "fast low oblique tracking alongside the boat",
                ["same lighthouse", "same storm light", "same sea state", "same rescue mission"],
                ["lower camera height", "boat becomes primary subject", "kinetic lateral motion", "closer danger"],
                ["repeat the distant aerial lighthouse composition", "stay only as a landscape overview"],
                "第二段必须明显不同于第一段：镜头压到贴近海面，重点从灯塔转为救援船本身。画面要让观众感到船身如何被浪头拍打、如何顶着雨和风向灯塔下方的狭窄入口冲去。这一段的叙事功能是体感上的危险升级。",
                "A cinematic escalation shot in the same storm-lashed lighthouse world, clearly different from the opening aerial view. The camera drops to wave height and tracks fast at an oblique angle beside the small rescue boat as it slams through dark breakers toward the narrow inlet beneath the lighthouse. The boat is now the primary subject, with rain whipping across the frame, spray exploding over the bow, and the lighthouse looming much larger in the background as its warm beam flashes across the water. This shot is about physical struggle and imminent risk, not distant scale. Photorealistic, premium maritime realism, violent but believable ocean motion, cold storm light, no fantasy elements.",
                defaults["model"],
                defaults["duration"],
                defaults["resolution"],
                defaults["prompt_optimizer"],
                input_mode="t2v",
                tags=["lighthouse", "storm", "escalation", "boat", "distinct"],
            ),
            shot_dict(
                "shot-03",
                "At the Edge of Safety",
                "payoff",
                "arrival",
                "a witness view from the lighthouse edge as the rescue boat reaches the cove",
                "the viewer sees that the journey has almost ended and the emotional meaning resolves",
                "cliffside-high",
                "extreme-wide witness composition",
                "restrained hold with the lighthouse beam and storm slowly easing",
                ["same lighthouse", "same cove", "same blue-hour storm palette", "same rescue boat"],
                ["new witness viewpoint", "new emotional function", "broader final composition", "motion calms down"],
                ["repeat the water-level struggle shot", "behave like another action beat"],
                "第三段不能再继续做动作镜头，而是要变成收束镜头：从灯塔边缘或悬崖高处俯看小船终于进入避风小湾，近处可以有一位匿名灯塔守望者或栏杆剪影，但不要抢主体。重点是从‘危险’转成‘接近安全’，让三段成为一个完整故事。",
                "A cinematic payoff shot in the same lighthouse rescue world, but with a clearly different emotional function from shot two. From high on the lighthouse balcony or cliffside edge, frame an extreme-wide witness view over the narrow cove as the small rescue boat finally reaches the shelter of the rocks below. A minimal anonymous silhouette of a lighthouse keeper or railing can appear in the near foreground as a witness, never dominating the frame. The beam sweeps once more through rain and mist while the storm begins to ease slightly, turning violent struggle into fragile safety. This is the emotional arrival shot, not another action angle. Photorealistic, restrained, premium maritime feature-film realism, rich weather detail, meaningful calm after danger.",
                defaults["model"],
                defaults["duration"],
                defaults["resolution"],
                defaults["prompt_optimizer"],
                input_mode="t2v",
                tags=["lighthouse", "storm", "payoff", "arrival", "distinct"],
            ),
        ],
    }
    package["music_plan"] = lighthouse_music_plan(package["shots"])
    return package


def build_cloud_postgirl_package(args):
    preset = read_json(
        pathlib.Path(__file__).resolve().parents[1] / "assets" / "cloud-postgirl-runaway-star-brief.json"
    )
    defaults = preset["defaults"]
    package = {
        "project": preset["project"],
        "topic": preset["topic"],
        "language": "zh-CN",
        "treatment": preset["treatment"],
        "defaults": defaults,
        "continuity_spine": {
            "world": (
                "The same sunrise cloud-sea town with suspended brass rail lines, flower-shaped platforms, "
                "floating rooftops, and a cliffside star mailbox above the clouds."
            ),
            "light": (
                "The same soft sunrise light with natural pastel blue-pink clouds, warm golden edge light, "
                "and gentle atmospheric haze."
            ),
            "emotion": "A progression from hopeful departure, to playful chase, to warm first-delivery accomplishment.",
            "cause_effect": (
                "Shot 1 establishes the route and the glowing parcel slipping loose. "
                "Shot 2 follows the chase as the parcel escapes farther along the mail tram. "
                "Shot 3 reveals that returning the parcel to the star mailbox lights the waking cloud town."
            ),
        },
        "audit_targets": {
            "required_total_score": 85,
            "required_distinctness_score": 26,
            "min_adjacent_difference_axes": 3,
        },
        "tags": preset["tags"],
        "shots": [
            shot_dict(
                "shot-01",
                "Morning Route",
                "setup",
                "world-establishment",
                "a tiny brass sky-mail tram crossing a sunrise cloud town with the trainee postgirl aboard",
                "the viewer understands the floating rail world, the heroine, and the glowing parcel beginning to slip free",
                "high-aerial",
                "wide-establishing",
                "gliding aerial descent toward the tram and station",
                ["same brass mail tram", "same pastel sunrise cloud sea", "same trainee postgirl", "same glowing starlight parcel"],
                ["world setup", "high aerial scale", "environment as primary subject"],
                [],
                "第一段是建立镜头：晨曦中的云海小镇、悬空黄铜邮轨、花瓣形站台和一辆穿云而行的小邮车共同建立完整世界。"
                "见习少女邮差站在车尾平台，怀里鼓鼓的邮包里有一颗发光星屑包裹正悄悄松脱。重点是柔和自然的粉蓝晨光、"
                "可爱主角的第一眼魅力、以及故事即将开始的出发感，不要急着进入激烈动作。",
                "A cinematic anime opening shot at sunrise above a floating cloud-sea town. Suspended brass mail rails curve between flower-shaped platforms, tiny rooftops, and cliffside postal towers rising out of soft pastel blue-pink clouds. A small brass sky-mail tram glides along the route as a cute trainee postgirl, around early-teen age, stands on the rear platform in an oversized blue postal cape and cap. A glowing starlight parcel is just starting to slip loose from her mail satchel, hinting at the coming chase. The camera begins high above the cloud town and performs a smooth descending drift toward the tram [推进], establishing world, heroine, and morning promise. High-definition anime feature-film look, soft hand-painted textures, gentle golden rim light, cute but cinematic, no chaotic action yet.",
                defaults["model"],
                defaults["duration"],
                defaults["resolution"],
                defaults["prompt_optimizer"],
                input_mode="t2v",
                tags=["anime", "setup", "cloud-town", "postgirl", "distinct"],
            ),
            shot_dict(
                "shot-02",
                "Catch the Star",
                "escalation",
                "chase",
                "the trainee postgirl chasing the runaway glowing parcel across the moving tram roof",
                "the parcel breaks fully free and the heroine must catch it before it flies toward the open clouds",
                "roof-height-low",
                "medium tracking",
                "fast low oblique tracking along the tram roof",
                ["same brass mail tram", "same pastel sunrise light", "same cloud-town route", "same glowing parcel and heroine silhouette"],
                ["much lower camera height", "heroine becomes primary subject", "kinetic lateral chase motion", "story shifts from setup to pursuit"],
                ["repeat the high aerial establishing composition", "behave like another calm world-building shot", "lose the tram roof geography"],
                "第二段必须明显压低镜头并收紧构图，直接进入追逐。镜头贴近邮车车顶或侧前方，见习少女邮差在晨风里追赶那颗"
                "已经挣脱邮包、带着星屑尾迹向前弹跳的小包裹。重点从世界建立转到角色动作和任务目标，动作强度是中等，"
                "轻冒险、兴奋、可爱，不要做成危险特技大片。",
                "A cinematic continuation of the same sunrise cloud-mail world, clearly different from the opening aerial setup. Continue from the moving tram and drop the camera to roof height for a fast low oblique tracking shot alongside the brass car. The trainee postgirl is now the primary subject as she runs after the runaway glowing parcel bouncing and skimming across the tram roof, leaving a tiny stardust trail in the morning wind. The cloud town and flower station blur past behind her, her oversized blue cape and short hair whipping back as she reaches forward with focused excitement. This is a playful adventure chase, not a dangerous stunt spectacle. Keep the same soft pastel blue-pink sunrise logic and the same tram geography, but make the shot intimate, kinetic, and clearly more specific than shot one. High-definition anime feature-film look, cute expressive motion, clean cinematic action, moderate energy.",
                defaults["model"],
                defaults["duration"],
                defaults["resolution"],
                defaults["prompt_optimizer"],
                input_mode="i2v",
                anchor_from="shot-01",
                frame_position="end",
                frame_offset_seconds=0.12,
                tags=["anime", "escalation", "chase", "i2v", "distinct"],
            ),
            shot_dict(
                "shot-03",
                "First Delivery Light",
                "payoff",
                "arrival",
                "the girl and the giant cliffside star mailbox as the cloud town lights up below",
                "catching and delivering the parcel reveals that it is the first morning mail that wakes the whole route",
                "cliffside-high",
                "extreme-wide witness composition",
                "restrained hold with a gentle reveal of the town lights awakening",
                ["same cloud town", "same pastel sunrise palette", "same trainee postgirl", "same glowing parcel now delivered"],
                ["new witness viewpoint", "new emotional function", "broader payoff composition", "motion calms down after the chase"],
                ["repeat the tram-roof pursuit angle", "behave like another middle chase shot", "keep the heroine as a close action subject"],
                "第三段不能再追逐，而是要进入收束。镜头切到悬崖边巨大的星形邮筒附近，以明显更远、更稳、更有见证感的构图看见"
                "少女终于把包裹送入邮筒，随后云海小镇的轨道灯与窗灯依次亮起。角色仍然可爱，但这段的主体是‘送达后整个世界被唤醒’"
                "这一层意义，要有晨曦发光感和第一次完成任务的小小成就感。",
                "A cinematic payoff shot in the same sunrise cloud-post world, but with a clearly different function from shot two. From a high cliffside viewpoint beside a giant star-shaped mailbox, frame an extreme-wide witness composition over the cloud town below. The trainee postgirl, now a small figure in the frame, finally places the recovered glowing parcel into the mailbox; a warm pulse of light travels outward as rail lamps, station lanterns, and tiny windows across the floating town awaken one after another through the pastel morning haze. The chase energy resolves into wonder and accomplishment. Keep the same soft natural blue-pink sunrise palette and the same heroine silhouette, but shift the emphasis from action to luminous payoff and story meaning. High-definition anime feature-film look, gentle hand-painted atmosphere, cinematic scale, emotionally clear ending, no repeated chase composition.",
                defaults["model"],
                defaults["duration"],
                defaults["resolution"],
                defaults["prompt_optimizer"],
                input_mode="t2v",
                tags=["anime", "payoff", "arrival", "mailbox", "distinct"],
            ),
        ],
    }
    package["music_plan"] = cloud_postgirl_music_plan(package["shots"])
    return package


def build_cloud_postgirl_fast_package(args):
    preset = read_json(
        pathlib.Path(__file__).resolve().parents[1] / "assets" / "cloud-postgirl-runaway-star-fast-brief.json"
    )
    defaults = preset["defaults"]
    package = {
        "project": preset["project"],
        "topic": preset["topic"],
        "language": "zh-CN",
        "treatment": preset["treatment"],
        "defaults": defaults,
        "continuity_spine": {
            "world": (
                "The same sunrise cloud-sea town with suspended brass rail lines, flower-shaped stations, "
                "a moving sky-mail tram, and a cliffside star mailbox above the same cloud valley."
            ),
            "light": (
                "The same soft sunrise light with natural pastel blue-pink clouds, warm golden edge light, "
                "and gentle haze across all image anchors and generated motion."
            ),
            "emotion": "A progression from hopeful departure, to playful chase, to warm first-delivery accomplishment.",
            "cause_effect": (
                "Shot 1 starts from a prepared setup anchor still and introduces the parcel slipping loose. "
                "Shot 2 continues the same tram geography as the chase intensifies. "
                "Shot 3 uses a separate payoff anchor still at the star mailbox so Fast mode can end on a clearly different composition without repeating shot two."
            ),
        },
        "audit_targets": {
            "required_total_score": 85,
            "required_distinctness_score": 26,
            "min_adjacent_difference_axes": 3,
        },
        "tags": preset["tags"],
        "shots": [
            shot_dict(
                "shot-01",
                "Morning Route",
                "setup",
                "world-establishment",
                "a prepared anime key art still of the sunrise cloud tram and the trainee postgirl before the parcel escapes",
                "the viewer understands the floating rail world, the heroine, and the glowing parcel beginning to slip free",
                "high-aerial",
                "wide-establishing",
                "gentle aerial drift and small character/environment motion from the still anchor",
                ["same brass mail tram", "same pastel sunrise cloud sea", "same trainee postgirl", "same glowing starlight parcel"],
                ["world setup", "high aerial scale", "environment as primary subject"],
                [],
                "Fast 版第一段必须从预先准备的 setup anchor still 起步。锚点图应已经包含晨曦云海小镇、悬空黄铜邮轨、"
                "小邮车和见习少女邮差。生成时不要重写世界，而是让画面在 6 秒内轻柔活起来：云层缓慢流动、邮车前行、"
                "少女回头察觉包裹松脱，发光星屑包裹开始滑出邮包。重点仍是建立世界和出发感。",
                "Starting from the provided anime setup anchor still of the sunrise cloud-mail tram, animate the scene into a gentle cinematic opening. The soft pastel cloud sea drifts, the brass tram moves forward along the suspended rail, the trainee postgirl in her oversized blue cape notices movement in her satchel, and the glowing starlight parcel begins to slip loose. Keep the same established composition and world identity from the anchor image, then add subtle motion, light wind, and a clear story trigger. High-definition anime feature-film look, soft hand-painted textures, gentle golden rim light, cute and cinematic, calm but alive, no abrupt camera redesign.",
                defaults["model"],
                defaults["duration"],
                defaults["resolution"],
                defaults["prompt_optimizer"],
                input_mode="i2v",
                first_frame_image="anchors/shot-01-start.png",
                tags=["anime", "setup", "fast", "i2v", "distinct"],
            ),
            shot_dict(
                "shot-02",
                "Catch the Star",
                "escalation",
                "chase",
                "the trainee postgirl chasing the runaway glowing parcel across the moving tram roof",
                "the parcel breaks fully free and the heroine must catch it before it flies toward the open clouds",
                "roof-height-low",
                "medium tracking",
                "fast low oblique tracking along the tram roof",
                ["same brass mail tram", "same pastel sunrise light", "same cloud-town route", "same glowing parcel and heroine silhouette"],
                ["much lower camera height", "heroine becomes primary subject", "kinetic lateral chase motion", "story shifts from setup to pursuit"],
                ["repeat the high aerial establishing composition", "behave like another calm world-building shot", "lose the tram roof geography"],
                "第二段继续使用 i2v，但必须比第一段更低、更近、更动。沿用第一段末帧的车体和角色关系，镜头压到邮车车顶高度，"
                "让见习少女邮差在晨风里追赶弹跳的发光包裹。动作强度中等，重点是轻冒险和明确任务推进，不要拍成危险杂技。",
                "Continue from the end frame of shot one in the same sunrise cloud-mail world, but drop to a much lower roof-height viewpoint and turn the scene into a playful chase. The runaway glowing parcel bounces and skims along the moving tram roof, leaving a tiny stardust trail, while the trainee postgirl runs after it with focused excitement, her blue cape and short hair moving in the wind. Keep the same tram, same pastel sunrise logic, and same story geography, but make the shot intimate, kinetic, and clearly different from the setup. Moderate action energy, cute anime feature-film motion, clean cinematic chase, not a dangerous stunt spectacle.",
                defaults["model"],
                defaults["duration"],
                defaults["resolution"],
                defaults["prompt_optimizer"],
                input_mode="i2v",
                anchor_from="shot-01",
                frame_position="end",
                frame_offset_seconds=0.12,
                tags=["anime", "escalation", "chase", "fast", "i2v", "distinct"],
            ),
            shot_dict(
                "shot-03",
                "First Delivery Light",
                "payoff",
                "arrival",
                "a prepared payoff anchor still of the girl beside the giant cliffside star mailbox above the waking cloud town",
                "delivering the parcel reveals that it is the first morning mail that lights the whole route",
                "cliffside-high",
                "extreme-wide witness composition",
                "restrained hold with a gentle reveal of the town lights awakening",
                ["same cloud town", "same pastel sunrise palette", "same trainee postgirl", "same glowing parcel now delivered"],
                ["new witness viewpoint", "new emotional function", "broader payoff composition", "motion calms down after the chase"],
                ["repeat the tram-roof pursuit angle", "behave like another middle chase shot", "keep the heroine as a close action subject"],
                "Fast 版第三段不要再从第二段末帧硬续，以免重复镜头。应改用单独准备的 payoff anchor still：少女已经抵达悬崖边巨大的"
                "星形邮筒，脚下是同一座晨曦云海小镇。生成时让她把包裹送入邮筒，然后轨道灯、站台灯和小镇窗灯依次苏醒，完成温暖收束。",
                "Starting from the provided payoff anchor still at the cliffside star mailbox, animate a clearly different final image in the same sunrise cloud-post world. The trainee postgirl, now small in the frame, places the recovered glowing parcel into the giant star-shaped mailbox. A warm pulse of light travels outward and rail lamps, station lanterns, and tiny windows across the floating town awaken one after another through the pastel morning haze. Keep the same heroine design, same cloud town palette, and same sunrise light logic, but do not behave like another chase shot. High-definition anime feature-film look, gentle hand-painted atmosphere, luminous emotional payoff, stable witness composition.",
                defaults["model"],
                defaults["duration"],
                defaults["resolution"],
                defaults["prompt_optimizer"],
                input_mode="i2v",
                first_frame_image="anchors/shot-03-start.png",
                tags=["anime", "payoff", "arrival", "fast", "i2v", "distinct"],
            ),
        ],
    }
    package["music_plan"] = cloud_postgirl_music_plan(package["shots"])
    return package


def render_director_brief(package):
    lines = [
        f"# Director Brief: {package['project']}",
        "",
        f"- Topic: {package['topic']}",
        f"- Treatment: {package['treatment']}",
        f"- Default model: {package['defaults']['model']}",
        f"- Default duration: {package['defaults']['duration']}s",
        f"- Default resolution: {package['defaults']['resolution']}",
        f"- Prompt optimizer: {str(package['defaults']['prompt_optimizer']).lower()}",
        f"- Soundtrack model: {package['music_plan']['model']}",
        f"- Soundtrack mode: {package['music_plan']['mode']}",
        "",
        "## Continuity Spine",
        "",
    ]
    for key, value in package["continuity_spine"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Story Arc", ""])
    for shot in package["shots"]:
        lines.append(f"- {shot['shot_id']}: {shot['title']} — {shot['dramatic_purpose']} / {shot['story_beat']}")
    lines.extend(["", "## Soundtrack Arc", ""])
    lines.append(f"- Goal: {package['music_plan']['goal']}")
    lines.append(f"- Overall arc: {package['music_plan']['overall_arc']}")
    return "\n".join(lines) + "\n"


def render_storyboard(package):
    lines = ["# Storyboard", ""]
    for shot in package["shots"]:
        lines.extend(
            [
                f"## {shot['shot_id']} — {shot['title']}",
                "",
                f"- Dramatic purpose: {shot['dramatic_purpose']}",
                f"- Story beat: {shot['story_beat']}",
                f"- Primary subject: {shot['primary_subject']}",
                f"- New information: {shot['new_information']}",
                f"- Camera height: {shot['camera_height']}",
                f"- Framing: {shot['framing']}",
                f"- Camera movement: {shot['camera_movement']}",
                f"- Continuity anchors: {', '.join(shot['continuity_anchors'])}",
            ]
        )
        if shot["difference_axes"]:
            lines.append(f"- Difference axes: {', '.join(shot['difference_axes'])}")
        if shot["must_not_repeat"]:
            lines.append(f"- Must not repeat: {', '.join(shot['must_not_repeat'])}")
        if shot.get("first_frame_image"):
            lines.append(f"- First frame image: {shot['first_frame_image']}")
        if shot.get("anchor_from"):
            lines.append(f"- Anchor from: {shot['anchor_from']}")
        if shot.get("status") == "existing":
            lines.append(f"- Existing video: {shot['video_path']}")
        else:
            lines.append(f"- Input mode: {shot['input_mode']}")
        lines.extend(["", "### Chinese Intent", "", shot["prompt_zh"], ""])
    return "\n".join(lines) + "\n"


def render_shotlist(package):
    lines = ["# Shot List", ""]
    for shot in package["shots"]:
        lines.extend(
            [
                f"## {shot['shot_id']} — {shot['title']}",
                "",
                f"- Dramatic purpose: {shot['dramatic_purpose']}",
                f"- Story beat: {shot['story_beat']}",
                f"- Input mode: {shot.get('input_mode', shot.get('status', 't2v'))}",
                f"- Camera height: {shot['camera_height']}",
                f"- Framing: {shot['framing']}",
                f"- Camera movement: {shot['camera_movement']}",
                f"- First frame image: {shot.get('first_frame_image', 'n/a')}",
                f"- Anchor from: {shot.get('anchor_from', 'n/a')}",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def render_prompts(package):
    lines = ["# Prompts", ""]
    for shot in package["shots"]:
        if shot.get("status") == "existing":
            continue
        lines.extend(
            [
                f"## {shot['shot_id']} — {shot['title']}",
                "",
                "### Chinese Intent",
                "",
                shot["prompt_zh"],
                "",
                "### English Production Prompt",
                "",
                shot["prompt_en"],
                "",
            ]
        )
    return "\n".join(lines)


def render_music_plan(package):
    plan = package["music_plan"]
    lines = [
        "# Music Plan",
        "",
        f"- Model: {plan['model']}",
        f"- Mode: {plan['mode']}",
        f"- Vocal policy: {plan['vocal_policy']}",
        f"- Goal: {plan['goal']}",
        f"- Duration strategy: {plan['duration_strategy']}",
        f"- Target video duration: {plan['target_video_duration_seconds']}s",
        f"- Overall arc: {plan['overall_arc']}",
        f"- Palette: {plan['palette']}",
        "",
        "## Cue Sheet",
        "",
    ]
    for cue in plan["cue_sheet"]:
        lines.extend(
            [
                f"### {cue['shot_id']} — {cue['title']}",
                "",
                f"- Start: {cue['start_seconds']}s",
                f"- End: {cue['end_seconds']}s",
                f"- Story function: {cue['story_function']}",
                f"- Music function: {cue['music_function']}",
                f"- Energy: {cue['energy']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Chinese Music Prompt",
            "",
            plan["prompt_zh"],
            "",
            "## English Music Prompt",
            "",
            plan["prompt_en"],
            "",
            "## Mix Plan",
            "",
            f"- Music volume: {plan['mix_plan']['music_volume']}",
            f"- Fade in: {plan['mix_plan']['fade_in_seconds']}s",
            f"- Fade out: {plan['mix_plan']['fade_out_seconds']}s",
            f"- Loop strategy: {plan['mix_plan']['loop_strategy']}",
            f"- Trim to video: {str(plan['mix_plan']['trim_to_video']).lower()}",
            "",
        ]
    )
    return "\n".join(lines)


def render_distinctness_check(package):
    planned_shots = package["shots"]
    lines = ["# Distinctness Check", ""]
    for previous, current in zip(planned_shots, planned_shots[1:]):
        lines.extend(
            [
                f"## {previous['shot_id']} -> {current['shot_id']}",
                "",
                f"- Expected difference axes: {', '.join(current['difference_axes']) or 'n/a'}",
                f"- Must not repeat: {', '.join(current['must_not_repeat']) or 'n/a'}",
                f"- Previous framing: {previous['framing']}",
                f"- Current framing: {current['framing']}",
                f"- Previous camera height: {previous['camera_height']}",
                f"- Current camera height: {current['camera_height']}",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Create a Hailuo story package")
    parser.add_argument("--topic", default="cinematic nature story")
    parser.add_argument(
        "--preset",
        choices=[
            "iceland-continuation",
            "storm-lighthouse-rescue",
            "cloud-postgirl-runaway-star",
            "cloud-postgirl-runaway-star-fast",
        ],
        default=None,
    )
    parser.add_argument("--existing-shot-video", default=None)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--treatment", default="cinematic connected three-shot story")
    parser.add_argument("--model", default="MiniMax-Hailuo-2.3")
    parser.add_argument("--duration", type=int, default=6)
    parser.add_argument("--resolution", default="768P")
    parser.add_argument("--prompt-optimizer", action="store_true")
    args = parser.parse_args()

    output_dir = pathlib.Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.preset == "iceland-continuation":
        if not args.existing_shot_video:
            raise RuntimeError("--existing-shot-video is required for the iceland-continuation preset")
        package = build_iceland_package(args)
    elif args.preset == "storm-lighthouse-rescue":
        package = build_lighthouse_package(args)
    elif args.preset == "cloud-postgirl-runaway-star":
        package = build_cloud_postgirl_package(args)
    elif args.preset == "cloud-postgirl-runaway-star-fast":
        package = build_cloud_postgirl_fast_package(args)
    else:
        package = build_generic_package(args)

    package["created_at"] = dt.datetime.now().isoformat(timespec="seconds")
    package["output_dir"] = str(output_dir)

    write_json(output_dir / "story-package.json", package)
    write_text(output_dir / "director-brief.md", render_director_brief(package))
    write_text(output_dir / "storyboard.md", render_storyboard(package))
    write_text(output_dir / "shotlist.md", render_shotlist(package))
    write_text(output_dir / "prompts.md", render_prompts(package))
    write_text(output_dir / "music-plan.md", render_music_plan(package))
    write_text(output_dir / "distinctness-check.md", render_distinctness_check(package))
    print(json.dumps({"story_package": str(output_dir / "story-package.json")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
