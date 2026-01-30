import os
os.environ['FLASK_ENV'] = 'development'
from app import app

print("=== COOKIE SECURITY VERIFICATION ===")
print(f"FLASK_ENV: {os.getenv('FLASK_ENV')}")
print(f"SESSION_COOKIE_SECURE: {app.config['SESSION_COOKIE_SECURE']} (dev should be False)")
print(f"SESSION_COOKIE_HTTPONLY: {app.config['SESSION_COOKIE_HTTPONLY']}")
print(f"SESSION_COOKIE_SAMESITE: {app.config['SESSION_COOKIE_SAMESITE']}")

if app.config['SESSION_COOKIE_SAMESITE'] == 'Lax':
    print("\n✅ FIX VERIFIED: SAMESITE=Lax prevents CSRF")
else:
    print(f"\n❌ FAILED: SAMESITE={app.config['SESSION_COOKIE_SAMESITE']}")
