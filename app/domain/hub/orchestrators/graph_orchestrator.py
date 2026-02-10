"""
Graph Orchestrator — 채팅 그래프 빌더

도구(TOOLS), 노드(model/rag/tool), 체크포인터, 조건 라우팅.
"""

import logging
import sys
from typing import Any, Dict, List, Literal, Optional

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from domain.models import ChatState

logger = logging.getLogger(__name__)


# --- 1. 도구 (오케스트레이터 → HTTP → Hub → call_tool → 도메인 MCP → Spoke) ---


def _hub_result_to_str(result: Any) -> str:
    """Hub call 결과를 문자열로."""
    if result is None:
        return "호출 실패"
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        import json
        return json.dumps(result, ensure_ascii=False)
    return str(result)


@tool
def analyze_with_exaone(
    subject: str,
    sender: str,
    body: Optional[str] = None,
    recipient: Optional[str] = None,
    date: Optional[str] = None,
    attachments: Optional[List[str]] = None,
    headers: Optional[Dict[str, Any]] = None,
    _policy_context: Optional[str] = None,
) -> str:
    """EXAONE으로 이메일 분석. HTTP → Hub → Spam MCP → Spoke."""
    from domain.hub.mcp.http_client import spam_call  # type: ignore

    args: Dict[str, Any] = {
        "subject": subject,
        "sender": sender,
        "body": body or "",
        "recipient": recipient or "",
        "date": date or "",
        "policy_context": _policy_context or "",
    }
    if attachments is not None:
        args["attachments"] = attachments
    if headers is not None:
        args["headers"] = headers
    result = spam_call("analyze_email", args)
    return _hub_result_to_str(result)


@tool
def search_documents(query: str) -> str:
    """문서에서 관련 정보를 검색합니다. HTTP → Hub → Chat MCP → Spoke."""
    from domain.hub.mcp.http_client import chat_call  # type: ignore

    result = chat_call("search_documents", {"query": query})
    return _hub_result_to_str(result)


@tool
def get_current_time() -> str:
    """현재 시간을 반환합니다. HTTP → Hub → Chat MCP → Spoke."""
    from domain.hub.mcp.http_client import chat_call  # type: ignore

    result = chat_call("get_current_time", {})
    return _hub_result_to_str(result)


@tool
def calculate(expression: str) -> str:
    """수학 표현식을 계산합니다. HTTP → Hub → Chat MCP → Spoke."""
    from domain.hub.mcp.http_client import chat_call  # type: ignore

    result = chat_call("calculate", {"expression": expression})
    return _hub_result_to_str(result)


@tool
def define(term: str) -> str:
    """용어(term)의 정의나 설명을 문서에서 검색해 반환합니다. 예: IFRS, OECD 등."""
    from domain.hub.mcp.http_client import chat_call  # type: ignore

    result = chat_call("search_documents", {"query": term})
    return _hub_result_to_str(result)


TOOLS = [
    analyze_with_exaone,
    search_documents,
    get_current_time,
    calculate,
    define,
]
TOOL_MAP: Dict[str, Any] = {t.name: t for t in TOOLS}


# --- 2. 노드 (model, rag, tool) ---


def _get_llm(provider: Optional[str] = None, **kwargs):
    """LLM 인스턴스 반환 (ExaOne)."""
    from domain.hub.llm import get_llm  # type: ignore

    return get_llm(provider=provider, **kwargs)


def _supports_tool_calling(provider: Optional[str] = None) -> bool:
    """Tool Calling 지원 여부 확인."""
    from domain.hub.llm.exaone_provider import supports_tool_calling  # type: ignore

    return supports_tool_calling(provider)


def _get_llm_provider():
    """LLMProvider 클래스 반환."""
    from domain.hub.llm.exaone_provider import LLMProvider  # type: ignore

    return LLMProvider


