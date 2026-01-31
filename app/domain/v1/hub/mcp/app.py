"""
Llama + ExaOne 연결 FastMCP 앱.

도구:
- classify_with_llama(text): Llama 3.2 시멘틱 분류기로 BLOCK/RULE_BASED/POLICY_BASED 분류
- generate_with_exaone(prompt, max_tokens): ExaOne 7.8B로 텍스트 생성
- classify_then_generate(text, generate_prompt): Llama 분류 후 ExaOne으로 생성
"""

from fastmcp import FastMCP

mcp = FastMCP("Llama + ExaOne")

# ---------------------------------------------------------------------------
# 내부 구현 (재사용·테스트용)
# ---------------------------------------------------------------------------

def _classify_with_llama_impl(text: str) -> str:
    """Llama 시멘틱 분류 (Hub Llama Adapter 경유). BLOCK | RULE_BASED | POLICY_BASED."""
    try:
        from domain.v1.hub.llm import (  # type: ignore
            classify,
            is_classifier_available,
        )

        if not is_classifier_available():
            return "POLICY_BASED"  # 어댑터 없으면 기본 정책 기반
        return classify(text.strip()) if text else "POLICY_BASED"
    except Exception:
        return "POLICY_BASED"


def _generate_with_exaone_impl(prompt: str, max_tokens: int = 512) -> str:
    """ExaOne으로 텍스트 생성 (Hub ExaOne Adapter 경유)."""
    try:
        from domain.v1.hub.llm import generate_text  # type: ignore

        return generate_text(prompt.strip(), max_tokens=max_tokens)
    except Exception as e:
        return f"[ExaOne 오류] {e}"


def _classify_then_generate_impl(
    text: str,
    generate_prompt: str,
    max_tokens: int = 512,
) -> dict:
    """Llama로 분류한 뒤, BLOCK이 아니면 ExaOne으로 generate_prompt 기반 생성."""
    classification = _classify_with_llama_impl(text)
    result: dict = {
        "classification": classification,
        "generated": None,
        "skipped": False,
    }
    if classification == "BLOCK":
        result["skipped"] = True
        result["generated"] = "(BLOCK으로 생성 생략)"
        return result
    # RULE_BASED / POLICY_BASED 모두 ExaOne 생성 수행 (generate_prompt에 {text} 반영 가능)
    full_prompt = generate_prompt.strip()
    if "{text}" in full_prompt:
        full_prompt = full_prompt.replace("{text}", text.strip())
    result["generated"] = _generate_with_exaone_impl(full_prompt, max_tokens=max_tokens)
    return result


# ---------------------------------------------------------------------------
# MCP 도구
# ---------------------------------------------------------------------------


@mcp.tool
def classify_with_llama(text: str) -> str:
    """Llama 3.2 시멘틱 분류기로 입력 텍스트를 분류합니다.

    Returns:
        'BLOCK' | 'RULE_BASED' | 'POLICY_BASED'
    """
    return _classify_with_llama_impl(text)


@mcp.tool
def generate_with_exaone(prompt: str, max_tokens: int = 512) -> str:
    """ExaOne 7.8B로 프롬프트에 대한 텍스트를 생성합니다."""
    return _generate_with_exaone_impl(prompt, max_tokens)


@mcp.tool
def classify_then_generate(
    text: str,
    generate_prompt: str,
    max_tokens: int = 512,
) -> dict:
    """먼저 Llama로 text를 분류하고, BLOCK이 아니면 ExaOne으로 generate_prompt를 사용해 생성합니다.

    generate_prompt에 {text}가 있으면 사용자 입력으로 치환됩니다.
    """
    return _classify_then_generate_impl(text, generate_prompt, max_tokens)


def get_http_app():
    """Fast MCP로 통일한 ASGI 앱: GET /health + MCP 프로토콜(/server).

    메인 앱에서 app.mount("/mcp", get_http_app()) 하면
    - GET /mcp/health → 헬스 체크
    - /mcp/server → MCP 프로토콜 (Fast MCP)
    """
    from fastapi import FastAPI  # type: ignore

    wrapper = FastAPI(title="MCP (Llama + ExaOne)", tags=["MCP"])

    @wrapper.get("/health")
    async def health():
        return {"status": "ok", "service": "MCP", "protocol": "Fast MCP"}

    # Fast MCP 프로토콜은 /server 하위에 마운트 (기존 /mcp/server 경로 유지)
    mcp_asgi = mcp.http_app(path="/server")
    wrapper.mount("/server", mcp_asgi)

    return wrapper

