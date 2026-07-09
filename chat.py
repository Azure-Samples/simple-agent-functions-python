"""Console chat client for the Repo Digest function app."""
import os
import urllib.request

BASE_URL = os.environ.get("AGENT_URL", "http://localhost:7071").rstrip("/")
FUNCTION_KEY = os.environ.get("FUNCTION_KEY", "")

print(f"=== Repo Digest Agent Chat ===")
print(f"Endpoint: {BASE_URL}/api/ask")
print("Ask for a daily digest, or include a public repo like microsoft-foundry/foundry-samples.")
print("Type 'exit' or 'quit' to end.\n")

while True:
    message = input("You: ").strip()
    if not message or message.lower() in ("exit", "quit"):
        print("Goodbye!")
        break

    url = f"{BASE_URL}/api/ask"
    if FUNCTION_KEY:
        url += f"?code={FUNCTION_KEY}"
    try:
        req = urllib.request.Request(url, data=message.encode(), method="POST")
        with urllib.request.urlopen(req) as resp:
            print(f"\nAgent: {resp.read().decode()}\n")
    except Exception as e:
        print(f"\nError: {e}\n")
