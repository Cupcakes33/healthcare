"use client";

import type { RedFlagResult } from "@/types";
import { AlertTriangle, ShieldAlert, Siren } from "lucide-react";

const FLAG_CONFIG = {
  CAUTION: {
    icon: AlertTriangle,
    bg: "bg-yellow-50 border-yellow-300",
    text: "text-yellow-800",
    label: "주의 관찰",
  },
  URGENT: {
    icon: ShieldAlert,
    bg: "bg-orange-50 border-orange-300",
    text: "text-orange-800",
    label: "빠른 진료 필요",
  },
  EMERGENCY: {
    icon: Siren,
    bg: "bg-red-50 border-red-400",
    text: "text-red-800",
    label: "즉시 응급실 방문",
  },
} as const;

interface RedFlagBannerProps {
  redFlag: RedFlagResult;
}

export function RedFlagBanner({ redFlag }: RedFlagBannerProps) {
  if (redFlag.level === "NONE") return null;

  const config = FLAG_CONFIG[redFlag.level];
  const Icon = config.icon;

  return (
    <div className={`rounded-lg border p-4 ${config.bg}`}>
      <div className={`flex items-center gap-2 font-semibold ${config.text}`}>
        <Icon className="size-5" />
        <span>{config.label}</span>
      </div>
      <p className={`mt-2 text-sm ${config.text}`}>{redFlag.message}</p>
      {redFlag.matched_rules.length > 0 && (
        <ul className={`mt-2 list-inside list-disc text-sm ${config.text}/80`}>
          {redFlag.matched_rules.map((rule) => (
            <li key={rule}>{rule}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
