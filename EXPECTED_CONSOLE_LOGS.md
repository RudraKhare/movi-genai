# 🔍 Expected Console Logs - Image Upload Feature

## 📋 Complete Console Log Reference

### Test Scenario 1: Button Click (No File Selected)
**Action**: Click camera button, then cancel file picker

```
[ImageUploadButton] Rendering, disabled: false onImageSelect: function
[ImageUploadButton] Button clicked!
[ImageUploadButton] disabled: false
[ImageUploadButton] onImageSelect: function
[ImageUploadButton] fileInputRef.current: <input type="file" accept="image/*">
[ImageUploadButton] Triggering file input click
```

---

### Test Scenario 2: Single Match Auto-Forward (Success)
**Action**: Upload image with clear trip text like "Bulk - 00:01"

```console
[ImageUploadButton] Rendering, disabled: false onImageSelect: function
[ImageUploadButton] Button clicked!
[ImageUploadButton] disabled: false
[ImageUploadButton] onImageSelect: function
[ImageUploadButton] fileInputRef.current: <input type="file" accept="image/*">
[ImageUploadButton] Triggering file input click
[ImageUploadButton] File input changed
[ImageUploadButton] Selected file: File {
  name: "bulk_schedule.png",
  size: 45678,
  type: "image/png",
  lastModified: 1699876543210
}
[ImageUploadButton] File validation passed, calling onImageSelect
[MoviWidget] handleImageUpload called with file: File {
  name: "bulk_schedule.png",
  size: 45678,
  type: "image/png"
}
[MoviWidget] Current state - loading: false, awaitingConfirm: false
[MoviWidget] Creating object URL and image message
[MoviWidget] Creating FormData and uploading...
[MoviWidget] Calling uploadAgentImage API...
[MoviWidget] OCR Response: {
  match_type: "single",
  trip_id: 5,
  confidence: 0.89,
  auto_forward: true,
  display_name: "Bulk - 00:01",
  route_name: "Bulk Route",
  scheduled_time: "00:01"
}
[MoviWidget] Updating message status to processing
[MoviWidget] Single match detected, auto-forwarding with trip_id: 5
[MoviWidget] Auto-forwarding to agent: {
  text: "<image>",
  user_id: 1,
  currentPage: "busDashboard",
  selectedTripId: 5,
  selectedRouteId: undefined
}
[MoviWidget] Sending message: {
  text: "<image>",
  user_id: 1,
  currentPage: "busDashboard",
  selectedTripId: 5
}
[MoviWidget] Auto-forward response: {
  message: "Here's the information for trip Bulk - 00:01...",
  trip_id: 5,
  route_id: 2,
  current_state: "active"
}
[MoviWidget] Agent reply: {
  message: "Here's the information for trip Bulk - 00:01...",
  trip_id: 5
}
```

**Network Requests** (in order):
1. `POST /api/agent/image` → Status: 200
2. `POST /api/agent/message` → Status: 200

---

### Test Scenario 3: Multiple Matches (Ambiguous)
**Action**: Upload image with partial text like "Jayanagar"

```console
[ImageUploadButton] Rendering, disabled: false onImageSelect: function
[ImageUploadButton] Button clicked!
[ImageUploadButton] Triggering file input click
[ImageUploadButton] File input changed
[ImageUploadButton] Selected file: File {
  name: "jayanagar_partial.jpg",
  size: 52341,
  type: "image/jpeg"
}
[ImageUploadButton] File validation passed, calling onImageSelect
[MoviWidget] handleImageUpload called with file: File { name: "jayanagar_partial.jpg", ... }
[MoviWidget] Current state - loading: false, awaitingConfirm: false
[MoviWidget] Creating object URL and image message
[MoviWidget] Creating FormData and uploading...
[MoviWidget] Calling uploadAgentImage API...
[MoviWidget] OCR Response: {
  match_type: "multiple",
  needs_clarification: true,
  message: "I found multiple trips matching your image. Which one did you mean?",
  candidates: [
    {
      trip_id: 3,
      display_name: "Jayanagar-08:00",
      confidence: 0.72,
      route_name: "Jayanagar Route",
      scheduled_time: "08:00"
    },
    {
      trip_id: 7,
      display_name: "Jayanagar-09:00",
      confidence: 0.68,
      route_name: "Jayanagar Route",
      scheduled_time: "09:00"
    },
    {
      trip_id: 12,
      display_name: "Jayanagar Express-08:30",
      confidence: 0.65,
      route_name: "Jayanagar Express",
      scheduled_time: "08:30"
    }
  ]
}
[MoviWidget] Updating message status to processing
[MoviWidget] Multiple matches detected, showing candidates: [
  { trip_id: 3, display_name: "Jayanagar-08:00", confidence: 0.72 },
  { trip_id: 7, display_name: "Jayanagar-09:00", confidence: 0.68 },
  { trip_id: 12, display_name: "Jayanagar Express-08:30", confidence: 0.65 }
]
```

