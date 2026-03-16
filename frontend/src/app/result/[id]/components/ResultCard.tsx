"use client";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { PackageRecommendation } from "@/types";

interface ResultCardProps {
  recommendation: PackageRecommendation;
  rank: number;
}

export function ResultCard({ recommendation, rank }: ResultCardProps) {
  const scorePercent = Math.round(recommendation.match_score * 100);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <span className="flex size-6 items-center justify-center rounded-full bg-accent text-xs font-bold text-accent-foreground">
              {rank}
            </span>
            {recommendation.package_name}
          </span>
          <span className="text-sm font-medium text-accent-foreground">
            {scorePercent}% 매칭
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-foreground">{recommendation.reason}</p>
        {recommendation.matched_tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {recommendation.matched_tags.map((tag) => (
              <span
                key={tag}
                className="rounded-md bg-secondary px-2 py-0.5 text-xs text-secondary-foreground"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
