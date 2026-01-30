"""Verify old /login route removed, enhanced /auth/login working"""
from app import app

print("\n=== VERIFYING OLD ROUTE REMOVAL ===\n")

with app.test_client() as client:
    # Test 1: Old /login should return 404
    print("TEST 1: Old /login route (should be 404)")
    response = client.get('/login', follow_redirects=False)
    print(f"  Status: {response.status_code}")
    if response.status_code == 404:
        print("  [OK] OLD ROUTE REMOVED")
    else:
        print(f"  [FAIL] Expected 404, got {response.status_code}")
    
    # Test 2: Enhanced /auth/login should still work
    print("\nTEST 2: Enhanced /auth/login (should work)")
    response = client.get('/auth/login', follow_redirects=False)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print("  [OK] ENHANCED AUTH WORKING")
    else:
        print(f"  [FAIL] Expected 200, got {response.status_code}")
    
    # Test 3: Protected route redirect
    print("\nTEST 3: /dashboard redirect (unauthorized)")
    response = client.get('/dashboard', follow_redirects=False)
    print(f"  Status: {response.status_code}")
    print(f"  Location: {response.headers.get('Location', 'None')}")
    if response.status_code == 302 and '/auth/login' in response.headers.get('Location', ''):
        print("  [OK] REDIRECT TO ENHANCED AUTH")
    else:
        print("  [FAIL] Expected redirect to /auth/login")

print("\n=== PR #2 VERIFICATION COMPLETE ===")
