# -*- coding: utf-8 -*-
"""Teste rápido da API key Gemini — lê do .env"""
import json
import urllib.request
from dotenv import load_dotenv
import os

load_dotenv()
key = os.getenv("GEMINI_API_KEY", "")
model = os.getenv("LLM_MODEL", "gemini-2.5-flash-lite")
print(f"Key: {key[:12]}...")
print(f"Model: {model}")

url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={key}"
payload = {
    "contents": [{"role": "user", "parts": [{"text": "Responda apenas: OK FUNCIONANDO"}]}],
    "generationConfig": {"temperature": 0.1, "maxOutputTokens": 50}
}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    text = body["candidates"][0]["content"]["parts"][0]["text"]
    usage = body.get("usageMetadata", {})
    print(f"SUCESSO: {text.strip()}")
    print(f"Tokens input: {usage.get('promptTokenCount', 0)}")
    print(f"Tokens output: {usage.get('candidatesTokenCount', 0)}")
except urllib.error.HTTPError as e:
    print(f"HTTP ERROR {e.code}: {e.read().decode('utf-8', errors='replace')}")
except Exception as e:
    print(f"ERRO: {e}")
