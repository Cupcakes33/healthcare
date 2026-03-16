"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getPackages, deletePackage } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { PackageFormDialog } from "./PackageFormDialog";
import { Pencil, Trash2, Plus } from "lucide-react";

const GENDER_LABEL: Record<string, string> = {
  M: "남성",
  F: "여성",
  ALL: "전체",
};

export function PackageTable() {
  const queryClient = useQueryClient();
  const [editId, setEditId] = useState<number | null>(null);
  const [createOpen, setCreateOpen] = useState(false);

  const { data: packages, isLoading } = useQuery({
    queryKey: ["admin-packages"],
    queryFn: getPackages,
  });

  const deleteMutation = useMutation({
    mutationFn: deletePackage,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-packages"] });
    },
  });

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-12 rounded bg-muted" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="size-4" />
          패키지 추가
        </Button>
      </div>

      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>이름</TableHead>
              <TableHead className="hidden md:table-cell">병원</TableHead>
              <TableHead className="hidden sm:table-cell">대상</TableHead>
              <TableHead className="hidden sm:table-cell">가격대</TableHead>
              <TableHead>상태</TableHead>
              <TableHead className="w-24">작업</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {packages?.map((pkg) => (
              <TableRow key={pkg.id}>
                <TableCell className="font-medium">{pkg.name}</TableCell>
                <TableCell className="hidden md:table-cell">
                  {pkg.hospital_name}
                </TableCell>
                <TableCell className="hidden sm:table-cell">
                  {GENDER_LABEL[pkg.target_gender] ?? pkg.target_gender}{" "}
                  {pkg.min_age}~{pkg.max_age}세
                </TableCell>
                <TableCell className="hidden sm:table-cell">
                  {pkg.price_range}
                </TableCell>
                <TableCell>
                  <Badge variant={pkg.is_active ? "default" : "secondary"}>
                    {pkg.is_active ? "활성" : "비활성"}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      onClick={() => setEditId(pkg.id)}
                    >
                      <Pencil className="size-3.5" />
                    </Button>
                    <Dialog>
                      <DialogTrigger
                        render={
                          <Button variant="ghost" size="icon-xs">
                            <Trash2 className="size-3.5 text-destructive" />
                          </Button>
                        }
                      />
                      <DialogContent>
                        <DialogTitle>패키지 비활성화</DialogTitle>
                        <DialogDescription>
                          &quot;{pkg.name}&quot;을(를) 비활성화하시겠습니까?
                        </DialogDescription>
                        <DialogFooter>
                          <DialogClose
                            render={
                              <Button variant="outline">취소</Button>
                            }
                          />
                          <DialogClose
                            render={
                              <Button
                                variant="destructive"
                                onClick={() => deleteMutation.mutate(pkg.id)}
                              >
                                비활성화
                              </Button>
                            }
                          />
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </div>
                </TableCell>
              </TableRow>
            ))}
            {packages?.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground">
                  등록된 패키지가 없습니다.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <PackageFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        mode="create"
      />

      {editId !== null && (
        <PackageFormDialog
          open={true}
          onOpenChange={(open) => { if (!open) setEditId(null); }}
          mode="edit"
          packageId={editId}
        />
      )}
    </div>
  );
}
