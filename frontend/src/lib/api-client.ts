import { API_BASE_URL } from "@/lib/constants";
import type { QuestionnaireRequest, QuestionnaireResponse } from "@/types";

export async function submitQuestionnaire(
  data: QuestionnaireRequest
): Promise<QuestionnaireResponse> {
  const response = await fetch(`${API_BASE_URL}/questionnaire`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail ?? "문진 제출에 실패했습니다");
  }

  return response.json();
}

export async function getResult(
  sessionKey: string
): Promise<QuestionnaireResponse> {
  const response = await fetch(`${API_BASE_URL}/result/${sessionKey}`);

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail ?? "결과를 불러올 수 없습니다");
  }

  return response.json();
}
