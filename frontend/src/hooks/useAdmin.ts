"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getStats,
  getPackages,
  getPackageDetail,
  createPackage,
  updatePackage,
  deletePackage,
} from "@/lib/api-client";
import type { PackageFormData } from "@/types";

export function useAdminStats() {
  return useQuery({
    queryKey: ["admin-stats"],
    queryFn: getStats,
  });
}

export function usePackages(isActive?: boolean) {
  return useQuery({
    queryKey: ["admin-packages", isActive],
    queryFn: () => getPackages(isActive),
  });
}

export function usePackageDetail(id: number | null) {
  return useQuery({
    queryKey: ["admin-package-detail", id],
    queryFn: () => getPackageDetail(id!),
    enabled: id != null,
  });
}

export function useCreatePackage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PackageFormData) => createPackage(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-packages"] });
    },
  });
}

export function useUpdatePackage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: PackageFormData }) =>
      updatePackage(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["admin-packages"] });
      queryClient.invalidateQueries({
        queryKey: ["admin-package-detail", id],
      });
    },
  });
}

export function useDeletePackage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deletePackage,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-packages"] });
    },
  });
}
