"""Backward-compat stub — 실제 구현은 infrastructure.llm.gemini_adapter로 이동됨."""
from infrastructure.llm.gemini_adapter import *  # noqa: F401,F403
from infrastructure.llm.gemini_adapter import (  # noqa: F401
    _close_genai_client,
    generate_multimodal,
    get_image_caption_for_rag,
    stream_multimodal,
)
