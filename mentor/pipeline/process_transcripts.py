"""Transcribe reels (faster-whisper) and OCR carousel images (RapidOCR).

Reads mentor/inbox/<code>/ -> writes mentor/transcripts/<code>.md
Checkpointed: skips codes whose transcript file already exists.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

from rapidocr_onnxruntime import RapidOCR
from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parents[2]
INBOX = ROOT / "mentor" / "inbox"
TRANSCRIPTS = ROOT / "mentor" / "transcripts"
MODEL_SIZE = "small"


def load_meta() -> tuple[dict[str, dict], dict[str, dict]]:
    idx = json.loads((ROOT / "posts_index.json").read_text(encoding="utf-8"))
    man = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    by_code = {r["code"]: r for r in idx["records"]}
    themes = {it["code"]: it.get("themes", []) for it in man["items"]}
    return by_code, themes


def extract_audio(video: Path, wav: Path) -> bool:
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(video),
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", str(wav),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        return True
    except (subprocess.SubprocessError, OSError):
        return False


def ocr_images(ocr: RapidOCR, images: list[Path]) -> list[str]:
    slides: list[str] = []
    for img in images:
        result, _ = ocr(img)
        lines = [line[1] for line in (result or []) if line[1] and len(line[1].strip()) > 1]
        joined = "\n".join(lines).strip()
        if joined:
            slides.append(joined)
    return slides


def main() -> None:
    TRANSCRIPTS.mkdir(parents=True, exist_ok=True)
    by_code, themes = load_meta()
    dirs = sorted(d for d in INBOX.iterdir() if d.is_dir())
    todo = [d for d in dirs if not (TRANSCRIPTS / f"{d.name}.md").exists()]
    print(f"[transcribe] {len(todo)} posts to process of {len(dirs)}", flush=True)

    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    ocr = RapidOCR()

    for n, pdir in enumerate(todo, 1):
        code = pdir.name
        meta = by_code.get(code, {})
        video = pdir / "video.mp4"
        parts: list[str] = []
        header = (
            "---\n"
            f"code: {code}\n"
            f"date: {dt.datetime.utcfromtimestamp(meta['taken_at']).date().isoformat() if meta.get('taken_at') else ''}\n"
            f"themes: {', '.join(themes.get(code, []))}\n"
            "---\n\n"
        )
        cap = (meta.get("caption") or "").strip()
        if cap:
            parts.append("## Caption\n\n" + cap + "\n")

        if video.exists():
            wav = pdir / "audio.wav"
            if extract_audio(video, wav):
                seg_iter, info = model.transcribe(str(wav), vad_filter=True, beam_size=5)
                text = " ".join(s.text.strip() for s in seg_iter).strip()
                wav.unlink(missing_ok=True)
                dur = getattr(info, "duration", 0)
                print(f"[{n}/{len(todo)}] {code} speech={len(text)}ch dur={dur:.0f}s", flush=True)
                if text:
                    parts.append("## Transcript\n\n" + text + "\n")
                elif dur < 20:
                    print(f"[{n}/{len(todo)}] {code} low-info (<20s no speech)", flush=True)
            else:
                print(f"[{n}/{len(todo)}] {code} ffmpeg failed", flush=True)

        images = sorted(pdir.glob("img_*.jpg"))
        if images:
            try:
                slides = ocr_images(ocr, images)
            except Exception as exc:  # noqa: BLE001 - OCR must never kill the batch
                print(f"[{n}/{len(todo)}] {code} OCR error {exc}", flush=True)
                slides = []
            if slides:
                body = "\n\n---\n\n".join(slides)
                parts.append("## Slides (OCR)\n\n" + body + "\n")

        out = TRANSCRIPTS / f"{code}.md"
        out.write_text(header + "\n".join(parts), encoding="utf-8")
    print("[transcribe] all done", flush=True)


if __name__ == "__main__":
    sys.exit(main())
