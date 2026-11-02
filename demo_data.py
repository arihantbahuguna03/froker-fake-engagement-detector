"""
Demo engagement event data for fake engagement detection.
All data is synthetic — no real creator names, IDs, or metrics.
"""

from datetime import datetime, timedelta

BASE_TIME = datetime(2024, 11, 3, 14, 0, 0)

# Normal creator — clean engagement pattern
DEMO_NORMAL_EVENTS = [
    {"creator_id": "DEMO_CREATOR_001", "post_id": "P001", "event_type": "like",
     "ts": BASE_TIME + timedelta(minutes=i * 8), "actor_id": f"USER_{1000+i}",
     "ip": f"192.168.1.{(i % 50) + 10}"}
    for i in range(20)
] + [
    {"creator_id": "DEMO_CREATOR_001", "post_id": "P001", "event_type": "comment",
     "ts": BASE_TIME + timedelta(minutes=i * 25), "actor_id": f"USER_{2000+i}",
     "ip": f"192.168.1.{(i % 30) + 20}"}
    for i in range(8)
]

# Suspicious creator — like spike + comment cluster from same IPs
DEMO_SUSPICIOUS_EVENTS = [
    # 80 likes in 3 minutes from 5 IPs rotating
    {"creator_id": "DEMO_CREATOR_002", "post_id": "P002", "event_type": "like",
     "ts": BASE_TIME + timedelta(seconds=i * 2), "actor_id": f"BOT_USER_{i}",
     "ip": f"10.0.0.{(i % 5) + 1}"}
    for i in range(80)
] + [
    # 40 comments in 4 minutes — same IP cluster
    {"creator_id": "DEMO_CREATOR_002", "post_id": "P002", "event_type": "comment",
     "ts": BASE_TIME + timedelta(seconds=240 + i * 6), "actor_id": f"BOT_USER_{100+i}",
     "ip": f"10.0.0.{(i % 3) + 1}"}
    for i in range(40)
]

# Borderline creator — elevated but not clearly fake
DEMO_BORDERLINE_EVENTS = [
    {"creator_id": "DEMO_CREATOR_003", "post_id": "P003", "event_type": "like",
     "ts": BASE_TIME + timedelta(minutes=i * 3), "actor_id": f"USER_{3000+i}",
     "ip": f"172.16.0.{(i % 20) + 5}"}
    for i in range(35)
] + [
    {"creator_id": "DEMO_CREATOR_003", "post_id": "P003", "event_type": "comment",
     "ts": BASE_TIME + timedelta(minutes=i * 10), "actor_id": f"USER_{4000+i}",
     "ip": f"172.16.0.{(i % 15) + 10}"}
    for i in range(12)
]

ALL_DEMO_EVENTS = DEMO_NORMAL_EVENTS + DEMO_SUSPICIOUS_EVENTS + DEMO_BORDERLINE_EVENTS

# Per-creator historical baselines (normal week avg)
CREATOR_BASELINES = {
    "DEMO_CREATOR_001": {"avg_likes_per_post": 18.0, "avg_comments_per_post": 6.0, "std_likes": 4.0, "std_comments": 2.0},
    "DEMO_CREATOR_002": {"avg_likes_per_post": 22.0, "avg_comments_per_post": 8.0, "std_likes": 5.0, "std_comments": 2.5},
    "DEMO_CREATOR_003": {"avg_likes_per_post": 28.0, "avg_comments_per_post": 9.0, "std_likes": 6.0, "std_comments": 3.0},
}

SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/DEMO_WEBHOOK_URL"
STATE_FILE_PATH   = "/tmp/froker_engagement_state.json"
DAG_OWNER         = "demo-owner@demo.com"
