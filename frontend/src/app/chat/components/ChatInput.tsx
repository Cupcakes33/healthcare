"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

const MAX_LENGTH = 500;

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t bg-background p-4">
      <div className="mx-auto flex max-w-3xl items-end gap-2">
        <div className="relative flex-1">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value.slice(0, MAX_LENGTH))}
            onKeyDown={handleKeyDown}
            placeholder="증상을 설명해주세요..."
            disabled={disabled}
            rows={1}
            className="flex min-h-[40px] max-h-[120px] w-full resize-none rounded-lg border border-input bg-transparent px-3 py-2.5 text-sm placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none disabled:opacity-50"
          />
          <span className="absolute right-2 bottom-1 text-xs text-muted-foreground">
            {input.length}/{MAX_LENGTH}
          </span>
        </div>
        <Button
          onClick={handleSubmit}
          disabled={disabled || !input.trim()}
          size="sm"
        >
          전송
        </Button>
      </div>
    </div>
  );
}
