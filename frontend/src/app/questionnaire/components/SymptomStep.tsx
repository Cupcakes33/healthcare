"use client";

import { useMemo } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { SYMPTOM_OPTIONS } from "@/lib/constants";
import type { UseFormReturn } from "react-hook-form";
import type { QuestionnaireSchema } from "@/lib/schema";

interface SymptomStepProps {
  form: UseFormReturn<QuestionnaireSchema>;
}

export function SymptomStep({ form }: SymptomStepProps) {
  const {
    watch,
    setValue,
    formState: { errors },
  } = form;

  const selectedSymptoms = watch("symptoms");

  const categorized = useMemo(() => {
    const map = new Map<string, typeof SYMPTOM_OPTIONS>();
    for (const symptom of SYMPTOM_OPTIONS) {
      const list = map.get(symptom.category) ?? [];
      list.push(symptom);
      map.set(symptom.category, list);
    }
    return map;
  }, []);

  const toggleSymptom = (code: string) => {
    const current = selectedSymptoms ?? [];
    const next = current.includes(code)
      ? current.filter((c) => c !== code)
      : [...current, code];
    setValue("symptoms", next, { shouldValidate: true });
  };

  return (
    <div className="space-y-6">
      {errors.symptoms && (
        <p className="text-sm text-destructive">{errors.symptoms.message}</p>
      )}
      {Array.from(categorized.entries()).map(([category, symptoms]) => (
        <div key={category} className="space-y-3">
          <h3 className="text-sm font-semibold text-primary">{category}</h3>
          <div className="grid grid-cols-2 gap-2">
            {symptoms.map((symptom) => {
              const checked = selectedSymptoms?.includes(symptom.code) ?? false;
              return (
                <Label
                  key={symptom.code}
                  className="flex cursor-pointer items-center gap-2 rounded-lg border border-input px-3 py-2.5 text-sm transition-colors hover:bg-muted/50 has-[:checked]:border-primary has-[:checked]:bg-secondary"
                >
                  <Checkbox
                    checked={checked}
                    onCheckedChange={() => toggleSymptom(symptom.code)}
                  />
                  <span>{symptom.name}</span>
                </Label>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
