"""
Test actual auth redirect flow to identify bugs
"""

from flask import session

from app import app

print("\n=== TESTING AUTH REDIRECT FLOW ===\n")

with app.test_client() as client:
    with app.app_context():
        # Test 1: Access protected /dashboard without login
        print("TEST 1: Access /dashboard (protected) without auth")
        response = client.get("/dashboard", follow_redirects=False)
        print(f"  Status: {response.status_code}")
        print(f"  Location: {response.headers.get('Location', 'None')}")
        print(f"  Expected: 302 redirect to /auth/login?next=/dashboard")

        # Test 2: Check old /login route behavior
        print("\nTEST 2: Access old /login route")
        response = client.get("/login", follow_redirects=False)
        print(f"  Status: {response.status_code}")
        print(f"  Location: {response.headers.get('Location', 'None')}")
        print(f"  Expected: 302 redirect to /auth/login")

        # Test 3: Check new /auth/login route
        print("\nTEST 3: Access new /auth/login route")
        response = client.get("/auth/login", follow_redirects=False)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✓ Renders login page")
        else:
            print(f"  Location: {response.headers.get('Location', 'None')}")

        # Test 4: Test open redirect protection
        print("\nTEST 4: Test open redirect protection")
        malicious_next = "http://evil.com/phishing"
        response = client.get(f"/auth/login?next={malicious_next}", follow_redirects=False)
        print(f"  Status: {response.status_code}")
        print(f"  Malicious next param: {malicious_next}")

        # Test 5: Test safe internal redirect
        print("\nTEST 5: Test safe internal redirect")
        safe_next = "/dashboard"
        response = client.post(
            "/auth/login",
            data={"email": "nonexistent@test.com", "password": "wrong"},
            follow_redirects=False,
        )
        print(f"  Login with bad credentials: {response.status_code}")

        print("\n=== SECURITY FINDINGS ===")
        # Check cookie flags
        print(f"SESSION_COOKIE_SECURE: {app.config.get('SESSION_COOKIE_SECURE')}")
        print(f"SESSION_COOKIE_HTTPONLY: {app.config.get('SESSION_COOKIE_HTTPONLY')}")
        print(f"SESSION_COOKIE_SAMESITE: {app.config.get('SESSION_COOKIE_SAMESITE')}")