**Then user clicks "Jayanagar-08:00 (72% match)" button:**

```console
[MoviWidget] Option clicked: {
  trip_id: 3,
  name: "Jayanagar-08:00",
  text: "Jayanagar-08:00 (72% match)",
  confidence: 0.72
}
[MoviWidget] Sending option with trip_id: {
  text: "Jayanagar-08:00",
  user_id: 1,
  currentPage: "busDashboard",
  selectedTripId: 3
}
[MoviWidget] Sending message: {
  text: "Jayanagar-08:00",
  user_id: 1,
  selectedTripId: 3
}
[MoviWidget] Agent reply: {
  message: "Here's the information for Jayanagar-08:00...",
  trip_id: 3
}
```

**Network Requests** (in order):
1. `POST /api/agent/image` → Status: 200
2. *(User clicks candidate button)*
3. `POST /api/agent/message` → Status: 200

---

### Test Scenario 4: No Match (Fallback)
**Action**: Upload random image with no trip text

```console
[ImageUploadButton] Button clicked!
[ImageUploadButton] File input changed
[ImageUploadButton] Selected file: File {
  name: "random_photo.png",
  size: 123456,
  type: "image/png"
}
[ImageUploadButton] File validation passed, calling onImageSelect
[MoviWidget] handleImageUpload called with file: File { name: "random_photo.png", ... }
[MoviWidget] Current state - loading: false, awaitingConfirm: false
[MoviWidget] Creating object URL and image message
[MoviWidget] Creating FormData and uploading...
[MoviWidget] Calling uploadAgentImage API...
[MoviWidget] OCR Response: {
  match_type: "none",
  message: "Could not identify trip from image. No readable text or matching trips found.",
  auto_forward: false,
  extracted_text: "some random text",
  confidence: 0.12
}
[MoviWidget] Updating message status to processing
[MoviWidget] No match or fallback case
```

**Network Requests**:
1. `POST /api/agent/image` → Status: 200

---

### Test Scenario 5: File Validation Error (File Too Large)
**Action**: Select 15MB image file

```console
[ImageUploadButton] Button clicked!
[ImageUploadButton] Triggering file input click
[ImageUploadButton] File input changed
[ImageUploadButton] Selected file: File {
  name: "huge_image.png",
  size: 15728640,  // 15MB
  type: "image/png"
}
[ImageUploadButton] File too large: 15728640
```

**Alert Message**: "Image too large. Please select an image smaller than 10MB."

---

### Test Scenario 6: Invalid File Type
**Action**: Select PDF file instead of image

```console
[ImageUploadButton] Button clicked!
[ImageUploadButton] Triggering file input click
[ImageUploadButton] File input changed
[ImageUploadButton] Selected file: File {
  name: "document.pdf",
  size: 234567,
  type: "application/pdf"
}
[ImageUploadButton] Invalid file type: application/pdf
```

**Alert Message**: "Please select an image file (JPG, PNG)"

---

### Test Scenario 7: Network Error (Backend Offline)
**Action**: Upload image while backend is stopped

```console
[ImageUploadButton] File validation passed, calling onImageSelect
[MoviWidget] handleImageUpload called with file: File { ... }
[MoviWidget] Creating object URL and image message
[MoviWidget] Creating FormData and uploading...
[MoviWidget] Calling uploadAgentImage API...
[MoviWidget] Error uploading image: AxiosError {
  message: "Network Error",
  code: "ERR_NETWORK",
  config: { url: "http://localhost:8000/api/agent/image", method: "post" }
}
[MoviWidget] Error details: Network Error
```

**UI Error Banner**: "Failed to process image. Please try again."

