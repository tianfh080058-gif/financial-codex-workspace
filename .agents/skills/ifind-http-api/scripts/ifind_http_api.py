#!/usr/bin/env python3
"""Small, token-safe client for the iFinD / 同花顺 HTTP API."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

import certifi
import requests


BASE_URL = os.environ.get("IFIND_BASE_URL", "https://quantapi.51ifind.com/api/v1").rstrip("/")

KEYCHAIN_SERVICES = {
    "refresh_token": "financial-codex-workspace.ifind.refresh_token",
    "access_token": "financial-codex-workspace.ifind.access_token",
    "login": "financial-codex-workspace.ifind.login",
}

KEYCHAIN_ACCOUNT = "financial-codex-workspace"

ENV_NAMES = {
    "refresh_token": "IFIND_REFRESH_TOKEN",
    "access_token": "IFIND_ACCESS_TOKEN",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_keychain_secret(service: str, account: str | None = None) -> str | None:
    if platform.system() != "Darwin":
        return None
    command = ["security", "find-generic-password"]
    if account:
        command.extend(["-a", account])
    command.extend(["-s", service, "-w"])
    try:
        proc = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    value = proc.stdout.strip()
    return value or None


def read_secret(kind: str) -> str | None:
    env_name = ENV_NAMES.get(kind)
    if env_name:
        value = os.environ.get(env_name)
        if value:
            return value
    service = KEYCHAIN_SERVICES.get(kind)
    if service:
        return read_keychain_secret(service, account=KEYCHAIN_ACCOUNT) or read_keychain_secret(service)
    return None


def post_json(endpoint: str, payload: dict[str, Any], headers: dict[str, str], timeout: float) -> dict[str, Any]:
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    try:
        response = requests.post(
            url,
            json=payload,
            headers={**headers, "Content-Type": "application/json", "Accept-Encoding": "gzip,deflate"},
            timeout=timeout,
            verify=certifi.where(),
        )
        try:
            parsed: Any = response.json()
        except ValueError:
            parsed = response.text
        return {
            "ok": 200 <= response.status_code < 300,
            "http_status": response.status_code,
            "url": url,
            "response": parsed,
            "error_type": None if 200 <= response.status_code < 300 else "HTTPError",
            "error": None if 200 <= response.status_code < 300 else response.text[:2000],
        }
    except requests.RequestException as exc:
        return {
            "ok": False,
            "url": url,
            "error_type": type(exc).__name__,
            "error": repr(exc),
        }
    except Exception as exc:  # noqa: BLE001 - CLI should return sanitized diagnostics.
        return {
            "ok": False,
            "url": url,
            "error_type": type(exc).__name__,
            "error": repr(exc),
        }


def summarize_response(response: Any) -> dict[str, Any]:
    if isinstance(response, dict):
        summary: dict[str, Any] = {
            "type": "object",
            "keys": sorted(map(str, response.keys())),
        }
        for key in ("errorcode", "errmsg", "datatype", "perf", "dataVol"):
            if key in response:
                summary[key] = response[key]
        tables = response.get("tables")
        if isinstance(tables, list):
            summary["table_count"] = len(tables)
            table_summaries = []
            for table in tables[:5]:
                if isinstance(table, dict):
                    table_summary = {
                        "keys": sorted(map(str, table.keys())),
                        "thscode": table.get("thscode"),
                    }
                    table_data = table.get("table")
                    if isinstance(table_data, dict):
                        table_summary["table_keys"] = sorted(map(str, table_data.keys()))
                    elif isinstance(table_data, list):
                        table_summary["row_count"] = len(table_data)
                    table_summaries.append(table_summary)
            summary["tables"] = table_summaries
        return summary
    if isinstance(response, list):
        return {"type": "array", "row_count": len(response)}
    return {"type": type(response).__name__, "preview": str(response)[:500]}


def emit(payload: dict[str, Any]) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("status") != "fail" else 1


def command_check_env(_args: argparse.Namespace) -> int:
    refresh_token = read_secret("refresh_token")
    access_token = read_secret("access_token")
    return emit(
        {
            "checked_at_utc": utc_now(),
            "status": "ok",
            "base_url": BASE_URL,
            "python": sys.executable,
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "credentials": {
                "refresh_token_found": bool(refresh_token),
                "access_token_found": bool(access_token),
                "refresh_token_source": "env_or_keychain" if refresh_token else None,
                "access_token_source": "env_or_keychain" if access_token else None,
            },
        }
    )


def command_get_access_token(args: argparse.Namespace) -> int:
    refresh_token = read_secret("refresh_token")
    if not refresh_token:
        return emit(
            {
                "checked_at_utc": utc_now(),
                "status": "fail",
                "endpoint": "get_access_token",
                "missing": "IFIND_REFRESH_TOKEN or macOS Keychain refresh_token",
            }
        )
    raw = post_json(
        "get_access_token",
        {},
        {"refresh_token": refresh_token},
        timeout=args.timeout,
    )
    response_summary = summarize_response(raw.get("response"))
    token_present = False
    if isinstance(raw.get("response"), dict):
        data = raw["response"].get("data")
        token_present = isinstance(data, dict) and bool(data.get("access_token"))
    return emit(
        {
            "checked_at_utc": utc_now(),
            "status": "ok" if raw.get("ok") and token_present else "fail",
            "endpoint": "get_access_token",
            "http_status": raw.get("http_status"),
            "access_token_returned": token_present,
            "response_summary": response_summary,
            "error_type": raw.get("error_type"),
            "error": raw.get("error"),
        }
    )


def request_with_access_token(endpoint: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    access_token = read_secret("access_token")
    if not access_token:
        return {
            "checked_at_utc": utc_now(),
            "status": "fail",
            "endpoint": endpoint,
            "missing": "IFIND_ACCESS_TOKEN or macOS Keychain access_token",
        }
    raw = post_json(endpoint, payload, {"access_token": access_token}, timeout=timeout)
    return {
        "checked_at_utc": utc_now(),
        "status": "ok" if raw.get("ok") else "fail",
        "endpoint": endpoint,
        "parameters": payload,
        "http_status": raw.get("http_status"),
        "response_summary": summarize_response(raw.get("response")),
        "error_type": raw.get("error_type"),
        "error": raw.get("error"),
    }


def command_smoke_test(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {"codes": args.codes, "indicators": args.indicators}
    if args.functionpara:
        payload["functionpara"] = json.loads(args.functionpara)
    return emit(request_with_access_token("real_time_quotation", payload, timeout=args.timeout))


def command_history(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "codes": args.codes,
        "indicators": args.indicators,
        "startdate": args.startdate,
        "enddate": args.enddate,
    }
    if args.functionpara:
        payload["functionpara"] = json.loads(args.functionpara)
    return emit(request_with_access_token("cmd_history_quotation", payload, timeout=args.timeout))


def command_request(args: argparse.Namespace) -> int:
    payload = json.loads(args.payload)
    return emit(request_with_access_token(args.endpoint, payload, timeout=args.timeout))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Token-safe iFinD HTTP API client.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_env = subparsers.add_parser("check-env", help="Check local environment and credential presence.")
    check_env.set_defaults(func=command_check_env)

    get_token = subparsers.add_parser("get-access-token", help="Validate refresh_token by requesting current access_token.")
    get_token.add_argument("--timeout", type=float, default=20.0)
    get_token.set_defaults(func=command_get_access_token)

    smoke = subparsers.add_parser("smoke-test", help="Call real_time_quotation with sanitized output.")
    smoke.add_argument("--codes", default="300033.SZ")
    smoke.add_argument("--indicators", default="open,high,low,latest")
    smoke.add_argument("--functionpara")
    smoke.add_argument("--timeout", type=float, default=20.0)
    smoke.set_defaults(func=command_smoke_test)

    history = subparsers.add_parser("history", help="Call cmd_history_quotation with sanitized output.")
    history.add_argument("--codes", required=True)
    history.add_argument("--indicators", required=True)
    history.add_argument("--startdate", required=True)
    history.add_argument("--enddate", required=True)
    history.add_argument("--functionpara")
    history.add_argument("--timeout", type=float, default=20.0)
    history.set_defaults(func=command_history)

    request = subparsers.add_parser("request", help="Call an arbitrary documented endpoint with a JSON payload.")
    request.add_argument("--endpoint", required=True)
    request.add_argument("--payload", required=True)
    request.add_argument("--timeout", type=float, default=20.0)
    request.set_defaults(func=command_request)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except json.JSONDecodeError as exc:
        return emit({"checked_at_utc": utc_now(), "status": "fail", "error_type": "JSONDecodeError", "error": str(exc)})


if __name__ == "__main__":
    raise SystemExit(main())
