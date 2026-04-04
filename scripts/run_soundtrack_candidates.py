#!/usr/bin/env python3

import argparse
import copy
import json
import pathlib
import shutil
import subprocess

from minimax_common import read_json, write_json, write_text


DEFAULT_VARIANTS = [
    {
        "id": "airy-dawn-wonder",
        "label": "Airy Dawn Wonder",
        "goal_suffix_zh": "更偏晨曦云海的轻盈奇遇感。",
        "palette_append_zh": "更强调轻木管、钟琴、竖琴与柔和长弦，减少明显鼓点。",
        "prompt_zh_suffix": (
            "这一版优先突出天空苏醒、晨光漂浮、轻盈起飞感，木管与钟琴更清楚，"
            "中段推进存在但不要让节奏压过梦幻感。"
        ),
        "prompt_en_suffix": (
            "Favor airy dawn wonder, floating cloudlight, and delicate lift. "
            "Let woodwinds, bells, and harp read more clearly. Maintain propulsion in shot two, "
            "but keep the music dreamlike rather than punchy."
        ),
        "music_volume": 0.24,
        "fade_in_seconds": 1.0,
        "fade_out_seconds": 1.8,
    },
    {
        "id": "playful-adventure-pulse",
        "label": "Playful Adventure Pulse",
        "goal_suffix_zh": "更偏轻冒险推进与角色魅力。",
        "palette_append_zh": "加入更明确的拨弦、轻打击和木管脉冲，但仍保持可爱与电影感。",
        "prompt_zh_suffix": (
            "这一版让第二段的追逐推进更鲜明，用轻打击、拨弦和木管节奏带出活力，"
            "但不要变成预告片轰炸或流行歌曲。第一段仍需保留出发感，第三段要自然回到温暖收束。"
        ),
        "prompt_en_suffix": (
            "Push the middle chase with clearer playful propulsion using light percussion, pizzicato, "
            "and animated woodwind rhythm, but keep it cute and cinematic rather than trailer-heavy or pop-driven. "
            "Shot one must still breathe, and shot three must resolve warmly."
        ),
        "music_volume": 0.27,
        "fade_in_seconds": 0.8,
        "fade_out_seconds": 1.7,
    },
    {
        "id": "warm-glowing-delivery",
        "label": "Warm Glowing Delivery",
        "goal_suffix_zh": "更偏送达后的发光回报与情绪回暖。",
        "palette_append_zh": "强化暖弦、柔和钢琴和发光钟铃，保留少量中段节奏推力。",
        "prompt_zh_suffix": (
            "这一版优先让第三段的送达和小镇苏醒更有情绪回报，结尾要有发光、释然、"
            "第一次完成使命的温暖感；同时保留第二段适度推进，不要让前两段过于平。"
        ),
        "prompt_en_suffix": (
            "Favor the emotional glow of delivery payoff and the town awakening. "
            "Use warmer strings, soft piano, and luminous bell colors so the third shot lands with relief and accomplishment, "
            "while still preserving enough pulse in shot two to avoid a flat arc."
        ),
        "music_volume": 0.25,
        "fade_in_seconds": 0.9,
        "fade_out_seconds": 2.0,
    },
]


