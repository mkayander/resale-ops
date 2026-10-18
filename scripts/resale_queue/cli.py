"""CLI for resale queue folders (any synced or local RESALE_ROOT)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .meta import build_index, init_item, write_index_files
from .photos import PhotoProcessConfig, prepare_item_photos, write_photo_report
from .sheets import push_from_env


def _root_from_args(args: argparse.Namespace) -> Path:
    return Path(args.root).expanduser().resolve()


def cmd_init(args: argparse.Namespace) -> None:
    item_dir = init_item(_root_from_args(args), args.slug)
    print(json.dumps({"item_dir": str(item_dir)}, ensure_ascii=False))


def cmd_prepare_photos(args: argparse.Namespace) -> None:
    root = _root_from_args(args)
    if not args.item_dir and not args.item:
        raise SystemExit("prepare-photos requires <item-id> or --item-dir")
    item_dir = root / "queue" / args.item if not args.item_dir else Path(args.item_dir).expanduser().resolve()
    if not item_dir.is_dir():
        raise SystemExit(f"Item directory not found: {item_dir}")
    config = PhotoProcessConfig(
        max_edge=args.max_edge,
        max_bytes=args.max_bytes,
        jpeg_quality=args.jpeg_quality,
    )
    report = prepare_item_photos(item_dir, config, move_originals=args.archive_originals)
    write_photo_report(item_dir, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def cmd_prepare_all(args: argparse.Namespace) -> None:
    root = _root_from_args(args)
    queue = root / "queue"
    if not queue.is_dir():
        raise SystemExit(f"Missing queue directory: {queue}")
    config = PhotoProcessConfig(
        max_edge=args.max_edge,
        max_bytes=args.max_bytes,
        jpeg_quality=args.jpeg_quality,
    )
    summaries = []
    for item_dir in sorted(queue.iterdir()):
        if not item_dir.is_dir():
            continue
        inbox = item_dir / "inbox"
        if not inbox.is_dir() or not any(inbox.iterdir()):
            continue
        report = prepare_item_photos(item_dir, config, move_originals=not args.no_archive)
        write_photo_report(item_dir, report)
        summaries.append({"item": item_dir.name, "files": len(report["files"])})
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


def cmd_index(args: argparse.Namespace) -> None:
    root = _root_from_args(args)
    rows = build_index(root)
    json_path, csv_path = write_index_files(root, rows)
    print(json.dumps({"count": len(rows), "json": str(json_path), "csv": str(csv_path)}, ensure_ascii=False))


def cmd_sheet_push(args: argparse.Namespace) -> None:
    root = _root_from_args(args)
    if args.credentials:
        from .sheets import push_index_to_sheet

        count = push_index_to_sheet(
            root,
            args.spreadsheet_id or "",
            args.sheet_name,
            Path(args.credentials).expanduser().resolve(),
        )
    else:
        count = push_from_env(root)
    print(json.dumps({"rows_pushed": count}, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resale queue: photos, index, optional Google Sheets push",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Resale root directory (cloud-synced or local path to Resale/)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init", help="Create a new queue item folder")
    init_p.add_argument("slug", help="Short slug, e.g. ikea-markus-chair")
    init_p.set_defaults(func=cmd_init)

    prep = sub.add_parser("prepare-photos", help="Sanitize/compress inbox photos into photos/post")
    prep.add_argument("item", nargs="?", help="Item folder name under queue/")
    prep.add_argument("--item-dir", help="Absolute path to item folder (overrides item)")
    prep.add_argument("--max-edge", type=int, default=2048)
    prep.add_argument("--max-bytes", type=int, default=2_000_000)
    prep.add_argument("--jpeg-quality", type=int, default=85)
    prep.add_argument(
        "--archive-originals", action="store_true",
        help="Opt in to storing a second copy under photos/original (not for cloud queue)",
    )
    prep.set_defaults(func=cmd_prepare_photos)

    prep_all = sub.add_parser("prepare-all", help="Prepare photos for every item with inbox files")
    prep_all.add_argument("--max-edge", type=int, default=2048)
    prep_all.add_argument("--max-bytes", type=int, default=2_000_000)
    prep_all.add_argument("--jpeg-quality", type=int, default=85)
    prep_all.add_argument("--archive-originals", action="store_true")
    prep_all.set_defaults(func=cmd_prepare_all)

    index_p = sub.add_parser("index", help="Rebuild queue-index.json and queue-index.csv")
    index_p.set_defaults(func=cmd_index)

    sheet = sub.add_parser("sheet-push", help="Push queue-index.json to Google Sheets (optional)")
    sheet.add_argument("--spreadsheet-id", help="Overrides RESALE_SHEET_ID")
    sheet.add_argument("--sheet-name", default="Queue")
    sheet.add_argument("--credentials", help="Service account JSON; else GOOGLE_APPLICATION_CREDENTIALS")
    sheet.set_defaults(func=cmd_sheet_push)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "sheet-push" and args.credentials and not args.spreadsheet_id:
        import os

        args.spreadsheet_id = os.environ.get("RESALE_SHEET_ID", "").strip()
    args.func(args)


if __name__ == "__main__":
    main()
