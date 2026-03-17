import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <div className="mx-auto w-full max-w-2xl space-y-8 text-center">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold text-primary">스마트 문진</h1>
          <p className="text-muted-foreground">
            증상을 알려주시면 맞춤 검진 패키지를 추천해 드립니다.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Link href="/chat" className="block">
            <Card className="h-full cursor-pointer transition-shadow hover:ring-2 hover:ring-primary/30">
              <CardHeader>
                <CardTitle className="text-lg">채팅형 문진</CardTitle>
                <CardDescription>자연어로 편하게</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  자연어로 편하게 증상을 설명해보세요. AI가 후속 질문을 통해
                  정확한 정보를 수집합니다.
                </p>
              </CardContent>
            </Card>
          </Link>

          <Link href="/questionnaire" className="block">
            <Card className="h-full cursor-pointer transition-shadow hover:ring-2 hover:ring-primary/30">
              <CardHeader>
                <CardTitle className="text-lg">선택형 문진</CardTitle>
                <CardDescription>체크박스로 빠르게</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  체크박스로 빠르게 증상을 선택하세요. 간단한 정보 입력만으로
                  검진을 추천받을 수 있습니다.
                </p>
              </CardContent>
            </Card>
          </Link>
        </div>
      </div>
    </div>
  );
}
