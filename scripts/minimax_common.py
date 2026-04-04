#!/usr/bin/env python3

import base64
import json
import mimetypes
import os
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request


def get_api_key():
    api_key = (
        os.environ.get("MINIMAX_API_KEY")
        or os.environ.get("MINIMAX_API_KEY_MAX")
        or os.environ.get("MINIMAX_API_KEY_PRO")
    )
    if not api_key:
        raise RuntimeError(
            "MiniMax API key not found in MINIMAX_API_KEY, MINIMAX_API_KEY_MAX, or MINIMAX_API_KEY_PRO."
        )
    return api_key


def get_base_url():
    return os.environ.get("MINIMAX_BASE_URL", "https://api.minimaxi.com").rstrip("/")


def skill_root():
    return pathlib.Path(__file__).resolve().parents[1]


def ensure_parent(path):
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)


def resolve_path(path_value, base_dir=None):
    path = pathlib.Path(path_value)
    if path.is_absolute():
        return path
    if base_dir:
        return (pathlib.Path(base_dir) / path).resolve()
    return path.resolve()


def read_text(relative_path):
    return (skill_root() / relative_path).read_text(encoding="utf-8")


def write_text(path, content):
    ensure_parent(path)
    pathlib.Path(path).write_text(content, encoding="utf-8")


def write_json(path, payload):
    ensure_parent(path)
    pathlib.Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def slugify(value):
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return re.sub(r"-{2,}", "-", normalized) or "run"


def post_json(api_path, payload):
    api_key = get_api_key()
    url = f"{get_base_url()}{api_path}"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(body)
        except json.JSONDecodeError:
            raise RuntimeError(f"HTTP {exc.code}: {body}") from exc


def get_json(api_path, params):
    api_key = get_api_key()
    query = urllib.parse.urlencode(params)
    url = f"{get_base_url()}{api_path}?{query}"
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(body)
        except json.JSONDecodeError:
            raise RuntimeError(f"HTTP {exc.code}: {body}") from exc


def download_file(url, output_path):
    ensure_parent(output_path)
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request) as response:
        pathlib.Path(output_path).write_bytes(response.read())


def check_success(response_json):
    if response_json.get("base_resp", {}).get("status_code") != 0:
        raise RuntimeError(json.dumps(response_json, ensure_ascii=False, indent=2))


def wait_for_video(task_id, timeout_seconds=900, interval_seconds=10):
    deadline = time.time() + timeout_seconds
    last_response = None
    while time.time() < deadline:
        _, response_json = get_json("/v1/query/video_generation", {"task_id": task_id})
        check_success(response_json)
        last_response = response_json
        status = response_json.get("status")
        if status == "Success":
            return response_json
        if status == "Fail":
            raise RuntimeError(json.dumps(response_json, ensure_ascii=False, indent=2))
        time.sleep(interval_seconds)
    raise TimeoutError(
        f"Timed out while waiting for video task {task_id}. Last response: "
        f"{json.dumps(last_response, ensure_ascii=False, indent=2)}"
    )


def retrieve_file(file_id):
    _, response_json = get_json("/v1/files/retrieve", {"file_id": file_id})
    check_success(response_json)
    return response_json


def sniff_mime_type(file_path):
    raw = pathlib.Path(file_path).read_bytes()
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if raw[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return mimetypes.guess_type(pathlib.Path(file_path).name)[0] or "application/octet-stream"


def file_to_data_url(path):
    file_path = pathlib.Path(path)
    mime_type = sniff_mime_type(file_path)
    encoded = base64.b64encode(file_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"
