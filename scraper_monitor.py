#!/usr/bin/env python3
"""
Scraper Monitoring and Alerting System
Real-time monitoring to prevent Pacific Dawn-type data loss

This system provides:
- Real-time success rate monitoring
- Automated alerts for data quality issues
- Performance tracking and trend analysis
- Integration with external monitoring systems
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import sqlite3
import os

logger = logging.getLogger(__name__)

@dataclass
class ScrapingMetric:
    """Individual scraping metric record"""
    timestamp: str
    date_scraped: str
    trips_attempted: int
    trips_successful: int
    trips_failed: int
    zero_fish_high_anglers: int
    weight_qualifiers_found: int
    success_rate: float
    data_quality_score: float
    alerts_triggered: List[str]

class ScraperMonitor:
    """Real-time scraper monitoring system"""

    def __init__(self, db_path: str = "scraper_monitoring.db"):
        self.db_path = db_path
        self.init_database()

        # Alert thresholds
        self.SUCCESS_RATE_CRITICAL = 85.0
        self.SUCCESS_RATE_WARNING = 90.0
        self.ZERO_FISH_RATE_CRITICAL = 15.0
        self.CONSECUTIVE_FAILURES_ALERT = 3

    def init_database(self):
        """Initialize monitoring database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraping_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                date_scraped TEXT NOT NULL,
                trips_attempted INTEGER,
                trips_successful INTEGER,
                trips_failed INTEGER,
                zero_fish_high_anglers INTEGER,
                weight_qualifiers_found INTEGER,
                success_rate REAL,
                data_quality_score REAL,
                alerts_triggered TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                context TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                acknowledged BOOLEAN DEFAULT FALSE
            )
        """)

        conn.commit()
        conn.close()

    def record_scraping_session(self, stats: Dict, date_scraped: str) -> ScrapingMetric:
        """Record metrics from a scraping session"""

        # Calculate data quality score
        success_rate = stats.get('success_rate', 0)
        zero_fish_rate = (stats.get('zero_fish_high_anglers', 0) / max(stats.get('trips_attempted', 1), 1)) * 100

        # Quality score: 100 = perfect, 0 = completely broken
        quality_score = min(100, (success_rate + max(0, 100 - zero_fish_rate * 2)) / 2)

        # Determine alerts
        alerts = []
        if success_rate < self.SUCCESS_RATE_CRITICAL:
            alerts.append(f"CRITICAL_SUCCESS_RATE:{success_rate:.1f}%")
        elif success_rate < self.SUCCESS_RATE_WARNING:
            alerts.append(f"WARNING_SUCCESS_RATE:{success_rate:.1f}%")

        if zero_fish_rate > self.ZERO_FISH_RATE_CRITICAL:
            alerts.append(f"CRITICAL_ZERO_FISH_RATE:{zero_fish_rate:.1f}%")

        if stats.get('weight_qualifiers_found', 0) == 0 and stats.get('trips_successful', 0) > 5:
            alerts.append("SUSPICIOUS_NO_WEIGHT_QUALIFIERS")

        # Create metric record
        metric = ScrapingMetric(
            timestamp=datetime.now().isoformat(),
            date_scraped=date_scraped,
            trips_attempted=stats.get('trips_attempted', 0),
            trips_successful=stats.get('trips_successful', 0),
            trips_failed=stats.get('trips_failed', 0),
            zero_fish_high_anglers=stats.get('zero_fish_high_anglers', 0),
            weight_qualifiers_found=stats.get('weight_qualifiers_found', 0),
            success_rate=success_rate,
            data_quality_score=quality_score,
            alerts_triggered=alerts
        )

        # Save to database
        self._save_metric(metric)

        # Process alerts
        self._process_alerts(metric)

        return metric

    def _save_metric(self, metric: ScrapingMetric):
        """Save metric to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO scraping_metrics (
                timestamp, date_scraped, trips_attempted, trips_successful, trips_failed,
                zero_fish_high_anglers, weight_qualifiers_found, success_rate,
                data_quality_score, alerts_triggered
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metric.timestamp, metric.date_scraped, metric.trips_attempted,
            metric.trips_successful, metric.trips_failed, metric.zero_fish_high_anglers,
            metric.weight_qualifiers_found, metric.success_rate,
            metric.data_quality_score, json.dumps(metric.alerts_triggered)
        ))

        conn.commit()
        conn.close()

    def _process_alerts(self, metric: ScrapingMetric):
        """Process and send alerts based on metrics"""
        for alert in metric.alerts_triggered:
            severity = "CRITICAL" if "CRITICAL" in alert else "WARNING"
            self._create_alert(alert, severity, metric)

        # Check for trend-based alerts
        self._check_trend_alerts(metric)

    def _create_alert(self, alert_type: str, severity: str, metric: ScrapingMetric):
        """Create and dispatch an alert"""
        if "SUCCESS_RATE" in alert_type:
            message = f"Scraper success rate {severity.lower()}: {metric.success_rate:.1f}% for {metric.date_scraped}"
        elif "ZERO_FISH_RATE" in alert_type:
            message = f"High zero-fish rate detected: {(metric.zero_fish_high_anglers/metric.trips_attempted*100):.1f}% for {metric.date_scraped}"
        elif "NO_WEIGHT_QUALIFIERS" in alert_type:
            message = f"No weight qualifiers found despite successful scraping - possible parsing regression for {metric.date_scraped}"
        else:
            message = f"Data quality alert: {alert_type} for {metric.date_scraped}"

        # Save alert to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alerts (alert_type, severity, message, context)
            VALUES (?, ?, ?, ?)
        """, (alert_type, severity, message, json.dumps(asdict(metric))))
        conn.commit()
        conn.close()

        # Dispatch alert
        self._dispatch_alert(severity, message, metric)

    def _dispatch_alert(self, severity: str, message: str, metric: ScrapingMetric):
        """Dispatch alert to various channels"""
        logger.error(f"🚨 {severity} ALERT: {message}")

        # Console alert
        print(f"\n{'='*60}")
        print(f"🚨 SCRAPER ALERT - {severity}")
        print(f"{'='*60}")
        print(f"Message: {message}")
        print(f"Date: {metric.date_scraped}")
        print(f"Success Rate: {metric.success_rate:.1f}%")
        print(f"Data Quality Score: {metric.data_quality_score:.1f}/100")
        print(f"Timestamp: {metric.timestamp}")
        print(f"{'='*60}\n")

        # In production, would integrate with:
        # - Slack webhooks
        # - Email notifications
        # - PagerDuty
        # - SMS alerts
        # - Dashboard updates

    def _check_trend_alerts(self, current_metric: ScrapingMetric):
        """Check for concerning trends over time"""
        # Get recent metrics for trend analysis
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT success_rate, data_quality_score
            FROM scraping_metrics
            ORDER BY created_at DESC
            LIMIT ?
        """, (self.CONSECUTIVE_FAILURES_ALERT + 1,))

        recent_metrics = cursor.fetchall()
        conn.close()

        if len(recent_metrics) >= self.CONSECUTIVE_FAILURES_ALERT:
            # Check for consecutive failures
            consecutive_failures = 0
            for success_rate, _ in recent_metrics:
                if success_rate < self.SUCCESS_RATE_CRITICAL:
                    consecutive_failures += 1
                else:
                    break

            if consecutive_failures >= self.CONSECUTIVE_FAILURES_ALERT:
                self._create_alert(
                    f"CONSECUTIVE_FAILURES:{consecutive_failures}",
                    "CRITICAL",
                    current_metric
                )

            # Check for declining trend
            if len(recent_metrics) >= 5:
                rates = [rate for rate, _ in recent_metrics[:5]]
                if all(rates[i] < rates[i+1] for i in range(4)):  # Strictly decreasing
                    self._create_alert(
                        "DECLINING_TREND",
                        "WARNING",
                        current_metric
                    )

    def get_recent_metrics(self, days: int = 7) -> List[Dict]:
        """Get recent metrics for reporting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM scraping_metrics
            WHERE created_at > datetime('now', '-{} days')
            ORDER BY created_at DESC
        """.format(days))

        columns = [description[0] for description in cursor.description]
        metrics = []
        for row in cursor.fetchall():
            metric_dict = dict(zip(columns, row))
            metric_dict['alerts_triggered'] = json.loads(metric_dict['alerts_triggered'] or '[]')
            metrics.append(metric_dict)

        conn.close()
        return metrics

    def get_active_alerts(self) -> List[Dict]:
        """Get unacknowledged alerts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM alerts
            WHERE acknowledged = FALSE
            ORDER BY created_at DESC
        """)

        columns = [description[0] for description in cursor.description]
        alerts = []
        for row in cursor.fetchall():
            alert_dict = dict(zip(columns, row))
            alert_dict['context'] = json.loads(alert_dict['context'] or '{}')
            alerts.append(alert_dict)

        conn.close()
        return alerts

    def acknowledge_alert(self, alert_id: int):
        """Acknowledge an alert"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE alerts SET acknowledged = TRUE WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()

    def generate_health_report(self) -> Dict:
        """Generate comprehensive health report"""
        recent_metrics = self.get_recent_metrics(7)
        active_alerts = self.get_active_alerts()

        if not recent_metrics:
            return {
                'status': 'no_data',
                'message': 'No recent scraping data available',
                'timestamp': datetime.now().isoformat()
            }

        # Calculate averages
        avg_success_rate = sum(m['success_rate'] for m in recent_metrics) / len(recent_metrics)
        avg_quality_score = sum(m['data_quality_score'] for m in recent_metrics) / len(recent_metrics)
        total_critical_alerts = len([a for a in active_alerts if a['severity'] == 'CRITICAL'])

        # Determine overall health
        if total_critical_alerts > 0 or avg_success_rate < self.SUCCESS_RATE_CRITICAL:
            status = 'critical'
            message = f"System health CRITICAL: {total_critical_alerts} active alerts, {avg_success_rate:.1f}% avg success rate"
        elif avg_success_rate < self.SUCCESS_RATE_WARNING:
            status = 'warning'
            message = f"System health WARNING: {avg_success_rate:.1f}% avg success rate"
        else:
            status = 'healthy'
            message = f"System healthy: {avg_success_rate:.1f}% avg success rate"

        return {
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'avg_success_rate': round(avg_success_rate, 1),
                'avg_quality_score': round(avg_quality_score, 1),
                'days_analyzed': len(recent_metrics),
                'active_critical_alerts': total_critical_alerts,
                'active_warning_alerts': len([a for a in active_alerts if a['severity'] == 'WARNING'])
            },
            'recent_performance': recent_metrics[:5],  # Last 5 runs
            'active_alerts': active_alerts
        }

def main():
    """Example usage of the monitoring system"""
    monitor = ScraperMonitor()

    # Simulate scraping stats (would come from actual scraper)
    example_stats = {
        'trips_attempted': 45,
        'trips_successful': 38,
        'trips_failed': 7,
        'zero_fish_high_anglers': 3,
        'weight_qualifiers_found': 2,
        'success_rate': 84.4  # This would trigger a critical alert
    }

    # Record the session
    metric = monitor.record_scraping_session(example_stats, "2025-09-24")

    # Generate health report
    health_report = monitor.generate_health_report()
    print(json.dumps(health_report, indent=2))

    return health_report

if __name__ == "__main__":
    main()