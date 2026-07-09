"""Console chat client for the Simple Agent hosted agent."""
import json
import os
import urllib.request

BASE_URL = os.environ.get("AGENT_URL", "http://localhost:8088").rstrip("/")


def _extract_response_text(response):
    if isinstance(response, dict):
        if response.get("output_text"):
            return response["output_text"]
        for item in response.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in ("output_text", "text") and content.get("text"):
                    return content["text"]
    return json.dumps(response)


print("=== Simple Agent Chat ===")
print(f"Endpoint: {BASE_URL}/responses")
print(f"Type 'exit' or 'quit' to end.\n")

while True:
    message = input("You: ").strip()
    if not message or message.lower() in ("exit", "quit"):
        print("Goodbye!")
        break

    url = f"{BASE_URL}/responses"
    try:
        body = json.dumps({"input": message, "stream": False}).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            response = json.loads(resp.read().decode())
            print(f"\nAgent: {_extract_response_text(response)}\n")
    except Exception as e:
        print(f"\nError: {e}\n")
