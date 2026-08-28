# -*- coding: utf-8 -*-
"""
AIDA boshlangich strategiyalarni seed qilish.
python manage.py shell < self_improvement/seed.py
"""
from self_improvement.models import Strategy, KnowledgeChunk

strategies = [
    {
        "name": "Direct Answer Strategy",
        "domain": "general",
        "description": "Togri va qisqa javob berish",
        "prompt_template": "Siz AIDA - ilgor AI.\n\nTOPSHIRIQ: {{user_request}}\nMAQSAD: {{goal}}\n\nAniq va toliq javob bering:",
        "success_rate": 0.65,
    },
    {
        "name": "Step-by-Step Reasoning",
        "domain": "reasoning",
        "description": "Bosqichma-bosqich mantiqiy tahlil",
        "prompt_template": "Siz AIDA - mantiqiy tahlilchi.\n\nTOPSHIRIQ: {{user_request}}\n\n1. Muammoni tushunish\n2. Strategiya\n3. Yechish\n4. Tekshirish\n\nJAVOB:",
        "success_rate": 0.72,
    },
    {
        "name": "Code Expert Strategy",
        "domain": "code",
        "description": "Professional kod yozish",
        "prompt_template": "Siz AIDA - dasturchi.\n\nTOPSHIRIQ: {{user_request}}\nBILIMLAR: {{knowledge}}\n\nIshlaydigan kod yozing:",
        "success_rate": 0.70,
    },
    {
        "name": "Knowledge-Enhanced Strategy",
        "domain": "knowledge",
        "description": "Bilim bazasidan foydalanib javob berish",
        "prompt_template": "Siz AIDA - bilim mutaxassisi.\n\nTOPSHIRIQ: {{user_request}}\nBILIMLAR:\n{{knowledge}}\n\nToliq javob bering:",
        "success_rate": 0.68,
    },
    {
        "name": "Creative Generation Strategy",
        "domain": "creative",
        "description": "Ijodiy kontent yaratish",
        "prompt_template": "Siz AIDA - ijodiy AI.\n\nTOPSHIRIQ: {{user_request}}\n\nOriginal va ijodiy javob yozing:",
        "success_rate": 0.62,
    },
    {
        "name": "Math Solver Strategy",
        "domain": "math",
        "description": "Matematik masalalar yechish",
        "prompt_template": "Siz AIDA - matematik mutaxassis.\n\nMASALA: {{user_request}}\n\nBosqichma-bosqich yechim:\n",
        "success_rate": 0.75,
    },
    {
        "name": "Language Expert Strategy",
        "domain": "language",
        "description": "Til va matn tahlil",
        "prompt_template": "Siz AIDA - til mutaxassisi.\n\nTOPSHIRIQ: {{user_request}}\n\nProfessional til tahlili:",
        "success_rate": 0.67,
    },
]

created = 0
for s in strategies:
    obj, is_new = Strategy.objects.get_or_create(name=s["name"], defaults=s)
    if is_new:
        created += 1

print(f"Strategiyalar: {created} yangi, {Strategy.objects.count()} jami.")
print("Seed muvaffaqiyatli yakunlandi!")
