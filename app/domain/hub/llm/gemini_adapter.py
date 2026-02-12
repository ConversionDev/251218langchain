"""
Gemini 멀티모달 어댑터.

이미지 + 텍스트 + RAG 컨텍스트를 Gemini에 전달해 스트리밍/일괄 응답을 반환합니다.
API 키는 core.config의 gemini_api_key(GEMINI_API_KEY)에서 읽습니다.
"""

import base64
import logging
from typing import Generator, List, Optional

logger = logging.getLogger(__name__)

# 이미지 개수·크기 제한 (선택)
MAX_IMAGES = 5
MAX_B64_SIZE_PER_IMAGE = 4 * 1024 * 1024  # 4MB


def _decode_image(b64: str) -> tuple[bytes, str]:
    """base64 문자열을 bytes와 mime_type으로 변환. data URL이면 prefix 제거."""
    raw = b64.strip()
    if raw.startswith("data:"):
        # data:image/png;base64,xxxx
        rest = raw.split(",", 1)
        if len(rest) == 2:
            raw = rest[1]
        head = rest[0] if rest else ""
        if ";" in head:
            mime = head.split(";")[0].replace("data:", "").strip()
        else:
            mime = "image/png"
    else:
        mime = "image/jpeg"
    return base64.b64decode(raw), mime


def stream_multimodal(
    user_text: str,
    images: List[str],
    context: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    사용자 메시지 + 이미지(들) + (선택) RAG 컨텍스트로 Gemini를 호출하고 텍스트 스트리밍.

    Args:
        user_text: 사용자 질문/메시지
        images: base64 이미지 문자열 리스트 (data URL 포함 가능)
        context: RAG에서 가져온 참고 문서 텍스트

    Yields:
        응답 텍스트 청크
    """
    from core.config import get_settings

    settings = get_settings()
    api_key = getattr(settings, "gemini_api_key", None) or getattr(settings, "GEMINI_API_KEY", None)
    if not api_key:
        logger.warning("Gemini API 키 없음. .env에 GEMINI_API_KEY를 설정하세요.")
        yield "이미지 분석을 사용하려면 서버에 Gemini API 키가 설정되어 있어야 합니다."
        return

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model_id = getattr(settings, "gemini_model", None) or "gemini-2.5-flash"
    model = genai.GenerativeModel(model_id)

    # 입력 parts: 텍스트 + 이미지들
    parts: list = []
    if context and context.strip():
        system_and_context = (
            "참고 컨텍스트 (아래 문서를 우선 참고하여 답변하고, 인용 시 [출처: ...]를 밝혀 주세요):\n"
            f"{context}\n\n"
            "답변은 일반 텍스트로만 작성하고, ```json 또는 빈 코드 블록을 사용하지 마세요. "
            "참고 문서가 능력(Ability) 목록·직무/역량 분류 형태이면, 왼쪽 열에 능력명(영문)·오른쪽 열에 [능력] 직무명 형태의 표로 정리해 주세요."
        )
        parts.append(system_and_context + "\n\n사용자 질문 및 첨부 이미지에 대해 위 컨텍스트를 참고해 답변해 주세요.\n\n")
    parts.append(user_text or "위 이미지(들)에 대해 설명해 주세요.")

    limited = images[:MAX_IMAGES] if len(images) > MAX_IMAGES else images
    for b64_img in limited:
        try:
            if len(b64_img) > MAX_B64_SIZE_PER_IMAGE:
                logger.warning("이미지 base64 크기 초과, 건너뜀")
                continue
            img_bytes, mime = _decode_image(b64_img)
            parts.append({"mime_type": mime, "data": img_bytes})
        except Exception as e:
            logger.warning("이미지 디코딩 실패: %s", e)
            continue

    if not parts:
        yield "처리할 수 있는 입력이 없습니다."
        return

    try:
        response = model.generate_content(parts, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        logger.exception("Gemini 멀티모달 호출 실패: %s", e)
        yield f"이미지 분석 중 오류가 발생했습니다: {str(e)}"


def generate_multimodal(
    user_text: str,
    images: List[str],
    context: Optional[str] = None,
) -> str:
    """스트리밍 없이 전체 응답을 한 번에 반환."""
    return "".join(stream_multimodal(user_text, images, context))


def get_image_caption_for_rag(images: List[str]) -> str:
    """
    이미지(들)에서 RAG 검색에 쓸 수 있는 글자·키워드·요약을 추출합니다.
    이미지만 보냈을 때 DB 검색 쿼리로 사용됩니다.

    Args:
        images: base64 이미지 문자열 리스트 (data URL 포함 가능)

    Returns:
        검색 쿼리로 쓸 수 있는 한두 문장. 실패 시 빈 문자열.
    """
    if not images:
        return ""

    from core.config import get_settings

    settings = get_settings()
    api_key = getattr(settings, "gemini_api_key", None) or getattr(settings, "GEMINI_API_KEY", None)
    if not api_key:
        logger.warning("Gemini API 키 없음. 이미지→RAG 쿼리 추출 불가.")
        return ""

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model_id = getattr(settings, "gemini_model", None) or "gemini-2.5-flash"
    model = genai.GenerativeModel(model_id)

    prompt = (
        "이 이미지(들)에 보이는 글자, 키워드, 핵심 내용을 문서 검색 쿼리로 쓸 수 있게 "
        "한두 문장으로만 추출해 주세요. 다른 설명 없이 검색에 쓸 문장만 반환하세요."
    )
    parts: list = [prompt]
    limited = images[:MAX_IMAGES] if len(images) > MAX_IMAGES else images
    for b64_img in limited:
        try:
            if len(b64_img) > MAX_B64_SIZE_PER_IMAGE:
                continue
            img_bytes, mime = _decode_image(b64_img)
            parts.append({"mime_type": mime, "data": img_bytes})
        except Exception as e:
            logger.warning("이미지 디코딩 실패(캡션): %s", e)
            continue

    if len(parts) <= 1:
        return ""

    try:
        response = model.generate_content(parts)
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        logger.warning("이미지 캡션 추출 실패: %s", e)
    return ""
