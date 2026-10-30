"""ComfyUI client: upload → /api/prompt → polling → download, with a timeout at each step.

Two backends, same API (/api prefix):
    local ComfyUI: COMFY_URL=http://127.0.0.1:8188 (default), no key;
    Comfy Cloud  : COMFY_URL=https://cloud.comfy.org and COMFY_API_KEY=<key>.
The variables can also be set in .env at the repo root (template: .env.example).

Usage (runs a real job, so it consumes credits on Comfy Cloud):
    python -m pipeline.comfy_client edit photo.jpg --preset vampire -o .tmp/jobs/job_x/
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from dataclasses import dataclass, replace
from pathlib import Path

import httpx

WORKFLOWS_DIR = Path(__file__).resolve().parent.parent / "workflows"


def load_dotenv(path: Path = Path(__file__).resolve().parent.parent / ".env") -> None:
    """Loads the KEY=value lines of the .env at the repo root; a variable already set in the environment takes precedence."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.strip().partition("=")
        if sep and not key.startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_dotenv()

# Variable inputs of each workflow: name → (node id, input), ids from the API-format JSON.
SLOTS = {
    "edit": {"image": ("54", "image"), "prompt": ("4", "text"), "seed": ("7", "seed"), "prefix": ("9", "filename_prefix")},
    # LTX 2.5 in two passes: half-resolution latent (356), x2 upscale; video and audio in a single latent.
    "i2v": {
        "image": ("395", "image"),
        "prompt": ("364", "text"),
        "seed": ("339", "noise_seed"),
        "width": ("356", "width"),
        "height": ("356", "height"),
        "length": ("356", "length"),
        "audio_length": ("366", "frames_number"),
        "prefix": ("75", "filename_prefix"),
    },
}
I2V_FPS = 24  # fixed in workflows/i2v.json (365, 366, 370)
I2V_MEGAPIXELS = 1.2  # final resolution; 960×1280 at 3:4
MAX_RATIO = 3  # widest accepted aspect ratio, either orientation


def i2v_size(width: int, height: int, megapixels: float = I2V_MEGAPIXELS) -> tuple[int, int]:
    """Final size at the image's aspect ratio, a multiple of 64 so that pass 1 (half size) stays a multiple of 32."""
    ratio = width / height
    if not 1 / MAX_RATIO <= ratio <= MAX_RATIO:  # beyond, one side rounds down to 0
        raise ValueError(f"aspect ratio {width}×{height} outside 1:{MAX_RATIO}..{MAX_RATIO}:1")
    w = round((megapixels * 1e6 * ratio) ** 0.5 / 64) * 64
    h = round((megapixels * 1e6 / ratio) ** 0.5 / 64) * 64
    return w, h


class ComfyError(RuntimeError):
    pass


class ComfyTimeout(ComfyError):
    pass


@dataclass(frozen=True)
class Timeouts:
    http: float = 30.0  # each request
    transfer: float = 120.0  # upload / download of one file
    edit: float = 300.0  # full job, queue time included
    i2v: float = 900.0
    poll: float = 2.0  # polling interval


@dataclass(frozen=True)
class JobResult:
    prompt_id: str
    files: list[Path]  # local copies
    seed: int | None = None  # actual seed, to replay a job


def resolve_seed(seed: int | None) -> int:
    """Random seed by default: a fixed seed gives the same draw for every photo, and seed 42
    made Vampire and Witch nearly identical to the input (no-op, Oct 28)."""
    return random.randrange(2**32) if seed is None else seed


def load_workflow(name: str, **values: object) -> dict:
    graph = json.loads((WORKFLOWS_DIR / f"{name}.json").read_text(encoding="utf-8"))
    for key, value in values.items():
        node, field = SLOTS[name][key]
        graph[node]["inputs"][field] = value
    return graph


def output_files(outputs: dict) -> list[dict]:
    """Final files of a job ({node: {"images"|"videos"|…: [{filename, subfolder, type}]}}), excluding previews."""
    return [
        f
        for node in outputs.values()
        for items in node.values()
        if isinstance(items, list)
        for f in items
        if isinstance(f, dict) and "filename" in f and f.get("type", "output") == "output"
    ]


