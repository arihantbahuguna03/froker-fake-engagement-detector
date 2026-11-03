"""
Fake Engagement Detection Config — Example
===========================================
Copy this file to detection_config.py and fill in your calibrated values.
detection_config.py is gitignored — this example shows the structure only.

Thresholds were calibrated by analysing real fraud incident patterns and
creator baseline distributions. Setting them too low → false positives that
harm genuine creators. Setting them too high → missed fraud that costs money.
"""

# ── Velocity spike detection ──────────────────────────────────────────────────
# Flag a post if >N engagement events arrive within WINDOW_MINUTES.
# Calibration: proprietary — available on request.
VELOCITY_WINDOW_MINUTES = 5       # lookback window (public — not the threshold)
VELOCITY_THRESHOLD      = None    # events/window to trigger flag — proprietary

# ── IP cluster detection ──────────────────────────────────────────────────────
# Flag a post if top-5 IPs account for >X% of all events.
# Calibration: proprietary — available on request.
IP_CLUSTER_THRESHOLD = None       # fraction (0–1) — proprietary

# ── Z-score anomaly detection ─────────────────────────────────────────────────
# Flag a creator if their event count exceeds Nσ above personal baseline.
# Calibration: proprietary — available on request.
ZSCORE_THRESHOLD = None           # standard deviations — proprietary
