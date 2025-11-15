# 🚀 Quick Start - Test Image Upload NOW

## ⚡ 30-Second Test

### Step 1: Start Servers (2 terminals)
```powershell
# Terminal 1
cd C:\Users\rudra\Desktop\movi\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Terminal 2
cd C:\Users\rudra\Desktop\movi\frontend
npm run dev
```

### Step 2: Open Browser
1. Go to http://localhost:5173
2. Press **F12** (DevTools)
3. Click **Console** tab

### Step 3: Test Button
1. Click blue MOVI button (bottom-right)
2. Click 📷 camera icon in chat

**✅ PASS**: See logs like:
```
[ImageUploadButton] Button clicked!
```

**❌ FAIL**: No logs? Check step 4 below.

### Step 4: Upload Image
1. Select any image file
2. Watch Console for:
```
[MoviWidget] OCR Response: { match_type: "...", ... }
```

**✅ PASS**: Image appears in chat
**❌ FAIL**: Error? Check backend logs.

---

## 🎯 What to Expect (Visual)

### Before Upload
```
┌──────────────────────────────────┐
│  MOVI Assistant          🗑️ ✕   │
├──────────────────────────────────┤
│                                  │
│  [Empty chat - placeholder msg]  │
│                                  │
├──────────────────────────────────┤
│  📷  [Type message...]    [Send] │
└──────────────────────────────────┘
      ↑
   Click here first
```

### After Clicking Camera
```
File picker opens:
┌─────────────────────────────┐
│ Open                        │
│                             │
│ 📁 Documents                │
│ 📁 Pictures                 │
│ 📄 bulk_schedule.png        │
│ 📄 trip_image.jpg           │
│                             │
│        [Cancel] [Open]      │
└─────────────────────────────┘
```

### During Upload (Uploading State)
```
┌──────────────────────────────────┐
│  MOVI Assistant          🗑️ ✕   │
├──────────────────────────────────┤
│ You:                             │
│  ┌───────────────┐               │
│  │ [Image]       │  ⏳          │
│  │ bulk.png      │               │
│  └───────────────┘               │
│  Uploading...                    │
├──────────────────────────────────┤
│  📷  [Type message...]    [Send] │
│      (button disabled)           │
└──────────────────────────────────┘
```

### Success - Single Match (Auto-Forward)
```
┌──────────────────────────────────┐
│  MOVI Assistant          🗑️ ✕   │
├──────────────────────────────────┤
│ You:                             │
│  ┌───────────────┐               │
│  │ [Image]       │  ✅          │
│  │ bulk.png      │               │
│  └───────────────┘               │
│  Identified: Bulk - 00:01        │
│                                  │
│ MOVI:                            │
│  Here's the info for Bulk-00:01  │
│  • Route: Bulk Route             │
│  • Status: Active                │
│  • Next departure: 23:30         │
├──────────────────────────────────┤
│  📷  [Type message...]    [Send] │
└──────────────────────────────────┘
```

### Success - Multiple Matches (Candidates)
```
┌──────────────────────────────────┐
│  MOVI Assistant          🗑️ ✕   │
├──────────────────────────────────┤
│ You:                             │
│  ┌───────────────┐               │
│  │ [Image]       │  ✅          │
│  │ jayanagar.png │               │
│  └───────────────┘               │
│  Image processed                 │
│                                  │
│ MOVI:                            │
│  I found multiple trips:         │
│  ┌──────────────────────────┐   │
│  │ Jayanagar-08:00 (72%)    │   │
│  └──────────────────────────┘   │
│  ┌──────────────────────────┐   │
│  │ Jayanagar-09:00 (68%)    │   │
│  └──────────────────────────┘   │
│  ┌──────────────────────────┐   │
│  │ Jayanagar Exp-08:30 (65%)│   │
│  └──────────────────────────┘   │
│          ↑                       │
│     Click any button             │
├──────────────────────────────────┤
│  📷  [Type message...]    [Send] │
└──────────────────────────────────┘
```

### Failure - No Match (Fallback)
```
┌──────────────────────────────────┐
│  MOVI Assistant          🗑️ ✕   │
├──────────────────────────────────┤
│ You:                             │
│  ┌───────────────┐               │
│  │ [Image]       │  ❌          │
│  │ random.jpg    │               │
│  └───────────────┘               │
│  Could not identify trip         │
│                                  │
│ MOVI:                            │
│  Sorry, I couldn't identify the  │
│  trip from the image. Try typing │
│  the trip details or upload a    │
│  clearer image.                  │
├──────────────────────────────────┤
│  📷  [Type message...]    [Send] │
└──────────────────────────────────┘
```

