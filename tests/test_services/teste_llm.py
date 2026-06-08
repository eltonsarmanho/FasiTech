from __future__ import annotations

import os
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest
import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=True)


@dataclass(frozen=True)
class LLMRuntime:
    provider: str
    model: str
    api_key: str = ""
    base_url: str = ""


def _load_llm_config_module() -> Any:
    candidates = (
        "backend.config.LLMConfig",
        "config.LLMConfig",
        "LLMConfig",
    )

    for module_name in candidates:
        try:
            return import_module(module_name)
        except Exception:
            continue

    pytest.skip("backend/config/LLMConfig.py não encontrado no projeto.")


def _load_settings() -> Any | None:
    try:
        return import_module("backend.config.settings").settings
    except Exception:
        return None


def _env_or_setting(settings: Any | None, env_name: str, setting_name: str | None = None) -> str:
    value = os.getenv(env_name)
    if value:
        return value

    if settings is None:
        return ""

    return str(getattr(settings, setting_name or env_name.lower(), "") or "")


def _resolve_runtime(config: Any) -> LLMRuntime:
    settings = _load_settings()

    google_api_key = _env_or_setting(settings, "GOOGLE_API_KEY", "gemini_api_key")
    gemini_api_key = _env_or_setting(settings, "GEMINI_API_KEY", "gemini_api_key")
    if google_api_key or gemini_api_key:
        return LLMRuntime(
            provider="gemini",
            model=os.getenv("GEMINI_MODEL", getattr(config, "GEMINI_MODEL", "gemini-2.5-flash")),
            api_key=google_api_key or gemini_api_key,
        )

    maritalk_api_key = (
        os.getenv("MARITALK_API_KEY")
        or os.getenv("MARITACA_API_KEY")
        or _env_or_setting(settings, "OPENAI_API_KEY", "openai_api_key")
    )
    if maritalk_api_key:
        return LLMRuntime(
            provider="openai_like",
            model=os.getenv("MARITALK_MODEL", getattr(config, "MARITALK_MODEL", "sabiazinho-4")),
            api_key=maritalk_api_key,
            base_url=os.getenv("MARITALK_BASE_URL") or os.getenv("MARITACA_BASE_URL"),
        )

    return LLMRuntime(
        provider="ollama",
        model=os.getenv("OLLAMA_LLM_MODEL", getattr(config, "OLLAMA_LLM_MODEL", "qwen2.5:3b")),
        base_url=(
            os.getenv("OLLAMA_HOST")
            or os.getenv("OLLAMA_BASE_URL")
            or _env_or_setting(settings, "OLLAMA_BASE_URL", "ollama_base_url")
            or "http://localhost:11434"
        ),
    )


def _raise_for_unexpected_http_error(response: requests.Response, service_name: str) -> None:
    if response.status_code == 429:
        pytest.skip(f"{service_name} indisponível por limite de uso/quota no momento.")

    if response.status_code >= 400:
        detail = response.text[:500]
        raise AssertionError(
            f"{service_name} retornou HTTP {response.status_code}: {detail}"
        )


def _ask_gemini(runtime: LLMRuntime) -> str:
    try:
        response = requests.post(
            (
                "https://generativelanguage.googleapis.com/v1beta/"
                f"models/{runtime.model}:generateContent"
            ),
            headers={"x-goog-api-key": runtime.api_key},
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": "Responda apenas com o resultado final: 2+2 é igual a?"}
                        ]
                    }
                ],
                "generationConfig": {"temperature": 0},
            },
            timeout=30,
        )
    except requests.RequestException as exc:
        pytest.skip(f"Gemini indisponível via API REST: {exc}")

    _raise_for_unexpected_http_error(response, "Gemini")
    data = response.json()
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    return " ".join(part.get("text", "") for part in parts).strip()


def _ask_openai_like_with_requests(runtime: LLMRuntime) -> str:
    base_url = (runtime.base_url or "https://api.openai.com/v1").rstrip("/")

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {runtime.api_key}"},
            json={
                "model": runtime.model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": "Responda apenas com o resultado final."},
                    {"role": "user", "content": "2+2 é igual a?"},
                ],
            },
            timeout=30,
        )
    except requests.RequestException as exc:
        pytest.skip(f"OpenAI-like indisponível em {base_url}: {exc}")

    _raise_for_unexpected_http_error(response, "OpenAI-like")
    return response.json()["choices"][0]["message"]["content"].strip()


def _ask_openai_like(runtime: LLMRuntime) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        return _ask_openai_like_with_requests(runtime)

    kwargs = {"api_key": runtime.api_key}
    if runtime.base_url:
        kwargs["base_url"] = runtime.base_url

    client = OpenAI(**kwargs)
    response = client.chat.completions.create(
        model=runtime.model,
        temperature=0,
        messages=[
            {"role": "system", "content": "Responda apenas com o resultado final."},
            {"role": "user", "content": "2+2 é igual a?"},
        ],
    )
    return response.choices[0].message.content.strip()


def _ask_ollama(runtime: LLMRuntime) -> str:
    try:
        response = requests.post(
            f"{runtime.base_url.rstrip('/')}/api/chat",
            json={
                "model": runtime.model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": "Responda apenas com o resultado final."},
                    {"role": "user", "content": "2+2 é igual a?"},
                ],
            },
            timeout=30,
        )
    except requests.RequestException as exc:
        pytest.skip(f"Ollama indisponível em {runtime.base_url}: {exc}")

    if response.status_code == 404:
        pytest.skip(f"Modelo Ollama '{runtime.model}' não encontrado em {runtime.base_url}.")

    _raise_for_unexpected_http_error(response, "Ollama")
    return response.json().get("message", {}).get("content", "").strip()


def _ask_llm(runtime: LLMRuntime) -> str:
    if runtime.provider == "gemini":
        return _ask_gemini(runtime)
    if runtime.provider == "openai_like":
        return _ask_openai_like(runtime)
    return _ask_ollama(runtime)


def test_llm_2_mais_2():
    config = _load_llm_config_module()
    runtime = _resolve_runtime(config)

    answer = _ask_llm(runtime)

    assert "4" in answer, f"Resposta inesperada ({runtime.provider}/{runtime.model}): {answer}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
