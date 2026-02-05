#!/usr/bin/env python3
"""
Data Limits Enforcement Audit Script
Checks whether tier limits are properly enforced to prevent overages
"""

import os
import re
from typing import Dict, List, Tuple


def check_models_auth():
    """Check if UsageTracking model exists and is properly configured"""
    
    with open("models_auth.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        "UsageTracking model exists": "class UsageTracking" in content,
        "Tier limits defined": "def get_tier_limits" in content,
        "Overage fees defined": "overage_fee_per_video" in content,
        "Hard caps for FREE": "overage_allowed": False" in content,
        "Soft caps for PREMIUM": '"overage_allowed": True' in content,
    }
    
    return checks

def check_tier_gating():
    """Check if tier gating middleware exists and is complete"""
    
    if not os.path.exists("tier_gating.py"):
        return {"Tier gating module exists": False}
    
    with open("tier_gating.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        "Tier gating module exists": True,
        "require_tier decorator": "def require_tier" in content,
        "check_usage_limit decorator": "def check_usage_limit" in content,
        "require_feature decorator": "def require_feature" in content,
        "Usage field mapping": "usage_field_map" in content,
        "Limit enforcement logic": "if current_usage + increment > limit:" in content,
        "Upgrade prompts": "upgrade_required" in content,
    }
    
    return checks

