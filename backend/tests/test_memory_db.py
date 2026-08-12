"""
Persistence and database unit tests for HealthSathi user memory module (src/db.py).
"""

import os
import tempfile
import time

import pytest

from db import (
    create_or_update_user,
    delete_user,
    get_or_create_user,
    get_user,
    init_db,
    record_health_preferences,
    update_last_interaction,
)


@pytest.fixture
def temp_db():
    """Fixture providing a temporary SQLite database file for isolated testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    init_db(db_path=db_path)
    yield db_path

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except PermissionError:
        pass


def test_create_save_close_and_retrieve_user(temp_db):
    """
    Persistence Test:
    1. Create a user
    2. Save health facts
    3. Simulate closing & restarting the connection
    4. Verify data persists accurately
    """
    user_id = "test_user_ramesh_123"
    facts = {
        "reminder_preference": "Medication reminder",
        "contact_preference": "phone",
        "interaction_preferences": ["slow speech"],
    }

    created_record = create_or_update_user(
        user_id=user_id,
        name="Sakshyam",
        language_preference="English + Hindi",
        facts=facts,
        db_path=temp_db,
    )

    assert created_record is not None
    assert created_record["user_id"] == user_id
    assert created_record["name"] == "Sakshyam"
    assert created_record["language_preference"] == "English + Hindi"
    assert created_record["facts"]["reminder_preference"] == "Medication reminder"

    retrieved_user = get_user(user_id=user_id, db_path=temp_db)

    assert retrieved_user is not None
    assert retrieved_user["user_id"] == user_id
    assert retrieved_user["name"] == "Sakshyam"
    assert retrieved_user["language_preference"] == "English + Hindi"
    assert retrieved_user["facts"]["reminder_preference"] == "Medication reminder"
    assert retrieved_user["facts"]["contact_preference"] == "phone"
    assert "slow speech" in retrieved_user["facts"]["interaction_preferences"]


def test_same_user_id_returns_same_record(temp_db):
    """Verify that multiple queries with the same user ID return the same persistent record."""
    user_id = "persistent_user_001"

    created = create_or_update_user(
        user_id=user_id,
        name="Ananya",
        language_preference="Hinglish",
        facts={"reminder_preference": "Appointment check-in"},
        db_path=temp_db,
    )

    first_fetch = get_user(user_id, db_path=temp_db)
    second_fetch = get_user(user_id, db_path=temp_db)
    get_or_create_res = get_or_create_user(user_id, db_path=temp_db)

    assert (
        created["user_id"]
        == first_fetch["user_id"]
        == second_fetch["user_id"]
        == get_or_create_res["user_id"]
    )
    assert first_fetch["name"] == second_fetch["name"] == "Ananya"
    assert first_fetch["facts"]["reminder_preference"] == "Appointment check-in"


def test_new_user_id_creates_separate_record(temp_db):
    """Verify that distinct user IDs create completely independent memory records."""
    user_id_1 = "user_delhi_101"
    user_id_2 = "user_mumbai_102"

    user1 = create_or_update_user(
        user_id=user_id_1,
        name="Vikram",
        language_preference="Hindi",
        facts={"reminder_preference": "General health check-in"},
        db_path=temp_db,
    )

    user2 = create_or_update_user(
        user_id=user_id_2,
        name="Siddharth",
        language_preference="English",
        facts={"reminder_preference": "Doctor visit preparation"},
        db_path=temp_db,
    )

    assert user1["user_id"] != user2["user_id"]
    assert user1["name"] == "Vikram"
    assert user2["name"] == "Siddharth"
    assert user1["language_preference"] == "Hindi"
    assert user2["language_preference"] == "English"


def test_update_existing_user_health_preferences(temp_db):
    """Verify updating an existing user's health facts preserves prior information."""
    user_id = "user_update_789"

    get_or_create_user(
        user_id=user_id,
        name="Kavita",
        language_preference="English + Hindi",
        db_path=temp_db,
    )

    record_health_preferences(
        user_id=user_id,
        reminder_preference="Daily 8am pill",
        contact_preference="phone",
        interaction_preferences=["morning preferred"],
        db_path=temp_db,
    )

    updated = record_health_preferences(
        user_id=user_id,
        interaction_preferences=["morning preferred", "brief responses"],
        db_path=temp_db,
    )

    assert updated["name"] == "Kavita"
    assert updated["facts"]["reminder_preference"] == "Daily 8am pill"
    assert updated["facts"]["contact_preference"] == "phone"
    assert updated["facts"]["interaction_preferences"] == [
        "morning preferred",
        "brief responses",
    ]


def test_last_interaction_timestamp(temp_db):
    """Verify updating last_interaction updates timestamps correctly."""
    user_id = "timestamp_user_999"

    user = get_or_create_user(user_id=user_id, name="Rahul", db_path=temp_db)
    t1 = user["last_interaction"]

    time.sleep(0.01)

    success = update_last_interaction(user_id=user_id, db_path=temp_db)
    assert success is True

    refreshed = get_user(user_id=user_id, db_path=temp_db)
    t2 = refreshed["last_interaction"]

    assert t1 is not None
    assert t2 is not None
    assert t2 >= t1


def test_error_handling_invalid_inputs_and_nonexistent_users(temp_db):
    """Verify that invalid inputs or non-existent records fail gracefully without crashing."""
    assert get_user(user_id="non_existent_id", db_path=temp_db) is None
    assert get_user(user_id="", db_path=temp_db) is None
    assert create_or_update_user(user_id="", db_path=temp_db) is None
    assert update_last_interaction(user_id="", db_path=temp_db) is False

    create_or_update_user(user_id="temp_to_delete", name="Temp", db_path=temp_db)
    assert delete_user("temp_to_delete", db_path=temp_db) is True
    assert get_user("temp_to_delete", db_path=temp_db) is None
