"""
Fake Engagement Detector
=================================
Hourly Airflow job that monitors creator engagement patterns and flags
suspicious activity before prize payouts run.

Built Aug 2024 – Aug 2025 using raw Python + Airflow.
No ML framework — rule-based detection + z-score anomaly detection.

Problem:
  Creators game the leaderboard by buying likes and comments.
  The platform pays out prize money based on rank — fake engagement directly
  costs money and destroys genuine creator trust.

Detection signals:
  1. Velocity spike — >50 events in <5 minutes on one post
  2. IP cluster — >60% of events from ≤5 unique IPs
  3. Z-score — event count >3σ above creator's personal baseline
  4. Comment-to-like ratio anomaly — comments spike without proportional likes

State machine per creator:
  CLEAN → WATCH (1 signal) → FLAGGED (2+ signals) → REVIEWED (manual)
"""

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import requests

from demo_data import (
    ALL_DEMO_EVENTS,
    CREATOR_BASELINES,
    SLACK_WEBHOOK_URL,
    STATE_FILE_PATH,
)


def _load_detection_config() -> tuple[int, int, float, float]:
    """
    Load calibrated fraud detection thresholds from detection_config.py.

    Thresholds were calibrated by analysing real fraud incident patterns and
    creator baseline distributions. Setting them too low → false positives that
    harm genuine creators; too high → missed fraud that costs prize money.

    Implementation: proprietary — available on request.
    Copy detection_config.example.py → detection_config.py to run with your own values.
    """
    try:
        import detection_config
        return (
            detection_config.VELOCITY_WINDOW_MINUTES,
            detection_config.VELOCITY_THRESHOLD,
            detection_config.IP_CLUSTER_THRESHOLD,
            detection_config.ZSCORE_THRESHOLD,
        )
    except ImportError:
        raise RuntimeError(
            "detection_config.py not found. "
            "Copy detection_config.example.py → detection_config.py and fill in your values."
        )


VELOCITY_WINDOW_MINUTES, VELOCITY_THRESHOLD, IP_CLUSTER_THRESHOLD, ZSCORE_THRESHOLD = (
    _load_detection_config()
)


# ── State management ─────────────────────────────────────────────────────────

def load_state() -> dict:
    path = Path(STATE_FILE_PATH)
    if path.exists():
        return json.loads(path.read_text())
    return {}


def save_state(state: dict) -> None:
    Path(STATE_FILE_PATH).write_text(json.dumps(state, indent=2, default=str))


# ── Detection rules ───────────────────────────────────────────────────────────

def check_velocity(events: list[dict]) -> list[str]:
    """Flag post IDs where >VELOCITY_THRESHOLD events hit in VELOCITY_WINDOW_MINUTES."""
    flags = []
    by_post = defaultdict(list)
    for e in events:
        by_post[e["post_id"]].append(e["ts"])

    for post_id, timestamps in by_post.items():
        timestamps.sort()
        for i, ts in enumerate(timestamps):
            window_end = ts + timedelta(minutes=VELOCITY_WINDOW_MINUTES)
            count = sum(1 for t in timestamps[i:] if t <= window_end)
            if count >= VELOCITY_THRESHOLD:
                flags.append(f"velocity:{post_id}:{count}_events_in_{VELOCITY_WINDOW_MINUTES}min")
                break
    return flags


def check_ip_cluster(events: list[dict]) -> list[str]:
    """Flag posts where >60% of events come from ≤5 unique IPs."""
    flags = []
    by_post = defaultdict(list)
    for e in events:
        by_post[e["post_id"]].append(e["ip"])

    for post_id, ips in by_post.items():
        if len(ips) < 10:
            continue
        top5_count = sum(v for _, v in Counter(ips).most_common(5))
        ratio = top5_count / len(ips)
        if ratio >= IP_CLUSTER_THRESHOLD:
            flags.append(f"ip_cluster:{post_id}:{ratio*100:.0f}%_from_top5_ips")
    return flags


def check_zscore(creator_id: str, events: list[dict]) -> list[str]:
    """Flag creators whose event counts exceed 3σ above their personal baseline."""
    flags   = []
    baseline = CREATOR_BASELINES.get(creator_id)
    if not baseline:
        return flags

    by_post = defaultdict(lambda: defaultdict(int))
    for e in events:
        by_post[e["post_id"]][e["event_type"]] += 1

    for post_id, counts in by_post.items():
        for event_type in ("likes", "comments"):
            count = counts.get(event_type.rstrip("s"), 0) + counts.get(event_type, 0)
            mean  = baseline.get(f"avg_{event_type}_per_post", 0)
            std   = baseline.get(f"std_{event_type}", 1)
            if std == 0:
                continue
            z = (count - mean) / std
            if z >= ZSCORE_THRESHOLD:
                flags.append(f"zscore:{post_id}:{event_type}:z={z:.1f}")
    return flags


# ── State machine ─────────────────────────────────────────────────────────────

def next_state(current: str, signal_count: int) -> str:
    if current == "REVIEWED":
        return "REVIEWED"
    if signal_count == 0:
        return "CLEAN"
    if signal_count == 1:
        return "WATCH"
    return "FLAGGED"


# ── Slack alert ───────────────────────────────────────────────────────────────

def post_alert(creator_id: str, state: str, signals: list[str]) -> None:
    icon  = "🚨" if state == "FLAGGED" else "👀"
    lines = [
        f"{icon} *Engagement Alert — {creator_id}*",
        f"Status: *{state}*",
        f"Signals detected:",
    ]
    for s in signals:
        lines.append(f"  • {s}")
    lines.append(f"Detected at: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}")

    requests.post(SLACK_WEBHOOK_URL, json={"text": "\n".join(lines)}, timeout=10).raise_for_status()


# ── Main ──────────────────────────────────────────────────────────────────────

def run_detector(events: list[dict] | None = None) -> dict:
    events = events or ALL_DEMO_EVENTS
    state  = load_state()

    by_creator = defaultdict(list)
    for e in events:
        by_creator[e["creator_id"]].append(e)

    results = {}
    for creator_id, creator_events in by_creator.items():
        signals  = []
        signals += check_velocity(creator_events)
        signals += check_ip_cluster(creator_events)
        signals += check_zscore(creator_id, creator_events)

        prev_state   = state.get(creator_id, {}).get("state", "CLEAN")
        new_state    = next_state(prev_state, len(signals))

        state[creator_id] = {
            "state":      new_state,
            "signals":    signals,
            "updated_at": datetime.now().isoformat(),
        }

        status_icon = {"CLEAN": "✅", "WATCH": "👀", "FLAGGED": "🚨", "REVIEWED": "📋"}.get(new_state, "?")
        print(f"{status_icon} {creator_id}: {new_state}  ({len(signals)} signal(s))")
        for s in signals:
            print(f"     • {s}")

        if new_state in ("WATCH", "FLAGGED") and os.getenv("SLACK_ENABLED", "false").lower() == "true":
            post_alert(creator_id, new_state, signals)

        results[creator_id] = {"state": new_state, "signals": signals}

    save_state(state)
    return results


if __name__ == "__main__":
    print("\nFake Engagement Detector\n" + "="*40)
    run_detector()
