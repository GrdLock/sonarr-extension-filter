"""
Transmission client implementation
"""

import requests
import json
from app.clients.base_client import BaseDownloadClient


class TransmissionClient(BaseDownloadClient):
    """Transmission download client"""

    def __init__(self, config, logger):
        super().__init__(config, logger)
        self.session = requests.Session()
        self.session.auth = (config.username, config.password)
        self.session_id = None
        self.rpc_url = f"{config.url}{config.rpc_path or '/transmission/rpc'}"
        self._initialized = False

    def _ensure_initialized(self):
        """Ensure session is initialized (lazy initialization)"""
        if not self._initialized:
            self._get_session_id()
            self._initialized = True

    def _get_session_id(self):
        """Get session ID from Transmission"""
        try:
            response = self.session.post(self.rpc_url, timeout=10)

            if response.status_code == 409:
                self.session_id = response.headers.get('X-Transmission-Session-Id')
                self.session.headers['X-Transmission-Session-Id'] = self.session_id
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to get Transmission session ID: {str(e)}")
            return False

    def _rpc_call(self, method, arguments=None):
        """Make RPC call to Transmission"""
        if not self.session_id:
            self._get_session_id()

        payload = {
            'method': method,
            'arguments': arguments or {}
        }

        try:
            response = self.session.post(
                self.rpc_url,
                json=payload,
                timeout=10
            )

            if response.status_code == 409:
                self._get_session_id()
                response = self.session.post(
                    self.rpc_url,
                    json=payload,
                    timeout=10
                )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            self.logger.error(f"Transmission RPC call failed: {str(e)}")
            return None

    def get_torrent_files(self, download_id):
        """Get files in a torrent"""
        try:
            self._ensure_initialized()
            result = self._rpc_call(
                'torrent-get',
                {'ids': [download_id], 'fields': ['files']}
            )

            if result and 'arguments' in result and 'torrents' in result['arguments']:
                torrents = result['arguments']['torrents']

                if torrents:
                    files_data = torrents[0].get('files', [])
                    files = [file_info['name'] for file_info in files_data]

                    self.logger.debug(f"Retrieved {len(files)} files from Transmission")
                    return {'files': files}

            return None

        except Exception as e:
            self.logger.error(f"Failed to get torrent files from Transmission: {str(e)}")
            return None

    def remove_torrent(self, download_id, delete_files=True):
        """Remove torrent from Transmission"""
        try:
            self._ensure_initialized()
            result = self._rpc_call(
                'torrent-remove',
                {'ids': [download_id], 'delete-local-data': delete_files}
            )

            if result and result.get('result') == 'success':
                self.logger.info(f"Removed torrent {download_id} from Transmission")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to remove torrent from Transmission: {str(e)}")
            return False
