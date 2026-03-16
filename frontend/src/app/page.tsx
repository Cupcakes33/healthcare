import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background">
      <div className="mx-auto max-w-md space-y-8 text-center">
        <h1 className="text-4xl font-bold text-primary">
          스마트 문진
        </h1>
        <p className="text-muted-foreground">
          증상을 선택하면 맞춤 검진 패키지를 추천해 드립니다.
        </p>
        <Button size="lg" render={<Link href="/questionnaire" />}>
          문진 시작하기
        </Button>
      </div>
    </div>
  );
}
