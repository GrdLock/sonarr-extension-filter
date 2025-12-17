"""
Statistics tracking for the application
"""

from datetime import datetime
from collections import defaultdict
import threading
import json
import os
from pathlib import Path


class Statistics:
    """Track application statistics with persistent storage"""

    def __init__(self, stats_file=None):
        self.lock = threading.Lock()

        # Default stats file location
        if stats_file is None:
            # Try multiple locations in order of preference
            stats_dir = os.getenv('STATS_DIR')
            if not stats_dir:
                # Check for common directories
                for directory in ['/data', '/app/logs', 'logs', '.']:
                    if os.path.isdir(directory) or directory == '.':
                        stats_dir = directory
                        break

            try:
                os.makedirs(stats_dir, exist_ok=True)
            except Exception as e:
                # Fallback to current directory if we can't create the stats dir
                import sys
                print(f"Warning: Could not create stats directory {stats_dir}: {e}. Using current directory.", file=sys.stderr)
                stats_dir = '.'

            self.stats_file = os.path.join(stats_dir, 'statistics.json')
        else:
            self.stats_file = stats_file

        # Print stats file location for debugging
        import sys
        print(f"Statistics file location: {os.path.abspath(self.stats_file)}", file=sys.stderr)

        # Initialize with default values
        self.start_time = datetime.now()
        self.total_processed = 0
        self.total_blocked = 0
        self.total_errors = 0
        self.blocked_files = []
        self.extension_counts = defaultdict(int)
        self.recent_activity = []
        self.max_recent = 50

        # Load existing statistics if available
        self._load_stats()

    def _load_stats(self):
        """Load statistics from persistent storage"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)

                self.start_time = datetime.fromisoformat(data.get('start_time', datetime.now().isoformat()))
                self.total_processed = data.get('total_processed', 0)
                self.total_blocked = data.get('total_blocked', 0)
                self.total_errors = data.get('total_errors', 0)
                self.extension_counts = defaultdict(int, data.get('extension_counts', {}))
                self.recent_activity = data.get('recent_activity', [])
            # else: file doesn't exist yet, will be created on first save
        except Exception as e:
            # If loading fails, print error for debugging
            import sys
            print(f"Error loading statistics from {self.stats_file}: {e}", file=sys.stderr)

    def _save_stats(self):
        """Save statistics to persistent storage"""
        try:
            data = {
                'start_time': self.start_time.isoformat(),
                'total_processed': self.total_processed,
                'total_blocked': self.total_blocked,
                'total_errors': self.total_errors,
                'extension_counts': dict(self.extension_counts),
                'recent_activity': self.recent_activity
            }

            # Ensure directory exists
            stats_dir = os.path.dirname(self.stats_file)
            if stats_dir:  # Only create if dirname is not empty
                os.makedirs(stats_dir, exist_ok=True)

            # Write atomically
            temp_file = f"{self.stats_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            os.replace(temp_file, self.stats_file)

        except Exception as e:
            # If saving fails, print error for debugging
            import sys
            print(f"Error saving statistics to {self.stats_file}: {e}", file=sys.stderr)

    def increment_processed(self):
        """Increment processed count"""
        with self.lock:
            self.total_processed += 1
            self._save_stats()

    def increment_blocked(self):
        """Increment blocked count"""
        with self.lock:
            self.total_blocked += 1
            self._save_stats()

    def increment_errors(self):
        """Increment error count"""
        with self.lock:
            self.total_errors += 1
            self._save_stats()

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

            self._save_stats()

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

            self._save_stats()

    def get_stats(self):
        """
        Get current statistics

        Returns:
            dict: Statistics dictionary
        """
        with self.lock:
            # Reload from disk to get latest data
            self._load_stats()

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
            self._save_stats()
