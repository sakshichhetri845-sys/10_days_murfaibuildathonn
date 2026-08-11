"""
Day 6 Outbound Health Follow-up Tests.
Tests for outbound room detection, memory loading, prompt selection, and missing memory fallback.
"""

from memory_service import MemoryService
from prompts.outbound_prompt import build_outbound_instructions


def test_outbound_prompt_building_with_context():
    sample_context = "Name: Riya Verma\nPrevious guidance: Routine Checkup Advice"
    instructions = build_outbound_instructions(sample_context)
    assert "HealthSaathi" in instructions
    assert "Riya Verma" in instructions
    assert "Routine Checkup Advice" in instructions
    assert "automated" in instructions


def test_outbound_prompt_building_missing_context():
    instructions = build_outbound_instructions("")
    assert "HealthSaathi" in instructions
    assert "No prior interaction recorded" in instructions
    assert "automated" in instructions


def test_outbound_room_name_parsing():
    room_names = [
        "outbound-followup-riya_verma",
        "outbound-riya_verma",
        "followup-riya_verma",
    ]
    for rname in room_names:
        clean_id = rname
        for prefix in ["outbound-followup-", "outbound-", "followup-"]:
            if clean_id.startswith(prefix):
                clean_id = clean_id[len(prefix) :]
                break
        assert clean_id == "riya_verma"


def test_sqlite_memory_loading_for_outbound():
    user_id = "test_day6_riya"
    # Clean up any previous test run
    MemoryService.delete_memory(user_id)

    # Save test memory
    saved = MemoryService.save_memory(
        user_id=user_id,
        name="Riya Verma",
        ongoing_conditions=["Mild Hypertension"],
        last_triage_outcome="Routine Checkup Advice",
    )
    assert saved

    # Retrieve memory
    mem = MemoryService.get_memory(user_id)
    assert mem is not None
    assert mem["name"] == "Riya Verma"
    assert mem["ongoing_conditions"] == ["Mild Hypertension"]
    assert mem["last_triage_outcome"] == "Routine Checkup Advice"

    summary = MemoryService.format_memory_summary(mem)
    assert "Riya Verma" in summary
    assert "Mild Hypertension" in summary

    # Clean up
    MemoryService.delete_memory(user_id)


def test_missing_memory_fallback():
    user_id = "non_existent_user_9999"
    mem = MemoryService.get_memory(user_id)
    assert mem is None

    # Verify build_outbound_instructions handles None/empty context gracefully
    formatted_summary = MemoryService.format_memory_summary(mem)
    instructions = build_outbound_instructions(formatted_summary)
    assert "No prior interaction recorded" in instructions


def test_outbound_opening_behavior_requirements():
    instructions = build_outbound_instructions("Name: Riya Verma")
    # Rule 1: Identify agent
    assert "HealthSaathi" in instructions
    # Rule 2: Identify automated status
    assert "automated" in instructions
    # Rule 3: Explain why calling
    assert "follow-up" in instructions
    # Rule 4: Explain how to make it stop / decline option
    assert "end the call at any time" in instructions
    # Rule 5: Consent check / continue check
    assert (
        "Would you like to continue?" in instructions
        or "Is this a good time to talk?" in instructions
        or "convenient time" in instructions
    )

    # Rule 6: Response handling for decline calls end_call
    assert "end_call" in instructions