class ComfyClient:
    def __init__(self, url: str | None = None, api_key: str | None = None, timeouts: Timeouts = Timeouts()):
        self.url = (url or os.environ.get("COMFY_URL") or "http://127.0.0.1:8188").rstrip("/")
        self.api_key = api_key or os.environ.get("COMFY_API_KEY") or None
        self.cloud = self.api_key is not None
        self.timeouts = timeouts
        # No follow_redirects: on Cloud, /api/view redirects to a signed URL that must not receive the key.
        headers = {"X-API-Key": self.api_key} if self.api_key else {}
        self.http = httpx.Client(base_url=self.url, headers=headers, timeout=timeouts.http)
        # Recorded as soon as they exist, so that purge() also covers jobs that failed midway.
        self.uploads: list[str] = []  # images uploaded to input/
        self.prompt_ids: list[str] = []
        self.remote: list[dict] = []  # ComfyUI-side outputs ({filename, subfolder, type})

    def __enter__(self) -> ComfyClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.http.close()

    @staticmethod
    def _check(r: httpx.Response) -> httpx.Response:
        if r.is_error:
            raise ComfyError(f"{r.request.method} {r.request.url.path} → {r.status_code} : {r.text[:500]}")
        return r

    def upload_image(self, path: Path, name: str | None = None) -> str:
        """Uploads an image to input/; `name` avoids collisions between users locally."""
        with path.open("rb") as f:
            r = self.http.post(
                "/api/upload/image",
                files={"image": (name or path.name, f)},
                data={"type": "input", "overwrite": "true"},
                timeout=self.timeouts.transfer,
            )
        data = self._check(r).json()
        uploaded = f"{data['subfolder']}/{data['name']}" if data.get("subfolder") else data["name"]
        self.uploads.append(uploaded)
        return uploaded

    def submit(self, graph: dict) -> str:
        data = self._check(self.http.post("/api/prompt", json={"prompt": graph})).json()
        if data.get("prompt_id"):
            self.prompt_ids.append(data["prompt_id"])
        if data.get("node_errors"):
            raise ComfyError(f"workflow rejected: {data['node_errors']}")
        return data["prompt_id"]

    def _poll(self, prompt_id: str) -> dict | None:
        """Outputs if the job is done, None if still running; ComfyError if it failed."""
        if self.cloud:
            job = self._check(self.http.get(f"/api/jobs/{prompt_id}")).json()
            if job["status"] == "completed":
                return job.get("outputs") or {}
            if job["status"] in ("failed", "cancelled"):
                raise ComfyError(f"job {prompt_id} {job['status']}: {job.get('execution_error')}")
            return None
        entry = self._check(self.http.get(f"/api/history/{prompt_id}")).json().get(prompt_id)
        if not entry:  # still queued or running
            return None
        status = entry.get("status", {})
        if status.get("status_str") == "error":
            raise ComfyError(f"job {prompt_id} failed: {status.get('messages')}")
        return entry.get("outputs", {}) if status.get("completed") else None

    def wait(self, prompt_id: str, timeout: float) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                outputs = self._poll(prompt_id)
            except httpx.TransportError:  # transient network failure: retry until the deadline
                outputs = None
            if outputs is not None:
                return outputs
            time.sleep(self.timeouts.poll)
        self.cancel(prompt_id)
        raise ComfyTimeout(f"job {prompt_id} not finished after {timeout:.0f} s, cancelled")

    def cancel(self, prompt_id: str) -> None:
        """Best effort: removes the job from the queue and interrupts it if running."""
        try:
            self.http.post("/api/queue", json={"delete": [prompt_id]})
            self.http.post("/api/interrupt", json={"prompt_id": prompt_id})
        except httpx.HTTPError:
            pass

    def download(self, file: dict, dest_dir: Path) -> Path:
        params = {"filename": file["filename"], "subfolder": file.get("subfolder", ""), "type": file.get("type", "output")}
        r = self.http.get("/api/view", params=params, timeout=self.timeouts.transfer)
        if r.is_redirect:  # Cloud: signed URL, fetched without the key
            r = httpx.get(r.headers["location"], timeout=self.timeouts.transfer)
        self._check(r)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / Path(file["filename"]).name
        dest.write_bytes(r.content)
        return dest

    def run(self, graph: dict, dest_dir: Path, timeout: float) -> JobResult:
        prompt_id = self.submit(graph)
        files = output_files(self.wait(prompt_id, timeout))
        self.remote += files
        if not files:
            raise ComfyError(f"job {prompt_id} finished without an output file")
        return JobResult(prompt_id, [self.download(f, dest_dir) for f in files])

    def purge(self) -> None:
        """GDPR, best effort: removes this client's jobs from the history, failed ones included; locally, also
        deletes their files in input/ and output/ if COMFY_DIR points to the ComfyUI folder. On Comfy Cloud,
        file retention is up to the service."""
        if self.prompt_ids:
            try:
                self.http.post("/api/history", json={"delete": self.prompt_ids})
            except httpx.HTTPError:
                pass
        root = os.environ.get("COMFY_DIR")
        if not self.cloud and root:
            inputs, outputs = Path(root, "input").resolve(), Path(root, "output").resolve()
            paths = [(inputs, inputs / name) for name in self.uploads]
            paths += [(outputs, outputs / f.get("subfolder", "") / f["filename"]) for f in self.remote]
            for base, path in paths:
                path = path.resolve()  # follows symlinks and "..": names come from the backend
                if path.is_relative_to(base) and path != base:
                    path.unlink(missing_ok=True)
        self.uploads, self.prompt_ids, self.remote = [], [], []

    def edit(
        self, photo: Path, prompt: str, dest_dir: Path, seed: int | None = None, upload_name: str | None = None
    ) -> JobResult:
        seed = resolve_seed(seed)
        image = self.upload_image(photo, upload_name)
        graph = load_workflow("edit", image=image, prompt=prompt, seed=seed)
        return replace(self.run(graph, dest_dir, self.timeouts.edit), seed=seed)

    def i2v(
        self, image: Path, prompt: str, dest_dir: Path, seconds: int = 5, seed: int | None = None, upload_name: str | None = None
    ) -> JobResult:
        from PIL import Image  # Gradio dependency

        with Image.open(image) as im:
            w, h = i2v_size(*im.size)
        seed = resolve_seed(seed)
        frames = seconds * I2V_FPS + 1  # LTX expects 8k + 1 frames
        uploaded = self.upload_image(image, upload_name)
        graph = load_workflow(
            "i2v",
            image=uploaded,
            prompt=prompt,
            seed=seed,
            width=w // 2,
            height=h // 2,
            length=frames,
            audio_length=frames,
        )
        return replace(self.run(graph, dest_dir, self.timeouts.i2v), seed=seed)


