import { API_BASE_URL } from "@/lib/constants";
import { getStoredToken, clearStoredToken } from "@/hooks/useAuth";
import type {
  AdminLoginRequest,
  AdminLoginResponse,
  PackageDetail,
  PackageFormData,
  PackageListItem,
  QuestionnaireRequest,
  QuestionnaireResponse,
  StatsResponse,
} from "@/types";

function parseErrorMessage(body: unknown, fallback: string): string {
  if (body && typeof body === "object") {
    const obj = body as Record<string, unknown>;
    if (obj.error && typeof obj.error === "object") {
      const err = obj.error as Record<string, unknown>;
      if (typeof err.message === "string") return err.message;
    }
    if (typeof obj.detail === "string") return obj.detail;
    if (typeof obj.message === "string") return obj.message;
  }
  return fallback;
}

export async function submitQuestionnaire(
  data: QuestionnaireRequest
): Promise<QuestionnaireResponse> {
  const response = await fetch(`${API_BASE_URL}/questionnaire`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(parseErrorMessage(body, "문진 제출에 실패했습니다"));
  }

  return response.json();
}

export async function getResult(
  sessionKey: string
): Promise<QuestionnaireResponse> {
  const response = await fetch(`${API_BASE_URL}/result/${sessionKey}`);

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(parseErrorMessage(body, "결과를 불러올 수 없습니다"));
  }

  return response.json();
}

function authHeaders(): Record<string, string> {
  const token = getStoredToken();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

async function authFetch(url: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(url, {
    ...init,
    headers: { ...authHeaders(), ...init?.headers },
  });

  if (response.status === 401) {
    clearStoredToken();
    if (typeof window !== "undefined") {
      window.location.href = "/admin/login";
    }
    throw new Error("인증이 만료되었습니다");
  }

  return response;
}

export async function adminLogin(
  data: AdminLoginRequest
): Promise<AdminLoginResponse> {
  const response = await fetch(`${API_BASE_URL}/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    if (response.status === 429) {
      throw new Error("로그인 시도 횟수를 초과했습니다. 잠시 후 다시 시도해주세요.");
    }
    throw new Error("아이디 또는 비밀번호가 올바르지 않습니다");
  }

  return response.json();
}

export async function getStats(): Promise<StatsResponse> {
  const response = await authFetch(`${API_BASE_URL}/admin/stats`);
  if (!response.ok) throw new Error("통계를 불러올 수 없습니다");
  return response.json();
}

export async function getPackages(isActive?: boolean): Promise<PackageListItem[]> {
  const params = isActive != null ? `?is_active=${isActive}` : "";
  const response = await authFetch(`${API_BASE_URL}/admin/packages${params}`);
  if (!response.ok) throw new Error("패키지 목록을 불러올 수 없습니다");
  return response.json();
}

export async function getPackageDetail(id: number): Promise<PackageDetail> {
  const response = await authFetch(`${API_BASE_URL}/admin/packages/${id}`);
  if (!response.ok) throw new Error("패키지를 찾을 수 없습니다");
  return response.json();
}

export async function createPackage(
  data: PackageFormData
): Promise<PackageDetail> {
  const response = await authFetch(`${API_BASE_URL}/admin/packages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(parseErrorMessage(body, "패키지 생성에 실패했습니다"));
  }
  return response.json();
}

export async function updatePackage(
  id: number,
  data: PackageFormData
): Promise<PackageDetail> {
  const response = await authFetch(`${API_BASE_URL}/admin/packages/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(parseErrorMessage(body, "패키지 수정에 실패했습니다"));
  }
  return response.json();
}

export async function deletePackage(id: number): Promise<void> {
  const response = await authFetch(`${API_BASE_URL}/admin/packages/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("패키지 삭제에 실패했습니다");
}
