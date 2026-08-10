"""
Database Optimization Utilities - Phase E Performance

Utilities for query optimization, index recommendations, and N+1 detection.
"""
from django.db import connection
from django.db.models import Prefetch
import logging
import time
from contextlib import contextmanager
from typing import List, Dict

logger = logging.getLogger(__name__)


@contextmanager
def query_debugger(name: str = "Query Block"):
    """
    Context manager to log SQL queries and execution time.

    Usage:
        with query_debugger("Featured Jobs"):
            jobs = Job.objects.filter(is_featured=True)[:10]
    """
    queries_before = len(connection.queries)
    start_time = time.time()

    yield

    queries_after = len(connection.queries)
    end_time = time.time()

    num_queries = queries_after - queries_before
    duration = (end_time - start_time) * 1000  # ms

    logger.info(
        f"[{name}] Queries: {num_queries} | Time: {duration:.2f}ms"
    )

    if num_queries > 10:
        logger.warning(f"[{name}] High query count detected: {num_queries} queries")

    # Log slow queries
    if duration > 1000:  # > 1 second
        logger.warning(f"[{name}] Slow query block: {duration:.2f}ms")


def analyze_queries(threshold_ms: int = 10) -> List[Dict]:
    """
    Analyze recent queries and return slow ones.

    Args:
        threshold_ms: Threshold in milliseconds

    Returns:
        List of slow queries with timing info
    """
    slow_queries = []

    for query in connection.queries:
        time_ms = float(query['time']) * 1000  # Convert to ms

        if time_ms > threshold_ms:
            slow_queries.append({
                'sql': query['sql'][:200],  # Truncate long SQL
                'time_ms': round(time_ms, 2),
            })

    return slow_queries


def get_missing_indexes() -> List[str]:
    """
    Analyze query patterns and suggest missing indexes.

    Returns:
        List of index recommendations
    """
    recommendations = []

    # Common patterns to check
    checks = [
        ("Job", "status", "Jobs often filtered by status"),
        ("Job", "posted_at", "Jobs sorted by posted date"),
        ("Job", "company_id, status", "Composite index for company jobs"),
        ("User", "email", "User lookup by email"),
        ("User", "role", "User filtering by role"),
        ("Application", "user_id, status", "Application filtering"),
        ("RashidMessage", "conversation_id, created_at", "Message pagination"),
    ]

    for model_name, fields, reason in checks:
        recommendations.append({
            'model': model_name,
            'fields': fields,
            'reason': reason,
            'command': f"# python manage.py makemigrations --empty {model_name.lower()}s\n"
                      f"# Then add: migrations.AddIndex('{model_name}', models.Index(fields=[{fields}]))"
        })

    return recommendations


def detect_n_plus_one(queryset, related_fields: List[str]) -> Dict:
    """
    Check if queryset will cause N+1 queries.

    Args:
        queryset: Django QuerySet to analyze
        related_fields: Expected related fields that should be prefetched

    Returns:
        Analysis result with recommendations
    """
    query_str = str(queryset.query).lower()

    missing_optimizations = []

    for field in related_fields:
        if field.lower() not in query_str:
            missing_optimizations.append(field)

    return {
        'has_issues': len(missing_optimizations) > 0,
        'missing_fields': missing_optimizations,
        'recommendations': [
            f"Add .select_related('{field}')" if '__' not in field
            else f"Add .prefetch_related('{field}')"
            for field in missing_optimizations
        ]
    }


# ============================================================================
# Optimized QuerySet Helpers
# ============================================================================


def optimize_job_queryset(queryset):
    """
    Apply common optimizations to Job querysets.

    Usage:
        jobs = optimize_job_queryset(Job.objects.filter(status='active'))
    """
    return queryset.select_related(
        'company',
        'company__industry',
    ).prefetch_related(
        'required_skills',
        'tags',
    )


def optimize_user_queryset(queryset):
    """Apply common optimizations to User querysets"""
    return queryset.select_related(
        'career_profile',
    ).prefetch_related(
        'career_profile__career_user_skills',
        'career_profile__career_user_skills__skill',
    )


def optimize_application_queryset(queryset):
    """Apply common optimizations to Application querysets"""
    return queryset.select_related(
        'user',
        'user__career_profile',
        'job',
        'job__company',
    )


def optimize_conversation_queryset(queryset):
    """Apply common optimizations to Conversation querysets"""
    return queryset.select_related(
        'user',
    ).prefetch_related(
        Prefetch(
            'messages',
            queryset=RashidMessage.objects.order_by('-created_at')[:50]
        )
    )


# ============================================================================
# Database Health Checks
# ============================================================================


def check_database_health() -> Dict:
    """
    Run database health checks.

    Returns:
        Health check results
    """
    from django.db import connection

    results = {
        'connection': 'OK',
        'pool_size': None,
        'active_connections': None,
        'table_count': None,
        'index_count': None,
    }

    try:
        # Test connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            results['connection'] = 'OK'

            # Get table count
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            results['table_count'] = cursor.fetchone()[0]

            # Get index count
            cursor.execute("""
                SELECT COUNT(*)
                FROM pg_indexes
                WHERE schemaname = 'public'
            """)
            results['index_count'] = cursor.fetchone()[0]

            # Get active connections
            cursor.execute("""
                SELECT COUNT(*)
                FROM pg_stat_activity
                WHERE datname = current_database()
            """)
            results['active_connections'] = cursor.fetchone()[0]

    except Exception as e:
        results['connection'] = f'ERROR: {str(e)}'
        logger.error(f"Database health check failed: {e}")

    return results


def get_table_sizes() -> List[Dict]:
    """
    Get size of all tables in database.

    Returns:
        List of tables with sizes
    """
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 20
        """)

        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_slow_queries(limit: int = 10) -> List[Dict]:
    """
    Get slowest queries from pg_stat_statements.

    Note: Requires pg_stat_statements extension enabled.

    Args:
        limit: Number of queries to return
    """
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT
                    query,
                    calls,
                    mean_exec_time,
                    max_exec_time,
                    total_exec_time
                FROM pg_stat_statements
                WHERE query NOT LIKE '%pg_stat_statements%'
                ORDER BY mean_exec_time DESC
                LIMIT {limit}
            """)

            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.warning(f"pg_stat_statements not available: {e}")
        return []


# ============================================================================
# Management Command Helper
# ============================================================================


def print_optimization_report():
    """
    Print comprehensive optimization report.

    Usage in management command:
        from apps.core.db_optimization import print_optimization_report
        print_optimization_report()
    """
    print("\n" + "="*60)
    print("DATABASE OPTIMIZATION REPORT")
    print("="*60 + "\n")

    # Health check
    print("📊 Database Health:")
    health = check_database_health()
    for key, value in health.items():
        print(f"  - {key}: {value}")

    # Table sizes
    print("\n💾 Largest Tables:")
    tables = get_table_sizes()
    for table in tables[:10]:
        print(f"  - {table['tablename']}: {table['size']}")

    # Missing indexes
    print("\n🔍 Index Recommendations:")
    recommendations = get_missing_indexes()
    for rec in recommendations[:5]:
        print(f"  - {rec['model']}.{rec['fields']}")
        print(f"    Reason: {rec['reason']}")

    # Slow queries
    print("\n🐌 Slow Queries:")
    slow = get_slow_queries(5)
    if slow:
        for q in slow:
            print(f"  - Avg: {q['mean_exec_time']:.2f}ms | Calls: {q['calls']}")
            print(f"    {q['query'][:100]}...")
    else:
        print("  No slow query data available (enable pg_stat_statements)")

    print("\n" + "="*60 + "\n")