---

### Test Scenario 8: Backend 500 Error
**Action**: Upload image, backend has internal error

```console
[MoviWidget] Calling uploadAgentImage API...
[MoviWidget] Error uploading image: AxiosError {
  message: "Request failed with status code 500",
  response: {
    status: 500,
    statusText: "Internal Server Error",
    data: {
      detail: "Google Vision API key not configured"
    }
  }
}
[MoviWidget] Error details: {
  detail: "Google Vision API key not configured"
}
```

---

### Test Scenario 9: Button Disabled During Upload
**Action**: Try clicking button while upload in progress

```console
[ImageUploadButton] Rendering, disabled: true onImageSelect: function
[ImageUploadButton] Button clicked!
[ImageUploadButton] disabled: true
[ImageUploadButton] onImageSelect: function
// (nothing happens - button is disabled)
```

---

### Test Scenario 10: Normal Text Message Still Works
**Action**: Type "show me trip bulk-00:01" and press Enter

```console
[MoviWidget] Sending message: {
  text: "show me trip bulk-00:01",
  user_id: 1,
  currentPage: "busDashboard"
}
[MoviWidget] Agent reply: {
  message: "Here's the information for trip Bulk - 00:01...",
  trip_id: 5
}
```

**Network Requests**:
1. `POST /api/agent/message` → Status: 200

---

## 🎯 Key Log Patterns to Watch For

### ✅ SUCCESS Pattern
```
Button clicked → File selected → Validation passed → Upload started → 
Response received → Match detected → Auto-forward OR Candidates shown
```

### ❌ ERROR Pattern
```
Button clicked → File selected → Validation passed → Upload started → 
Error caught → Error logged → UI error shown
```

### 🔍 DEBUG Pattern
```
[Component] Action description: data object
```

---

## 📊 Console Log Categories

### ImageUploadButton Logs (Blue prefix)
- `[ImageUploadButton] Rendering`
- `[ImageUploadButton] Button clicked!`
- `[ImageUploadButton] File input changed`
- `[ImageUploadButton] File validation passed`

### MoviWidget Logs (Green prefix)
- `[MoviWidget] handleImageUpload called`
- `[MoviWidget] Creating FormData`
- `[MoviWidget] OCR Response:`
- `[MoviWidget] Single match detected`
- `[MoviWidget] Multiple matches detected`
- `[MoviWidget] Auto-forwarding to agent:`
- `[MoviWidget] Option clicked:`
- `[MoviWidget] Error uploading image:`

---

## 🔧 How to Filter Logs in DevTools

### Show only image upload logs:
```javascript
// In Console filter box, type:
MoviWidget ImageUploadButton
```

### Show only errors:
```javascript
// In Console, click "Errors" level filter
```

### Show network requests:
```javascript
// Network tab → Filter: "agent"
```

---

## 🐛 Troubleshooting by Log Pattern

### Pattern: No logs at all
**Problem**: Button not rendering or event not attached
**Check**: Inspect element, verify `<ImageUploadButton>` exists in DOM

### Pattern: Logs stop at "Triggering file input click"
**Problem**: File picker not opening
**Check**: Browser permissions, popup blockers

### Pattern: Logs stop at "Calling uploadAgentImage API"
**Problem**: Network request not sent
**Check**: Axios configuration, CORS, backend URL

### Pattern: Error at "OCR Response"
**Problem**: Backend error or parsing issue
**Check**: Backend logs, response format

### Pattern: No "Auto-forwarding" after single match
**Problem**: Conditional logic not triggered
**Check**: `ocrResult.match_type === 'single'` and `ocrResult.auto_forward === true`

---

## ✅ Expected Log Counts (Successful Upload)

| Action | Expected Logs |
|--------|---------------|
| Button click | 5 logs (ImageUploadButton) |
| File selection | 3 logs (validation) |
| Upload start | 4 logs (MoviWidget upload) |
| Single match | 5 logs (auto-forward) |
| Multiple matches | 2 logs (candidates) |
| No match | 1 log (fallback) |
| Error | 2 logs (error + details) |

**Total for successful auto-forward**: ~17 console logs

---

**Last Updated**: 2025-11-13
**Purpose**: Debugging reference for image upload feature
**Use**: Compare actual console output with these patterns
