"""Importable, token-safe wrapper around the project iFinD HTTP helper."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

from .common import PROJECT_ROOT, utc_now


class IfindHttpClient:
    """Small wrapper that reuses the existing iFinD script without printing secrets."""

    def __init__(self, script_path: Path | None = None, timeout: float = 20.0) -> None:
        self.script_path = script_path or PROJECT_ROOT / ".agents" / "skills" / "ifind-http-api" / "scripts" / "ifind_http_api.py"
        self.timeout = timeout
        self._module: ModuleType | None = None

    def _load_module(self) -> ModuleType:
        if self._module is not None:
            return self._module
        spec = importlib.util.spec_from_file_location("workspace_ifind_http_api", self.script_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot import iFinD client from {self.script_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self._module = module
        return module

    def credential_status(self) -> dict[str, Any]:
        module = self._load_module()
        return {
            "checked_at": utc_now(),
            "refresh_token_found": bool(module.read_secret("refresh_token")),
            "access_token_found": bool(module.read_secret("access_token")),
            "secret_policy": "tokens are read from env/keychain and never returned by trading_core",
        }

    def request_raw(self, endpoint: str, payload: dict[str, Any], timeout: float | None = None) -> dict[str, Any]:
        module = self._load_module()
        access_token = module.read_secret("access_token")
        if not access_token:
            return {
                "checked_at": utc_now(),
                "status": "fail",
                "endpoint": endpoint,
                "missing": "IFIND_ACCESS_TOKEN or macOS Keychain access_token",
            }
        raw = module.post_json(endpoint, payload, {"access_token": access_token}, timeout=timeout or self.timeout)
        return {
            "checked_at": utc_now(),
            "status": "ok" if raw.get("ok") else "fail",
            "endpoint": endpoint,
            "parameters": payload,
            "http_status": raw.get("http_status"),
            "response": raw.get("response"),
            "error_type": raw.get("error_type"),
            "error": raw.get("error"),
        }

    def history_quote(
        self,
        *,
        codes: str,
        indicators: str,
        startdate: str,
        enddate: str,
        functionpara: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "codes": codes,
            "indicators": indicators,
            "startdate": startdate,
            "enddate": enddate,
        }
        if functionpara:
            payload["functionpara"] = functionpara
        return self.request_raw("cmd_history_quotation", payload, timeout=timeout)
