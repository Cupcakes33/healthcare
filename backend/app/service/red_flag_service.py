from __future__ import annotations

from pathlib import Path
from typing import List

import yaml

from app.domain.schemas.patient import RedFlagResult

LEVEL_PRIORITY = {"NONE": 0, "CAUTION": 1, "URGENT": 2, "EMERGENCY": 3}

RULES_PATH = Path(__file__).resolve().parent.parent / "core" / "red_flag_rules.yml"


def _load_rules(path: Path = RULES_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class RedFlagService:
    def __init__(self, rules_path: Path = RULES_PATH) -> None:
        config = _load_rules(rules_path)
        self._rules = [
            (
                r["level"],
                set(r["required_symptoms"]),
                r["description"],
                r["message"],
            )
            for r in config["rules"]
        ]
        self._default_message = config.get("default_message", "특이 소견이 없습니다.")

    def check(self, symptoms: List[str]) -> RedFlagResult:
        symptom_set = set(symptoms)
        matched_rules: List[str] = []
        highest_level = "NONE"
        highest_message = self._default_message

        for level, required, description, message in self._rules:
            if required.issubset(symptom_set):
                matched_rules.append(description)
                if LEVEL_PRIORITY[level] > LEVEL_PRIORITY[highest_level]:
                    highest_level = level
                    highest_message = message

        return RedFlagResult(
            level=highest_level,
            matched_rules=matched_rules,
            message=highest_message,
        )
