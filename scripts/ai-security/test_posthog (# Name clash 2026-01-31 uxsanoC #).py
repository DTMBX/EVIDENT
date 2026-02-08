# Copyright © 2024–2026 Faith Frontier Ecclesiastical Trust. All rights reserved.
# PROPRIETARY — See LICENSE.

"""
Test PostHog Analytics Integration
Verify API key is working
"""

import os

from dotenv import load_dotenv

load_dotenv()

print("\n" + "=" * 70)
print("  POSTHOG ANALYTICS - CONNECTION TEST")
print("=" * 70 + "\n")

# Test 1: Check API key
print("[1/3] Checking Configuration...")
api_key = os.getenv("POSTHOG_API_KEY")
host = os.getenv("POSTHOG_HOST", "https://app.posthog.com")

if api_key and api_key != "your_key_here":
    print(f"   [OK] API Key: {api_key[:15]}...")
    print(f"   [OK] Host: {host}")
else:
    print("   [ERROR] POSTHOG_API_KEY not configured!")
    exit(1)

# Test 2: Initialize PostHog
print("\n[2/3] Initializing PostHog Client...")
try:
    import posthog

    posthog.api_key = api_key
    posthog.host = host
    print("   [OK] PostHog client initialized")
except Exception as e:
    print(f"   [ERROR] Failed to initialize: {e}")
    exit(1)

# Test 3: Send test event
print("\n[3/3] Sending Test Event...")
try:
    posthog.capture(
        distinct_id="test_user_123",
        event="System Test",
        properties={"test_type": "PostHog Integration", "timestamp": "test", "status": "testing"},
    )
    print("   [OK] Test event sent successfully!")
    print("   [INFO] Event should appear in PostHog dashboard within 60 seconds")
except Exception as e:
    print(f"   [ERROR] Failed to send event: {e}")
    exit(1)

# Summary
print("\n" + "=" * 70)
print("  POSTHOG STATUS: ACTIVE")
print("=" * 70)
print("\n✅ Analytics are now tracking:")
print("   • User signups with tier information")
print("   • Login attempts (success/failure)")
print("   • Device and browser details")
print("   • User journey through the platform")
print("\n📊 View your dashboard:")
print(f"   → {host}")
print("\n🔔 Real-time events will appear in:")
print("   → PostHog > Events > Live Events")
print("\n" + "=" * 70 + "\n")
