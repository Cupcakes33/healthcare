import { Card, CardContent, CardHeader } from "@/components/ui/card";

export function ResultSkeleton() {
  return (
    <div className="mx-auto max-w-lg space-y-6 animate-pulse">
      <div className="space-y-3">
        <div className="h-5 w-24 rounded bg-muted" />
        <div className="h-4 w-full rounded bg-muted" />
        <div className="h-4 w-3/4 rounded bg-muted" />
      </div>

      {[1, 2, 3].map((i) => (
        <Card key={i}>
          <CardHeader>
            <div className="h-5 w-48 rounded bg-muted" />
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="h-4 w-full rounded bg-muted" />
            <div className="h-4 w-2/3 rounded bg-muted" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
