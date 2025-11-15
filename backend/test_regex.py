import re

text = "Remove vehicle from Bulk - 00:01"

# Try: "from [trip_name]"
from_match = re.search(r'\bfrom\s+(.+?)(?:\s+vehicle|\s+at|\s*$)', text, re.IGNORECASE)
if from_match:
    trip_label = from_match.group(1).strip()
    print(f"Extracted from 'from' pattern: '{trip_label}'")
else:
    print("No match for 'from' pattern")

# Try alternative pattern
from_match2 = re.search(r'\bfrom\s+(.+?)$', text, re.IGNORECASE)
if from_match2:
    trip_label2 = from_match2.group(1).strip()
    print(f"Alternative extraction: '{trip_label2}'")
