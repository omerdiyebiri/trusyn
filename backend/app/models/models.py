from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Float, Text, Uuid as UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base
import enum

class SubscriptionPlan(str, enum.Enum):
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    subscription_plan = Column(Enum(SubscriptionPlan), default=SubscriptionPlan.BASIC)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="tenant")
    brands = relationship("Brand", back_populates="tenant")

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    TENANT_STAFF = "tenant_staff"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.TENANT_STAFF)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="users")

class Brand(Base):
    __tablename__ = "brands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    name = Column(String, nullable=False)
    official_domains = Column(Text)  # JSON or comma-separated
    keywords = Column(Text)          # JSON or comma-separated
    logo_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="brands")
    incidents = relationship("Incident", back_populates="brand")

class IncidentStatus(str, enum.Enum):
    DETECTED = "detected"
    ANALYZING = "analyzing"
    VALIDATED = "validated"
    REPORTED = "reported"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"

class ThreatType(str, enum.Enum):
    PHISHING = "phishing"
    BRAND_IMPERSONATION = "brand_impersonation"
    TYPOSQUATTING = "typosquatting"

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"))
    target_url = Column(String, nullable=False)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.DETECTED)
    threat_type = Column(Enum(ThreatType))
    confidence_score = Column(Float, default=0.0)
    screenshot_path = Column(String, nullable=True)
    whois_raw = Column(Text, nullable=True)
    discovered_at = Column(DateTime, default=datetime.utcnow)

    brand = relationship("Brand", back_populates="incidents")
    reports = relationship("Report", back_populates="incident")

class RecipientType(str, enum.Enum):
    CLOUDFLARE = "cloudflare"
    HOSTING = "hosting"
    REGISTRAR = "registrar"
    GOOGLE_DMCA = "google_dmca"

class ReportStatus(str, enum.Enum):
    SENT = "sent"
    RECEIVED = "received"
    PENDING_REVIEW = "pending_review"

class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"))
    recipient_type = Column(Enum(RecipientType))
    recipient_email = Column(String)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(ReportStatus), default=ReportStatus.SENT)
    raw_content = Column(Text)

    incident = relationship("Incident", back_populates="reports")
