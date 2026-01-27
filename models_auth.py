"""
BarberX Authentication & Tier System
Database models for users, tiers, and usage tracking
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime
from enum import Enum

bcrypt = Bcrypt()
db = SQLAlchemy()
bcrypt = Bcrypt()


class TierLevel(Enum):
    """Subscription tier levels with soft caps and overage billing"""

    FREE = 0
    PROFESSIONAL = 49  # $49/mo with 3-day trial
    PREMIUM = 249  # $249/mo with soft caps
    ENTERPRISE = 999  # $999/mo with soft caps and lower overage rates
    ADMIN = 9999


class User(UserMixin, db.Model):
    """User account model"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Profile
    full_name = db.Column(db.String(100))
    organization = db.Column(db.String(200))

    # Tier & subscription
    tier = db.Column(db.Enum(TierLevel), default=TierLevel.FREE, nullable=False)
    subscription_start = db.Column(db.DateTime, default=datetime.utcnow)
    subscription_end = db.Column(db.DateTime)

    # Stripe subscription tracking
    stripe_customer_id = db.Column(db.String(100), unique=True, nullable=True, index=True)
    stripe_subscription_id = db.Column(db.String(100), unique=True, nullable=True)
    stripe_subscription_status = db.Column(db.String(50), nullable=True)  # active, canceled, past_due, etc.
    stripe_current_period_end = db.Column(db.DateTime, nullable=True)
    trial_end = db.Column(db.DateTime, nullable=True)  # For 3-day trial tracking
    is_on_trial = db.Column(db.Boolean, default=False)

    # Storage tracking
    storage_used_mb = db.Column(db.Float, default=0.0)

    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    usage = db.relationship("UsageTracking", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        """Verify password"""
        return bcrypt.check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()

    @property
    def is_subscription_active(self):
        """Check if subscription is active"""
        if self.tier == TierLevel.ADMIN:
            return True
        if not self.subscription_end:
            return self.tier == TierLevel.FREE
        return datetime.utcnow() < self.subscription_end

    @property
    def tier_name(self):
        """Get friendly tier name"""
        return self.tier.name.title()

    @property
    def tier_price(self):
        """Get tier monthly price"""
        return self.tier.value

    def get_tier_limits(self):
        """Get usage limits for current tier"""
        limits = {
            TierLevel.FREE: {
                "bwc_videos_per_month": 2,
                "max_file_size_mb": 100,
                "document_pages_per_month": 50,
                "transcription_minutes_per_month": 30,
                "search_queries_per_month": 100,
                "storage_gb": 0.5,
                "export_watermark": True,
            },
            TierLevel.PROFESSIONAL: {
                "bwc_videos_per_month": 20,  # 20 videos (hard cap for PRO)
                "bwc_video_hours_per_month": 2,  # 2 hours of video per month
                "max_file_size_mb": 1024,  # 1 GB per file
                "pdf_documents_per_month": 10,  # 10 PDFs per month (hard cap)
                "transcription_minutes_per_month": 120,  # 2 hours = 120 minutes
                "ai_assistant_access": "basic",  # Basic AI assistant
                "search_queries_per_month": 1000,  # 1,000 queries
                "storage_gb": 25,
                "export_watermark": False,
                "case_limit": 10,  # Max 10 active cases
                "court_ready_reports": "basic",  # Basic templates
                "trial_days": 3,  # 3-day free trial
                "api_access": False,
                "overage_allowed": False,  # Hard caps - must upgrade
            },
            TierLevel.PREMIUM: {
                "bwc_videos_per_month": 100,  # 100 videos (soft cap)
                "bwc_video_hours_per_month": 10,  # 10 hours (soft cap)
                "max_file_size_mb": 5120,  # 5 GB per file
                "pdf_documents_per_month": 100,  # 100 PDFs (soft cap)
                "transcription_minutes_per_month": 600,  # 10 hours (soft cap)
                "ai_assistant_access": "full",  # Full context AI chat
                "search_queries_per_month": 10000,  # 10k queries (soft cap)
                "storage_gb": 500,
                "export_watermark": False,
                "case_limit": 50,  # 50 active cases (soft cap)
                "court_ready_reports": "advanced",  # Advanced templates
                "timeline_builder": True,
                "api_access": True,
                "forensic_analysis": True,
                "priority_support": True,
                # Overage fees for PREMIUM (soft caps)
                "overage_allowed": True,
                "overage_fee_per_video": 2.00,  # $2 per video over 100
                "overage_fee_per_video_hour": 5.00,  # $5 per hour over 10
                "overage_fee_per_pdf": 1.00,  # $1 per PDF over 100
                "overage_fee_per_case": 5.00,  # $5 per case over 50
            },
            TierLevel.ENTERPRISE: {
                "bwc_videos_per_month": 500,  # 500 videos (soft cap)
                "bwc_video_hours_per_month": 50,  # 50 hours (soft cap)
                "max_file_size_mb": 20480,  # 20 GB for 4K videos
                "pdf_documents_per_month": 500,  # 500 PDFs (soft cap)
                "transcription_minutes_per_month": 3000,  # 50 hours (soft cap)
                "ai_assistant_access": "private_instance",  # Private AI instance
                "search_queries_per_month": 50000,  # 50k queries (soft cap)
                "storage_gb": 2000,  # 2TB storage (soft cap)
                "export_watermark": False,
                "case_limit": 200,  # 200 active cases (soft cap)
                "court_ready_reports": "firm_branded",  # Firm-branded output
                "timeline_builder": True,
                "multi_bwc_sync": 20,  # 20 concurrent videos
                "api_access": True,
                "forensic_analysis": True,
                "white_label": True,
                "priority_support": True,
                "sla_guaranteed": True,
                "dedicated_pm": True,  # Dedicated project manager
                "self_hosted": True,  # Docker deployment option
                "on_premises_data": True,  # Data residency control
                "concurrent_users": 50,  # 50 team members (soft cap)
                # Overage fees for ENTERPRISE (lower rates due to volume)
                "overage_allowed": True,
                "overage_fee_per_video": 1.00,  # $1 per video over 500
                "overage_fee_per_video_hour": 3.00,  # $3 per hour over 50
                "overage_fee_per_pdf": 0.50,  # $0.50 per PDF over 500
                "overage_fee_per_case": 2.00,  # $2 per case over 200
                "overage_fee_per_gb_storage": 0.50,  # $0.50 per GB over 2TB
                "overage_fee_per_user": 20.00,  # $20 per user over 50
            },
            TierLevel.ADMIN: {
                "bwc_videos_per_month": -1,
                "max_file_size_mb": -1,
                "document_pages_per_month": -1,
                "transcription_minutes_per_month": -1,
                "search_queries_per_month": -1,
                "storage_gb": -1,
                "export_watermark": False,
                "multi_bwc_sync": -1,
                "api_access": True,
                "forensic_analysis": True,
                "white_label": True,
                "priority_support": True,
                "backend_access": True,
                "admin_dashboard": True,
            },
        }
        return limits.get(self.tier, limits[TierLevel.FREE])

    def can_access_feature(self, feature):
        """Check if user has access to a feature"""
        limits = self.get_tier_limits()
        return limits.get(feature, False)

    def can_analyze(self):
        """Check if user can perform analysis (based on monthly limits)"""
        limits = self.get_tier_limits()
        bwc_limit = limits.get("bwc_videos_per_month", 0)

        # Unlimited for some tiers
        if bwc_limit == -1:
            return True

        # Check current month usage
        from datetime import datetime

        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        usage_this_month = UsageTracking.query.filter(
            UsageTracking.user_id == self.id, UsageTracking.month >= current_month
        ).first()

        if not usage_this_month:
            return True

        return usage_this_month.bwc_videos_analyzed < bwc_limit

    def __repr__(self):
        return f"<User {self.email} ({self.tier_name})>"


class UsageTracking(db.Model):
    """Track user usage per month"""

    __tablename__ = "usage_tracking"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Period
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)

    # Usage counters
    bwc_videos_processed = db.Column(db.Integer, default=0)
    bwc_video_hours_used = db.Column(db.Float, default=0.0)  # Track video hours
    pdf_documents_processed = db.Column(db.Integer, default=0)  # Track PDF count (not pages)
    document_pages_processed = db.Column(db.Integer, default=0)  # Still track pages for stats
    transcription_minutes_used = db.Column(db.Integer, default=0)
    search_queries_made = db.Column(db.Integer, default=0)
    storage_used_mb = db.Column(db.Float, default=0)
    api_calls_made = db.Column(db.Integer, default=0)
    cases_created = db.Column(db.Integer, default=0)  # Track case count

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "year", "month", name="unique_user_month"),)

    @staticmethod
    def get_or_create_current(user_id):
        """Get or create usage tracking for current month"""
        now = datetime.utcnow()
        usage = UsageTracking.query.filter_by(user_id=user_id, year=now.year, month=now.month).first()

        if not usage:
            usage = UsageTracking(user_id=user_id, year=now.year, month=now.month)
            db.session.add(usage)
            db.session.commit()

        return usage

    def increment(self, field, amount=1):
        """Increment a usage counter"""
        current = getattr(self, field, 0)
        setattr(self, field, current + amount)
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def check_limit(self, field, user):
        """Check if user has hit their limit for a field"""
        limits = user.get_tier_limits()
        limit = limits.get(field.replace("_used", "_per_month").replace("_made", "_per_month"), 0)

        # -1 means unlimited
        if limit == -1:
            return True

        current = getattr(self, field, 0)
        return current < limit

    def __repr__(self):
        return f"<UsageTracking User:{self.user_id} {self.year}-{self.month:02d}>"


class ApiKey(db.Model):
    """API keys for programmatic access"""

    __tablename__ = "api_keys"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100))

    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_used = db.Column(db.DateTime)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    user = db.relationship("User", backref="api_keys")

    @staticmethod
    def generate_key():
        """Generate a random API key"""
        import secrets

        return f"bx_{secrets.token_urlsafe(48)}"

    def is_valid(self):
        """Check if API key is valid"""
        if not self.is_active:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

    def __repr__(self):
        return f"<ApiKey {self.name} ({self.key[:16]}...)>"
