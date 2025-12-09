"""
Extension checking logic
"""

import os


class ExtensionChecker:
    """Check files for blocked extensions"""

    def __init__(self, filtering_config, logger):
        self.config = filtering_config
        self.logger = logger

        # Normalize extensions (ensure they start with '.')
        self.blocked_extensions = [
            ext if ext.startswith('.') else f'.{ext}'
            for ext in filtering_config.blocked_extensions
        ]

        # Convert to lowercase for case-insensitive comparison
        self.blocked_extensions = [ext.lower() for ext in self.blocked_extensions]

        self.logger.info(f"Blocking extensions: {', '.join(self.blocked_extensions)}")

    def check_files(self, file_list):
        """
        Check a list of files for blocked extensions

        Args:
            file_list: List of file paths or names

        Returns:
            list: List of files with blocked extensions
        """
        blocked_files = []

        for file_path in file_list:
            # Extract extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()

            # Check if extension is blocked
            if ext in self.blocked_extensions:
                blocked_files.append(file_path)
                self.logger.debug(f"Blocked file found: {file_path} (extension: {ext})")

        return blocked_files

    def is_extension_blocked(self, filename):
        """
        Check if a single file has a blocked extension

        Args:
            filename: Name or path of file

        Returns:
            bool: True if extension is blocked
        """
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        return ext in self.blocked_extensions
