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

export interface AdminLoginRequest {
  username: string;
  password: string;
}

export interface AdminLoginResponse {
  token: string;
  expires_at: string;
}

export interface SymptomCount {
  name: string;
  count: number;
}

export interface PackageCount {
  name: string;
  count: number;
}

export interface StatsResponse {
  total_sessions: number;
  age_distribution: Record<string, number>;
  top_symptoms: SymptomCount[];
  top_packages: PackageCount[];
  red_flag_ratio: number;
}

export interface PackageListItem {
  id: number;
  name: string;
  hospital_name: string;
  target_gender: string;
  min_age: number;
  max_age: number;
  price_range: string;
  is_active: boolean;
  item_count: number;
  tag_count: number;
  created_at: string;
}

export interface SymptomTagInfo {
  id: number;
  code: string;
  name: string;
  relevance_score: number;
}

export interface CheckupItemInfo {
  id: number;
  code: string;
  name: string;
}

export interface PackageDetail {
  id: number;
  name: string;
  description: string | null;
  hospital_name: string;
  target_gender: string;
  min_age: number;
  max_age: number;
  price_range: string;
  is_active: boolean;
  symptom_tags: SymptomTagInfo[];
  checkup_items: CheckupItemInfo[];
  created_at: string;
  updated_at: string;
}

export interface PackageFormData {
  name: string;
  description: string;
  hospital_name: string;
  target_gender: "M" | "F" | "ALL";
  min_age: number;
  max_age: number;
  price_range: string;
  symptom_tags: { symptom_tag_id: number; relevance_score: number }[];
  item_ids: number[];
}
