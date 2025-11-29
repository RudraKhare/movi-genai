# 🚀 MOVI Deployment Guide

Complete step-by-step guide to deploy MOVI application for FREE.

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRODUCTION STACK                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   FRONTEND   │────▶│   BACKEND    │────▶│   DATABASE   │    │
│  │   Vercel     │     │   Render     │     │   Supabase   │    │
│  │   (FREE)     │     │   (FREE)     │     │   (FREE)     │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│                              │                                   │
│                              ▼                                   │
│                       ┌──────────────┐                          │
│                       │    Gemini    │                          │
│                       │   (FREE)     │                          │
│                       └──────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

## 📋 Free Tier Limits

| Service | Free Tier Limits | Notes |
|---------|-----------------|-------|
| **Vercel** | 100GB bandwidth, unlimited deploys | Perfect for frontend |
| **Render** | 750 hrs/month, sleeps after 15min | Sufficient for demo |
| **Supabase** | 500MB storage, 2 projects | Already set up |
| **Gemini** | 15 req/min, 1M tokens/month | Generous for demo |

---

## 🔧 STEP 1: Deploy Backend to Render

### 1.1 Push Code to GitHub

```bash
# Make sure all changes are committed
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 1.2 Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub (recommended)
3. Authorize Render to access your repositories

### 1.3 Create New Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository: `RudraKhare/movi-genai`
3. Configure the service:

| Setting | Value |
|---------|-------|
| **Name** | `movi-backend` |
| **Region** | Oregon (US West) - Free tier |
| **Branch** | `main` or `release/day6-fullstack-verification` |
| **Root Directory** | `backend` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | Free |

### 1.4 Configure Environment Variables

In Render dashboard → Your Service → **Environment**:

```bash
# Required
DATABASE_URL=postgresql://postgres.xxxxx:password@aws-0-region.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
FASTAPI_SECRET_KEY=your-secret-key-at-least-32-characters-long

# LLM Configuration (use Gemini - it's free!)
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
LLM_MODEL=gemini-2.0-flash
USE_LLM_PARSE=true

# CORS - Add your Vercel URL after deployment
CORS_ORIGINS=https://your-app.vercel.app

# Production settings
FASTAPI_DEBUG=false
```

### 1.5 Get Your Gemini API Key (Free)

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Click **"Create API Key"**
3. Copy the key and add to Render environment variables

### 1.6 Deploy

1. Click **"Create Web Service"**
2. Wait for build to complete (5-10 minutes)
3. Note your backend URL: `https://movi-backend.onrender.com`

### 1.7 Test Backend

```bash
# Test health endpoint
curl https://movi-backend.onrender.com/api/health

# Expected response:
# {"status": "healthy", ...}
```

---

## 🎨 STEP 2: Deploy Frontend to Vercel

### 2.1 Create Vercel Account

1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub
3. Authorize Vercel to access your repositories

### 2.2 Import Project

1. Click **"Add New..."** → **"Project"**
2. Select your repository: `RudraKhare/movi-genai`
3. Configure:

| Setting | Value |
|---------|-------|
| **Framework Preset** | Vite |
| **Root Directory** | `frontend` |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |

### 2.3 Configure Environment Variables

In Vercel → Project Settings → **Environment Variables**:

```bash
VITE_API_URL=https://movi-backend.onrender.com
```

### 2.4 Deploy

1. Click **"Deploy"**
2. Wait for build (2-3 minutes)
3. Your app is live at: `https://your-app.vercel.app`

### 2.5 Update Backend CORS

Go back to Render and update `CORS_ORIGINS`:

```bash
CORS_ORIGINS=https://your-app.vercel.app
```

Click **"Save Changes"** - Render will redeploy automatically.

---

## ✅ STEP 3: Verify Deployment

### 3.1 Test Full Flow

1. Open your Vercel URL: `https://your-app.vercel.app`
2. Navigate to any page (BusDashboard, ManageRoute)
3. Open the MOVI widget (chat icon)
4. Try a command: "Show all trips"
5. Verify response comes back

### 3.2 Check Backend Logs

In Render dashboard → Your Service → **Logs**:
- Look for successful startup messages
- Check for any errors

### 3.3 Test API Directly

```bash
# Health check
curl https://movi-backend.onrender.com/api/health

# Test agent endpoint
curl -X POST https://movi-backend.onrender.com/api/agent \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key-change-in-production" \
  -d '{"message": "show trips", "page_context": "BusDashboard"}'
```

---

## ⚠️ Important Notes

### Render Free Tier Sleep

Render free tier **spins down after 15 minutes of inactivity**.

**First request after sleep**: Takes 30-60 seconds (cold start)

**Solutions**:
1. **Accept it** - First load is slow, then fast
2. **Use a ping service** - [UptimeRobot](https://uptimerobot.com) to ping every 14 min
3. **Upgrade to paid** - $7/month for always-on

### Keeping Backend Awake (Optional)

1. Go to [UptimeRobot](https://uptimerobot.com) (free)
2. Create new monitor:
   - Type: HTTP(s)
   - URL: `https://movi-backend.onrender.com/api/health`
   - Interval: 14 minutes

---

## 🔄 Continuous Deployment

Both Vercel and Render support **automatic deployments**:

1. Push to GitHub
2. Services detect changes
3. Automatic rebuild and deploy

### Branch Deployments

- **Vercel**: Creates preview URLs for each PR
- **Render**: Can configure branch-specific deploys

---

## 🐛 Troubleshooting

### Backend won't start

1. Check Render logs for errors
2. Verify all environment variables are set
3. Test DATABASE_URL connection locally first

### CORS errors

1. Verify `CORS_ORIGINS` includes your Vercel URL
2. Check for trailing slashes (don't include them)
3. Redeploy backend after changing CORS

### Frontend can't reach backend

1. Check `VITE_API_URL` is correct in Vercel
2. Ensure backend is awake (not sleeping)
3. Check browser console for errors

### LLM not responding

1. Verify `GEMINI_API_KEY` is valid
2. Check Gemini quota at [Google AI Studio](https://aistudio.google.com)
3. Try `LLM_PROVIDER=gemini` and `LLM_MODEL=gemini-2.0-flash`

---

## 📊 Cost Summary

| Service | Monthly Cost |
|---------|-------------|
| Vercel Frontend | $0 |
| Render Backend | $0 |
| Supabase Database | $0 |
| Gemini API | $0 |
| **Total** | **$0** |

---

## 🚀 Going to Production

When ready for production, consider:

1. **Custom Domain**: Add your own domain to Vercel/Render
2. **Render Paid**: $7/month for always-on backend
3. **Supabase Pro**: $25/month for more storage/features
4. **API Key Security**: Rotate keys, add rate limiting
5. **Monitoring**: Add error tracking (Sentry)
6. **Backup**: Regular database backups

---

## Quick Reference URLs

After deployment, your URLs will be:

```
Frontend:  https://movi-xxxxx.vercel.app
Backend:   https://movi-backend.onrender.com
Database:  (Supabase - already configured)
```

Keep these handy for testing and sharing!
