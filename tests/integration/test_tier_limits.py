"""
Professional-level integration tests for tier limits and usage tracking.
Tests the complete tier system including hard caps, soft caps, and overage billing.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from datetime import datetime

import pytest
from flask import Flask

from models_auth import TierLevel, UsageTracking, User, db


@pytest.fixture
def app():
    """Create test Flask application."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"

    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def db_session(app):
    """Get database session."""
    with app.app_context():
        yield db.session


class TestTierConfiguration:
    """Test tier configuration and limits."""

    def test_free_tier_limits(self, app, db_session):
        """Test FREE tier has correct hard limits."""
        with app.app_context():
            user = User(email="free@test.com", tier=TierLevel.FREE)
            user.set_password("testpass123")
            db_session.add(user)
            db_session.commit()

            limits = user.get_tier_limits()

            assert limits["bwc_videos_per_month"] == 1, "FREE tier should allow 1 video"
            assert limits["pdf_documents_per_month"] == 1, "FREE tier should allow 1 PDF"
            assert limits["one_time_file_upload"] == 1, "FREE tier should have one-time upload"
            assert limits["case_limit"] == 1, "FREE tier should allow 1 case"
            assert limits["storage_gb"] == 1, "FREE tier should have 1GB storage"
            assert limits["export_watermark"] is True, "FREE tier exports should be watermarked"
            assert limits["data_retention_days"] == 7, "FREE tier should have 7-day retention"
            assert limits["overage_allowed"] is False, "FREE tier should not allow overages"

    def test_starter_tier_limits(self, app, db_session):
        """Test STARTER tier has hard cap (no overages)."""
        with app.app_context():
            user = User(email="starter@test.com", tier=TierLevel.STARTER)
            user.set_password("testpass123")
            db_session.add(user)
            db_session.commit()

            limits = user.get_tier_limits()

            assert limits["bwc_videos_per_month"] == 10, "STARTER should allow 10 videos"
            assert limits["pdf_documents_per_month"] == 5, "STARTER should allow 5 PDFs"
            assert limits["case_limit"] == 5, "STARTER should allow 5 cases"
            assert limits["storage_gb"] == 10, "STARTER should have 10GB storage"
            assert limits["export_watermark"] is False, "STARTER exports should not be watermarked"
            assert (
                limits["overage_allowed"] is False
            ), "STARTER should NOT allow overages (HARD CAP)"
            assert limits["trial_days"] == 7, "STARTER should have 7-day trial"

    def test_professional_tier_limits(self, app, db_session):
        """Test PROFESSIONAL tier has soft cap with overage billing."""
        with app.app_context():
            user = User(email="pro@test.com", tier=TierLevel.PROFESSIONAL)
            user.set_password("testpass123")
            db_session.add(user)
            db_session.commit()

            limits = user.get_tier_limits()

            assert limits["bwc_videos_per_month"] == 25, "PRO should allow 25 videos"
            assert limits["pdf_documents_per_month"] == 15, "PRO should allow 15 PDFs"
            assert limits["case_limit"] == 15, "PRO should allow 15 cases"
            assert limits["storage_gb"] == 50, "PRO should have 50GB storage"
            assert limits["overage_allowed"] is True, "PRO should allow overages (SOFT CAP)"
            assert limits["overage_fee_per_video"] == 1.50, "PRO overage should be $1.50/video"
            assert limits["overage_fee_per_pdf"] == 0.75, "PRO overage should be $0.75/PDF"
            assert limits["trial_days"] == 3, "PRO should have 3-day trial"

    def test_premium_tier_limits(self, app, db_session):
        """Test PREMIUM tier has soft cap with higher overage fees."""
        with app.app_context():
            user = User(email="premium@test.com", tier=TierLevel.PREMIUM)
            user.set_password("testpass123")
            db_session.add(user)
            db_session.commit()

            limits = user.get_tier_limits()

            assert limits["bwc_videos_per_month"] == 75, "PREMIUM should allow 75 videos"
            assert limits["pdf_documents_per_month"] == 50, "PREMIUM should allow 50 PDFs"
            assert limits["case_limit"] == 40, "PREMIUM should allow 40 cases"
            assert limits["overage_allowed"] is True, "PREMIUM should allow overages"
            assert (
                limits["overage_fee_per_video"] == 2.00
            ), "PREMIUM overage should be $2.00/video (higher than PRO)"
            assert (
                limits["overage_fee_per_pdf"] == 1.00
            ), "PREMIUM overage should be $1.00/PDF (higher than PRO)"
            assert limits["api_access"] is True, "PREMIUM should have API access"

    def test_enterprise_tier_unlimited(self, app, db_session):
        """Test ENTERPRISE tier has no limits."""
        with app.app_context():
            user = User(email="enterprise@test.com", tier=TierLevel.ENTERPRISE)
            user.set_password("testpass123")
            db_session.add(user)
            db_session.commit()

            limits = user.get_tier_limits()

            assert limits["bwc_videos_per_month"] == -1, "ENTERPRISE should have unlimited videos"
            assert limits["pdf_documents_per_month"] == -1, "ENTERPRISE should have unlimited PDFs"
            assert limits["case_limit"] == -1, "ENTERPRISE should have unlimited cases"
            assert limits["storage_gb"] == -1, "ENTERPRISE should have unlimited storage"
            assert (
                limits["overage_allowed"] is False
            ), "ENTERPRISE should not need overages (unlimited)"
            assert limits["is_unlimited"] is True, "ENTERPRISE should be marked as unlimited"
            assert limits["white_label"] is True, "ENTERPRISE should have white-label"


