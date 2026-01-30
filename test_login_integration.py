"""
Test Login Flow - Full Integration Test
"""
import os
from app import app
from models_auth import db

def test_login_integration():
    """Test the login page and authentication"""
    
    with app.test_client() as client:
        # Test 1: Login page loads
        print("Test 1: Login page loads...")
        response = client.get('/auth/login')
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert b'BarberX' in response.data, "Page should contain BarberX"
        assert b'loginForm' in response.data, "Page should contain login form"
        print("✓ Login page loads successfully")
        
        # Test 2: Test invalid login
        print("\nTest 2: Invalid credentials rejected...")
        response = client.post('/auth/login', data={
            'email': 'invalid@test.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        assert b'Invalid email or password' in response.data, "Should show error message"
        print("✓ Invalid credentials correctly rejected")
        
        # Test 3: Test valid login (test user)
        print("\nTest 3: Valid credentials accepted (test user)...")
        response = client.post('/auth/login', data={
            'email': 'test@barberx.info',
            'password': 'Password123!',
            'remember': 'true'
        }, follow_redirects=False)
        
        # Should redirect on successful login
        assert response.status_code in [302, 303], f"Should redirect, got {response.status_code}"
        assert response.location in ['/dashboard', 'http://localhost/dashboard'], \
            f"Should redirect to dashboard, got {response.location}"
        print("✓ Valid credentials accepted, redirects to dashboard")
        
        # Test 4: Test admin login
        print("\nTest 4: Admin login...")
        response = client.post('/auth/login', data={
            'email': 'admin@barberx.info',
            'password': 'Admin123!'
        }, follow_redirects=False)
        
        assert response.status_code in [302, 303], f"Should redirect, got {response.status_code}"
        print("✓ Admin login successful")
        
        # Test 5: Check JavaScript files exist
        print("\nTest 5: JavaScript files accessible...")
        js_files = [
            '/static/js/toast-notifications.js',
            '/static/js/loading-states.js',
            '/static/js/form-validation.js'
        ]
        
        for js_file in js_files:
            response = client.get(js_file)
            assert response.status_code == 200, f"{js_file} should be accessible, got {response.status_code}"
            print(f"  ✓ {js_file} accessible")
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)
        print("\nYou can now login with:")
        print("  Test User: test@barberx.info / Password123!")
        print("  Admin:     admin@barberx.info / Admin123!")

if __name__ == '__main__':
    try:
        test_login_integration()
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
