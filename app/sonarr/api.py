"""
Sonarr API client
"""

import requests


class SonarrAPI:
    """Client for interacting with Sonarr API"""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.base_url = f"{config.url}/api/v3"
        self.headers = {
            'X-Api-Key': config.api_key,
            'Content-Type': 'application/json'
        }

    def get_queue(self):
        """
        Get current download queue

        Returns:
            list: List of queue items
        """
        try:
            url = f"{self.base_url}/queue"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            records = data.get('records', [])

            self.logger.debug(f"Retrieved {len(records)} items from queue")
            return records

        except Exception as e:
            self.logger.error(f"Failed to get queue from Sonarr: {str(e)}")
            return []

    def remove_from_queue(self, queue_id, remove_from_client=True, blocklist=False):
        """
        Remove an item from the queue

        Args:
            queue_id: Queue item ID
            remove_from_client: Remove from download client
            blocklist: Add to blocklist

        Returns:
            bool: True if successful
        """
        try:
            url = f"{self.base_url}/queue/{queue_id}"
            params = {
                'removeFromClient': str(remove_from_client).lower(),
                'blocklist': str(blocklist).lower()
            }

            self.logger.info(f"Removing queue item {queue_id} with params: {params}")
            self.logger.debug(f"DELETE URL: {url}")

            response = requests.delete(
                url,
                headers=self.headers,
                params=params,
                timeout=10
            )

            self.logger.debug(f"Response status: {response.status_code}")
            self.logger.debug(f"Response body: {response.text}")

            response.raise_for_status()

            action = "removed and blocklisted" if blocklist else "removed"
            self.logger.info(f"Queue item {queue_id} {action} successfully")

            # Verify blocklist was applied if requested
            if blocklist:
                self.logger.info("Verifying item was added to blocklist...")
                # Small delay to allow Sonarr to process
                import time
                time.sleep(1)
                blocklist_items = self.get_blocklist()
                self.logger.info(f"Current blocklist has {len(blocklist_items)} items")

            return True

        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error removing queue item {queue_id}: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to remove queue item {queue_id}: {str(e)}")
            return False

    def get_blocklist(self, page=1, page_size=20):
        """
        Get blocklist items

        Args:
            page: Page number
            page_size: Number of items per page

        Returns:
            list: List of blocklist items
        """
        try:
            url = f"{self.base_url}/blocklist"
            params = {
                'page': page,
                'pageSize': page_size
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            records = data.get('records', [])

            self.logger.debug(f"Retrieved {len(records)} blocklist items (total: {data.get('totalRecords', 0)})")
            return records

        except Exception as e:
            self.logger.error(f"Failed to get blocklist from Sonarr: {str(e)}")
            return []

    def get_series(self, series_id=None):
        """
        Get series information

        Args:
            series_id: Optional series ID

        Returns:
            dict or list: Series data
        """
        try:
            if series_id:
                url = f"{self.base_url}/series/{series_id}"
            else:
                url = f"{self.base_url}/series"

            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            self.logger.error(f"Failed to get series from Sonarr: {str(e)}")
            return None
