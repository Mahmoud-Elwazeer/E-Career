"""
Alerting Rules Configuration

Defines alerting rules for Prometheus monitoring.
"""

from typing import Dict, Any, List


ALERTING_RULES = {
    'groups': [
        {
            'name': 'usam_career_compass_alerts',
            'rules': [
                # ============================================================================
                # High Priority Alerts
                # ============================================================================
                
                {
                    'alert': 'HighErrorRate',
                    'expr': 'sum(rate(http_requests_errors_total[5m])) / sum(rate(http_requests_total[5m])) > 0.05',
                    'for': '5m',
                    'labels': {
                        'severity': 'critical',
                    },
                    'annotations': {
                        'summary': 'High error rate detected',
                        'description': 'Error rate is above 5% over the last 5 minutes',
                    },
                },
                {
                    'alert': 'HighLatency',
                    'expr': 'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 2',
                    'for': '10m',
                    'labels': {
                        'severity': 'critical',
                    },
                    'annotations': {
                        'summary': 'High latency detected',
                        'description': '95th percentile latency is above 2 seconds',
                    },
                },
                {
                    'alert': 'DatabaseConnectionPoolExhausted',
                    'expr': 'database_connections_in_use / database_connections_max > 0.9',
                    'for': '5m',
                    'labels': {
                        'severity': 'critical',
                    },
                    'annotations': {
                        'summary': 'Database connection pool nearly exhausted',
                        'description': 'Database connection pool is above 90% utilization',
                    },
                },
                
                # ============================================================================
                # Medium Priority Alerts
                # ============================================================================
                
                {
                    'alert': 'HighCacheMissRate',
                    'expr': 'cache_misses_total / (cache_hits_total + cache_misses_total) > 0.3',
                    'for': '15m',
                    'labels': {
                        'severity': 'warning',
                    },
                    'annotations': {
                        'summary': 'High cache miss rate',
                        'description': 'Cache miss rate is above 30%',
                    },
                },
                {
                    'alert': 'HighAIRequestCost',
                    'expr': 'ai_tokens_total > 1000000',  # 1M tokens per day
                    'for': '1h',
                    'labels': {
                        'severity': 'warning',
                    },
                    'annotations': {
                        'summary': 'High AI request cost',
                        'description': 'AI token usage is above 1M tokens per day',
                    },
                },
                {
                    'alert': 'HighDatabaseQueryCount',
                    'expr': 'rate(database_queries_total[5m]) > 100',
                    'for': '10m',
                    'labels': {
                        'severity': 'warning',
                    },
                    'annotations': {
                        'summary': 'High database query count',
                        'description': 'Database query rate is above 100 queries per second',
                    },
                },
                {
                    'alert': 'HighMemoryUsage',
                    'expr': 'process_resident_memory_bytes / process_virtual_memory_bytes > 0.8',
                    'for': '10m',
                    'labels': {
                        'severity': 'warning',
                    },
                    'annotations': {
                        'summary': 'High memory usage',
                        'description': 'Memory usage is above 80%',
                    },
                },
                
                # ============================================================================
                # Low Priority Alerts
                # ============================================================================
                
                {
                    'alert': 'SlowDatabaseQueries',
                    'expr': 'rate(database_query_duration_seconds_sum[5m]) / rate(database_query_duration_seconds_count[5m]) > 0.5',
                    'for': '15m',
                    'labels': {
                        'severity': 'info',
                    },
                    'annotations': {
                        'summary': 'Slow database queries detected',
                        'description': 'Average database query time is above 500ms',
                    },
                },
                {
                    'alert': 'HighRequestRate',
                    'expr': 'rate(http_requests_total[5m]) > 1000',
                    'for': '10m',
                    'labels': {
                        'severity': 'info',
                    },
                    'annotations': {
                        'summary': 'High request rate',
                        'description': 'Request rate is above 1000 requests per second',
                    },
                },
                {
                    'alert': 'HighCacheSize',
                    'expr': 'cache_keys_total > 100000',
                    'for': '1h',
                    'labels': {
                        'severity': 'info',
                    },
                    'annotations': {
                        'summary': 'High cache size',
                        'description': 'Cache has more than 100,000 keys',
                    },
                },
                
                # ============================================================================
                # Business Logic Alerts
                # ============================================================================
                
                {
                    'alert': 'HighJobScrapeFailureRate',
                    'expr': 'rate(job_scrape_failures_total[5m]) / rate(job_scrape_attempts_total[5m]) > 0.1',
                    'for': '15m',
                    'labels': {
                        'severity': 'warning',
                    },
                    'annotations': {
                        'summary': 'High job scrape failure rate',
                        'description': 'Job scrape failure rate is above 10%',
                    },
                },
                {
                    'alert': 'LowJobCount',
                    'expr': 'job_count_total < 1000',
                    'for': '1h',
                    'labels': {
                        'severity': 'warning',
                    },
                    'annotations': {
                        'summary': 'Low job count',
                        'description': 'Total job count is below 1000',
                    },
                },
                {
                    'alert': 'HighUserChurn',
                    'expr': 'rate(user_churn_total[7d]) > 0.05',
                    'for': '7d',
                    'labels': {
                        'severity': 'warning',
                    },
                    'annotations': {
                        'summary': 'High user churn rate',
                        'description': 'Weekly user churn rate is above 5%',
                    },
                },
                
                # ============================================================================
                # Infrastructure Alerts
                # ============================================================================
                
                {
                    'alert': 'ServiceDown',
                    'expr': 'up == 0',
                    'for': '1m',
                    'labels': {
                        'severity': 'critical',
                    },
                    'annotations': {
                        'summary': 'Service is down',
                        'description': 'The service is not responding',
                    },
                },
                {
                    'alert': 'DiskSpaceLow',
                    'expr': 'node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.1',
                    'for': '5m',
                    'labels': {
                        'severity': 'critical',
                    },
                    'annotations': {
                        'summary': 'Low disk space',
                        'description': 'Disk space is below 10%',
                    },
                },
                {
                    'alert': 'HighCPUUsage',
                    'expr': 'rate(process_cpu_seconds_total[5m]) > 0.8',
                    'for': '10m',
                    'labels': {
                        'severity': 'warning',
                    },
                    'annotations': {
                        'summary': 'High CPU usage',
                        'description': 'CPU usage is above 80%',
                    },
                },
            ],
        },
    ],
}


def get_alerting_rules() -> Dict[str, Any]:
    """
    Get alerting rules configuration.
    
    Returns:
        Dictionary with alerting rules
    """
    return ALERTING_RULES


def get_alert_summary() -> Dict[str, Any]:
    """
    Get a summary of alerting rules.
    
    Returns:
        Dictionary with alert summary
    """
    critical_count = 0
    warning_count = 0
    info_count = 0
    
    for group in ALERTING_RULES['groups']:
        for rule in group['rules']:
            severity = rule['labels'].get('severity', 'info')
            if severity == 'critical':
                critical_count += 1
            elif severity == 'warning':
                warning_count += 1
            else:
                info_count += 1
    
    return {
        'total_rules': sum(len(g['rules']) for g in ALERTING_RULES['groups']),
        'by_severity': {
            'critical': critical_count,
            'warning': warning_count,
            'info': info_count,
        },
        'groups': len(ALERTING_RULES['groups']),
    }