"use client";

interface RedFlagBannerProps {
  message: string;
}

export function RedFlagBanner({ message }: RedFlagBannerProps) {
  return (
    <div className="bg-destructive/15 border-b border-destructive/30 px-4 py-3 text-center">
      <p className="text-sm font-medium text-destructive">{message}</p>
    </div>
  );
}
