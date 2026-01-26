"""
LangChain RAG 채팅 서비스

벡터 스토어 기반 RAG 채팅 기능을 제공합니다.
서버 초기화 및 채팅 API를 위한 전체 인터페이스를 제공합니다.
"""

import os
import warnings
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from core.config import settings  # type: ignore
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable


class ChatService:
    """RAG 기반 채팅 서비스.

    server.py에서 사용하는 전체 인터페이스를 제공합니다.
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        collection_name: Optional[str] = None,
        model_name_or_path: Optional[str] = None,
    ):
        """ChatService 초기화.

        Args:
            connection_string: PostgreSQL 연결 문자열
            collection_name: PGVector 컬렉션 이름
            model_name_or_path: 모델 경로 (선택적)
        """
        self.connection_string = connection_string
        self.collection_name = collection_name
        self.model_name_or_path = model_name_or_path

        # 초기화 상태
        self.local_embeddings = None
        self.local_llm = None
        self.local_rag_chain: Optional[Runnable] = None
        self.vector_store = None

    def initialize_embeddings(self):
        """Embedding 모델 초기화."""
        import torch

        try:
            # langchain-huggingface 사용
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
            except ImportError:
                from langchain_community.embeddings import HuggingFaceEmbeddings

            from core.config import get_settings  # type: ignore

            settings = get_settings()

            # GPU 필수 확인
            if not torch.cuda.is_available():
                raise RuntimeError(
                    "CUDA가 사용 불가능합니다. GPU가 필요합니다.\n"
                    "torch.cuda.is_available()이 False입니다."
                )
            
            # EMBEDDING_DEVICE 환경 변수 또는 CUDA 사용
            embedding_device = settings.embedding_device
            if embedding_device is None:
                embedding_device = "cuda"  # GPU 전용

            self.local_embeddings = HuggingFaceEmbeddings(
                model_name=settings.default_embedding_model,
                model_kwargs={"device": embedding_device},
            )
            # 간단한 테스트
            self.local_embeddings.embed_query("test")
            print(
                f"[OK] 로컬 Embedding 모델 초기화 완료 (sentence-transformers, device={embedding_device})"
            )
        except Exception as e:
            print(f"[WARNING] 로컬 Embedding 모델 초기화 실패: {str(e)[:100]}...")
            self.local_embeddings = None

    def initialize_llm(self):
        """LLM 모델 초기화 - 조건부 로딩."""
        from core.config import get_settings  # type: ignore

        settings = get_settings()
        # EXAONE은 LangGraph에서 사용되므로 local_llm은 None으로 설정
        self.local_llm = None

    def initialize_rag_chain(self):
        """RAG 체인 초기화."""
        if self.local_llm and self.local_embeddings and self.connection_string:
            try:
                self.local_rag_chain = self._create_rag_chain(
                    self.local_llm, self.local_embeddings
                )
                print("[OK] 로컬 RAG 체인 초기화 완료")
            except Exception as e:
                print(f"[WARNING] 로컬 RAG 체인 초기화 실패: {str(e)[:100]}...")
                self.local_rag_chain = None
        else:
            print("[WARNING] RAG 체인 초기화 건너뜀 (LLM 또는 Embeddings 없음)")

    def _create_rag_chain(self, llm_model, embeddings_model) -> Runnable:
        """RAG 체인 생성."""
        # LangChain 1.x 호환: langchain 또는 langchain_classic에서 import 시도
        try:
            from langchain.chains import (
                create_history_aware_retriever,
                create_retrieval_chain,
            )
            from langchain.chains.combine_documents import create_stuff_documents_chain
        except ImportError:
            # 하위 호환성: langchain-classic 패키지 사용
            try:
                from langchain_classic.chains import (
                    create_history_aware_retriever,
                    create_retrieval_chain,
                )
                from langchain_classic.chains.combine_documents import (
                    create_stuff_documents_chain,
                )
            except ImportError:
                # 최신 LangChain 1.x: 다른 경로에서 import 시도
                from langchain.chains.history_aware_retriever import create_history_aware_retriever
                from langchain.chains.retrieval import create_retrieval_chain
                from langchain.chains.combine_documents import create_stuff_documents_chain
        
        from langchain_community.vectorstores import PGVector

        # Retriever 생성
        current_vector_store = PGVector(
            embedding_function=embeddings_model,
            collection_name=self.collection_name,
            connection_string=self.connection_string,
        )
        retriever = current_vector_store.as_retriever(search_kwargs={"k": 3})

        # 대화 기록을 고려한 검색 쿼리 생성 프롬프트
        contextualize_q_system_prompt = (
            "대화 기록과 최신 사용자 질문이 주어졌을 때, "
            "대화 기록의 맥락을 참고하여 독립적으로 이해할 수 있는 질문으로 재구성하세요. "
            "질문에 답하지 말고, 필요시 재구성하고 그렇지 않으면 그대로 반환하세요."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        # 대화 기록을 고려한 Retriever 생성
        history_aware_retriever = create_history_aware_retriever(
            llm_model, retriever, contextualize_q_prompt
        )

        # 질문 답변 프롬프트
        qa_system_prompt = (
            "당신은 LangChain과 PGVector를 사용하는 도움이 되는 AI 어시스턴트입니다. "
            "다음 검색된 컨텍스트 정보를 참고하여 사용자의 질문에 답변해주세요. "
            "컨텍스트에 답변할 수 없는 질문이면, 정중하게 그렇게 말씀해주세요. "
            "답변은 최대 3문장으로 간결하게 작성해주세요.\n\n"
            "컨텍스트:\n{context}"
        )
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        # 문서 결합 체인 생성
        question_answer_chain = create_stuff_documents_chain(llm_model, qa_prompt)

        # 최종 RAG 체인 생성
        rag_chain = create_retrieval_chain(
            history_aware_retriever, question_answer_chain
        )

        return rag_chain

    def chat_with_rag(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        model_type: str = "local",
    ) -> str:
        """RAG 체인을 사용하여 채팅합니다.

        Args:
            message: 사용자 메시지
            history: 대화 기록 [{"role": "user", "content": "..."}, ...]
            model_type: 모델 타입 ("local", "openai" 등)

        Returns:
            AI 응답
        """
        if not self.local_rag_chain:
            raise RuntimeError("RAG 체인이 초기화되지 않았습니다.")

        # 대화 기록 변환
        chat_history: List[BaseMessage] = []
        if history:
            for msg in history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    chat_history.append(HumanMessage(content=content))
                elif role == "assistant":
                    chat_history.append(AIMessage(content=content))

        # RAG 체인 실행
        result = self.local_rag_chain.invoke(
            {"input": message, "chat_history": chat_history}
        )

        return result.get("answer", "응답을 생성할 수 없습니다.")

    async def chat_with_rag_stream(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        model_type: str = "local",
    ) -> AsyncGenerator[str, None]:
        """RAG 체인을 사용하여 스트리밍 채팅합니다.

        Args:
            message: 사용자 메시지
            history: 대화 기록
            model_type: 모델 타입

        Yields:
            응답 청크
        """
        if not self.local_rag_chain:
            yield "RAG 체인이 초기화되지 않았습니다."
            return

        # 대화 기록 변환
        chat_history: List[BaseMessage] = []
        if history:
            for msg in history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    chat_history.append(HumanMessage(content=content))
                elif role == "assistant":
                    chat_history.append(AIMessage(content=content))

        # 디버그 모드 확인
        debug_mode = settings.debug_streaming
        important_events = [
            "on_chain_start",
            "on_chain_end",
            "on_chat_model_start",
            "on_chat_model_end",
            "on_llm_start",
            "on_llm_end",
        ]

        # 스트리밍 실행
        last_yielded_content = ""

        async for event in self.local_rag_chain.astream_events(
            {"input": message, "chat_history": chat_history}, version="v2"
        ):
            event_type = event.get("event", "")
            event_name = event.get("name", "")
            data = event.get("data", {})

            # 디버그 로깅 (중요 이벤트만)
            if debug_mode and event_type in important_events:
                print(
                    f"[DEBUG] Event: {event_type}, Name: {event_name}, Data keys: {list(data.keys())}"
                )

            # 스트리밍 청크 처리
            if event_type == "on_chat_model_stream":
                chunk = data.get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    yield chunk.content
                    last_yielded_content += chunk.content

            elif event_type == "on_llm_stream":
                chunk = data.get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    yield chunk.content
                    last_yielded_content += chunk.content


async def stream_chat(
    message: str,
    vector_store=None,
    chat_history: Optional[List[BaseMessage]] = None,
    system_prompt: Optional[str] = None,
    use_rag: bool = True,
) -> AsyncGenerator[str, None]:
    """스트리밍 방식으로 채팅합니다 (독립 함수).

    Args:
        message: 사용자 메시지
        vector_store: 벡터 스토어 인스턴스
        chat_history: 이전 대화 기록
        system_prompt: 시스템 프롬프트
        use_rag: RAG 사용 여부

    Yields:
        응답 청크
    """
    from core.llm.providers.llm_provider import get_llm  # type: ignore

    llm = get_llm()

    # 컨텍스트 검색
    context = ""
    if use_rag and vector_store:
        try:
            docs = vector_store.similarity_search(message, k=3)
            if docs:
                context = "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"[WARNING] RAG 검색 실패: {e}")

    # 프롬프트 구성
    if system_prompt:
        system_content = system_prompt
    else:
        system_content = "당신은 도움이 되는 AI 어시스턴트입니다."

    if context:
        system_content += f"\n\n참고 컨텍스트:\n{context}"

    # 메시지 구성
    messages: List[BaseMessage] = [SystemMessage(content=system_content)]

    if chat_history:
        messages.extend(chat_history)

    messages.append(HumanMessage(content=message))

    # 디버그 모드 확인
    debug_mode = os.environ.get("DEBUG_STREAMING", "").lower() == "true"
    important_events = [
        "on_chain_start",
        "on_chain_end",
        "on_chat_model_start",
        "on_chat_model_end",
        "on_llm_start",
        "on_llm_end",
    ]

    # 스트리밍 실행
    async for event in llm.astream_events(messages, version="v2"):
        event_type = event.get("event", "")
        event_name = event.get("name", "")
        data = event.get("data", {})

        # 디버그 로깅 (중요 이벤트만)
        if debug_mode and event_type in important_events:
            print(
                f"[DEBUG] Event: {event_type}, Name: {event_name}, Data keys: {list(data.keys())}"
            )

        # 스트리밍 청크 처리
        if event_type == "on_chat_model_stream":
            chunk = data.get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                yield chunk.content

        elif event_type == "on_llm_stream":
            chunk = data.get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                yield chunk.content
