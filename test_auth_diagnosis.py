"""
Test script to diagnose auth routing issues
"""
from app import app, ENHANCED_AUTH_AVAILABLE
import os

os.environ["FLASK_ENV"] = "development"

with app.app_context():
    print(f"✓ ENHANCED_AUTH_AVAILABLE: {ENHANCED_AUTH_AVAILABLE}")
    print(f"✓ Login manager view: {app.login_manager.login_view}")
    
    print(f"\n=== Registered Blueprints ===")
    for bp_name, bp in app.blueprints.items():
        print(f"  {bp_name}: {bp.url_prefix}")
    
    print(f"\n=== Auth-Related Routes ===")
    for rule in app.url_map.iter_rules():
        if "login" in rule.rule or "dashboard" in rule.rule or "auth" in rule.rule:
            print(f"  {rule.rule:30} -> {rule.endpoint:30} {rule.methods}")
    
    print(f"\n=== Cookie Config ===")
    print(f"  SESSION_COOKIE_SECURE: {app.config.get('SESSION_COOKIE_SECURE', 'NOT SET')}")
    print(f"  SESSION_COOKIE_HTTPONLY: {app.config.get('SESSION_COOKIE_HTTPONLY', 'NOT SET')}")
    print(f"  SESSION_COOKIE_SAMESITE: {app.config.get('SESSION_COOKIE_SAMESITE', 'NOT SET')}")
    print(f"  PERMANENT_SESSION_LIFETIME: {app.config.get('PERMANENT_SESSION_LIFETIME')}")
