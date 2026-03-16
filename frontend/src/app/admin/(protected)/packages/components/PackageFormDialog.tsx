"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createPackage,
  updatePackage,
  getPackageDetail,
} from "@/lib/api-client";
import { Button } from "@/components/ui/button";
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
import type { PackageFormData } from "@/types";

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
  const queryClient = useQueryClient();

  const { data: existing } = useQuery({
    queryKey: ["admin-package-detail", packageId],
    queryFn: () => getPackageDetail(packageId!),
    enabled: mode === "edit" && packageId != null,
  });

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

  const createMut = useMutation({
    mutationFn: (data: PackageFormData) => createPackage(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-packages"] });
      onOpenChange(false);
      form.reset();
    },
  });

  const updateMut = useMutation({
    mutationFn: (data: PackageFormData) => updatePackage(packageId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-packages"] });
      queryClient.invalidateQueries({
        queryKey: ["admin-package-detail", packageId],
      });
      onOpenChange(false);
    },
  });

  const isPending = createMut.isPending || updateMut.isPending;
  const mutError = createMut.error || updateMut.error;

  const onSubmit = (data: PackageFormData) => {
    if (mode === "create") {
      createMut.mutate(data);
    } else {
      updateMut.mutate(data);
    }
  };

  const targetGender = form.watch("target_gender");

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[80vh] overflow-y-auto">
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

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="pkg-min-age">최소 나이</Label>
              <Input
                id="pkg-min-age"
                type="number"
                {...form.register("min_age", { valueAsNumber: true })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="pkg-max-age">최대 나이</Label>
              <Input
                id="pkg-max-age"
                type="number"
                {...form.register("max_age", { valueAsNumber: true })}
              />
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
