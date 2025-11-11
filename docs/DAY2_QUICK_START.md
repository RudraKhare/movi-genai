# Day 2: Supabase Database Setup - Quick Start

## 🎯 Objective
Connect Movi backend to Supabase and seed the database with test data.

## ⏱️ Time Required
30-45 minutes

---

## 🚀 Quick Setup (5 Steps)

### Step 1: Get Supabase Credentials (10 min)

1. Go to https://app.supabase.com
2. Create new project: `movi-transport`
3. Save your database password!
4. Copy these 4 values:
   - Project URL
   - anon key  
   - service_role key
   - Database connection string (URI format)

📚 **Detailed guide**: See `docs/SUPABASE_SETUP.md`

---

### Step 2: Configure Environment (2 min)

```bash
# Navigate to backend
cd backend

# Create .env file from template
cp .env.template .env

# Edit .env and paste your credentials
notepad .env  # or use your preferred editor
```

**Required variables:**
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_ROLE_KEY=eyJxxx...
DATABASE_URL=postgresql://postgres:yourpassword@db.xxx.supabase.co:5432/postgres
```

⚠️ **Never commit `.env` to Git!** (already in `.gitignore`)

---

### Step 3: Run Database Migration (5 min)

**Option A: Supabase Dashboard (Recommended)**
1. Go to Supabase Dashboard → SQL Editor
2. Click "New query"
3. Copy contents of `migrations/001_init.sql`
4. Paste and click "Run"
5. Should see: "Success. No rows returned"

**Option B: Command Line**
```bash
psql $DATABASE_URL -f ../migrations/001_init.sql
```

---

### Step 4: Verify Connection (2 min)

```bash
# From backend directory
python verify_db.py
```

**Expected output:**
```
✅ Database connection successful!
⚠️  stops: 0 rows
⚠️  paths: 0 rows
...
💡 Run: python scripts/seed_db.py to populate data
```

---

### Step 5: Seed Data (5 min)

```bash
# From project root
cd ..
python scripts/seed_db.py
```

**Expected output:**
```
✅ Stops: 8 inserted
✅ Paths: 3 inserted
✅ Routes: 4 inserted
✅ Vehicles: 6 inserted
✅ Daily Trips: 10 inserted
✅ Bookings: 40 inserted
🎉 Database seeded successfully!
```

---

## ✅ Verification

Run verification again:
```bash
cd backend
python verify_db.py
```

**Should now show:**
```
✅ stops: 8 rows
✅ paths: 3 rows
✅ routes: 4 rows
✅ vehicles: 6 rows
✅ daily_trips: 10 rows
✅ bookings: 40 rows
🎉 All tables verified successfully!
```

---

## 🎉 Success!

Your database is now ready! You can:
- View data in Supabase Dashboard → Table Editor
- Start the backend: `python -m uvicorn app.main:app --reload`
- Proceed to Day 3: FastAPI CRUD endpoints

---

## 🔧 Troubleshooting

### "Database connection failed"
- Check DATABASE_URL format (must start with `postgresql://`)
- Verify password is correct
- Ensure internet connection

### "No module named 'supabase'"
```bash
pip install supabase asyncpg
```

### "SUPABASE_URL not found"
- Ensure `.env` file exists in `backend/` directory
- Check variable names are exact (case-sensitive)

### Tables already exist
Run in Supabase SQL Editor:
```sql
DROP TABLE IF EXISTS audit_logs, bookings, deployments, daily_trips, 
                      drivers, vehicles, routes, path_stops, paths, stops CASCADE;
```
Then re-run migration.

---

## 📚 Related Documentation

- Full setup guide: `docs/SUPABASE_SETUP.md`
- Database schema: `migrations/001_init.sql`
- Seed script: `scripts/seed_db.py`
- Verification: `backend/verify_db.py`

---

## 🎯 Next: Day 3

Once database is verified, continue to Day 3:
- Implement SQLAlchemy models
- Create FastAPI CRUD endpoints
- Test with Swagger UI at http://localhost:8000/docs
