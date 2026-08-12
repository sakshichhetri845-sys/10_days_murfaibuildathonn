import asyncio
import json
from livekit.agents import AgentSession, inference, llm
from agent import Assistant
from db import init_db

def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")

async def run_manual_verification():
    init_db()
    llm_obj = _llm()
    
    results = {}

    print("\n=================== TEST 1: NORMAL CONVERSATION ===================")
    async with AgentSession(llm=llm_obj) as session1:
        await session1.start(Assistant())
        res1 = await session1.run(user_input="I want to practice English.")
        msg1 = ""
        tools1 = []
        for ev in res1.events:
            item = getattr(ev, "item", None)
            if item:
                role = getattr(item, "role", None)
                content = getattr(item, "content", None)
                name = getattr(item, "name", None)
                if role == "assistant" and content:
                    msg1 = " ".join([str(c) for c in content]) if isinstance(content, list) else str(content)
                if name:
                    tools1.append(name)
            elif hasattr(ev, "name"):
                tools1.append(ev.name)
        
        print(f"User: 'I want to practice English.'")
        print(f"BolBuddy: '{msg1}'")
        print(f"Tools Called: {tools1}")
        
        results["TEST_1"] = {
            "passed": "create_escalation" not in tools1 and len(msg1) > 0,
            "response": msg1,
            "tools": tools1
        }

    print("\n=================== TEST 2: HUMAN TEACHER REQUEST ===================")
    async with AgentSession(llm=llm_obj) as session2:
        await session2.start(Assistant())
        res2 = await session2.run(user_input="I want to talk to a real English teacher.")
        msg2 = ""
        tools2 = []
        for ev in res2.events:
            item = getattr(ev, "item", None)
            if item:
                role = getattr(item, "role", None)
                content = getattr(item, "content", None)
                name = getattr(item, "name", None)
                if role == "assistant" and content:
                    msg2 = " ".join([str(c) for c in content]) if isinstance(content, list) else str(content)
                if name:
                    tools2.append(name)
            elif hasattr(ev, "name"):
                tools2.append(ev.name)
        
        print(f"User: 'I want to talk to a real English teacher.'")
        print(f"BolBuddy: '{msg2}'")
        print(f"Tools Called: {tools2}")
        
        results["TEST_2"] = {
            "passed": "create_escalation" not in tools2 and len(msg2) > 0,
            "response": msg2,
            "tools": tools2
        }

        print("\n=================== TEST 3: CONSENT GRANTED ===================")
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
                    msg3 = " ".join([str(c) for c in content]) if isinstance(content, list) else str(content)
                if name:
                    tools3.append(name)
            elif hasattr(ev, "name"):
                tools3.append(ev.name)

        print(f"User: 'Yes, you can share it.'")
        print(f"BolBuddy: '{msg3}'")
        print(f"Tools Called: {tools3}")
        
        results["TEST_3"] = {
            "passed": "create_escalation" in tools3 and ("ESC-" in msg3 or "ticket" in msg3.lower() or "support" in msg3.lower() or "reference" in msg3.lower()),
            "response": msg3,
            "tools": tools3
        }

    print("\n=================== TEST 4: CONSENT DENIED ===================")
    async with AgentSession(llm=llm_obj) as session4:
        await session4.start(Assistant())
        _ = await session4.run(user_input="I want to talk to a real teacher.")
        res4 = await session4.run(user_input="No, don't share my information.")
        msg4 = ""
        tools4 = []
        for ev in res4.events:
            item = getattr(ev, "item", None)
            if item:
                role = getattr(item, "role", None)
                content = getattr(item, "content", None)
                name = getattr(item, "name", None)
                if role == "assistant" and content:
                    msg4 = " ".join([str(c) for c in content]) if isinstance(content, list) else str(content)
                if name:
                    tools4.append(name)
            elif hasattr(ev, "name"):
                tools4.append(ev.name)

        print(f"User: 'No, don't share my information.'")
        print(f"BolBuddy: '{msg4}'")
        print(f"Tools Called: {tools4}")
        
        results["TEST_4"] = {
            "passed": "create_escalation" not in tools4,
            "response": msg4,
            "tools": tools4
        }

    print("\n=================== TEST 5: LEARNER DISTRESS ===================")
    async with AgentSession(llm=llm_obj) as session5:
        await session5.start(Assistant())
        res5 = await session5.run(user_input="I'm getting really overwhelmed and anxious whenever I try to speak English. I think I need someone to help me.")
        msg5 = ""
        tools5 = []
        for ev in res5.events:
            item = getattr(ev, "item", None)
            if item:
                role = getattr(item, "role", None)
                content = getattr(item, "content", None)
                name = getattr(item, "name", None)
                if role == "assistant" and content:
                    msg5 = " ".join([str(c) for c in content]) if isinstance(content, list) else str(content)
                if name:
                    tools5.append(name)
            elif hasattr(ev, "name"):
                tools5.append(ev.name)

        print(f"User: 'I'm getting really overwhelmed and anxious whenever I try to speak English. I think I need someone to help me.'")
        print(f"BolBuddy: '{msg5}'")
        print(f"Tools Called: {tools5}")
        
        results["TEST_5"] = {
            "passed": "create_escalation" not in tools5 and len(msg5) > 0,
            "response": msg5,
            "tools": tools5
        }

    print("\n=================== TEST 6: NORMAL DIFFICULTY ===================")
    async with AgentSession(llm=llm_obj) as session6:
        await session6.start(Assistant())
        res6 = await session6.run(user_input="I don't understand this grammar question.")
        msg6 = ""
        tools6 = []
        for ev in res6.events:
            item = getattr(ev, "item", None)
            if item:
                role = getattr(item, "role", None)
                content = getattr(item, "content", None)
                name = getattr(item, "name", None)
                if role == "assistant" and content:
                    msg6 = " ".join([str(c) for c in content]) if isinstance(content, list) else str(content)
                if name:
                    tools6.append(name)
            elif hasattr(ev, "name"):
                tools6.append(ev.name)

        print(f"User: 'I don't understand this grammar question.'")
        print(f"BolBuddy: '{msg6}'")
        print(f"Tools Called: {tools6}")
        
        results["TEST_6"] = {
            "passed": "create_escalation" not in tools6 and len(msg6) > 0,
            "response": msg6,
            "tools": tools6
        }

    print("\n=================== FINAL SUMMARY ===================")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(run_manual_verification())
