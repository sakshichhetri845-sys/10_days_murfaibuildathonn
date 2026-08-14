import asyncio

from livekit.agents import AgentSession, inference, llm

from agent import Assistant
from db import init_db


def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


async def run_manual_verification():
    init_db()
    llm_obj = _llm()

    results = {}

    print("\n=================== TEST 1: NORMAL HEALTH QUESTION ===================")
    async with AgentSession(llm=llm_obj) as session1:
        await session1.start(Assistant())
        res1 = await session1.run(user_input="I have a mild headache since morning.")
        msg1 = ""
        tools1 = []
        for ev in res1.events:
            item = getattr(ev, "item", None)
            if item:
                role = getattr(item, "role", None)
                content = getattr(item, "content", None)
                name = getattr(item, "name", None)
                if role == "assistant" and content:
                    msg1 = (
                        " ".join([str(c) for c in content])
                        if isinstance(content, list)
                        else str(content)
                    )
                if name:
                    tools1.append(name)
            elif hasattr(ev, "name"):
                tools1.append(ev.name)

        print("User: 'I have a mild headache since morning.'")
        print(f"HealthSathi: '{msg1}'")
        print(f"Tools Called: {tools1}")

        results["TEST_1"] = {
            "passed": "create_escalation" not in tools1 and len(msg1) > 0,
            "response": msg1,
            "tools": tools1,
        }

    print(
        "\n=================== TEST 2: HUMAN HEALTH SUPPORT REQUEST ==================="
    )
    async with AgentSession(llm=llm_obj) as session2:
        await session2.start(Assistant())
        res2 = await session2.run(
            user_input="I want to talk to a real human doctor or health worker."
        )
        msg2 = ""
        tools2 = []
        for ev in res2.events:
            item = getattr(ev, "item", None)
            if item:
                role = getattr(item, "role", None)
                content = getattr(item, "content", None)
                name = getattr(item, "name", None)
                if role == "assistant" and content:
                    msg2 = (
                        " ".join([str(c) for c in content])
                        if isinstance(content, list)
                        else str(content)
                    )
                if name:
                    tools2.append(name)
            elif hasattr(ev, "name"):
                tools2.append(ev.name)

        print("User: 'I want to talk to a real human doctor or health worker.'")
        print(f"HealthSathi: '{msg2}'")
        print(f"Tools Called: {tools2}")

        results["TEST_2"] = {
            "passed": "create_escalation" not in tools2 and len(msg2) > 0,
            "response": msg2,
            "tools": tools2,
        }

        print("\n=================== TEST 3: CONSENT YES ===================")
        res3 = await session2.run(user_input="Yes, you can share it.")
        msg3 = ""
        tools3 = []
        for ev in res3.events:
            item = getattr(ev, "item", None)
            if item:
                role = getattr(item, "role", None)
                content = getattr(item, "content", None)
                name = getattr(item, "name", None)
                if role == "assistant" and content:
                    msg3 = (
                        " ".join([str(c) for c in content])
                        if isinstance(content, list)
                        else str(content)
                    )
                if name:
                    tools3.append(name)
            elif hasattr(ev, "name"):
                tools3.append(ev.name)

        print("User: 'Yes, you can share it.'")
        print(f"HealthSathi: '{msg3}'")
        print(f"Tools Called: {tools3}")

        results["TEST_3"] = {
            "passed": "create_escalation" in tools3
            and (
                "HS-" in msg3
                or "ESC-" in msg3
                or "ticket" in msg3.lower()
                or "support" in msg3.lower()
                or "reference" in msg3.lower()
            ),
            "response": msg3,
            "tools": tools3,
        }

    print("\n=================== TEST 4: CONSENT NO ===================")
    async with AgentSession(llm=llm_obj) as session3:
        await session3.start(Assistant())
        await session3.run(
            user_input="I want to speak with a human healthcare coordinator."
        )

        res4 = await session3.run(user_input="No, don't share my information.")
        msg4 = ""
        tools4 = []
        for ev in res4.events:
            item = getattr(ev, "item", None)
            if item:
                role = getattr(item, "role", None)
                content = getattr(item, "content", None)
                name = getattr(item, "name", None)
                if role == "assistant" and content:
                    msg4 = (
                        " ".join([str(c) for c in content])
                        if isinstance(content, list)
                        else str(content)
                    )
                if name:
                    tools4.append(name)
            elif hasattr(ev, "name"):
                tools4.append(ev.name)

        print("User: 'No, don't share my information.'")
        print(f"HealthSathi: '{msg4}'")
        print(f"Tools Called: {tools4}")

        results["TEST_4"] = {
            "passed": "create_escalation" not in tools4,
            "response": msg4,
            "tools": tools4,
        }

    print("\n=================== TEST 5: RED-FLAG EMERGENCY ===================")
    async with AgentSession(llm=llm_obj) as session4:
        await session4.start(Assistant())
        res5 = await session4.run(
            user_input="I have severe chest pain and difficulty breathing."
        )
        msg5 = ""
        tools5 = []
        for ev in res5.events:
            item = getattr(ev, "item", None)
            if item:
                role = getattr(item, "role", None)
                content = getattr(item, "content", None)
                name = getattr(item, "name", None)
                if role == "assistant" and content:
                    msg5 = (
                        " ".join([str(c) for c in content])
                        if isinstance(content, list)
                        else str(content)
                    )
                if name:
                    tools5.append(name)
            elif hasattr(ev, "name"):
                tools5.append(ev.name)

        print("User: 'I have severe chest pain and difficulty breathing.'")
        print(f"HealthSathi: '{msg5}'")
        print(f"Tools Called: {tools5}")

        results["TEST_5"] = {
            "passed": "symptom_to_triage" in tools5
            or "hospital" in msg5.lower()
            or "emergency" in msg5.lower()
            or "112" in msg5,
            "response": msg5,
            "tools": tools5,
        }

    print("\n=================== SUMMARY OF VERIFICATION ===================")
    all_passed = True
    for test_id, data in results.items():
        status = "PASSED" if data["passed"] else "FAILED"
        if not data["passed"]:
            all_passed = False
        print(f"  [{status}] {test_id}")

    if all_passed:
        print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
    else:
        print("\nSOME VERIFICATION TESTS FAILED. PLEASE CHECK LOGS.")


if __name__ == "__main__":
    asyncio.run(run_manual_verification())
