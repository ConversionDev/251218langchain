"use client";

import { ChatPanel } from "@/modules/chat/components/ChatPanel";

export default function ChatPage() {
  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <ChatPanel />
    </div>
  );
}