def model_node(state: ChatState) -> ChatState:
    """모델 노드. LLM 호출·Tool Calling, 스트리밍 지원."""
    LLMProvider = _get_llm_provider()
    provider = state.get("model_provider") or LLMProvider.get_provider_name()
    llm = _get_llm(provider=provider)

    messages = list(state.get("messages", []))
    context = state.get("context")

    if context and messages:
        system_msg_idx = None
        for i, msg in enumerate(messages):
            if isinstance(msg, SystemMessage):
                system_msg_idx = i
                break
        context_addition = (
            f"\n\n참고 컨텍스트 (아래 문서를 우선 참고하여 답변하고, 인용 시 [출처: ...]를 밝혀 주세요):\n{context}"
            "\n\n답변은 일반 텍스트로만 작성하고, ```json 또는 빈 코드 블록을 사용하지 마세요."
        )
        if system_msg_idx is not None:
            old_content = str(messages[system_msg_idx].content)
            messages[system_msg_idx] = SystemMessage(
                content=old_content + context_addition
            )
        else:
            messages = [
                SystemMessage(
                    content=f"당신은 도움이 되는 AI 어시스턴트입니다.{context_addition}"
                )
            ] + messages

    if _supports_tool_calling(provider):
        llm_with_tools = llm.bind_tools(TOOLS)
        chunks = []
        tool_calls = []
        for chunk in llm_with_tools.stream(messages):
            chunks.append(chunk)
            if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                tool_calls.extend(chunk.tool_calls)
        if chunks:
            full_content = "".join(
                chunk.content for chunk in chunks
                if hasattr(chunk, "content") and chunk.content
            )
            response = (
                AIMessage(content=full_content, tool_calls=tool_calls)
                if tool_calls
                else AIMessage(content=full_content)
            )
        else:
            response = AIMessage(content="")
    else:
        chunks = []
        for chunk in llm.stream(messages):
            chunks.append(chunk)
        if chunks:
            full_content = "".join(
                chunk.content for chunk in chunks
                if hasattr(chunk, "content") and chunk.content
            )
            response = AIMessage(content=full_content)
        else:
            response = AIMessage(content="")

    return {"messages": [response], "model_provider": provider}


def tool_node(state: ChatState) -> ChatState:
    """도구 노드. tool_calls 실행 후 ToolMessage 반환."""
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    results: List[BaseMessage] = []

    tool_calls = getattr(last_message, "tool_calls", None) if last_message else None
    if tool_calls:
        for call in tool_calls:
            name = call["name"]
            args = call.get("args", {})
            if name in TOOL_MAP:
                try:
                    output = TOOL_MAP[name].invoke(args)
                except Exception as e:
                    output = f"도구 실행 오류: {str(e)}"
            else:
                output = f"알 수 없는 도구: {name}"
            results.append(
                ToolMessage(
                    content=str(output),
                    tool_call_id=call["id"],
                    name=name,
                )
            )

    return {"messages": results}


# 질문과 무관한 문서 제외: 거리(score)가 이 값 이하인 문서만 참고 (코사인 거리, 작을수록 유사)
RAG_DISTANCE_THRESHOLD = 0.8
# 표준 키워드 없을 때: 최소거리가 이 값보다 크면 "공시 무관 질문"으로 보고 disclosure 결과 전부 제외
RAG_DISCLOSURE_NO_KEYWORD_MAX_DISTANCE = 0.75

def _infer_disclosure_standard_filter(query: str) -> Optional[Dict[str, Any]]:
    """
    질문 텍스트에서 참조할 disclosure 표준을 추론해 메타데이터 필터 dict 반환.
    (PGVector 등 메타데이터 필터용)
    """
    types = _infer_disclosure_standard_types(query)
    if not types:
        return None
    if len(types) == 1:
        return {"standard_type": types[0]}
    return {"standard_type": {"$in": types}}


def _infer_disclosure_standard_types(query: str) -> Optional[List[str]]:
    """
    질문 텍스트에서 참조할 disclosure 표준을 추론해 standard_type 리스트 반환.
    - IFRS/S1/S2/국제 재무 → ['IFRS_S1', 'IFRS_S2']
    - OECD/경제협력 → ['OECD']
    - ISO/30414 → ['ISO30414']
    - green stock/stocktake → ['GLOBAL_GREEN_STOCKTAKE']
    표준이 불명확하면 None(필터 없음). disclosures 테이블 검색 시 사용.
    """
    if not query or not query.strip():
        return None
    q = query.strip().lower()
    if "ifrs" in q or "s1" in q or "s2" in q or "국제 재무" in q or "국제재무" in q:
        return ["IFRS_S1", "IFRS_S2"]
    if "oecd" in q or "경제협력" in q or "경제 협력" in q:
        return ["OECD"]
    if "iso" in q or "30414" in q or "인적자본" in q:
        return ["ISO30414"]
    if "green stock" in q or "stocktake" in q or "global green" in q or "그린스탁" in q:
        return ["GLOBAL_GREEN_STOCKTAKE"]
    return None


def _retrieve_with_threshold(
    store: Any, query: str, k: int = 5, filter_dict: Optional[Dict[str, Any]] = None
) -> List[Any]:
    """유사도(거리) 임계값 이하인 문서만 반환. filter_dict 있으면 메타데이터 필터 적용(disclosure 표준별)."""
    kwargs: Dict[str, Any] = {"query": query, "k": k}
    if filter_dict:
        kwargs["filter"] = filter_dict
    try:
        # (Document, score) 반환. pgvector 코사인 거리: 작을수록 유사
        pairs = store.similarity_search_with_score(**kwargs)
    except Exception:
        kwargs.pop("filter", None)
        return store.similarity_search(**kwargs)
    result = []
    for doc, score in pairs:
        if score <= RAG_DISTANCE_THRESHOLD:
            result.append(doc)
    return result


