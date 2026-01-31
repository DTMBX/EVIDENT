"""
Test script to verify quota system is working correctly
"""

import sys

sys.path.insert(0, ".")

from app import app
from models_auth import User, db
from usage_meter import SmartMeter, UsageQuota


def test_quota_system():
    """Test quota initialization and tracking"""
    with app.app_context():
        print("\n" + "=" * 70)
        print("  TESTING QUOTA SYSTEM")
        print("=" * 70 + "\n")

        # Get all users
        users = User.query.all()

        print(f"Found {len(users)} users in database:\n")

        for user in users:
            print(f"👤 User: {user.email}")
            print(f"   Tier: {user.tier}")

            # Get quota
            quota = UsageQuota.query.filter_by(user_id=user.id).first()

            if quota:
                print(f"   ✅ Quota initialized")
                print(f"   📊 AI Tokens: {quota.ai_tokens_used}/{quota.ai_tokens_limit}")
                print(f"   🤖 AI Requests: {quota.ai_requests_count}/{quota.ai_requests_limit}")
                print(
                    f"   💾 Storage: {quota.storage_bytes_used}/{quota.storage_bytes_limit} bytes"
                )
                print(f"   📁 Files: {quota.files_uploaded_count}/{quota.files_uploaded_limit}")
                print(f"   🔍 Analyses: {quota.analyses_count}/{quota.analyses_limit}")
                print(f"   💰 Cost: ${quota.total_cost_usd or 0:.2f}")
                print(
                    f"   📅 Period: {quota.period_start.strftime('%Y-%m-%d')} to {quota.period_end.strftime('%Y-%m-%d')}"
                )

                # Test quota check
                has_quota, msg = quota.check_quota("ai_requests")
                print(f"   🔐 Can make AI request: {'✅ Yes' if has_quota else '❌ No'}")
                if not has_quota:
                    print(f"      Message: {msg}")
            else:
                print(f"   ❌ No quota found")

            print()

        # Test event tracking
        print("\n" + "=" * 70)
        print("  TESTING EVENT TRACKING")
        print("=" * 70 + "\n")

        if users:
            test_user = users[0]
            print(f"Testing with user: {test_user.email}\n")

            # Track a test event
            event = SmartMeter.track_event(
                user_id=test_user.id,
                event_type="test_event",
                event_category="testing",
                resource_name="quota_system_test",
                tokens_input=100,
                tokens_output=50,
                cost_usd=0.001,
                status="success",
            )

            print(f"✅ Test event tracked:")
            print(f"   ID: {event.id}")
            print(f"   Type: {event.event_type}")
            print(f"   Tokens: {event.tokens_input + event.tokens_output}")
            print(f"   Cost: ${event.cost_usd}")
            print(f"   Timestamp: {event.timestamp}")

            # Get updated quota
            quota = UsageQuota.query.filter_by(user_id=test_user.id).first()
            print(f"\n📊 Updated quota after test event:")
            print(f"   AI Tokens: {quota.ai_tokens_used}/{quota.ai_tokens_limit}")
            print(f"   AI Requests: {quota.ai_requests_count}/{quota.ai_requests_limit}")
            print(f"   Cost: ${quota.total_cost_usd or 0:.6f}")

        print("\n" + "=" * 70)
        print("  ✅ QUOTA SYSTEM TEST COMPLETE")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    test_quota_system()
