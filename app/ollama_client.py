# app/ollama_client.py
from __future__ import annotations
import json
import os
import requests
from typing import Any, Dict, Optional


class OllamaClient:
    """Unified client for Ollama API calls with configurable defaults."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 120,
    ):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "kimi-k2-thinking:cloud")
        self.timeout = timeout
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.2,
        format: Optional[str] = None,
    ) -> str:
        """Generate text completion from Ollama."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model or self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if format:
            payload["format"] = format
        
        try:
            r = requests.post(url, json=payload, timeout=self.timeout)
            r.raise_for_status()
            return r.json()["response"]
        except requests.RequestException as e:
            raise RuntimeError(f"Ollama API error: {e}")
    
    def generate_json(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Generate and parse JSON response from Ollama."""
        response = self.generate(
            prompt=prompt,
            model=model,
            temperature=temperature,
            format="json",
        )
        return extract_json(response)


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
        try:
            return json.loads(candidate)
        except Exception:
            pass

    raise ValueError("Could not parse JSON from Ollama output.")


# Backward compatibility
def ollama_generate(
    prompt: str,
    model: str = "kimi-k2-thinking:cloud",
    base_url: str = "http://localhost:11434",
    temperature: float = 0.2,
) -> str:
    """Legacy function for backward compatibility."""
    client = OllamaClient(base_url=base_url, model=model)
    return client.generate(prompt=prompt, temperature=temperature)
