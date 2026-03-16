from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.domain.models import (
    CheckupItem,
    CheckupPackage,
    CheckupPackageItem,
    PackageSymptomTag,
    SymptomTag,
)

logger = logging.getLogger(__name__)

SYMPTOM_TAGS = [
    # 심혈관
    {"code": "CHEST_PAIN", "name": "흉통", "category": "심혈관"},
    {"code": "CHEST_PRESSURE", "name": "가슴 압박감", "category": "심혈관"},
    {"code": "PALPITATION", "name": "두근거림", "category": "심혈관"},
    {"code": "SHORTNESS_OF_BREATH", "name": "호흡곤란", "category": "심혈관"},
    {"code": "ARM_RADIATING_PAIN", "name": "팔 방사통", "category": "심혈관"},
    {"code": "JAW_RADIATING_PAIN", "name": "턱 방사통", "category": "심혈관"},
    {"code": "BACK_RADIATING_PAIN", "name": "등 방사통", "category": "심혈관"},
    # 신경계
    {"code": "HEADACHE", "name": "두통", "category": "신경계"},
    {"code": "THUNDERCLAP_HEADACHE", "name": "벼락두통", "category": "신경계"},
    {"code": "DIZZINESS", "name": "어지러움", "category": "신경계"},
    {"code": "NUMBNESS", "name": "저림/감각이상", "category": "신경계"},
    {"code": "UNILATERAL_PARALYSIS", "name": "편측 마비", "category": "신경계"},
    {"code": "SPEECH_DISORDER", "name": "언어장애", "category": "신경계"},
    # 소화기
    {"code": "ABDOMINAL_PAIN", "name": "복통", "category": "소화기"},
    {"code": "NAUSEA", "name": "구역/구토", "category": "소화기"},
    {"code": "HEARTBURN", "name": "속쓰림", "category": "소화기"},
    # 호흡기
    {"code": "COUGH", "name": "기침", "category": "호흡기"},
    {"code": "CHRONIC_COUGH", "name": "만성 기침", "category": "호흡기"},
    {"code": "SPUTUM", "name": "가래", "category": "호흡기"},
    {"code": "WHEEZING", "name": "쌕쌕거림", "category": "호흡기"},
    # 전신
    {"code": "FATIGUE", "name": "피로감", "category": "전신"},
    {"code": "WEIGHT_LOSS", "name": "체중 감소", "category": "전신"},
    {"code": "UNEXPLAINED_WEIGHT_LOSS", "name": "원인불명 체중 감소", "category": "전신"},
    {"code": "FEVER", "name": "발열", "category": "전신"},
]

CHECKUP_ITEMS = [
    {"code": "BLOOD_TEST_CBC", "name": "일반혈액검사(CBC)", "description": "적혈구, 백혈구, 혈소판 등 혈구 수 측정"},
    {"code": "BLOOD_TEST_LIPID", "name": "혈중지질검사", "description": "총콜레스테롤, HDL, LDL, 중성지방 측정"},
    {"code": "CHEST_XRAY", "name": "흉부 X-ray", "description": "폐, 심장 등 흉부 장기 영상 검사"},
    {"code": "ECG", "name": "심전도", "description": "심장 전기 활동 측정"},
    {"code": "GASTROSCOPY", "name": "위내시경", "description": "식도, 위, 십이지장 내시경 검사"},
    {"code": "COLONOSCOPY", "name": "대장내시경", "description": "대장 전체 내시경 검사"},
    {"code": "ABDOMINAL_US", "name": "복부 초음파", "description": "간, 담낭, 췌장, 비장, 신장 초음파"},
    {"code": "CT_CHEST", "name": "흉부 CT", "description": "흉부 컴퓨터단층촬영"},
    {"code": "MRI_BRAIN", "name": "뇌 MRI", "description": "뇌 자기공명영상"},
    {"code": "THYROID_US", "name": "갑상선 초음파", "description": "갑상선 초음파 검사"},
    {"code": "LIVER_FUNCTION", "name": "간기능검사", "description": "AST, ALT, GGT 등 간 효소 측정"},
    {"code": "KIDNEY_FUNCTION", "name": "신기능검사", "description": "BUN, 크레아티닌 등 신장 기능 측정"},
]

