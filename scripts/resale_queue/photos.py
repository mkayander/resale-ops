"""Sanitize and compress listing photos for cross-device handoff."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps

PROCESSOR_ID = "resale_queue/1.0.0"
SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
_POST_NAME = re.compile(r"^(\d{2})\.jpg$", re.IGNORECASE)


@dataclass(frozen=True)
class PhotoProcessConfig:
    max_edge: int = 2048
    max_bytes: int = 2_000_000
    jpeg_quality: int = 85
    min_jpeg_quality: int = 60


@dataclass(frozen=True)
class PhotoProcessResult:
    source: str
    destination: str
    width: int
    height: int
    bytes_before: int
    bytes_after: int
    had_exif: bool


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_image(path: Path) -> Image.Image:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image)
        return image.convert("RGB")


def _save_jpeg(image: Image.Image, dest: Path, quality: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest, format="JPEG", quality=quality, optimize=True)


def _fit_max_edge(image: Image.Image, max_edge: int) -> Image.Image:
    width, height = image.size
    longest = max(width, height)
    if longest <= max_edge:
        return image
    scale = max_edge / longest
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def _encode_under_budget(image: Image.Image, dest: Path, config: PhotoProcessConfig) -> int:
    quality = config.jpeg_quality
    while quality >= config.min_jpeg_quality:
        _save_jpeg(image, dest, quality)
        size = dest.stat().st_size
        if size <= config.max_bytes:
            return size
        quality -= 5
    return dest.stat().st_size


def process_one(source: Path, dest: Path, config: PhotoProcessConfig) -> PhotoProcessResult:
    bytes_before = source.stat().st_size
    with Image.open(source) as probe:
        had_exif = bool(probe.getexif())
    image = _load_image(source)
    image = _fit_max_edge(image, config.max_edge)
    if dest.suffix.lower() not in {".jpg", ".jpeg"}:
        dest = dest.with_suffix(".jpg")
    bytes_after = _encode_under_budget(image, dest, config)
    return PhotoProcessResult(
        source=source.name,
        destination=dest.name,
        width=image.size[0],
        height=image.size[1],
        bytes_before=bytes_before,
        bytes_after=bytes_after,
        had_exif=had_exif,
    )


def list_existing_post_paths(post_dir: Path) -> list[str]:
    """Sorted `photos/post/NN.jpg` paths for numbered posting copies already on disk."""
    if not post_dir.is_dir():
        return []
    names = sorted(
        path.name
        for path in post_dir.iterdir()
        if path.is_file() and _POST_NAME.match(path.name)
    )
    return [f"photos/post/{name}" for name in names]


def next_post_index(post_dir: Path) -> int:
    highest = 0
    if post_dir.is_dir():
        for path in post_dir.iterdir():
            if not path.is_file():
                continue
            match = _POST_NAME.match(path.name)
            if match:
                highest = max(highest, int(match.group(1)))
    return highest + 1 if highest else 1


def iter_inbox_files(inbox: Path) -> list[Path]:
    if not inbox.is_dir():
        return []
    files = [
        path
        for path in sorted(inbox.iterdir())
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    ]
    return files


def prepare_item_photos(
    item_dir: Path,
    config: PhotoProcessConfig,
    *,
    move_originals: bool = False,
) -> dict:
    """Sanitize photos, verify outputs, then discard staging originals by default."""
    inbox = item_dir / "inbox"
    post_dir = item_dir / "photos" / "post"
    original_dir = item_dir / "photos" / "original"
    post_dir.mkdir(parents=True, exist_ok=True)
    if move_originals:
        original_dir.mkdir(parents=True, exist_ok=True)

    inbox_files = iter_inbox_files(inbox)
    existing_posts = list_existing_post_paths(post_dir)

    if not inbox_files:
        return {
            "processed_at": _utc_now(),
            "processor": PROCESSOR_ID,
            "metadata_status": "stripped_verified" if existing_posts else "no_inbox_files",
            "config": {
                "max_edge": config.max_edge,
                "max_bytes": config.max_bytes,
                "jpeg_quality": config.jpeg_quality,
            },
            "files": [],
            "post": existing_posts,
            "skipped": "empty_inbox",
        }

    results: list[PhotoProcessResult] = []
    start_index = next_post_index(post_dir)
    for offset, source in enumerate(inbox_files):
        index = start_index + offset
        dest = post_dir / f"{index:02d}.jpg"
        result = process_one(source, dest, config)
        # Read output back before deleting/moving the only source.
        with Image.open(dest) as check:
            if check.getexif() or check.size != (result.width, result.height):
                dest.unlink(missing_ok=True)
                raise ValueError(f"sanitized photo verification failed: {dest}")
        if result.bytes_after > config.max_bytes:
            dest.unlink(missing_ok=True)
            raise ValueError(f"photo exceeds requested byte limit: {dest}")
        results.append(result)
        if move_originals:
            target = original_dir / source.name
            if target.exists():
                target = original_dir / f"{source.stem}-{index}{source.suffix.lower()}"
            source.replace(target)
        else:
            source.unlink()

    new_posts = [f"photos/post/{r.destination}" for r in results]
    all_posts = existing_posts + new_posts
    report = {
        "processed_at": _utc_now(),
        "processor": PROCESSOR_ID,
        "metadata_status": "stripped_verified",
        "config": {
            "max_edge": config.max_edge,
            "max_bytes": config.max_bytes,
            "jpeg_quality": config.jpeg_quality,
        },
        "files": [r.__dict__ for r in results],
        "post": all_posts,
    }
    return report


def write_photo_report(item_dir: Path, report: dict) -> None:
    meta_path = item_dir / "meta.json"
    meta = {}
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    from .schema import normalize_meta, validate_meta
    meta = normalize_meta(meta)
    meta.setdefault("photos", {})
    meta["photos"].update(
        {
            "prepared_filenames": [Path(x).name for x in report["post"]],
            "post_count": len(report["post"]),
            "metadata_status": report["metadata_status"],
            "processed_at": report["processed_at"],
            "processor": report["processor"],
            "last_run": report,
        }
    )
    meta["updated_at"] = report["processed_at"]
    meta = validate_meta(meta)
    tmp = meta_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(meta_path)
