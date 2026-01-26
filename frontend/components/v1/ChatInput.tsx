"use client";

import { useState, KeyboardEvent } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input);
      setInput("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="p-4 bg-[#16213e] border-t border-[rgba(102,126,234,0.2)] md:p-3">
      <div className="flex gap-3 items-end max-w-full">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="메시지를 입력하세요... (Enter로 전송, Shift+Enter로 줄바꿈)"
          disabled={disabled}
          rows={1}
          className="flex-1 px-4 py-3 border border-[rgba(102,126,234,0.3)] rounded-[1.5rem] text-[0.95rem] font-inherit resize-none max-h-[120px] overflow-y-auto transition-all bg-[rgba(255,255,255,0.05)] text-[#e0e0e0] placeholder:text-[#666] focus:outline-none focus:border-[#667eea] focus:shadow-[0_0_0_3px_rgba(102,126,234,0.1)] disabled:bg-[rgba(255,255,255,0.02)] disabled:cursor-not-allowed disabled:text-[#666] md:text-sm md:px-[0.9rem] md:py-[0.6rem]"
        />
        <Button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          className="w-11 h-11 border-none rounded-full bg-gradient-to-br from-[#667eea] to-[#764ba2] text-white cursor-pointer flex items-center justify-center transition-all flex-shrink-0 hover:scale-105 hover:shadow-[0_4px_12px_rgba(102,126,234,0.4)] active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed md:w-10 md:h-10"
          aria-label="메시지 전송"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </Button>
      </div>
    </div>
  );
}