def _build_context_with_sources(docs: List[Any]) -> str:
    """각 문서 앞에 [출처: id=..., source=..., page=...] 를 붙여 DB에서 찾을 수 있게 함."""
    parts = []
    for doc in docs:
        meta = getattr(doc, "metadata", None) or {}
        id_val = meta.get("id") or meta.get("doc_id")
        source = meta.get("source", "")
        page = meta.get("page", "")
        standard_type = meta.get("standard_type", "")
        unique_id = meta.get("unique_id", "")
        tokens = []
        if id_val is not None:
            tokens.append(f"id={id_val}")
        if source:
            tokens.append(f"source={source}")
        if page != "":
            tokens.append(f"page={page}")
        if standard_type:
            tokens.append(f"standard_type={standard_type}")
        if unique_id:
            tokens.append(f"unique_id={unique_id}")
        cite = "[출처: " + ", ".join(tokens) + "]" if tokens else "[출처: (메타데이터 없음)]"
        parts.append(f"{cite}\n{doc.page_content}")
    return "\n\n".join(parts)


def rag_node(state: ChatState) -> ChatState:
    """RAG 노드. PGVector 유사도 검색 후, 거리 임계값 이하인 문서만 컨텍스트로 사용."""
    messages = state.get("messages", [])

    user_query: Optional[str] = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_query = str(msg.content)
            break

    if not user_query:
        return {"context": ""}

    # 로그 레벨과 관계없이 RAG 진입을 확인할 수 있도록 WARNING 사용
    _q = (user_query[:80] + "…") if len(user_query) > 80 else user_query
    logger.warning("[RAG] 질의 처리 중: %s", _q)
    try:
        if "fastapi_server" in sys.modules:
            import fastapi_server  # type: ignore

            fastapi_server.ensure_rag_initialized()
            all_docs: list = []
            main_count = 0
            if fastapi_server.vector_store:
                main_docs = _retrieve_with_threshold(fastapi_server.vector_store, user_query, k=5)
                main_count = len(main_docs)
                all_docs.extend(main_docs)
            # disclosures 테이블 검색 (id, content, embedding, source, page, standard_type, section_title, metadata, unique_id)
            # 표준 판별 시 해당 standard_type만 검색
            disclosure_count_before_threshold = 0
            try:
                from core.database import SessionLocal  # type: ignore
                from domain.hub.repositories.disclosure_repository import (  # type: ignore
                    search_disclosures_with_filter,
                )

                # disclosure 테이블은 FlagEmbedding(BGE-m3)으로 적재됨 → 쿼리도 동일 모델(fp16)로 같은 벡터 공간
                query_vec = None
                try:
                    from domain.shared.embedding import get_disclosure_embedding_model  # type: ignore
                    bge = get_disclosure_embedding_model()
                    if bge is not None and hasattr(bge, "embed_query"):
                        for attempt in range(2):
                            try:
                                query_vec = bge.embed_query(user_query)
                                break
                            except Exception as _e1:
                                if attempt == 0:
                                    logger.warning("[RAG] disclosure embed_query 1회 실패, 재시도: %s", _e1)
                                else:
                                    raise
                except Exception as _e:
                    logger.warning("[RAG] disclosure 쿼리 임베딩 실패: %s", _e)
                if query_vec is None:
                    emb = getattr(fastapi_server, "local_embeddings", None)
                    if emb is not None and hasattr(emb, "embed_query"):
                        query_vec = emb.embed_query(user_query)
                if query_vec is not None:
                    db = SessionLocal()
                    try:
                        standard_types = _infer_disclosure_standard_types(user_query)
                        pairs = search_disclosures_with_filter(
                            db, query_vec, k=10, standard_types=standard_types
                        )
                        disclosure_count_before_threshold = len(pairs)
                        disclosure_passed = 0
                        min_distance = None
                        closest_doc = None
                        passed_docs: List[Any] = []
                        for doc, distance in pairs:
                            if min_distance is None or distance < min_distance:
                                min_distance = distance
                                closest_doc = doc
                            if distance <= RAG_DISTANCE_THRESHOLD:
                                passed_docs.append(doc)
                                disclosure_passed += 1
                        # 표준 키워드 없을 때: 최소거리가 크면 무관한 질문으로 보고 disclosure 결과 사용 안 함
                        if (
                            standard_types is None
                            and min_distance is not None
                            and min_distance > RAG_DISCLOSURE_NO_KEYWORD_MAX_DISTANCE
                        ):
                            passed_docs = []
                            disclosure_passed = 0
                            logger.info(
                                "[RAG] disclosure: 키워드 없음, 최소거리=%.4f > %.2f → 무관한 질문으로 판단, disclosure 제외",
                                min_distance,
                                RAG_DISCLOSURE_NO_KEYWORD_MAX_DISTANCE,
                            )
                        else:
                            for doc in passed_docs:
                                all_docs.append(doc)
                            # 후보는 있는데 임계값 통과 0건이면 최소 1건이라도 포함 (거리 임계값 완화 fallback)
                            if (
                                disclosure_count_before_threshold > 0
                                and disclosure_passed == 0
                                and closest_doc is not None
                            ):
                                all_docs.append(closest_doc)
                                disclosure_passed = 1
                                logger.warning(
                                    "[RAG] disclosure 임계값 통과 0건 → 최소 1건 포함 (최소거리=%.4f, threshold=%.2f)",
                                    min_distance or 0,
                                    RAG_DISTANCE_THRESHOLD,
                                )
                        extra = ""
                        if disclosure_count_before_threshold > 0 and disclosure_passed == 0 and min_distance is not None and closest_doc is None:
                            extra = f", 최소거리={min_distance:.4f}"
                        level = logger.warning if disclosure_count_before_threshold > 0 and disclosure_passed == 0 else logger.info
                        level(
                            "[RAG] disclosure: standard_types=%s, 후보=%s, 임계값 통과=%s (threshold=%.2f)%s",
                            standard_types,
                            disclosure_count_before_threshold,
                            disclosure_passed,
                            RAG_DISTANCE_THRESHOLD,
                            extra,
                        )
                    finally:
                        db.close()
                else:
                    logger.warning("RAG disclosure: embed_query 사용 가능한 모델 없음, disclosure 검색 생략")
            except Exception as e:
                logger.warning("RAG disclosure(테이블) 검색 실패: %s", e, exc_info=True)
            if all_docs:
                context = _build_context_with_sources(all_docs)
                logger.info(
                    "[RAG] context 사용: main=%s, disclosure 포함 총 %s건",
                    main_count,
                    len(all_docs),
                )
                return {"context": context}
            logger.info(
                "[RAG] 검색 결과 없음 (main=%s, disclosure 후보=%s, threshold=%.2f)",
                main_count,
                disclosure_count_before_threshold,
                RAG_DISTANCE_THRESHOLD,
            )
        return {"context": ""}
    except Exception as e:
        logger.warning("RAG 검색 실패: %s", e)
        return {"context": ""}


