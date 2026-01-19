import json
from app.ollama_client import OllamaClient


def align_resume(
    resume: dict,
    job_description: str,
    client: OllamaClient = None,
) -> dict:
    """
    Align resume to job description using Ollama.
    
    Args:
        resume: Base resume dictionary
        job_description: Job description text
        client: Optional OllamaClient instance (creates default if None)
    
    Returns:
        Tailored resume dictionary
    """
    if client is None:
        client = OllamaClient()
    
    with open("prompts/resume_align.txt", encoding="utf-8") as f:
        prompt = f.read()

    prompt = prompt.replace("{{ resume }}", json.dumps(resume, indent=2))
    prompt = prompt.replace("{{ job_description }}", job_description)

    return client.generate_json(prompt=prompt, temperature=0.2)
