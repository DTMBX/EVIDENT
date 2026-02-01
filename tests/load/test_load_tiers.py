"""
Professional-grade load testing script using Python locust.
Tests concurrent user scenarios and tier-specific load patterns.
"""

import json
import random

from locust import HttpUser, between, tag, task


class BarberXUser(HttpUser):
    """Base user for load testing BarberX platform."""

    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    def on_start(self):
        """Initialize user session."""
        self.tier = "FREE"
        self.auth_token = None


class FreeTrierUser(BarberXUser):
    """FREE tier user - demo cases only."""

    weight = 40  # 40% of users are FREE tier

    @task(5)
    @tag("public", "free")
    def browse_homepage(self):
        """Browse public homepage."""
        self.client.get("/")

    @task(10)
    @tag("demo", "free")
    def view_demo_cases(self):
        """View demo cases."""
        self.client.get("/demo-cases")

    @task(8)
    @tag("education", "free")
    def browse_educational_resources(self):
        """Browse educational content."""
        self.client.get("/education-center")

    @task(3)
    @tag("pricing", "free")
    def view_pricing(self):
        """View pricing page (considering upgrade)."""
        self.client.get("/pricing")

    @task(2)
    @tag("upload", "free")
    def attempt_one_time_upload(self):
        """Attempt one-time upload."""
        # Simulates file upload form submission
        self.client.post("/api/upload/free", json={"file_type": "pdf", "size_mb": 5})


class StarterTierUser(BarberXUser):
    """STARTER tier user - basic features with hard cap."""

    weight = 30  # 30% of users are STARTER tier

    def on_start(self):
        """Login as STARTER user."""
        super().on_start()
        self.tier = "STARTER"
        # Simulate login
        response = self.client.post(
            "/auth/login",
            json={"email": f"starter_{random.randint(1, 100)}@test.com", "password": "testpass123"},
        )

    @task(8)
    @tag("upload", "starter")
    def upload_video(self):
        """Upload BWC video."""
        self.client.post("/api/upload/video", json={"file_size_mb": 256, "duration_minutes": 15})

    @task(6)
    @tag("upload", "starter")
    def upload_pdf(self):
        """Upload PDF document."""
        self.client.post("/api/upload/pdf", json={"file_size_mb": 5, "pages": 25})

    @task(10)
    @tag("analysis", "starter")
    def view_analysis_results(self):
        """View analysis results."""
        case_id = random.randint(1, 100)
        self.client.get(f"/cases/{case_id}/analysis")

    @task(5)
    @tag("export", "starter")
    def export_report(self):
        """Export court-ready report."""
        case_id = random.randint(1, 100)
        self.client.post(f"/api/export/report", json={"case_id": case_id, "format": "pdf"})

    @task(3)
    @tag("dashboard", "starter")
    def check_usage_dashboard(self):
        """Check usage limits in dashboard."""
        self.client.get("/dashboard/usage")


class ProfessionalTierUser(BarberXUser):
    """PROFESSIONAL tier user - flexible growth with soft cap."""

    weight = 20  # 20% of users are PROFESSIONAL tier

    def on_start(self):
        """Login as PROFESSIONAL user."""
        super().on_start()
        self.tier = "PROFESSIONAL"
        response = self.client.post(
            "/auth/login",
            json={"email": f"pro_{random.randint(1, 50)}@test.com", "password": "testpass123"},
        )

    @task(12)
    @tag("upload", "professional")
    def batch_upload_videos(self):
        """Batch upload multiple videos."""
        self.client.post(
            "/api/upload/batch",
            json={
                "files": [
                    {"type": "video", "size_mb": 512, "duration_minutes": 45},
                    {"type": "video", "size_mb": 768, "duration_minutes": 60},
                ]
            },
        )

    @task(10)
    @tag("analysis", "professional")
    def run_advanced_analysis(self):
        """Run advanced forensic analysis."""
        case_id = random.randint(1, 200)
        self.client.post(
            f"/api/analysis/forensic", json={"case_id": case_id, "analysis_type": "voice_stress"}
        )

    @task(6)
    @tag("export", "professional")
    def generate_timeline(self):
        """Generate timeline visualization."""
        case_id = random.randint(1, 200)
        self.client.post(f"/api/timeline/generate", json={"case_id": case_id})

    @task(8)
    @tag("search", "professional")
    def legal_research_query(self):
        """Perform legal research."""
        query = random.choice(
            [
                "Fourth Amendment",
                "Miranda Rights",
                "Qualified Immunity",
                "Brady Violation",
                "Excessive Force",
            ]
        )
        self.client.post(
            "/api/legal-library/search", json={"query": query, "jurisdiction": "federal"}
        )

    @task(4)
    @tag("overage", "professional")
    def check_overage_billing(self):
        """Check overage costs."""
        self.client.get("/api/billing/overage-summary")


