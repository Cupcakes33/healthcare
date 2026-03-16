"use client";

import { useState, useCallback } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { submitQuestionnaire } from "@/lib/api-client";
import { questionnaireSchema, type QuestionnaireSchema } from "@/lib/schema";
import { TOTAL_STEPS, DISCLAIMER } from "@/lib/constants";
import { BasicInfoStep } from "./BasicInfoStep";
import { SymptomStep } from "./SymptomStep";
import { DetailStep } from "./DetailStep";
import { Loader2 } from "lucide-react";

const STEP_TITLES = ["기본 정보", "증상 선택", "상세 정보"];

const STEP_FIELDS: (keyof QuestionnaireSchema)[][] = [
  ["age", "gender"],
  ["symptoms"],
  ["duration", "existingConditions"],
];

export function QuestionnaireForm() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const form = useForm<QuestionnaireSchema>({
    resolver: zodResolver(questionnaireSchema),
    defaultValues: {
      age: undefined as unknown as number,
      gender: undefined as unknown as "M" | "F",
      symptoms: [],
      duration: "",
      existingConditions: [],
    },
  });

  const validateCurrentStep = useCallback(async () => {
    const fields = STEP_FIELDS[step];
    return form.trigger(fields);
  }, [form, step]);

  const handleNext = useCallback(async () => {
    const valid = await validateCurrentStep();
    if (valid) setStep((s) => Math.min(s + 1, TOTAL_STEPS - 1));
  }, [validateCurrentStep]);

  const handlePrev = useCallback(() => {
    setStep((s) => Math.max(s - 1, 0));
  }, []);

  const handleSubmit = useCallback(async () => {
    const valid = await validateCurrentStep();
    if (!valid) return;

    const values = form.getValues();
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const response = await submitQuestionnaire({
        age: values.age,
        gender: values.gender,
        symptoms: values.symptoms,
        duration: values.duration,
        existing_conditions: values.existingConditions,
      });
      router.push(`/result/${response.session_key}`);
    } catch (error) {
      setSubmitError(
        error instanceof Error ? error.message : "오류가 발생했습니다"
      );
    } finally {
      setIsSubmitting(false);
    }
  }, [form, router, validateCurrentStep]);

  const progressValue = ((step + 1) / TOTAL_STEPS) * 100;

  return (
    <div className="mx-auto w-full max-w-lg space-y-6">
      <Progress value={progressValue}>
        <span className="text-sm font-medium text-muted-foreground">
          {step + 1} / {TOTAL_STEPS}
        </span>
      </Progress>

      <Card>
        <CardHeader>
          <CardTitle>{STEP_TITLES[step]}</CardTitle>
        </CardHeader>
        <CardContent>
          {step === 0 && <BasicInfoStep form={form} />}
          {step === 1 && <SymptomStep form={form} />}
          {step === 2 && <DetailStep form={form} />}
        </CardContent>
      </Card>

      {submitError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {submitError}
        </div>
      )}

      <div className="flex gap-3">
        {step > 0 && (
          <Button
            variant="outline"
            onClick={handlePrev}
            disabled={isSubmitting}
            className="flex-1"
          >
            이전
          </Button>
        )}
        {step < TOTAL_STEPS - 1 ? (
          <Button onClick={handleNext} className="flex-1">
            다음
          </Button>
        ) : (
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="flex-1 bg-accent text-accent-foreground hover:bg-accent/80"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="animate-spin" />
                분석 중...
              </>
            ) : (
              "분석 시작"
            )}
          </Button>
        )}
      </div>

      <p className="text-center text-xs text-muted-foreground">{DISCLAIMER}</p>
    </div>
  );
}
