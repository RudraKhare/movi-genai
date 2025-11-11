# Supabase Setup Guide for MOVI

This guide will walk you through setting up Supabase for the MOVI project.

## 📋 Prerequisites
- A GitHub or Google account
- Web browser

## 🚀 Step-by-Step Setup

### 1. Create Supabase Account & Project

1. **Go to Supabase**: https://app.supabase.com
2. **Sign in** with GitHub or Google
3. **Click "New Project"**
4. **Fill in the details**:
   - **Name**: `movi-transport` (or any name you prefer)
   - **Database Password**: Create a strong password (save this!)
   - **Region**: Choose closest to you (e.g., `Southeast Asia (Singapore)` for India)
   - **Pricing Plan**: Free (sufficient for development)
5. **Click "Create new project"**
6. Wait 2-3 minutes for the project to be provisioned

---

### 2. Get Your Credentials

Once your project is ready:

#### A. Get API Keys
1. In your project dashboard, click **"Project Settings"** (gear icon in left sidebar)
2. Click **"API"** in the settings menu
3. Copy the following values:

```
Project URL: https://[your-project-id].supabase.co
anon key: eyJhbGc...  (starts with eyJ)
service_role key: eyJhbGc...  (starts with eyJ, different from anon)
```

#### B. Get Database URL
1. Still in **Project Settings**, click **"Database"**
2. Scroll down to **"Connection String"**
3. Select **"URI"** tab
4. Copy the connection string (looks like: `postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres`)
5. **Important**: Replace `[password]` with the database password you created in Step 1

---

### 3. Configure Your Local Environment

1. **Open** `c:\Users\rudra\Desktop\movi\.env.local`
   (If it doesn't exist, copy from `.env.example`)

2. **Paste your credentials**:

```bash
# Supabase Configuration
SUPABASE_URL=https://[your-project-id].supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Database Configuration
DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres

# FastAPI Configuration
FASTAPI_SECRET_KEY=replace_me_with_secure_random_string

# Frontend Environment Variables
VITE_SUPABASE_URL=https://[your-project-id].supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VITE_API_BASE_URL=http://localhost:8000
```

3. **Save the file**

---

### 4. Run Database Migration

**Option A: Using Supabase SQL Editor (Recommended)**

1. In your Supabase dashboard, click **"SQL Editor"** in the left sidebar
2. Click **"New query"**
3. Open `c:\Users\rudra\Desktop\movi\migrations\001_init.sql`
4. **Copy ALL contents** of the file
5. **Paste** into the SQL Editor
6. Click **"Run"** (or press Ctrl+Enter)
7. Wait for "Success. No rows returned"

**Option B: Using psql (if installed)**

```powershell
# In PowerShell
cd c:\Users\rudra\Desktop\movi
psql $env:DATABASE_URL -f migrations\001_init.sql
```

---

### 5. Verify Tables Created

1. In Supabase dashboard, click **"Table Editor"** in the left sidebar
2. You should see these tables:
   - ✅ stops
   - ✅ paths
   - ✅ path_stops
   - ✅ routes
   - ✅ vehicles
   - ✅ drivers
   - ✅ daily_trips
   - ✅ deployments
   - ✅ bookings
   - ✅ audit_logs

---

### 6. Seed the Database

```powershell
# In PowerShell
cd c:\Users\rudra\Desktop\movi

# Activate backend virtual environment
cd backend
.\.venv\Scripts\Activate.ps1

# Run seed script
cd ..
python scripts\seed_db.py
```

**Expected output:**
```
==========================================
🌱 MOVI Database Seed Script
==========================================
✅ Using Supabase connection

🌱 Seeding via Supabase client...
🧹 Cleaning existing data...
📍 Inserting stops...
   ✅ Inserted 12 stops
🛤️  Inserting paths...
   ✅ Inserted 4 paths
🔗 Linking paths to stops...
   ✅ Created 20 path-stop links
🚏 Inserting routes...
   ✅ Inserted 8 routes
🚌 Inserting vehicles...
   ✅ Inserted 10 vehicles
👨‍✈️ Inserting drivers...
   ✅ Inserted 8 drivers
🚍 Inserting daily trips...
   ✅ Inserted 10 daily trips
🔗 Creating deployments...
   ✅ Created 7 deployments
📝 Creating bookings...
   ✅ Created 40+ bookings

✅ Supabase seeding complete!

==========================================
🎉 Database seeding completed successfully!
==========================================
```

---

### 7. Verify Seeded Data

**In Supabase Table Editor:**

1. Click **"daily_trips"** table
2. You should see 10+ rows with data
3. Check **"bookings"** table - should have 40+ rows

**Or run SQL query:**

```sql
-- Check trips
SELECT * FROM daily_trips LIMIT 5;

-- Check bookings with trip names
SELECT 
  b.booking_id, 
  dt.display_name, 
  b.user_name, 
  b.seats, 
  b.status
FROM bookings b
JOIN daily_trips dt ON b.trip_id = dt.trip_id
LIMIT 10;

-- Check deployment status
SELECT * FROM trips_with_deployments;

-- Count confirmed bookings
SELECT COUNT(*) FROM bookings WHERE status = 'CONFIRMED';
```

---

## ✅ Success Checklist

- [ ] Supabase project created
- [ ] All 4 credentials copied to `.env.local`
- [ ] Migration SQL executed successfully
- [ ] All 10 tables visible in Table Editor
- [ ] Seed script ran without errors
- [ ] `daily_trips` table has 10+ rows
- [ ] `bookings` table has 40+ rows
- [ ] At least 3 trips have `booking_status_percentage > 50`

---

## 🐛 Troubleshooting

### Error: "No module named 'supabase'"

**Solution:**
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install supabase
```

### Error: "SUPABASE_URL not found"

**Solution:**
- Make sure `.env.local` exists in project root
- Check that environment variables are set correctly
- Try restarting your terminal

### Error: "Duplicate key value violates unique constraint"

**Solution:**
This happens if you run the seed script multiple times. Reset the database:
```powershell
.\scripts\reset_db.ps1
```

### Error: "Connection timeout"

**Solution:**
- Check your internet connection
- Verify the `DATABASE_URL` is correct
- Ensure Supabase project is not paused (free tier auto-pauses after inactivity)

---

## 🎯 Next Steps

After successful setup:

1. **Test the API**: Start the backend and verify database connection
   ```powershell
   cd backend
   $env:PYTHONPATH="c:\Users\rudra\Desktop\movi\backend"
   python -m uvicorn app.main:app --reload
   ```

2. **Move to Day 3**: Create FastAPI CRUD endpoints
3. **Build LangGraph tools**: Agent actions that query these tables

---

## 📚 Resources

- **Supabase Docs**: https://supabase.com/docs
- **Supabase Dashboard**: https://app.supabase.com
- **PostgreSQL Tutorial**: https://www.postgresql.org/docs/

---

**Status**: Setup guide complete ✅  
**Next**: Run the migration and seed scripts!