class PremiumTierUser(BarberXUser):
    """PREMIUM tier user - power user with API access."""

    weight = 8  # 8% of users are PREMIUM tier

    def on_start(self):
        """Login as PREMIUM user with API key."""
        super().on_start()
        self.tier = "PREMIUM"
        self.api_key = f"pk_test_{random.randint(10000, 99999)}"

    @task(15)
    @tag("api", "premium")
    def api_batch_process(self):
        """API: Batch process multiple cases."""
        self.client.post(
            "/api/v1/batch/process",
            headers={"X-API-Key": self.api_key},
            json={"cases": [{"id": random.randint(1, 500)} for _ in range(5)]},
        )

    @task(10)
    @tag("api", "premium")
    def api_forensic_analysis(self):
        """API: Run forensic analysis."""
        self.client.post(
            "/api/v1/forensic/analyze",
            headers={"X-API-Key": self.api_key},
            json={
                "case_id": random.randint(1, 500),
                "features": ["voice_stress", "emotion", "timeline"],
            },
        )

    @task(12)
    @tag("analysis", "premium")
    def multi_video_sync(self):
        """Sync multiple BWC videos."""
        self.client.post(
            "/api/multi-bwc/sync", json={"video_ids": [random.randint(1, 1000) for _ in range(3)]}
        )

    @task(5)
    @tag("export", "premium")
    def export_advanced_report(self):
        """Export advanced court-ready report."""
        self.client.post(
            "/api/export/advanced",
            json={"case_id": random.randint(1, 500), "format": "docx", "include_forensics": True},
        )


class EnterpriseTierUser(BarberXUser):
    """ENTERPRISE tier user - unlimited usage."""

    weight = 2  # 2% of users are ENTERPRISE tier

    def on_start(self):
        """Login as ENTERPRISE user."""
        super().on_start()
        self.tier = "ENTERPRISE"
        self.api_key = f"pk_live_{random.randint(10000, 99999)}"

    @task(20)
    @tag("api", "enterprise", "unlimited")
    def api_bulk_upload(self):
        """API: Bulk upload unlimited files."""
        self.client.post(
            "/api/v1/bulk/upload",
            headers={"X-API-Key": self.api_key},
            json={
                "files": [{"type": "video", "size_gb": random.uniform(1, 10)} for _ in range(20)]
            },
        )

    @task(15)
    @tag("api", "enterprise", "white-label")
    def generate_white_label_report(self):
        """Generate white-label branded report."""
        self.client.post(
            "/api/v1/export/white-label",
            headers={"X-API-Key": self.api_key},
            json={
                "case_id": random.randint(1, 10000),
                "firm_branding": {
                    "logo_url": "https://example.com/logo.png",
                    "color_scheme": "#1e3a8a",
                },
            },
        )

    @task(10)
    @tag("api", "enterprise", "analytics")
    def api_analytics_dashboard(self):
        """API: Get analytics dashboard data."""
        self.client.get("/api/v1/analytics/dashboard", headers={"X-API-Key": self.api_key})


# Performance test scenarios
class PerformanceTestUser(HttpUser):
    """Dedicated performance testing user."""

    wait_time = between(0.5, 2)

    @task
    @tag("performance", "api")
    def rapid_api_calls(self):
        """Rapid API calls to test rate limiting."""
        for _ in range(10):
            self.client.get("/health")

    @task
    @tag("performance", "homepage")
    def stress_homepage(self):
        """Stress test homepage loading."""
        self.client.get("/", name="Stress: Homepage")

    @task
    @tag("performance", "search")
    def stress_search(self):
        """Stress test search functionality."""
        self.client.post("/api/legal-library/search", json={"query": "test query", "limit": 100})


if __name__ == "__main__":
    print(
        """
    BarberX Load Testing Script
    ============================
    
    User Distribution:
    - FREE tier: 40%
    - STARTER tier: 30%
    - PROFESSIONAL tier: 20%
    - PREMIUM tier: 8%
    - ENTERPRISE tier: 2%
    
    Run with locust:
    ----------------
    # Web UI mode (recommended):
    locust -f tests/load/test_load_tiers.py --host=http://localhost:5000
    
    # Headless mode:
    locust -f tests/load/test_load_tiers.py --host=http://localhost:5000 --users 100 --spawn-rate 10 --run-time 10m --headless
    
    # Specific tier testing:
    locust -f tests/load/test_load_tiers.py --host=http://localhost:5000 --tags api premium
    
    Scenarios:
    ----------
    1. Concurrent Users: 100 users (40 FREE, 30 STARTER, 20 PRO, 8 PREMIUM, 2 ENTERPRISE)
    2. API Load: 200 requests/second (PREMIUM + ENTERPRISE)
    3. Peak Load: 500 concurrent users
    4. Stress Test: Rapid fire requests to test rate limiting
    """
    )