def run_command(args):
    completed = subprocess.run(args, check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def build_variant_package(base_package, variant):
    package = copy.deepcopy(base_package)
    music_plan = package["music_plan"]
    music_plan["goal"] = f"{music_plan['goal']} {variant['goal_suffix_zh']}".strip()
    music_plan["palette"] = f"{music_plan['palette']} {variant['palette_append_zh']}".strip()
    music_plan["prompt_zh"] = f"{music_plan['prompt_zh']} {variant['prompt_zh_suffix']}".strip()
    music_plan["prompt_en"] = f"{music_plan['prompt_en']} {variant['prompt_en_suffix']}".strip()
    music_plan["variant"] = {
        "id": variant["id"],
        "label": variant["label"],
    }
    mix_plan = music_plan["mix_plan"]
    mix_plan["music_volume"] = variant["music_volume"]
    mix_plan["fade_in_seconds"] = variant["fade_in_seconds"]
    mix_plan["fade_out_seconds"] = variant["fade_out_seconds"]
    return package


def load_variants(path):
    if not path:
        return DEFAULT_VARIANTS
    payload = read_json(path)
    variants = payload.get("variants") if isinstance(payload, dict) else payload
    if not isinstance(variants, list) or not variants:
        raise RuntimeError("variants json 必须是数组，或形如 {\"variants\": [...]}。")
    return variants


def summarize_candidate(candidate_dir, variant, audit_report, review_report):
    audit_total = int(audit_report.get("total_score", 0) or 0)
    review_total = int(review_report.get("total_score", 0) or 0) if review_report else 0
    overall_score = review_total * 0.7 + audit_total * 0.3
    return {
        "id": variant["id"],
        "label": variant["label"],
        "candidate_dir": str(candidate_dir),
        "audit_passed": bool(audit_report.get("passed")),
        "audit_total_score": audit_total,
        "review_passed": bool(review_report.get("passed")) if review_report else False,
        "review_total_score": review_total,
        "overall_score": round(overall_score, 2),
        "final_with_music": str((candidate_dir / "final-with-music.mp4").resolve())
        if (candidate_dir / "final-with-music.mp4").exists()
        else None,
        "review_summary": str((candidate_dir / "soundtrack-review-summary.md").resolve())
        if (candidate_dir / "soundtrack-review-summary.md").exists()
        else None,
    }


def build_markdown(summary):
    lines = [
        "# Soundtrack Candidate Leaderboard",
        "",
        f"- Story package: `{summary['story_package']}`",
        f"- Sequence preview: `{summary['sequence_preview']}`",
        "",
        "## Candidates",
        "",
    ]
    for item in summary["candidates"]:
        lines.extend(
            [
                f"### {item['id']} — {item['label']}",
                "",
                f"- Audit: {'PASS' if item['audit_passed'] else 'FAIL'} ({item['audit_total_score']}/100)",
                f"- Review: {'PASS' if item['review_passed'] else 'FAIL'} ({item['review_total_score']}/100)",
                f"- Overall: {item['overall_score']}",
            ]
        )
        if item["final_with_music"]:
            lines.append(f"- Final with music: `{item['final_with_music']}`")
        if item["review_summary"]:
            lines.append(f"- Review summary: `{item['review_summary']}`")
        lines.append("")
    if summary.get("best_candidate"):
        best = summary["best_candidate"]
        lines.extend(
            [
                "## Selected",
                "",
                f"- Best candidate: `{best['id']}` — {best['label']}",
                f"- Promoted final: `{summary['promoted_final_with_music']}`",
                f"- Promoted manifest: `{summary['promoted_manifest']}`",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def main():
    parser = argparse.ArgumentParser(description="Generate, audit, compare, and promote multiple soundtrack variants")
    parser.add_argument("--story-package", required=True)
    parser.add_argument("--sequence-preview", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--variants-json", default=None)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--promote-best", action="store_true")
    args = parser.parse_args()

    story_package_path = pathlib.Path(args.story_package).resolve()
    sequence_preview_path = pathlib.Path(args.sequence_preview).resolve()
    output_dir = pathlib.Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    base_package = read_json(story_package_path)
    variants = load_variants(args.variants_json)
    candidates = []

    for variant in variants:
        candidate_dir = output_dir / variant["id"]
        candidate_dir.mkdir(parents=True, exist_ok=True)
        variant_package = build_variant_package(base_package, variant)
        variant_package_path = candidate_dir / "story-package.variant.json"
        write_json(variant_package_path, variant_package)

        audit_report_path = candidate_dir / "soundtrack-audit-report.json"
        audit_summary_path = candidate_dir / "soundtrack-audit-summary.md"
        run_command(
            [
                "python3",
                str(pathlib.Path(__file__).with_name("audit_soundtrack_plan.py")),
                "--story-package",
                str(variant_package_path),
                "--report",
                str(audit_report_path),
                "--markdown",
                str(audit_summary_path),
            ]
        )
        audit_report = read_json(audit_report_path)
        review_report = None

        if args.execute and audit_report.get("passed"):
            run_command(
                [
                    "python3",
                    str(pathlib.Path(__file__).with_name("run_soundtrack_pipeline.py")),
                    "--story-package",
                    str(variant_package_path),
                    "--sequence-preview",
                    str(sequence_preview_path),
                    "--output-dir",
                    str(candidate_dir),
                    "--execute",
                ]
            )
            review_report = read_json(candidate_dir / "soundtrack-review-report.json")

        candidates.append(summarize_candidate(candidate_dir, variant, audit_report, review_report))

    passed_candidates = [
        item for item in candidates if item["audit_passed"] and (not args.execute or item["review_passed"])
    ]
    passed_candidates.sort(
        key=lambda item: (
            item["review_total_score"],
            item["audit_total_score"],
            item["overall_score"],
        ),
        reverse=True,
    )
    best_candidate = passed_candidates[0] if passed_candidates else None

    summary = {
        "story_package": str(story_package_path),
        "sequence_preview": str(sequence_preview_path),
        "candidates": candidates,
        "best_candidate": best_candidate,
    }

    if args.promote_best and best_candidate:
        promoted_dir = output_dir / "selected"
        promoted_dir.mkdir(parents=True, exist_ok=True)
        source_dir = pathlib.Path(best_candidate["candidate_dir"])
        final_src = source_dir / "final-with-music.mp4"
        manifest_src = source_dir / "soundtrack-manifest.json"
        summary_src = source_dir / "soundtrack-review-summary.md"
        final_dst = promoted_dir / "final-with-music.mp4"
        manifest_dst = promoted_dir / "soundtrack-manifest.json"
        review_dst = promoted_dir / "soundtrack-review-summary.md"
        shutil.copy2(final_src, final_dst)
        shutil.copy2(manifest_src, manifest_dst)
        shutil.copy2(summary_src, review_dst)
        summary["promoted_final_with_music"] = str(final_dst.resolve())
        summary["promoted_manifest"] = str(manifest_dst.resolve())
        summary["promoted_review_summary"] = str(review_dst.resolve())

    summary_path = output_dir / "candidate-summary.json"
    markdown_path = output_dir / "candidate-summary.md"
    write_json(summary_path, summary)
    write_text(markdown_path, build_markdown(summary))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
