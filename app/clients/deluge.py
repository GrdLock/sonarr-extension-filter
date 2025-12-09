"""
Deluge client implementation
"""

import requests
import json
from app.clients.base_client import BaseDownloadClient


class DelugeClient(BaseDownloadClient):
    """Deluge download client"""

    def __init__(self, config, logger):
        super().__init__(config, logger)
        self.session = requests.Session()
        self.rpc_url = f"{config.url}/json"
        self.request_id = 0
        self._authenticated = False

    def _ensure_authenticated(self):
        """Ensure authentication before making requests (lazy initialization)"""
        if not self._authenticated:
            self._login()

    def _login(self):
        """Authenticate with Deluge"""
        try:
            payload = {
                'method': 'auth.login',
                'params': [self.config.password],
                'id': self._get_request_id()
            }

            response = self.session.post(
                self.rpc_url,
                json=payload,
                timeout=10
            )

            response.raise_for_status()
            result = response.json()

            if result.get('result'):
                self.logger.info("Successfully authenticated with Deluge")
                self._authenticated = True
            else:
                raise Exception("Authentication failed")

        except Exception as e:
            self.logger.error(f"Failed to authenticate with Deluge: {str(e)}")
            raise

    def _get_request_id(self):
        """Get incrementing request ID"""
        self.request_id += 1
        return self.request_id

    def _rpc_call(self, method, params=None):
        """Make RPC call to Deluge"""
        payload = {
            'method': method,
            'params': params or [],
            'id': self._get_request_id()
        }

        try:
            response = self.session.post(
                self.rpc_url,
                json=payload,
                timeout=10
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            self.logger.error(f"Deluge RPC call failed: {str(e)}")
            return None

    def get_torrent_files(self, download_id):
        """Get files in a torrent"""
        try:
            self._ensure_authenticated()
            result = self._rpc_call(
                'web.get_torrent_files',
                [download_id]
            )

            if result and 'result' in result:
                files_data = result['result']
                files = [file_info['path'] for file_info in files_data.values()]

                self.logger.debug(f"Retrieved {len(files)} files from Deluge")
                return {'files': files}

            return None

        except Exception as e:
            self.logger.error(f"Failed to get torrent files from Deluge: {str(e)}")
            return None

    def remove_torrent(self, download_id, delete_files=True):
        """Remove torrent from Deluge"""
        try:
            self._ensure_authenticated()
            result = self._rpc_call(
                'core.remove_torrent',
                [download_id, delete_files]
            )

            if result and result.get('result'):
                self.logger.info(f"Removed torrent {download_id} from Deluge")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to remove torrent from Deluge: {str(e)}")
            return False
