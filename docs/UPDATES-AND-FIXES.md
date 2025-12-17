# Updates and Fixes

This document tracks significant changes, bug fixes, and improvements made to the Sonarr Extension Filter application.

---

## 2025-12-17: Dashboard Statistics and Blocklist Fixes

### Issues Identified

1. **Dashboard Not Updating Statistics**
   - Statistics were being incremented in memory but not persisted to disk
   - The `statistics.json` file was not being created
   - Dashboard showed 0 for all statistics even after processing torrents

2. **Torrents Not Being Removed from qBittorrent**
   - Timing issue: Sonarr processes items and removes them from queue before webhook completes
   - By the time the app checked the queue (after waiting for torrent to appear), the queue was empty
   - Queue ID was unavailable, preventing removal via Sonarr API

3. **Blocklist Not Working**
   - Items with blocked extensions were not being added to Sonarr's blocklist
   - Initial attempt to use `POST /api/v3/blocklist` endpoint resulted in 405 Method Not Allowed errors
   - Sonarr v3 API doesn't support directly adding items to blocklist

### Root Causes

1. **Silent Error Handling in Statistics**
   - `app/stats.py` was catching all exceptions and silently failing when saving statistics
   - No visibility into why saves were failing
   - Made debugging impossible

2. **Timing Issues with Sonarr Webhooks**
   - Sonarr sends "Grab" webhook AFTER processing the item
   - Queue is already empty by the time webhook arrives
   - Traditional queue-based removal approach doesn't work

3. **API Limitations**
   - Sonarr v3 API doesn't support POST to `/blocklist` endpoint
   - Only way to blocklist is via queue removal or marking history as failed

### Fixes Applied

#### 1. Statistics Persistence Fix (`app/stats.py`)

**Changes:**
- Improved error handling to print errors to stderr instead of silently failing
- Added diagnostic logging to show statistics file path on initialization
- Fixed directory creation logic to handle edge cases (empty dirname)
- Added error logging for both save and load operations

**Code Changes:**
```python
# Before: Silent failure
except Exception as e:
    pass

# After: Visible errors for debugging
except Exception as e:
    import sys
    print(f"Error saving statistics to {self.stats_file}: {e}", file=sys.stderr)
```

**Files Modified:**
- `app/stats.py:70-96` - Enhanced `_save_stats()` with better error handling
- `app/stats.py:16-57` - Added diagnostic logging in `__init__()`
- `app/stats.py:59-76` - Improved `_load_stats()` error reporting

#### 2. Direct Download Client Removal (`app/webhook_handler.py`)

**Changes:**
- Added fallback to remove torrents directly from qBittorrent when queue is empty
- Captures queue_id immediately when webhook arrives (before waiting for torrent)
- If queue removal fails, removes torrent directly from download client

**Logic Flow:**
1. Webhook arrives → capture queue_id immediately
2. Wait for torrent to appear in qBittorrent
3. Check for blocked files
4. Try to remove via Sonarr queue (if queue_id exists)
5. **Fallback:** Remove directly from qBittorrent if queue is empty

**Files Modified:**
- `app/webhook_handler.py:97-107` - Capture queue_id before torrent wait
- `app/webhook_handler.py:151-203` - Added direct download client removal fallback

#### 3. History-Based Blocklisting (`app/sonarr/api.py` & `app/webhook_handler.py`)

**Changes:**
- Implemented blocklisting via Sonarr's history API
- Uses `POST /api/v3/history/failed/{id}` to mark items as failed and add to blocklist
- Queries history by download ID to find the grabbed event

**New API Methods:**
- `get_history(download_id, event_type)` - Retrieves history records
- `blocklist_by_history_id(history_id)` - Marks history item as failed (adds to blocklist)

**Logic Flow:**
1. Remove torrent from qBittorrent
2. Query Sonarr history API for download_id
3. Find the "grabbed" event in history
4. Mark that history record as failed → automatically adds to blocklist

**Files Modified:**
- `app/sonarr/api.py:128-194` - Added history API methods
- `app/webhook_handler.py:159-183` - Integrated history-based blocklisting

#### 4. Cleanup (`app/sonarr/api.py`)

**Changes:**
- Removed broken `add_to_blocklist()` method that was causing 405 errors
- Method was attempting unsupported API operation

**Files Modified:**
- `app/sonarr/api.py` - Removed lines 128-169 (broken blocklist method)

### Testing Results

After fixes were applied:
- ✅ Torrents are successfully removed from qBittorrent
- ✅ Dashboard statistics update correctly
- ✅ `data/statistics.json` file is created and updated
- ✅ Items are added to Sonarr's blocklist via history API

### Technical Notes

#### Statistics File Location
- Environment variable `STATS_DIR` controls location (default: `/data` in Docker)
- Falls back to `/app/logs`, `logs`, or current directory if `/data` unavailable
- Diagnostic logging shows exact path on startup

#### Sonarr API Limitations
- Cannot directly POST to `/blocklist` endpoint (405 Method Not Allowed)
- Blocklisting only possible via:
  1. Queue removal with `blocklist=true` parameter
  2. Marking history record as failed via `/history/failed/{id}`

#### Webhook Timing
- Sonarr sends "Grab" webhook after processing item
- Queue may be empty by the time webhook is received
- Solution: Capture queue_id early OR use history API as fallback

### Future Improvements

1. **Optimize Timing**
   - Consider using Sonarr's "On Download" webhook instead of "On Grab"
   - May provide better timing for queue-based operations

2. **Statistics Monitoring**
   - Add health check endpoint that verifies statistics file is writable
   - Alert if statistics haven't been updated in X time

3. **Enhanced Logging**
   - Add structured logging for better debugging
   - Include timestamps in statistics for troubleshooting

### Related Issues

- Dashboard updating and blocklist issue (Fixed 2025-12-17)
- 403 error with qBittorrent (Fixed 2025-12-09)

---

## Version History

- **v1.0.0** - Initial release
- **v1.0.1** - Fixed qBittorrent 403 authentication errors
- **v1.0.2** - Fixed dashboard statistics persistence and blocklist functionality
