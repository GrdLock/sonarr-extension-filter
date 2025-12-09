"""
Web UI WSGI entry point
This file serves as the entry point for the Web UI application running on port 5001
"""

from app.config import Config
from app.stats import Statistics
from app.utils.logger import setup_logger
from app.web_ui import create_web_ui_app

# Initialize configuration
config = Config()

# Setup logging
logger = setup_logger(config)

# Initialize statistics (shared instance would be better, but this works for demo)
stats = Statistics()

# Create the Web UI app
app = create_web_ui_app(config, logger, stats)

if __name__ == '__main__':
    # Development mode
    logger.info(f"Starting Web UI on port {config.webui.port}")
    app.run(
        host=config.server.host,
        port=config.webui.port,
        debug=config.server.debug
    )
