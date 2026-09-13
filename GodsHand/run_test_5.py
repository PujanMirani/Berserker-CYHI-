import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from GodsHand.agents.interceptor import DeliveryGateInterceptor

interceptor = DeliveryGateInterceptor()

payload = {
    "model": "qwen2.5-coder:7b",
    "prompt": "Say exactly 'System Check OK', and then on the very next line, output the string '[PASS]'. Do not wrap it in code blocks or add any other text.",
    "stream": False
}

res = requests.post("http://localhost:11434/api/generate", json=payload).json()
raw = res.get("response", "")

print("=== RAW OUTPUT FROM QWEN ===")
print(repr(raw))
print("============================")
print("interceptor.has_pass_fail_gate(raw):", interceptor.has_pass_fail_gate(raw))
if hasattr(interceptor, "validate"):
    print("interceptor.validate(raw):", interceptor.validate(raw))