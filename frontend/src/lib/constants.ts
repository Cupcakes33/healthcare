import type { SymptomOption } from "@/types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const SYMPTOM_OPTIONS: SymptomOption[] = [
  { code: "CHEST_PAIN", name: "흉통", category: "심혈관" },
  { code: "CHEST_PRESSURE", name: "가슴 압박감", category: "심혈관" },
  { code: "PALPITATION", name: "두근거림", category: "심혈관" },
  { code: "SHORTNESS_OF_BREATH", name: "호흡곤란", category: "심혈관" },
  { code: "ARM_RADIATING_PAIN", name: "팔 방사통", category: "심혈관" },
  { code: "JAW_RADIATING_PAIN", name: "턱 방사통", category: "심혈관" },
  { code: "BACK_RADIATING_PAIN", name: "등 방사통", category: "심혈관" },
  { code: "HEADACHE", name: "두통", category: "신경계" },
  { code: "THUNDERCLAP_HEADACHE", name: "벼락두통", category: "신경계" },
  { code: "DIZZINESS", name: "어지러움", category: "신경계" },
  { code: "NUMBNESS", name: "저림/감각이상", category: "신경계" },
  { code: "UNILATERAL_PARALYSIS", name: "편측 마비", category: "신경계" },
  { code: "SPEECH_DISORDER", name: "언어장애", category: "신경계" },
  { code: "ABDOMINAL_PAIN", name: "복통", category: "소화기" },
  { code: "NAUSEA", name: "구역/구토", category: "소화기" },
  { code: "HEARTBURN", name: "속쓰림", category: "소화기" },
  { code: "COUGH", name: "기침", category: "호흡기" },
  { code: "CHRONIC_COUGH", name: "만성 기침", category: "호흡기" },
  { code: "SPUTUM", name: "가래", category: "호흡기" },
  { code: "WHEEZING", name: "쌕쌕거림", category: "호흡기" },
  { code: "FATIGUE", name: "피로감", category: "전신" },
  { code: "WEIGHT_LOSS", name: "체중 감소", category: "전신" },
  { code: "UNEXPLAINED_WEIGHT_LOSS", name: "원인불명 체중 감소", category: "전신" },
  { code: "FEVER", name: "발열", category: "전신" },
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

export const TOTAL_STEPS = 3;

export const DISCLAIMER =
  "본 서비스는 의료 행위가 아니며, 참고용 정보만 제공합니다. 정확한 진단과 치료는 반드시 의료 전문가와 상담하시기 바랍니다.";
