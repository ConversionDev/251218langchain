"""Backward-compat stub — 실제 구현은 infrastructure.llm으로 이동됨."""
from infrastructure.llm import *  # noqa: F401,F403
from infrastructure.llm import (  # noqa: F401
    analyze_email,
    classify_spam,
    generate_text,
    get_llm,
    get_provider_name,
    list_providers,
    supports_tool_calling,
)
