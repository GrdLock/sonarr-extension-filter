"""
Abstract base class for download clients
"""

from abc import ABC, abstractmethod


class BaseDownloadClient(ABC):
    """Abstract base class for download client implementations"""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    @abstractmethod
    def get_torrent_files(self, download_id):
        """
        Get list of files in a torrent

        Args:
            download_id: Download ID or hash

        Returns:
            dict: Dictionary with 'files' key containing list of file paths
        """
        pass

    @abstractmethod
    def remove_torrent(self, download_id, delete_files=True):
        """
        Remove a torrent from the client

        Args:
            download_id: Download ID or hash
            delete_files: Whether to delete downloaded files

        Returns:
            bool: True if successful
        """
        pass
