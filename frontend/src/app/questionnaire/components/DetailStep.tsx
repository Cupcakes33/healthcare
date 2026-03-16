"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DURATION_OPTIONS, EXISTING_CONDITIONS } from "@/lib/constants";
import type { UseFormReturn } from "react-hook-form";
import type { QuestionnaireSchema } from "@/lib/schema";

interface DetailStepProps {
  form: UseFormReturn<QuestionnaireSchema>;
}

export function DetailStep({ form }: DetailStepProps) {
  const {
    watch,
    setValue,
    formState: { errors },
  } = form;

  const duration = watch("duration");
  const existingConditions = watch("existingConditions");

  const toggleCondition = (condition: string) => {
    const current = existingConditions ?? [];
    const next = current.includes(condition)
      ? current.filter((c) => c !== condition)
      : [...current, condition];
    setValue("existingConditions", next);
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label>증상 지속 기간</Label>
        <Select
          value={duration}
          onValueChange={(val) => { if (val) setValue("duration", val, { shouldValidate: true }); }}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="기간을 선택해주세요" />
          </SelectTrigger>
          <SelectContent>
            {DURATION_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.duration && (
          <p className="text-sm text-destructive">{errors.duration.message}</p>
        )}
      </div>

      <div className="space-y-3">
        <Label>기저질환 (해당 사항 선택)</Label>
        <div className="grid grid-cols-2 gap-2">
          {EXISTING_CONDITIONS.map((condition) => {
            const checked = existingConditions?.includes(condition) ?? false;
            return (
              <Label
                key={condition}
                className="flex cursor-pointer items-center gap-2 rounded-lg border border-input px-3 py-2.5 text-sm transition-colors hover:bg-muted/50 has-[:checked]:border-primary has-[:checked]:bg-secondary"
              >
                <Checkbox
                  checked={checked}
                  onCheckedChange={() => toggleCondition(condition)}
                />
                <span>{condition}</span>
              </Label>
            );
          })}
        </div>
      </div>
    </div>
  );
}
