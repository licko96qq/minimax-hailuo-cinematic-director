#!/usr/bin/env python3

import argparse
import json
import pathlib
import re

from minimax_common import read_json, write_json, write_text


def expected_video_duration(shots):
    return round(sum(float(shot.get("duration", 0) or 0) for shot in shots), 3)


def structural_placeholder_lyrics(lyrics):
    stripped = re.sub(r"\[[^\]]+\]", "", lyrics or "")
    stripped = re.sub(r"\s+", "", stripped)
    return not stripped


def score_narrative_fit(package, plan):
    shots = package["shots"]
    cue_sheet = plan.get("cue_sheet", [])
    cue_lookup = {cue.get("shot_id"): cue for cue in cue_sheet}
    score = 30
    notes = []

    if plan.get("vocal_policy") != "no-vocals":
        score -= 6
        notes.append("配乐方案没有明确要求无人声。")
    if not plan.get("overall_arc"):
        score -= 6
        notes.append("配乐方案缺少整体情绪弧线。")
    if len(cue_sheet) != len(shots):
        score -= 8
        notes.append("配乐 cue 数量与镜头数量不一致。")

    for shot in shots:
        cue = cue_lookup.get(shot["shot_id"])
        if not cue:
            score -= 5
            notes.append(f"{shot['shot_id']} 缺少对应的配乐 cue。")
            continue
        if cue.get("story_function") != shot.get("dramatic_purpose"):
            score -= 2
            notes.append(f"{shot['shot_id']} 的配乐功能与镜头戏剧功能不完全匹配。")
        if not cue.get("music_function"):
            score -= 2
            notes.append(f"{shot['shot_id']} 没有明确写出配乐任务。")
        if not cue.get("energy"):
            score -= 1
            notes.append(f"{shot['shot_id']} 没有明确写出能量级别。")

    return max(score, 0), notes


def score_timing_fit(package, plan):
    target_duration = float(plan.get("target_video_duration_seconds", 0) or 0)
    expected_duration = expected_video_duration(package["shots"])
    cue_sheet = sorted(plan.get("cue_sheet", []), key=lambda item: item.get("start_seconds", 0))
    score = 25
    notes = []

    if abs(target_duration - expected_duration) > 0.6:
        score -= 8
        notes.append(
            f"配乐目标时长 {target_duration:.2f}s 与视频预估时长 {expected_duration:.2f}s 偏差过大。"
        )

    previous_end = 0.0
    for cue in cue_sheet:
        start = float(cue.get("start_seconds", 0) or 0)
        end = float(cue.get("end_seconds", 0) or 0)
        if abs(start - previous_end) > 0.35:
            score -= 4
            notes.append(f"{cue.get('shot_id', 'unknown')} 的 cue 时间衔接不连续。")
        if end <= start:
            score -= 4
            notes.append(f"{cue.get('shot_id', 'unknown')} 的 cue 时长无效。")
        previous_end = end

    if cue_sheet and abs(previous_end - target_duration) > 0.5:
        score -= 5
        notes.append("最后一个 cue 没有覆盖到目标视频尾部。")

    if not plan.get("duration_strategy"):
        score -= 4
        notes.append("配乐方案缺少时长处理策略。")

    return max(score, 0), notes


def score_generation_feasibility(plan):
    score = 25
    notes = []
    if not str(plan.get("model", "")).startswith("music-2.5"):
        score -= 8
        notes.append("当前配乐模型不是预期的 MiniMax music-2.5 系列。")
    if len(plan.get("prompt_zh", "")) < 80:
        score -= 6
        notes.append("中文配乐提示词过短，难以稳定约束情绪弧线与风格。")
    if "无人声" not in plan.get("prompt_zh", "") and "no vocals" not in plan.get("prompt_en", "").lower():
        score -= 5
        notes.append("配乐提示词没有明确声明无人声要求。")
    if plan.get("lyrics") and not structural_placeholder_lyrics(plan.get("lyrics", "")):
        score -= 4
        notes.append("当前配乐方案包含真实歌词文本，可能引入人声，不适合作为纯背景音乐。")
    if not plan.get("palette"):
        score -= 2
        notes.append("配乐方案缺少音色/编制方向。")
    return max(score, 0), notes


