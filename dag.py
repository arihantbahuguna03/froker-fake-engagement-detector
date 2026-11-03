"""
Airflow DAG — Fake Engagement Detector
Runs hourly. Checks all creator engagement events for anomalies.
Sends Slack alert for WATCH and FLAGGED creators before payout runs.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

DAG_ID    = "fake_engagement_detector"
DAG_OWNER = "demo-owner@demo.com"

default_args = {
    "owner":            DAG_OWNER,
    "retries":          0,
    "email_on_failure": False,
}

with DAG(
    dag_id=DAG_ID,
    default_args=default_args,
    description="Hourly fake engagement detection — flags suspicious creators before payout",
    schedule="30 * * * *",
    start_date=datetime(2024, 8, 1),
    catchup=False,
    tags=["fraud", "engagement"],
) as dag:

    def run_detection():
        import os
        os.environ["SLACK_ENABLED"] = "true"
        from detector import run_detector
        run_detector()

    detect = PythonOperator(
        task_id="detect_fake_engagement",
        python_callable=run_detection,
    )