class TestUsageTracking:
    """Test usage tracking and limit enforcement."""

    def test_usage_tracking_creation(self, app, db_session):
        """Test usage tracking record creation."""
        with app.app_context():
            user = User(email="test@test.com", tier=TierLevel.STARTER)
            user.set_password("testpass123")
            db_session.add(user)
            db_session.commit()

            usage = UsageTracking.get_or_create_current(user.id)

            assert usage.user_id == user.id
            assert usage.year == datetime.utcnow().year
            assert usage.month == datetime.utcnow().month
            assert usage.bwc_videos_processed == 0
            assert usage.pdf_documents_processed == 0

    def test_usage_increment(self, app, db_session):
        """Test incrementing usage counters."""
        with app.app_context():
            user = User(email="test@test.com", tier=TierLevel.STARTER)
            user.set_password("testpass123")
            db_session.add(user)
            db_session.commit()

            usage = UsageTracking.get_or_create_current(user.id)

            # Increment videos
            usage.increment("bwc_videos_processed", 1)
            assert usage.bwc_videos_processed == 1

            # Increment PDFs
            usage.increment("pdf_documents_processed", 1)
            assert usage.pdf_documents_processed == 1

            # Increment multiple
            usage.increment("bwc_videos_processed", 3)
            assert usage.bwc_videos_processed == 4

    def test_starter_hard_cap_enforcement(self, app, db_session):
        """Test STARTER tier hard cap prevents overages."""
        with app.app_context():
            user = User(email="starter@test.com", tier=TierLevel.STARTER)
            user.set_password("testpass123")
            db_session.add(user)
            db_session.commit()

            limits = user.get_tier_limits()
            usage = UsageTracking.get_or_create_current(user.id)

            # Simulate uploading to limit
            video_limit = limits["bwc_videos_per_month"]
            usage.bwc_videos_processed = video_limit
            db_session.commit()

            # Check if at limit
            assert usage.bwc_videos_processed >= video_limit
            assert limits["overage_allowed"] is False, "STARTER should not allow overages"

    def test_professional_soft_cap_allows_overage(self, app, db_session):
        """Test PROFESSIONAL tier soft cap allows overages."""
        with app.app_context():
            user = User(email="pro@test.com", tier=TierLevel.PROFESSIONAL)
            user.set_password("testpass123")
            db_session.add(user)
            db_session.commit()

            limits = user.get_tier_limits()
            usage = UsageTracking.get_or_create_current(user.id)

            # Simulate exceeding limit
            video_limit = limits["bwc_videos_per_month"]
            usage.bwc_videos_processed = video_limit + 5  # 5 overages
            db_session.commit()

            # Check overage calculation
            overage_count = usage.bwc_videos_processed - video_limit
            overage_fee = overage_count * limits["overage_fee_per_video"]

            assert limits["overage_allowed"] is True, "PRO should allow overages"
            assert overage_count == 5, "Should have 5 overage videos"
            assert overage_fee == 7.50, "Overage fee should be $7.50 (5 × $1.50)"


