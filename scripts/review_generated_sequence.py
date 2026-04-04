#!/usr/bin/env python3

import argparse
import json
import pathlib
import re
import subprocess
import tempfile

from minimax_common import ensure_parent, read_json, write_json, write_text


def run_command(args, capture_output=False):
    return subprocess.run(
        args,
        check=True,
        capture_output=capture_output,
        text=True,
    )


def probe_video(video_path):
    completed = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,bit_rate:stream=width,height,nb_frames",
            "-of",
            "json",
            str(video_path),
        ],
        capture_output=True,
    )
    payload = json.loads(completed.stdout)
    stream = payload["streams"][0]
    fmt = payload["format"]
    return {
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "duration_seconds": float(fmt["duration"]),
        "nb_frames": int(stream.get("nb_frames", 0)) if stream.get("nb_frames") else None,
        "size_bytes": int(fmt.get("size", 0)) if fmt.get("size") else None,
        "bit_rate": int(fmt.get("bit_rate", 0)) if fmt.get("bit_rate") else None,
    }


def extract_frame(video_path, output_path, timestamp):
    ensure_parent(output_path)
    run_command(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{timestamp:.3f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            str(output_path),
        ]
    )


def build_contact_sheet(video_path, output_path, duration_seconds):
    ensure_parent(output_path)
    start_ts = 0.0
    middle_ts = duration_seconds / 2.0
    end_ts = max(duration_seconds - 0.12, 0.0)
    with tempfile.TemporaryDirectory(prefix="hailuo-review-") as temp_dir:
        temp_dir_path = pathlib.Path(temp_dir)
        start_path = temp_dir_path / "start.jpg"
        middle_path = temp_dir_path / "middle.jpg"
        end_path = temp_dir_path / "end.jpg"
        extract_frame(video_path, start_path, start_ts)
        extract_frame(video_path, middle_path, middle_ts)
        extract_frame(video_path, end_path, end_ts)
        run_command(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(start_path),
                "-i",
                str(middle_path),
                "-i",
                str(end_path),
                "-filter_complex",
                (
                    "[0:v]scale=683:384[s0];"
                    "[1:v]scale=683:384[s1];"
                    "[2:v]scale=683:384[s2];"
                    "[s0][s1][s2]hstack=inputs=3[v]"
                ),
                "-map",
                "[v]",
                "-frames:v",
                "1",
                str(output_path),
            ]
        )


def compute_ssim(image_a, image_b):
    completed = subprocess.run(
        [
            "ffmpeg",
            "-i",
            str(image_a),
            "-i",
            str(image_b),
            "-lavfi",
            "ssim",
            "-f",
            "null",
            "-",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    text = "\n".join([completed.stdout, completed.stderr])
    match = re.search(r"All:([0-9.]+)", text)
    if not match:
        raise RuntimeError(f"Unable to parse SSIM output: {text}")
    return float(match.group(1))


def build_preview(video_paths, preview_path):
    ensure_parent(preview_path)
    concat_path = preview_path.with_suffix(".concat.txt")
    lines = [f"file '{path}'" for path in video_paths]
    concat_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-vf",
            "fps=24,format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-movflags",
            "+faststart",
            str(preview_path),
        ]
    )
    return concat_path


def completeness_score(shot_details, notes):
    score = 25
    if len(shot_details) < 2:
        notes.append("序列中少于两个可复核的镜头。")
        return 0
    widths = {detail["probe"]["width"] for detail in shot_details}
    heights = {detail["probe"]["height"] for detail in shot_details}
    if len(widths) > 1 or len(heights) > 1:
        score -= 8
        notes.append("镜头分辨率不一致。")
    for detail in shot_details:
        duration = detail["probe"]["duration_seconds"]
        if duration < 5.0 or duration > 6.2:
            score -= 4
            notes.append(f"{detail['shot_id']} 时长异常：{duration:.2f}s。")
        if not pathlib.Path(detail["contact_sheet"]).exists():
            score -= 5
            notes.append(f"{detail['shot_id']} 的三联帧审片图缺失。")
    return max(score, 0)


def distinctness_score(pairwise, max_adjacent_ssim, notes):
    if not pairwise:
        notes.append("没有可用于差异度复核的相邻镜头对。")
        return 0
    score = 45
    for pair in pairwise:
        ssim = pair["ssim"]
        if ssim > max_adjacent_ssim:
            score -= 22
            notes.append(
                f"{pair['from_shot']} 与 {pair['to_shot']} 的视觉相似度过高（SSIM {ssim:.3f}）。"
            )
        elif ssim > 0.62:
            score -= 8
            notes.append(
                f"{pair['from_shot']} 与 {pair['to_shot']} 在视觉上略接近（SSIM {ssim:.3f}），建议人工复看。"
            )
    return max(score, 0)


