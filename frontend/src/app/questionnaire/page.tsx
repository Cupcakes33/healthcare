import { QuestionnaireForm } from "./components/QuestionnaireForm";

export default function QuestionnairePage() {
  return (
    <main className="min-h-screen bg-background px-4 py-8 md:py-16">
      <div className="mx-auto max-w-lg">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-primary">스마트 문진</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            증상을 선택하면 맞춤 검진 패키지를 추천해 드립니다
          </p>
        </div>
        <QuestionnaireForm />
      </div>
    </main>
  );
}
