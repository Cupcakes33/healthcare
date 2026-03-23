import type { SymptomOption } from "@/types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const SYMPTOM_OPTIONS: SymptomOption[] = [
  { id: 1, code: "CHEST_PAIN", name: "흉통", category: "심혈관" },
  { id: 2, code: "CHEST_PRESSURE", name: "가슴 압박감", category: "심혈관" },
  { id: 3, code: "PALPITATION", name: "두근거림", category: "심혈관" },
  { id: 4, code: "SHORTNESS_OF_BREATH", name: "호흡곤란", category: "심혈관" },
  { id: 5, code: "ARM_RADIATING_PAIN", name: "팔 방사통", category: "심혈관" },
  { id: 6, code: "JAW_RADIATING_PAIN", name: "턱 방사통", category: "심혈관" },
  { id: 7, code: "BACK_RADIATING_PAIN", name: "등 방사통", category: "심혈관" },
  { id: 8, code: "HEADACHE", name: "두통", category: "신경계" },
  { id: 9, code: "THUNDERCLAP_HEADACHE", name: "벼락두통", category: "신경계" },
  { id: 10, code: "DIZZINESS", name: "어지러움", category: "신경계" },
  { id: 11, code: "NUMBNESS", name: "저림/감각이상", category: "신경계" },
  { id: 12, code: "UNILATERAL_PARALYSIS", name: "편측 마비", category: "신경계" },
  { id: 13, code: "SPEECH_DISORDER", name: "언어장애", category: "신경계" },
  { id: 14, code: "ABDOMINAL_PAIN", name: "복통", category: "소화기" },
  { id: 15, code: "NAUSEA", name: "구역/구토", category: "소화기" },
  { id: 16, code: "HEARTBURN", name: "속쓰림", category: "소화기" },
  { id: 17, code: "COUGH", name: "기침", category: "호흡기" },
  { id: 18, code: "CHRONIC_COUGH", name: "만성 기침", category: "호흡기" },
  { id: 19, code: "SPUTUM", name: "가래", category: "호흡기" },
  { id: 20, code: "WHEEZING", name: "쌕쌕거림", category: "호흡기" },
  { id: 21, code: "FATIGUE", name: "피로감", category: "전신" },
  { id: 22, code: "WEIGHT_LOSS", name: "체중 감소", category: "전신" },
  { id: 23, code: "UNEXPLAINED_WEIGHT_LOSS", name: "원인불명 체중 감소", category: "전신" },
  { id: 24, code: "FEVER", name: "발열", category: "전신" },
];

export const DURATION_OPTIONS = [
  { value: "1주 미만", label: "1주 미만" },
  { value: "1~2주", label: "1~2주" },
  { value: "2~4주", label: "2~4주" },
  { value: "1개월 이상", label: "1개월 이상" },
  { value: "3개월 이상", label: "3개월 이상" },
];

export const EXISTING_CONDITIONS = [
  "고혈압",
  "당뇨",
  "심장질환",
  "뇌혈관질환",
  "호흡기질환",
  "간질환",
  "신장질환",
  "갑상선질환",
  "암 병력",
];

export const CHECKUP_ITEMS = [
  { id: 1, code: "BLOOD_TEST_CBC", name: "일반혈액검사(CBC)" },
  { id: 2, code: "BLOOD_TEST_LIPID", name: "혈중지질검사" },
  { id: 3, code: "CHEST_XRAY", name: "흉부 X-ray" },
  { id: 4, code: "ECG", name: "심전도" },
  { id: 5, code: "GASTROSCOPY", name: "위내시경" },
  { id: 6, code: "COLONOSCOPY", name: "대장내시경" },
  { id: 7, code: "ABDOMINAL_US", name: "복부 초음파" },
  { id: 8, code: "CT_CHEST", name: "흉부 CT" },
  { id: 9, code: "MRI_BRAIN", name: "뇌 MRI" },
  { id: 10, code: "THYROID_US", name: "갑상선 초음파" },
  { id: 11, code: "LIVER_FUNCTION", name: "간기능검사" },
  { id: 12, code: "KIDNEY_FUNCTION", name: "신기능검사" },
];

const SYMPTOM_CODE_TO_NAME: Record<string, string> = Object.fromEntries(
  SYMPTOM_OPTIONS.map((s) => [s.code, s.name])
);

export function symptomCodeToKorean(code: string): string {
  return SYMPTOM_CODE_TO_NAME[code] ?? code;
}

export const TOTAL_STEPS = 3;

export const DISCLAIMER =
  "본 서비스는 의료 행위가 아니며, 참고용 정보만 제공합니다. 정확한 진단과 치료는 반드시 의료 전문가와 상담하시기 바랍니다.";
