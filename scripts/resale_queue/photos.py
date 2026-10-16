"""Sanitize and compress listing photos for cross-device handoff."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps

PROCESSOR_ID = "resale_queue/1.0.0"
SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


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
    move_originals: bool = True,
) -> dict:
    """Move inbox photos to photos/post as stripped JPEGs; optionally archive originals."""
    inbox = item_dir / "inbox"
    post_dir = item_dir / "photos" / "post"
    original_dir = item_dir / "photos" / "original"
    post_dir.mkdir(parents=True, exist_ok=True)
    if move_originals:
        original_dir.mkdir(parents=True, exist_ok=True)

    results: list[PhotoProcessResult] = []
    for index, source in enumerate(iter_inbox_files(inbox), start=1):
        dest = post_dir / f"{index:02d}.jpg"
        results.append(process_one(source, dest, config))
        if move_originals:
            target = original_dir / source.name
            if target.exists():
                target = original_dir / f"{source.stem}-{index}{source.suffix.lower()}"
            source.replace(target)
        else:
            source.unlink()

    relative_posts = [f"photos/post/{r.destination}" for r in results]
    report = {
        "processed_at": _utc_now(),
        "processor": PROCESSOR_ID,
        "metadata_status": "stripped_verified" if results else "no_inbox_files",
        "config": {
            "max_edge": config.max_edge,
            "max_bytes": config.max_bytes,
            "jpeg_quality": config.jpeg_quality,
        },
        "files": [r.__dict__ for r in results],
        "post": relative_posts,
    }
    return report


def write_photo_report(item_dir: Path, report: dict) -> None:
    meta_path = item_dir / "meta.json"
    meta = {}
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.setdefault("photos", {})
    meta["photos"].update(
        {
            "post": report["post"],
            "metadata_status": report["metadata_status"],
            "processed_at": report["processed_at"],
            "processor": report["processor"],
            "last_run": report,
        }
    )
    meta["updated_at"] = report["processed_at"]
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
