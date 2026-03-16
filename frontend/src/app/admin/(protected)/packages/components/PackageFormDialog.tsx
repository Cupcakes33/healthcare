"use client";

import { useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import {
  usePackageDetail,
  useCreatePackage,
  useUpdatePackage,
} from "@/hooks/useAdmin";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { SYMPTOM_OPTIONS, CHECKUP_ITEMS } from "@/lib/constants";
import type { PackageFormData } from "@/types";

const RELEVANCE_OPTIONS = [
  { value: 0.2, label: "매우 낮음" },
  { value: 0.4, label: "낮음" },
  { value: 0.6, label: "보통" },
  { value: 0.8, label: "높음" },
  { value: 1.0, label: "매우 높음" },
];

interface PackageFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: "create" | "edit";
  packageId?: number;
}

export function PackageFormDialog({
  open,
  onOpenChange,
  mode,
  packageId,
}: PackageFormDialogProps) {
  const { data: existing } = usePackageDetail(
    mode === "edit" ? (packageId ?? null) : null
  );

  const form = useForm<PackageFormData>({
    defaultValues: {
      name: "",
      description: "",
      hospital_name: "",
      target_gender: "ALL",
      min_age: 20,
      max_age: 80,
      price_range: "",
      symptom_tags: [],
      item_ids: [],
    },
  });

  useEffect(() => {
    if (existing && mode === "edit") {
      form.reset({
        name: existing.name,
        description: existing.description ?? "",
        hospital_name: existing.hospital_name,
        target_gender: existing.target_gender as "M" | "F" | "ALL",
        min_age: existing.min_age,
        max_age: existing.max_age,
        price_range: existing.price_range,
        symptom_tags: existing.symptom_tags.map((t) => ({
          symptom_tag_id: t.id,
          relevance_score: t.relevance_score,
        })),
        item_ids: existing.checkup_items.map((i) => i.id),
      });
    }
  }, [existing, mode, form]);

  const createMut = useCreatePackage();
  const updateMut = useUpdatePackage();

  const isPending = createMut.isPending || updateMut.isPending;
  const mutError = createMut.error || updateMut.error;

  const onSubmit = (data: PackageFormData) => {
    if (data.min_age > data.max_age) {
      form.setError("min_age", { message: "최소 나이는 최대 나이보다 클 수 없습니다" });
      return;
    }
    if (mode === "create") {
      createMut.mutate(data, {
        onSuccess: () => {
          onOpenChange(false);
          form.reset();
        },
      });
    } else {
      updateMut.mutate(
        { id: packageId!, data },
        { onSuccess: () => onOpenChange(false) }
      );
    }
  };

  const targetGender = form.watch("target_gender");
  const symptomTags = form.watch("symptom_tags");
  const itemIds = form.watch("item_ids");

  const selectedTagIds = useMemo(
    () => new Set(symptomTags.map((t) => t.symptom_tag_id)),
    [symptomTags]
  );

  const toggleTag = (tagId: number) => {
    const current = form.getValues("symptom_tags");
    if (selectedTagIds.has(tagId)) {
      form.setValue(
        "symptom_tags",
        current.filter((t) => t.symptom_tag_id !== tagId)
      );
    } else {
      form.setValue("symptom_tags", [
        ...current,
        { symptom_tag_id: tagId, relevance_score: 0.6 },
      ]);
    }
  };

  const updateTagRelevance = (tagId: number, score: number) => {
    const current = form.getValues("symptom_tags");
    form.setValue(
      "symptom_tags",
      current.map((t) =>
        t.symptom_tag_id === tagId ? { ...t, relevance_score: score } : t
      )
    );
  };

  const toggleItem = (itemId: number) => {
    const current = form.getValues("item_ids");
    if (current.includes(itemId)) {
      form.setValue(
        "item_ids",
        current.filter((id) => id !== itemId)
      );
    } else {
      form.setValue("item_ids", [...current, itemId]);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-lg">
        <DialogTitle>
          {mode === "create" ? "패키지 추가" : "패키지 수정"}
        </DialogTitle>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="pkg-name">패키지명</Label>
            <Input
              id="pkg-name"
              {...form.register("name", { required: true })}
              placeholder="패키지명"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="pkg-desc">설명</Label>
            <Input
              id="pkg-desc"
              {...form.register("description")}
              placeholder="패키지 설명"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="pkg-hospital">병원명</Label>
            <Input
              id="pkg-hospital"
              {...form.register("hospital_name", { required: true })}
              placeholder="병원명"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>대상 성별</Label>
              <Select
                value={targetGender}
                onValueChange={(val) => {
                  if (val) form.setValue("target_gender", val as "M" | "F" | "ALL");
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">전체</SelectItem>
                  <SelectItem value="M">남성</SelectItem>
                  <SelectItem value="F">여성</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="pkg-price">가격대</Label>
              <Input
                id="pkg-price"
                {...form.register("price_range", { required: true })}
                placeholder="30만~50만원"
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="pkg-min-age">최소 나이</Label>
                <Input
                  id="pkg-min-age"
                  type="number"
                  {...form.register("min_age", { valueAsNumber: true, min: 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="pkg-max-age">최대 나이</Label>
                <Input
                  id="pkg-max-age"
                  type="number"
                  {...form.register("max_age", { valueAsNumber: true, min: 0 })}
                />
              </div>
            </div>
            {form.formState.errors.min_age && (
              <p className="text-sm text-destructive">
                {form.formState.errors.min_age.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label>증상 태그</Label>
            <div className="max-h-40 overflow-y-auto rounded-lg border p-2 space-y-1">
              {SYMPTOM_OPTIONS.map((symptom) => {
                const isSelected = selectedTagIds.has(symptom.id);
                const tag = symptomTags.find((t) => t.symptom_tag_id === symptom.id);
                return (
                  <div key={symptom.code} className="flex items-center gap-2">
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={() => toggleTag(symptom.id)}
                    />
                    <span className="flex-1 text-sm">{symptom.name}</span>
                    {isSelected && (
                      <select
                        className="h-6 rounded border text-xs"
                        value={tag?.relevance_score ?? 0.6}
                        onChange={(e) =>
                          updateTagRelevance(symptom.id, parseFloat(e.target.value))
                        }
                      >
                        {RELEVANCE_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="space-y-2">
            <Label>검진 항목 (최소 1개)</Label>
            <div className="max-h-40 overflow-y-auto rounded-lg border p-2 space-y-1">
              {CHECKUP_ITEMS.map((item) => (
                <Label
                  key={item.id}
                  className="flex cursor-pointer items-center gap-2 text-sm"
                >
                  <Checkbox
                    checked={itemIds.includes(item.id)}
                    onCheckedChange={() => toggleItem(item.id)}
                  />
                  <span>{item.name}</span>
                </Label>
              ))}
            </div>
          </div>

          {mutError && (
            <p className="text-sm text-destructive">
              {mutError instanceof Error ? mutError.message : "오류가 발생했습니다"}
            </p>
          )}

          <DialogFooter>
            <DialogClose render={<Button variant="outline">취소</Button>} />
            <Button type="submit" disabled={isPending}>
              {isPending ? (
                <>
                  <Loader2 className="animate-spin" />
                  저장 중...
                </>
              ) : mode === "create" ? (
                "추가"
              ) : (
                "수정"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
