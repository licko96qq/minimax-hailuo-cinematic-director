#!/usr/bin/env python3

import argparse
import json
import pathlib
import subprocess

from minimax_common import read_json, write_json, write_text


def probe_media(path):
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def expected_video_duration(shots):
    return round(sum(float(shot.get("duration", 0) or 0) for shot in shots), 3)


def score_narrative_fit(package, notes):
    plan = package.get("music_plan", {})
    cue_sheet = plan.get("cue_sheet", [])
    score = 30
    if len(cue_sheet) != len(package["shots"]):
        score -= 10
        notes.append("配乐 cue 数量与镜头数量不一致。")
    if plan.get("vocal_policy") != "no-vocals":
        score -= 6
        notes.append("配乐方案没有锁定无人声策略。")
    if not plan.get("overall_arc"):
        score -= 6
        notes.append("配乐方案缺少清晰的整体弧线。")
    return max(score, 0)


def score_duration_fit(package, mixed_probe, music_summary, mix_summary, notes):
    target = float(package.get("music_plan", {}).get("target_video_duration_seconds", 0) or 0)
    expected = expected_video_duration(package["shots"])
    source_video_duration = float(mix_summary.get("video_duration_seconds", expected) or expected)
    mixed_duration = float(mixed_probe["format"]["duration"])
    source_duration = float((music_summary.get("duration_ms") or 0) / 1000.0)
    score = 30

    if abs(mixed_duration - source_video_duration) > 0.12:
        score -= 10
        notes.append(
            f"带配乐成片时长 {mixed_duration:.2f}s 与无声预览片时长 {source_video_duration:.2f}s 不一致。"
        )
    if target and abs(target - source_video_duration) > 0.6:
        score -= 3
        notes.append("配乐计划目标时长与实际生成视频时长存在偏差。")
    if source_duration < expected and not mix_summary.get("looped_music"):
        score -= 8
        notes.append("原始音乐短于视频，但混音记录没有表明已循环补足。")
    return max(score, 0)


def score_delivery_fit(mixed_probe, notes):
    score = 20
    audio_streams = [stream for stream in mixed_probe["streams"] if stream.get("codec_type") == "audio"]
    video_streams = [stream for stream in mixed_probe["streams"] if stream.get("codec_type") == "video"]
    if not video_streams:
        score = 0
        notes.append("成片缺少视频流。")
        return score
    if not audio_streams:
        score = 0
        notes.append("成片缺少音频流。")
        return score
    audio_stream = audio_streams[0]
    if int(audio_stream.get("sample_rate", 0) or 0) < 44100:
        score -= 5
        notes.append("成片音频采样率低于 44.1kHz。")
    if int(audio_stream.get("channels", 0) or 0) < 2:
        score -= 3
        notes.append("成片音频不是双声道。")
    return max(score, 0)


def score_risk_signals(music_summary, mix_summary, notes):
    score = 20
    bitrate = int(music_summary.get("bitrate", 0) or 0)
    volume = float(mix_summary.get("music_volume", 0) or 0)
    if bitrate and bitrate < 192000:
        score -= 5
        notes.append(f"原始音乐码率偏低（{bitrate} bps）。")
    if volume > 0.45:
        score -= 5
        notes.append("当前配乐音量偏高，若后续叠加旁白可能需要重新压低。")
    if volume < 0.18:
        score -= 4
        notes.append("当前配乐音量偏低，情绪支撑可能不足。")
    if mix_summary.get("trimmed_music"):
        notes.append("当前配乐按视频长度进行了裁切，请人工确认结尾落点是否自然。")
    return max(score, 0)


def build_markdown(report):
    lines = [
        "# 音画适配复盘报告",
        "",
        f"- 是否通过：{'是' if report['passed'] else '否'}",
        f"- 总分：{report['total_score']} / 100",
        f"- 叙事契合度：{report['scores']['narrative_fit']} / 30",
        f"- 时长契合度：{report['scores']['duration_fit']} / 30",
        f"- 交付完整性：{report['scores']['delivery_fit']} / 20",
        f"- 风险信号：{report['scores']['risk_signals']} / 20",
        "",
        "## 复盘意见",
        "",
    ]
    if report["notes"]:
        for note in report["notes"]:
            lines.append(f"- {note}")
    else:
        lines.append("- 音画适配通过，当前没有额外问题。")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Review the feasibility of soundtrack + video combination")
    parser.add_argument("--story-package", required=True)
    parser.add_argument("--mixed-video", required=True)
    parser.add_argument("--music-summary", required=True)
    parser.add_argument("--mix-summary", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    package = read_json(args.story_package)
    music_summary = read_json(args.music_summary)
    mix_summary = read_json(args.mix_summary)
    mixed_probe = probe_media(args.mixed_video)

    notes = []
    narrative_fit = score_narrative_fit(package, notes)
    duration_fit = score_duration_fit(package, mixed_probe, music_summary, mix_summary, notes)
    delivery_fit = score_delivery_fit(mixed_probe, notes)
    risk_signals = score_risk_signals(music_summary, mix_summary, notes)
    total_score = narrative_fit + duration_fit + delivery_fit + risk_signals
    passed = total_score >= 80 and delivery_fit > 0

    output_dir = pathlib.Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "passed": passed,
        "total_score": total_score,
        "scores": {
            "narrative_fit": narrative_fit,
            "duration_fit": duration_fit,
            "delivery_fit": delivery_fit,
            "risk_signals": risk_signals,
        },
        "mixed_video": str(pathlib.Path(args.mixed_video).resolve()),
        "music_summary": str(pathlib.Path(args.music_summary).resolve()),
        "mix_summary": str(pathlib.Path(args.mix_summary).resolve()),
        "notes": notes,
    }

    report_path = output_dir / "soundtrack-review-report.json"
    summary_path = output_dir / "soundtrack-review-summary.md"
    write_json(report_path, report)
    write_text(summary_path, build_markdown(report))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
