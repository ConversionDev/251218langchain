"""
Hub LLM Adapters - Llama/ExaOne 유일 진입점.

목표 구조: 내부 서비스·MCP 도구는 이 어댑터를 통해서만 Llama/ExaOne에 접근합니다.
- Llama Adapter: 시멘틱 분류(classify), 스팸 분류(classify_spam)
- ExaOne Adapter: 텍스트 생성(generate_text), LLM 인스턴스(get_llm), 이메일 분석(analyze_email)
- Provider 메타: get_provider_name, list_providers, supports_tool_calling (exaone_provider)
"""

from .exaone_adapter import (
    analyze_email,
    generate_text,
    get_llm,
)
from .llama_adapter import (
    classify,
    classify_spam,
    is_classifier_available,
)
from .exaone_provider import (
    get_provider_name,
    list_providers,
    supports_tool_calling,
)

__all__ = [
    # Llama
    "classify",
    "classify_spam",
    "is_classifier_available",
    # ExaOne
    "generate_text",
    "get_llm",
    "analyze_email",
    # Provider 메타
    "get_provider_name",
    "list_providers",
    "supports_tool_calling",
]
