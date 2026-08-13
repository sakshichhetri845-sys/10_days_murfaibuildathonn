import os
import time
from db import init_db, save_call_analytics, get_call_analytics, get_nearby_facilities

def verify_live_facility_logging():
    init_db()
    session_id = f"healthsathi_room_test_pune_hospital_{int(time.time())}"
    
    # 1. Simulate facility lookup for Pune
    facilities = get_nearby_facilities("Pune")
    print(f"Queried Pune facilities: Found {len(facilities)} facilities.")
    for f in facilities:
        print(f" - {f['facility_name']} ({f['facility_type']}): {f['address']}")
    
    # 2. Simulate call outcome persistence for FACILITY_FOUND
    save_call_analytics(
        session_id=session_id,
        duration=42,
        channel="browser",
        outcome="successful",
        outcome_type="FACILITY_FOUND",
    )
    
    # 3. Retrieve analytics dashboard data
    analytics = get_call_analytics("all")
    print("\n--- Call Analytics Dashboard State ---")
    print(f"Total Calls: {analytics['total_calls']}")
    print(f"Successful Calls: {analytics['successful_calls']}")
    print(f"Failed Calls: {analytics['failed_calls']}")
    print(f"Success Rate: {analytics['success_rate']}%")
    print(f"Breakdown: {analytics['outcome_breakdown']}")
    print("Recent Calls (Top 3):")
    for call in analytics["recent_calls"][:3]:
        print(f" - ID: {call['session_id']} | Outcome: {call['outcome']} ({call['outcome_type']}) | Duration: {call['duration']}s")

if __name__ == "__main__":
    verify_live_facility_logging()
