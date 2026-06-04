from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any


DEFAULT_API_BASE = "http://127.0.0.1:8000"
DEFAULT_PROVIDER_NAME = "Ofox UI Default"
DEFAULT_OFOX_BASE_URL = "https://api.ofox.ai/v1"
DEFAULT_OFOX_MODEL = "gpt-image-2"


def compact_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def request_json(
    method: str,
    api_base: str,
    path: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{api_base.rstrip('/')}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed: HTTP {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{method} {path} failed: {exc.reason}") from exc
    return json.loads(body or "{}")


def ofox_config(base_url: str = DEFAULT_OFOX_BASE_URL, model: str = DEFAULT_OFOX_MODEL) -> dict[str, str]:
    return {
        "api_key_env": "OFOX_API_KEY",
        "base_url": base_url,
        "model": model,
    }


def default_provider_payload(name: str, base_url: str = DEFAULT_OFOX_BASE_URL, model: str = DEFAULT_OFOX_MODEL) -> dict[str, Any]:
    return {
        "name": name,
        "type": "ofox",
        "enabled": True,
        "config_json": compact_json(ofox_config(base_url=base_url, model=model)),
    }


def ensure_default_ofox_provider(
    api_base: str,
    name: str = DEFAULT_PROVIDER_NAME,
    base_url: str = DEFAULT_OFOX_BASE_URL,
    model: str = DEFAULT_OFOX_MODEL,
) -> dict[str, Any]:
    providers = request_json("GET", api_base, "/ai_providers").get("items", [])
    payload = default_provider_payload(name, base_url=base_url, model=model)
    for provider in providers:
        if provider.get("name") == name and provider.get("type") == "ofox":
            expected_config = compact_json(ofox_config(base_url=base_url, model=model))
            if provider.get("enabled") is True and provider.get("config_json") == expected_config:
                return provider
            return request_json("PUT", api_base, f"/ai_providers/{provider['id']}", payload)
    return request_json("POST", api_base, "/ai_providers", payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or update the default Ofox provider without storing secrets.")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help=f"Backend API base URL. Default: {DEFAULT_API_BASE}")
    parser.add_argument("--name", default=DEFAULT_PROVIDER_NAME, help=f"Provider name. Default: {DEFAULT_PROVIDER_NAME}")
    parser.add_argument("--base-url", default=DEFAULT_OFOX_BASE_URL, help=f"Ofox base URL. Default: {DEFAULT_OFOX_BASE_URL}")
    parser.add_argument("--model", default=DEFAULT_OFOX_MODEL, help=f"Ofox image model. Default: {DEFAULT_OFOX_MODEL}")
    args = parser.parse_args()

    try:
        provider = ensure_default_ofox_provider(args.api_base, args.name, base_url=args.base_url, model=args.model)
        health = request_json("GET", args.api_base, f"/ai_providers/{provider['id']}/health")
    except RuntimeError as exc:
        print(f"[fail] {exc}", file=sys.stderr)
        return 1

    print("[ok] Ofox provider is ready")
    print(f"provider_id={provider['id']}")
    print(f"name={provider['name']}")
    print(f"type={provider['type']}")
    print(f"config_json={provider['config_json']}")
    print(f"health={health['status']} / {health['message']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
