"""Halloween Switch: group photo → "before → flash → after" MP4 (FLUX 3 Klein + LTX 2.5 via ComfyUI).

Run:
    python app.py                                                   # ComfyUI local, http://127.0.0.1:8188
    COMFY_URL=https://cloud.comfy.org COMFY_API_KEY=<key> python app.py   # Comfy Cloud
    python app.py --mock                                            # no ComfyUI: tint + still-image reveal
COMFY_DIR=<ComfyUI folder> enables, locally, purging its input/ and output/ after each job.
APP_AUTH=<user>:<password> requires a login (e.g. on a Hugging Face Space, see space/).
"""

from __future__ import annotations

import argparse
import os
import shutil
import tempfile
import threading
import time
import uuid
from pathlib import Path

import gradio as gr
import httpx
from PIL import Image, ImageChops, ImageOps

from pipeline.comfy_client import MAX_RATIO, ComfyClient, ComfyError, JobResult
from pipeline.faces import count_faces
from pipeline.presets import PRESETS
from pipeline.reveal import FORMATS, RevealConfig, make_reveal

JOBS_DIR = Path(tempfile.gettempdir()) / "halloween-switch"  # outside the repo, one subfolder per job
RETENTION = 30 * 60  # s: lifetime of uploads and outputs (app and Gradio cache)
MAX_SIDE = 2048  # px; Klein works at 1 MP
MAX_FILE_SIZE = "20mb"  # per upload, enforced by Gradio before any decoding
# Pillow refuses images above 2× this (60 MP) as decompression bombs, Gradio's own preprocessing included.
Image.MAX_IMAGE_PIXELS = 30_000_000


def purge_old_jobs() -> None:
    cutoff = time.time() - RETENTION
    for job in JOBS_DIR.glob("*/"):
        if job.stat().st_mtime < cutoff:
            shutil.rmtree(job, ignore_errors=True)


def purge_loop() -> None:
    while True:
        purge_old_jobs()
        time.sleep(RETENTION / 3)


def normalize(photo: Path, dest: Path) -> Path:
    """Rotates per EXIF, then re-encodes as JPEG without metadata (GPS, camera)."""
    with Image.open(photo) as im:
        if max(im.size) > MAX_RATIO * min(im.size):
            raise gr.Error(f"Photo too elongated: keep the aspect ratio within {MAX_RATIO}:1.")
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((MAX_SIDE, MAX_SIDE))
        im.save(dest, "JPEG", quality=95)
    return dest


class MockClient:
    """Replaces ComfyClient (--mock): free UI demo. Edit = orange-tinted photo, I2V = that same image
    (make_reveal then falls back to the slow zoom + flicker)."""

    def __enter__(self) -> MockClient:
        return self

    def __exit__(self, *exc: object) -> None:
        pass

    def edit(self, photo: Path, prompt: str, dest_dir: Path, upload_name: str | None = None) -> JobResult:
        time.sleep(1)
        with Image.open(photo) as im:
            tinted = ImageChops.multiply(im.convert("RGB"), Image.new("RGB", im.size, (255, 140, 40)))
            out = dest_dir / "mock_edit.png"
            tinted.save(out)
        return JobResult("mock-edit", [out])

    def i2v(self, image: Path, prompt: str, dest_dir: Path, upload_name: str | None = None) -> JobResult:
        time.sleep(1)
        return JobResult("mock-i2v", [image])

    def purge(self) -> None:
        pass


Client: type[ComfyClient] | type[MockClient] = ComfyClient


def read_auth() -> tuple[str, str] | None:
    """APP_AUTH=user:password guards access (public Space or Railway URL, each run consumes Comfy Cloud credits).
    Fails closed: a malformed value, or a hosted app without APP_AUTH, stops the launch instead of opening the app."""
    value = os.environ.get("APP_AUTH", "")
    if not value:
        if (os.environ.get("SPACE_ID") or os.environ.get("RAILWAY_PROJECT_ID")) and Client is ComfyClient:
            raise SystemExit("APP_AUTH=<user>:<password> is required on a Hugging Face Space or Railway.")
        return None
    user, _, pwd = value.partition(":")
    if not (user and pwd):
        raise SystemExit("APP_AUTH must be <user>:<password>, both non-empty.")
    return user, pwd


def generate(photo: str | None, preset_key: str, fmt: str, progress=gr.Progress()) -> tuple[Path, Path]:
    if not photo:
        raise gr.Error("Upload a group photo first.")
    job_id = uuid.uuid4().hex[:12]
    job = JOBS_DIR / job_id
    job.mkdir(parents=True)
    preset = PRESETS[preset_key]
    try:
        with Client() as client:
            try:
                progress(0.05, desc="1/3 Halloween makeover (FLUX 3 Klein)")
                before = normalize(Path(photo), job / "before.jpg")
                prompt = preset.edit_prompt_for(count_faces(before))
                still = client.edit(before, prompt, job, upload_name=f"hs_{job_id}.jpg").files[0]

                progress(0.3, desc="2/3 Animation (LTX 2.5), takes a few minutes")
                try:
                    after = client.i2v(still, preset.motion_prompt, job, upload_name=f"hs_{job_id}_edit.png").files[0]
                except (ComfyError, httpx.HTTPError) as e:  # fallback: FFmpeg slow zoom + flicker on the still
                    gr.Warning(f"Animation failed, falling back to a still-image reveal. ({e})")
                    after = still

                progress(0.9, desc="3/3 Reveal (FFmpeg)")
                out = make_reveal(before, after, job / f"halloween_{preset_key}.mp4", cfg=RevealConfig(fmt=fmt))
            except (ComfyError, httpx.HTTPError) as e:
                raise gr.Error(f"ComfyUI error: {e}") from e
            finally:
                client.purge()  # every upload and job of this run, failed ones included
    except BaseException:
        shutil.rmtree(job, ignore_errors=True)  # no result to show: drop the intermediate files now
        raise
    for f in job.iterdir():  # keep only what the UI displays
        if f not in (out, still):
            f.unlink()
    return out, still


with gr.Blocks(title="Halloween Switch", delete_cache=(RETENTION // 3, RETENTION)) as demo:
    gr.Markdown(
        "# 🎃 Halloween Switch\n"
        "Upload a group photo and pick a costume: you get a short **before → flash → after** video, ready to share."
    )
    with gr.Row():
        with gr.Column():
            photo = gr.Image(type="filepath", sources=["upload"], label="Group photo")
            preset = gr.Radio([(p.label, p.key) for p in PRESETS.values()], value="vampire", label="Costume")
            fmt = gr.Radio(list(FORMATS), value="auto", label="Format")
            go = gr.Button("Switch!", variant="primary")
            gr.Markdown(f"Photos and results are deleted automatically after {RETENTION // 60} minutes.")
        with gr.Column():
            video = gr.Video(label="Reveal", autoplay=True)
            still = gr.Image(type="filepath", label="Halloween photo")
    go.click(generate, [photo, preset, fmt], [video, still])


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mock", action="store_true", help="no ComfyUI: fake edit (tint) and still-image reveal")
    if p.parse_args().mock:
        Client = MockClient
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    threading.Thread(target=purge_loop, daemon=True).start()
    demo.queue(default_concurrency_limit=1, max_size=20).launch(
        allowed_paths=[str(JOBS_DIR)], auth=read_auth(), max_file_size=MAX_FILE_SIZE
    )
