# Copyright © 2024–2026 Faith Frontier Ecclesiastical Trust. All rights reserved.
# PROPRIETARY — See LICENSE.

"""
Evident Admin Account Setup - FIXED VERSION
Creates admin account using correct SQLAlchemy models
"""

import os
import sys

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models_auth import TierLevel, User, db

# SECURE ADMIN CREDENTIALS

# Securely load admin credentials from environment
ADMIN_EMAIL = os.environ.get("Evident_ADMIN_EMAIL", "admin@Evident.info")
ADMIN_PASSWORD = os.environ.get("Evident_ADMIN_PASSWORD")

if not ADMIN_PASSWORD:
    print("❌ ERROR: Evident_ADMIN_PASSWORD environment variable must be set")
    sys.exit(1)


def create_admin_fixed():
    """Create admin account using correct SQLAlchemy models"""

    print("\n" + "=" * 70)
    print("Evident Admin Account Setup (FIXED VERSION)")
    print("=" * 70 + "\n")

    with app.app_context():
        # Check if admin exists
        admin = User.query.filter_by(email=ADMIN_EMAIL).first()

        if admin:
            print(f"Admin account already exists: {admin.email}")
            # Update password and admin status
            admin.set_password(ADMIN_PASSWORD)
            admin.tier = TierLevel.ADMIN
            admin.is_admin = True
            admin.is_active = True
            admin.is_verified = True
            db.session.commit()
            print("Admin account updated.")
        else:
            print("Creating new admin account...")
            admin = User(
                email=ADMIN_EMAIL,
                full_name="Evident System Administrator",
                tier=TierLevel.ADMIN,
                is_admin=True,
                is_active=True,
                is_verified=True,
            )
            admin.set_password(ADMIN_PASSWORD)
            db.session.add(admin)
            db.session.commit()
            print("Admin account created.")

        # Only print non-sensitive status
        admin_count = User.query.filter_by(is_admin=True).count()
        if admin_count == 1:
            print("Security check: Exactly ONE admin exists.")
        else:
            print(f"WARNING: {admin_count} admins found (should be 1)")
        return True


if __name__ == "__main__":
    try:
        success = create_admin_fixed()
        if success:
            print("✅ Setup complete!")
            print("\n🌐 Login at: http://localhost:5000/auth/login")
            print("📧 Email: admin@Evident.info")
            sys.exit(0)
        else:
            print("❌ Setup failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