---

## 🔍 Console Output - What You'll See

### ✅ Good Output (Success)
```console
[ImageUploadButton] Button clicked!
[ImageUploadButton] File input changed
[ImageUploadButton] Selected file: File { name: "bulk.png", size: 45678 }
[ImageUploadButton] File validation passed, calling onImageSelect
[MoviWidget] handleImageUpload called with file: File { ... }
[MoviWidget] Creating FormData and uploading...
[MoviWidget] OCR Response: { match_type: "single", trip_id: 5, auto_forward: true }
[MoviWidget] Single match detected, auto-forwarding with trip_id: 5
[MoviWidget] Auto-forward response: { message: "Here's the info...", trip_id: 5 }
```

### ❌ Bad Output (Error)
```console
[MoviWidget] Error uploading image: AxiosError { message: "Network Error" }
[MoviWidget] Error details: Network Error
```

**Fix**: Check backend is running on port 8000

---

## 🐛 Quick Fixes

### Problem: No console logs when clicking button
**Fix 1**: Refresh browser (Ctrl+R)
**Fix 2**: Check ChatInput has `<ImageUploadButton />`
**Fix 3**: Check DevTools Console isn't filtered

### Problem: "Network Error" in console
**Fix 1**: Check backend is running: http://localhost:8000/health
**Fix 2**: Check CORS is enabled in backend
**Fix 3**: Check axios baseURL is correct

### Problem: "Google Vision API key not configured"
**Fix**: Add to `backend/.env`:
```
GOOGLE_VISION_KEY_BASE64=<your_base64_key>
```

### Problem: File picker doesn't open
**Fix**: Check browser console for popup blocker warning

---

## 📊 Network Tab - What to Check

### Expected Requests (Single Match)
```
1. POST /api/agent/image
   Status: 200 OK
   Response: { match_type: "single", trip_id: 5, auto_forward: true }

2. POST /api/agent/message
   Status: 200 OK
   Payload: { text: "<image>", selectedTripId: 5 }
   Response: { message: "Here's the info...", trip_id: 5 }
```

### Expected Requests (Multiple Matches)
```
1. POST /api/agent/image
   Status: 200 OK
   Response: { match_type: "multiple", candidates: [...] }

(User clicks candidate)

2. POST /api/agent/message
   Status: 200 OK
   Payload: { text: "Trip Name", selectedTripId: 3 }
```

---

## ✅ Success Checklist

- [ ] Backend running on :8000
- [ ] Frontend running on :5173
- [ ] Browser DevTools open
- [ ] Console tab visible
- [ ] MOVI widget opens
- [ ] Camera button visible
- [ ] File picker opens
- [ ] Console shows logs
- [ ] Network shows request
- [ ] Image appears in chat
- [ ] Agent responds

---

## 🎯 5-Minute Full Test

### Minute 1: Setup
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### Minute 2: Start Frontend
```powershell
cd frontend
npm run dev
```

### Minute 3: Open Browser
- http://localhost:5173
- F12 → Console tab

### Minute 4: Test Upload
- Click MOVI button
- Click 📷 camera
- Select image
- Watch console logs

### Minute 5: Verify
- ✅ Image bubble appears
- ✅ Console shows ~17 logs
- ✅ Network shows 2 requests
- ✅ Agent responds

---

## 🆘 Still Not Working?

### Share These 3 Things:
1. **Console Output** (all logs)
2. **Network Tab** (screenshot)
3. **Backend Terminal** (last 20 lines)

### Quick Commands to Run:
```powershell
# Check backend health
curl http://localhost:8000/health

# Check frontend build
cd frontend
npm run build

# Check file exists
Get-Item frontend\src\components\MoviWidget\MoviWidget.jsx
```

---

## 📚 Documentation Files Created

1. **PATCH_SUMMARY.md** - What was changed
2. **IMAGE_UPLOAD_INTEGRATION_COMPLETE.md** - Full test guide
3. **EXPECTED_CONSOLE_LOGS.md** - All console log patterns
4. **QUICK_START_TEST.md** - This file

---

**Ready to test?** Run the 30-second test above! 🚀

**Status**: ✅ Code complete - waiting for browser test
**Next**: Start servers → Open browser → Click camera → See logs
