# Day 2 Setup Checklist

Use this checklist to track your progress through Day 2 setup.

## 📋 Pre-Setup

- [ ] Supabase account created at https://app.supabase.com
- [ ] New project "movi-transport" created
- [ ] Database password saved securely
- [ ] All 4 credentials copied from Supabase dashboard

## 🔐 Credentials Collection

From **Supabase Dashboard → Settings → API**:
- [ ] SUPABASE_URL copied
- [ ] SUPABASE_ANON_KEY copied
- [ ] SUPABASE_SERVICE_ROLE_KEY copied

From **Supabase Dashboard → Settings → Database**:
- [ ] DATABASE_URL (URI format) copied
- [ ] Password replaced in DATABASE_URL

## 💻 Local Configuration

- [ ] Navigated to `backend/` directory
- [ ] Ran `python setup_env.py` OR created `.env` manually
- [ ] All 4 credentials pasted into `.env`
- [ ] `.env` file saved
- [ ] Verified `.env` is NOT staged in Git (`git status` should not show it)

## 🗄️ Database Schema

- [ ] Opened Supabase SQL Editor
- [ ] Copied contents of `migrations/001_init.sql`
- [ ] Pasted and ran query in SQL Editor
- [ ] Saw "Success. No rows returned" message
- [ ] Verified 10 tables appear in Supabase Table Editor

## ✅ Connection Verification

- [ ] Ran `python verify_db.py` from `backend/` directory
- [ ] Saw "✅ Database connection successful!"
- [ ] All tables show 0 rows (expected before seeding)

## 🌱 Data Seeding

- [ ] Returned to project root directory
- [ ] Ran `python scripts/seed_db.py`
- [ ] Saw "✅ Stops: 8 inserted" and other success messages
- [ ] Saw "🎉 Database seeded successfully!"
- [ ] No errors in output

## 🔍 Final Verification

- [ ] Ran `python verify_db.py` again from `backend/`
- [ ] All tables now show row counts > 0:
  - [ ] stops: 8 rows
  - [ ] paths: 3 rows
  - [ ] routes: 4 rows
  - [ ] vehicles: 6 rows
  - [ ] drivers: 5 rows
  - [ ] daily_trips: 10 rows
  - [ ] deployments: 4 rows
  - [ ] bookings: 40 rows
- [ ] Relationship verification passed (4 checks)
- [ ] Sample data displayed successfully

## 🎨 Supabase Dashboard Verification

- [ ] Opened Supabase Dashboard → Table Editor
- [ ] Can see `stops` table with 8 rows
- [ ] Can see `daily_trips` table with 10 rows
- [ ] Can see `bookings` table with 40 rows
- [ ] Data looks realistic (names, routes, etc.)

## 🚀 Backend Server Test

- [ ] Activated virtual environment
- [ ] Set PYTHONPATH environment variable
- [ ] Started uvicorn: `python -m uvicorn app.main:app --reload`
- [ ] Server started without errors
- [ ] Visited http://localhost:8000/health
- [ ] Got JSON response with `"status": "ok"`
- [ ] Visited http://localhost:8000/docs
- [ ] Saw Swagger UI with API documentation

## 📝 Git Status

- [ ] Ran `git status`
- [ ] Verified `.env` is NOT listed (should be ignored)
- [ ] New files ready to commit:
  - [ ] `backend/app/db.py`
  - [ ] `backend/verify_db.py`
  - [ ] `backend/setup_env.py`
  - [ ] `backend/.env.template`
  - [ ] `scripts/seed_db.py` (modified)
  - [ ] `docs/DAY2_*.md` files

## 🎯 Day 2 Complete!

- [ ] All checkboxes above are checked ✅
- [ ] Database is connected and populated
- [ ] Backend server runs successfully
- [ ] Ready to proceed to Day 3 (FastAPI endpoints)

---

## 🆘 If Any Step Failed

See troubleshooting in:
- `docs/DAY2_QUICK_START.md` - Common issues
- `docs/SUPABASE_SETUP.md` - Detailed setup help
- `docs/DAY2_IMPLEMENTATION_SUMMARY.md` - Technical details

Or run diagnostics:
```bash
cd backend
python verify_db.py  # Check connection and data
```

---

## 📊 Success Criteria

Your setup is successful when:
1. ✅ `python verify_db.py` shows all tables with data
2. ✅ Backend server starts without errors
3. ✅ Can access http://localhost:8000/health
4. ✅ No secrets are committed to Git

---

## 🎉 Next: Day 3

With database ready, you can now:
- Create SQLAlchemy models for all tables
- Implement FastAPI CRUD endpoints
- Test APIs with Swagger UI
- Connect frontend to backend

**Estimated time for Day 3**: 6-8 hours
