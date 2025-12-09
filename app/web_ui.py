"""
Web UI routes and handlers
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
import yaml
import os
import subprocess


def create_web_ui_app(config, logger, stats):
    """
    Create Web UI Flask application

    Args:
        config: Application configuration
        logger: Logger instance
        stats: Statistics instance

    Returns:
        Flask app instance
    """
    app = Flask(__name__)
    app.secret_key = config.security.session_secret

    # Store references
    app.config['APP_CONFIG'] = config
    app.config['APP_LOGGER'] = logger
    app.config['APP_STATS'] = stats

    # Authentication decorator
    def require_auth(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if config.webui.username and config.webui.password:
                if not session.get('authenticated'):
                    return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

    @app.route('/')
    @require_auth
    def dashboard():
        """Dashboard page"""
        return render_template('dashboard.html', config=config, stats=stats.get_stats())

    @app.route('/config')
    @require_auth
    def config_page():
        """Configuration page"""
        return render_template('config.html', config=config)

    @app.route('/logs')
    @require_auth
    def logs_page():
        """Logs page"""
        return render_template('logs.html', config=config)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login page"""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            if (username == config.webui.username and
                    password == config.webui.password):
                session['authenticated'] = True
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error='Invalid credentials')

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        """Logout"""
        session.pop('authenticated', None)
        return redirect(url_for('login'))

    # API Endpoints

    @app.route('/api/stats')
    @require_auth
    def get_stats():
        """Get statistics"""
        return jsonify(stats.get_stats())

    @app.route('/api/config', methods=['GET'])
    @require_auth
    def get_config():
        """Get current configuration"""
        return jsonify({
            'sonarr': {
                'url': config.sonarr.url,
                'api_key': config.sonarr.api_key[:10] + '...' if config.sonarr.api_key else ''
            },
            'download_client': {
                'type': config.download_client.type,
                'url': config.download_client.url,
                'username': config.download_client.username
            },
            'filtering': {
                'blocked_extensions': config.filtering.blocked_extensions,
                'action': config.filtering.action
            },
            'logging': {
                'level': config.logging.level
            }
        })

    @app.route('/api/config/save', methods=['POST'])
    @require_auth
    def save_config():
        """Save configuration"""
        try:
            data = request.get_json()

            # Load existing config file
            config_file = os.getenv('CONFIG_FILE', '/config/config.yaml')

            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f) or {}
            else:
                config_data = {}

            # Update Sonarr configuration
            if 'sonarr_url' in data:
                if 'sonarr' not in config_data:
                    config_data['sonarr'] = {}
                config_data['sonarr']['url'] = data['sonarr_url']

            if 'sonarr_api_key' in data:
                if 'sonarr' not in config_data:
                    config_data['sonarr'] = {}
                config_data['sonarr']['api_key'] = data['sonarr_api_key']

            # Update download client configuration
            if 'download_client_type' in data:
                if 'download_client' not in config_data:
                    config_data['download_client'] = {}
                config_data['download_client']['type'] = data['download_client_type']

            if 'download_client_url' in data:
                if 'download_client' not in config_data:
                    config_data['download_client'] = {}
                config_data['download_client']['url'] = data['download_client_url']

            if 'download_client_username' in data:
                if 'download_client' not in config_data:
                    config_data['download_client'] = {}
                config_data['download_client']['username'] = data['download_client_username']

            if 'download_client_password' in data:
                if 'download_client' not in config_data:
                    config_data['download_client'] = {}
                config_data['download_client']['password'] = data['download_client_password']

            if 'download_client_rpc_path' in data:
                if 'download_client' not in config_data:
                    config_data['download_client'] = {}
                # Only save if not empty (optional field)
                if data['download_client_rpc_path']:
                    config_data['download_client']['rpc_path'] = data['download_client_rpc_path']
                elif 'rpc_path' in config_data.get('download_client', {}):
                    # Remove if empty
                    del config_data['download_client']['rpc_path']

            # Update filtering configuration
            if 'blocked_extensions' in data:
                if 'filtering' not in config_data:
                    config_data['filtering'] = {}
                config_data['filtering']['blocked_extensions'] = data['blocked_extensions']

            if 'action' in data:
                if 'filtering' not in config_data:
                    config_data['filtering'] = {}
                config_data['filtering']['action'] = data['action']

            # Update Web UI configuration
            if 'webui_username' in data:
                if 'webui' not in config_data:
                    config_data['webui'] = {}
                # Only save if not empty (optional - disables auth if empty)
                if data['webui_username']:
                    config_data['webui']['username'] = data['webui_username']
                elif 'username' in config_data.get('webui', {}):
                    # Remove if empty
                    del config_data['webui']['username']

            if 'webui_password' in data:
                if 'webui' not in config_data:
                    config_data['webui'] = {}
                # Only save if not empty (optional - disables auth if empty)
                if data['webui_password']:
                    config_data['webui']['password'] = data['webui_password']
                elif 'password' in config_data.get('webui', {}):
                    # Remove if empty
                    del config_data['webui']['password']

            # Update logging configuration
            if 'log_level' in data:
                if 'logging' not in config_data:
                    config_data['logging'] = {}
                config_data['logging']['level'] = data['log_level']

            # Write config file
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)

            logger.info("Configuration saved successfully")

            return jsonify({
                'status': 'success',
                'message': 'Configuration saved. Restart required to apply changes.'
            })

        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/logs')
    @require_auth
    def get_logs():
        """Get log file contents using tail command to avoid memory issues"""
        try:
            lines = int(request.args.get('lines', 100))
            log_file = config.logging.file

            if not os.path.exists(log_file):
                return jsonify({'logs': [], 'total_lines': 0})

            # Use tail command for efficient reading
            result = subprocess.run(
                ['tail', '-n', str(lines), log_file],
                capture_output=True,
                text=True,
                timeout=5
            )

            log_lines = result.stdout.split('\n') if result.stdout else []

            # Get total line count
            wc_result = subprocess.run(
                ['wc', '-l', log_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            total_lines = int(wc_result.stdout.split()[0]) if wc_result.stdout else 0

            return jsonify({
                'logs': log_lines,
                'total_lines': total_lines
            })

        except subprocess.TimeoutExpired:
            logger.error("Timeout reading log file")
            return jsonify({'error': 'Timeout reading log file'}), 500
        except Exception as e:
            logger.error(f"Failed to read logs: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/test/sonarr')
    @require_auth
    def test_sonarr():
        """Test Sonarr connection"""
        try:
            from app.sonarr.api import SonarrAPI
            sonarr_api = SonarrAPI(config.sonarr, logger)

            # Try to get queue
            queue = sonarr_api.get_queue()

            return jsonify({
                'status': 'success',
                'message': f'Connected to Sonarr. Queue has {len(queue)} items.'
            })

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/test/download-client')
    @require_auth
    def test_download_client():
        """Test download client connection"""
        try:
            from app.clients.qbittorrent import QBittorrentClient
            from app.clients.transmission import TransmissionClient
            from app.clients.deluge import DelugeClient

            client_type = config.download_client.type.lower()

            if client_type == 'qbittorrent':
                client = QBittorrentClient(config.download_client, logger)
            elif client_type == 'transmission':
                client = TransmissionClient(config.download_client, logger)
            elif client_type == 'deluge':
                client = DelugeClient(config.download_client, logger)
            else:
                raise ValueError(f"Unsupported client: {client_type}")

            return jsonify({
                'status': 'success',
                'message': f'Connected to {client_type.title()} successfully.'
            })

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    return app


if __name__ == '__main__':
    # For standalone testing only
    from app.config import Config
    from app.stats import Statistics
    from app.utils.logger import setup_logger

    config = Config()
    logger = setup_logger(config)
    stats = Statistics()

    app = create_web_ui_app(config, logger, stats)
    app.run(host='0.0.0.0', port=config.webui.port, debug=True)
