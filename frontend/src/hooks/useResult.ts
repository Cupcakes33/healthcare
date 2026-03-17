"use client";

import { useQuery } from "@tanstack/react-query";
import { getResult } from "@/lib/api-client";

export function useResult(sessionKey: string) {
  return useQuery({
    queryKey: ["result", sessionKey],
    queryFn: () => getResult(sessionKey),
  });
}
