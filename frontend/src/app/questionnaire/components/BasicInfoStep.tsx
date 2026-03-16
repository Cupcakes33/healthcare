"use client";

import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import type { UseFormReturn } from "react-hook-form";
import type { QuestionnaireSchema } from "@/lib/schema";

interface BasicInfoStepProps {
  form: UseFormReturn<QuestionnaireSchema>;
}

export function BasicInfoStep({ form }: BasicInfoStepProps) {
  const {
    register,
    setValue,
    watch,
    formState: { errors },
  } = form;

  const gender = watch("gender");

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="age">나이</Label>
        <input
          id="age"
          type="number"
          min={1}
          max={150}
          placeholder="나이를 입력해주세요"
          className="flex h-9 w-full rounded-lg border border-input bg-transparent px-3 py-1 text-sm transition-colors placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
          {...register("age", { valueAsNumber: true })}
        />
        {errors.age && (
          <p className="text-sm text-destructive">{errors.age.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label>성별</Label>
        <RadioGroup
          value={gender ?? ""}
          onValueChange={(val) => setValue("gender", val as "M" | "F", { shouldValidate: true })}
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
        {errors.gender && (
          <p className="text-sm text-destructive">{errors.gender.message}</p>
        )}
      </div>
    </div>
  );
}
