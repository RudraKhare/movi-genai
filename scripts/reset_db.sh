#!/bin/bash
# Reset MOVI database - drops all tables, recreates schema, and seeds data

echo "=========================================="
echo "🔄 MOVI Database Reset Script"
echo "=========================================="

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ Error: DATABASE_URL not set"
    echo "Please set DATABASE_URL in .env.local"
    exit 1
fi

echo ""
echo "⚠️  WARNING: This will delete ALL data in the database!"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Aborted"
    exit 0
fi

echo ""
echo "🗑️  Dropping and recreating schema..."
psql $DATABASE_URL -f migrations/001_init.sql

if [ $? -ne 0 ]; then
    echo "❌ Migration failed!"
    exit 1
fi

echo ""
echo "🌱 Seeding database..."
python scripts/seed_db.py

if [ $? -ne 0 ]; then
    echo "❌ Seeding failed!"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Database reset complete!"
echo "=========================================="
