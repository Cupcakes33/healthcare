"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { adminLogin } from "@/lib/api-client";
import { useAuth } from "@/hooks/useAuth";
import { Loader2 } from "lucide-react";

export function LoginForm() {
  const router = useRouter();
  const { login, isAuthenticated, isReady } = useAuth();

  useEffect(() => {
    if (isReady && isAuthenticated) {
      router.replace("/admin/dashboard");
    }
  }, [isReady, isAuthenticated, router]);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError(null);
      setIsLoading(true);

      try {
        const response = await adminLogin({ username, password });
        login(response.token);
        router.push("/admin/dashboard");
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "로그인에 실패했습니다"
        );
      } finally {
        setIsLoading(false);
      }
    },
    [username, password, login, router]
  );

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle className="text-center">관리자 로그인</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="username">아이디</Label>
            <Input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="아이디"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">비밀번호</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="비밀번호"
              required
            />
          </div>
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
          <Button type="submit" disabled={isLoading} className="w-full">
            {isLoading ? (
              <>
                <Loader2 className="animate-spin" />
                로그인 중...
              </>
            ) : (
              "로그인"
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
