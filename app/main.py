"""
Main Flask application entry point
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.config import Config
from app.webhook_handler import WebhookHandler
from app.stats import Statistics
from app.utils.logger import setup_logger
import logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load configuration
config = Config()

# Configure app
app.config['MAX_CONTENT_LENGTH'] = config.security.max_payload_size
app.secret_key = config.security.session_secret

# Setup logging
logger = setup_logger(config)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Initialize webhook handler
webhook_handler = WebhookHandler(config, logger)

# Initialize statistics
stats = Statistics()


@app.route('/webhook', methods=['POST'])
@limiter.limit(config.security.webhook_rate_limit)
def handle_webhook():
    """
    Webhook endpoint for Sonarr notifications
    """
    try:
        # Get JSON payload from request
        payload = request.get_json()

        if not payload:
            logger.warning("Received webhook with no payload")
            return jsonify({"status": "error", "message": "No payload received"}), 400

        # Validate payload has required fields
        if not isinstance(payload, dict):
            logger.warning("Invalid payload format")
            return jsonify({"status": "error", "message": "Invalid payload format"}), 400

        # Log the event type
        event_type = payload.get('eventType', 'unknown')
        logger.info(f"Received webhook: {event_type}")

        # Only process 'Grab' events
        if event_type == 'Grab':
            result = webhook_handler.process_grab_event(payload)

            # Update statistics
            if result.get('status') == 'removed':
                stats.increment_blocked()
                stats.add_blocked_file(result.get('blocked_files', []))
            elif result.get('status') == 'clean':
                stats.increment_processed()

            return jsonify(result), 200
        else:
            logger.debug(f"Ignoring event type: {event_type}")
            return jsonify({"status": "ignored", "message": f"Event type '{event_type}' not processed"}), 200

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        stats.increment_errors()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "service": "sonarr-extension-filter",
        "webhook_port": config.server.port,
        "webui_port": config.webui.port if config.webui.enabled else None,
        "webui_enabled": config.webui.enabled
    }), 200


@app.route('/', methods=['GET'])
def index():
    """
    Root endpoint with basic info
    """
    return jsonify({
        "service": "Sonarr Extension Filter",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health",
            "webui": f"http://localhost:{config.webui.port}" if config.webui.enabled else "disabled"
        }
    }), 200


# Export stats for web UI
def get_app_stats():
    """Get application statistics"""
    return stats


# Export config for web UI
def get_app_config():
    """Get application configuration"""
    return config


# Export logger for web UI
def get_app_logger():
    """Get application logger"""
    return logger


if __name__ == '__main__':
    # Development mode only - use gunicorn in production
    logger.warning("Running in development mode. Use gunicorn for production.")
    app.run(
        host=config.server.host,
        port=config.server.port,
        debug=config.server.debug
    )
