import json

from django.test import TestCase

from .security import generate_access_key_with_profile


class PlatformChatTests(TestCase):
    def test_chat_code_prompt_enables_coder_mode(self):
        response = self.client.post(
            "/api/chat/",
            data=json.dumps(
                {
                    "prompt": "React frontend uchun kod yoz, panel component kerak",
                    "session_id": "test-coder-mode",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        message = response.json()["message"]
        self.assertIn("Coder rejimi", message)
        self.assertIn("```tsx", message)

    def test_learning_prompt_is_remembered_in_context(self):
        session_id = "test-learning-context"
        learn_response = self.client.post(
            "/api/chat/",
            data=json.dumps(
                {
                    "prompt": "eslab qol: loyiha premium Uzbek AI dashboard",
                    "session_id": session_id,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(learn_response.status_code, 200)
        self.assertIn("premium Uzbek AI dashboard", learn_response.json()["message"])

        followup_response = self.client.post(
            "/api/chat/",
            data=json.dumps(
                {
                    "prompt": "shu loyiha uchun reja ber",
                    "session_id": session_id,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(followup_response.status_code, 200)
        self.assertIn("premium Uzbek AI dashboard", followup_response.json()["message"])

    def test_platform_chat_uses_access_key_profile(self):
        _, secret = generate_access_key_with_profile(
            "Moda key",
            {
                "platform_name": "AIDA Fashion",
                "business_type": "kiyim do'koni",
                "audience": "yosh ayollar",
                "tone": "iliq va premium",
                "assistant_goal": "sotuvni oshirish",
                "custom_instructions": "Qisqa va ishonchli yoz",
            },
        )

        response = self.client.post(
            "/api/platform/chat/",
            data=json.dumps(
                {
                    "prompt": "Mijozga yangi kolleksiya haqida javob yoz",
                    "page": "product",
                    "customer_intent": "sotib olishdan oldin so'rayapti",
                    "locale": "uz-UZ",
                }
            ),
            content_type="application/json",
            HTTP_X_AIDA_KEY=secret,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("kiyim", payload["message"].lower())
        self.assertEqual(payload["key_name"], "Moda key")

    def test_key_create_stores_profile(self):
        response = self.client.post(
            "/api/keys/create/",
            data=json.dumps(
                {
                    "name": "Store key",
                    "platform_name": "AIDA Store",
                    "business_type": "kiyim do'koni",
                    "audience": "erkaklar",
                    "tone": "sotuvga yaqin",
                    "assistant_goal": "savatga olib borish",
                    "custom_instructions": "Qisqa yoz",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["platform_name"], "AIDA Store")
        self.assertEqual(payload["business_type"], "kiyim do'koni")
