# -*- coding: utf-8 -*-
"""
AIDA Multi-Agent Collaboration Test
===================================
1. Django orqali get_orchestrator() ni yuklaydi.
2. Tizimdagi ro'yxatdan o'tgan barcha agentlar ro'yxatini oladi.
3. Oddiy workflow statusini tekshiradi va agentlararo ulanishlarni o'qiydi.
"""
import django, os, asyncio

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AIDA.settings")
django.setup()

from webapp.agents.orchestrator import get_orchestrator

async def test_run():
    print("=" * 60)
    print("AIDA MULTI-AGENT COLONY TEST")
    print("=" * 60)
    
    orch = get_orchestrator()
    status = orch.get_status()
    
    print(f"\n[1] Faol agentlar soni: {len(status['agents'])} ta")
    for agent in status["agents"]:
        print(f"  - [{agent.get('type', 'Agent')}] {agent['name']} ({agent['status']})")
        print(f"    Sohalar (Capabilities): {agent.get('capabilities', [])}")

    print(f"\n[2] Tizimdagi ish oqimlari (Workflows):")
    for wf in status["workflows"]:
        print(f"  - {wf}")
        
    print(f"\n[3] Gateway holati: {status['gateway']}")
    print("=" * 60)

asyncio.run(test_run())
