"""
Torrent file parser
"""

import bencodepy


class TorrentParser:
    """Parse .torrent files and extract file information"""

    @staticmethod
    def parse_torrent_file(torrent_path):
        """
        Parse a .torrent file and extract file list

        Args:
            torrent_path: Path to .torrent file

        Returns:
            list: List of file paths in the torrent
        """
        try:
            with open(torrent_path, 'rb') as f:
                torrent_data = bencodepy.decode(f.read())

            files = []

            if b'info' in torrent_data:
                info = torrent_data[b'info']

                # Check if single file or multi-file torrent
                if b'files' in info:
                    # Multi-file torrent
                    for file_info in info[b'files']:
                        path_parts = [part.decode('utf-8') for part in file_info[b'path']]
                        file_path = '/'.join(path_parts)
                        files.append(file_path)
                else:
                    # Single file torrent
                    filename = info[b'name'].decode('utf-8')
                    files.append(filename)

            return files

        except Exception as e:
            raise Exception(f"Failed to parse torrent file: {str(e)}")

    @staticmethod
    def parse_torrent_data(torrent_bytes):
        """
        Parse torrent data from bytes

        Args:
            torrent_bytes: Torrent file as bytes

        Returns:
            list: List of file paths in the torrent
        """
        try:
            torrent_data = bencodepy.decode(torrent_bytes)

            files = []

            if b'info' in torrent_data:
                info = torrent_data[b'info']

                if b'files' in info:
                    for file_info in info[b'files']:
                        path_parts = [part.decode('utf-8') for part in file_info[b'path']]
                        file_path = '/'.join(path_parts)
                        files.append(file_path)
                else:
                    filename = info[b'name'].decode('utf-8')
                    files.append(filename)

            return files

        except Exception as e:
            raise Exception(f"Failed to parse torrent data: {str(e)}")