def packaging_score(preview_exists, shot_details, notes):
    score = 15
    if not preview_exists:
        score -= 10
        notes.append("序列拼接预览片未生成。")
    for detail in shot_details:
        if not pathlib.Path(detail["video_path"]).exists():
            score -= 5
            notes.append(f"{detail['shot_id']} 的视频文件缺失。")
    return max(score, 0)


def quality_signals_score(shot_details, notes):
    score = 15
    for detail in shot_details:
        probe = detail["probe"]
        bit_rate = probe.get("bit_rate") or 0
        size_bytes = probe.get("size_bytes") or 0
        if bit_rate and bit_rate < 1_200_000:
            score -= 3
            notes.append(
                f"{detail['shot_id']} 的码率偏低（{bit_rate} bps），请人工确认画面层次是否足够。"
            )
        if size_bytes and size_bytes < 900_000:
            score -= 2
            notes.append(
                f"{detail['shot_id']} 的文件体积偏小（{size_bytes} bytes），请确认画面是否过静。"
            )
    return max(score, 0)


def build_markdown(report):
    lines = [
        "# 成片复盘报告",
        "",
        f"- 是否通过：{'是' if report['passed'] else '否'}",
        f"- 总分：{report['total_score']} / 100",
        f"- 完整性：{report['scores']['completeness']} / 25",
        f"- 镜头差异度：{report['scores']['distinctness']} / 45",
        f"- 交付包装：{report['scores']['packaging']} / 15",
        f"- 质量信号：{report['scores']['quality_signals']} / 15",
        "",
        "## 相邻镜头 SSIM",
        "",
    ]
    for pair in report["pairwise"]:
        lines.append(f"- {pair['from_shot']} -> {pair['to_shot']}: {pair['ssim']:.3f}")
    lines.extend(["", "## 复盘意见", ""])
    if report["notes"]:
        for note in report["notes"]:
            lines.append(f"- {note}")
    else:
        lines.append("- 复盘通过，当前没有额外问题。")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Review a generated Hailuo sequence after rendering")
    parser.add_argument("--story-package", required=True)
    parser.add_argument("--generation-manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-adjacent-ssim", type=float, default=0.72)
    parser.add_argument("--required-total-score", type=int, default=75)
    args = parser.parse_args()

    story_package = read_json(args.story_package)
    generation_manifest = read_json(args.generation_manifest)
    output_dir = pathlib.Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_lookup = {shot["shot_id"]: shot for shot in generation_manifest["shots"]}
    shot_details = []

    for shot in story_package["shots"]:
        shot_id = shot["shot_id"]
        if shot.get("status") == "existing":
            video_path = pathlib.Path(shot["video_path"]).resolve()
        else:
            generated = generated_lookup.get(shot_id)
            if not generated or not generated.get("video_path"):
                raise RuntimeError(f"Missing generated video for {shot_id} in generation manifest.")
            video_path = pathlib.Path(generated["video_path"]).resolve()

        probe = probe_video(video_path)
        contact_sheet_path = output_dir / f"{shot_id}-contact.jpg"
        build_contact_sheet(video_path, contact_sheet_path, probe["duration_seconds"])
        shot_details.append(
            {
                "shot_id": shot_id,
                "title": shot["title"],
                "video_path": str(video_path),
                "contact_sheet": str(contact_sheet_path),
                "probe": probe,
            }
        )

    pairwise = []
    for previous, current in zip(shot_details, shot_details[1:]):
        ssim = compute_ssim(previous["contact_sheet"], current["contact_sheet"])
        pairwise.append(
            {
                "from_shot": previous["shot_id"],
                "to_shot": current["shot_id"],
                "ssim": ssim,
            }
        )

    preview_path = output_dir / "sequence-preview.mp4"
    concat_path = build_preview([detail["video_path"] for detail in shot_details], preview_path)

    notes = []
    completeness = completeness_score(shot_details, notes)
    distinctness = distinctness_score(pairwise, args.max_adjacent_ssim, notes)
    packaging = packaging_score(preview_path.exists(), shot_details, notes)
    quality_signals = quality_signals_score(shot_details, notes)
    total_score = completeness + distinctness + packaging + quality_signals
    passed = total_score >= args.required_total_score and all(
        pair["ssim"] <= args.max_adjacent_ssim for pair in pairwise
    )

    report = {
        "passed": passed,
        "total_score": total_score,
        "scores": {
            "completeness": completeness,
            "distinctness": distinctness,
            "packaging": packaging,
            "quality_signals": quality_signals,
        },
        "thresholds": {
            "required_total_score": args.required_total_score,
            "max_adjacent_ssim": args.max_adjacent_ssim,
        },
        "preview_path": str(preview_path),
        "concat_list_path": str(concat_path),
        "pairwise": pairwise,
        "shots": shot_details,
        "notes": notes,
    }

    report_path = output_dir / "review-report.json"
    summary_path = output_dir / "review-summary.md"
    write_json(report_path, report)
    write_text(summary_path, build_markdown(report))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
