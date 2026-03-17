"use client";

import { useResult } from "@/hooks/useResult";
import { DISCLAIMER } from "@/lib/constants";
import { RedFlagBanner } from "./RedFlagBanner";
import { ResultCard } from "./ResultCard";
import { ResultSkeleton } from "./ResultSkeleton";

const GENDER_LABEL: Record<string, string> = { M: "남성", F: "여성" };

interface ResultContentProps {
  sessionKey: string;
}

export function ResultContent({ sessionKey }: ResultContentProps) {
  const { data, isLoading, error } = useResult(sessionKey);

  if (isLoading) return <ResultSkeleton />;

  if (error || !data) {
    return (
      <div className="mx-auto max-w-lg text-center">
        <h2 className="text-lg font-semibold text-destructive">
          결과를 찾을 수 없습니다
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          유효하지 않은 링크이거나 결과가 만료되었습니다.
        </p>
      </div>
    );
  }

  const { summary, input_summary, red_flag, recommendations } = data;

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <section className="space-y-2">
        <h2 className="text-lg font-semibold text-primary">입력 요약</h2>
        <div className="rounded-lg bg-secondary/50 p-4 text-sm space-y-1">
          <p>
            <span className="font-medium">나이:</span> {input_summary.age}세
          </p>
          <p>
            <span className="font-medium">성별:</span>{" "}
            {GENDER_LABEL[input_summary.gender] ?? input_summary.gender}
          </p>
          <p>
            <span className="font-medium">증상:</span>{" "}
            {input_summary.symptoms.join(", ")}
          </p>
          <p>
            <span className="font-medium">지속 기간:</span>{" "}
            {input_summary.duration}
          </p>
          {input_summary.existing_conditions.length > 0 && (
            <p>
              <span className="font-medium">기저질환:</span>{" "}
              {input_summary.existing_conditions.join(", ")}
            </p>
          )}
        </div>
        {summary && (
          <div className="rounded-lg border border-border p-4 text-sm leading-relaxed">
            {summary}
          </div>
        )}
      </section>

      <RedFlagBanner redFlag={red_flag} />

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-primary">
          추천 검진 패키지
        </h2>
        {recommendations.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            추천 가능한 패키지가 없습니다.
          </p>
        ) : (
          recommendations.map((rec, idx) => (
            <ResultCard
              key={rec.package_id}
              recommendation={rec}
              rank={idx + 1}
            />
          ))
        )}
      </section>

      <footer className="rounded-lg bg-muted/50 p-4">
        <p className="text-center text-xs text-muted-foreground">
          {DISCLAIMER}
        </p>
      </footer>
    </div>
  );
}
