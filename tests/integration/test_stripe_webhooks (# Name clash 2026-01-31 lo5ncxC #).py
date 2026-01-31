"""
Stripe Webhook Test Script
Tests all webhook handlers with simulated events

Run with: python test_stripe_webhooks.py
"""

import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta

import requests

# Configuration
WEBHOOK_URL = "http://localhost:5000/api/stripe/webhook"
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_test_placeholder")


def generate_stripe_signature(payload: str, secret: str) -> str:
    """Generate Stripe webhook signature"""
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.{payload}"
    signature = hmac.new(
        secret.encode("utf-8"), signed_payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


def send_webhook_event(event_type: str, data: dict) -> dict:
    """Send a test webhook event"""
    event = {
        "id": f"evt_test_{int(time.time())}",
        "object": "event",
        "api_version": "2025-06-30.basil",
        "created": int(time.time()),
        "type": event_type,
        "data": {"object": data},
    }

    payload = json.dumps(event)
    signature = generate_stripe_signature(payload, WEBHOOK_SECRET)

    headers = {"Content-Type": "application/json", "Stripe-Signature": signature}

    try:
        response = requests.post(WEBHOOK_URL, data=payload, headers=headers, timeout=10)
        return {
            "event": event_type,
            "status_code": response.status_code,
            "response": (
                response.json()
                if response.headers.get("content-type", "").startswith("application/json")
                else response.text
            ),
            "success": response.status_code == 200,
        }
    except requests.exceptions.RequestException as e:
        return {"event": event_type, "status_code": 0, "response": str(e), "success": False}


def test_all_webhooks():
    """Test all webhook events"""

    print("=" * 70)
    print("🧪 STRIPE WEBHOOK TEST SUITE")
    print("=" * 70)
    print(f"Endpoint: {WEBHOOK_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Test data
    customer_id = "cus_test_123456"
    subscription_id = "sub_test_789012"
    invoice_id = "in_test_345678"
    user_id = "1"  # Admin user

    results = []

    # =========================================
    # 1. CHECKOUT EVENTS
    # =========================================
    print("\n📦 CHECKOUT EVENTS")
    print("-" * 50)

    # checkout.session.completed
    result = send_webhook_event(
        "checkout.session.completed",
        {
            "id": "cs_test_session_123",
            "object": "checkout.session",
            "customer": customer_id,
            "subscription": subscription_id,
            "payment_status": "paid",
            "status": "complete",
            "metadata": {"user_id": user_id, "tier": "PROFESSIONAL"},
        },
    )
    results.append(result)
    print(
        f"  {'✅' if result['success'] else '❌'} checkout.session.completed: {result['status_code']}"
    )

    # =========================================
    # 2. SUBSCRIPTION EVENTS
    # =========================================
    print("\n📋 SUBSCRIPTION EVENTS")
    print("-" * 50)

    # customer.subscription.created
    result = send_webhook_event(
        "customer.subscription.created",
        {
            "id": subscription_id,
            "object": "subscription",
            "customer": customer_id,
            "status": "active",
            "current_period_start": int(time.time()),
            "current_period_end": int(time.time()) + 30 * 24 * 60 * 60,  # 30 days
            "trial_end": None,
            "items": {
                "data": [{"price": {"id": "price_professional", "product": "prod_professional"}}]
            },
        },
    )
    results.append(result)
    print(
        f"  {'✅' if result['success'] else '❌'} customer.subscription.created: {result['status_code']}"
    )

    # customer.subscription.updated
    result = send_webhook_event(
        "customer.subscription.updated",
        {
            "id": subscription_id,
            "object": "subscription",
            "customer": customer_id,
            "status": "active",
            "current_period_start": int(time.time()),
            "current_period_end": int(time.time()) + 30 * 24 * 60 * 60,
            "cancel_at_period_end": False,
        },
    )
    results.append(result)
    print(
        f"  {'✅' if result['success'] else '❌'} customer.subscription.updated: {result['status_code']}"
    )

    # customer.subscription.trial_will_end
    result = send_webhook_event(
        "customer.subscription.trial_will_end",
        {
            "id": subscription_id,
            "object": "subscription",
            "customer": customer_id,
            "status": "trialing",
            "trial_end": int(time.time()) + 3 * 24 * 60 * 60,  # 3 days from now
        },
    )
    results.append(result)
    print(
        f"  {'✅' if result['success'] else '❌'} customer.subscription.trial_will_end: {result['status_code']}"
    )

    # customer.subscription.paused
    result = send_webhook_event(
        "customer.subscription.paused",
        {
            "id": subscription_id,
            "object": "subscription",
            "customer": customer_id,
            "status": "paused",
        },
    )
    results.append(result)
    print(
        f"  {'✅' if result['success'] else '❌'} customer.subscription.paused: {result['status_code']}"
    )

    # customer.subscription.resumed
    result = send_webhook_event(
        "customer.subscription.resumed",
        {
            "id": subscription_id,
            "object": "subscription",
            "customer": customer_id,
            "status": "active",
            "current_period_end": int(time.time()) + 30 * 24 * 60 * 60,
        },
    )
    results.append(result)
    print(
        f"  {'✅' if result['success'] else '❌'} customer.subscription.resumed: {result['status_code']}"
    )

    # customer.subscription.deleted
    result = send_webhook_event(
        "customer.subscription.deleted",
        {
            "id": subscription_id,
            "object": "subscription",
            "customer": customer_id,
            "status": "canceled",
        },
    )
    results.append(result)
    print(
        f"  {'✅' if result['success'] else '❌'} customer.subscription.deleted: {result['status_code']}"
    )

    # =========================================
    # 3. INVOICE EVENTS
    # =========================================
    print("\n💰 INVOICE EVENTS")
    print("-" * 50)

    # invoice.paid
    result = send_webhook_event(
        "invoice.paid",
        {
            "id": invoice_id,
            "object": "invoice",
            "customer": customer_id,
            "subscription": subscription_id,
            "status": "paid",
            "amount_paid": 7900,  # $79.00 in cents
            "currency": "usd",
            "paid": True,
        },
    )
    results.append(result)
    print(f"  {'✅' if result['success'] else '❌'} invoice.paid: {result['status_code']}")

    # invoice.payment_failed
    result = send_webhook_event(
        "invoice.payment_failed",
        {
            "id": invoice_id,
            "object": "invoice",
            "customer": customer_id,
            "subscription": subscription_id,
            "status": "open",
            "amount_due": 7900,
            "attempt_count": 1,
            "next_payment_attempt": int(time.time()) + 3 * 24 * 60 * 60,
        },
    )
    results.append(result)
    print(
        f"  {'✅' if result['success'] else '❌'} invoice.payment_failed: {result['status_code']}"
    )

    # invoice.payment_action_required
    result = send_webhook_event(
        "invoice.payment_action_required",
        {
            "id": invoice_id,
            "object": "invoice",
            "customer": customer_id,
            "subscription": subscription_id,
            "status": "open",
            "hosted_invoice_url": "https://invoice.stripe.com/i/test_invoice_123",
        },
    )
    results.append(result)
    print(
        f"  {'✅' if result['success'] else '❌'} invoice.payment_action_required: {result['status_code']}"
    )

    # invoice.upcoming
    result = send_webhook_event(
        "invoice.upcoming",
        {
            "id": None,  # Upcoming invoices don't have an ID yet
            "object": "invoice",
            "customer": customer_id,
            "subscription": subscription_id,
            "amount_due": 7900,
            "currency": "usd",
            "period_start": int(time.time()) + 27 * 24 * 60 * 60,
            "period_end": int(time.time()) + 57 * 24 * 60 * 60,
        },
    )
    results.append(result)
    print(f"  {'✅' if result['success'] else '❌'} invoice.upcoming: {result['status_code']}")

    # =========================================
    # 4. CUSTOMER EVENTS
    # =========================================
    print("\n👤 CUSTOMER EVENTS")
    print("-" * 50)

    # customer.created
    result = send_webhook_event(
        "customer.created",
        {
            "id": customer_id,
            "object": "customer",
            "email": "test@barberx.info",
            "name": "Test User",
            "created": int(time.time()),
        },
    )
    results.append(result)
    print(f"  {'✅' if result['success'] else '❌'} customer.created: {result['status_code']}")

    # customer.updated
    result = send_webhook_event(
        "customer.updated",
        {
            "id": customer_id,
            "object": "customer",
            "email": "updated@barberx.info",
            "name": "Updated User",
        },
    )
    results.append(result)
    print(f"  {'✅' if result['success'] else '❌'} customer.updated: {result['status_code']}")

    # =========================================
    # 5. PAYMENT INTENT EVENTS
    # =========================================
    print("\n💳 PAYMENT INTENT EVENTS")
    print("-" * 50)

    # payment_intent.succeeded
    result = send_webhook_event(
        "payment_intent.succeeded",
        {
            "id": "pi_test_123456",
            "object": "payment_intent",
            "customer": customer_id,
            "amount": 5000,  # $50.00
            "currency": "usd",
            "status": "succeeded",
            "metadata": {"type": "usage_credits", "credits": "100"},
        },
    )
    results.append(result)
    print(
        f"  {'✅' if result['success'] else '❌'} payment_intent.succeeded: {result['status_code']}"
    )

    # payment_intent.payment_failed
    result = send_webhook_event(
        "payment_intent.payment_failed",
        {
            "id": "pi_test_failed_789",
            "object": "payment_intent",
            "customer": customer_id,
            "amount": 5000,
            "currency": "usd",
            "status": "requires_payment_method",
            "last_payment_error": {"message": "Your card was declined."},
        },
    )
    results.append(result)
    print(
        f"  {'✅' if result['success'] else '❌'} payment_intent.payment_failed: {result['status_code']}"
    )

    # =========================================
    # SUMMARY
    # =========================================
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed

    print(f"\n  Total Events Tested: {len(results)}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  Success Rate: {passed/len(results)*100:.1f}%")

    if failed > 0:
        print("\n  Failed Events:")
        for r in results:
            if not r["success"]:
                print(f"    - {r['event']}: {r['status_code']} - {r['response']}")

    print("\n" + "=" * 70)
    print("Check your Flask server console for detailed webhook handling logs!")
    print("=" * 70)

    return results


if __name__ == "__main__":
    test_all_webhooks()
