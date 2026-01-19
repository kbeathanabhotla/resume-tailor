# app/score.py
from __future__ import annotations
from typing import Dict, Any

from app.render_text import resume_to_text
from app.ollama_client import ollama_generate, extract_json


def compute_ats_score_llm(
    job_description: str,
    tailored_resume: Dict[str, Any],
    model: str = "kimi-k2-thinking:cloud",
    ollama_base_url: str = "http://localhost:11434",
) -> Dict[str, Any]:
    resume_text = resume_to_text(tailored_resume)

    with open("prompts/ats_score.txt", "r", encoding="utf-8") as f:
        prompt = f.read()

    prompt = prompt.replace("{{ job_description }}", job_description)
    prompt = prompt.replace("{{ resume_text }}", resume_text)

    raw = ollama_generate(
        prompt=prompt,
        model=model,
        base_url=ollama_base_url,
        temperature=0.2,
    )

    data = extract_json(raw)

    # Minimal validation / normalization
    score = float(data.get("ats_score", 0))
    data["ats_score"] = max(0.0, min(100.0, score))

    conf = float(data.get("confidence", 0))
    data["confidence"] = max(0.0, min(100.0, conf))

    return data
