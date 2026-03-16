import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ResultCard } from "@/app/result/[id]/components/ResultCard";
import type { PackageRecommendation } from "@/types";

describe("ResultCard", () => {
  const recommendation: PackageRecommendation = {
    package_id: 1,
    package_name: "기본 종합검진",
    match_score: 0.85,
    reason: "두통과 피로감에 대한 기본 검사",
    matched_tags: ["HEADACHE", "FATIGUE"],
  };

  it("패키지명을 렌더링한다", () => {
    // when
    render(<ResultCard recommendation={recommendation} rank={1} />);

    // then
    expect(screen.getByText("기본 종합검진")).toBeInTheDocument();
  });

  it("매칭 점수를 퍼센트로 표시한다", () => {
    // when
    render(<ResultCard recommendation={recommendation} rank={1} />);

    // then
    expect(screen.getByText("85% 매칭")).toBeInTheDocument();
  });

  it("추천 사유를 표시한다", () => {
    // when
    render(<ResultCard recommendation={recommendation} rank={1} />);

    // then
    expect(screen.getByText("두통과 피로감에 대한 기본 검사")).toBeInTheDocument();
  });

  it("순위 배지를 표시한다", () => {
    // when
    render(<ResultCard recommendation={recommendation} rank={2} />);

    // then
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("매칭 태그를 렌더링한다", () => {
    // when
    render(<ResultCard recommendation={recommendation} rank={1} />);

    // then
    expect(screen.getByText("HEADACHE")).toBeInTheDocument();
    expect(screen.getByText("FATIGUE")).toBeInTheDocument();
  });
});
