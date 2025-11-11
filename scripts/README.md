# Scripts Directory

This directory contains utility scripts for the Movi project.

## Available Scripts

### `setup.ps1` (Windows PowerShell)
Initial setup script that:
- Checks Python and Node.js installations
- Creates Python virtual environment
- Installs backend dependencies
- Installs frontend dependencies
- Creates `.env.local` from `.env.example`

**Usage:**
```powershell
.\scripts\setup.ps1
```

## Future Scripts (To be added)

### `seed_db.py` (Day 2)
Populates the database with dummy data for stops, paths, routes, vehicles, drivers, and trips.

### `migrate_db.py` (Day 2)
Runs Alembic database migrations.

### `test_all.sh` / `test_all.ps1`
Runs all tests (backend + frontend).

### `deploy.sh`
Deployment script for production environments.
