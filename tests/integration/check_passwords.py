"""
Check and set passwords for admin and test users
"""

import sys

sys.path.insert(0, ".")

from app import app
from models_auth import User, db


def check_and_set_passwords():
    """Check if users have passwords and set them if needed"""
    with app.app_context():
        print("\n" + "=" * 70)
        print("  CHECKING USER PASSWORDS")
        print("=" * 70 + "\n")

        # Check admin user
        admin_user = User.query.filter_by(email="dtb33@pm.me").first()
        if admin_user:
            print(f"[ADMIN] dtb33@pm.me")
            print(f"   Has password hash: {bool(admin_user.password_hash)}")

            if admin_user.password_hash:
                # Test with common password
                test_passwords = ["admin123", "password", "Admin123!", "barberx"]
                for pwd in test_passwords:
                    if admin_user.check_password(pwd):
                        print(f"   Current password: {pwd}")
                        break
                else:
                    print(f"   Password exists but not in common list")
                    print(f"   Setting new password: Admin123!")
                    admin_user.set_password("Admin123!")
                    db.session.commit()
            else:
                print(f"   No password set - creating one")
                print(f"   New password: Admin123!")
                admin_user.set_password("Admin123!")
                db.session.commit()
        else:
            print("[ERROR] Admin user not found")

        print()

        # Check test user
        test_user = User.query.filter_by(email="test@barberx.info").first()
        if test_user:
            print(f"[TEST] test@barberx.info")
            print(f"   Has password hash: {bool(test_user.password_hash)}")

            if test_user.password_hash:
                # Test with common password
                test_passwords = ["test123", "password", "Test123!", "barberx"]
                for pwd in test_passwords:
                    if test_user.check_password(pwd):
                        print(f"   Current password: {pwd}")
                        break
                else:
                    print(f"   Password exists but not in common list")
                    print(f"   Setting new password: Test123!")
                    test_user.set_password("Test123!")
                    db.session.commit()
            else:
                print(f"   No password set - creating one")
                print(f"   New password: Test123!")
                test_user.set_password("Test123!")
                db.session.commit()
        else:
            print("[ERROR] Test user not found")

        print("\n" + "=" * 70)
        print("  LOGIN CREDENTIALS")
        print("=" * 70 + "\n")

        # Verify passwords work
        admin_user = User.query.filter_by(email="dtb33@pm.me").first()
        test_user = User.query.filter_by(email="test@barberx.info").first()

        if admin_user:
            admin_works = admin_user.check_password("Admin123!")
            print(f"[ADMIN USER]")
            print(f"   Email: dtb33@pm.me")
            print(f"   Password: Admin123!")
            print(f"   Login working: {'YES' if admin_works else 'NO'}")
            print(f"   Tier: {admin_user.tier}")
            print(f"   Admin: {admin_user.is_admin}")
            print()

        if test_user:
            test_works = test_user.check_password("Test123!")
            print(f"[TEST USER]")
            print(f"   Email: test@barberx.info")
            print(f"   Password: Test123!")
            print(f"   Login working: {'YES' if test_works else 'NO'}")
            print(f"   Tier: {test_user.tier}")
            print(f"   Admin: {test_user.is_admin}")
            print()

        print("=" * 70)
        print("  [SUCCESS] PASSWORD CHECK COMPLETE")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    check_and_set_passwords()