PACKAGES = [
    {
        "name": "기본 종합검진",
        "description": "건강한 성인을 위한 기본 건강 체크. 혈액검사, 영상검사 등 필수 항목을 포함합니다.",
        "hospital_name": "서울대학교병원",
        "target_gender": "ALL",
        "min_age": 20,
        "max_age": 80,
        "price_range": "30만~50만원",
        "items": ["BLOOD_TEST_CBC", "BLOOD_TEST_LIPID", "CHEST_XRAY", "LIVER_FUNCTION", "KIDNEY_FUNCTION"],
        "tags": [
            ("FATIGUE", 0.6),
            ("FEVER", 0.4),
            ("WEIGHT_LOSS", 0.5),
        ],
    },
    {
        "name": "심혈관 정밀검진",
        "description": "흉통, 호흡곤란 등 심혈관 증상이 있는 분을 위한 정밀 검진입니다.",
        "hospital_name": "서울대학교병원",
        "target_gender": "ALL",
        "min_age": 30,
        "max_age": 80,
        "price_range": "50만~80만원",
        "items": ["BLOOD_TEST_CBC", "BLOOD_TEST_LIPID", "ECG", "CHEST_XRAY", "CT_CHEST"],
        "tags": [
            ("CHEST_PAIN", 0.95),
            ("CHEST_PRESSURE", 0.9),
            ("PALPITATION", 0.85),
            ("SHORTNESS_OF_BREATH", 0.8),
            ("ARM_RADIATING_PAIN", 0.7),
        ],
    },
    {
        "name": "소화기 정밀검진",
        "description": "복통, 속쓰림 등 소화기 증상이 있는 분을 위한 정밀 검진입니다.",
        "hospital_name": "세브란스병원",
        "target_gender": "ALL",
        "min_age": 30,
        "max_age": 80,
        "price_range": "40만~70만원",
        "items": ["BLOOD_TEST_CBC", "GASTROSCOPY", "COLONOSCOPY", "ABDOMINAL_US", "LIVER_FUNCTION"],
        "tags": [
            ("ABDOMINAL_PAIN", 0.95),
            ("NAUSEA", 0.8),
            ("HEARTBURN", 0.85),
            ("WEIGHT_LOSS", 0.5),
        ],
    },
    {
        "name": "호흡기 정밀검진",
        "description": "기침, 호흡곤란 등 호흡기 증상이 있는 분을 위한 정밀 검진입니다.",
        "hospital_name": "삼성서울병원",
        "target_gender": "ALL",
        "min_age": 20,
        "max_age": 80,
        "price_range": "40만~60만원",
        "items": ["BLOOD_TEST_CBC", "CHEST_XRAY", "CT_CHEST", "LIVER_FUNCTION"],
        "tags": [
            ("COUGH", 0.8),
            ("CHRONIC_COUGH", 0.95),
            ("SPUTUM", 0.75),
            ("WHEEZING", 0.85),
            ("SHORTNESS_OF_BREATH", 0.7),
        ],
    },
    {
        "name": "뇌신경 정밀검진",
        "description": "두통, 어지러움, 저림 등 신경계 증상이 있는 분을 위한 정밀 검진입니다.",
        "hospital_name": "서울아산병원",
        "target_gender": "ALL",
        "min_age": 30,
        "max_age": 80,
        "price_range": "60만~100만원",
        "items": ["BLOOD_TEST_CBC", "MRI_BRAIN", "ECG", "BLOOD_TEST_LIPID"],
        "tags": [
            ("HEADACHE", 0.85),
            ("THUNDERCLAP_HEADACHE", 0.95),
            ("DIZZINESS", 0.8),
            ("NUMBNESS", 0.75),
            ("UNILATERAL_PARALYSIS", 0.9),
        ],
    },
    {
        "name": "여성 특화검진",
        "description": "여성 건강에 특화된 검진입니다. 갑상선, 복부 등 여성에게 빈번한 질환을 집중 검사합니다.",
        "hospital_name": "이화여자대학교 목동병원",
        "target_gender": "F",
        "min_age": 20,
        "max_age": 70,
        "price_range": "40만~70만원",
        "items": ["BLOOD_TEST_CBC", "THYROID_US", "ABDOMINAL_US", "CHEST_XRAY", "LIVER_FUNCTION"],
        "tags": [
            ("FATIGUE", 0.8),
            ("WEIGHT_LOSS", 0.6),
            ("DIZZINESS", 0.5),
        ],
    },
    {
        "name": "남성 특화검진",
        "description": "남성 건강에 특화된 검진입니다. 심혈관, 간 등 남성에게 빈번한 질환을 집중 검사합니다.",
        "hospital_name": "서울대학교병원",
        "target_gender": "M",
        "min_age": 30,
        "max_age": 70,
        "price_range": "40만~70만원",
        "items": ["BLOOD_TEST_CBC", "BLOOD_TEST_LIPID", "ECG", "ABDOMINAL_US", "LIVER_FUNCTION", "KIDNEY_FUNCTION"],
        "tags": [
            ("FATIGUE", 0.7),
            ("CHEST_PAIN", 0.6),
            ("ABDOMINAL_PAIN", 0.5),
        ],
    },
]


