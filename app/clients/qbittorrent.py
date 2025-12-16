"""
qBittorrent client implementation
"""

import requests
from app.clients.base_client import BaseDownloadClient


class QBittorrentClient(BaseDownloadClient):
    """qBittorrent download client"""

    def __init__(self, config, logger):
        super().__init__(config, logger)
        self.session = requests.Session()
        # Ensure URL has proper format for CSRF headers
        self.base_url = self.config.url.rstrip('/')
        # Set headers required for qBittorrent CSRF protection
        # Referer needs trailing slash, Origin does not
        self.session.headers.update({
            'Referer': f"{self.base_url}/",
            'Origin': self.base_url
        })
        self._authenticated = False

    def _ensure_authenticated(self):
        """Ensure authentication before making requests (lazy initialization)"""
        if not self._authenticated:
            try:
                # Clear cookies before re-authenticating to ensure fresh session
                self.session.cookies.clear()

                url = f"{self.base_url}/api/v2/auth/login"
                data = {
                    'username': self.config.username,
                    'password': self.config.password
                }

                self.logger.debug(f"Authenticating to qBittorrent at {url}")
                response = self.session.post(url, data=data, timeout=10)

                if response.status_code == 200 and response.text == 'Ok.':
                    self.logger.info("Successfully authenticated with qBittorrent")
                    self._authenticated = True
                else:
                    raise Exception(f"Authentication failed: {response.text}")

            except Exception as e:
                self.logger.error(f"Failed to authenticate with qBittorrent: {str(e)}")
                raise

    def _make_authenticated_request(self, method, url, max_retries=2, **kwargs):
        """
        Make an authenticated request with automatic retry on 403 (session expired)

        Args:
            method: HTTP method ('GET' or 'POST')
            url: Request URL
            max_retries: Number of retry attempts on authentication failure
            **kwargs: Additional arguments to pass to requests (params, data, etc.)

        Returns:
            Response object
        """
        for attempt in range(max_retries + 1):
            self._ensure_authenticated()

            try:
                self.logger.debug(f"{method} request to {url} (attempt {attempt + 1}/{max_retries + 1})")

                if method.upper() == 'GET':
                    response = self.session.get(url, timeout=10, **kwargs)
                elif method.upper() == 'POST':
                    response = self.session.post(url, timeout=10, **kwargs)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # If we get a 403, the session likely expired
                if response.status_code == 403 and attempt < max_retries:
                    self.logger.warning(f"qBittorrent returned 403 (attempt {attempt + 1}), re-authenticating...")
                    self._authenticated = False
                    continue

                return response

            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    self.logger.warning(f"Request failed (attempt {attempt + 1}), retrying... ({str(e)})")
                    self._authenticated = False
                    continue
                raise

        return response

    def get_torrent_files(self, download_id):
        """Get files in a torrent"""
        try:
            # Get torrent info with automatic session retry
            url = f"{self.base_url}/api/v2/torrents/files"
            params = {'hash': download_id}

            self.logger.debug(f"Getting torrent files for hash: {download_id}")
            response = self._make_authenticated_request('GET', url, params=params)
            response.raise_for_status()

            files_data = response.json()

            # Extract file names
            files = [file_info['name'] for file_info in files_data]

            self.logger.debug(f"Retrieved {len(files)} files from qBittorrent for {download_id}")

            return {'files': files}

        except Exception as e:
            self.logger.error(f"Failed to get torrent files from qBittorrent: {str(e)}")
            return None

    def remove_torrent(self, download_id, delete_files=True):
        """Remove torrent from qBittorrent"""
        try:
            url = f"{self.base_url}/api/v2/torrents/delete"
            data = {
                'hashes': download_id,
                'deleteFiles': 'true' if delete_files else 'false'
            }

            response = self._make_authenticated_request('POST', url, data=data)
            response.raise_for_status()

            self.logger.info(f"Removed torrent {download_id} from qBittorrent")
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove torrent from qBittorrent: {str(e)}")
            return False
