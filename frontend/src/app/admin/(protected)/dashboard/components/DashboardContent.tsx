"use client";

import { useAdminStats } from "@/hooks/useAdmin";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function DashboardContent() {
  const { data, isLoading, error } = useAdminStats();

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 animate-pulse">
        {Array.from({ length: 5 }).map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <div className="h-4 w-24 rounded bg-muted" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-16 rounded bg-muted" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error || !data) {
    return (
      <p className="text-sm text-destructive">통계를 불러올 수 없습니다.</p>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="bg-secondary/30">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              총 문진 건수
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{data.total_sessions}</p>
          </CardContent>
        </Card>

        <Card className="bg-secondary/30">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Red Flag 비율
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {Math.round(data.red_flag_ratio * 100)}%
            </p>
          </CardContent>
        </Card>

        <Card className="bg-secondary/30">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              문진 유형별
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1 text-sm">
              {Object.entries(data.intake_type_distribution).map(([type, count]) => {
                const label = type === "CHAT" ? "채팅형" : "선택형";
                const total = data.total_sessions || 1;
                const pct = Math.round((count / total) * 100);
                return (
                  <li key={type} className="flex justify-between">
                    <span>{label}</span>
                    <span className="font-medium">{pct}% ({count}건)</span>
                  </li>
                );
              })}
              {Object.keys(data.intake_type_distribution).length === 0 && (
                <li className="text-muted-foreground">데이터 없음</li>
              )}
            </ul>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">연령대별 분포</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1 text-sm">
              {Object.entries(data.age_distribution).map(([group, count]) => (
                <li key={group} className="flex justify-between">
                  <span>{group}</span>
                  <span className="font-medium">{count}건</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              인기 증상 TOP 5
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1 text-sm">
              {data.top_symptoms.map((s, i) => (
                <li key={s.name} className="flex justify-between">
                  <span>
                    {i + 1}. {s.name}
                  </span>
                  <span className="font-medium">{s.count}건</span>
                </li>
              ))}
              {data.top_symptoms.length === 0 && (
                <li className="text-muted-foreground">데이터 없음</li>
              )}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              인기 패키지 TOP 3
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1 text-sm">
              {data.top_packages.map((p, i) => (
                <li key={p.name} className="flex justify-between">
                  <span>
                    {i + 1}. {p.name}
                  </span>
                  <span className="font-medium">{p.count}건</span>
                </li>
              ))}
              {data.top_packages.length === 0 && (
                <li className="text-muted-foreground">데이터 없음</li>
              )}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
