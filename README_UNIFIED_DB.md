# 🔄 Unified Database Configuration

## Environment Variables

Ensure these variables are set in your `.env` file:

```bash
# Database Configuration
DB_PATH=glow_nest.db

# CORS Origins (comma-separated)
ALLOWED_ORIGINS=http://localhost:5173,https://*.builder.my,https://*.fly.dev

# API Base URL
API_BASE_URL=http://localhost:8080

# Server Port (optional, defaults to 8080)
PORT=8080
```

## Database Schema Changes

### ✅ Unified Database Path
- **Node.js**: Uses `process.env.DB_PATH` in `server/database.ts`
- **Python**: Uses `cli.db_config.get_db_path()` in all modules
- **Default**: `glow_nest.db` in project root

### ✅ Unified Table Schema
- **Table**: `street_districts` (migrated from `street_district_map`)
- **Migration**: Automatic in `cli/utils.py`
- **Columns**: `id`, `street`, `district`, `created_at`

### ✅ Fixed Property Insertion
- **Fixed**: Removed `is_promoted` field from insert
- **Fixed**: Added missing comma in values tuple
- **Schema**: 11 fields, 11 placeholders

## Development Ports

- **Vite Frontend**: http://localhost:5173
- **FastAPI Backend**: http://localhost:8080

## SSE Headers

All Server-Sent Events endpoints now use:
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

## CORS Configuration

Origins are read from `ALLOWED_ORIGINS` environment variable:
- Development: `http://localhost:5173`
- Production: `https://*.fly.dev,https://*.builder.my`

## Testing

### Local Testing
```bash
# Build frontend
npm run build

# Run smoke test
npm run selftest

# Start Python API
python -m cli.server

# Start Node.js dev server
npm run dev
```

### Expected Results
- ✅ Health endpoint: `{"status": "ok"}`
- ✅ Database unified: One path for all modules
- ✅ Street districts: Migrated schema
- ✅ Property insert: Fixed placeholders
- ✅ SSE: Proper headers
- ✅ CORS: Environment-based origins

## Migration Notes

### From Old Schema
- `street_district_map` → `street_districts` (automatic migration)
- `data/olx_offers.sqlite` → `glow_nest.db` (set in .env)

### Fixed Issues
- ❌ Property insert: 12 values, 11 placeholders → ✅ 11 values, 11 placeholders
- ❌ SSE headers: `text/plain` → ✅ `text/event-stream`
- ❌ Hardcoded ports: 8080 conflict → ✅ Vite:5173, API:8080
- ❌ UTF-8 artifacts: Г��ушевського → ✅ Грушевського
