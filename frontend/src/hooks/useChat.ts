"use client";

import { useCallback, useState } from "react";
import { startChat, sendChatMessage, completeChat } from "@/lib/api-client";
import type { ExtractedData } from "@/types";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  isComplete: boolean;
  turn: number;
  maxTurns: number;
  extractedData: ExtractedData | null;
  error: string | null;
  sessionId: string | null;
  startSession: (age: number, gender: "M" | "F") => Promise<void>;
  sendMessage: (message: string) => Promise<void>;
  completeAnalysis: () => Promise<string>;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [turn, setTurn] = useState(0);
  const [maxTurns, setMaxTurns] = useState(8);
  const [extractedData, setExtractedData] = useState<ExtractedData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const startSession = useCallback(async (age: number, gender: "M" | "F") => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await startChat({ age, gender });
      setSessionId(response.chat_session_id);
      setTurn(response.turn);
      setMaxTurns(response.max_turns);
      setMessages([
        {
          role: "assistant",
          content: response.message,
          timestamp: new Date(),
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "세션 생성에 실패했습니다");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const sendMessage = useCallback(async (message: string) => {
    if (!sessionId) return;

    setIsLoading(true);
    setError(null);

    setMessages((prev) => [
      ...prev,
      { role: "user", content: message, timestamp: new Date() },
    ]);

    try {
      const response = await sendChatMessage({
        chat_session_id: sessionId,
        message,
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.message,
          timestamp: new Date(),
        },
      ]);
      setTurn(response.turn);
      setIsComplete(response.is_complete);
      if (response.extracted_so_far) {
        setExtractedData(response.extracted_so_far);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "메시지 전송에 실패했습니다");
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const completeAnalysis = useCallback(async (): Promise<string> => {
    if (!sessionId) {
      throw new Error("활성 세션이 없습니다");
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await completeChat({ chat_session_id: sessionId });
      return response.session_key;
    } catch (err) {
      const message = err instanceof Error ? err.message : "분석 요청에 실패했습니다";
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  return {
    messages,
    isLoading,
    isComplete,
    turn,
    maxTurns,
    extractedData,
    error,
    sessionId,
    startSession,
    sendMessage,
    completeAnalysis,
  };
}
