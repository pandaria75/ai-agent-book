"""Configuration for the exact GPT-5.6 Responses API companion."""

import os
from pathlib import Path
from typing import Optional, Tuple

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().with_name(".env"))


def _optional_int_env(name: str) -> Optional[int]:
    """Read an optional integer without making module import configuration-fatal."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return None
    cleaned = raw_value.strip()
    if not cleaned or not cleaned.isascii() or not cleaned.isdecimal():
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
    DASHSCOPE_BASE_URL = os.getenv(
        "DASHSCOPE_BASE_URL",
        "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    )
    DASHSCOPE_MODEL = os.getenv("DASHSCOPE_MODEL", "qwen3.7-plus")
    BACKEND = os.getenv("BACKEND", "openai")
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5.6-sol")
    DEFAULT_TEMPERATURE = 0.3  # legacy CLI compatibility; intentionally omitted
    DEFAULT_MAX_TOKENS: Optional[int] = _optional_int_env("DEFAULT_MAX_TOKENS")
    DEFAULT_TOOL_CHOICE = os.getenv("DEFAULT_TOOL_CHOICE", "auto")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "20"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))
    WEB_SEARCH_MAX_RESULTS = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "5"))
    CODE_INTERPRETER_TIMEOUT = int(os.getenv("CODE_INTERPRETER_TIMEOUT", "30"))
    WEB_SEARCH_PROVIDER = os.getenv("WEB_SEARCH_PROVIDER", "native").lower()
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
    TAVILY_BASE_URL = os.getenv("TAVILY_BASE_URL", "https://api.tavily.com")

    @classmethod
    def resolve(
        cls, backend: Optional[str] = None, model: Optional[str] = None
    ) -> Tuple[str, str, str]:
        backend = backend or cls.BACKEND
        if backend == "openai":
            model = model or cls.MODEL_NAME
            return cls.OPENAI_API_KEY, cls.OPENAI_BASE_URL, model.removeprefix("openai/")
        if backend == "openrouter":
            model = model or cls.MODEL_NAME
            routed = model if model.startswith("openai/") else f"openai/{model}"
            return cls.OPENROUTER_API_KEY, cls.OPENROUTER_BASE_URL, routed
        if backend == "dashscope":
            return cls.DASHSCOPE_API_KEY, cls.DASHSCOPE_BASE_URL, model or cls.DASHSCOPE_MODEL
        raise ValueError("backend must be openai, openrouter, or dashscope")

    @classmethod
    def validate(cls, backend: Optional[str] = None) -> bool:
        key, _, _ = cls.resolve(backend)
        if not key:
            print(f"Error: no API key for {backend or cls.BACKEND}")
            return False
        return True

    @classmethod
    def validate_search(cls) -> bool:
        if cls.WEB_SEARCH_PROVIDER not in {"native", "tavily"}:
            print("Error: WEB_SEARCH_PROVIDER must be native or tavily")
            return False
        if cls.WEB_SEARCH_PROVIDER == "tavily" and not cls.TAVILY_API_KEY:
            print("Error: no TAVILY_API_KEY configured for Tavily search")
            return False
        return True

    @classmethod
    def display(cls, backend: Optional[str] = None) -> None:
        key, base_url, model = cls.resolve(backend)
        print("=== GPT-5.6 Responses Configuration ===")
        print(f"Backend: {backend or cls.BACKEND}")
        print(f"API Base URL: {base_url}")
        print(f"Model: {model}")
        print(f"API Key configured: {bool(key)}")


def check_config() -> bool:
    return Config.validate()
