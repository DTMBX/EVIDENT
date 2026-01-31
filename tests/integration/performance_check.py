"""
Performance Monitoring & Optimization Script
Run this to check and optimize database performance
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text

from app import app, db
from config_manager import DatabaseOptimizer


def check_database_performance():
    """Check database performance metrics"""
    print("=" * 60)
    print("DATABASE PERFORMANCE CHECK")
    print("=" * 60)

    with app.app_context():
        # 1. Check table sizes
        print("\n1. Table Sizes:")
        try:
            if "postgresql" in str(db.engine.url):
                # PostgreSQL
                result = db.session.execute(
                    text(
                        """
                    SELECT 
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """
                    )
                )
                for row in result:
                    print(f"   {row[0]:<30} {row[1]}")
            elif "sqlite" in str(db.engine.url):
                # SQLite
                result = db.session.execute(
                    text(
                        """
                    SELECT name FROM sqlite_master WHERE type='table'
                """
                    )
                )
                tables = [row[0] for row in result]
                for table in tables:
                    count = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    print(f"   {table:<30} {count} rows")
        except Exception as e:
            print(f"   Error: {e}")

        # 2. Check indexes
        print("\n2. Database Indexes:")
        try:
            if "postgresql" in str(db.engine.url):
                result = db.session.execute(
                    text(
                        """
                    SELECT tablename, indexname, indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                    ORDER BY tablename, indexname
                """
                    )
                )
                for row in result:
                    print(f"   {row[0]}.{row[1]}")
            elif "sqlite" in str(db.engine.url):
                result = db.session.execute(
                    text(
                        """
                    SELECT name, tbl_name FROM sqlite_master WHERE type='index'
                """
                    )
                )
                for row in result:
                    print(f"   {row[1]}.{row[0]}")
        except Exception as e:
            print(f"   Error: {e}")

        # 3. Check for missing indexes
        print("\n3. Checking for Missing Indexes:")
        optimizer = DatabaseOptimizer(db)

        # Expected indexes
        expected_indexes = [
            ("users", "idx_users_tier"),
            ("users", "idx_users_created_at"),
            ("users", "idx_users_last_login"),
            ("users", "idx_users_is_active"),
            ("analyses", "idx_analyses_user_id"),
            ("analyses", "idx_analyses_status"),
            ("usage_tracking", "idx_usage_user_year_month"),
        ]

        print("   Creating missing indexes...")
        optimizer.create_indexes()
        print("   ✓ Index check complete")

        # 4. Query performance test
        print("\n4. Query Performance Test:")

        # Test common queries
        queries = [
            ("Count users", "SELECT COUNT(*) FROM users"),
            ("Count analyses", "SELECT COUNT(*) FROM analyses"),
            ("Recent analyses", "SELECT * FROM analyses ORDER BY created_at DESC LIMIT 10"),
        ]

        for query_name, query in queries:
            start = time.time()
            try:
                result = db.session.execute(text(query))
                result.fetchall()
                elapsed = (time.time() - start) * 1000
                status = "✓" if elapsed < 100 else "⚠" if elapsed < 500 else "✗"
                print(f"   {status} {query_name:<30} {elapsed:>8.2f}ms")
            except Exception as e:
                print(f"   ✗ {query_name:<30} ERROR: {e}")

        # 5. Connection pool stats (PostgreSQL)
        print("\n5. Connection Pool Status:")
        try:
            pool = db.engine.pool
            if hasattr(pool, "size"):
                print(f"   Pool size: {pool.size()}")
                print(f"   Checked out: {pool.checkedout()}")
                print(f"   Overflow: {pool.overflow()}")
            else:
                print("   N/A (SQLite or pool not configured)")
        except Exception as e:
            print(f"   Error: {e}")


def optimize_database():
    """Run database optimizations"""
    print("\n" + "=" * 60)
    print("DATABASE OPTIMIZATION")
    print("=" * 60)

    with app.app_context():
        optimizer = DatabaseOptimizer(db)

        # 1. Create indexes
        print("\n1. Creating/Updating Indexes...")
        optimizer.create_indexes()
        print("   ✓ Indexes created")

        # 2. Analyze tables
        print("\n2. Analyzing Tables...")
        try:
            optimizer.analyze_tables()
            print("   ✓ Tables analyzed")
        except Exception as e:
            print(f"   ⚠ Analysis not supported: {e}")

        # 3. Vacuum (if supported)
        print("\n3. Vacuuming Database...")
        try:
            optimizer.vacuum_database()
            print("   ✓ Database vacuumed")
        except Exception as e:
            print(f"   ⚠ Vacuum not supported: {e}")


def check_slow_queries():
    """Check for slow queries in logs"""
    print("\n" + "=" * 60)
    print("SLOW QUERY CHECK")
    print("=" * 60)

    log_file = Path("logs/barberx.log")
    if not log_file.exists():
        print("   No log file found")
        return

    print("\n   Searching for slow queries (>1s)...")
    slow_queries = []

    with open(log_file, "r") as f:
        for line in f:
            if "Slow query" in line:
                slow_queries.append(line.strip())

    if slow_queries:
        print(f"   Found {len(slow_queries)} slow queries:")
        for query in slow_queries[-10:]:  # Show last 10
            print(f"   {query}")
    else:
        print("   ✓ No slow queries found")


def generate_performance_report():
    """Generate comprehensive performance report"""
    print("\n" + "=" * 60)
    print("PERFORMANCE REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    check_database_performance()
    check_slow_queries()

    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    print(
        """
    1. ✓ Ensure all indexes are created (run optimize_database())
    2. ✓ Enable connection pooling for PostgreSQL (configured in config_manager.py)
    3. ✓ Use pagination for large result sets (added to admin routes)
    4. ✓ Enable gzip compression (Flask-Compress added)
    5. ✓ Use streaming for large file uploads (implemented)
    6. ✓ Add caching for expensive queries (performance_optimizations.py)
    
    Next Steps:
    - Monitor slow queries in production
    - Set up Redis for distributed caching (optional)
    - Consider CDN for static assets
    - Monitor memory usage with profiling tools
    """
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database Performance Tools")
    parser.add_argument("action", choices=["check", "optimize", "report"], help="Action to perform")

    args = parser.parse_args()

    if args.action == "check":
        check_database_performance()
    elif args.action == "optimize":
        optimize_database()
    elif args.action == "report":
        generate_performance_report()
