"""
Test login functionality
"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask
from models_auth import db, User, TierLevel
from auth_routes import init_auth

# Create test app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///barberx_FRESH.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'test-secret-key-12345'
app.config['TESTING'] = True

# Initialize database
db.init_app(app)

# Initialize authentication
init_auth(app)

def test_login():
    """Test login functionality"""
    with app.app_context():
        # Check if database tables exist
        try:
            user_count = User.query.count()
            print(f"✓ Database connected: {user_count} users found")
            
            # List all users
            users = User.query.all()
            if users:
                print("\nExisting users:")
                for user in users:
                    print(f"  - {user.email} (Tier: {user.tier.name}, Active: {user.is_active})")
            else:
                print("\n⚠ No users found. Creating test user...")
                
                # Create test user
                test_user = User(
                    email='test@barberx.info',
                    full_name='Test User',
                    tier=TierLevel.FREE,
                    is_active=True
                )
                test_user.set_password('Password123!')
                db.session.add(test_user)
                db.session.commit()
                print(f"✓ Test user created: test@barberx.info / Password123!")
                
            # Test password verification
            test_email = 'test@barberx.info'
            user = User.query.filter_by(email=test_email).first()
            
            if user:
                # Test correct password
                if user.check_password('Password123!'):
                    print(f"\n✓ Password verification works for {test_email}")
                else:
                    print(f"\n✗ Password verification failed for {test_email}")
                    
                # Test wrong password
                if not user.check_password('wrongpassword'):
                    print(f"✓ Wrong password correctly rejected")
            else:
                print(f"\n✗ User {test_email} not found")
                
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_login()
