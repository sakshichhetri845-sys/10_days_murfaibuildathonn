"""
Real Demo Scenario Verification Script for Day 8 — HealthSathi Call Analytics.
"""

import sys
import os
import json
from db import init_db, save_call_analytics, get_call_analytics

def main():
    print("=== DAY 8 HEALTHSATHI CALL ANALYTICS DEMO SCENARIOS ===")
    init_db()

    initial = get_call_analytics(range_filter="all")
    initial_total = initial["total_calls"]
    initial_succ = initial["successful_calls"]
    initial_failed = initial["failed_calls"]
    print(f"Initial metrics: Total={initial_total}, Successful={initial_succ}, Failed={initial_failed}")

    # SCENARIO 1: SUCCESSFUL TRIAGE CALL
    print("\n--- Scenario 1: User reports dizzy symptoms (Triage Call) ---")
    s1 = save_call_analytics(
        session_id=f"demo_session_triage_{os.urandom(4).hex()}",
        duration=42,
        channel="browser",
        outcome="successful",
        outcome_type="TRIAGE_COMPLETED",
    )
    print(f"Recorded Triage Call: {json.dumps(s1, indent=2)}")

    # SCENARIO 2: FAILED INCOMPLETE CALL
    print("\n--- Scenario 2: User disconnects early before concern handled ---")
    s2 = save_call_analytics(
        session_id=f"demo_session_incomplete_{os.urandom(4).hex()}",
        duration=8,
        channel="browser",
        outcome="failed",
        outcome_type="INCOMPLETE",
    )
    print(f"Recorded Incomplete Call: {json.dumps(s2, indent=2)}")

    # VERIFY METRICS
    updated = get_call_analytics(range_filter="all")
    print("\n--- Updated Dashboard Metrics ---")
    print(f"Total Calls: {updated['total_calls']} (increased by {updated['total_calls'] - initial_total})")
    print(f"Successful Calls: {updated['successful_calls']} (increased by {updated['successful_calls'] - initial_succ})")
    print(f"Failed Calls: {updated['failed_calls']} (increased by {updated['failed_calls'] - initial_failed})")
    print(f"Success Rate: {updated['success_rate']}%")
    print(f"Outcome Breakdown: {json.dumps(updated['outcome_breakdown'], indent=2)}")

    assert updated['total_calls'] >= initial_total + 2
    assert updated['successful_calls'] >= initial_succ + 1
    assert updated['failed_calls'] >= initial_failed + 1
    print("\n[OK] All Day 8 Demo Scenarios verified successfully!")

if __name__ == "__main__":
    main()
