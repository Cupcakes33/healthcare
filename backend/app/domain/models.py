from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SymptomTag(Base):
    __tablename__ = "symptom_tag"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[str] = mapped_column(server_default=func.now())

    package_tags: Mapped[list["PackageSymptomTag"]] = relationship(back_populates="symptom_tag")

    __table_args__ = (
        Index("idx_symptom_tag_category", "category"),
    )


class CheckupItem(Base):
    __tablename__ = "checkup_item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(server_default=func.now())

    package_items: Mapped[list["CheckupPackageItem"]] = relationship(back_populates="item")


class CheckupPackage(Base):
    __tablename__ = "checkup_package"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    hospital_name: Mapped[str] = mapped_column(String(200), nullable=False)
    target_gender: Mapped[str] = mapped_column(String(10), nullable=False)
    min_age: Mapped[int] = mapped_column(Integer, nullable=False)
    max_age: Mapped[int] = mapped_column(Integer, nullable=False)
    price_range: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[str] = mapped_column(server_default=func.now())
    updated_at: Mapped[str] = mapped_column(server_default=func.now(), onupdate=func.now())

    package_items: Mapped[list["CheckupPackageItem"]] = relationship(back_populates="package")
    package_tags: Mapped[list["PackageSymptomTag"]] = relationship(back_populates="package")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="package")

    __table_args__ = (
        Index("idx_checkup_package_active", "is_active", postgresql_where=(is_active == True)),
        Index(
            "idx_checkup_package_target",
            "target_gender", "min_age", "max_age",
            postgresql_where=(is_active == True),
        ),
    )


class CheckupPackageItem(Base):
    __tablename__ = "checkup_package_item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("checkup_package.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("checkup_item.id"), nullable=False)

    package: Mapped["CheckupPackage"] = relationship(back_populates="package_items")
    item: Mapped["CheckupItem"] = relationship(back_populates="package_items")


class PackageSymptomTag(Base):
    __tablename__ = "package_symptom_tag"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("checkup_package.id"), nullable=False)
    symptom_tag_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("symptom_tag.id"), nullable=False)
    relevance_score: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)

    package: Mapped["CheckupPackage"] = relationship(back_populates="package_tags")
    symptom_tag: Mapped["SymptomTag"] = relationship(back_populates="package_tags")

    __table_args__ = (
        CheckConstraint("relevance_score >= 0 AND relevance_score <= 1", name="ck_relevance_score_range"),
        Index("idx_package_symptom_tag_tag", "symptom_tag_id"),
        Index("idx_package_symptom_tag_pkg", "package_id"),
    )


class IntakeSession(Base):
    __tablename__ = "intake_session"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_key: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    intake_type: Mapped[str] = mapped_column(String(10), nullable=False, default="FORM", server_default="FORM")
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    selected_symptoms: Mapped[dict] = mapped_column(JSONB, nullable=False)
    duration: Mapped[str] = mapped_column(String(50), nullable=False)
    underlying_conditions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    llm_summary: Mapped[Optional[str]] = mapped_column(Text)
    extracted_tags: Mapped[Optional[dict]] = mapped_column(JSONB)
    red_flag_level: Mapped[str] = mapped_column(String(20), nullable=False, default="NONE")
    red_flag_details: Mapped[Optional[dict]] = mapped_column(JSONB)
    chat_history: Mapped[Optional[dict]] = mapped_column(JSONB)
    llm_provider: Mapped[Optional[str]] = mapped_column(String(20))
    llm_model: Mapped[Optional[str]] = mapped_column(String(50))
    input_summary: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[str] = mapped_column(server_default=func.now())

    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="session")

    __table_args__ = (
        Index("idx_intake_session_created", "created_at"),
        Index("idx_intake_session_gender", "gender"),
        Index(
            "idx_intake_session_red_flag",
            "red_flag_level",
            postgresql_where=("red_flag_level != 'NONE'"),
        ),
    )


class Recommendation(Base):
    __tablename__ = "recommendation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("intake_session.id"), nullable=False)
    package_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("checkup_package.id"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    match_score: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    matched_tags: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[str] = mapped_column(server_default=func.now())

    session: Mapped["IntakeSession"] = relationship(back_populates="recommendations")
    package: Mapped["CheckupPackage"] = relationship(back_populates="recommendations")

    __table_args__ = (
        Index("idx_recommendation_session", "session_id"),
        Index("idx_recommendation_package", "package_id"),
    )
