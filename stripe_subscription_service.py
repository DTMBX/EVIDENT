"""
Stripe Subscription Service
Handles subscription creation, webhooks, and billing management
"""

import os
from datetime import datetime, timedelta
from functools import wraps

import stripe
from flask import Blueprint, jsonify, redirect, request, session, url_for

from models_auth import TierLevel, User, db

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Stripe Price IDs (set these in .env after creating products in Stripe)
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "")
STRIPE_PRICE_PREMIUM = os.getenv("STRIPE_PRICE_PREMIUM", "")

# Create Flask blueprint
stripe_bp = Blueprint("stripe", __name__, url_prefix="/api/stripe")


def require_login(f):
    """Decorator to require login"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)

    return decorated_function


class StripeSubscriptionService:
    """Service class for Stripe subscription management"""

    @staticmethod
    def create_customer(user):
        """Create or retrieve Stripe customer for user"""
        if user.stripe_customer_id:
            try:
                # Retrieve existing customer
                customer = stripe.Customer.retrieve(user.stripe_customer_id)
                return customer
            except stripe.error.StripeError:
                # Customer not found, create new one
                pass

        # Create new Stripe customer
        customer = stripe.Customer.create(
            email=user.email,
            name=user.full_name or user.email,
            metadata={"user_id": user.id, "organization": user.organization or ""},
        )

        # Save customer ID
        user.stripe_customer_id = customer.id
        db.session.commit()

        return customer

    @staticmethod
    def create_checkout_session(user, tier, success_url, cancel_url):
        """
        Create Stripe checkout session for subscription

        Args:
            user: User model instance
            tier: TierLevel enum (PROFESSIONAL or PREMIUM)
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if user cancels
        """
        # Get or create customer
        customer = StripeSubscriptionService.create_customer(user)

        # Determine price ID and trial days
        if tier == TierLevel.PROFESSIONAL:
            price_id = STRIPE_PRICE_PRO
            trial_days = 3  # 3-day free trial for PRO
        elif tier == TierLevel.PREMIUM:
            price_id = STRIPE_PRICE_PREMIUM
            trial_days = 0  # No trial for PREMIUM
        else:
            raise ValueError(f"Invalid tier for checkout: {tier}")

        if not price_id:
            raise ValueError(f"Stripe price ID not configured for {tier.name}")

        # Create checkout session
        session_params = {
            "customer": customer.id,
            "payment_method_types": ["card"],
            "line_items": [
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            "mode": "subscription",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": {"user_id": user.id, "tier": tier.name},
            "allow_promotion_codes": True,  # Allow discount codes
        }

        # Add trial period for PRO
        if trial_days > 0:
            session_params["subscription_data"] = {
                "trial_period_days": trial_days,
                "metadata": {"user_id": user.id, "tier": tier.name},
            }

        checkout_session = stripe.checkout.Session.create(**session_params)

        return checkout_session

    @staticmethod
    def create_portal_session(user, return_url):
        """
        Create Stripe customer portal session for subscription management
        Allows users to update payment, cancel subscription, etc.
        """
        if not user.stripe_customer_id:
            raise ValueError("User has no Stripe customer ID")

        portal_session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=return_url,
        )

        return portal_session

    @staticmethod
    def handle_checkout_completed(session):
        """Handle successful checkout completion"""
        user_id = session.get("metadata", {}).get("user_id")
        if not user_id:
            print("No user_id in checkout session metadata")
            return

        user = User.query.get(int(user_id))
        if not user:
            print(f"User {user_id} not found")
            return

        # Get subscription details
        subscription_id = session.get("subscription")
        if subscription_id:
            subscription = stripe.Subscription.retrieve(subscription_id)

            # Update user subscription info
            tier_name = session.get("metadata", {}).get("tier", "PROFESSIONAL")
            user.tier = TierLevel[tier_name]
            user.stripe_subscription_id = subscription.id
            user.stripe_subscription_status = subscription.status
            user.stripe_current_period_end = datetime.fromtimestamp(subscription.current_period_end)
            user.subscription_start = datetime.utcnow()

            # Check if trial
            if subscription.trial_end:
                user.trial_end = datetime.fromtimestamp(subscription.trial_end)
                user.is_on_trial = True
            else:
                user.is_on_trial = False

            db.session.commit()
            print(f"✅ User {user.email} upgraded to {tier_name}")

    @staticmethod
    def handle_subscription_updated(subscription):
        """Handle subscription update (status change, renewal, etc.)"""
        # Find user by subscription ID
        user = User.query.filter_by(stripe_subscription_id=subscription.id).first()
        if not user:
            print(f"User not found for subscription {subscription.id}")
            return

        # Update subscription status
        user.stripe_subscription_status = subscription.status
        user.stripe_current_period_end = datetime.fromtimestamp(subscription.current_period_end)

        # Check trial status
        if subscription.trial_end:
            user.trial_end = datetime.fromtimestamp(subscription.trial_end)
            trial_end_dt = datetime.fromtimestamp(subscription.trial_end)
            user.is_on_trial = datetime.utcnow() < trial_end_dt
        else:
            user.is_on_trial = False

        # Handle status changes
        if subscription.status in ["active", "trialing"]:
            # Subscription is active
            pass
        elif subscription.status in ["canceled", "unpaid", "past_due"]:
            # Downgrade to FREE if subscription ended
            if subscription.status == "canceled":
                user.tier = TierLevel.FREE
                user.subscription_end = datetime.utcnow()
                print(f"⚠️ User {user.email} downgraded to FREE (subscription canceled)")

        db.session.commit()
        print(f"✅ Updated subscription for {user.email}: {subscription.status}")

    @staticmethod
    def handle_subscription_deleted(subscription):
        """Handle subscription cancellation"""
        user = User.query.filter_by(stripe_subscription_id=subscription.id).first()
        if not user:
            return

        # Downgrade to FREE
        user.tier = TierLevel.FREE
        user.stripe_subscription_status = "canceled"
        user.subscription_end = datetime.utcnow()
        user.is_on_trial = False

        db.session.commit()
        print(f"❌ User {user.email} subscription canceled, downgraded to FREE")


# ============================================================================
# FLASK ROUTES
# ============================================================================


@stripe_bp.route("/create-checkout-session", methods=["POST"])
@require_login
def create_checkout_session():
    """Create Stripe checkout session"""
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.json
    tier_name = data.get("tier", "PROFESSIONAL").upper()

    try:
        tier = TierLevel[tier_name]
    except KeyError:
        return jsonify({"error": f"Invalid tier: {tier_name}"}), 400

    if tier not in [TierLevel.PROFESSIONAL, TierLevel.PREMIUM]:
        return jsonify({"error": "Invalid tier for checkout"}), 400

    # Build URLs
    base_url = request.host_url.rstrip("/")
    success_url = f"{base_url}/dashboard?checkout=success&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{base_url}/pricing?checkout=canceled"

    try:
        checkout_session = StripeSubscriptionService.create_checkout_session(
            user=user, tier=tier, success_url=success_url, cancel_url=cancel_url
        )

        return jsonify({"url": checkout_session.url})

    except Exception as e:
        print(f"Error creating checkout session: {e}")
        return jsonify({"error": str(e)}), 500


@stripe_bp.route("/create-portal-session", methods=["POST"])
@require_login
def create_portal_session():
    """Create Stripe customer portal session"""
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    if not user.stripe_customer_id:
        return jsonify({"error": "No subscription found"}), 404

    base_url = request.host_url.rstrip("/")
    return_url = f"{base_url}/dashboard"

    try:
        portal_session = StripeSubscriptionService.create_portal_session(user, return_url)
        return jsonify({"url": portal_session.url})

    except Exception as e:
        print(f"Error creating portal session: {e}")
        return jsonify({"error": str(e)}), 500


@stripe_bp.route("/webhook", methods=["POST"])
def stripe_webhook():
    """
    Handle Stripe webhook events
    Configure this endpoint in Stripe Dashboard: https://dashboard.stripe.com/webhooks
    """
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    if not STRIPE_WEBHOOK_SECRET:
        print("⚠️ STRIPE_WEBHOOK_SECRET not configured")
        return jsonify({"error": "Webhook secret not configured"}), 500

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError:
        # Invalid payload
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return jsonify({"error": "Invalid signature"}), 400

    # Handle event
    event_type = event["type"]

    if event_type == "checkout.session.completed":
        # Payment successful, subscription created
        session = event["data"]["object"]
        StripeSubscriptionService.handle_checkout_completed(session)

    elif event_type == "customer.subscription.updated":
        # Subscription updated (status change, renewal, etc.)
        subscription = event["data"]["object"]
        StripeSubscriptionService.handle_subscription_updated(subscription)

    elif event_type == "customer.subscription.deleted":
        # Subscription canceled
        subscription = event["data"]["object"]
        StripeSubscriptionService.handle_subscription_deleted(subscription)

    elif event_type == "invoice.payment_failed":
        # Payment failed
        invoice = event["data"]["object"]
        customer_id = invoice.get("customer")
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            user.stripe_subscription_status = "past_due"
            db.session.commit()
            print(f"⚠️ Payment failed for {user.email}")

    return jsonify({"status": "success"}), 200


@stripe_bp.route("/config", methods=["GET"])
def get_stripe_config():
    """Get Stripe publishable key for frontend"""
    return jsonify(
        {
            "publishableKey": STRIPE_PUBLISHABLE_KEY,
            "prices": {"pro": STRIPE_PRICE_PRO, "premium": STRIPE_PRICE_PREMIUM},
        }
    )
