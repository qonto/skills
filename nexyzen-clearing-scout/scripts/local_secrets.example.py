"""Optional local credentials for submit_to_nexyzen.py / check_compensations.py.

Copy this file to `local_secrets.py` (same folder) and fill in your own
values to skip setting OS environment variables by hand. `local_secrets.py`
is gitignored — it is never committed, and must never be published.

Uses setdefault() so a real environment variable, if set, always wins.
"""

import os

os.environ.setdefault("NEXYZEN_AFFILIATE_CODE", "your-affiliate-code")
os.environ.setdefault("NEXYZEN_TOKEN", "your-api-token")
