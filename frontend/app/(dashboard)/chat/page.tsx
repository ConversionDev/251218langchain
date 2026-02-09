"use client";

import { ChatPanel } from "@/modules/chat/components/ChatPanel";

export default function ChatPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-foreground">채팅</h1>
        <p className="text-muted-foreground">
          RAG로 등록된 데이터를 검색해 답변합니다.
        </p>
      </div>
      <ChatPanel />
    </div>
  );
}
