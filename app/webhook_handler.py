"""
Webhook handler for processing Sonarr events
"""

from app.torrent_parser import TorrentParser
from app.extension_checker import ExtensionChecker
from app.clients.qbittorrent import QBittorrentClient
from app.clients.transmission import TransmissionClient
from app.clients.deluge import DelugeClient
from app.sonarr.api import SonarrAPI
import time


class WebhookHandler:
    """Handles incoming webhooks from Sonarr"""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.extension_checker = ExtensionChecker(config.filtering, logger)
        self.sonarr_api = SonarrAPI(config.sonarr, logger)

        # Initialize appropriate download client
        self.download_client = self._init_download_client()

    def _init_download_client(self):
        """Initialize the appropriate download client"""
        client_type = self.config.download_client.type.lower()

        if client_type == 'qbittorrent':
            return QBittorrentClient(self.config.download_client, self.logger)
        elif client_type == 'transmission':
            return TransmissionClient(self.config.download_client, self.logger)
        elif client_type == 'deluge':
            return DelugeClient(self.config.download_client, self.logger)
        else:
            raise ValueError(f"Unsupported download client type: {client_type}")

    def _wait_for_torrent(self, download_id, max_retries=3):
        """
        Wait for torrent to be available in download client with exponential backoff

        Args:
            download_id: Download ID or hash
            max_retries: Maximum number of retry attempts

        Returns:
            dict or None: Torrent data if found, None otherwise
        """
        for attempt in range(max_retries):
            # Exponential backoff: 2, 4, 8 seconds
            wait_time = 2 ** (attempt + 1)
            time.sleep(wait_time)

            self.logger.debug(f"Attempt {attempt + 1}/{max_retries} to retrieve torrent {download_id}")
            torrent_data = self.download_client.get_torrent_files(download_id)

            # Check if we have both torrent data AND a populated file list
            if torrent_data and torrent_data.get('files'):
                self.logger.debug(f"Successfully retrieved torrent with {len(torrent_data['files'])} files")
                return torrent_data

            if attempt < max_retries - 1:
                if torrent_data and not torrent_data.get('files'):
                    self.logger.debug(f"Torrent found but file list not yet populated, waiting {wait_time * 2} seconds before retry...")
                else:
                    self.logger.debug(f"Torrent not found, waiting {wait_time * 2} seconds before retry...")

        return None

    def process_grab_event(self, payload):
        """
        Process a 'Grab' event from Sonarr

        Args:
            payload: Webhook payload from Sonarr

        Returns:
            dict: Result of processing
        """
        try:
            # Extract relevant information
            series_title = payload.get('series', {}).get('title', 'Unknown')
            release_title = payload.get('release', {}).get('title', 'Unknown')
            download_id = payload.get('downloadId', '')

            self.logger.info(f"Processing grab for: {series_title} - {release_title}")
            self.logger.debug(f"Download ID: {download_id}")

            if not download_id:
                self.logger.warning("No download ID provided in webhook payload")
                return {
                    "status": "warning",
                    "message": "No download ID provided"
                }

            # Get torrent info from download client with retry logic
            torrent_data = self._wait_for_torrent(download_id)

            if not torrent_data:
                self.logger.warning(f"Could not retrieve torrent data for {download_id} after multiple attempts")
                return {
                    "status": "warning",
                    "message": "Could not retrieve torrent data"
                }

            # Check for blocked extensions
            file_list = torrent_data.get('files', [])
            self.logger.debug(f"Found {len(file_list)} files in torrent")

            blocked_files = self.extension_checker.check_files(file_list)

            if blocked_files:
                self.logger.warning(f"Found {len(blocked_files)} blocked files in {release_title}")
                self.logger.warning(f"Blocked files: {', '.join(blocked_files)}")

                # Extract series information for blocklist
                series_id = payload.get('series', {}).get('id')
                self.logger.debug(f"Series ID: {series_id}")

                # Remove the download
                queue_id = self._get_queue_id(download_id)

                if queue_id:
                    action = self.config.filtering.action
                    blocklist = 'blocklist' in action.lower()

                    success = self.sonarr_api.remove_from_queue(
                        queue_id,
                        remove_from_client=True,
                        blocklist=blocklist
                    )

                    if success:
                        # If blocklist was requested, verify and add as fallback if needed
                        if blocklist and series_id:
                            self.logger.info("Ensuring blocklist was applied...")
                            # Try to add directly to blocklist as a fallback
                            # This ensures the item is blocklisted even if the queue removal
                            # method didn't properly add it to the blocklist
                            self.sonarr_api.add_to_blocklist(series_id, release_title)

                        self.logger.info(f"Successfully removed {release_title} from queue")
                        return {
                            "status": "removed",
                            "message": f"Removed download with {len(blocked_files)} blocked file(s)",
                            "blocked_files": blocked_files,
                            "blocklisted": blocklist
                        }
                    else:
                        self.logger.error(f"Failed to remove {release_title} from queue")
                        return {
                            "status": "error",
                            "message": "Failed to remove from queue"
                        }
                else:
                    self.logger.error(f"Could not find queue ID for {download_id}")
                    # If we can't find the queue ID but blocklist is requested,
                    # try to add directly to blocklist
                    action = self.config.filtering.action
                    blocklist = 'blocklist' in action.lower()

                    if blocklist and series_id:
                        self.logger.info("Attempting direct blocklist add since queue ID not found")
                        self.sonarr_api.add_to_blocklist(series_id, release_title)

                    return {
                        "status": "error",
                        "message": "Could not find queue ID"
                    }
            else:
                self.logger.info(f"No blocked extensions found in {release_title}")
                return {
                    "status": "clean",
                    "message": "No blocked extensions found"
                }

        except Exception as e:
            self.logger.error(f"Error processing grab event: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }

    def _get_queue_id(self, download_id):
        """
        Get Sonarr queue ID from download ID

        Args:
            download_id: Download client's download ID

        Returns:
            int: Queue ID or None
        """
        queue_items = self.sonarr_api.get_queue()

        # Debug logging
        self.logger.debug(f"Looking for download ID: {download_id}")
        self.logger.debug(f"Found {len(queue_items)} items in queue")

        # Case-insensitive comparison for torrent hashes
        download_id_lower = download_id.lower() if download_id else ''

        for item in queue_items:
            queue_download_id = item.get('downloadId', '')
            queue_download_id_lower = queue_download_id.lower() if queue_download_id else ''

            if queue_download_id_lower == download_id_lower:
                self.logger.debug(f"Found match! Queue ID: {item.get('id')}")
                return item.get('id')

        # If no match found, log all queue download IDs for debugging
        self.logger.warning(f"No queue match found for {download_id}")
        if queue_items:
            queue_ids = [item.get('downloadId', 'N/A') for item in queue_items[:5]]  # Show first 5
            self.logger.debug(f"Queue download IDs: {', '.join(queue_ids)}")
        return None
