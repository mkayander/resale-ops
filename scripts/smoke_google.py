#!/usr/bin/env python3
"""Opt-in READ-ONLY Google smoke check for a dedicated sandbox.

Never used by mandatory CI or release gates. Never access resale production IDs.
"""
from __future__ import annotations

import json
import os
import socket
import sys
from pathlib import Path


def report(status: str, detail: str, *, warning: bool = False) -> None:
    message = f"Google smoke: {status} — {detail}"
    print(message, flush=True)
    if warning:
        print(f"::warning::{message}", flush=True)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as output:
            output.write(f"- **{status}**: {detail}\n")


def main() -> int:
    keys = ("GOOGLE_SMOKE_CREDENTIALS_JSON", "GOOGLE_SMOKE_FOLDER_ID",
            "GOOGLE_SMOKE_SPREADSHEET_ID")
    if not all(os.environ.get(key) for key in keys):
        report("SKIPPED", "Set sandbox-only GitHub Actions secrets to enable the manual check")
        return 0

    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError

        socket.setdefaulttimeout(12)
        credentials = Credentials.from_service_account_info(
            json.loads(os.environ["GOOGLE_SMOKE_CREDENTIALS_JSON"]),
            scopes=[
                "https://www.googleapis.com/auth/drive.metadata.readonly",
                "https://www.googleapis.com/auth/spreadsheets.readonly",
            ],
        )
        folder = build("drive", "v3", credentials=credentials, cache_discovery=False)
        info = folder.files().get(
            fileId=os.environ["GOOGLE_SMOKE_FOLDER_ID"],
            fields="id,mimeType", supportsAllDrives=True,
        ).execute(num_retries=0)
        if info.get("mimeType") != "application/vnd.google-apps.folder":
            report("FAIL", "Sandbox Drive ID is not a folder", warning=True)
            return 1

        sheets = build("sheets", "v4", credentials=credentials, cache_discovery=False)
        tab = os.environ.get("GOOGLE_SMOKE_TAB", "Queue").replace("'", "''")
        header = sheets.spreadsheets().values().get(
            spreadsheetId=os.environ["GOOGLE_SMOKE_SPREADSHEET_ID"],
            range=f"'{tab}'!A1:B1",
        ).execute(num_retries=0).get("values", [])
        if not header or header[0][:2] != ["id", "status"]:
            report("FAIL", "Sandbox Queue tab does not have expected headers", warning=True)
            return 1

        report("PASS", "Sandbox Drive folder and Sheets Queue headers readable")
        return 0
    except Exception as exc:
        # Errors here do not affect mandatory CI. Never log credential JSON.
        try:
            if isinstance(exc, HttpError):
                code = int(exc.resp.status)
                if code in (401, 403, 404):
                    report("CONFIG_ERROR", f"Sandbox access or resource problem (HTTP {code})", warning=True)
                    return 2
                report("INCONCLUSIVE", f"Google API HTTP {code}", warning=True)
                return 75
        except NameError:
            pass
        if isinstance(exc, (json.JSONDecodeError, ValueError, KeyError)):
            report("CONFIG_ERROR", "Invalid sandbox smoke credentials or settings", warning=True)
            return 2
        report("INCONCLUSIVE", f"External check failed ({type(exc).__name__})", warning=True)
        return 75


if __name__ == "__main__":
    sys.exit(main())
