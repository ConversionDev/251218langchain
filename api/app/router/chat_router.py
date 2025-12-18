"""
FastAPI 기준의 API 엔드포인트 계층입니다.

chat_router.py
POST /api/chat
세션 ID, 메시지 리스트 등을 받아 대화형 응답 반환.
"""

import os
import re
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import Runnable
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    """챗봇 요청 모델."""

    message: str
    history: Optional[List[dict]] = []
    model_type: Optional[str] = "openai"  # "openai" 또는 "local"


class ChatResponse(BaseModel):
    """챗봇 응답 모델."""

    response: str


def get_rag_chains():
    """전역 RAG 체인과 할당량 상태를 반환하는 함수.

    이 함수는 api_server.py의 전역 변수에 접근하기 위해
    api_server 모듈에서 import하여 사용합니다.
    순환 import 방지를 위해 함수 내부에서 import합니다.
    """
    # 순환 import 방지를 위해 함수 내부에서 import
    import sys

    # api_server 모듈이 이미 로드되어 있는지 확인
    if "app.api_server" in sys.modules:
        from .. import api_server
    else:
        # 모듈이 아직 로드되지 않은 경우 직접 import
        import importlib

        api_server = importlib.import_module("app.api_server")

    return {
        "openai_rag_chain": api_server.openai_rag_chain,
        "local_rag_chain": api_server.local_rag_chain,
        "openai_quota_exceeded": api_server.openai_quota_exceeded,
        "openai_llm": api_server.openai_llm,
        "openai_embeddings": api_server.openai_embeddings,
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """챗봇 API 엔드포인트 - LangChain RAG 체인 사용."""
    # 전역 RAG 체인 가져오기
    chains = get_rag_chains()
    openai_rag_chain: Optional[Runnable] = chains["openai_rag_chain"]
    local_rag_chain: Optional[Runnable] = chains["local_rag_chain"]
    openai_quota_exceeded: bool = chains["openai_quota_exceeded"]
    openai_llm = chains["openai_llm"]
    openai_embeddings = chains["openai_embeddings"]

    # 모델 타입에 따라 적절한 RAG 체인 선택
    # 프론트엔드에서 전달된 model_type이 없으면 .env의 LLM_PROVIDER 사용
    model_type = request.model_type or os.getenv("LLM_PROVIDER", "openai")
    if model_type:
        model_type = model_type.lower()

    # 디버깅: 받은 model_type 로그 출력
    print(
        f"[DEBUG] 받은 model_type: {request.model_type}, 처리된 model_type: {model_type}"
    )

    # "midm"도 "local"로 처리
    if model_type == "midm":
        model_type = "local"

    if model_type == "openai":
        if not openai_rag_chain:
            # 할당량 초과 여부 확인
            if openai_quota_exceeded:
                # 할당량 초과인 경우 명확한 메시지
                error_msg = (
                    "⚠️ OpenAI API 할당량이 초과되었습니다.\n\n"
                    "서버 시작 시 '[WARNING] OpenAI API 할당량 초과' 메시지가 확인되었습니다.\n\n"
                    "해결 방법:\n"
                    "1. OpenAI 계정의 사용량 및 할당량을 확인하세요\n"
                    "2. OpenAI 계정에 결제 정보를 추가하거나 할당량을 늘리세요\n"
                    "3. 또는 '🖥️ 로컬 모델' 버튼을 선택하여 로컬 Midm 모델을 사용하세요"
                )
            elif not openai_llm and not openai_embeddings:
                # 둘 다 초기화 실패 (할당량 초과가 아닌 경우)
                error_msg = (
                    "OpenAI 모델이 초기화되지 않았습니다.\n\n"
                    "가능한 원인:\n"
                    "1. OpenAI API 키가 설정되지 않았거나 잘못되었습니다\n"
                    "2. 네트워크 연결 문제\n\n"
                    "해결 방법:\n"
                    "- .env 파일에 올바른 OPENAI_API_KEY를 설정하세요\n"
                    "- 또는 '로컬 모델' 버튼을 선택하여 로컬 모델을 사용하세요"
                )
            else:
                # 일부만 실패
                error_details = []
                if not openai_llm:
                    error_details.append("OpenAI LLM이 초기화되지 않았습니다")
                if not openai_embeddings:
                    error_details.append("OpenAI Embeddings가 초기화되지 않았습니다")
                error_msg = f"OpenAI RAG 체인 생성 실패: {', '.join(error_details)}"

            print(f"[ERROR] OpenAI 모델 사용 시도 실패: {error_msg}")
            raise HTTPException(
                status_code=503,
                detail=error_msg,
            )
        current_rag_chain = openai_rag_chain
    elif model_type == "local" or model_type == "midm":
        if not local_rag_chain:
            raise HTTPException(
                status_code=503,
                detail="로컬 모델이 초기화되지 않았습니다. Midm 모델과 sentence-transformers를 확인해주세요.",
            )
        print(f"[DEBUG] 로컬 RAG 체인 사용 (model_type: {model_type})")
        current_rag_chain = local_rag_chain
    else:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 모델 타입입니다: {model_type}. 'openai' 또는 'local'을 사용해주세요.",
        )

    try:
        # 대화 기록을 LangChain 메시지 형식으로 변환
        chat_history = []
        if request.history:
            for msg in request.history:
                if msg.get("role") == "user":
                    chat_history.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("role") == "assistant":
                    chat_history.append(AIMessage(content=msg.get("content", "")))

        # RAG 체인 실행
        result = current_rag_chain.invoke(
            {
                "input": request.message,
                "chat_history": chat_history,
            }
        )

        # 체인 결과에서 답변 추출
        response_text = result.get("answer", "답변을 생성할 수 없습니다.")

        # response_text가 None이거나 문자열이 아닌 경우 처리
        if response_text is None:
            response_text = "답변을 생성할 수 없습니다."
        else:
            response_text = str(response_text)

        # 응답에서 이전 대화 내용 제거 (중복 방지)
        # Midm 모델에서 이미 정리했으므로 간단한 체크만 수행
        if response_text and (
            "Human:" in response_text or "Assistant:" in response_text
        ):
            # 빠른 정규식으로 마지막 Assistant: 이후만 추출
            assistant_match = re.search(
                r"Assistant:\s*(.+?)(?:\nHuman:|$)", response_text, re.DOTALL
            )
            if assistant_match:
                response_text = assistant_match.group(1).strip()

        # 빈 응답 방지
        if not response_text or not response_text.strip():
            response_text = "답변을 생성할 수 없습니다."

        return ChatResponse(response=response_text)

    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] 챗봇 응답 생성 실패: {error_msg}")

        # OpenAI API 호출량 초과 에러 확인
        if (
            "quota" in error_msg.lower()
            or "429" in error_msg
            or "insufficient_quota" in error_msg
            or "exceeded" in error_msg.lower()
        ):
            error_detail = "OpenAI API 호출량이 초과되었습니다. 할당량을 확인하고 다시 시도해주세요."
            raise HTTPException(
                status_code=429,
                detail=error_detail,
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"응답 생성 중 오류가 발생했습니다: {error_msg[:200]}",
            )
