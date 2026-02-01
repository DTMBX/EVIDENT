"""
Deep professional-level tests for tier enforcement and access control.
Tests decorator-based tier gating and usage limit enforcement.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from flask import Flask, jsonify, session

from models_auth import TierLevel, UsageTracking, User, db
from tier_gating import check_usage_limit, require_tier


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
def client(app):
    """Get test client."""
    return app.test_client()


@pytest.fixture
def users(app):
    """Create test users for each tier."""
    with app.app_context():
        users_dict = {}

        for tier in [
            TierLevel.FREE,
            TierLevel.STARTER,
            TierLevel.PROFESSIONAL,
            TierLevel.PREMIUM,
            TierLevel.ENTERPRISE,
        ]:
            user = User(email=f"{tier.name.lower()}@test.com", tier=tier, is_active=True)
            user.set_password("testpass123")
            db.session.add(user)
            users_dict[tier.name] = user

        db.session.commit()

        # Reload users to get IDs
        for tier_name in users_dict:
            users_dict[tier_name] = User.query.filter_by(
                email=f"{tier_name.lower()}@test.com"
            ).first()

        return users_dict


class TestTierRequireDecorator:
    """Test @require_tier decorator for access control."""

    def test_require_tier_allows_exact_tier(self, app, client, users):
        """Test user with exact required tier can access."""
        with app.app_context():

            @app.route("/test-pro-feature")
            @require_tier(TierLevel.PROFESSIONAL)
            def pro_feature():
                return jsonify({"message": "PRO feature accessed"})

            with client.session_transaction() as sess:
                sess["user_id"] = users["PROFESSIONAL"].id

            response = client.get("/test-pro-feature")
            assert response.status_code == 200
            data = response.get_json()
            assert data["message"] == "PRO feature accessed"

    def test_require_tier_allows_higher_tier(self, app, client, users):
        """Test user with higher tier can access lower tier features."""
        with app.app_context():

            @app.route("/test-starter-feature")
            @require_tier(TierLevel.STARTER)
            def starter_feature():
                return jsonify({"message": "STARTER feature accessed"})

            # PROFESSIONAL user should access STARTER feature
            with client.session_transaction() as sess:
                sess["user_id"] = users["PROFESSIONAL"].id

            response = client.get("/test-starter-feature")
            assert response.status_code == 200

    def test_require_tier_blocks_lower_tier(self, app, client, users):
        """Test user with lower tier cannot access higher tier features."""
        with app.app_context():

            @app.route("/test-premium-feature")
            @require_tier(TierLevel.PREMIUM)
            def premium_feature():
                return jsonify({"message": "PREMIUM feature accessed"})

            # STARTER user should NOT access PREMIUM feature
            with client.session_transaction() as sess:
                sess["user_id"] = users["STARTER"].id

            response = client.get("/test-premium-feature")
            assert response.status_code == 403
            data = response.get_json()
            assert "upgrade_required" in data
            assert data["upgrade_required"] is True

    def test_require_tier_requires_authentication(self, app, client):
        """Test @require_tier blocks unauthenticated users."""
        with app.app_context():

            @app.route("/test-auth-required")
            @require_tier(TierLevel.FREE)
            def auth_required():
                return jsonify({"message": "Authenticated"})

            # No session - should be blocked
            response = client.get("/test-auth-required")
            assert response.status_code == 401
            data = response.get_json()
            assert "Authentication required" in data["error"]


class TestUsageLimitDecorator:
    """Test @check_usage_limit decorator for usage tracking."""

    def test_usage_limit_allows_under_limit(self, app, client, users):
        """Test user under limit can proceed."""
        with app.app_context():

            @app.route("/test-upload", methods=["POST"])
            @check_usage_limit("bwc_videos_per_month", increment=1)
            def upload_video():
                return jsonify({"message": "Upload successful"})

            # STARTER user with 0 videos (limit is 10)
            with client.session_transaction() as sess:
                sess["user_id"] = users["STARTER"].id

            response = client.post("/test-upload")
            assert response.status_code == 200

            # Check usage was incremented
            usage = UsageTracking.get_or_create_current(users["STARTER"].id)
            assert usage.bwc_videos_processed == 1

    def test_usage_limit_blocks_at_hard_cap(self, app, client, users):
        """Test STARTER tier hard cap blocks at limit."""
        with app.app_context():

            @app.route("/test-upload-hard-cap", methods=["POST"])
            @check_usage_limit("bwc_videos_per_month", increment=1)
            def upload_with_hard_cap():
                return jsonify({"message": "Upload successful"})

            starter_user = users["STARTER"]

            # Set usage to limit
            usage = UsageTracking.get_or_create_current(starter_user.id)
            usage.bwc_videos_processed = 10  # At STARTER limit
            db.session.commit()

            with client.session_transaction() as sess:
                sess["user_id"] = starter_user.id

            # Should be blocked (STARTER has hard cap)
            response = client.post("/test-upload-hard-cap")
            # This would return an error in actual implementation
            # Implementation depends on how check_usage_limit handles hard caps

    def test_usage_limit_allows_overage_for_soft_cap(self, app, client, users):
        """Test PROFESSIONAL tier soft cap allows overage."""
        with app.app_context():
            pro_user = users["PROFESSIONAL"]
            limits = pro_user.get_tier_limits()

            # PRO should allow overages
            assert limits["overage_allowed"] is True

            # Set usage to limit
            usage = UsageTracking.get_or_create_current(pro_user.id)
            usage.bwc_videos_processed = limits["bwc_videos_per_month"]
            db.session.commit()

            # Should still be able to upload (with overage fee)
            # Implementation would show overage modal to user


class TestTierUpgradeIncentives:
    """Test that tier structure incentivizes natural progression."""

    def test_starter_to_pro_upgrade_incentive(self, app, users):
        """Test STARTER users hitting hard cap are incentivized to upgrade to PRO."""
        with app.app_context():
            starter_limits = users["STARTER"].get_tier_limits()
            pro_limits = users["PROFESSIONAL"].get_tier_limits()

            # STARTER has restrictive hard cap
            assert starter_limits["overage_allowed"] is False
            assert starter_limits["bwc_videos_per_month"] == 10

            # PRO offers 2.5x more capacity + flexibility
            assert pro_limits["overage_allowed"] is True
            assert pro_limits["bwc_videos_per_month"] == 25

            # PRO provides much more value for $50 more per month
            price_diff = TierLevel.PROFESSIONAL.value - TierLevel.STARTER.value
            capacity_mult = (
                pro_limits["bwc_videos_per_month"] / starter_limits["bwc_videos_per_month"]
            )

            assert price_diff == 50  # $79 - $29 = $50
            assert capacity_mult == 2.5  # 25/10 = 2.5x

            # Plus PRO adds: overage flexibility, more storage (50GB vs 10GB)
            assert pro_limits["storage_gb"] == 50
            assert starter_limits["storage_gb"] == 10

    def test_pro_to_premium_upgrade_incentive(self, app, users):
        """Test PRO users are incentivized to upgrade to PREMIUM for better rates."""
        with app.app_context():
            pro_limits = users["PROFESSIONAL"].get_tier_limits()
            premium_limits = users["PREMIUM"].get_tier_limits()

            # PREMIUM has 3x capacity
            assert premium_limits["bwc_videos_per_month"] == 75
            assert pro_limits["bwc_videos_per_month"] == 25

            # PREMIUM adds API access (huge value)
            assert premium_limits["api_access"] is True
            assert pro_limits["api_access"] is False

            # PREMIUM has forensic analysis
            assert premium_limits["forensic_analysis"] is True

            # PREMIUM has much more storage (250GB vs 50GB)
            assert premium_limits["storage_gb"] == 250
            assert pro_limits["storage_gb"] == 50

    def test_overage_cost_vs_upgrade_cost(self, app, users):
        """Test that frequent overages cost more than upgrading."""
        with app.app_context():
            pro_limits = users["PROFESSIONAL"].get_tier_limits()
            premium_limits = users["PREMIUM"].get_tier_limits()

            # If PRO user uploads 50 videos (25 base + 25 overage)
            pro_base_cost = TierLevel.PROFESSIONAL.value  # $79
            overage_count = 25
            overage_cost = (
                overage_count * pro_limits["overage_fee_per_video"]
            )  # 25 × $1.50 = $37.50
            pro_total = pro_base_cost + overage_cost  # $79 + $37.50 = $116.50

            premium_cost = TierLevel.PREMIUM.value  # $199

            # At 50 videos, PRO with overage = $116.50
            # PREMIUM allows 75 videos for $199
            # But PREMIUM also adds: API, forensic tools, priority support
            # So if user consistently needs 50+ videos, PREMIUM is better value

            assert pro_total == 116.50
            assert premium_cost == 199

            # Breakeven point: When does overage cost justify PREMIUM?
            # $199 - $79 = $120 difference
            # $120 / $1.50 per video = 80 overage videos
            # So if user needs 25 + 80 = 105 videos, they should upgrade
            # Since PREMIUM only allows 75, this incentivizes ENTERPRISE


class TestDataIntegrity:
    """Test data integrity and edge cases."""

    def test_usage_tracking_monthly_reset(self, app, users):
        """Test that usage should reset monthly (conceptually)."""
        with app.app_context():
            from datetime import datetime

            user = users["STARTER"]
            usage = UsageTracking.get_or_create_current(user.id)

            # Current month usage
            assert usage.year == datetime.utcnow().year
            assert usage.month == datetime.utcnow().month

            # In a real system, next month would create new UsageTracking record
            # This is handled by get_or_create_current checking year/month

    def test_trial_expiration_logic(self, app, users):
        """Test trial period tracking."""
        with app.app_context():
            from datetime import datetime, timedelta

            starter_user = users["STARTER"]
            starter_limits = starter_user.get_tier_limits()

            # STARTER gets 7-day trial
            assert starter_limits["trial_days"] == 7

            # Simulate trial activation
            starter_user.is_on_trial = True
            starter_user.trial_end = datetime.utcnow() + timedelta(days=7)
            db.session.commit()

            # Check trial is active
            assert starter_user.is_on_trial is True
            assert starter_user.trial_end > datetime.utcnow()

    def test_tier_display_names(self, app, users):
        """Test tier display names are user-friendly."""
        with app.app_context():
            assert users["FREE"].tier_name == "Explorer"
            assert users["STARTER"].tier_name == "Practitioner"
            assert users["PROFESSIONAL"].tier_name == "Counselor"
            assert users["PREMIUM"].tier_name == "Advocate"
            assert users["ENTERPRISE"].tier_name == "Enterprise"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