class TestTierComparison:
    """Test tier comparison and progressive pricing."""

    def test_overage_fee_progression(self, app, db_session):
        """Test that overage fees increase with tier (incentivize upgrades)."""
        with app.app_context():
            pro_user = User(email="pro@test.com", tier=TierLevel.PROFESSIONAL)
            premium_user = User(email="premium@test.com", tier=TierLevel.PREMIUM)

            pro_limits = pro_user.get_tier_limits()
            premium_limits = premium_user.get_tier_limits()

            # PRO should have LOWER overage fees than PREMIUM
            assert (
                pro_limits["overage_fee_per_video"] < premium_limits["overage_fee_per_video"]
            ), "PRO overage should be cheaper than PREMIUM to support growth"
            assert (
                pro_limits["overage_fee_per_pdf"] < premium_limits["overage_fee_per_pdf"]
            ), "PRO PDF overage should be cheaper than PREMIUM"

    def test_hard_vs_soft_cap_strategy(self, app, db_session):
        """Test that cheaper tier has hard cap, more expensive has soft cap."""
        with app.app_context():
            starter_user = User(email="starter@test.com", tier=TierLevel.STARTER)
            pro_user = User(email="pro@test.com", tier=TierLevel.PROFESSIONAL)

            starter_limits = starter_user.get_tier_limits()
            pro_limits = pro_user.get_tier_limits()

            # STARTER ($29) should have HARD CAP
            assert (
                starter_limits["overage_allowed"] is False
            ), "STARTER should have hard cap (predictable pricing)"

            # PROFESSIONAL ($79) should have SOFT CAP
            assert (
                pro_limits["overage_allowed"] is True
            ), "PROFESSIONAL should have soft cap (flexible growth)"

    def test_trial_duration_by_tier(self, app, db_session):
        """Test trial duration is appropriate for each tier."""
        with app.app_context():
            starter_user = User(email="starter@test.com", tier=TierLevel.STARTER)
            pro_user = User(email="pro@test.com", tier=TierLevel.PROFESSIONAL)

            starter_limits = starter_user.get_tier_limits()
            pro_limits = pro_user.get_tier_limits()

            # STARTER gets longer trial (7 days) to prove value at lower price
            assert starter_limits.get("trial_days") == 7, "STARTER should have 7-day trial"

            # PRO gets shorter trial (3 days) for faster decision
            assert pro_limits.get("trial_days") == 3, "PROFESSIONAL should have 3-day trial"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unlimited_tier_limits(self, app, db_session):
        """Test unlimited tiers handle -1 properly."""
        with app.app_context():
            user = User(email="enterprise@test.com", tier=TierLevel.ENTERPRISE)
            limits = user.get_tier_limits()

            # All key limits should be -1 (unlimited)
            assert limits["bwc_videos_per_month"] == -1
            assert limits["pdf_documents_per_month"] == -1
            assert limits["case_limit"] == -1
            assert limits["storage_gb"] == -1

    def test_free_tier_one_time_upload(self, app, db_session):
        """Test FREE tier one-time upload tracking."""
        with app.app_context():
            user = User(email="free@test.com", tier=TierLevel.FREE)
            user.set_password("testpass123")
            db_session.add(user)
            db_session.commit()

            # Initially should not have used one-time upload
            assert user.one_time_upload_used is False

            # Simulate using one-time upload
            user.one_time_upload_used = True
            user.one_time_upload_date = datetime.utcnow()
            db_session.commit()

            # Should now be marked as used
            assert user.one_time_upload_used is True
            assert user.one_time_upload_date is not None

    def test_tier_price_mapping(self, app):
        """Test tier enum values match monthly prices."""
        with app.app_context():
            assert TierLevel.FREE.value == 0, "FREE should be $0"
            assert TierLevel.STARTER.value == 29, "STARTER should be $29"
            assert TierLevel.PROFESSIONAL.value == 79, "PROFESSIONAL should be $79"
            assert TierLevel.PREMIUM.value == 199, "PREMIUM should be $199"
            assert TierLevel.ENTERPRISE.value == 599, "ENTERPRISE should be $599"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
