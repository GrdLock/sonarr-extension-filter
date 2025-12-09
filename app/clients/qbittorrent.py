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
        self._authenticated = False

    def _ensure_authenticated(self):
        """Ensure authentication before making requests (lazy initialization)"""
        if not self._authenticated:
            try:
                url = f"{self.config.url}/api/v2/auth/login"
                data = {
                    'username': self.config.username,
                    'password': self.config.password
                }

                response = self.session.post(url, data=data, timeout=10)

                if response.status_code == 200 and response.text == 'Ok.':
                    self.logger.info("Successfully authenticated with qBittorrent")
                    self._authenticated = True
                else:
                    raise Exception(f"Authentication failed: {response.text}")

            except Exception as e:
                self.logger.error(f"Failed to authenticate with qBittorrent: {str(e)}")
                raise

    def get_torrent_files(self, download_id):
        """Get files in a torrent"""
        try:
            self._ensure_authenticated()
            # Get torrent info
            url = f"{self.config.url}/api/v2/torrents/files"
            params = {'hash': download_id}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            files_data = response.json()

            # Extract file names
            files = [file_info['name'] for file_info in files_data]

            self.logger.debug(f"Retrieved {len(files)} files from qBittorrent")

            return {'files': files}

        except Exception as e:
            self.logger.error(f"Failed to get torrent files from qBittorrent: {str(e)}")
            return None

    def remove_torrent(self, download_id, delete_files=True):
        """Remove torrent from qBittorrent"""
        try:
            self._ensure_authenticated()
            url = f"{self.config.url}/api/v2/torrents/delete"
            data = {
                'hashes': download_id,
                'deleteFiles': 'true' if delete_files else 'false'
            }

            response = self.session.post(url, data=data, timeout=10)
            response.raise_for_status()

            self.logger.info(f"Removed torrent {download_id} from qBittorrent")
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove torrent from qBittorrent: {str(e)}")
            return False
