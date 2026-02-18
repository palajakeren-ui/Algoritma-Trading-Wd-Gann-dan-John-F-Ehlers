# Docker & Deployment Guide

## Quick Start (Without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python start_production.py
```

---

## Docker Deployment (Optional)

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Basic Deployment

```bash
# Build and run backend only
docker-compose up -d gann-backend

# View logs
docker-compose logs -f gann-backend

# Stop
docker-compose down
```

### Full Deployment (with Redis & Nginx)

```bash
# Start all services
docker-compose --profile full up -d

# Check status
docker-compose ps

# Stop all
docker-compose --profile full down
```

### Development Mode

```bash
docker-compose --profile dev up -d
```

---

## Configuration

### Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env`:
```env
FLASK_ENV=production
FLASK_PORT=5000
MASTER_KEY=your_secure_key_here
TZ=Asia/Jakarta
```

---

## Backup & Restore

### Create Backup

**Windows (PowerShell):**
```powershell
.\scripts\backup.ps1
```

**Python (Cross-platform):**
```bash
python scripts/backup_utility.py create
```

**Linux/Mac:**
```bash
chmod +x scripts/backup.sh
./scripts/backup.sh
```

### List Backups

```bash
python scripts/backup_utility.py list
```

### Restore Backup

**Windows:**
```powershell
.\scripts\restore.ps1 -BackupFile "backups\gann_quant_backup_XXXXXX.zip"
```

**Python:**
```bash
python scripts/backup_utility.py restore backups/gann_quant_backup_XXXXXX.zip
```

---

## Volumes & Data

| Directory | Description |
|-----------|-------------|
| `outputs/` | Trading journal, execution logs |
| `logs/` | Application logs |
| `data/` | Market data cache |
| `vault/` | Encrypted credentials |
| `configs/` | Configuration files |
| `backups/` | Backup archives |

---

## Health Check

```bash
# Check API status
curl http://localhost:5000/api/settings/execution-gate/status
```

---

## Troubleshooting

### Container won't start
```bash
docker-compose logs gann-backend
```

### Permission issues
```bash
# Linux/Mac
sudo chown -R $USER:$USER outputs logs data vault
```

### Port already in use
```bash
# Change port in .env
FLASK_PORT=5001
```
