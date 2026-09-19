from types import SimpleNamespace

from agent import agent as agent_module
from agent.agent import extract_text_from_response


def test_extract_text_from_response_handles_function_call():
    response = SimpleNamespace(
        parts=[
            SimpleNamespace(
                function_call={"name": "daily_plan", "args": {"date": "2026-09-17"}}
            )
        ]
    )

    text = extract_text_from_response(response)

    assert "tool" in text.lower()
    assert "not enabled" in text.lower()


def test_gemini_follow_up_preserves_thought_signature(monkeypatch):
    model_content = SimpleNamespace(
        role="model",
        parts=[
            SimpleNamespace(
                function_call=SimpleNamespace(name="list_materials", args={}),
                thought_signature=b"signature",
            )
        ],
    )
    first_response = SimpleNamespace(
        candidates=[SimpleNamespace(content=model_content)]
    )
    final_response = SimpleNamespace(text="Here are the materials.")

    class FakeModel:
        def __init__(self):
            self.requests = []

        def generate_content(self, content):
            self.requests.append(content)
            return first_response if len(self.requests) == 1 else final_response

    monkeypatch.setattr(agent_module.tools, "dispatch", lambda conn, name, args: [])
    client = agent_module.GeminiClient.__new__(agent_module.GeminiClient)
    client.model = FakeModel()

    _, reply = client.generate([{"role": "user", "content": "List my materials"}], conn=object())

    assert reply == "Here are the materials."
    assert client.model.requests[1][-2] is model_content
    assert client.model.requests[1][-2].parts[0].thought_signature == b"signature"
