export interface QuestionnaireFormData {
  age: number | null;
  gender: "M" | "F" | null;
  symptoms: string[];
  duration: string;
  existingConditions: string[];
}

export interface QuestionnaireRequest {
  age: number;
  gender: "M" | "F";
  symptoms: string[];
  duration: string;
  existing_conditions: string[];
}

export interface InputSummary {
  age: number;
  gender: string;
  symptoms: string[];
  duration: string;
  existing_conditions: string[];
}

export interface RedFlagResult {
  level: "NONE" | "CAUTION" | "URGENT" | "EMERGENCY";
  matched_rules: string[];
  message: string;
}

export interface PackageRecommendation {
  package_id: number;
  package_name: string;
  match_score: number;
  reason: string;
  matched_tags: string[];
}

export interface QuestionnaireResponse {
  session_key: string;
  summary: string | null;
  input_summary: InputSummary;
  red_flag: RedFlagResult;
  recommendations: PackageRecommendation[];
}

export interface SymptomOption {
  code: string;
  name: string;
  category: string;
}
