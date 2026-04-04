#!/usr/bin/env python3

import argparse
import json
import pathlib
import re

from minimax_common import read_json, write_json, write_text


def tokenize(text):
    return {token for token in re.findall(r"[a-zA-Z']+", text.lower()) if len(token) > 2}


def jaccard(a, b):
    if not a and not b:
        return 1.0
    return len(a & b) / max(len(a | b), 1)


def score_story(shots):
    beats = [shot.get("story_beat") for shot in shots]
    unique_beats = len(set(beats))
    score = 10
    notes = []
    if len(shots) >= 3 and unique_beats >= 3:
        score = 25
    else:
        score = max(10, unique_beats * 8)
        notes.append("故事节拍没有清晰拆分为建立、升级、收束三段。")
    return score, notes


def score_continuity(package):
    spine = package.get("continuity_spine", {})
    score = 20 if len(spine) >= 3 else 10
    notes = []
    if len(spine) < 3:
        notes.append("连续性主线定义不足，缺少足够的世界/光线/情绪锚点。")
    for shot in package["shots"]:
        anchors = shot.get("continuity_anchors", [])
        if shot.get("status") != "existing" and len(anchors) < 2:
            score -= 3
            notes.append(f"{shot['shot_id']} 的连续性锚点过少。")
    return max(score, 0), notes


def score_distinctness(shots, min_axes):
    score = 30
    notes = []
    for previous, current in zip(shots, shots[1:]):
        changed = 0
        for key in ("camera_height", "framing", "primary_subject", "story_beat", "camera_movement"):
            if previous.get(key) != current.get(key):
                changed += 1
        if len(current.get("difference_axes", [])) < min_axes:
            score -= 6
            notes.append(f"{current['shot_id']} 声明的差异轴数量不足。")
        if changed < min_axes:
            score -= 8
            notes.append(f"{previous['shot_id']} 与 {current['shot_id']} 在镜头语言上差异不够明显。")
        if not current.get("must_not_repeat"):
            score -= 4
            notes.append(f"{current['shot_id']} 没有明确写出禁止重复的内容。")
    return max(score, 0), notes


def score_prompts(shots):
    score = 25
    notes = []
    prompts = [shot.get("prompt_en", "") for shot in shots if shot.get("status") != "existing"]
    token_sets = [tokenize(prompt) for prompt in prompts]
    for index in range(len(token_sets) - 1):
        similarity = jaccard(token_sets[index], token_sets[index + 1])
        if similarity > 0.72:
            score -= 8
            notes.append(
                f"第 {index + 1} 段与第 {index + 2} 段的提示词相似度过高（{similarity:.2f}）。"
            )
    for shot in shots:
        if shot.get("status") == "existing":
            continue
        if len(shot.get("prompt_en", "")) < 180:
            score -= 3
            notes.append(f"{shot['shot_id']} 的英文生产提示词过薄，不足以支撑电影级镜头控制。")
    return max(score, 0), notes


def build_markdown(report):
    lines = [
        "# 审核结果报告",
        "",
        f"- 是否通过：{'是' if report['passed'] else '否'}",
        f"- 总分：{report['total_score']} / 100",
        f"- 故事结构：{report['scores']['story']} / 25",
        f"- 连续性：{report['scores']['continuity']} / 20",
        f"- 镜头差异度：{report['scores']['distinctness']} / 30",
        f"- 提示词质量：{report['scores']['prompt_quality']} / 25",
        "",
        "## 审核意见",
        "",
    ]
    if report["notes"]:
        for note in report["notes"]:
            lines.append(f"- {note}")
    else:
        lines.append("- 故事包通过审核，当前没有额外修改意见。")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Audit a Hailuo story package")
    parser.add_argument("--story-package", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--markdown", required=True)
    args = parser.parse_args()

    package = read_json(args.story_package)
    shots = package["shots"]
    min_axes = package.get("audit_targets", {}).get("min_adjacent_difference_axes", 3)
    required_total = package.get("audit_targets", {}).get("required_total_score", 80)
    required_distinctness = package.get("audit_targets", {}).get("required_distinctness_score", 24)

    story_score, story_notes = score_story(shots)
    continuity_score, continuity_notes = score_continuity(package)
    distinctness_score, distinctness_notes = score_distinctness(shots, min_axes)
    prompt_score, prompt_notes = score_prompts(shots)

    total_score = story_score + continuity_score + distinctness_score + prompt_score
    notes = story_notes + continuity_notes + distinctness_notes + prompt_notes
    passed = total_score >= required_total and distinctness_score >= required_distinctness

    report = {
        "passed": passed,
        "total_score": total_score,
        "scores": {
            "story": story_score,
            "continuity": continuity_score,
            "distinctness": distinctness_score,
            "prompt_quality": prompt_score,
        },
        "requirements": {
            "required_total_score": required_total,
            "required_distinctness_score": required_distinctness,
            "min_adjacent_difference_axes": min_axes,
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
