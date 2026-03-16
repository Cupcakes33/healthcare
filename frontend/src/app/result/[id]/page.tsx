import { ResultContent } from "./components/ResultContent";

export default async function ResultPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <main className="min-h-screen bg-background px-4 py-8 md:py-16">
      <div className="mx-auto max-w-lg">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-primary">문진 결과</h1>
        </div>
        <ResultContent sessionKey={id} />
      </div>
    </main>
  );
}
