import type { QuestionnaireResponse } from "@/types";

export const mockResultNone: QuestionnaireResponse = {
  session_key: "test-session-key",
  summary: "45세 남성 환자가 두통과 피로감을 호소합니다.",
  input_summary: {
    age: 45,
    gender: "M",
    symptoms: ["HEADACHE", "FATIGUE"],
    duration: "1~2주",
    existing_conditions: ["고혈압"],
  },
  red_flag: {
    level: "NONE",
    matched_rules: [],
    message: "",
  },
  recommendations: [
    {
      package_id: 1,
      package_name: "기본 종합검진",
      match_score: 0.85,
      reason: "두통과 피로감에 대한 기본 검사",
      matched_tags: ["HEADACHE", "FATIGUE"],
    },
    {
      package_id: 2,
      package_name: "뇌신경 검진",
      match_score: 0.72,
      reason: "두통 증상에 특화된 검진",
      matched_tags: ["HEADACHE"],
    },
  ],
};

export const mockResultCaution: QuestionnaireResponse = {
  ...mockResultNone,
  red_flag: {
    level: "CAUTION",
    matched_rules: ["만성 기침 + 체중 감소"],
    message: "주의가 필요한 증상 조합이 감지되었습니다.",
  },
};

export const mockResultUrgent: QuestionnaireResponse = {
  ...mockResultNone,
  red_flag: {
    level: "URGENT",
    matched_rules: ["편측 마비 + 언어장애"],
    message: "빠른 시일 내에 전문의 진료를 받으시기 바랍니다.",
  },
};

export const mockResultEmergency: QuestionnaireResponse = {
  ...mockResultNone,
  red_flag: {
    level: "EMERGENCY",
    matched_rules: ["흉통 + 팔 방사통"],
    message: "즉시 가까운 응급실을 방문해주세요.",
  },
};
