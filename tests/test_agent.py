from types import SimpleNamespace

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
