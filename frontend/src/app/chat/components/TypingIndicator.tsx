"use client";

export function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="rounded-2xl rounded-bl-sm bg-secondary px-4 py-3">
        <div className="flex gap-1">
          <span className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-[bounce_1.4s_ease-in-out_infinite]" />
          <span className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-[bounce_1.4s_ease-in-out_0.2s_infinite]" />
          <span className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-[bounce_1.4s_ease-in-out_0.4s_infinite]" />
        </div>
      </div>
    </div>
  );
}
