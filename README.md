# Froker Fake Engagement Detector

Hourly Airflow job that monitors creator engagement patterns, detects suspicious activity using rule-based checks + z-score anomaly detection, and alerts the team before prize payouts run.

> Built Aug 2024 – Aug 2025 using raw Python + Airflow. No ML framework — deliberate choice for auditability and low latency.

---

## Problem

Froker pays prize money weekly to top creators based on leaderboard rank. Creators discovered they could game the rank by buying likes and comments. By the time the team noticed, payout had already run.

**Result:** Fake-engagement creators won prize money. Genuine creators lost. Brands lost trust in Froker's creator quality.

---

## Solution

A stateful detection pipeline that runs hourly and catches anomalies **before** payout:

### Detection signals

| Signal | What it catches |
|---|---|
| **Velocity spike** | >50 engagement events on one post in <5 minutes |
| **IP cluster** | >60% of events from ≤5 unique IP addresses |
| **Z-score anomaly** | Event count >3σ above creator's personal baseline |
| **Comment-to-like ratio** | Comments spike disproportionately to likes |

### State machine

```
CLEAN → WATCH (1 signal) → FLAGGED (2+ signals) → REVIEWED (manual)
```

State persists across runs — a creator stays FLAGGED until manually reviewed. Prevents alert fatigue from repeated false positives being re-sent every hour.

---

## Architecture

```
Airflow (hourly, runs 30 min before payout job)
    └── PythonOperator
            ├── Load engagement events (current window)
            ├── Run 3 detection checks per creator
            ├── Load previous state from file
            ├── Update state machine per creator
            ├── Save state
            └── Slack alert for WATCH + FLAGGED creators
```

---

## Files

| File | Description |
|---|---|
| `detector.py` | Detection rules + state machine + Slack alerts |
| `dag.py` | Airflow DAG — hourly, runs before payout |
| `demo_data.py` | Demo engagement events (normal, suspicious, borderline) |
| `requirements.txt` | Dependencies |

---

## Sample Slack Alert

```
🚨 Froker Engagement Alert — DEMO_CREATOR_002
Status: FLAGGED
Signals detected:
  • velocity:P002:80_events_in_5min
  • ip_cluster:P002:87%_from_top5_ips
  • zscore:P002:likes:z=11.6
Detected at: 2024-11-03 13:30 IST
```

---

## Run locally

```bash
pip install -r requirements.txt
python detector.py
```

---

## Design Decisions

| Decision | Reasoning |
|---|---|
| Rules + z-score, no ML model | Small dataset at a startup. Rules are auditable and explainable — important when disputing a creator's payout |
| Personal baseline per creator | A creator with 5K followers flagged at the same absolute threshold as one with 50K would produce constant false positives |
| State machine, not stateless alerts | Without state, every hourly run re-alerts the same flagged creator. The team gets 24 Slack messages a day for one bad actor |
| Runs 30 min before payout | Gives the ops team a window to review and block payout manually if needed |
