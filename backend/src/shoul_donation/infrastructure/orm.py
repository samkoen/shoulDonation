"""Relational tables. These rows never leave the infrastructure layer."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, LargeBinary, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SynagogueRow(Base):
    __tablename__ = "synagogues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    membership: Mapped[MembershipRow | None] = relationship(back_populates="user", uselist=False)


class MembershipRow(Base):
    __tablename__ = "memberships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    synagogue_id: Mapped[str | None] = mapped_column(ForeignKey("synagogues.id"), nullable=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    user: Mapped[UserRow] = relationship(back_populates="membership")
    synagogue: Mapped[SynagogueRow | None] = relationship()


class ProjectRow(Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("synagogue_id", "name", name="uq_projects_synagogue_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    synagogue_id: Mapped[str] = mapped_column(ForeignKey("synagogues.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    synagogue: Mapped[SynagogueRow] = relationship()


class AssignmentRow(Base):
    __tablename__ = "project_assignments"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_assignments_project_user"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    synagogue_id: Mapped[str] = mapped_column(ForeignKey("synagogues.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    project: Mapped[ProjectRow] = relationship()
    assignee: Mapped[UserRow] = relationship()
    synagogue: Mapped[SynagogueRow] = relationship()


class ConstructionBudgetRow(Base):
    __tablename__ = "construction_budgets"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    synagogue_id: Mapped[str] = mapped_column(ForeignKey("synagogues.id"), nullable=False, index=True)
    construction_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    target_percent: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    project: Mapped[ProjectRow] = relationship()


class DedicationRow(Base):
    __tablename__ = "dedications"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_dedications_project_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    synagogue_id: Mapped[str] = mapped_column(ForeignKey("synagogues.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    plan_x: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    plan_y: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    plan_region: Mapped[str | None] = mapped_column(Text, nullable=True)
    project: Mapped[ProjectRow] = relationship()


class CalculatorSettingsRow(Base):
    __tablename__ = "calculator_settings"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    synagogue_id: Mapped[str] = mapped_column(ForeignKey("synagogues.id"), nullable=False, index=True)
    min_monthly: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    max_monthly: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    max_months: Mapped[int] = mapped_column(Integer, nullable=False)
    min_per_donor: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    max_per_donor: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    min_donors: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    project: Mapped[ProjectRow] = relationship()


class ProposalRow(Base):
    __tablename__ = "proposals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    synagogue_id: Mapped[str] = mapped_column(ForeignKey("synagogues.id"), nullable=False, index=True)
    dedication_id: Mapped[str] = mapped_column(ForeignKey("dedications.id"), nullable=False)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    monthly_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    months: Mapped[int] = mapped_column(Integer, nullable=False)
    donor_count: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    financed_total: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    project: Mapped[ProjectRow] = relationship()
    dedication: Mapped[DedicationRow] = relationship()
    author: Mapped[UserRow] = relationship()


class LeadRow(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    synagogue_id: Mapped[str | None] = mapped_column(ForeignKey("synagogues.id"), nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"), nullable=True, index=True)
    dedication_id: Mapped[str | None] = mapped_column(ForeignKey("dedications.id"), nullable=True)
    assignee_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    requested_synagogue_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    project: Mapped[ProjectRow | None] = relationship()
    dedication: Mapped[DedicationRow | None] = relationship()
    assignee: Mapped[UserRow | None] = relationship()
    synagogue: Mapped[SynagogueRow | None] = relationship()


class ProjectPlanRow(Base):
    __tablename__ = "project_plans"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    synagogue_id: Mapped[str] = mapped_column(ForeignKey("synagogues.id"), nullable=False, index=True)
    content_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    project: Mapped[ProjectRow] = relationship()


class PublicPageRow(Base):
    __tablename__ = "public_pages"
    __table_args__ = (UniqueConstraint("slug", name="uq_public_pages_slug"),)

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    synagogue_id: Mapped[str] = mapped_column(ForeignKey("synagogues.id"), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    vision: Mapped[str] = mapped_column(String(2000), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    project: Mapped[ProjectRow] = relationship()


class GalleryImageRow(Base):
    __tablename__ = "gallery_images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    synagogue_id: Mapped[str] = mapped_column(ForeignKey("synagogues.id"), nullable=False, index=True)
    content_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    project: Mapped[ProjectRow] = relationship()


class ContractorRow(Base):
    __tablename__ = "dedication_contractors"

    dedication_id: Mapped[str] = mapped_column(ForeignKey("dedications.id"), primary_key=True)
    synagogue_id: Mapped[str] = mapped_column(ForeignKey("synagogues.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    dedication: Mapped[DedicationRow] = relationship()


class MeetingRow(Base):
    __tablename__ = "meetings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), nullable=False, index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    note: Mapped[str] = mapped_column(String(500), nullable=False)
    close_chance: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    lead: Mapped[LeadRow] = relationship()
