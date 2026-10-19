"""SQLAlchemy domain models for CampusFind.

The exact UML entities are dual-written alongside the legacy ItemReport API
model while clients and previously stored records transition safely.
"""
from datetime import date, datetime
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from app.db.session import Base

ITEM_STATUSES = (
    "Pending Approval", "Active", "Rejected", "Match Found",
    "Claim Requested", "Approved for Return", "Returned", "Closed",
)
ROLES = ("Campus User", "Administrator")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role in ('Campus User','Administrator')", name="ck_user_role"),
        CheckConstraint("verification_status in ('Unverified','Verified')", name="ck_user_verification_status"),
    )
    id: Mapped[int] = mapped_column("user_id", Integer, primary_key=True)
    display_name: Mapped[str] = mapped_column("name", String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="Campus User")
    verification_status: Mapped[str] = mapped_column(String(20), nullable=False, default="Unverified")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    reports = relationship("ItemReport", back_populates="owner")
    lost_reports = relationship("LostReport", back_populates="owner", foreign_keys="LostReport.owner_id")
    found_reports = relationship("FoundReport", back_populates="finder", foreign_keys="FoundReport.finder_id")
    claims = relationship("Claim", back_populates="claimant", foreign_keys="Claim.claimant_id")
    notifications = relationship("Notification", back_populates="recipient")
    audit_events = relationship("AuditEvent", back_populates="actor", foreign_keys="AuditEvent.actor_id")

    @property
    def verified(self):
        return self.verification_status == "Verified"

    @verified.setter
    def verified(self, value):
        self.verification_status = "Verified" if value else "Unverified"


class LostReport(Base):
    __tablename__ = "lost_reports"
    __table_args__ = (CheckConstraint("status in ('Pending Approval','Active','Rejected','Match Found','Claim Requested','Approved for Return','Returned','Closed')", name="ck_lost_report_status"),)
    report_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    date_lost: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Pending Approval", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    owner = relationship("User", back_populates="lost_reports", foreign_keys=[owner_id])
    matches = relationship("Match", back_populates="lost_report", foreign_keys="Match.lost_report_id")


class FoundReport(Base):
    __tablename__ = "found_reports"
    __table_args__ = (CheckConstraint("status in ('Pending Approval','Active','Rejected','Match Found','Claim Requested','Approved for Return','Returned','Closed')", name="ck_found_report_status"),)
    report_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    finder_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    found_location: Mapped[str] = mapped_column(String(255), nullable=False)
    date_found: Mapped[date] = mapped_column(Date, nullable=False)
    custody_location: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Pending Approval", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    finder = relationship("User", back_populates="found_reports", foreign_keys=[finder_id])
    matches = relationship("Match", back_populates="found_report", foreign_keys="Match.found_report_id")
    claims = relationship("Claim", back_populates="report", foreign_keys="Claim.report_id")


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("lost_report_id", "found_report_id", name="uq_match_report_pair"),
        CheckConstraint("confidence in ('High','Medium','Low')", name="ck_match_confidence"),
        CheckConstraint("status = 'Match Found'", name="ck_match_status"),
    )
    match_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lost_report_id: Mapped[int] = mapped_column(ForeignKey("lost_reports.report_id"), index=True, nullable=False)
    found_report_id: Mapped[int] = mapped_column(ForeignKey("found_reports.report_id"), index=True, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Match Found")
    lost_report = relationship("LostReport", back_populates="matches", foreign_keys=[lost_report_id])
    found_report = relationship("FoundReport", back_populates="matches", foreign_keys=[found_report_id])


class Claim(Base):
    __tablename__ = "claims"
    __table_args__ = (CheckConstraint("status in ('Pending','Approved for Return','Rejected')", name="ck_claim_status"),)
    claim_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("found_reports.report_id"), index=True, nullable=False)
    claimant_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True, nullable=False)
    proof_reference: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Pending")
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"))
    decision_comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime)
    id = synonym("claim_id")
    item_id = synonym("report_id")
    report = relationship("FoundReport", back_populates="claims", foreign_keys=[report_id])
    claimant = relationship("User", back_populates="claims", foreign_keys=[claimant_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint("delivery_status in ('Pending','Sent','Failed')", name="ck_notification_delivery_status"),
    )
    notification_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(60), nullable=False, default="general")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime)
    delivery_status: Mapped[str] = mapped_column(String(12), nullable=False, default="Pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    id = synonym("notification_id")
    user_id = synonym("recipient_id")
    recipient = relationship("User", back_populates="notifications")

    @property
    def read(self):
        return self.read_at is not None

    @read.setter
    def read(self, value):
        self.read_at = datetime.utcnow() if value else None


class AuditEvent(Base):
    __tablename__ = "audit_events"
    event_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"), index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    actor = relationship("User", back_populates="audit_events", foreign_keys=[actor_id])


class StatusHistory(Base):
    __tablename__ = "status_history"
    history_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    old_status: Mapped[str] = mapped_column(String(32), nullable=False)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"))
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    changer = relationship("User", foreign_keys=[changed_by])


# Legacy compatibility models are retained so pre-transition data remains
# readable while the API is migrated. No migration drops these tables.
class ItemReport(Base):
    __tablename__ = "item_reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    item_name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    custody_location: Mapped[str | None] = mapped_column(String(255))
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Pending Approval")
    moderation_comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="reports")
    images = relationship("ItemImage", back_populates="report", cascade="all, delete-orphan")


class ItemImage(Base):
    __tablename__ = "item_images"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column("report_id", ForeignKey("item_reports.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    report = relationship("ItemReport", back_populates="images")
    report_id = synonym("item_id")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

