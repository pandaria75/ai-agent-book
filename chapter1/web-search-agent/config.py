"""
配置文件 - Kimi API 配置
"""

import os
from typing import Optional
from dotenv import load_dotenv

# main.py loads the script-local file first. This also makes direct imports of
# Config behave consistently when the module is used outside the CLI.
load_dotenv()


# Provider resolution lives in the shared agentbook package so every chapter
# stays consistent; see agentbook/providers.py. The fallback keeps this
# experiment runnable from a checkout where agentbook is not installed.
try:
    from agentbook.providers import (
        PROVIDERS,
        SUPPORTED_PROVIDERS,
        canonical_provider,
        map_model_to_openrouter,
        resolve_backend,
        resolve_llm_backend,
    )
except ImportError:  # pragma: no cover - exercised only without the package
    import sys as _sys

    _sys.path.insert(
        0, str(__import__("pathlib").Path(__file__).resolve().parents[2])
    )
    from agentbook.providers import (
        PROVIDERS,
        SUPPORTED_PROVIDERS,
        canonical_provider,
        map_model_to_openrouter,
        resolve_backend,
        resolve_llm_backend,
    )


class Config:
    """配置类"""
    
    # Kimi API 配置
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "kimi").lower()
    MOONSHOT_API_KEY: str = os.getenv("MOONSHOT_API_KEY", "")
    # 向后兼容：如果没有 MOONSHOT_API_KEY，尝试使用 KIMI_API_KEY
    if not MOONSHOT_API_KEY:
        MOONSHOT_API_KEY = os.getenv("KIMI_API_KEY", "")
    
    KIMI_BASE_URL: str = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
    
    # 模型配置
    MODEL_NAME: str = os.getenv("MODEL_NAME", "")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "kimi-k3")

    # Search provider is independent from the LLM provider.
    SEARCH_PROVIDER: str = os.getenv("SEARCH_PROVIDER", "moonshot").lower()
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    TAVILY_BASE_URL: str = os.getenv("TAVILY_BASE_URL", "https://api.tavily.com")

    # 搜索配置
    MAX_SEARCH_ITERATIONS: int = int(
        os.getenv("MAX_SEARCH_ITERATIONS", "5")
    )  # 最大搜索迭代次数
    # 这个超时同时作用于 Formula 工具调用和 chat completion。kimi-k3 以
    # reasoning_effort=max 运行，单次 completion 常需 1-3 分钟（validation/
    # 目录里保留的真实运行记录中有 161 秒、121 秒的调用），30 秒会让交互模式
    # 反复 "Request timed out"。默认值与 run_experiment_1_2.py 的 --timeout
    # 保持一致，确保 README 里的交互入口与验收脚本跑在同一配置下。
    SEARCH_TIMEOUT: float = float(os.getenv("SEARCH_TIMEOUT", "180"))
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def validate(cls, provider: str = None) -> bool:
        """
        验证配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        try:
            resolve_backend(provider or cls.LLM_PROVIDER)
        except ValueError as exc:
            print(f"错误: {exc}")
            return False
        return True
    
    @classmethod
    def get_api_key(cls, provider: str = None, api_key: Optional[str] = None) -> str:
        """
        获取 API Key
        
        Args:
            api_key: 可选的 API key，如果提供则使用，否则从环境变量获取
            
        Returns:
            API key
        """
        if api_key:
            return api_key
        if provider:
            try:
                return PROVIDERS[canonical_provider(provider)].api_key()
            except KeyError:
                return ""
        return cls.MOONSHOT_API_KEY

    @classmethod
    def get_default_model(cls, provider: str = None) -> str:
        """Return the .env model override or the registry provider default."""
        if cls.MODEL_NAME:
            return cls.MODEL_NAME
        if cls.DEFAULT_MODEL != "kimi-k3" and (not provider or canonical_provider(provider) == "kimi"):
            return cls.DEFAULT_MODEL
        try:
            return PROVIDERS[canonical_provider(provider or cls.LLM_PROVIDER)].default_model
        except KeyError:
            return "kimi-k3"