def main() -> None:
    from pipeline.faces import count_faces
    from pipeline.presets import PRESETS

    sys.stdout.reconfigure(encoding="utf-8")  # Windows cp1252 console: the docstring contains "→"
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("edit", help="photo → Halloween image (FLUX 3 Klein)")
    e.add_argument("photo", type=Path)
    e.add_argument("--preset", choices=PRESETS, default="vampire")
    e.add_argument("--seed", type=int, help="default: random")
    e.add_argument("-o", "--out", type=Path, required=True, help="output folder")
    v = sub.add_parser("i2v", help="Halloween image → video (LTX 2.5)")
    v.add_argument("image", type=Path)
    v.add_argument("--preset", choices=PRESETS, default="vampire")
    v.add_argument("--seconds", type=int, default=5)
    v.add_argument("--seed", type=int, help="default: random")
    v.add_argument("-o", "--out", type=Path, required=True, help="output folder")
    a = p.parse_args()
    with ComfyClient() as client:
        if a.cmd == "edit":
            n = count_faces(a.photo)
            print(f"{n} face(s) detected")
            res = client.edit(a.photo, PRESETS[a.preset].edit_prompt_for(n), a.out, a.seed)
        else:
            res = client.i2v(a.image, PRESETS[a.preset].motion_prompt, a.out, a.seconds, a.seed)
    print(res.prompt_id, f"seed {res.seed}", *res.files, sep="\n")


if __name__ == "__main__":
    main()
