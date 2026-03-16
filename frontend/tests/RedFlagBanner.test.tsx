import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { RedFlagBanner } from "@/app/result/[id]/components/RedFlagBanner";
import type { RedFlagResult } from "@/types";

describe("RedFlagBanner", () => {
  it("NONE 레벨이면 아무것도 렌더링하지 않는다", () => {
    // given
    const redFlag: RedFlagResult = {
      level: "NONE",
      matched_rules: [],
      message: "",
    };

    // when
    const { container } = render(<RedFlagBanner redFlag={redFlag} />);

    // then
    expect(container.innerHTML).toBe("");
  });

  it("CAUTION 레벨이면 '주의 관찰' 라벨을 표시한다", () => {
    // given
    const redFlag: RedFlagResult = {
      level: "CAUTION",
      matched_rules: [],
      message: "주의가 필요합니다.",
    };

    // when
    render(<RedFlagBanner redFlag={redFlag} />);

    // then
    expect(screen.getByText("주의 관찰")).toBeInTheDocument();
    expect(screen.getByText("주의가 필요합니다.")).toBeInTheDocument();
  });

  it("URGENT 레벨이면 '빠른 진료 필요' 라벨을 표시한다", () => {
    // given
    const redFlag: RedFlagResult = {
      level: "URGENT",
      matched_rules: [],
      message: "빠른 진료가 필요합니다.",
    };

    // when
    render(<RedFlagBanner redFlag={redFlag} />);

    // then
    expect(screen.getByText("빠른 진료 필요")).toBeInTheDocument();
  });

  it("EMERGENCY 레벨이면 '즉시 응급실 방문' 라벨을 표시한다", () => {
    // given
    const redFlag: RedFlagResult = {
      level: "EMERGENCY",
      matched_rules: ["흉통 + 팔 방사통"],
      message: "즉시 응급실을 방문해주세요.",
    };

    // when
    render(<RedFlagBanner redFlag={redFlag} />);

    // then
    expect(screen.getByText("즉시 응급실 방문")).toBeInTheDocument();
    expect(screen.getByText("흉통 + 팔 방사통")).toBeInTheDocument();
  });

  it("matched_rules가 있으면 규칙 목록을 렌더링한다", () => {
    // given
    const redFlag: RedFlagResult = {
      level: "CAUTION",
      matched_rules: ["규칙1", "규칙2"],
      message: "주의",
    };

    // when
    render(<RedFlagBanner redFlag={redFlag} />);

    // then
    expect(screen.getByText("규칙1")).toBeInTheDocument();
    expect(screen.getByText("규칙2")).toBeInTheDocument();
  });
});