async def _get_or_create_tag(session: AsyncSession, data: dict) -> SymptomTag:
    result = await session.execute(
        select(SymptomTag).where(SymptomTag.code == data["code"])
    )
    tag = result.scalar_one_or_none()
    if tag:
        logger.info("증상 태그 이미 존재: %s", data["code"])
        return tag
    tag = SymptomTag(**data)
    session.add(tag)
    await session.flush()
    logger.info("증상 태그 생성: %s", data["code"])
    return tag


async def _get_or_create_item(session: AsyncSession, data: dict) -> CheckupItem:
    result = await session.execute(
        select(CheckupItem).where(CheckupItem.code == data["code"])
    )
    item = result.scalar_one_or_none()
    if item:
        logger.info("검진 항목 이미 존재: %s", data["code"])
        return item
    item = CheckupItem(**data)
    session.add(item)
    await session.flush()
    logger.info("검진 항목 생성: %s", data["code"])
    return item


async def _get_or_create_package(
    session: AsyncSession,
    pkg_data: dict,
    tag_map: dict,
    item_map: dict,
) -> None:
    result = await session.execute(
        select(CheckupPackage).where(CheckupPackage.name == pkg_data["name"])
    )
    if result.scalar_one_or_none():
        logger.info("패키지 이미 존재: %s", pkg_data["name"])
        return

    package = CheckupPackage(
        name=pkg_data["name"],
        description=pkg_data["description"],
        hospital_name=pkg_data["hospital_name"],
        target_gender=pkg_data["target_gender"],
        min_age=pkg_data["min_age"],
        max_age=pkg_data["max_age"],
        price_range=pkg_data["price_range"],
    )
    session.add(package)
    await session.flush()

    for item_code in pkg_data["items"]:
        item = item_map[item_code]
        pkg_item = CheckupPackageItem(package_id=package.id, item_id=item.id)
        session.add(pkg_item)

    for tag_code, score in pkg_data["tags"]:
        tag = tag_map[tag_code]
        pkg_tag = PackageSymptomTag(
            package_id=package.id,
            symptom_tag_id=tag.id,
            relevance_score=score,
        )
        session.add(pkg_tag)

    logger.info("패키지 생성: %s (항목 %d개, 태그 %d개)", pkg_data["name"], len(pkg_data["items"]), len(pkg_data["tags"]))


async def seed() -> None:
    async with async_session() as session:
        async with session.begin():
            tag_map = {}
            for tag_data in SYMPTOM_TAGS:
                tag = await _get_or_create_tag(session, tag_data)
                tag_map[tag_data["code"]] = tag

            item_map = {}
            for item_data in CHECKUP_ITEMS:
                item = await _get_or_create_item(session, item_data)
                item_map[item_data["code"]] = item

            for pkg_data in PACKAGES:
                await _get_or_create_package(session, pkg_data, tag_map, item_map)

    logger.info("시드 데이터 삽입 완료")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    asyncio.run(seed())


if __name__ == "__main__":
    main()
