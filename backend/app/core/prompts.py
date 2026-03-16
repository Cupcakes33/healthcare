from __future__ import annotations

from typing import List, Tuple

from app.domain.schemas.patient import QuestionnaireRequest

OUTPUT_SCHEMA = """{
  "summary": "문진 요약 (한국어 2~3문장)",
  "extracted_tags": ["증상태그코드1", "증상태그코드2"],
  "recommendations": [
    {
      "package_id": 1,
      "reason": "추천 근거 (한국어 1~2문장)",
      "confidence": 0.85
    }
  ],
  "confidence": 0.85
}"""

FEW_SHOT_EXAMPLE = """예시:

입력:
- 나이: 52세, 성별: 남성
- 증상: 가슴 답답함, 운동 시 숨참
- 기간: 3주
- 기저질환: 고혈압

출력:
{
  "summary": "52세 남성 환자가 3주간 가슴 답답함과 운동 시 호흡곤란을 호소합니다. 고혈압 기저질환이 있어 심혈관계 정밀 검사가 권장됩니다.",
  "extracted_tags": ["CHEST_TIGHTNESS", "DYSPNEA"],
  "recommendations": [
    {
      "package_id": 2,
      "reason": "가슴 답답함과 호흡곤란 증상이 있고 고혈압 기저질환이 있어 심혈관 정밀검진이 적합합니다.",
      "confidence": 0.9
    }
  ],
  "confidence": 0.88
}"""

SYSTEM_PROMPT = f"""당신은 의료 문진 분석 도우미입니다.
환자가 선택한 증상 정보를 분석하여 요약, 증상 태그 추출, 검진 패키지 추천을 수행합니다.

중요 제약:
- 진단이나 처방을 하지 마세요. 검진 패키지 추천만 수행합니다.
- 입력되지 않은 정보를 추측하지 마세요.
- 불확실한 정보는 포함하지 마세요.

반드시 아래 JSON 형식으로만 응답하세요:
{OUTPUT_SCHEMA}

규칙:
- extracted_tags: 제공된 증상 태그 목록에서만 선택 (1~5개)
- recommendations: 제공된 패키지 목록에서만 선택 (1~3개)
- confidence 기준:
  - 0.9 이상: 증상이 특정 패키지와 명확히 연관되고, 나이/성별/기저질환이 모두 부합
  - 0.7~0.9: 증상이 연관되나 기저질환 등 일부 정보가 불충분
  - 0.5~0.7: 증상이 간접적으로 연관되거나 여러 패키지가 비슷하게 적합
  - 0.5 미만: 증상과 패키지의 연관성이 약하거나 정보가 부족

{FEW_SHOT_EXAMPLE}"""

GENDER_MAP = {"M": "남성", "F": "여성"}


def build_questionnaire_prompt(
    questionnaire: QuestionnaireRequest,
    packages: List[dict],
    symptom_tags: List[dict],
) -> Tuple[str, str]:
    gender_text = GENDER_MAP.get(questionnaire.gender, questionnaire.gender)

    tag_list = "\n".join(
        f"- {t['code']}: {t['name']} [{t.get('category', '')}]"
        for t in symptom_tags
    )

    package_list = "\n".join(
        f"- ID {p['id']}: {p['name']} — {p.get('description', '')} "
        f"({p['hospital_name']}, "
        f"대상: {GENDER_MAP.get(p.get('target_gender', ''), p.get('target_gender', 'ALL'))} "
        f"{p.get('min_age', 0)}~{p.get('max_age', 150)}세, {p.get('price_range', '')})"
        for p in packages
    )

    symptoms_text = ", ".join(questionnaire.symptoms)
    conditions_text = ", ".join(questionnaire.existing_conditions) if questionnaire.existing_conditions else "없음"

    user_prompt = f"""환자 정보:
- 나이: {questionnaire.age}세
- 성별: {gender_text}
- 증상: {symptoms_text}
- 증상 지속 기간: {questionnaire.duration}
- 기저질환: {conditions_text}

이용 가능한 증상 태그:
{tag_list}

이용 가능한 검진 패키지:
{package_list}

위 환자 정보를 분석하여 문진 요약, 관련 증상 태그 추출, 적합한 검진 패키지를 추천해주세요."""

    return SYSTEM_PROMPT, user_prompt
