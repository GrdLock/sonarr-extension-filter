# Sonarr Extension Filter

A Python-based web service that automatically monitors Sonarr downloads and removes torrents containing files with unwanted extensions (e.g., `.exe`, `.msi`, `.bat`). This prevents potentially malicious or unwanted files from being downloaded.

NOTE: I have only personally tested this on MacOS with qBittorrent. It's designed to run as a Docker container, so it theoretically should work fine on Windows or Linux as well. And I've included support for Transmission and Deluge, however have not actually tested this functionality.

![alt text](https://raw.githubusercontent.com/GrdLock/sonarr-extension-filter/refs/heads/main/app/homepage.png "Main Screen")

## Features

- 🔍 Automatically inspects torrent file lists when Sonarr grabs a download
- 🚫 Removes torrents containing blocked file extensions
- 📋 Supports multiple download clients (qBittorrent, Transmission, Deluge)
- 🐳 Docker-ready with easy deployment
- ⚙️ Configurable via YAML file, environment variables, or Web UI
- 📊 Comprehensive logging of all actions
- 🔒 Optional blocklist integration to prevent re-downloads
- 🌐 Web UI for easy configuration and monitoring
  - Real-time dashboard with statistics
  - Sonarr and download client configuration
  - Extension filtering management (blocked/allowed)
  - Live log viewer with search and filtering
  - Connection testing tools
  - Optional password authentication

## Architecture

```
┌─────────────┐
│   Sonarr    │  Grabs torrent from indexer
└──────┬──────┘
       │
       │ Webhook (HTTP POST)
       │ On Grab event
       ▼
┌─────────────────────────────────────┐
│  Extension Filter Service           │
│  (Python Flask - Port 9090)         │
│                                     │
│  1. Receives webhook notification   │
│  2. Extracts download_id            │
│  3. Queries download client         │
│  4. Retrieves .torrent file         │
│  5. Parses file list                │
│  6. Checks for blocked extensions   │
│  7. Removes via Sonarr API if found │
└──────┬─────────────┬────────────────┘
       │             │
       │             │ API Calls
       ▼             ▼
┌─────────────┐ ┌──────────────────┐
│   Sonarr    │ │ Download Client  │
│   API       │ │ (qBit/Trans/Del) │
└─────────────┘ └──────────────────┘
```

## Prerequisites

- Docker and Docker Compose (recommended)
- OR Python 3.11+ with pip
- Sonarr instance (v3 or v4)
- Download client (qBittorrent, Transmission, or Deluge)

## Quick Start

### 1. Clone or Download

```bash
git clone <your-repo-url>
cd sonarr-extension-filter
```

### 2. Configure

Copy the example configuration file and edit it with your settings:

```bash
cp config.yaml.example config.yaml
nano config.yaml
```

Update the following values:
- `sonarr.url` - Your Sonarr URL (or configure via Web UI after startup)
- `sonarr.api_key` - Your Sonarr API key (Settings → General → Security)
- `download_client.*` - Your download client details (or configure via Web UI)
- `filtering.blocked_extensions` - Extensions to block
- `security.session_secret` - Random string for session encryption (generate with `openssl rand -hex 32`)
- `webui.username` and `webui.password` - Web UI credentials (leave empty to disable auth)

**Tip:** You can configure most settings through the Web UI after starting the service. Only `security.session_secret` must be set in the config file initially.

### 3. Start the Service

#### Option A: Docker (Recommended)

```bash
# Create logs directory
mkdir -p logs

# Start with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f
```

#### Option B: Manual Python Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the webhook service
python -m app.main &

# Run the Web UI (in another terminal or tmux session)
python -m app.webui_app
```

### 4. Configure Sonarr Webhook

1. Open Sonarr web interface
2. Go to **Settings → Connect**
3. Click the **+** button
4. Select **Webhook**
5. Configure:
   - **Name**: Extension Filter
   - **URL**: `http://sonarr-extension-filter:9090/webhook` (if in same Docker network)
     - Or `http://localhost:9090/webhook` (if running locally)
   - **Method**: POST
   - **Triggers**: Check **On Grab**
6. Click **Test** to verify connection
7. Click **Save**

### 5. Access Web UI

Open your browser and navigate to:

```
http://localhost:9091
```

Default credentials (if authentication is enabled):
- Username: `admin`
- Password: `changeme` (change this in config.yaml!)

## Configuration

### Configuration File (config.yaml)

The configuration file supports all settings. See `config.yaml.example` for a complete example.

### Environment Variables

You can override configuration with environment variables:

```bash
# Sonarr
SONARR_URL=http://localhost:8989
SONARR_API_KEY=your_api_key

# Download Client
DOWNLOAD_CLIENT_TYPE=qbittorrent
DOWNLOAD_CLIENT_URL=http://localhost:8080
DOWNLOAD_CLIENT_USERNAME=admin
DOWNLOAD_CLIENT_PASSWORD=adminpass

# Filtering
BLOCKED_EXTENSIONS=.exe,.msi,.bat,.com
ACTION_ON_MATCH=remove_and_blocklist

# Security
SESSION_SECRET=your-random-secret-key

# Web UI
WEB_UI_ENABLED=true
WEB_UI_PORT=9091
WEB_UI_USERNAME=admin
WEB_UI_PASSWORD=changeme

# Logging
LOG_LEVEL=INFO
```

### Extension Filtering

**Blocked Extensions**

Default blocked extensions include:
- `.exe`, `.msi`, `.bat`, `.com`, `.cmd`, `.scr` - Windows executables
- `.vbs`, `.vbe`, `.js`, `.jse`, `.wsf`, `.wsh` - Scripts
- `.ps1`, `.psm1`, `.psd1` - PowerShell
- `.dll`, `.sys` - System files
- `.rar`, `.iso` - Other common fake TV torrents

You can customize this list in the configuration or via the Web UI.

Example in config.yaml:
```yaml
filtering:
  blocked_extensions:
    - .exe
    - .msi
    - .bat
  action: remove_and_blocklist
```

## Web UI Usage

### Dashboard

The dashboard provides:
- **Statistics**: Processed downloads, blocked files, errors, uptime
- **Blocked Extensions Chart**: Count of each blocked extension type
- **Current Configuration**: Active settings overview
- **Recent Activity**: Real-time feed of blocked files

### Configuration Page

The configuration page allows you to edit all major settings through the Web UI:

**Sonarr Configuration:**
- Sonarr URL
- API Key (with show/hide toggle)

**Download Client Configuration:**
- Client type (qBittorrent, Transmission, Deluge)
- Client URL
- Username and password (with show/hide toggle)
- RPC path (for Transmission/Deluge)

**Extension Filtering:**
- Blocked extensions list
- Action on match (remove or remove and blocklist)

**Web UI Security:**
- Web UI username and password (leave empty to disable authentication)

**Logging:**
- Log level (DEBUG, INFO, WARNING, ERROR)

**Connection Testing:**
- Test Sonarr connection button
- Test download client connection button

All changes are saved to config.yaml and require a service restart to take effect.

### Logs Page

- Real-time log viewing with color-coding
- Search functionality
- Adjustable line count (50, 100, 250, 500, 1000)
- Auto-refresh toggle
- Download logs feature

## Testing

### Test the Service

```bash
# Check health endpoint
curl http://localhost:9090/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "sonarr-extension-filter"
}
```

### Test Webhook Manually

```bash
curl -X POST http://localhost:9090/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "Grab",
    "series": {"title": "Test Series"},
    "release": {"title": "Test.Release.1080p"},
    "downloadId": "test123"
  }'
```

### Test in Sonarr

1. Go to **Settings → Connect** in Sonarr
2. Find your webhook configuration
3. Click **Test**
4. Check the logs for confirmation

## Troubleshooting

### Webhook not receiving requests

**Solution:**
1. Check firewall rules
2. Verify URL in Sonarr webhook settings
3. Check Docker network connectivity
4. Test with `curl` command

### Can't retrieve torrent data

**Possible causes:**
- Download client not accessible
- Wrong credentials
- Torrent not yet added

**Solution:**
The service uses exponential backoff with 3 retries (2s, 4s, 8s). If it still fails, check download client logs.

### Service crashes on startup

**If service still crashes, check:**
1. Configuration file syntax (YAML format)
2. API keys are correct
3. All required fields in config
4. Docker logs for error details: `docker-compose logs`

### Web UI not accessible

**Check:**
1. Port 9091 is not blocked by firewall
2. Service is running: `docker-compose ps`
3. Check logs: `docker-compose logs webui`

### Docker networking issues (Connection Refused errors)

If you see errors like "Connection refused" when the service tries to reach Sonarr or your download client:

**Problem:** Using `localhost` in config.yaml when running in Docker won't work because the container treats `localhost` as itself, not the host machine.

**Solutions:**
1. **If Sonarr/download client are on the host machine:**
   - Use `host.docker.internal` instead of `localhost` (Docker Desktop)
   - Or use your host machine's IP address (e.g., `192.168.1.100`)

2. **If Sonarr/download client are in Docker containers:**
   - Add them to the same Docker network as the extension filter
   - Use the container names as hostnames
   - Example: `http://sonarr:8989` instead of `http://localhost:8989`

3. **Custom Docker network:**
   - Edit docker-compose.yml and change the network settings:
   ```yaml
   networks:
     arr-network:
       external: true
       name: your_existing_network_name
   ```

## Maintenance

### Updating

```bash
# Docker
docker-compose pull
docker-compose up -d

# Manual
git pull
pip install -r requirements.txt --upgrade
# Restart services
```

### Backup

Important files to backup:
- `config.yaml`
- `logs/` (optional)

### Viewing Logs

```bash
# Docker
docker-compose logs -f

# Manual
tail -f logs/sonarr-extension-filter.log
```

## FAQ

**Q: Will this work with Radarr?**
A: With minor modifications, yes. The webhook structure is similar. But the current build here is designed specifically for Sonarr

**Q: Does this slow down downloads?**
A: Minimal impact - 2-8 second delay to check file list (with retries).

**Q: What happens if the service is down?**
A: Downloads proceed normally. No filtering occurs.

**Q: Can I use multiple instances?**
A: Yes, run multiple Docker containers on different ports.

**Q: Can I disable the Web UI?**
A: Yes! Set `WEB_UI_ENABLED=false` in environment or config.

**Q: Why are there two ports?**
A: Port 9090 is for the Sonarr webhook (API). Port 9091 is for the Web UI. They run independently.

**Q: Can I configure everything through the Web UI?**
A: Yes! All major settings can be edited through the Web UI configuration page, including Sonarr connection, download client settings, blocked/allowed extensions, and authentication.

**Q: What is the "allowed extensions" feature?**
A: It lets you explicitly allow certain file types that you want to keep, like subtitle files (.srt) or NFO files (.nfo), even if they might otherwise be flagged.

**Q: How do I disable Web UI authentication?**
A: Leave both the username and password fields empty in the configuration (either in config.yaml or via the Web UI settings).

**Q: How do I use this with Docker when Sonarr is on my host machine?**
A: In your config.yaml, use `host.docker.internal` instead of `localhost` for the Sonarr URL. Example: `http://host.docker.internal:8989`

## Development

### Project Structure

```
sonarr-extension-filter/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── start.sh
├── config.yaml.example
├── .env.example
├── app/
│   ├── main.py                 # Webhook API
│   ├── webui_app.py            # Web UI entry point
│   ├── config.py               # Configuration
│   ├── webhook_handler.py      # Webhook processing
│   ├── web_ui.py               # Web UI routes
│   ├── stats.py                # Statistics
│   ├── clients/                # Download clients
│   ├── sonarr/                 # Sonarr API
│   ├── utils/                  # Utilities
│   ├── templates/              # HTML templates
│   └── static/                 # CSS/JS
└── logs/
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - Feel free to use and modify

## Support

For issues, questions, or feature requests:
- Create an issue on GitHub
- Check the troubleshooting section above
- Review the FAQ

## Changelog

### Version 1.0.0
- Initial release
- Support for qBittorrent, Transmission, Deluge
- Webhook-based monitoring
- Configurable extension blocking
- Docker support
- Web UI with dashboard, configuration, and logs
  - Full configuration editor for all settings
  - Sonarr connection configuration
  - Download client configuration (type, URL, credentials, RPC path)
  - Blocked and allowed extensions management
  - Web UI authentication settings
  - Connection testing tools
- Rate limiting and security features
- Exponential backoff for torrent retrieval (2s, 4s, 8s delays)
- Lazy initialization for download clients (no crash on startup if client unavailable)
- Comprehensive logging with live viewer
- Session-based authentication with configurable credentials
