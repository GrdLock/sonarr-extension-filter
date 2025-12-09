"""
Configuration management for the application
"""

import os
import yaml
from typing import List
from dataclasses import dataclass


@dataclass
class SonarrConfig:
    url: str
    api_key: str


@dataclass
class DownloadClientConfig:
    type: str
    url: str
    username: str
    password: str
    rpc_path: str = None


@dataclass
class FilteringConfig:
    blocked_extensions: List[str]
    action: str
    allowed_extensions: List[str] = None


@dataclass
class ServerConfig:
    host: str
    port: int
    debug: bool


@dataclass
class WebUIConfig:
    enabled: bool
    port: int
    username: str = None
    password: str = None


@dataclass
class SecurityConfig:
    session_secret: str
    webhook_rate_limit: str
    max_payload_size: int


@dataclass
class LoggingConfig:
    level: str
    file: str
    max_bytes: int
    backup_count: int
    console: bool


class Config:
    """Main configuration class"""

    def __init__(self):
        self.sonarr = None
        self.download_client = None
        self.filtering = None
        self.server = None
        self.webui = None
        self.security = None
        self.logging = None

        # Load configuration
        self._load_config()

    def _load_config(self):
        """Load configuration from file or environment variables"""

        # Try to load from config file first
        config_file = os.getenv('CONFIG_FILE', '/config/config.yaml')

        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
        else:
            # Use environment variables
            config_data = self._load_from_env()

        # Parse configuration sections
        self.sonarr = SonarrConfig(
            url=config_data.get('sonarr', {}).get('url', os.getenv('SONARR_URL', 'http://localhost:8989')),
            api_key=config_data.get('sonarr', {}).get('api_key', os.getenv('SONARR_API_KEY', ''))
        )

        self.download_client = DownloadClientConfig(
            type=config_data.get('download_client', {}).get('type', os.getenv('DOWNLOAD_CLIENT_TYPE', 'qbittorrent')),
            url=config_data.get('download_client', {}).get('url', os.getenv('DOWNLOAD_CLIENT_URL', 'http://localhost:8080')),
            username=config_data.get('download_client', {}).get('username', os.getenv('DOWNLOAD_CLIENT_USERNAME', 'admin')),
            password=config_data.get('download_client', {}).get('password', os.getenv('DOWNLOAD_CLIENT_PASSWORD', '')),
            rpc_path=config_data.get('download_client', {}).get('rpc_path', os.getenv('DOWNLOAD_CLIENT_RPC_PATH'))
        )

        # Parse blocked extensions from env or config
        blocked_ext_env = os.getenv('BLOCKED_EXTENSIONS', '')
        if blocked_ext_env:
            blocked_extensions = [ext.strip() for ext in blocked_ext_env.split(',')]
        else:
            blocked_extensions = config_data.get('filtering', {}).get('blocked_extensions', ['.exe', '.msi', '.bat'])

        self.filtering = FilteringConfig(
            blocked_extensions=blocked_extensions,
            action=config_data.get('filtering', {}).get('action', os.getenv('ACTION_ON_MATCH', 'remove_and_blocklist')),
            allowed_extensions=config_data.get('filtering', {}).get('allowed_extensions', [])
        )

        self.server = ServerConfig(
            host=config_data.get('server', {}).get('host', os.getenv('SERVER_HOST', '0.0.0.0')),
            port=int(config_data.get('server', {}).get('port', os.getenv('SERVER_PORT', 9090))),
            debug=config_data.get('server', {}).get('debug', os.getenv('DEBUG', 'false').lower() == 'true')
        )

        self.webui = WebUIConfig(
            enabled=config_data.get('webui', {}).get('enabled', os.getenv('WEB_UI_ENABLED', 'true').lower() == 'true'),
            port=int(config_data.get('webui', {}).get('port', os.getenv('WEB_UI_PORT', 9091))),
            username=config_data.get('webui', {}).get('username', os.getenv('WEB_UI_USERNAME', '')),
            password=config_data.get('webui', {}).get('password', os.getenv('WEB_UI_PASSWORD', ''))
        )

        # Security configuration with defaults
        self.security = SecurityConfig(
            session_secret=config_data.get('security', {}).get('session_secret',
                                                               os.getenv('SESSION_SECRET', os.urandom(32).hex())),
            webhook_rate_limit=config_data.get('security', {}).get('webhook_rate_limit',
                                                                    os.getenv('WEBHOOK_RATE_LIMIT', '60/hour')),
            max_payload_size=config_data.get('security', {}).get('max_payload_size',
                                                                  int(os.getenv('MAX_PAYLOAD_SIZE', 1048576)))
        )

        self.logging = LoggingConfig(
            level=config_data.get('logging', {}).get('level', os.getenv('LOG_LEVEL', 'INFO')),
            file=config_data.get('logging', {}).get('file', 'logs/sonarr-extension-filter.log'),
            max_bytes=config_data.get('logging', {}).get('max_bytes', 10485760),
            backup_count=config_data.get('logging', {}).get('backup_count', 5),
            console=config_data.get('logging', {}).get('console', True)
        )

    def _load_from_env(self):
        """Create config structure from environment variables"""
        return {
            'sonarr': {},
            'download_client': {},
            'filtering': {},
            'server': {},
            'webui': {},
            'security': {},
            'logging': {}
        }