def score_mix_feasibility(plan):
    mix_plan = plan.get("mix_plan", {})
    score = 20
    notes = []
    volume = float(mix_plan.get("music_volume", 0) or 0)
    fade_in = float(mix_plan.get("fade_in_seconds", 0) or 0)
    fade_out = float(mix_plan.get("fade_out_seconds", 0) or 0)

    if volume < 0.18 or volume > 0.55:
        score -= 8
        notes.append(f"音乐混音音量 {volume:.2f} 超出建议范围。")
    if fade_in < 0.5:
        score -= 4
        notes.append("音乐淡入时间过短，开头可能显得生硬。")
    if fade_out < 1.0:
        score -= 4
        notes.append("音乐淡出时间过短，结尾可能显得突然。")
    if mix_plan.get("loop_strategy") != "loop_if_short_trim_if_long":
        score -= 2
        notes.append("混音策略没有明确说明短音乐循环、长音乐裁切。")
    if not mix_plan.get("trim_to_video", False):
        score -= 2
        notes.append("混音方案没有明确要求按视频时长裁切。")

    return max(score, 0), notes


def build_markdown(report):
    lines = [
        "# 配乐审核结果报告",
        "",
        f"- 是否通过：{'是' if report['passed'] else '否'}",
        f"- 总分：{report['total_score']} / 100",
        f"- 叙事契合度：{report['scores']['narrative_fit']} / 30",
        f"- 时间结构契合度：{report['scores']['timing_fit']} / 25",
        f"- 生成可行性：{report['scores']['generation_feasibility']} / 25",
        f"- 混音可行性：{report['scores']['mix_feasibility']} / 20",
        "",
        "## 审核意见",
        "",
    ]
    if report["notes"]:
        for note in report["notes"]:
            lines.append(f"- {note}")
    else:
        lines.append("- 配乐方案通过审核，当前没有额外修改意见。")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Audit soundtrack feasibility for a Hailuo story package")
    parser.add_argument("--story-package", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--markdown", required=True)
    args = parser.parse_args()

    package = read_json(args.story_package)
    plan = package.get("music_plan")
    if not plan:
        raise RuntimeError("story-package.json 缺少 music_plan，无法执行配乐审核。")

    narrative_fit, narrative_notes = score_narrative_fit(package, plan)
    timing_fit, timing_notes = score_timing_fit(package, plan)
    generation_feasibility, generation_notes = score_generation_feasibility(plan)
    mix_feasibility, mix_notes = score_mix_feasibility(plan)
    total_score = narrative_fit + timing_fit + generation_feasibility + mix_feasibility

    targets = plan.get("audit_targets", {})
    required_total = int(targets.get("required_total_score", 80))
    required_narrative = int(targets.get("required_narrative_fit", 22))
    required_mix = int(targets.get("required_mix_feasibility", 16))
    notes = narrative_notes + timing_notes + generation_notes + mix_notes
    passed = (
        total_score >= required_total
        and narrative_fit >= required_narrative
        and mix_feasibility >= required_mix
    )

    report = {
        "passed": passed,
        "total_score": total_score,
        "scores": {
            "narrative_fit": narrative_fit,
            "timing_fit": timing_fit,
            "generation_feasibility": generation_feasibility,
            "mix_feasibility": mix_feasibility,
        },
        "requirements": {
            "required_total_score": required_total,
            "required_narrative_fit": required_narrative,
            "required_mix_feasibility": required_mix,
        },
        "notes": notes,
    }

    report_path = pathlib.Path(args.report).resolve()
    markdown_path = pathlib.Path(args.markdown).resolve()
    write_json(report_path, report)
    write_text(markdown_path, build_markdown(report))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
