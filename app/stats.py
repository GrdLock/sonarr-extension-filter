"""
Statistics tracking for the application
"""

from datetime import datetime
from collections import defaultdict
import threading


class Statistics:
    """Track application statistics"""

    def __init__(self):
        self.lock = threading.Lock()
        self.start_time = datetime.now()
        self.total_processed = 0
        self.total_blocked = 0
        self.total_errors = 0
        self.blocked_files = []
        self.extension_counts = defaultdict(int)
        self.recent_activity = []
        self.max_recent = 50

    def increment_processed(self):
        """Increment processed count"""
        with self.lock:
            self.total_processed += 1

    def increment_blocked(self):
        """Increment blocked count"""
        with self.lock:
            self.total_blocked += 1

    def increment_errors(self):
        """Increment error count"""
        with self.lock:
            self.total_errors += 1

    def add_blocked_file(self, files):
        """
        Add blocked files to tracking

        Args:
            files: List of blocked file paths
        """
        with self.lock:
            for file_path in files:
                ext = file_path.split('.')[-1].lower() if '.' in file_path else 'unknown'
                self.extension_counts[f'.{ext}'] += 1

                # Add to recent activity
                self.recent_activity.insert(0, {
                    'time': datetime.now().isoformat(),
                    'type': 'blocked',
                    'file': file_path
                })

                # Limit recent activity list size
                if len(self.recent_activity) > self.max_recent:
                    self.recent_activity = self.recent_activity[:self.max_recent]

    def add_activity(self, activity_type, message):
        """
        Add general activity

        Args:
            activity_type: Type of activity
            message: Activity message
        """
        with self.lock:
            self.recent_activity.insert(0, {
                'time': datetime.now().isoformat(),
                'type': activity_type,
                'message': message
            })

            if len(self.recent_activity) > self.max_recent:
                self.recent_activity = self.recent_activity[:self.max_recent]

    def get_stats(self):
        """
        Get current statistics

        Returns:
            dict: Statistics dictionary
        """
        with self.lock:
            uptime = datetime.now() - self.start_time

            return {
                'uptime_seconds': int(uptime.total_seconds()),
                'uptime_str': str(uptime).split('.')[0],
                'total_processed': self.total_processed,
                'total_blocked': self.total_blocked,
                'total_errors': self.total_errors,
                'extension_counts': dict(self.extension_counts),
                'recent_activity': self.recent_activity[:20]
            }

    def reset_stats(self):
        """Reset all statistics"""
        with self.lock:
            self.start_time = datetime.now()
            self.total_processed = 0
            self.total_blocked = 0
            self.total_errors = 0
            self.blocked_files = []
            self.extension_counts = defaultdict(int)
            self.recent_activity = []
