"""
changedetection.io Integration for Career Page Monitoring.

Monitors employer career pages for new job postings without needing to
poll constantly. When a change is detected, triggers a targeted scrape.

Setup:
- Self-hosted changedetection.io instance (Docker)
- API key configured in settings.CHANGE_DETECTION_API_KEY
- Base URL configured in settings.CHANGE_DETECTION_URL
"""
import logging
from typing import List, Dict, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class ChangeDetectionClient:
    """Client for changedetection.io REST API."""

    def __init__(self):
        self.base_url = getattr(settings, 'CHANGE_DETECTION_URL', 'http://localhost:5000')
        self.api_key = getattr(settings, 'CHANGE_DETECTION_API_KEY', '')
        self.timeout = 30

    @property
    def headers(self) -> Dict:
        h = {'Content-Type': 'application/json'}
        if self.api_key:
            h['x-api-key'] = self.api_key
        return h

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def health_check(self) -> bool:
        """Check if changedetection.io is reachable."""
        try:
            resp = requests.get(
                f"{self.base_url}/api/v1/systeminfo",
                headers=self.headers,
                timeout=self.timeout,
            )
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"changedetection.io health check failed: {e}")
            return False

    def list_watches(self) -> Dict:
        """List all monitored URLs."""
        resp = requests.get(
            f"{self.base_url}/api/v1/watch",
            headers=self.headers,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def add_watch(
        self,
        url: str,
        title: str = "",
        tag: str = "career-page",
        check_interval: int = 3600,
        css_filter: str = "",
    ) -> Optional[str]:
        """
        Add a new URL to monitor.

        Args:
            url: Career page URL to monitor
            title: Label for the watch
            tag: Tag for grouping (default: career-page)
            check_interval: Check frequency in seconds (default: 1 hour)
            css_filter: Optional CSS selector to watch specific section

        Returns:
            Watch UUID or None on failure
        """
        payload = {
            'url': url,
            'title': title or url,
            'tag': tag,
            'time_between_check': {'minutes': check_interval // 60},
        }
        if css_filter:
            payload['css_filter'] = css_filter

        try:
            resp = requests.post(
                f"{self.base_url}/api/v1/watch",
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get('uuid')
        except Exception as e:
            logger.error(f"Failed to add watch for {url}: {e}")
            return None

    def delete_watch(self, watch_uuid: str) -> bool:
        """Remove a watch by UUID."""
        try:
            resp = requests.delete(
                f"{self.base_url}/api/v1/watch/{watch_uuid}",
                headers=self.headers,
                timeout=self.timeout,
            )
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.error(f"Failed to delete watch {watch_uuid}: {e}")
            return False

    def get_watch_history(self, watch_uuid: str) -> List[Dict]:
        """Get change history for a watch."""
        try:
            resp = requests.get(
                f"{self.base_url}/api/v1/watch/{watch_uuid}/history",
                headers=self.headers,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to get history for {watch_uuid}: {e}")
            return []

    def get_latest_snapshot(self, watch_uuid: str) -> Optional[str]:
        """Get the latest page snapshot text."""
        try:
            resp = requests.get(
                f"{self.base_url}/api/v1/watch/{watch_uuid}/history/latest",
                headers=self.headers,
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                return resp.text
        except Exception as e:
            logger.error(f"Failed to get snapshot for {watch_uuid}: {e}")
        return None

    def trigger_recheck(self, watch_uuid: str) -> bool:
        """Force an immediate recheck of a watch."""
        try:
            resp = requests.get(
                f"{self.base_url}/api/v1/watch/{watch_uuid}/trigger-check",
                headers=self.headers,
                timeout=self.timeout,
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Failed to trigger recheck for {watch_uuid}: {e}")
            return False


class CareerPageMonitor:
    """
    High-level service for monitoring career pages via changedetection.io.

    Integrates with the scraper pipeline to trigger targeted scrapes when
    career pages change.
    """

    def __init__(self):
        self.client = ChangeDetectionClient()

    @property
    def is_available(self) -> bool:
        return self.client.is_configured and self.client.health_check()

    def register_company_career_page(
        self, company_name: str, career_url: str, css_selector: str = ""
    ) -> Optional[str]:
        """
        Register a company's career page for monitoring.

        Returns the watch UUID for tracking.
        """
        return self.client.add_watch(
            url=career_url,
            title=f"{company_name} - Careers",
            tag="career-page",
            check_interval=3600,
            css_filter=css_selector,
        )

    def register_source_pages(self) -> int:
        """
        Register all active sources' career pages for monitoring.

        Returns count of successfully registered watches.
        """
        from apps.jobs.models import Source

        sources = Source.objects.filter(is_active=True, url__isnull=False)
        registered = 0

        for source in sources:
            if source.url and not self._is_already_watched(source.url):
                watch_id = self.client.add_watch(
                    url=source.url,
                    title=f"{source.name} - Career Page",
                    tag="career-page",
                    check_interval=3600,
                )
                if watch_id:
                    registered += 1
                    logger.info(f"Registered watch for {source.name}: {watch_id}")

        return registered

    def _is_already_watched(self, url: str) -> bool:
        """Check if a URL is already being monitored."""
        try:
            watches = self.client.list_watches()
            for watch_id, watch_data in watches.items():
                if watch_data.get('url') == url:
                    return True
        except Exception:
            pass
        return False

    def get_changed_pages(self) -> List[Dict]:
        """
        Get list of career pages that have changed recently.

        Returns list of dicts with url, title, last_changed timestamp.
        """
        try:
            watches = self.client.list_watches()
            changed = []
            for watch_id, watch_data in watches.items():
                if watch_data.get('last_changed'):
                    changed.append({
                        'watch_id': watch_id,
                        'url': watch_data.get('url'),
                        'title': watch_data.get('title', ''),
                        'last_changed': watch_data.get('last_changed'),
                    })
            return changed
        except Exception as e:
            logger.error(f"Failed to get changed pages: {e}")
            return []

    def process_changes(self) -> Dict:
        """
        Process detected changes — trigger targeted scrapes for changed pages.

        Returns summary of processed changes.
        """
        from .tasks import scrape_single_url

        changed = self.get_changed_pages()
        processed = 0
        errors = 0

        for page in changed:
            try:
                scrape_single_url.delay(url=page['url'])
                processed += 1
            except Exception as e:
                logger.error(f"Failed to queue scrape for {page['url']}: {e}")
                errors += 1

        return {
            'total_changes': len(changed),
            'processed': processed,
            'errors': errors,
        }


_monitor: Optional[CareerPageMonitor] = None


def get_career_page_monitor() -> CareerPageMonitor:
    global _monitor
    if _monitor is None:
        _monitor = CareerPageMonitor()
    return _monitor
