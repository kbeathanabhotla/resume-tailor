# app/score.py
from __future__ import annotations
from typing import Dict, Any, Optional

from app.render_text import resume_to_text
from app.ollama_client import OllamaClient


def compute_ats_score_llm(
    job_description: str,
    tailored_resume: Dict[str, Any],
    client: Optional[OllamaClient] = None,
) -> Dict[str, Any]:
    """
    Compute ATS alignment score between job description and resume.
    
    Args:
        job_description: Job description text
        tailored_resume: Tailored resume dictionary
        client: Optional OllamaClient instance (creates default if None)
    
    Returns:
        Dictionary with ats_score, confidence, and analysis
    """
    if client is None:
        client = OllamaClient()
    
    resume_text = resume_to_text(tailored_resume)

    with open("prompts/ats_score.txt", "r", encoding="utf-8") as f:
        prompt = f.read()

    prompt = prompt.replace("{{ job_description }}", job_description)
    prompt = prompt.replace("{{ resume_text }}", resume_text)

    data = client.generate_json(prompt=prompt, temperature=0.2)

    # Minimal validation / normalization
    score = float(data.get("ats_score", 0))
    data["ats_score"] = max(0.0, min(100.0, score))

    conf = float(data.get("confidence", 0))
    data["confidence"] = max(0.0, min(100.0, conf))

    return data
