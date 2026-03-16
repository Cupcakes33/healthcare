import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ResultContent } from "@/app/result/[id]/components/ResultContent";
import { DISCLAIMER } from "@/lib/constants";
import { mockResultNone, mockResultEmergency } from "./fixtures/result";

vi.mock("@/hooks/useResult", () => ({
  useResult: vi.fn(),
}));

import { useResult } from "@/hooks/useResult";

const mockUseResult = vi.mocked(useResult);

describe("ResultContent", () => {
  it("로딩 중일 때 스켈레톤을 표시한다", () => {
    // given
    mockUseResult.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as ReturnType<typeof useResult>);

    // when
    render(<ResultContent sessionKey="test-key" />);

    // then
    expect(screen.queryByText("입력 요약")).not.toBeInTheDocument();
  });

  it("에러 시 에러 메시지를 표시한다", () => {
    // given
    mockUseResult.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("not found"),
    } as ReturnType<typeof useResult>);

    // when
    render(<ResultContent sessionKey="test-key" />);

    // then
    expect(screen.getByText("결과를 찾을 수 없습니다")).toBeInTheDocument();
  });

  it("정상 데이터 시 입력 요약을 표시한다", () => {
    // given
    mockUseResult.mockReturnValue({
      data: mockResultNone,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useResult>);

    // when
    render(<ResultContent sessionKey="test-key" />);

    // then
    expect(screen.getByText("입력 요약")).toBeInTheDocument();
    expect(screen.getAllByText(/45세/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/남성/).length).toBeGreaterThan(0);
  });

  it("추천 패키지 목록을 렌더링한다", () => {
    // given
    mockUseResult.mockReturnValue({
      data: mockResultNone,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useResult>);

    // when
    render(<ResultContent sessionKey="test-key" />);

    // then
    expect(screen.getByText("추천 검진 패키지")).toBeInTheDocument();
    expect(screen.getByText("기본 종합검진")).toBeInTheDocument();
    expect(screen.getByText("뇌신경 검진")).toBeInTheDocument();
  });

  it("면책 조항을 항상 표시한다", () => {
    // given
    mockUseResult.mockReturnValue({
      data: mockResultNone,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useResult>);

    // when
    render(<ResultContent sessionKey="test-key" />);

    // then
    expect(screen.getByText(DISCLAIMER)).toBeInTheDocument();
  });

  it("RedFlag가 NONE이면 배너를 표시하지 않는다", () => {
    // given
    mockUseResult.mockReturnValue({
      data: mockResultNone,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useResult>);

    // when
    render(<ResultContent sessionKey="test-key" />);

    // then
    expect(screen.queryByText("주의 관찰")).not.toBeInTheDocument();
    expect(screen.queryByText("즉시 응급실 방문")).not.toBeInTheDocument();
  });

  it("RedFlag가 EMERGENCY이면 배너를 표시한다", () => {
    // given
    mockUseResult.mockReturnValue({
      data: mockResultEmergency,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useResult>);

    // when
    render(<ResultContent sessionKey="test-key" />);

    // then
    expect(screen.getByText("즉시 응급실 방문")).toBeInTheDocument();
  });

  it("LLM 요약이 있으면 표시한다", () => {
    // given
    mockUseResult.mockReturnValue({
      data: mockResultNone,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useResult>);

    // when
    render(<ResultContent sessionKey="test-key" />);

    // then
    expect(
      screen.getByText("45세 남성 환자가 두통과 피로감을 호소합니다.")
    ).toBeInTheDocument();
  });
});
