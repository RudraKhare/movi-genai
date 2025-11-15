# Gemini API Timeout Fix

## Problem
Gemini API was frequently timing out (10 seconds), causing:
```
ERROR: Gemini request timed out
TimeoutError
```

This resulted in `action=unknown` and failed user requests.

## Solution Implemented

### 1. Increased Timeout (10s → 30s)
**File**: `langgraph/tools/llm_client.py` (line 381)

**Before**:
```python
response = await asyncio.wait_for(
    asyncio.to_thread(model.generate_content, prompt),
    timeout=config["timeout"]  # Was 10 seconds
)
```

**After**:
```python
response = await asyncio.wait_for(
    asyncio.to_thread(model.generate_content, prompt),
    timeout=30.0  # Increased to 30 seconds
)
```

---

### 2. Retry Logic with Exponential Backoff
**File**: `langgraph/tools/llm_client.py` (line 460)

**Added**:
```python
elif config["provider"] == "gemini":
    # Retry logic for Gemini (handles timeouts)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = await _call_gemini(text, config, context)
            break  # Success, exit retry loop
        except TimeoutError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"[LLM] Gemini timeout on attempt {attempt + 1}/{max_retries}, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"[LLM] Gemini timed out after {max_retries} attempts")
                raise
```

**Retry Schedule**:
- **Attempt 1**: Try with 30s timeout
- **If timeout**: Wait 1 second, retry (Attempt 2)
- **If timeout**: Wait 2 seconds, retry (Attempt 3)
- **If timeout**: Wait 4 seconds, final attempt
- **If still timeout**: Raise error

**Total max time**: 30s × 3 attempts + 7s wait = ~97 seconds max

---

## Expected Behavior

### Before Fix:
```
User: "duplicate route tech-loop to tech loop 2"
→ Gemini timeout after 10s
→ action=unknown
→ User sees: "Additional information needed"
```

### After Fix:
```
User: "duplicate route tech-loop to tech loop 2"
→ Attempt 1: Gemini timeout after 30s
→ Wait 1s
→ Attempt 2: Gemini responds successfully!
→ action=duplicate_route
→ User sees: "✅ Duplicated route successfully"
```

---

## Impact

- ✅ **Increased timeout**: 3x longer (10s → 30s) to handle slow responses
- ✅ **Retry logic**: Up to 3 attempts with exponential backoff
- ✅ **Better UX**: Most timeout issues will be resolved automatically
- ✅ **Logging**: Clear logs show retry attempts for debugging

---

## Testing

The server will auto-reload. Try these commands that previously timed out:

1. **"duplicate route tech-loop to tech loop 2"**
2. **"what's the status of Bulk - 00:01"**
3. **"Assign vehicle 'KA01AB1234' and driver 'Ramesh Kumar' to trip 5"**

Expected: Should succeed on first or second attempt instead of immediately failing.