# --- 3. 체크포인터 ---

_checkpointer: Optional[MemorySaver] = None


def get_checkpointer() -> MemorySaver:
    """체크포인터 인스턴스 반환 (싱글톤)."""
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = MemorySaver()
    return _checkpointer


def get_thread_config(thread_id: Optional[str] = None) -> Dict[str, Any]:
    """스레드 설정 반환."""
    if thread_id:
        return {"configurable": {"thread_id": thread_id}}
    return {}


# --- 4. 조건 (라우팅) ---
def should_use_tools(state: ChatState) -> Literal["tools", "__end__"]:
    """도구 사용 여부 결정. tool_calls 있으면 tools, 없으면 종료."""
    messages = state.get("messages", [])
    if not messages:
        return "__end__"
    last_message = messages[-1]
    if isinstance(last_message, AIMessage):
        tool_calls = getattr(last_message, "tool_calls", None)
        if tool_calls:
            return "tools"
    return "__end__"


# --- 5. 그래프 빌더 ---
_default_graph = None


def build_agent_graph(use_checkpointer: bool = True):
    """에이전트 그래프 빌드. RAG는 항상 사용 (진입점: rag → model)."""
    graph = StateGraph(ChatState)
    graph.add_node("rag", rag_node)
    graph.add_node("model", model_node)
    graph.add_node("tools", tool_node)

    # 진입점: rag → model (RAG 항상 사용)
    graph.set_entry_point("rag")
    graph.add_edge("rag", "model")

    graph.add_conditional_edges(
        "model",
        should_use_tools,
        {"tools": "tools", "__end__": END},
    )
    graph.add_edge("tools", "model")

    checkpointer = get_checkpointer() if use_checkpointer else None
    return graph.compile(checkpointer=checkpointer)


def get_default_graph():
    """기본 에이전트 그래프 반환 (싱글톤)."""
    global _default_graph
    if _default_graph is None:
        _default_graph = build_agent_graph(use_checkpointer=True)
    return _default_graph


__all__ = [
    "get_checkpointer",
    "get_thread_config",
    "should_use_tools",
    "TOOLS",
    "TOOL_MAP",
    "build_agent_graph",
    "get_default_graph",
    "model_node",
    "rag_node",
    "tool_node",
]
