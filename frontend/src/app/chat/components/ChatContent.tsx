"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useChat } from "@/hooks/useChat";
import { ChatBubble } from "./ChatBubble";
import { ChatInput } from "./ChatInput";

export function ChatContent() {
  const router = useRouter();
  const {
    messages,
    isLoading,
    isComplete,
    turn,
    maxTurns,
    error,
    sessionId,
    startSession,
    sendMessage,
    completeAnalysis,
  } = useChat();

  const [age, setAge] = useState<number | "">("");
  const [gender, setGender] = useState<"M" | "F" | "">("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleStartSession = async () => {
    if (!age || !gender) return;
    await startSession(Number(age), gender);
  };

  const handleComplete = async () => {
    setIsAnalyzing(true);
    try {
      const sessionKey = await completeAnalysis();
      router.push(`/result/${sessionKey}`);
    } catch {
      setIsAnalyzing(false);
    }
  };

  if (!sessionId) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
        <div className="mx-auto w-full max-w-md space-y-8">
          <div className="text-center space-y-2">
            <h1 className="text-2xl font-bold text-primary">채팅형 문진</h1>
            <p className="text-sm text-muted-foreground">
              기본 정보를 입력하면 AI가 증상에 대해 질문합니다.
            </p>
          </div>

          <div className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="age">나이</Label>
              <input
                id="age"
                type="number"
                min={1}
                max={150}
                value={age}
                onChange={(e) => setAge(e.target.value ? Number(e.target.value) : "")}
                placeholder="나이를 입력해주세요"
                className="flex h-9 w-full rounded-lg border border-input bg-transparent px-3 py-1 text-sm transition-colors placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
              />
            </div>

            <div className="space-y-2">
              <Label>성별</Label>
              <RadioGroup
                value={gender}
                onValueChange={(val) => setGender(val as "M" | "F")}
                className="flex gap-4"
              >
                <Label className="flex cursor-pointer items-center gap-2 rounded-lg border border-input px-4 py-3 transition-colors has-[:checked]:border-primary has-[:checked]:bg-secondary">
                  <RadioGroupItem value="M" />
                  <span>남성</span>
                </Label>
                <Label className="flex cursor-pointer items-center gap-2 rounded-lg border border-input px-4 py-3 transition-colors has-[:checked]:border-primary has-[:checked]:bg-secondary">
                  <RadioGroupItem value="F" />
                  <span>여성</span>
                </Label>
              </RadioGroup>
            </div>

            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}

            <Button
              onClick={handleStartSession}
              disabled={!age || !gender || isLoading}
              className="w-full"
            >
              {isLoading ? "시작 중..." : "채팅 시작"}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-background">
      <div className="border-b px-4 py-3 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-primary">채팅형 문진</h1>
        <span className="text-sm text-muted-foreground">{turn}/{maxTurns}</span>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="mx-auto max-w-3xl space-y-3">
          {messages.map((msg, idx) => (
            <ChatBubble key={idx} message={msg} />
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="rounded-2xl rounded-bl-sm bg-secondary px-4 py-2.5 text-sm text-muted-foreground">
                입력 중...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {error && (
        <div className="border-t bg-destructive/10 px-4 py-2 text-center text-sm text-destructive">
          {error}
        </div>
      )}

      {isComplete ? (
        <div className="border-t bg-background p-4">
          <div className="mx-auto max-w-3xl">
            <Button
              onClick={handleComplete}
              disabled={isAnalyzing}
              className="w-full"
            >
              {isAnalyzing ? "분석 중..." : "분석 시작하기"}
            </Button>
          </div>
        </div>
      ) : (
        <ChatInput onSend={sendMessage} disabled={isLoading} />
      )}
    </div>
  );
}
