import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { useForm, FormProvider } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { BasicInfoStep } from "@/app/questionnaire/components/BasicInfoStep";
import { SymptomStep } from "@/app/questionnaire/components/SymptomStep";
import { DetailStep } from "@/app/questionnaire/components/DetailStep";
import { questionnaireSchema, type QuestionnaireSchema } from "@/lib/schema";

function FormWrapper({
  children,
  defaultValues,
}: {
  children: (form: ReturnType<typeof useForm<QuestionnaireSchema>>) => React.ReactNode;
  defaultValues?: Partial<QuestionnaireSchema>;
}) {
  const form = useForm<QuestionnaireSchema>({
    resolver: zodResolver(questionnaireSchema),
    defaultValues: {
      age: undefined as unknown as number,
      gender: undefined as unknown as "M" | "F",
      symptoms: [],
      duration: "",
      existingConditions: [],
      ...defaultValues,
    },
  });

  return <FormProvider {...form}>{children(form)}</FormProvider>;
}

describe("BasicInfoStep", () => {
  it("나이 입력 필드를 렌더링한다", () => {
    // when
    render(
      <FormWrapper>
        {(form) => <BasicInfoStep form={form} />}
      </FormWrapper>
    );

    // then
    expect(screen.getByLabelText("나이")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("나이를 입력해주세요")).toBeInTheDocument();
  });

  it("성별 선택 라디오 버튼을 렌더링한다", () => {
    // when
    render(
      <FormWrapper>
        {(form) => <BasicInfoStep form={form} />}
      </FormWrapper>
    );

    // then
    expect(screen.getByText("남성")).toBeInTheDocument();
    expect(screen.getByText("여성")).toBeInTheDocument();
  });

  it("나이를 입력할 수 있다", () => {
    // when
    render(
      <FormWrapper>
        {(form) => <BasicInfoStep form={form} />}
      </FormWrapper>
    );

    // then
    const ageInput = screen.getByLabelText("나이") as HTMLInputElement;
    fireEvent.change(ageInput, { target: { value: "30" } });
    expect(ageInput.value).toBe("30");
  });
});

describe("SymptomStep", () => {
  it("증상 카테고리를 렌더링한다", () => {
    // when
    render(
      <FormWrapper>
        {(form) => <SymptomStep form={form} />}
      </FormWrapper>
    );

    // then
    expect(screen.getByText("심혈관")).toBeInTheDocument();
    expect(screen.getByText("신경계")).toBeInTheDocument();
    expect(screen.getByText("소화기")).toBeInTheDocument();
    expect(screen.getByText("호흡기")).toBeInTheDocument();
    expect(screen.getByText("전신")).toBeInTheDocument();
  });

  it("증상 체크박스를 렌더링한다", () => {
    // when
    render(
      <FormWrapper>
        {(form) => <SymptomStep form={form} />}
      </FormWrapper>
    );

    // then
    expect(screen.getByText("흉통")).toBeInTheDocument();
    expect(screen.getByText("두통")).toBeInTheDocument();
    expect(screen.getByText("피로감")).toBeInTheDocument();
  });
});

describe("DetailStep", () => {
  it("증상 지속 기간 라벨을 렌더링한다", () => {
    // when
    render(
      <FormWrapper>
        {(form) => <DetailStep form={form} />}
      </FormWrapper>
    );

    // then
    expect(screen.getByText("증상 지속 기간")).toBeInTheDocument();
  });

  it("기저질환 체크박스를 렌더링한다", () => {
    // when
    render(
      <FormWrapper>
        {(form) => <DetailStep form={form} />}
      </FormWrapper>
    );

    // then
    expect(screen.getByText("고혈압")).toBeInTheDocument();
    expect(screen.getByText("당뇨")).toBeInTheDocument();
    expect(screen.getByText("심장질환")).toBeInTheDocument();
  });

  it("기저질환 라벨 텍스트를 표시한다", () => {
    // when
    render(
      <FormWrapper>
        {(form) => <DetailStep form={form} />}
      </FormWrapper>
    );

    // then
    expect(screen.getByText("기저질환 (해당 사항 선택)")).toBeInTheDocument();
  });
});
