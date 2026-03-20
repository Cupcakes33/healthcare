"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useChat } from "@/hooks/useChat";
import { ChatBubble } from "./ChatBubble";
import { ChatInput } from "./ChatInput";
import { TypingIndicator } from "./TypingIndicator";
import { RedFlagBanner } from "./RedFlagBanner";

const EMERGENCY_KEYWORDS = ["응급", "119", "응급실"];

export function ChatContent() {
  const router = useRouter();
  const {
    messages,
    isLoading,
    isComplete,
    canAnalyze,
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
  }, [messages, isLoading]);

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

  const hasEmergency = messages.some(
    (msg) =>
      msg.role === "assistant" &&
      EMERGENCY_KEYWORDS.some((kw) => msg.content.includes(kw))
  );

  const isSessionExpired = error?.includes("찾을 수 없습니다");
  const isRateLimited = error?.includes("요청 횟수");
  const isOverloaded = error?.includes("많은 사용자");

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
              <div className="space-y-2">
                <p className="text-sm text-destructive">{error}</p>
                {isOverloaded && (
                  <p className="text-xs text-muted-foreground">
                    <Link href="/questionnaire" className="underline">
                      선택형 문진
                    </Link>
                    을 이용해보세요.
                  </p>
                )}
              </div>
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

      {hasEmergency && (
        <RedFlagBanner message="응급 증상이 감지되었습니다. 즉시 가까운 응급실을 방문해주세요." />
      )}

      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="mx-auto max-w-3xl space-y-3">
          {messages.map((msg, idx) => (
            <ChatBubble key={idx} message={msg} />
          ))}
          {isLoading && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {error && (
        <div className="border-t bg-destructive/10 px-4 py-3 text-center">
          <p className="text-sm text-destructive">{error}</p>
          {isSessionExpired && (
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={() => router.push("/chat")}
            >
              처음부터 다시 시작
            </Button>
          )}
          {(isRateLimited || isOverloaded) && (
            <p className="mt-1 text-xs text-muted-foreground">
              <Link href="/questionnaire" className="underline">
                선택형 문진
              </Link>
              을 이용해보세요.
            </p>
          )}
        </div>
      )}

      <div className="border-t bg-background p-4">
        <div className="mx-auto max-w-3xl space-y-2">
          {canAnalyze && !isComplete && (
            <p className="text-sm text-muted-foreground text-center">
              충분한 정보가 수집되었습니다. 바로 분석하거나, 대화를 계속할 수 있습니다.
            </p>
          )}

          {turn > 1 && (
            <Button
              onClick={handleComplete}
              disabled={isAnalyzing || isLoading}
              variant={canAnalyze ? "default" : "outline"}
              className="w-full"
            >
              {isAnalyzing ? "분석 중입니다... (약 3~5초 소요)" : "분석 시작하기"}
            </Button>
          )}

          {!isComplete && (
            <ChatInput onSend={sendMessage} disabled={isLoading || !!error} />
          )}
        </div>
      </div>
    </div>
  );
}
