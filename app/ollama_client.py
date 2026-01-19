# app/ollama_client.py
from __future__ import annotations
import json
import requests
from typing import Any, Dict, Optional


def ollama_generate(
    prompt: str,
    model: str = "kimi-k2-thinking:cloud",
    base_url: str = "http://localhost:11434",
    temperature: float = 0.2,
) -> str:
    url = f"{base_url}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["response"]


def extract_json(text: str) -> Dict[str, Any]:
    """
    Tries to extract the first valid JSON object from model output.
    Works around models that wrap JSON with commentary.
    """
    text = text.strip()

    # Fast path: whole string is JSON
    try:
        return json.loads(text)
    except Exception:
        pass

    # Find first {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        return json.loads(candidate)

    raise ValueError("Could not parse JSON from Ollama output.")