def check_app_integration():
    """Check if decorators are applied in app.py"""
    
    if not os.path.exists("app.py"):
        return {"app.py exists": False}
    
    with open("app.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count decorator usage
    tier_usage_count = len(re.findall(r'@require_tier', content))
    limit_usage_count = len(re.findall(r'@check_usage_limit', content))
    feature_usage_count = len(re.findall(r'@require_feature', content))
    
    checks = {
        "app.py exists": True,
        "require_tier used": tier_usage_count > 0,
        "check_usage_limit used": limit_usage_count > 0,
        "require_feature used": feature_usage_count > 0,
        "tier_gating imported": "from tier_gating import" in content or "import tier_gating" in content,
    }
    
    return checks

def check_critical_routes():
    """Check if critical upload routes have limit enforcement"""
    
    if not os.path.exists("app.py"):
        return {}
    
    with open("app.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    critical_routes = {
        "video upload": r'@app\.route.*upload.*video|@app\.route.*/api/upload/video',
        "pdf upload": r'@app\.route.*upload.*pdf|@app\.route.*/api/upload/pdf',
        "transcription": r'@app\.route.*/api/transcribe',
        "ai analysis": r'@app\.route.*/api/analyze',
    }
    
    protected_routes = {}
    
    for route_name, pattern in critical_routes.items():
        route_matches = re.finditer(pattern, content, re.IGNORECASE)
        
        for match in route_matches:
            # Check if decorator exists within 5 lines before route
            start = max(0, match.start() - 500)
            snippet = content[start:match.end()]
            
            has_limit_check = '@check_usage_limit' in snippet
            has_tier_check = '@require_tier' in snippet
            
            protected_routes[f"{route_name} protected"] = has_limit_check or has_tier_check
    
    return protected_routes

def check_database_schema():
    """Check if database has usage tracking tables"""
    
    # Check for migration files
    migration_files = [
        "migrate_add_stripe_subscriptions.py",
        "migrate_add_free_tier_uploads.py",
        "migrate_add_tier.py",
        "migrate_add_storage.py",
    ]
    
    checks = {}
    for file in migration_files:
        checks[f"Migration: {file}"] = os.path.exists(file)
    
    # Check if UsageTracking table is created
    if os.path.exists("models_auth.py"):
        with open("models_auth.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks["UsageTracking table defined"] = "class UsageTracking" in content
        checks["Usage counters defined"] = "pdf_documents_processed" in content
        checks["Monthly reset logic"] = "billing_period_start" in content
    
    return checks

def identify_vulnerabilities():
    """Identify potential limit bypass vulnerabilities"""
    
    vulnerabilities = []
    
    # Check 1: Are there any upload routes without decorators?
    if os.path.exists("app.py"):
        with open("app.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all route definitions
        routes = re.findall(r'@app\.route\([\'"]([^\'"]+)[\'"]\).*?def\s+(\w+)', content, re.DOTALL)
        
        for path, func_name in routes:
            if any(keyword in path.lower() or keyword in func_name.lower() 
                   for keyword in ['upload', 'process', 'analyze', 'transcribe', 'create']):
                # This is a critical route - check for protection
                
                # Find the function definition
                func_pattern = rf'@app\.route.*?{re.escape(func_name)}.*?(?=@app\.route|def\s+\w+|$)'
                func_match = re.search(func_pattern, content, re.DOTALL)
                
                if func_match:
                    func_code = func_match.group(0)
                    
                    has_protection = (
                        '@check_usage_limit' in func_code or
                        '@require_tier' in func_code or
                        '@require_feature' in func_code
                    )
                    
                    if not has_protection:
                        vulnerabilities.append({
                            "type": "Unprotected Route",
                            "route": path,
                            "function": func_name,
                            "severity": "HIGH",
                            "description": "Critical route missing limit enforcement"
                        })
    
    # Check 2: Are soft caps properly configured?
    if os.path.exists("models_auth.py"):
        with open("models_auth.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # PREMIUM and ENTERPRISE should have overage_allowed: True
        if '"overage_allowed": False' in content:
            # Count how many tiers have overage_allowed: False
            false_count = content.count('"overage_allowed": False')
            if false_count != 3:  # Should be exactly 3 (FREE, STARTER, PROFESSIONAL)
                vulnerabilities.append({
                    "type": "Configuration Error",
                    "severity": "MEDIUM",
                    "description": f"Expected 3 tiers with hard caps, found {false_count}"
                })
    
    # Check 3: Is overage billing implemented?
    if os.path.exists("tier_gating.py"):
        with open("tier_gating.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "overage_allowed" not in content:
            vulnerabilities.append({
                "type": "Missing Feature",
                "severity": "HIGH",
                "description": "Overage billing logic not implemented in tier_gating.py"
            })
    
    return vulnerabilities

def check_overage_implementation():
    """Check if overage billing is properly implemented"""
    
    checks = {}
    
    if os.path.exists("tier_gating.py"):
        with open("tier_gating.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks["Overage allowed check"] = "overage_allowed" in content
        checks["Overage fee calculation"] = "overage_fee_per" in content
        checks["Soft cap handling"] = "if current_usage + increment > limit:" in content
    else:
        checks["tier_gating.py exists"] = False
    
    return checks

def main():
    print("="*80)
    print("DATA LIMITS ENFORCEMENT AUDIT")
    print("="*80)
    print()
    
    # Check 1: Models
    print("📋 STEP 1: Checking models_auth.py...")
    model_checks = check_models_auth()
    for check, passed in model_checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
    print()
    
    # Check 2: Tier Gating
    print("🔒 STEP 2: Checking tier_gating.py...")
    gating_checks = check_tier_gating()
    for check, passed in gating_checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
    print()
    
    # Check 3: App Integration
    print("🔗 STEP 3: Checking app.py integration...")
    app_checks = check_app_integration()
    for check, passed in app_checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
    print()
    
    # Check 4: Critical Routes
    print("🛡️  STEP 4: Checking critical route protection...")
    route_checks = check_critical_routes()
    if route_checks:
        for check, passed in route_checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check}")
    else:
        print("  ⚠️  No critical routes found or app.py missing")
    print()
    
    # Check 5: Database Schema
    print("💾 STEP 5: Checking database schema...")
    db_checks = check_database_schema()
    for check, passed in db_checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
    print()
    
    # Check 6: Overage Implementation
    print("💰 STEP 6: Checking overage billing...")
    overage_checks = check_overage_implementation()
    for check, passed in overage_checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
    print()
    
    # Check 7: Vulnerabilities
    print("🚨 STEP 7: Identifying vulnerabilities...")
    vulns = identify_vulnerabilities()
    if vulns:
        for vuln in vulns:
            severity_icon = "🔴" if vuln['severity'] == 'HIGH' else "🟡"
            print(f"  {severity_icon} {vuln['type']}: {vuln.get('description', '')}")
            if 'route' in vuln:
                print(f"      Route: {vuln['route']}")
                print(f"      Function: {vuln['function']}")
    else:
        print("  ✅ No vulnerabilities detected")
    print()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    
    all_checks = {**model_checks, **gating_checks, **app_checks, **db_checks, **overage_checks}
    passed = sum(1 for v in all_checks.values() if v)
    total = len(all_checks)
    
    print(f"\n✅ Checks Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"🚨 Vulnerabilities: {len(vulns)}")
    
    # Critical Issues
    critical_issues = []
    
    if not model_checks.get("Tier limits defined"):
        critical_issues.append("❌ CRITICAL: Tier limits not defined")
    
    if not gating_checks.get("check_usage_limit decorator"):
        critical_issues.append("❌ CRITICAL: Usage limit enforcement missing")
    
    if not app_checks.get("check_usage_limit used"):
        critical_issues.append("❌ CRITICAL: Limits not enforced in app.py")
    
    if critical_issues:
        print("\n🔴 CRITICAL ISSUES:")
        for issue in critical_issues:
            print(f"  {issue}")
        print("\n⚠️  DATA LIMITS ARE NOT PROPERLY ENFORCED!")
        print("   Users can bypass limits and cause unlimited overages.")
    else:
        print("\n✅ DATA LIMITS APPEAR TO BE PROPERLY CONFIGURED")
        print("   However, implementation verification required:")
        print("   1. Test upload exceeding limits")
        print("   2. Verify hard caps block users (FREE/STARTER/PROFESSIONAL)")
        print("   3. Verify soft caps allow overage with fees (PREMIUM/ENTERPRISE)")
    
    print()

if __name__ == '__main__':
    main()
